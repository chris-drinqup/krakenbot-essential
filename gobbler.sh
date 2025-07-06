#!/bin/bash

# Version: 1.6 - ENHANCED: Limit orders by default, market orders for high-confidence signals
# MAJOR CHANGES:
# - Use limit orders when predicted price is provided
# - Use market orders only when ORDER_TYPE="market" or PRICE="market" 
# - Check ACTUAL balances instead of just lock files
# - SELL orders now allowed if user has actual base currency to sell
# - BUY orders now allowed if user has actual quote currency to buy
# - Lock files serve as optimization, but real balances are the authority

ACTION=$1       # buy, sell, or balance
PRICE=$2        # predicted price (or pair for balance command, or "market" for immediate execution)
ORDER_TYPE=$3   # market, limit, or PID for balance command
PAIR=$4         # trading pair (e.g., ADAUSD) or PID for balance command
PID=$5          # process ID from calling script
FORMAT_OPTION=$6 # --format=json or empty for human readable

DEPENDENCY_DIR=${DEPENDENCY_DIR:-/home/chris/krakenbot}  # Matches que.py lock_dir
FEE_PERCENTAGE=0.003  # 0.3% trading fee

# Handle balance command with different parameter order
if [ "$ACTION" == "balance" ]; then
    PAIR=$2
    FORMAT_OPTION=$3
    PID=$4
fi

# Parse format option EARLY
OUTPUT_FORMAT="human"
if [ "$FORMAT_OPTION" = "--format=json" ]; then
    OUTPUT_FORMAT="json"
fi

# Enhanced logging function
log_structured() {
    local LEVEL=$1
    local MESSAGE=$2
    local USER=$3
    local LOG_FILE="$DEPENDENCY_DIR/gobbler_${PAIR,,}.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S %Z') - $LEVEL - $USER - $MESSAGE" >> "$LOG_FILE"
}

# FIXED: Ensure gobbler.sh is executable
if [ ! -x "$0" ]; then
    chmod +x "$0"
    log_structured "INFO" "Fixed gobbler.sh permissions" "system"
fi

# NEW: Check actual balance for a specific user
check_actual_balance() {
    local USER=$1
    local CURRENCY_TYPE=$2  # "base" or "quote"
    local MIN_AMOUNT=$3     # minimum amount needed

    local LFILE="/home/chris/dp_logs/${USER}.log"
    local KFILE="/home/chris/keys/${USER}"

    if [ ! -f "$KFILE" ]; then
        echo "0"  # No key file = no balance
        return 1
    fi

    # Get balance via dp command
    local BALANCE_OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" --status buy "$TRADE_PAIR" 0 2>&1)

    if [ $? -ne 0 ]; then
        echo "0"  # Command failed = assume no balance
        return 1
    fi

    local ACTUAL_BALANCE=""

    if [ "$CURRENCY_TYPE" = "quote" ]; then
        # Extract quote currency balance (USD, USDT, etc.)
        ACTUAL_BALANCE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${QUOTE_CURRENCY} currency: \\\$\([0-9]*\.[0-9]*\).*/\1/p")
        if [[ -z "$ACTUAL_BALANCE" ]]; then
            ACTUAL_BALANCE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${KRAKEN_QUOTE_CURRENCY} currency: \\\$\([0-9]*\.[0-9]*\).*/\1/p")
        fi
    else
        # Extract base currency balance (ADA, BTC, etc.)
        ACTUAL_BALANCE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${BASE_CURRENCY} coins: \([0-9]*\.[0-9]*\).*/\1/p")
        if [[ -z "$ACTUAL_BALANCE" ]]; then
            ACTUAL_BALANCE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${KRAKEN_BASE_CURRENCY} coins: \([0-9]*\.[0-9]*\).*/\1/p")
        fi
    fi

    # Default to 0 if parsing failed
    if [[ -z "$ACTUAL_BALANCE" ]] || [[ "$ACTUAL_BALANCE" == "" ]]; then
        ACTUAL_BALANCE="0"
    fi

    echo "$ACTUAL_BALANCE"

    # Check if balance meets minimum requirement
    if (( $(echo "$ACTUAL_BALANCE >= $MIN_AMOUNT" | bc -l 2>/dev/null || echo "0") )); then
        return 0  # Sufficient balance
    else
        return 1  # Insufficient balance
    fi
}

# CRITICAL FIX: Position-based lock management (NO TIMEOUTS) - but check real balances first
create_position_lock() {
    local LOCK_FILE=$1
    local USER=$2
    local ACTION=$3
    local PID=$$

    # Create lock with position info and timestamp (but NO timeout)
    echo "$PID:$(date +%s):$ACTION:$USER" > "$LOCK_FILE"
    log_structured "INFO" "Created position lock: $ACTION for $USER" "$USER"
    return 0
}

# Check if position lock exists (without timeout - only cleared by opposite trade)
check_position_lock() {
    local LOCK_FILE=$1
    local REQUIRED_ACTION=$2
    local USER=$3

    if [ -f "$LOCK_FILE" ]; then
        # Read lock info
        LOCK_INFO=$(cat "$LOCK_FILE" 2>/dev/null)
        LOCK_ACTION=$(echo "$LOCK_INFO" | cut -d':' -f3)
        LOCK_USER=$(echo "$LOCK_INFO" | cut -d':' -f4)
        LOCK_TIME=$(echo "$LOCK_INFO" | cut -d':' -f2)

        if [ "$LOCK_USER" = "$USER" ]; then
            # Same user - check position logic
            if [ "$REQUIRED_ACTION" = "buy" ] && [ "$LOCK_ACTION" = "buy" ]; then
                log_structured "INFO" "Position lock prevents multiple buys (existing buy position)" "$USER"
                return 1  # Block: already have buy position
            elif [ "$REQUIRED_ACTION" = "sell" ] && [ "$LOCK_ACTION" = "sell" ]; then
                log_structured "INFO" "Position lock prevents multiple sells (no position to sell)" "$USER"
                return 1  # Block: already sold, no position
            else
                # Opposite action allowed (sell after buy, or buy after sell)
                log_structured "INFO" "Position lock allows opposite action: $REQUIRED_ACTION after $LOCK_ACTION" "$USER"
                return 0  # Allow opposite trade
            fi
        else
            # Different user - check stale lock (only remove if very old, like 1+ hours)
            CURRENT_TIME=$(date +%s)
            LOCK_AGE=$((CURRENT_TIME - LOCK_TIME))

            if [ $LOCK_AGE -gt 3600 ]; then  # 1 hour for different users only
                log_structured "WARN" "Removing stale position lock from different user ($LOCK_USER, age: ${LOCK_AGE}s)" "$USER"
                rm -f "$LOCK_FILE"
                return 0
            else
                log_structured "INFO" "Respecting active position lock from user $LOCK_USER" "$USER"
                return 1
            fi
        fi
    else
        # No lock exists - action allowed
        return 0
    fi
}

# Clear position lock when opposite trade completes
clear_position_lock() {
    local LOCK_FILE=$1
    local COMPLETED_ACTION=$2
    local USER=$3

    if [ -f "$LOCK_FILE" ]; then
        LOCK_INFO=$(cat "$LOCK_FILE" 2>/dev/null)
        LOCK_ACTION=$(echo "$LOCK_INFO" | cut -d':' -f3)
        LOCK_USER=$(echo "$LOCK_INFO" | cut -d':' -f4)

        if [ "$LOCK_USER" = "$USER" ]; then
            # Check if this is the opposite action that clears the lock
            if [ "$COMPLETED_ACTION" = "sell" ] && [ "$LOCK_ACTION" = "buy" ]; then
                rm -f "$LOCK_FILE"
                log_structured "INFO" "Cleared buy position lock after successful sell" "$USER"
            elif [ "$COMPLETED_ACTION" = "buy" ] && [ "$LOCK_ACTION" = "sell" ]; then
                rm -f "$LOCK_FILE"
                log_structured "INFO" "Cleared sell position lock after successful buy" "$USER"
            fi
        fi
    fi
}

# Cleanup function for script exit
cleanup_locks_on_exit() {
    # Only clean up locks created by this process
    for USER in funboy mason josh rick; do
        BUY_LOCK_FILE="$DEPENDENCY_DIR/position_lock_${USER}_${PAIR,,}_buy.lock"
        SELL_LOCK_FILE="$DEPENDENCY_DIR/position_lock_${USER}_${PAIR,,}_sell.lock"

        # Check if lock was created by this process
        for LOCK_FILE in "$BUY_LOCK_FILE" "$SELL_LOCK_FILE"; do
            if [ -f "$LOCK_FILE" ]; then
                LOCK_PID=$(cut -d':' -f1 "$LOCK_FILE" 2>/dev/null)
                if [ "$LOCK_PID" = "$$" ]; then
                    rm -f "$LOCK_FILE"
                    log_structured "INFO" "Cleaned up lock on exit: $LOCK_FILE" "$USER"
                fi
            fi
        done
    done
}
trap cleanup_locks_on_exit EXIT

# Currency detection functions
get_currency_info() {
    local TRADING_PAIR=$1
    local CLEAN_PAIR=$(echo "$TRADING_PAIR" | tr -d '/')
    local QUOTE_CURRENCIES=("USDT" "USD" "EUR" "GBP" "CAD" "AUD" "JPY" "CHF" "XBT" "BTC" "ETH")
    local BASE_CURRENCY=""
    local QUOTE_CURRENCY=""

    for quote in "${QUOTE_CURRENCIES[@]}"; do
        if [[ "$CLEAN_PAIR" == *"$quote" ]]; then
            QUOTE_CURRENCY="$quote"
            BASE_CURRENCY=$(echo "$CLEAN_PAIR" | sed "s/$quote$//")
            break
        fi
    done

    if [[ -z "$QUOTE_CURRENCY" ]]; then
        if [[ "$CLEAN_PAIR" =~ ^([A-Z0-9]+)(USD|EUR|GBP|CAD|JPY)$ ]]; then
            BASE_CURRENCY="${BASH_REMATCH[1]}"
            QUOTE_CURRENCY="${BASH_REMATCH[2]}"
        else
            local PAIR_LENGTH=${#CLEAN_PAIR}
            if [[ $PAIR_LENGTH -gt 6 ]]; then
                QUOTE_CURRENCY=$(echo "$CLEAN_PAIR" | tail -c 5 | head -c 4)
                BASE_CURRENCY=$(echo "$CLEAN_PAIR" | head -c $((PAIR_LENGTH - 4)))
            else
                QUOTE_CURRENCY=$(echo "$CLEAN_PAIR" | tail -c 4 | head -c 3)
                BASE_CURRENCY=$(echo "$CLEAN_PAIR" | head -c $((PAIR_LENGTH - 3)))
            fi
        fi
    fi

    echo "$BASE_CURRENCY|$QUOTE_CURRENCY"
}

get_kraken_currency_name() {
    local CURRENCY=$1
    case $CURRENCY in
        "USD") echo "ZUSD" ;;
        "EUR") echo "ZEUR" ;;
        "GBP") echo "ZGBP" ;;
        "CAD") echo "ZCAD" ;;
        "JPY") echo "ZJPY" ;;
        "AUD") echo "ZAUD" ;;
        "CHF") echo "CHF" ;;
        "BTC"|"XBT") echo "XXBT" ;;
        "ETH") echo "XETH" ;;
        "LTC") echo "XLTC" ;;
        "XRP") echo "XXRP" ;;
        "ADA") echo "ADA" ;;
        "DOT") echo "DOT" ;;
        "USDT") echo "USDT" ;;
        "USDC") echo "USDC" ;;
        "DAI") echo "DAI" ;;
        *) echo "$CURRENCY" ;;
    esac
}

# Extract currency information
TRADE_PAIR=$(echo "$PAIR" | tr -d '/')
CURRENCY_INFO=$(get_currency_info "$PAIR")
BASE_CURRENCY=$(echo "$CURRENCY_INFO" | cut -d'|' -f1)
QUOTE_CURRENCY=$(echo "$CURRENCY_INFO" | cut -d'|' -f2)
KRAKEN_BASE_CURRENCY=$(get_kraken_currency_name "$BASE_CURRENCY")
KRAKEN_QUOTE_CURRENCY=$(get_kraken_currency_name "$QUOTE_CURRENCY")

if [ "$OUTPUT_FORMAT" != "json" ]; then
    echo "🔍 Enhanced Position-Based Trading with SMART ORDER TYPES:" >&2
    echo "   Pair: $PAIR ($BASE_CURRENCY/$QUOTE_CURRENCY)" >&2
    echo "   Order Logic: Limit orders for predicted prices, Market orders for urgent signals" >&2
    echo "   Balance Authority: ACTUAL exchange balances override lock files" >&2
fi

# HANDLE BALANCE COMMAND (unchanged)
if [ "$ACTION" == "balance" ]; then
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo "Checking balances for all users..." >&2
    fi

    TOTAL_QUOTE=0
    TOTAL_BASE=0
    ACTIVE_USERS=0

    for USER in funboy mason josh rick
    do
        LFILE="/home/chris/dp_logs/${USER}.log"
        KFILE="/home/chris/keys/${USER}"

        if [ ! -f "$KFILE" ]; then
            if [ "$OUTPUT_FORMAT" != "json" ]; then
                echo "User $USER: key file not found" >&2
            fi
            continue
        fi

        if [ "$OUTPUT_FORMAT" != "json" ]; then
            echo "Checking balance for user: $USER" >&2
        fi

        BALANCE_OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" --status buy "$TRADE_PAIR" 0 2>&1)

        if [ $? -eq 0 ]; then
            # Extract balances
            QUOTE_BALANCE=""
            if [[ -z "$QUOTE_BALANCE" ]]; then
                QUOTE_BALANCE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${QUOTE_CURRENCY} currency: \\\$\([0-9]*\.[0-9]*\).*/\1/p")
            fi
            if [[ -z "$QUOTE_BALANCE" ]]; then
                QUOTE_BALANCE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${KRAKEN_QUOTE_CURRENCY} currency: \\\$\([0-9]*\.[0-9]*\).*/\1/p")
            fi

            USER_BASE=""
            if [[ -z "$USER_BASE" ]]; then
                USER_BASE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${BASE_CURRENCY} coins: \([0-9]*\.[0-9]*\).*/\1/p")
            fi
            if [[ -z "$USER_BASE" ]]; then
                USER_BASE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*${KRAKEN_BASE_CURRENCY} coins: \([0-9]*\.[0-9]*\).*/\1/p")
            fi

            USER_QUOTE="$QUOTE_BALANCE"

            if [ -z "$USER_QUOTE" ] || [ "$USER_QUOTE" = "" ]; then
                USER_QUOTE="0.00"
            fi
            if [ -z "$USER_BASE" ] || [ "$USER_BASE" = "" ]; then
                USER_BASE="0.0000"
            fi

            if [ "$USER_QUOTE" != "0.00" ] && [ "$USER_QUOTE" != "0" ]; then
                TOTAL_QUOTE=$(echo "$TOTAL_QUOTE + $USER_QUOTE" | bc -l)
                ACTIVE_USERS=$((ACTIVE_USERS + 1))
            fi

            if [ "$USER_BASE" != "0.0000" ] && [ "$USER_BASE" != "0" ]; then
                TOTAL_BASE=$(echo "$TOTAL_BASE + $USER_BASE" | bc -l)
            fi

            if [ "$OUTPUT_FORMAT" != "json" ]; then
                echo "User $USER: \$${USER_QUOTE} ${QUOTE_CURRENCY}, ${USER_BASE} ${BASE_CURRENCY}" >&2
            fi
        else
            if [ "$OUTPUT_FORMAT" != "json" ]; then
                echo "Failed to get balance for $USER: $BALANCE_OUTPUT" >&2
            fi
        fi
    done

    TOTAL_QUOTE=$(printf "%.2f" "$TOTAL_QUOTE" 2>/dev/null || echo "0.00")
    TOTAL_BASE=$(printf "%.4f" "$TOTAL_BASE" 2>/dev/null || echo "0.0000")

    if [ "$OUTPUT_FORMAT" = "json" ]; then
        echo "{\"status\":\"success\",\"available_usd\":\"$TOTAL_QUOTE\",\"available_base\":\"$TOTAL_BASE\",\"active_users\":$ACTIVE_USERS,\"timestamp\":\"$(date -Iseconds)\",\"pair\":\"$PAIR\",\"quote_currency\":\"$QUOTE_CURRENCY\"}"
    else
        echo "Total Available Balances:"
        echo "${QUOTE_CURRENCY}: \$${TOTAL_QUOTE}"
        echo "${BASE_CURRENCY}: ${TOTAL_BASE}"
        echo "Active users: ${ACTIVE_USERS}"
    fi

    exit 0
fi

# Validate inputs for buy/sell actions
if [ -z "$ACTION" ] || [ -z "$PRICE" ] || [ -z "$ORDER_TYPE" ] || [ -z "$PAIR" ] || [ -z "$PID" ]; then
    echo "Usage: $0 <buy|sell|balance> <price|pair> <market|limit|pid> <pair|pid> <pid> [--format=json]" >&2
    exit 1
fi

# ENHANCED: Position-based trading with SMART ORDER TYPES and REAL BALANCE CHECKING
for USER in funboy mason josh rick
do
    USER_START_TIME=$(date +%s.%N)

    LFILE="/home/chris/dp_logs/${USER}.log"
    KFILE="/home/chris/keys/${USER}"

    # Position-based lock files (per user, per pair)
    BUY_LOCK_FILE="$DEPENDENCY_DIR/position_lock_${USER}_${PAIR,,}_buy.lock"
    SELL_LOCK_FILE="$DEPENDENCY_DIR/position_lock_${USER}_${PAIR,,}_sell.lock"

    if [ ! -f "$KFILE" ]; then
        log_structured "WARN" "API key file $KFILE not found, skipping" "$USER"
        continue
    fi

    if [ "$ACTION" == "buy" ]; then
        # SMART BUY LOGIC: Check locks first, fall back to real balance if needed

        # Step 1: Check if we should respect buy lock (prevents spam buying)
        if [ -f "$BUY_LOCK_FILE" ]; then
            LOCK_INFO=$(cat "$BUY_LOCK_FILE" 2>/dev/null)
            LOCK_USER=$(echo "$LOCK_INFO" | cut -d':' -f4)

            if [ "$LOCK_USER" = "$USER" ]; then
                log_structured "INFO" "Buy blocked - user already has buy lock (existing position)" "$USER"
                echo "Buy blocked for $USER - already have position"
                continue
            fi
        fi

        # Step 2: Check if we have quote currency to buy with
        ACTUAL_QUOTE_BALANCE=$(check_actual_balance "$USER" "quote" "1.0")
        CHECK_RESULT=$?

        if [ $CHECK_RESULT -eq 0 ] && (( $(echo "$ACTUAL_QUOTE_BALANCE > 1.0" | bc -l 2>/dev/null || echo "0") )); then
            # User has sufficient quote currency for buying

            # Step 3: Execute buy and create proper lock state
            create_position_lock "$BUY_LOCK_FILE" "$USER" "buy"

            # Clear any stale sell lock since we're buying again
            if [ -f "$SELL_LOCK_FILE" ]; then
                clear_position_lock "$SELL_LOCK_FILE" "buy" "$USER"
            fi

            VOLUME="99%"  # Use 99% of available quote currency

            # ENHANCED: Determine order type based on price and order_type parameters
            if [ "$ORDER_TYPE" == "market" ] || [ "${PRICE}" == "market" ]; then
                # Use market order for immediate execution
                log_structured "INFO" "Executing market buy with $VOLUME of available ${QUOTE_CURRENCY} funds (balance: $ACTUAL_QUOTE_BALANCE)" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" buy "$TRADE_PAIR" "$VOLUME" --makemarket --timeout=30 2>&1)
            else
                # Use limit order with predicted price
                log_structured "INFO" "Setting limit buy at $PRICE with $VOLUME of available ${QUOTE_CURRENCY} funds (balance: $ACTUAL_QUOTE_BALANCE)" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" buy "$TRADE_PAIR" "$VOLUME" --price="$PRICE" --timeout=30 2>&1)
            fi

            EXIT_CODE=$?

            if [ $EXIT_CODE -eq 0 ] && ! echo "$OUTPUT" | grep -q "Error"; then
                log_structured "INFO" "Buy succeeded - Buy lock active until sell" "$USER"
                echo "Buy succeeded for $USER - Position opened"
            else
                # Buy failed - remove the position lock
                rm -f "$BUY_LOCK_FILE"
                ERROR_MSG=$(echo "$OUTPUT" | grep -i error | head -n1)
                log_structured "ERROR" "Buy failed, removed buy lock: $ERROR_MSG" "$USER"
                echo "Buy failed for $USER: $ERROR_MSG"
            fi
        else
            log_structured "INFO" "Buy blocked - insufficient quote currency balance: $ACTUAL_QUOTE_BALANCE ${QUOTE_CURRENCY}" "$USER"
            echo "Buy blocked for $USER - insufficient ${QUOTE_CURRENCY} balance ($ACTUAL_QUOTE_BALANCE)"
        fi

    elif [ "$ACTION" == "sell" ]; then
        # SMART SELL LOGIC: Check locks first, fall back to real balance if locks missing

        # Step 1: Check if we should respect sell lock (prevents spam selling)
        if [ -f "$SELL_LOCK_FILE" ]; then
            LOCK_INFO=$(cat "$SELL_LOCK_FILE" 2>/dev/null)
            LOCK_USER=$(echo "$LOCK_INFO" | cut -d':' -f4)

            if [ "$LOCK_USER" = "$USER" ]; then
                log_structured "INFO" "Sell blocked - user already has sell lock (no position to close)" "$USER"
                echo "Sell blocked for $USER - no position to close"
                continue
            fi
        fi

        # Step 2: Check if we have buy lock (ideal case - clear position tracking)
        if [ -f "$BUY_LOCK_FILE" ]; then
            LOCK_INFO=$(cat "$BUY_LOCK_FILE" 2>/dev/null)
            LOCK_USER=$(echo "$LOCK_INFO" | cut -d':' -f4)

            if [ "$LOCK_USER" = "$USER" ]; then
                log_structured "INFO" "Sell allowed - user has buy position lock" "$USER"
                ALLOW_SELL=true
                SELL_REASON="buy_lock_found"
            else
                ALLOW_SELL=false
                SELL_REASON="buy_lock_different_user"
            fi
        else
            # Step 3: No buy lock found - check real balance (handles missing/stale locks)
            ACTUAL_BASE_BALANCE=$(check_actual_balance "$USER" "base" "1.0")
            CHECK_RESULT=$?

            if [ $CHECK_RESULT -eq 0 ] && (( $(echo "$ACTUAL_BASE_BALANCE > 1.0" | bc -l 2>/dev/null || echo "0") )); then
                log_structured "INFO" "Sell allowed - no buy lock found but user has actual ${BASE_CURRENCY} balance: $ACTUAL_BASE_BALANCE (missing/stale lock recovery)" "$USER"
                ALLOW_SELL=true
                SELL_REASON="real_balance_fallback"
            else
                log_structured "INFO" "Sell blocked - no buy lock and insufficient balance: $ACTUAL_BASE_BALANCE ${BASE_CURRENCY}" "$USER"
                ALLOW_SELL=false
                SELL_REASON="no_position"
            fi
        fi

        # Step 4: Execute sell if allowed
        if [ "$ALLOW_SELL" = true ]; then
            VOLUME="100%"  # Use 100% of available base currency

            # ENHANCED: Determine order type based on price and order_type parameters
            if [ "$ORDER_TYPE" == "market" ] || [ "${PRICE}" == "market" ]; then
                # Use market order for immediate execution
                log_structured "INFO" "Executing market sell with $VOLUME of available ${BASE_CURRENCY} funds (reason: $SELL_REASON)" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" sell "$TRADE_PAIR" "$VOLUME" --makemarket --timeout=30 2>&1)
            else
                # Use limit order with predicted price
                log_structured "INFO" "Setting limit sell at $PRICE with $VOLUME of available ${BASE_CURRENCY} funds (reason: $SELL_REASON)" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" sell "$TRADE_PAIR" "$VOLUME" --price="$PRICE" --timeout=30 2>&1)
            fi

            EXIT_CODE=$?

            if [ $EXIT_CODE -eq 0 ] && ! echo "$OUTPUT" | grep -q "Error"; then
                # Sell succeeded - update lock state properly
                clear_position_lock "$BUY_LOCK_FILE" "sell" "$USER"
                create_position_lock "$SELL_LOCK_FILE" "$USER" "sell"

                log_structured "INFO" "Sell succeeded - Lock state rebuilt: cleared buy lock, created sell lock" "$USER"
                echo "Sell succeeded for $USER - Position closed"
            else
                ERROR_MSG=$(echo "$OUTPUT" | grep -i error | head -n1)
                log_structured "ERROR" "Sell failed: $ERROR_MSG" "$USER"
                echo "Sell failed for $USER: $ERROR_MSG"
            fi
        else
            # Not allowed to sell
            echo "Sell blocked for $USER - $SELL_REASON"

            # Create sell lock to prevent future attempts if truly no position
            if [ "$SELL_REASON" = "no_position" ]; then
                create_position_lock "$SELL_LOCK_FILE" "$USER" "sell"
            fi
        fi
    fi

    USER_END_TIME=$(date +%s.%N)
    USER_EXECUTION_TIME=$(echo "$USER_END_TIME - $USER_START_TIME" | bc -l)
    log_structured "INFO" "Smart order execution time: ${USER_EXECUTION_TIME}s" "$USER"
done

if [ "$OUTPUT_FORMAT" != "json" ]; then
    echo "🎯 SMART Order-Type Trading Complete:" >&2
    echo "   LIMIT ORDERS: Used by default with predicted prices for precision" >&2
    echo "   MARKET ORDERS: Used only for high-confidence immediate signals" >&2
    echo "   BALANCE AUTHORITY: Real exchange balances override lock files" >&2
    echo "   POSITION TRACKING: Lock files prevent spam, real balances handle recovery" >&2
fi

exit 0

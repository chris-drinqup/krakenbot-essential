#!/bin/bash

# Version: 1.6 - Added email notifications for buy/sell completions
# CRITICAL FIX for BASE_CURRENCY extraction from ADAUSDT pairs
# Fixed USDT vs ZUSD currency detection and proper regex parsing
# FIXED: BASE_CURRENCY now correctly extracts "ADA" from "ADAUSDT" instead of "ADAUSDT"

# Copyright (c) 2025 Chris Barringer
# All rights reserved.

ACTION=$1       # buy, sell, or balance
PRICE=$2        # predicted price (or pair for balance command)
ORDER_TYPE=$3   # market, limit, or PID for balance command
PAIR=$4         # trading pair (e.g., ADAUSD) or PID for balance command
PID=$5          # process ID from calling script
FORMAT_OPTION=$6 # --format=json or empty for human readable

DEPENDENCY_DIR=${DEPENDENCY_DIR:-/home/chris/krakenbot/pro}  # Matches que.py lock_dir
FEE_PERCENTAGE=0.003  # 0.3% trading fee
LOCK_TIMEOUT=300  # 5 minutes lock timeout

# Handle balance command with different parameter order
if [ "$ACTION" == "balance" ]; then
    PAIR=$2
    # Flexible parameter parsing: handle both with and without PID
    if [ "$3" = "--format=json" ]; then
        # Called without PID: balance ADAUSDT --format=json
        PID=""
        FORMAT_OPTION=$3
    else
        # Called with PID: balance ADAUSDT 101763 --format=json
        PID=$3
        FORMAT_OPTION=$4
    fi
fi

# Set up log file path - fix the log file detection
if [ "$ACTION" != "balance" ]; then
    KRAKEN_LOG="$DEPENDENCY_DIR/$(ls -t $DEPENDENCY_DIR/krakendp_${PAIR,,}_*.log 2>/dev/null | head -n1 | xargs basename 2>/dev/null)"
    if [ -z "$KRAKEN_LOG" ] || [ "$KRAKEN_LOG" = "$DEPENDENCY_DIR/" ]; then
        KRAKEN_LOG="$DEPENDENCY_DIR/krakendp_${PAIR,,}_$(date +%Y%m%d).log"
    fi
else
    KRAKEN_LOG="$DEPENDENCY_DIR/gobbler_balance.log"
fi

# Parse format option
OUTPUT_FORMAT="human"
if [ "$FORMAT_OPTION" = "--format=json" ]; then
    OUTPUT_FORMAT="json"
fi

echo "Starting gobbler with params: $@" >&2

# Enhanced logging function
log_structured() {
    local LEVEL=$1
    local MESSAGE=$2
    local USER=$3
    echo "$(date '+%Y-%m-%d %H:%M:%S %Z') - $LEVEL - $USER - $MESSAGE" >> "$KRAKEN_LOG"
}

# Email notification function
send_trade_alert() {
    local ACTION=$1
    local USER=$2
    local VOLUME=$3
    local PRICE=$4
    local PAIR=$5
    local PROFIT=$6
    
    # Send to notification API
    curl -s -X POST http://localhost:5001/notify \
      -H "Content-Type: application/json" \
      -d "{
        \"action\": \"$ACTION\",
        \"user\": \"$USER\",
        \"volume\": \"$VOLUME\",
        \"price\": \"$PRICE\",
        \"pair\": \"$PAIR\",
        \"profit\": \"$PROFIT\"
      }" > /dev/null 2>&1
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ALERT - Trade notification sent: $ACTION $VOLUME $PAIR @ \$$PRICE for $USER (profit: \$$PROFIT)" >> "$KRAKEN_LOG"
}

# Check if bc is installed
if ! command -v bc >/dev/null 2>&1; then
    echo "Error: 'bc' command not found. Please install bc to perform calculations." >&2
    exit 1
fi

# Function to detect USD currency format dynamically
detect_usd_currency() {
    local BALANCE_TEXT=$1
    if echo "$BALANCE_TEXT" | grep -q "USDT currency:"; then
        echo "USDT"
    elif echo "$BALANCE_TEXT" | grep -q "ZUSD currency:"; then
        echo "ZUSD"
    else
        echo "UNKNOWN"
    fi
}

# Function to extract USD balance dynamically
extract_usd_balance() {
    local BALANCE_TEXT=$1
    local USD_CURRENCY=$(detect_usd_currency "$BALANCE_TEXT")

    if [ "$USD_CURRENCY" = "USDT" ]; then
        echo "$BALANCE_TEXT" | sed -n 's/.*USDT currency: \$\([0-9]*\.[0-9]*\).*/\1/p'
    elif [ "$USD_CURRENCY" = "ZUSD" ]; then
        echo "$BALANCE_TEXT" | sed -n 's/.*ZUSD currency: \$\([0-9]*\.[0-9]*\).*/\1/p'
    else
        echo ""
    fi
}

# FIXED: Handle balance command using dp --status with proper parsing
if [ "$ACTION" == "balance" ]; then
    echo "Checking balances for all users using dp --status..." >&2

    # Convert pair to Kraken format and extract base currency
    TRADE_PAIR=$(echo "$PAIR" | tr -d '/')

    # CRITICAL FIX: Extract base currency properly from pairs like ADAUSDT
    # Old (broken): BASE_CURRENCY=$(echo "$PAIR" | cut -d'/' -f1)  # ADAUSDT -> ADAUSDT (no slash!)
    # New (fixed): Remove USDT/USD suffix to get base currency
    BASE_CURRENCY=$(echo "$PAIR" | sed 's/USDT$//' | sed 's/USD$//')  # ADAUSDT -> ADA

    echo "DEBUG: PAIR=$PAIR, BASE_CURRENCY=$BASE_CURRENCY, TRADE_PAIR=$TRADE_PAIR" >&2

    TOTAL_USD=0
    TOTAL_BASE=0
    ACTIVE_USERS=0

    for USER in funboy mason josh rick
    do
        LFILE="/home/chris/dp_logs/${USER}.log"
        KFILE="/home/chris/keys/${USER}"

        # Check if key file exists
        if [ ! -f "$KFILE" ]; then
            echo "User $USER: key file not found" >&2
            continue
        fi

        # Use dp --status to get balance
        echo "Checking balance for user: $USER" >&2
        BALANCE_OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" --status buy "$TRADE_PAIR" 0 2>&1)

        if [ $? -eq 0 ]; then
            echo "Raw balance output for $USER: $BALANCE_OUTPUT" >&2

            # FIXED: Parse the --status output using dynamic USD currency detection
            USER_USD=$(extract_usd_balance "$BALANCE_OUTPUT")

            # Extract base currency balance - NOW USING CORRECT BASE_CURRENCY
            USER_BASE=$(echo "$BALANCE_OUTPUT" | sed -n "s/.*$BASE_CURRENCY coins: \([0-9]*\.[0-9]*\).*/\1/p")

            echo "DEBUG: Looking for '$BASE_CURRENCY coins:' in output, found: '$USER_BASE'" >&2

            # Set to 0 if empty or not found
            if [ -z "$USER_USD" ] || [ "$USER_USD" = "" ]; then
                USER_USD="0.00"
            fi
            if [ -z "$USER_BASE" ] || [ "$USER_BASE" = "" ]; then
                USER_BASE="0.0000"
            fi

            # Add to totals (using bc for decimal arithmetic)
            if [ "$USER_USD" != "0.00" ] && [ "$USER_USD" != "0" ]; then
                TOTAL_USD=$(echo "$TOTAL_USD + $USER_USD" | bc -l)
                ACTIVE_USERS=$((ACTIVE_USERS + 1))
            fi

            if [ "$USER_BASE" != "0.0000" ] && [ "$USER_BASE" != "0" ]; then
                TOTAL_BASE=$(echo "$TOTAL_BASE + $USER_BASE" | bc -l)
            fi

            echo "User $USER: \$${USER_USD} USD, ${USER_BASE} ${BASE_CURRENCY}" >&2
        else
            echo "Failed to get balance for $USER: $BALANCE_OUTPUT" >&2
        fi
    done

    # Ensure totals are properly formatted
    TOTAL_USD=$(printf "%.2f" "$TOTAL_USD" 2>/dev/null || echo "0.00")
    TOTAL_BASE=$(printf "%.4f" "$TOTAL_BASE" 2>/dev/null || echo "0.0000")

    # Output result
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        echo "{\"status\":\"success\",\"available_usd\":\"$TOTAL_USD\",\"available_base\":\"$TOTAL_BASE\",\"active_users\":$ACTIVE_USERS,\"timestamp\":\"$(date -Iseconds)\",\"pair\":\"$PAIR\"}"
    else
        echo "Total Available Balances:"
        echo "USD: \$${TOTAL_USD}"
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

# Convert pair to Kraken format and extract base currency
TRADE_PAIR=$(echo "$PAIR" | tr -d '/')
# CRITICAL FIX: Extract base currency properly from pairs like ADAUSDT
BASE_CURRENCY=$(echo "$PAIR" | sed 's/USDT$//' | sed 's/USD$//')  # ADAUSDT -> ADA

# Enhanced lock management with timeout
create_lock_with_timeout() {
    local LOCK_FILE=$1
    local TIMEOUT=${2:-$LOCK_TIMEOUT}
    local PID=$$

    # Check if lock exists and is stale
    if [ -f "$LOCK_FILE" ]; then
        LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)))
        if [ $LOCK_AGE -gt $TIMEOUT ]; then
            log_structured "WARN" "Removing stale lock (age: ${LOCK_AGE}s)" "system"
            rm -f "$LOCK_FILE"
        else
            return 1  # Lock still valid
        fi
    fi

    # Create lock with PID and timestamp
    echo "$PID:$(date +%s)" > "$LOCK_FILE"
    return 0
}

# Cleanup function
cleanup_locks_on_exit() {
    for USER in funboy mason josh rick; do
        BUY_LOCK_FILE="$DEPENDENCY_DIR/buy_lock_${USER}.lock"
        SELL_LOCK_FILE="$DEPENDENCY_DIR/sell_lock_${USER}.lock"

        # Only remove our own locks
        if [ -f "$BUY_LOCK_FILE" ]; then
            LOCK_PID=$(cut -d':' -f1 "$BUY_LOCK_FILE" 2>/dev/null)
            if [ "$LOCK_PID" = "$$" ]; then
                rm -f "$BUY_LOCK_FILE"
            fi
        fi

        if [ -f "$SELL_LOCK_FILE" ]; then
            LOCK_PID=$(cut -d':' -f1 "$SELL_LOCK_FILE" 2>/dev/null)
            if [ "$LOCK_PID" = "$$" ]; then
                rm -f "$SELL_LOCK_FILE"
            fi
        fi
    done
}
trap cleanup_locks_on_exit EXIT

# Error classification function
classify_error() {
    local ERROR_MSG=$1

    if echo "$ERROR_MSG" | grep -qi "insufficient funds"; then
        echo "INSUFFICIENT_FUNDS"
    elif echo "$ERROR_MSG" | grep -qi "volume minimum"; then
        echo "VOLUME_TOO_SMALL"
    elif echo "$ERROR_MSG" | grep -qi "rate limit\|too many"; then
        echo "RATE_LIMIT"
    elif echo "$ERROR_MSG" | grep -qi "network\|connection\|timeout"; then
        echo "NETWORK"
    else
        echo "UNKNOWN"
    fi
}

# Enhanced error handling
handle_trade_error() {
    local ERROR_TYPE=$1
    local USER=$2
    local ERROR_MSG=$3

    case $ERROR_TYPE in
        INSUFFICIENT_FUNDS)
            log_structured "INFO" "Insufficient funds, skipping" "$USER"
            ;;
        VOLUME_TOO_SMALL)
            log_structured "INFO" "Volume too small, adjusting minimum" "$USER"
            ;;
        RATE_LIMIT)
            log_structured "WARN" "Rate limit hit, waiting 30s" "$USER"
            sleep 30
            ;;
        NETWORK)
            log_structured "WARN" "Network error, retrying in 10s" "$USER"
            sleep 10
            ;;
        *)
            log_structured "ERROR" "Unknown error: $ERROR_MSG" "$USER"
            ;;
    esac
}

# JSON output function
output_result() {
    local STATUS=$1
    local USER=$2
    local VOLUME=$3
    local PRICE=$4
    local PROFIT=$5
    local ORDER_ID=$6
    local ERROR_MSG=$7

    if [ "$OUTPUT_FORMAT" = "json" ]; then
        if [ "$STATUS" = "success" ]; then
            echo "{\"status\":\"success\",\"user\":\"$USER\",\"executed_volume\":\"$VOLUME\",\"executed_price\":\"$PRICE\",\"profit\":\"$PROFIT\",\"order_id\":\"$ORDER_ID\",\"timestamp\":\"$(date -Iseconds)\",\"action\":\"$ACTION\",\"pair\":\"$PAIR\"}"
        else
            echo "{\"status\":\"error\",\"user\":\"$USER\",\"error\":\"$ERROR_MSG\",\"timestamp\":\"$(date -Iseconds)\",\"action\":\"$ACTION\",\"pair\":\"$PAIR\"}"
        fi
    else
        # Original human-readable output
        if [ "$STATUS" = "success" ]; then
            echo "$ACTION succeeded for $USER"
            echo "Calculated volume requested = $VOLUME coins"
            echo "Executed at price: $PRICE"
            echo "Predicted profit: \$$PROFIT"
            echo "Order ID: $ORDER_ID"
        else
            echo "$ACTION failed for $USER: $ERROR_MSG"
        fi
    fi
}

# Performance monitoring
SCRIPT_START_TIME=$(date +%s.%N)

# Multi-user loop with enhanced error handling
for USER in funboy mason josh rick
do
    USER_START_TIME=$(date +%s.%N)

    LFILE="/home/chris/dp_logs/${USER}.log"
    KFILE="/home/chris/keys/${USER}"
    BUY_LOCK_FILE="$DEPENDENCY_DIR/buy_lock_${USER}.lock"
    SELL_LOCK_FILE="$DEPENDENCY_DIR/sell_lock_${USER}.lock"

    # Check if key file exists
    if [ ! -f "$KFILE" ]; then
        log_structured "WARN" "API key file $KFILE not found, skipping" "$USER"
        continue
    fi

    if [ "$ACTION" == "buy" ]; then
        if create_lock_with_timeout "$BUY_LOCK_FILE"; then
            log_structured "INFO" "Buy lock created" "$USER"
            VOLUME="99%"  # Use 99% of available USD

            if [ "$ORDER_TYPE" == "market" ]; then
                log_structured "INFO" "Executing market buy with 99% of available funds" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" buy "$TRADE_PAIR" "$VOLUME" --makemarket --timeout=30 2>&1)
            else
                log_structured "INFO" "Setting limit buy at $PRICE with 99% of available funds" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" buy "$TRADE_PAIR" "$VOLUME" --makemarket --price="$PRICE" --timeout=30 2>&1)
            fi
            EXIT_CODE=$?

            # Extract balances and trade details from dp output using dynamic USD detection
            USD_BALANCE=$(extract_usd_balance "$OUTPUT")
            if [ -z "$USD_BALANCE" ]; then
                USD_BALANCE="0.0"
            fi

            BASE_BALANCE=$(echo "$OUTPUT" | grep "$BASE_CURRENCY coins" | head -n1 | sed "s/.*$BASE_CURRENCY coins: //; s/,.*//" | tr -d '[:space:]' || echo "0.0")
            VOLUME_COINS=$(echo "$OUTPUT" | grep "Calculated volume requested" | sed 's/.*= //; s/ coins//' | tr -d '[:space:]' || echo "0.0")

            if [ "$USD_BALANCE" == "0.0" ] && [ "$VOLUME_COINS" == "0.0" ]; then
                CURRENCY=$(detect_usd_currency "$OUTPUT")
                ERROR_MSG="No $CURRENCY available ($CURRENCY: $USD_BALANCE)"
                ERROR_TYPE=$(classify_error "$ERROR_MSG")
                handle_trade_error "$ERROR_TYPE" "$USER" "$ERROR_MSG"
                output_result "error" "$USER" "" "" "" "" "$ERROR_MSG"
                rm -f "$BUY_LOCK_FILE"
                continue
            fi

            # Calculate predicted profit
            EXIT_PRICE=$(echo "$PRICE * 1.034" | bc -l)
            ENTRY_TOTAL=$(echo "$PRICE * $VOLUME_COINS" | bc -l)
            EXIT_TOTAL=$(echo "$EXIT_PRICE * $VOLUME_COINS" | bc -l)
            ENTRY_FEE=$(echo "$ENTRY_TOTAL * $FEE_PERCENTAGE" | bc -l)
            EXIT_FEE=$(echo "$EXIT_TOTAL * $FEE_PERCENTAGE" | bc -l)
            PREDICTED_PROFIT=$(echo "$EXIT_TOTAL - $ENTRY_TOTAL - $ENTRY_FEE - $EXIT_FEE" | bc -l)

            if [ $EXIT_CODE -ne 0 ] || echo "$OUTPUT" | grep -q "Error"; then
                ERROR_MSG=$(echo "$OUTPUT" | grep -i error | head -n1)
                if [ -z "$ERROR_MSG" ]; then
                    if echo "$OUTPUT" | grep -q "volume minimum not met"; then
                        ERROR_MSG="Insufficient funds (volume minimum not met)"
                    else
                        ERROR_MSG="Unknown error occurred"
                    fi
                fi

                ERROR_TYPE=$(classify_error "$ERROR_MSG")
                handle_trade_error "$ERROR_TYPE" "$USER" "$ERROR_MSG"
                output_result "error" "$USER" "" "" "" "" "$ERROR_MSG"
                rm -f "$BUY_LOCK_FILE"
            else
                # Extract order ID
                ORDER_ID=$(echo "$OUTPUT" | grep -i "order.*id" | sed 's/.*id[^0-9A-Za-z]*\([0-9A-Za-z-]*\).*/\1/' || echo "unknown")

                log_structured "INFO" "Buy succeeded, volume: $VOLUME_COINS, profit: \$$PREDICTED_PROFIT" "$USER"
                
                # Send email notification for successful buy
                send_trade_alert "BUY" "$USER" "$VOLUME_COINS" "$PRICE" "$PAIR" "$PREDICTED_PROFIT"
                
                output_result "success" "$USER" "$VOLUME_COINS" "$PRICE" "$PREDICTED_PROFIT" "$ORDER_ID" ""
            fi
        else
            log_structured "INFO" "Buy skipped, lock exists" "$USER"
            output_result "error" "$USER" "" "" "" "" "Buy lock exists"
        fi

    elif [ "$ACTION" == "sell" ]; then
        if create_lock_with_timeout "$SELL_LOCK_FILE"; then
            log_structured "INFO" "Sell lock created" "$USER"

            # Remove buy lock if it exists
            if [ -f "$BUY_LOCK_FILE" ]; then
                rm -f "$BUY_LOCK_FILE"
                log_structured "INFO" "Removed buy lock" "$USER"
            fi

            VOLUME="100%"  # Use 100% of available base currency

            if [ "$ORDER_TYPE" == "market" ]; then
                log_structured "INFO" "Executing market sell with 100% of available funds" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" sell "$TRADE_PAIR" "$VOLUME" --makemarket --timeout=30 2>&1)
            else
                log_structured "INFO" "Setting limit sell at $PRICE with 100% of available funds" "$USER"
                OUTPUT=$(/home/code/dp --keyfile="${KFILE}" --logfile="${LFILE}" sell "$TRADE_PAIR" "$VOLUME" --makemarket --price="$PRICE" --timeout=30 2>&1)
            fi
            EXIT_CODE=$?

            # Extract balances and trade details from dp output using dynamic USD detection
            USD_BALANCE=$(extract_usd_balance "$OUTPUT")
            if [ -z "$USD_BALANCE" ]; then
                USD_BALANCE="0.0"
            fi

            BASE_BALANCE=$(echo "$OUTPUT" | grep "$BASE_CURRENCY coins" | head -n1 | sed "s/.*$BASE_CURRENCY coins: //; s/,.*//" | tr -d '[:space:]' || echo "0.0")
            VOLUME_COINS=$(echo "$OUTPUT" | grep "Calculated volume requested" | sed 's/.*= //; s/ coins//' | tr -d '[:space:]' || echo "0.0")

            if [ "$BASE_BALANCE" == "0.0" ] && [ "$VOLUME_COINS" == "0.0" ]; then
                ERROR_MSG="No $BASE_CURRENCY available ($BASE_BALANCE)"
                ERROR_TYPE=$(classify_error "$ERROR_MSG")
                handle_trade_error "$ERROR_TYPE" "$USER" "$ERROR_MSG"
                output_result "error" "$USER" "" "" "" "" "$ERROR_MSG"
                rm -f "$SELL_LOCK_FILE"
                continue
            fi

            # Calculate predicted profit
            ENTRY_PRICE=$(echo "$PRICE / 1.034" | bc -l)
            ENTRY_TOTAL=$(echo "$ENTRY_PRICE * $VOLUME_COINS" | bc -l)
            EXIT_TOTAL=$(echo "$PRICE * $VOLUME_COINS" | bc -l)
            ENTRY_FEE=$(echo "$ENTRY_TOTAL * $FEE_PERCENTAGE" | bc -l)
            EXIT_FEE=$(echo "$EXIT_TOTAL * $FEE_PERCENTAGE" | bc -l)
            PREDICTED_PROFIT=$(echo "$EXIT_TOTAL - $ENTRY_TOTAL - $ENTRY_FEE - $EXIT_FEE" | bc -l)

            if [ $EXIT_CODE -ne 0 ] || echo "$OUTPUT" | grep -q "Error"; then
                ERROR_MSG=$(echo "$OUTPUT" | grep -i error | head -n1)
                if [ -z "$ERROR_MSG" ]; then
                    if echo "$OUTPUT" | grep -q "volume minimum not met"; then
                        ERROR_MSG="Insufficient funds (volume minimum not met)"
                    else
                        ERROR_MSG="Unknown error occurred"
                    fi
                fi

                ERROR_TYPE=$(classify_error "$ERROR_MSG")
                handle_trade_error "$ERROR_TYPE" "$USER" "$ERROR_MSG"
                output_result "error" "$USER" "" "" "" "" "$ERROR_MSG"
                rm -f "$SELL_LOCK_FILE"
            else
                # Extract order ID and actual profit if available
                ORDER_ID=$(echo "$OUTPUT" | grep -i "order.*id" | sed 's/.*id[^0-9A-Za-z]*\([0-9A-Za-z-]*\).*/\1/' || echo "unknown")
                ACTUAL_PROFIT=$(echo "$OUTPUT" | grep -o "Profit: \$[0-9.]*" | sed 's/Profit: \$//' || echo "$PREDICTED_PROFIT")

                log_structured "INFO" "Sell succeeded, volume: $VOLUME_COINS, profit: \$$ACTUAL_PROFIT" "$USER"
                
                # Send email notification for successful sell
                send_trade_alert "SELL" "$USER" "$VOLUME_COINS" "$PRICE" "$PAIR" "$ACTUAL_PROFIT"
                
                output_result "success" "$USER" "$VOLUME_COINS" "$PRICE" "$ACTUAL_PROFIT" "$ORDER_ID" ""
            fi
        else
            log_structured "INFO" "Sell skipped, lock exists" "$USER"
            output_result "error" "$USER" "" "" "" "" "Sell lock exists"
        fi
    else
        ERROR_MSG="Invalid action: $ACTION. Use 'buy', 'sell', or 'balance'."
        log_structured "ERROR" "$ERROR_MSG" "system"
        output_result "error" "system" "" "" "" "" "$ERROR_MSG"
        exit 1
    fi

    # Performance monitoring per user
    USER_END_TIME=$(date +%s.%N)
    USER_EXECUTION_TIME=$(echo "$USER_END_TIME - $USER_START_TIME" | bc -l)
    log_structured "INFO" "Execution time: ${USER_EXECUTION_TIME}s" "$USER"
done

# Overall performance monitoring
SCRIPT_END_TIME=$(date +%s.%N)
TOTAL_EXECUTION_TIME=$(echo "$SCRIPT_END_TIME - $SCRIPT_START_TIME" | bc -l)
log_structured "INFO" "Total gobbler.sh execution time: ${TOTAL_EXECUTION_TIME}s" "system"

exit 0

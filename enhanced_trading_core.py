# enhanced_trading_core.py
# Version: 1.0 - Core utilities with atomic JSON writes and profit tracking
# Contains: Atomic JSON functions, balance functions, bootstrap functions, real profit tracking
# CRITICAL: Preserves all existing functionality while adding atomic JSON corruption prevention

import pandas as pd
import numpy as np
import os
import time
import subprocess
import json
import csv
import tempfile
import shutil
import glob
from datetime import datetime, timedelta
from config import args, PAIR, DYNAMIC_PARAMS, DEPENDENCY_DIR, RUN_ID, TIMEFRAMES_TO_EVALUATE
from logging_setup import logger, debug_logger
import traceback

# ============================================================================
# ATOMIC JSON FUNCTIONS - NEW: Prevents file corruption during writes
# ============================================================================

def safe_json_dumps(obj):
    """Safely serialize objects with numpy types to JSON"""
    def convert_types(obj):
        if hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        return obj

    return json.dumps(convert_types(obj))

def safe_json_convert(obj):
    """Convert objects with numpy types for JSON serialization (for json.dump)"""
    def convert_types(obj):
        if hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        return obj

    return convert_types(obj)

def atomic_json_write(filepath, data, indent=2):
    """
    Atomically write JSON data to file to prevent corruption
    Uses temporary file + atomic move for guaranteed consistency
    """
    try:
        # Create temp file in same directory to ensure atomic move works
        temp_file = filepath + '.tmp'

        # Write to temporary file first
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(safe_json_convert(data), f, indent=indent, ensure_ascii=False)

        # Atomic move - only happens if write completely succeeded
        shutil.move(temp_file, filepath)
        logger.debug(f"Atomic JSON write successful: {filepath}")
        return True

    except Exception as e:
        # Clean up temp file on any error
        if 'temp_file' in locals() and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        logger.error(f"Atomic JSON write failed for {filepath}: {e}")
        return False

def safe_backup_and_write(filepath, data, indent=2, keep_backups=3):
    """
    Backup existing file before writing new data with atomic operations
    Creates timestamped backups and cleans up old ones
    """
    try:
        # Create backup if file exists
        if os.path.exists(filepath):
            backup_file = f"{filepath}.backup.{int(time.time())}"
            shutil.copy2(filepath, backup_file)
            logger.debug(f"Created backup: {backup_file}")

            # Clean up old backups (keep only recent ones)
            backup_pattern = f"{filepath}.backup.*"
            backups = sorted(glob.glob(backup_pattern))
            if len(backups) > keep_backups:
                for old_backup in backups[:-keep_backups]:
                    try:
                        os.remove(old_backup)
                        logger.debug(f"Cleaned up old backup: {old_backup}")
                    except:
                        pass

        # Write new data atomically
        return atomic_json_write(filepath, data, indent)

    except Exception as e:
        logger.error(f"Safe backup and write failed for {filepath}: {e}")
        return False

# ============================================================================
# BALANCE AND EXCHANGE FUNCTIONS - Enhanced multi-user support
# ============================================================================

def extract_quote_currency(pair):
    """Extract quote currency from trading pair (e.g., ADAUSDT -> USDT)"""
    quote_currencies = ["USDT", "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "XBT", "BTC", "ETH"]
    pair_upper = pair.upper()
    for quote in quote_currencies:
        if pair_upper.endswith(quote):
            return quote
    return "USD"  # fallback

def get_all_user_balances(pair):
    """Get detailed per-user balances from ALL exchange accounts via gobbler.sh - DYNAMIC USER DETECTION"""
    try:
        gobbler_script = os.path.join(DEPENDENCY_DIR, "dependencies_v1", "gobbler.sh")
        if not os.path.exists(gobbler_script):
            # Try current directory
            gobbler_script = "gobbler.sh"
            if not os.path.exists(gobbler_script):
                # Try dependencies directory
                gobbler_script = os.path.join("dependencies_v1", "gobbler.sh")

        # Get aggregated balances first to extract user data
        balance_cmd = [gobbler_script, "balance", pair, "--format=json"]

        logger.info(f"Checking DYNAMIC MULTI-USER exchange balances: {' '.join(balance_cmd)}")

        result = subprocess.run(balance_cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            try:
                # Parse the full output to extract per-user information
                output_lines = result.stdout.strip().split('\n')
                json_line = None
                user_balances = {}

                # Find JSON line and parse user balance lines
                for line in output_lines:
                    if line.startswith('{"status"'):
                        json_line = line
                    elif 'User ' in line and ':' in line:
                        # Parse lines like: "User mason: $87.96921078 USDT, 0.0 ADA"
                        try:
                            parts = line.split('User ')[1]
                            user_part, balance_part = parts.split(':')
                            username = user_part.strip()

                            # Extract USD amount
                            if ' USDT' in balance_part:
                                usd_amount = float(balance_part.split(' USDT')[0].replace('$', '').replace(',', ''))
                            elif ' USD' in balance_part:
                                usd_amount = float(balance_part.split(' USD')[0].replace('$', '').replace(',', ''))
                            else:
                                usd_amount = 0.0

                            # Extract base currency amount
                            if ', ' in balance_part:
                                base_part = balance_part.split(', ')[1]
                                if ' ADA' in base_part:
                                    base_amount = float(base_part.split(' ADA')[0])
                                else:
                                    base_amount = 0.0
                            else:
                                base_amount = 0.0

                            user_balances[username] = {
                                'usd': usd_amount,
                                'base': base_amount,
                                'has_funds': usd_amount > 0.5 or base_amount > 0.01  # Lower minimum for real tracking
                            }

                        except Exception as e:
                            logger.warning(f"Could not parse user balance line: {line} - {e}")
                            continue

                if json_line:
                    balance_data = json.loads(json_line)
                    total_usd = float(balance_data.get('available_usd', 0))
                    total_base = float(balance_data.get('available_base', 0))
                    active_users = balance_data.get('active_users', 0)
                else:
                    # Fallback: calculate totals from parsed user data
                    total_usd = sum(user['usd'] for user in user_balances.values())
                    total_base = sum(user['base'] for user in user_balances.values())
                    active_users = len([u for u in user_balances.values() if u['has_funds']])

                # Log detailed per-user balances
                logger.info(f"💰 DYNAMIC Multi-Account Balance Check:")
                for username, balance in user_balances.items():
                    status = "✅ Available for trading" if balance['has_funds'] else "❌ Insufficient funds, skipping"
                    logger.info(f"   {username}: ${balance['usd']:.2f} USD, {balance['base']:.4f} {pair.replace('USDT', '').replace('USD', '')} {status}")

                logger.info(f"   TOTAL: ${total_usd:.2f} across {active_users} active accounts")

                return {
                    'usd': total_usd,
                    'base': total_base,
                    'active_users': active_users,
                    'user_balances': user_balances,
                    'success': True
                }

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse balance JSON: {e}")
                logger.error(f"Raw output: {result.stdout}")
                return {'usd': 0, 'base': 0, 'success': False, 'error': 'json_parse_error', 'user_balances': {}}
        else:
            logger.error(f"Balance check failed: {result.stderr}")
            return {'usd': 0, 'base': 0, 'success': False, 'error': 'command_failed', 'user_balances': {}}

    except Exception as e:
        logger.error(f"Error getting exchange balances: {e}")
        return {'usd': 0, 'base': 0, 'success': False, 'error': str(e), 'user_balances': {}}

def get_actual_exchange_balances(pair):
    """Get actual balances from ALL exchange accounts via gobbler.sh - ENHANCED MULTI-USER"""
    # Use the enhanced function and return compatible format
    enhanced_result = get_all_user_balances(pair)
    return {
        'usd': enhanced_result['usd'],
        'base': enhanced_result['base'],
        'active_users': enhanced_result.get('active_users', 0),
        'user_balances': enhanced_result.get('user_balances', {}),
        'success': enhanced_result['success']
    }

# ============================================================================
# BOOTSTRAP FUNCTIONS - Enhanced with atomic writes
# ============================================================================

def get_bootstrap_confluence_threshold():
    """Get current confluence threshold based on bootstrap state and learning progress - AGGRESSIVE MODE + DYNAMIC AWARE"""
    try:
        # Try to import config functions, with fallbacks
        try:
            from config import load_confluence_state, save_confluence_state, PAIR, DYNAMIC_PARAMS
        except ImportError:
            logger.warning("Config functions not available, using fallback threshold")
            return 0.02  # AGGRESSIVE fallback

        confluence_state = load_confluence_state(PAIR)

        # Get current state
        bootstrap_mode = confluence_state.get('bootstrap_mode', True)
        trades_completed = confluence_state.get('trades_completed', 0)
        bootstrap_trades_needed = DYNAMIC_PARAMS.get('bootstrap_trades_needed', 1)  # AGGRESSIVE: Only need 1 trade

        if bootstrap_mode and trades_completed < bootstrap_trades_needed:
            # AGGRESSIVE BOOTSTRAP MODE: Start ultra-relaxed for micro-trading
            progress = trades_completed / bootstrap_trades_needed
            start_threshold = DYNAMIC_PARAMS.get('min_confluence', 0.02)  # AGGRESSIVE: 0.02
            target_threshold = DYNAMIC_PARAMS.get('target_min_confluence', 0.05)  # AGGRESSIVE: 0.05

            # Exponential learning curve (but already very low)
            current_threshold = start_threshold + (target_threshold - start_threshold) * (progress ** 0.7)

            logger.info(f"AGGRESSIVE BOOTSTRAP MODE: {trades_completed}/{bootstrap_trades_needed} trades, "
                       f"threshold: {current_threshold:.3f} (progress: {progress:.1%})")

            # Update state with atomic write
            confluence_state['current_parameters']['min_confluence'] = current_threshold
            save_confluence_state(PAIR, confluence_state)

            return current_threshold

        elif bootstrap_mode and trades_completed >= bootstrap_trades_needed:
            # TRANSITION TO AGGRESSIVE REGULAR MODE
            target_threshold = DYNAMIC_PARAMS.get('target_min_confluence', 0.05)  # AGGRESSIVE: 0.05

            logger.info(f"BOOTSTRAP COMPLETE: Transitioning to aggressive mode with threshold: {target_threshold:.3f}")

            # Update to regular mode with atomic write
            confluence_state['bootstrap_mode'] = False
            confluence_state['current_parameters']['min_confluence'] = target_threshold
            save_confluence_state(PAIR, confluence_state)

            return target_threshold

        else:
            # AGGRESSIVE REGULAR MODE: Use adaptive learning with REAL PROFITS
            performance_history = confluence_state.get('performance_history', [])
            current_threshold = confluence_state.get('current_parameters', {}).get('min_confluence', 0.05)

            if len(performance_history) >= 5:
                # Analyze recent REAL performance (not predictions)
                recent_performance = performance_history[-10:]  # Last 10 trades
                real_profit_trades = [trade for trade in recent_performance if trade.get('is_real_profit', False)]

                if real_profit_trades:
                    # Calculate win rate based on REAL profits
                    win_rate = sum(1 for trade in real_profit_trades if trade.get('profit', 0) > 0) / len(real_profit_trades)
                    avg_profit = sum(trade.get('profit', 0) for trade in real_profit_trades) / len(real_profit_trades)

                    logger.info(f"REAL PERFORMANCE: {len(real_profit_trades)} completed trades, "
                               f"win rate: {win_rate:.1%}, avg profit: ${avg_profit:.2f}")
                else:
                    # No real profits yet, use all trades
                    win_rate = sum(1 for trade in recent_performance if trade.get('profit', 0) > 0) / len(recent_performance)

                # AGGRESSIVE: More tolerant adaptive adjustment based on REAL results
                if win_rate > 0.7:
                    # High win rate - can tighten threshold slightly (but keep it low)
                    adjusted_threshold = min(0.08, current_threshold + 0.01)  # Max 0.08
                    logger.info(f"AGGRESSIVE MODE: High REAL win rate ({win_rate:.1%}) - slight tightening to {adjusted_threshold:.3f}")
                elif win_rate < 0.3:  # AGGRESSIVE: Lower bar (0.3 vs 0.4)
                    # Low win rate - relax threshold
                    adjusted_threshold = max(0.01, current_threshold - 0.01)  # Min 0.01
                    logger.info(f"AGGRESSIVE MODE: Low REAL win rate ({win_rate:.1%}) - relaxing threshold to {adjusted_threshold:.3f}")
                else:
                    adjusted_threshold = current_threshold
                    logger.info(f"AGGRESSIVE MODE: Balanced REAL win rate ({win_rate:.1%}) - maintaining threshold: {adjusted_threshold:.3f}")

                # Update state with atomic write
                confluence_state['current_parameters']['min_confluence'] = adjusted_threshold
                save_confluence_state(PAIR, confluence_state)

                return adjusted_threshold
            else:
                logger.info(f"AGGRESSIVE MODE: Using target threshold: {current_threshold:.3f} (insufficient history)")
                return current_threshold

    except Exception as e:
        logger.warning(f"Could not get bootstrap threshold: {e}")
        # AGGRESSIVE fallback
        return 0.02  # AGGRESSIVE: Ultra-low fallback

def update_bootstrap_trade_results_with_real_profit(trade_result):
    """Updated function that uses REAL profits instead of predictions with atomic writes"""
    try:
        try:
            from config import load_confluence_state, save_confluence_state, PAIR
        except ImportError:
            logger.warning("Config functions not available, skipping bootstrap update")
            return

        if not trade_result:
            return

        confluence_state = load_confluence_state(PAIR)

        # Increment trade count
        confluence_state['trades_completed'] = confluence_state.get('trades_completed', 0) + 1

        # Add to performance history
        if 'performance_history' not in confluence_state:
            confluence_state['performance_history'] = []

        # Get REAL profit from trade execution
        real_profit = 0.0
        is_real_profit = False

        if trade_result.get('signal') == 'sell':
            # For sell trades, calculate real profit
            real_profit = trade_result.get('total_real_profit', 0.0)
            is_real_profit = True
        else:
            # For buy trades, profit is 0 until sold
            real_profit = 0.0
            is_real_profit = False

        trade_record = {
            'timestamp': trade_result.get('timestamp', datetime.now()).isoformat(),
            'signal': trade_result.get('signal', 'unknown'),
            'confidence': trade_result.get('enhanced_confidence', 0.5),
            'confluence_strength': trade_result.get('confluence_strength', 0.0),
            'profit': real_profit,  # REAL profit, not predicted
            'threshold_used': trade_result.get('dynamic_threshold_used', 0.02),
            'is_real_profit': is_real_profit,  # Flag real vs pending
            'signal_driven_exit': trade_result.get('signal_driven_mode', False)  # NEW: Track signal-driven mode
        }

        confluence_state['performance_history'].append(trade_record)

        # Keep only recent history
        if len(confluence_state['performance_history']) > 50:
            confluence_state['performance_history'] = confluence_state['performance_history'][-50:]

        confluence_state['last_adaptation'] = datetime.now().isoformat()

        # Save with atomic write
        save_confluence_state(PAIR, confluence_state)

        bootstrap_mode = confluence_state.get('bootstrap_mode', True)
        trades_completed = confluence_state.get('trades_completed', 0)

        logger.info(f"📊 UPDATED BOOTSTRAP with REAL DATA + SIGNAL-DRIVEN: {trades_completed} trades, "
                   f"mode: {'BOOTSTRAP' if bootstrap_mode else 'AGGRESSIVE'}, "
                   f"real_profit: ${trade_record['profit']:.4f}")

    except Exception as e:
        logger.error(f"Error updating bootstrap trade results: {e}")

def save_confluence_state(pair, state):
    """Save confluence state with atomic writes"""
    try:
        confluence_file = os.path.join(DEPENDENCY_DIR, f"confluence_adaptation_{pair.lower().replace('/', '').replace('usdt', '').replace('usd', '')}.json")
        
        # Ensure directories exist
        os.makedirs(DEPENDENCY_DIR, exist_ok=True)
        
        # Use atomic write with backup
        return safe_backup_and_write(confluence_file, state)

    except Exception as e:
        logger.error(f"Error saving confluence state: {e}")
        return False

# ============================================================================
# REAL PROFIT TRACKING SYSTEM - Enhanced with atomic writes
# ============================================================================

def initialize_trade_history():
    """Initialize trade history CSV with proper headers"""
    trade_history_file = os.path.join(DEPENDENCY_DIR, "trade_history.csv")

    if not os.path.exists(trade_history_file):
        with open(trade_history_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'trade_id', 'timestamp', 'pair', 'user', 'action', 'volume',
                'price', 'total_usd', 'fees', 'order_id', 'signal_confidence',
                'confluence_strength', 'market_regime', 'is_closed', 'buy_trade_id'
            ])
        logger.info(f"Initialized trade history: {trade_history_file}")

    return trade_history_file

def generate_trade_id():
    """Generate unique trade ID"""
    return f"trade_{int(datetime.now().timestamp())}_{os.getpid()}"

def record_trade_execution(trade_details, gobbler_result):
    """Record actual trade execution with real data from gobbler.sh"""
    try:
        trade_history_file = initialize_trade_history()

        # Extract real execution data from gobbler results
        user_results = gobbler_result.get('user_results', {})

        recorded_trades = []

        for username, result in user_results.items():
            if result.get('status') not in ['success', 'success_no_json']:
                continue

            # Get actual trade data from gobbler.sh result
            trade_result = result.get('trade_result', {})

            trade_record = {
                'trade_id': generate_trade_id(),
                'timestamp': datetime.now().isoformat(),
                'pair': trade_details['pair'],
                'user': username,
                'action': trade_details['signal'],  # 'buy' or 'sell'
                'volume': result.get('volume', 0),
                'price': trade_details['price'],  # Market price at execution
                'total_usd': result.get('amount', 0),  # Actual USD amount
                'fees': 0,  # Will be extracted from actual trade response
                'order_id': trade_result.get('order_id', 'unknown'),
                'signal_confidence': trade_details.get('confidence', 0),
                'confluence_strength': trade_details.get('confluence_strength', 0),
                'market_regime': trade_details.get('market_regime', 'unknown'),
                'is_closed': False,  # Still open position
                'buy_trade_id': ''  # Will link sells to buys
            }

            # Extract actual fees from gobbler response if available
            if 'executed_price' in trade_result:
                trade_record['price'] = float(trade_result['executed_price'])
            if 'fees' in trade_result:
                trade_record['fees'] = float(trade_result['fees'])

            # Record the trade
            with open(trade_history_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=trade_record.keys())
                writer.writerow(trade_record)

            recorded_trades.append(trade_record)

            logger.info(f"📝 RECORDED REAL TRADE: {username} {trade_details['signal'].upper()} "
                       f"{trade_record['volume']:.4f} {trade_details['pair']} at ${trade_record['price']:.4f}")

        return recorded_trades

    except Exception as e:
        logger.error(f"Error recording trade execution: {e}")
        return []

def calculate_real_profit(sell_trade, buy_trades):
    """Calculate real profit from actual buy/sell prices - NO ASSUMPTIONS"""
    try:
        if not buy_trades:
            logger.warning("No matching buy trades found for profit calculation")
            return 0.0, "No matching buy trades"

        # Use FIFO (First In, First Out) accounting
        remaining_sell_volume = float(sell_trade['volume'])
        total_cost_basis = 0.0
        total_bought_volume = 0.0
        fees_paid = 0.0

        for buy_trade in buy_trades:
            if remaining_sell_volume <= 0:
                break

            buy_volume = float(buy_trade['volume'])
            buy_price = float(buy_trade['price'])
            buy_fees = float(buy_trade.get('fees', 0))

            # How much of this buy order applies to current sell
            volume_to_use = min(remaining_sell_volume, buy_volume)

            # Calculate cost basis for this portion
            cost_basis = volume_to_use * buy_price
            total_cost_basis += cost_basis
            total_bought_volume += volume_to_use
            fees_paid += (buy_fees * volume_to_use / buy_volume)  # Proportional fees

            remaining_sell_volume -= volume_to_use

            logger.debug(f"FIFO calculation: Used {volume_to_use:.4f} from buy at ${buy_price:.4f}")

        # Calculate profit from actual prices
        sell_volume = float(sell_trade['volume'])
        sell_price = float(sell_trade['price'])
        sell_fees = float(sell_trade.get('fees', 0))

        sell_proceeds = sell_volume * sell_price
        total_fees = fees_paid + sell_fees

        # Real profit = proceeds - cost - fees
        real_profit = sell_proceeds - total_cost_basis - total_fees
        profit_percentage = (real_profit / total_cost_basis * 100) if total_cost_basis > 0 else 0

        profit_details = {
            'sell_proceeds': sell_proceeds,
            'cost_basis': total_cost_basis,
            'total_fees': total_fees,
            'profit_usd': real_profit,
            'profit_percentage': profit_percentage,
            'volume_sold': sell_volume,
            'avg_buy_price': total_cost_basis / total_bought_volume if total_bought_volume > 0 else 0,
            'sell_price': sell_price
        }

        logger.info(f"💰 REAL PROFIT CALCULATED:")
        logger.info(f"   Sold: {sell_volume:.4f} at ${sell_price:.4f} = ${sell_proceeds:.2f}")
        logger.info(f"   Cost: ${total_cost_basis:.2f} (avg: ${profit_details['avg_buy_price']:.4f})")
        logger.info(f"   Fees: ${total_fees:.2f}")
        logger.info(f"   PROFIT: ${real_profit:.2f} ({profit_percentage:.2f}%)")

        return real_profit, profit_details

    except Exception as e:
        logger.error(f"Error calculating real profit: {e}")
        return 0.0, f"Calculation error: {str(e)}"

def process_sell_trade_profit(sell_trade_record):
    """Process a sell trade and calculate real profit against previous buys"""
    try:
        trade_history_file = os.path.join(DEPENDENCY_DIR, "trade_history.csv")

        if not os.path.exists(trade_history_file):
            logger.warning("No trade history file found")
            return 0.0

        # Read all trades for this user and pair
        user = sell_trade_record['user']
        pair = sell_trade_record['pair']

        buy_trades = []

        with open(trade_history_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row['user'] == user and
                    row['pair'] == pair and
                    row['action'] == 'buy' and
                    row['is_closed'] == 'False'):
                    buy_trades.append(row)

        if not buy_trades:
            logger.warning(f"No open buy positions found for {user} {pair}")
            return 0.0

        # Sort by timestamp (FIFO)
        buy_trades.sort(key=lambda x: x['timestamp'])

        # Calculate real profit
        real_profit, profit_details = calculate_real_profit(sell_trade_record, buy_trades)

        # Mark buy positions as closed and record profit
        sell_volume_remaining = float(sell_trade_record['volume'])

        updated_rows = []
        with open(trade_history_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row['user'] == user and
                    row['pair'] == pair and
                    row['action'] == 'buy' and
                    row['is_closed'] == 'False' and
                    sell_volume_remaining > 0):

                    buy_volume = float(row['volume'])
                    volume_closed = min(sell_volume_remaining, buy_volume)

                    if volume_closed >= buy_volume * 0.99:  # Close if >99% sold
                        row['is_closed'] = 'True'

                    sell_volume_remaining -= volume_closed

                updated_rows.append(row)

        # Write back updated data
        with open(trade_history_file, 'w', newline='') as f:
            if updated_rows:
                writer = csv.DictWriter(f, fieldnames=updated_rows[0].keys())
                writer.writeheader()
                writer.writerows(updated_rows)

        # Log profit to separate file with atomic write protection
        profit_log_file = os.path.join(DEPENDENCY_DIR, "realized_profits.csv")
        profit_record = {
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'pair': pair,
            'sell_trade_id': sell_trade_record['trade_id'],
            'real_profit_usd': real_profit,
            'profit_details': safe_json_dumps(profit_details) if isinstance(profit_details, dict) else str(profit_details)
        }

        # Initialize profit log if needed
        if not os.path.exists(profit_log_file):
            with open(profit_log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=profit_record.keys())
                writer.writeheader()

        # Record realized profit
        with open(profit_log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=profit_record.keys())
            writer.writerow(profit_record)

        return real_profit

    except Exception as e:
        logger.error(f"Error processing sell trade profit: {e}")
        return 0.0

# ============================================================================
# UTILITY FUNCTIONS - Enhanced model integration
# ============================================================================

def get_trained_model_predictions(pair, timeframes, live_data):
    """Get predictions from actually trained models instead of using stored values"""
    try:
        from models import load_saved_model, enhanced_make_predictions

        all_predictions = {}
        all_confidences = {}

        for tf in timeframes:
            if tf not in live_data or live_data[tf].empty:
                continue

            try:
                # Load the actual trained model
                model, features, encoders, modifications = load_saved_model(tf)

                if model is not None:
                    logger.info(f"✅ Loaded trained model for {tf}")

                    # Get latest data for prediction
                    df = live_data[tf].tail(1)  # Use latest row

                    # Make actual predictions using the trained model
                    predictions, confidences = enhanced_make_predictions(
                        model, df, encoders, modifications, features
                    )

                    all_predictions[tf] = predictions
                    all_confidences[tf] = confidences

                    logger.info(f"🎯 {tf}: pred={predictions.iloc[-1]}, conf={confidences.iloc[-1]:.3f}")

                else:
                    logger.warning(f"❌ No trained model available for {tf}")

            except Exception as e:
                logger.error(f"Error loading model for {tf}: {e}")
                continue

        return all_predictions, all_confidences

    except Exception as e:
        logger.error(f"Error in get_trained_model_predictions: {e}")
        return {}, {}

def get_bootstrap_aware_ml_confluence_threshold(df, market_regime_data, current_confluence,
                                               participating_timeframes, all_confidences, pair):
    """ML confluence threshold that properly respects bootstrap state + INTEGRATES TRAINED MODELS - AGGRESSIVE MODE"""
    try:
        # Get the current bootstrap threshold as baseline
        bootstrap_threshold = get_bootstrap_confluence_threshold()

        # Try to import ML functions
        try:
            from dynamic_confluence_ml import get_dynamic_confluence_threshold
            ML_CONFLUENCE_AVAILABLE = True
        except ImportError:
            ML_CONFLUENCE_AVAILABLE = False

        if ML_CONFLUENCE_AVAILABLE:
            try:
                # CRITICAL FIX: Check if we have trained models available
                from models import load_saved_model

                models_available = []
                for tf in participating_timeframes:
                    model, features, encoders, modifications = load_saved_model(tf)
                    if model is not None:
                        models_available.append(tf)

                if models_available:
                    logger.info(f"🎯 Found trained models for: {models_available}")
                else:
                    logger.warning("⚠️ No trained models found - using bootstrap only")

                # Try to get ML optimization (enhanced with model awareness)
                confluence_result = get_dynamic_confluence_threshold(
                    df=df,
                    market_regime_data=market_regime_data,
                    current_confluence=current_confluence,
                    participating_timeframes=participating_timeframes,
                    all_confidences=all_confidences,
                    pair=pair
                )

                ml_threshold = confluence_result['threshold']

                # AGGRESSIVE FIX: Always use the lower threshold for more trading
                try:
                    from config import load_confluence_state
                    confluence_state = load_confluence_state(pair)
                    bootstrap_mode = confluence_state.get('bootstrap_mode', True)
                except ImportError:
                    bootstrap_mode = True  # Default to bootstrap mode if config unavailable

                if bootstrap_mode:
                    # In bootstrap mode, use the minimum threshold for maximum trading
                    final_threshold = min(bootstrap_threshold, ml_threshold, 0.02)  # Force ultra-low
                    logger.info(f"AGGRESSIVE BOOTSTRAP-AWARE ML: ML={ml_threshold:.3f}, Bootstrap={bootstrap_threshold:.3f}, Using={final_threshold:.3f}")
                    constrained = final_threshold < ml_threshold
                else:
                    # In regular mode, still prioritize low thresholds
                    final_threshold = min(ml_threshold, 0.05)  # Cap at 0.05 for aggressive trading
                    logger.info(f"AGGRESSIVE ML-Optimized Threshold: {final_threshold:.3f} (regular mode)")
                    constrained = False

                return {
                    'threshold': final_threshold,
                    'market_features': confluence_result.get('market_features', {}),
                    'bootstrap_constrained': constrained,
                    'ml_successful': True,
                    'aggressive_mode': True,
                    'models_available': len(models_available),
                    'optimizer': confluence_result.get('optimizer')  # Pass optimizer for logging
                }

            except Exception as e:
                logger.warning(f"ML confluence failed, using aggressive bootstrap: {e}")
                return {
                    'threshold': min(bootstrap_threshold, 0.02),  # Force ultra-low
                    'market_features': {},
                    'bootstrap_fallback': True,
                    'ml_successful': False,
                    'aggressive_mode': True
                }
        else:
            # No ML available, use aggressive bootstrap
            aggressive_threshold = min(bootstrap_threshold, 0.02)
            logger.info(f"AGGRESSIVE Bootstrap Confluence: {aggressive_threshold:.3f} (ML not available)")
            return {
                'threshold': aggressive_threshold,
                'market_features': {},
                'ml_available': False,
                'ml_successful': False,
                'aggressive_mode': True
            }

    except Exception as e:
        logger.error(f"Error in bootstrap-aware ML confluence: {e}")
        return {
            'threshold': 0.01,  # AGGRESSIVE: Ultra-safe bootstrap default
            'market_features': {},
            'error': str(e),
            'ml_successful': False,
            'aggressive_mode': True
        }

# Export all functions
__all__ = [
    # Atomic JSON functions
    'atomic_json_write',
    'safe_backup_and_write', 
    'safe_json_dumps',
    'safe_json_convert',
    
    # Balance functions
    'extract_quote_currency',
    'get_all_user_balances',
    'get_actual_exchange_balances',
    
    # Bootstrap functions  
    'get_bootstrap_confluence_threshold',
    'update_bootstrap_trade_results_with_real_profit',
    'save_confluence_state',
    
    # Real profit tracking
    'initialize_trade_history',
    'generate_trade_id',
    'record_trade_execution',
    'calculate_real_profit',
    'process_sell_trade_profit',
    
    # Utility functions
    'get_trained_model_predictions',
    'get_bootstrap_aware_ml_confluence_threshold'
]

logger.info("✅ enhanced_trading_core.py v1.0 loaded successfully with atomic JSON protection and all core utilities")

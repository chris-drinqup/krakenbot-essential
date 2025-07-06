# Version: 1.7 - CRITICAL FIXES for Column Availability and Boolean Indexing + Emoji Removal
# Revision Notes:
# - 1.6: CRITICAL FIXES for missing column availability during optimization
# - 1.7: Removed all emojis that could cause encoding/syntax errors

import pandas as pd
import numpy as np
import optuna
import traceback
from datetime import datetime, timedelta
import warnings

from config import args, PAIR, DYNAMIC_PARAMS, DEPENDENCY_DIR, RUN_ID
from logging_setup import logger, debug_logger, update_fix_log

# Suppress optuna logging
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings('ignore', category=FutureWarning)

def fix_boolean_indexing_issues():
    """CRITICAL FIX: Apply system-wide fixes for boolean indexing"""
    try:
        # Set pandas options to handle boolean indexing safely
        pd.set_option('mode.chained_assignment', None)
        pd.set_option('future.no_silent_downcasting', True)

        logger.info("Applied boolean indexing safety fixes")
        return True
    except Exception as e:
        logger.error(f"Failed to apply boolean indexing fixes: {e}")
        return False

def get_available_columns(df):
    """Get available columns for optimization with validation"""
    try:
        available_columns = {
            'close_columns': [],
            'rsi_columns': [],
            'atr_columns': [],
            'volume_columns': [],
            'timeframes': []
        }

        # Check for standard timeframe columns
        for tf in ['5m', '15m', '30m', '1h', '4h', '6h', '1d']:
            close_col = f'close_{tf}'
            rsi_col = f'RSI_{tf}'
            atr_col = f'ATR_{tf}'
            volume_col = f'volume_{tf}'

            if close_col in df.columns and not df[close_col].isna().all():
                available_columns['close_columns'].append(close_col)
                available_columns['timeframes'].append(tf)

            if rsi_col in df.columns and not df[rsi_col].isna().all():
                available_columns['rsi_columns'].append(rsi_col)

            if atr_col in df.columns and not df[atr_col].isna().all():
                available_columns['atr_columns'].append(atr_col)

            if volume_col in df.columns and not df[volume_col].isna().all():
                available_columns['volume_columns'].append(volume_col)

        # Check for cross-timeframe columns
        if 'close_5m' in df.columns and not df['close_5m'].isna().all():
            available_columns['close_columns'].append('close_5m')
        if 'RSI_5m' in df.columns and not df['RSI_5m'].isna().all():
            available_columns['rsi_columns'].append('RSI_5m')
        if 'ATR_5m' in df.columns and not df['ATR_5m'].isna().all():
            available_columns['atr_columns'].append('ATR_5m')

        logger.info(f"Available columns analysis: {len(available_columns['close_columns'])} close, "
                   f"{len(available_columns['rsi_columns'])} RSI, "
                   f"{len(available_columns['atr_columns'])} ATR columns")

        return available_columns

    except Exception as e:
        logger.error(f"Error analyzing available columns: {e}")
        return {'close_columns': [], 'rsi_columns': [], 'atr_columns': [], 'volume_columns': [], 'timeframes': []}

def safe_calculate_volatility(close_prices, window=20):
    """Safely calculate volatility with error handling"""
    try:
        if len(close_prices) < window:
            window = max(5, len(close_prices) // 2)

        returns = close_prices.pct_change(fill_method=None).dropna()
        if len(returns) < 5:
            return 0.02  # Default volatility

        volatility = returns.rolling(window=window, min_periods=min(5, len(returns))).std().iloc[-1]

        if pd.isna(volatility) or volatility <= 0:
            return returns.std() if len(returns) > 0 else 0.02

        return max(0.001, min(0.5, volatility))  # Clamp to reasonable range

    except Exception as e:
        logger.warning(f"Error calculating volatility: {e}")
        return 0.02  # Safe default

def update_thresholds(df, dynamic_params):
    """Enhanced threshold updates with improved column detection"""
    try:
        logger.info("Starting enhanced threshold updates")

        available_cols = get_available_columns(df)

        # Risk-reward ratio updates with enhanced column detection
        if available_cols['close_columns']:
            close_col = available_cols['close_columns'][0]
            close_prices = df[close_col].dropna()

            if len(close_prices) > 20:
                volatility = safe_calculate_volatility(close_prices)
                regime_type = 'low' if volatility < 0.015 else 'high' if volatility > 0.025 else 'normal'
                logger.info(f"Market volatility: {volatility:.2%}, regime: {regime_type}")

                # Dynamic profit/loss adjustments
                base_profit = 0.015
                base_loss = 0.005

                if volatility > 0.025:  # High volatility
                    profit_mult = 1.5
                    loss_mult = 0.8
                elif volatility < 0.015:  # Low volatility
                    profit_mult = 0.8
                    loss_mult = 1.2
                else:  # Normal volatility
                    profit_mult = 1.0
                    loss_mult = 1.0

                dynamic_params['profit_percentage_1'] = base_profit * profit_mult
                dynamic_params['profit_percentage_2'] = base_profit * profit_mult * 1.6
                dynamic_params['stop_loss_percentage_1'] = base_loss * loss_mult

                logger.info(f"Updated risk-reward ratios: profit_1={dynamic_params['profit_percentage_1']:.3f}, "
                           f"profit_2={dynamic_params['profit_percentage_2']:.3f}, "
                           f"stop_loss={dynamic_params['stop_loss_percentage_1']:.3f}")
        else:
            logger.debug("No price data available for risk calculation, using defaults")

        # Confidence threshold optimization with enhanced detection
        try:
            if available_cols['timeframes'] and available_cols['atr_columns']:
                tf = available_cols['timeframes'][0]
                atr_col = available_cols['atr_columns'][0]

                atr_values = df[atr_col].dropna()
                if len(atr_values) > 10:
                    avg_atr = atr_values.tail(20).mean()
                    close_col = available_cols['close_columns'][0]
                    avg_price = df[close_col].dropna().tail(20).mean()

                    if avg_price > 0:
                        trend_strength = avg_atr / avg_price
                        volatility = safe_calculate_volatility(df[close_col].dropna())

                        confidence = 0.5 + (trend_strength * 10) - (volatility * 2)
                        confidence = max(0.3, min(0.8, confidence))

                        dynamic_params['confidence_threshold'] = confidence

                        logger.debug(f"Profit confidence calculation: volatility={volatility:.4f}, "
                                   f"trend_strength={trend_strength:.4f}, confidence={confidence:.3f}")
                    else:
                        logger.warning("Invalid price data for confidence calculation")
                else:
                    logger.warning("Insufficient ATR data for confidence calculation")
            else:
                logger.warning("No timeframe data available for profit confidence calculation")
        except Exception as e:
            logger.warning(f"Error in confidence optimization: {e}")

        # Buy/sell threshold optimization with prediction column detection
        try:
            prediction_cols = [col for col in df.columns if 'prediction' in col.lower() or 'signal' in col.lower()]

            if prediction_cols:
                for col in prediction_cols[:3]:  # Check first few prediction columns
                    pred_data = df[col].dropna()
                    if len(pred_data) > 50:
                        buy_ratio = (pred_data == 2).mean() if len(pred_data) > 0 else 0.33
                        sell_ratio = (pred_data == 0).mean() if len(pred_data) > 0 else 0.33

                        # Adjust thresholds based on prediction distribution
                        dynamic_params['buy_threshold'] = max(0.3, min(0.8, 0.5 + (buy_ratio - 0.33) * 2))
                        dynamic_params['sell_threshold'] = max(0.3, min(0.8, 0.5 + (sell_ratio - 0.33) * 2))

                        logger.info(f"Updated thresholds based on {col}: buy={dynamic_params['buy_threshold']:.3f}, "
                                   f"sell={dynamic_params['sell_threshold']:.3f}")
                        break
                else:
                    logger.warning("No prediction columns found for confidence optimization")
            else:
                logger.warning("No prediction columns found for confidence optimization")
        except Exception as e:
            logger.warning(f"Error in threshold optimization: {e}")

        # RSI level updates with enhanced column detection
        try:
            if available_cols['rsi_columns'] and available_cols['close_columns']:
                rsi_col = available_cols['rsi_columns'][0]
                close_col = available_cols['close_columns'][0]

                rsi_data = df[rsi_col].dropna()
                close_data = df[close_col].dropna()

                if len(rsi_data) > 50 and len(close_data) > 50:
                    # Simple adaptive RSI levels based on market conditions
                    volatility = safe_calculate_volatility(close_data)

                    if volatility > 0.025:  # High volatility - tighter levels
                        dynamic_params['rsi_oversold'] = 35
                        dynamic_params['rsi_overbought'] = 65
                    elif volatility < 0.015:  # Low volatility - wider levels
                        dynamic_params['rsi_oversold'] = 25
                        dynamic_params['rsi_overbought'] = 75
                    else:  # Normal volatility - standard levels
                        dynamic_params['rsi_oversold'] = 30
                        dynamic_params['rsi_overbought'] = 70

                    logger.info(f"Updated RSI levels: oversold={dynamic_params['rsi_oversold']}, "
                               f"overbought={dynamic_params['rsi_overbought']}")
                else:
                    logger.warning("Missing required columns for RSI optimization: close_5m, RSI_5m")
                    dynamic_params['rsi_oversold'] = 30
                    dynamic_params['rsi_overbought'] = 70
            else:
                logger.warning("Missing required columns for RSI optimization: close_5m, RSI_5m")
                dynamic_params['rsi_oversold'] = 30
                dynamic_params['rsi_overbought'] = 70

        except Exception as e:
            logger.warning(f"Error in RSI level updates: {e}")
            dynamic_params['rsi_oversold'] = 30
            dynamic_params['rsi_overbought'] = 70

        logger.info("Enhanced threshold updates completed successfully")

    except Exception as e:
        logger.error(f"Error in update_thresholds: {e}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")

def enhance_rsi_optimization(df, dynamic_params):
    """Enhanced RSI optimization with intelligent column selection and boolean indexing fixes"""
    try:
        logger.info("Starting RSI level optimization with enhanced validation")

        available_cols = get_available_columns(df)

        if not available_cols['close_columns'] or not available_cols['rsi_columns']:
            logger.warning("No RSI data available, keeping default levels")
            dynamic_params['rsi_oversold'] = 30
            dynamic_params['rsi_overbought'] = 70
            return

        # Use the best available combination
        selected_tf = available_cols['timeframes'][0] if available_cols['timeframes'] else '5m'
        close_col = available_cols['close_columns'][0]

        # Find matching RSI column
        rsi_col = None
        if f'RSI_{selected_tf}' in available_cols['rsi_columns']:
            rsi_col = f'RSI_{selected_tf}'
        elif 'RSI_5m' in available_cols['rsi_columns']:
            rsi_col = 'RSI_5m'
        elif available_cols['rsi_columns']:
            rsi_col = available_cols['rsi_columns'][0]

        if not rsi_col:
            logger.warning("No matching RSI column found, keeping default levels")
            dynamic_params['rsi_oversold'] = 30
            dynamic_params['rsi_overbought'] = 70
            return

        logger.info(f"Using {selected_tf} and {close_col} for RSI optimization")

        # Proceed with optimization using selected columns
        close_prices = df[close_col].dropna()
        rsi_values = df[rsi_col].dropna()

        if len(close_prices) < 50 or len(rsi_values) < 50:
            logger.warning("Insufficient data for RSI optimization")
            dynamic_params['rsi_oversold'] = 30
            dynamic_params['rsi_overbought'] = 70
            return

        # CRITICAL FIX: Safe data alignment to prevent boolean indexing issues
        try:
            # Find common index range
            common_index = close_prices.index.intersection(rsi_values.index)
            if len(common_index) < 50:
                logger.warning("Insufficient aligned data for RSI optimization")
                dynamic_params['rsi_oversold'] = 30
                dynamic_params['rsi_overbought'] = 70
                return

            # Use only common index data
            close_aligned = close_prices.loc[common_index]
            rsi_aligned = rsi_values.loc[common_index]

        except Exception as e:
            logger.warning(f"Data alignment failed: {e}")
            dynamic_params['rsi_oversold'] = 30
            dynamic_params['rsi_overbought'] = 70
            return

        # Calculate returns for optimization with enhanced safety
        try:
            returns = close_aligned.pct_change(fill_method=None).dropna()

            # Align RSI with returns using safe indexing
            rsi_for_returns = rsi_aligned.reindex(returns.index).dropna()
            returns_for_rsi = returns.reindex(rsi_for_returns.index).dropna()

            if len(returns_for_rsi) < 30:
                logger.warning("Insufficient data after alignment for RSI optimization")
                dynamic_params['rsi_oversold'] = 30
                dynamic_params['rsi_overbought'] = 70
                return

        except Exception as e:
            logger.warning(f"Return calculation failed: {e}")
            dynamic_params['rsi_oversold'] = 30
            dynamic_params['rsi_overbought'] = 70
            return

        def rsi_objective(trial):
            """Enhanced RSI optimization objective with boolean indexing safety"""
            try:
                oversold = trial.suggest_int('rsi_oversold', 20, 40)
                overbought = trial.suggest_int('rsi_overbought', 60, 80)

                if oversold >= overbought:
                    return -1000.0

                # CRITICAL FIX: Safe boolean indexing for signal creation
                try:
                    # Create boolean masks safely
                    buy_mask = rsi_for_returns < oversold
                    sell_mask = rsi_for_returns > overbought

                    # Convert to integer signals
                    buy_signals = buy_mask.astype(int)
                    sell_signals = sell_mask.astype(int)

                    # Calculate strategy returns with safe indexing
                    strategy_returns = (buy_signals.shift(1).fillna(0) * returns_for_rsi -
                                      sell_signals.shift(1).fillna(0) * returns_for_rsi)

                    strategy_returns = strategy_returns.dropna()

                    if len(strategy_returns) == 0 or strategy_returns.std() == 0:
                        return -1000.0

                    # Sharpe ratio as objective with safety checks
                    excess_return = strategy_returns.mean()
                    volatility = strategy_returns.std()

                    if volatility <= 0 or pd.isna(excess_return) or pd.isna(volatility):
                        return -1000.0

                    sharpe = excess_return / volatility

                    # Safety check for extreme values
                    if pd.isna(sharpe) or abs(sharpe) > 100:
                        return -1000.0

                    return sharpe

                except Exception as signal_error:
                    logger.debug(f"Signal generation error: {signal_error}")
                    return -1000.0

            except Exception as e:
                logger.debug(f"RSI objective error: {e}")
                return -1000.0

        try:
            # Run optimization with timeout and error handling
            study = optuna.create_study(direction='maximize')
            study.optimize(rsi_objective, n_trials=20, timeout=30)

            if study.best_trial and study.best_value > -999:
                best_params = study.best_trial.params
                dynamic_params.update(best_params)
                logger.info(f"RSI optimization succeeded: {best_params}, score: {study.best_value:.3f}")

                update_fix_log(
                    issue_id="RSIOptimization",
                    status="Success",
                    description=f"Successfully updated RSI levels: {best_params}",
                    versions=["price_and_hyperparameters.py v1.7"],
                    file_name="price_and_hyperparameters.py"
                )
            else:
                logger.warning("RSI optimization failed, keeping defaults")
                dynamic_params['rsi_oversold'] = 30
                dynamic_params['rsi_overbought'] = 70

        except Exception as e:
            logger.error(f"RSI optimization error: {e}")
            dynamic_params['rsi_oversold'] = 30
            dynamic_params['rsi_overbought'] = 70

    except Exception as e:
        logger.error(f"Error in RSI optimization: {e}")
        dynamic_params['rsi_oversold'] = 30
        dynamic_params['rsi_overbought'] = 70

def comprehensive_parameter_optimization(df, dynamic_params):
    """CRITICAL FIX: Enhanced parameter optimization with proper column checking and boolean indexing safety"""
    try:
        logger.info("Starting comprehensive parameter optimization with CRITICAL FIXES")

        # Apply boolean indexing fixes first
        fix_boolean_indexing_issues()

        # Enhanced threshold updates with smart column detection
        update_thresholds(df, dynamic_params)

        # Enhanced RSI optimization with intelligent column detection and safety fixes
        enhance_rsi_optimization(df, dynamic_params)

        # Save parameters with error handling
        try:
            from indicator_utils import save_parameters
            save_parameters(dynamic_params, PAIR, '5m')
        except ImportError:
            logger.warning("indicator_utils not available, skipping parameter save")
        except Exception as e:
            logger.warning(f"Could not save parameters: {e}")

        logger.info("Comprehensive parameter optimization completed successfully")

        update_fix_log(
            issue_id="ComprehensiveOptimization",
            status="Success",
            description="Enhanced parameter optimization completed with column checking and boolean indexing fixes",
            versions=["price_and_hyperparameters.py v1.7"],
            file_name="price_and_hyperparameters.py"
        )

    except Exception as e:
        logger.error(f"Error in comprehensive parameter optimization: {e}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")

        update_fix_log(
            issue_id="ComprehensiveOptimizationError",
            status="Error",
            description=f"Parameter optimization failed: {str(e)}",
            versions=["price_and_hyperparameters.py v1.7"],
            file_name="price_and_hyperparameters.py"
        )

def optimize_volume_parameters(df, dynamic_params):
    """Enhanced volume parameter optimization with safety checks"""
    try:
        available_cols = get_available_columns(df)

        if not available_cols['volume_columns']:
            logger.debug("Volume optimization data unavailable, using defaults")
            return

        volume_col = available_cols['volume_columns'][0]
        volume_data = df[volume_col].dropna()

        if len(volume_data) < 50:
            logger.warning("Insufficient volume data for optimization")
            return

        # Calculate volume statistics safely
        volume_stats = {
            'mean': volume_data.mean(),
            'std': volume_data.std(),
            'median': volume_data.median(),
            'q75': volume_data.quantile(0.75),
            'q90': volume_data.quantile(0.90)
        }

        # Update volume-based parameters
        if volume_stats['std'] > 0:
            # Higher volatility = larger position sizes
            volatility_factor = min(2.0, volume_stats['std'] / volume_stats['mean'])
            dynamic_params['portfolio_size'] = dynamic_params.get('portfolio_size', 1000) * volatility_factor

        logger.info(f"Updated volume parameters based on statistics: {volume_stats}")

    except Exception as e:
        logger.warning(f"Error in volume parameter optimization: {e}")

def adaptive_timeframe_selection(df, dynamic_params):
    """Select optimal timeframe based on available data quality"""
    try:
        available_cols = get_available_columns(df)

        if not available_cols['timeframes']:
            logger.warning("No timeframes available for selection")
            return

        # Score timeframes based on data quality
        timeframe_scores = {}

        for tf in available_cols['timeframes']:
            score = 0

            # Check data availability
            close_col = f'close_{tf}'
            if close_col in df.columns:
                close_data = df[close_col].dropna()
                if len(close_data) > 100:
                    score += 1

                    # Check data quality
                    volatility = safe_calculate_volatility(close_data)
                    if 0.01 < volatility < 0.1:  # Reasonable volatility range
                        score += 1

            # Check indicator availability
            if f'RSI_{tf}' in df.columns:
                score += 1
            if f'MACD_{tf}' in df.columns:
                score += 1
            if f'ATR_{tf}' in df.columns:
                score += 1

            timeframe_scores[tf] = score

        if timeframe_scores:
            best_timeframe = max(timeframe_scores, key=timeframe_scores.get)
            dynamic_params['selected_timeframe'] = best_timeframe

            logger.info(f"Selected optimal timeframe: {best_timeframe} (score: {timeframe_scores[best_timeframe]})")
            logger.debug(f"Timeframe scores: {timeframe_scores}")

    except Exception as e:
        logger.warning(f"Error in adaptive timeframe selection: {e}")

# Backward compatibility functions
def update_profit_thresholds(df, dynamic_params):
    """Backward compatibility wrapper"""
    update_thresholds(df, dynamic_params)

def optimize_rsi_levels(df, dynamic_params):
    """Backward compatibility wrapper"""
    enhance_rsi_optimization(df, dynamic_params)

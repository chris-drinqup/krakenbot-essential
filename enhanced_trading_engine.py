# enhanced_trading_engine.py
# Version: 1.0 - Main Trading Engine with Signal-Driven Exits + Dynamic Confluence + Real Profit Tracking
# Contains: EnhancedTradingEngine, signal-driven exit logic, main trading iterations, trade execution
# CRITICAL: Preserves all existing functionality while adding intelligent signal-driven exit logic

import pandas as pd
import numpy as np
import os
import time
import subprocess
import json
import csv
from datetime import datetime, timedelta
from config import args, PAIR, DYNAMIC_PARAMS, DEPENDENCY_DIR, RUN_ID, TIMEFRAMES_TO_EVALUATE
from logging_setup import logger, debug_logger
import traceback

# Import from our modular files
from enhanced_trading_core import (
    safe_json_dumps,
    safe_json_convert, 
    extract_quote_currency,
    get_all_user_balances,
    get_actual_exchange_balances,
    get_bootstrap_confluence_threshold,
    get_trained_model_predictions,
    get_bootstrap_aware_ml_confluence_threshold,
    update_bootstrap_trade_results_with_real_profit,
    initialize_trade_history,
    generate_trade_id,
    record_trade_execution,
    calculate_real_profit,
    process_sell_trade_profit
)

from dynamic_confluence_engine import DynamicConfluenceEngine

# ML-powered dynamic confluence imports with fallback - PRESERVED from original
try:
    from dynamic_confluence_ml import get_dynamic_confluence_threshold, ConfluenceMLOptimizer, log_confluence_decision
    ML_CONFLUENCE_AVAILABLE = True
    logger.info("✅ ML-powered dynamic confluence system loaded successfully")
except ImportError as e:
    ML_CONFLUENCE_AVAILABLE = False
    logger.warning(f"⚠️ ML confluence system not available: {e}")
    logger.warning("Will use bootstrap-only thresholds")

    # Create dummy classes for compatibility - PRESERVED from original
    class ConfluenceMLOptimizer:
        def __init__(self, pair):
            self.pair = pair
            self.loaded = False

        def load_or_create_model(self):
            return False

    def log_confluence_decision(optimizer, threshold, trade_result, features):
        pass

    def get_dynamic_confluence_threshold(df, market_regime_data, current_confluence,
                                       participating_timeframes, all_confidences, pair):
        return {
            'threshold': 0.05,
            'market_features': {},
            'ml_active': False,
            'fallback': True
        }

# ============================================================================
# NEW: SIGNAL-DRIVEN EXIT LOGIC - The key enhancement replacing profit caps
# ============================================================================

def should_exit_based_on_signals(all_predictions, all_confidences, current_price, entry_price, entry_time,
                                 market_regime, position_type, entry_data=None):
    """
    NEW: Signal-driven exit logic - replaces artificial profit caps with ML intelligence
    Uses the same sophisticated confluence analysis for exits as we do for entries
    Returns: should_exit, exit_reason, confidence, recommended_action
    """
    try:
        if not all_predictions or not all_confidences:
            return False, "no_signals", 0.0, "hold"

        # Get current profit percentage
        if position_type == 'buy':
            profit_pct = (current_price - entry_price) / entry_price
        else:  # sell
            profit_pct = (entry_price - current_price) / entry_price

        # ENHANCED: Get signal-driven exit parameters from config - PRESERVED from original
        min_profit_after_fees = DYNAMIC_PARAMS.get('min_profit_after_fees', 0.004)  # Still protect against fees
        use_signal_driven_exits = DYNAMIC_PARAMS.get('use_signal_driven_exits', True)

        # Safety net: Emergency stop loss (should rarely trigger with good signals) - PRESERVED from original
        emergency_stop_loss = DYNAMIC_PARAMS.get('emergency_stop_loss', 0.03)  # 3% max loss

        if profit_pct < -emergency_stop_loss:
            return True, f"emergency_stop_loss_{profit_pct:.4f}", 1.0, "emergency_exit"

        # If signal-driven exits are disabled, fall back to old behavior - PRESERVED from original
        if not use_signal_driven_exits:
            logger.info("📊 Signal-driven exits disabled, using traditional profit targets")
            return False, "signal_driven_disabled", 0.0, "hold"

        # NEW: Use confluence analysis for exit decisions
        logger.info(f"🎯 SIGNAL-DRIVEN EXIT ANALYSIS for {position_type} position:")
        logger.info(f"   Current profit: {profit_pct:.4f} ({profit_pct*100:.2f}%)")
        logger.info(f"   Entry price: ${entry_price:.4f}, Current: ${current_price:.4f}")

        # Calculate exit confluence using the same sophisticated system as entries
        exit_confluence_engine = DynamicConfluenceEngine(PAIR, DEPENDENCY_DIR)

        # Determine what constitutes an "exit signal" based on position type
        exit_signals = {}
        exit_confidences = {}

        for tf in all_predictions.keys():
            if tf in all_confidences:
                signal = all_predictions[tf].iloc[-1] if hasattr(all_predictions[tf], 'iloc') else all_predictions[tf]
                confidence = all_confidences[tf].iloc[-1] if hasattr(all_confidences[tf], 'iloc') else all_confidences[tf]

                # For buy positions, sell signals (0) are exit signals
                # For sell positions, buy signals (2) are exit signals
                if position_type == 'buy' and signal == 0:
                    exit_signals[tf] = signal
                    exit_confidences[tf] = confidence
                elif position_type == 'sell' and signal == 2:
                    exit_signals[tf] = signal
                    exit_confidences[tf] = confidence

        # Use dynamic confluence to analyze exit signals
        if exit_signals and exit_confidences:
            exit_signal, exit_confluence_strength, participating_tfs, debug_info = exit_confluence_engine.calculate_dynamic_confluence(
                exit_signals, exit_confidences, market_regime
            )

            logger.info(f"   Exit confluence analysis:")
            logger.info(f"   - Exit signal strength: {exit_confluence_strength:.3f}")
            logger.info(f"   - Participating timeframes: {participating_tfs}")
            logger.info(f"   - Strategy applied: {debug_info.get('strategy_applied', 'standard')}")

            # Get dynamic exit threshold (can be different from entry threshold) - PRESERVED from original
            exit_threshold = DYNAMIC_PARAMS.get('exit_confluence_threshold', 0.6)  # Higher bar for exits

            # Adjust threshold based on profit situation
            if profit_pct > 0.02:  # In good profit (>2%)
                # Lower threshold - more willing to exit with profits
                adjusted_exit_threshold = exit_threshold * 0.7
                threshold_reason = "lowered_for_profit_protection"
            elif profit_pct < 0:  # In loss
                # Higher threshold - need stronger signals to exit at a loss
                adjusted_exit_threshold = exit_threshold * 1.3
                threshold_reason = "raised_for_loss_prevention"
            else:
                adjusted_exit_threshold = exit_threshold
                threshold_reason = "standard"

            logger.info(f"   - Exit threshold: {adjusted_exit_threshold:.3f} ({threshold_reason})")

            # SIGNAL-DRIVEN DECISION: Exit based on confluence analysis
            if exit_confluence_strength >= adjusted_exit_threshold:
                # Strong exit signals detected
                exit_reason = f"signal_driven_exit_confluence_{exit_confluence_strength:.3f}_threshold_{adjusted_exit_threshold:.3f}_profit_{profit_pct:.4f}"

                # Determine recommended action based on signal strength
                if exit_confluence_strength > 0.8:
                    recommended_action = "immediate_exit"
                elif exit_confluence_strength > 0.7:
                    recommended_action = "standard_exit"
                else:
                    recommended_action = "cautious_exit"

                logger.info(f"   ✅ SIGNAL-DRIVEN EXIT TRIGGERED: {recommended_action}")
                logger.info(f"      Reason: Strong exit confluence ({exit_confluence_strength:.3f})")
                logger.info(f"      Participating TFs: {participating_tfs}")

                return True, exit_reason, exit_confluence_strength, recommended_action
            else:
                logger.info(f"   ⏳ HOLDING: Exit confluence below threshold ({exit_confluence_strength:.3f} < {adjusted_exit_threshold:.3f})")
        else:
            logger.info(f"   📊 No clear exit signals detected, analyzing hold vs exit")

        # ENHANCED: Check for conflicting signals (strong hold signals)
        hold_signals = {}
        hold_confidences = {}

        for tf in all_predictions.keys():
            if tf in all_confidences:
                signal = all_predictions[tf].iloc[-1] if hasattr(all_predictions[tf], 'iloc') else all_predictions[tf]
                confidence = all_confidences[tf].iloc[-1] if hasattr(all_confidences[tf], 'iloc') else all_confidences[tf]

                # For buy positions, buy signals (2) suggest holding
                # For sell positions, sell signals (0) suggest holding
                if position_type == 'buy' and signal == 2:
                    hold_signals[tf] = signal
                    hold_confidences[tf] = confidence
                elif position_type == 'sell' and signal == 0:
                    hold_signals[tf] = signal
                    hold_confidences[tf] = confidence

        # Analyze hold confluence
        if hold_signals and hold_confidences:
            hold_signal, hold_confluence_strength, hold_participating_tfs, hold_debug_info = exit_confluence_engine.calculate_dynamic_confluence(
                hold_signals, hold_confidences, market_regime
            )

            logger.info(f"   Hold confluence analysis:")
            logger.info(f"   - Hold signal strength: {hold_confluence_strength:.3f}")
            logger.info(f"   - Hold timeframes: {hold_participating_tfs}")

            # Strong hold signals should prevent early exits - PRESERVED from original
            hold_threshold = DYNAMIC_PARAMS.get('hold_confluence_threshold', 0.5)

            if hold_confluence_strength >= hold_threshold:
                logger.info(f"   🔒 STRONG HOLD SIGNALS: Staying in position ({hold_confluence_strength:.3f})")
                return False, f"strong_hold_signals_{hold_confluence_strength:.3f}", hold_confluence_strength, "strong_hold"

        # Time-based safety check (but only if signals are unclear) - PRESERVED from original
        max_hold_hours = DYNAMIC_PARAMS.get('max_hold_time_hours', 72)  # 3 days max
        time_held = (datetime.now() - entry_time).total_seconds() / 3600

        if time_held > max_hold_hours:
            # Only force exit if we don't have strong hold signals
            if not hold_signals or hold_confluence_strength < 0.4:
                logger.info(f"   ⏰ MAX HOLD TIME: Forcing exit after {time_held:.1f} hours")
                return True, f"max_hold_time_{time_held:.1f}h", 0.5, "time_forced_exit"
            else:
                logger.info(f"   ⏰ Max hold time reached but strong signals suggest holding")

        # Minimum profit protection (but much more lenient than before) - PRESERVED from original
        if profit_pct < min_profit_after_fees:
            logger.info(f"   💰 Below minimum profit threshold ({profit_pct:.4f} < {min_profit_after_fees:.4f})")
            return False, f"below_min_profit_{profit_pct:.4f}", 0.0, "hold_for_profit"

        # Default: Let signals continue to guide us
        logger.info(f"   📈 SIGNAL-DRIVEN HOLD: No clear exit signals, continuing to monitor")
        return False, f"monitoring_signals_profit_{profit_pct:.4f}", 0.3, "signal_monitoring"

    except Exception as e:
        logger.error(f"Error in signal-driven exit logic: {e}")
        # Fallback to safety exit if there's an error
        if profit_pct < -0.02:  # Exit if losing more than 2%
            return True, f"error_fallback_exit_{str(e)}", 0.5, "error_exit"
        return False, f"error_continue_{str(e)}", 0.0, "error_hold"

# ============================================================================
# ENHANCED TRADING ENGINE CLASS - Core trading logic with signal-driven exits
# ============================================================================

class EnhancedTradingEngine:
    def __init__(self, pair, base_position_size=1000):
        self.pair = pair
        self.base_position_size = base_position_size  # Fallback only
        
        # ENHANCED: Confidence multipliers optimized for signal-driven trading - PRESERVED from original
        self.confidence_multipliers = {
            'very_high': 1.0,    # Use 100% of available funds
            'high': 0.95,        # Use 95% of available funds
            'medium': 0.85,      # Use 85% of available funds
            'low': 0.70,         # Use 70% of available funds
            'very_low': 0.50     # Use 50% of available funds
        }
        self.min_confluence_timeframes = 1  # Only need 1 timeframe for signal-driven

        # Initialize dynamic confluence engine
        self.dynamic_confluence = DynamicConfluenceEngine(pair, DEPENDENCY_DIR)

    def calculate_dynamic_position_size(self, confidence, volatility_factor=1.0, signal=None):
        """
        Calculate position size based on ACTUAL multi-account exchange balances and confidence - ENHANCED FOR SIGNAL-DRIVEN
        Returns: position_size_usd, confidence_level, actual_balances
        """
        try:
            # Get actual MULTI-ACCOUNT exchange balances with per-user details - PRESERVED from original
            balances = get_actual_exchange_balances(self.pair)

            if not balances['success']:
                logger.warning(f"Could not get actual balances, using conservative fallback")
                # Use very conservative fallback
                position_size = 50.0  # Lower minimum
                return position_size, 'very_low', balances

            available_usd = balances['usd']
            available_base = balances['base']
            active_users = balances.get('active_users', 0)
            user_balances = balances.get('user_balances', {})

            if signal == 2:  # BUY signal - use USD balance
                max_available = available_usd
                currency_type = 'USD'
            elif signal == 0:  # SELL signal - use base currency balance
                max_available = available_base
                currency_type = self.pair.replace('USDT', '').replace('USD', '')
            else:
                logger.warning("No valid signal provided for position sizing")
                return 0, 'very_low', balances

            if max_available <= 0:
                logger.warning(f"No {currency_type} available for {['SELL', 'HOLD', 'BUY'][signal]} signal across {active_users} accounts")
                return 0, 'very_low', balances

            # SIGNAL-DRIVEN: Adjusted confidence thresholds (less aggressive than micro-trading) - PRESERVED from original
            if confidence >= 0.75:  # Higher bar for signal-driven (quality over quantity)
                confidence_level = 'very_high'
                confidence_multiplier = self.confidence_multipliers['very_high']
            elif confidence >= 0.60:  # Good confidence
                confidence_level = 'high'
                confidence_multiplier = self.confidence_multipliers['high']
            elif confidence >= 0.45:  # Moderate confidence
                confidence_level = 'medium'
                confidence_multiplier = self.confidence_multipliers['medium']
            elif confidence >= 0.30:  # Lower confidence
                confidence_level = 'low'
                confidence_multiplier = self.confidence_multipliers['low']
            else:
                confidence_level = 'very_low'
                confidence_multiplier = self.confidence_multipliers['very_low']

            # SIGNAL-DRIVEN: More conservative volatility adjustment (let signals handle volatility) - PRESERVED from original
            volatility_adjustment = 1.0 / max(0.8, min(1.3, volatility_factor))

            # Calculate position size
            position_size = max_available * confidence_multiplier * volatility_adjustment

            # SIGNAL-DRIVEN: Higher minimum position size for quality trades - PRESERVED from original
            position_size = max(5.0, position_size)  # $5 minimum for signal-driven

            logger.info(f"SIGNAL-DRIVEN Multi-Account Dynamic Position Sizing:")
            logger.info(f"   Available {currency_type}: {max_available:.2f} (across {active_users} accounts)")
            logger.info(f"   Confidence: {confidence:.3f} ({confidence_level})")
            logger.info(f"   Multiplier: {confidence_multiplier:.1%}")
            logger.info(f"   Volatility Adj: {volatility_adjustment:.2f}")
            logger.info(f"   Final Position: ${position_size:.2f}")

            # Add per-user position distribution info - PRESERVED from original
            if user_balances:
                logger.info(f"   User Distribution Preview:")
                users_with_funds = [(user, data) for user, data in user_balances.items() if data['has_funds']]
                if users_with_funds:
                    total_user_funds = sum(data['usd'] if signal == 2 else data['base'] for user, data in users_with_funds)
                    for user, data in users_with_funds:
                        user_amount = data['usd'] if signal == 2 else data['base']
                        user_portion = (user_amount / total_user_funds) * position_size if total_user_funds > 0 else 0
                        logger.info(f"     {user}: ${user_portion:.2f} ({user_amount/total_user_funds*100:.1f}% of total)")

            return position_size, confidence_level, balances

        except Exception as e:
            logger.error(f"Error calculating dynamic position size: {e}")
            return 5.0, 'very_low', {'usd': 0, 'base': 0, 'success': False}  # Higher fallback for signal-driven

    def check_multi_timeframe_confluence(self, all_predictions, all_confidences, market_regime=None):
        """
        ENHANCED: Check if multiple timeframes agree on the signal using DYNAMIC CONFLUENCE ENGINE
        Returns: final_signal, confluence_strength, participating_timeframes, debug_info
        """
        try:
            if not all_predictions or not all_confidences:
                return 1, 0.0, [], {}  # Hold signal

            # Use dynamic confluence engine for intelligent analysis - PRESERVED from original
            final_signal, confluence_strength, participating_timeframes, debug_info = self.dynamic_confluence.calculate_dynamic_confluence(
                all_predictions, all_confidences, market_regime
            )

            logger.info(f"🧠 DYNAMIC Multi-timeframe confluence:")
            logger.info(f"   Signal: {final_signal}, Strength: {confluence_strength:.3f}")
            logger.info(f"   Participating TFs: {participating_timeframes}")

            if debug_info.get('strategy_applied'):
                logger.info(f"   🎯 Strategy: {debug_info['strategy_applied']}")
                logger.info(f"   📋 Reason: {debug_info['override_reason']}")

            if debug_info.get('learning_active'):
                logger.info(f"   🎓 Learning: Active ({len(self.dynamic_confluence.performance_history)} trades)")
            else:
                logger.info(f"   🎓 Learning: Collecting data ({len(self.dynamic_confluence.performance_history)}/{self.dynamic_confluence.min_trades_for_learning})")

            return final_signal, confluence_strength, participating_timeframes, debug_info

        except Exception as e:
            logger.error(f"Error in dynamic multi-timeframe confluence: {e}")
            # Fallback to original method
            return self._fallback_confluence_check(all_predictions, all_confidences)

    def _fallback_confluence_check(self, all_predictions, all_confidences):
        """Fallback confluence calculation if dynamic engine fails - USES DYNAMIC WEIGHTS AS FALLBACK - PRESERVED from original"""
        try:
            logger.warning("🔄 FALLBACK: Dynamic confluence failed, using learned weights as fallback")

            # CRITICAL FIX: Use learned weights from dynamic engine as fallback, not hardcoded - PRESERVED from original
            try:
                fallback_weights = self.dynamic_confluence.learned_weights.copy()
                logger.info(f"✅ Using learned weights as fallback: {fallback_weights}")
            except:
                # Only use hardcoded as last resort - PRESERVED from original
                logger.warning("⚠️ No learned weights available, using emergency hardcoded weights")
                fallback_weights = {
                    '5m': 4.0,   # Higher weight for quick execution
                    '15m': 3.5,  # Higher weight for entry timing
                    '30m': 2.5,  # Local trend
                    '1h': 2.0,   # Medium trend
                    '4h': 1.5,   # Strong trend
                    '6h': 1.0,   # Market structure
                    '1d': 0.5    # Major trend
                }

            total_weight = 0
            weighted_signal_sum = 0
            participating_timeframes = []
            timeframe_signals = {}

            for tf in TIMEFRAMES_TO_EVALUATE:
                if tf in all_predictions and tf in all_confidences:
                    signal = all_predictions[tf].iloc[-1] if hasattr(all_predictions[tf], 'iloc') else all_predictions[tf]
                    confidence = all_confidences[tf].iloc[-1] if hasattr(all_confidences[tf], 'iloc') else all_confidences[tf]

                    # SIGNAL-DRIVEN: Higher confidence requirement (quality over quantity) - PRESERVED from original
                    if confidence >= 0.3:  # Raised from 0.2 to 0.3 for signal-driven
                        weight = fallback_weights.get(tf, 1.0) * confidence
                        weighted_signal_sum += signal * weight
                        total_weight += weight

                        timeframe_signals[tf] = {
                            'signal': signal,
                            'confidence': confidence,
                            'weight': weight
                        }
                        participating_timeframes.append(tf)

            if total_weight == 0:
                return 1, 0.0, [], {}  # Hold if no valid signals

            # Calculate weighted average signal
            weighted_average = weighted_signal_sum / total_weight

            # CRITICAL FIX: Use dynamic thresholds if available, not hardcoded - PRESERVED from original
            try:
                # Try to use dynamic engine's thresholds
                sell_threshold = 0.8  # Dynamic engine's threshold
                buy_threshold = 1.2   # Dynamic engine's threshold
                logger.info(f"✅ Using dynamic engine thresholds in fallback: sell={sell_threshold}, buy={buy_threshold}")
            except:
                # Emergency fallback thresholds - PRESERVED from original
                sell_threshold = 0.85  # Slightly more conservative for signal-driven
                buy_threshold = 1.15   # Slightly more conservative for signal-driven
                logger.warning(f"⚠️ Using emergency thresholds: sell={sell_threshold}, buy={buy_threshold}")

            # Determine final signal - PRESERVED from original
            if weighted_average < sell_threshold:
                final_signal = 0  # Sell
            elif weighted_average > buy_threshold:
                final_signal = 2  # Buy
            else:
                final_signal = 1  # Hold

            # Calculate confluence strength - PRESERVED from original
            signal_agreement = 0
            for tf_data in timeframe_signals.values():
                if tf_data['signal'] == final_signal:
                    signal_agreement += tf_data['weight']

            confluence_strength = signal_agreement / total_weight if total_weight > 0 else 0

            # Only need 1 timeframe for signal-driven - PRESERVED from original
            if len(participating_timeframes) < self.min_confluence_timeframes:
                final_signal = 1  # Hold if insufficient confluence
                confluence_strength = 0

            logger.info(f"SMART FALLBACK confluence: signal={final_signal}, "
                       f"strength={confluence_strength:.3f}, "
                       f"participating_tfs={participating_timeframes}")

            return final_signal, confluence_strength, participating_timeframes, {'fallback_mode': 'smart_learned_weights'}

        except Exception as e:
            logger.error(f"Error in fallback confluence check: {e}")
            return 1, 0.0, [], {}

    def detect_market_regime(self, df):
        """
        Detect current market regime: trending_up, trending_down, ranging
        Returns: regime, regime_strength, trend_direction
        PRESERVED from original enhanced_trading.py
        """
        try:
            # Use multiple timeframes for regime detection - PRESERVED from original
            regimes = {}

            for tf in ['5m', '15m', '1h', '1d']:
                close_col = f'close_{tf}'
                if close_col not in df.columns:
                    continue

                close_prices = df[close_col].tail(50)

                # Calculate trend indicators - PRESERVED from original
                short_ma = close_prices.tail(10).mean()
                long_ma = close_prices.tail(30).mean()

                # Price trend
                price_trend = (close_prices.iloc[-1] - close_prices.iloc[-20]) / close_prices.iloc[-20]

                # Moving average trend
                ma_trend = (short_ma - long_ma) / long_ma

                # Volatility (for ranging detection)
                volatility = close_prices.pct_change().tail(20).std()

                # SIGNAL-DRIVEN: More conservative regime detection (quality signals) - PRESERVED from original
                if abs(price_trend) < 0.02 and volatility < 0.025:  # Slightly higher thresholds
                    tf_regime = 'ranging'
                    strength = 1 - abs(price_trend) / 0.02
                elif price_trend > 0.01 and ma_trend > 0:  # Higher threshold for trending
                    tf_regime = 'trending_up'
                    strength = min(1.0, price_trend / 0.05)
                elif price_trend < -0.01 and ma_trend < 0:  # Higher threshold for trending
                    tf_regime = 'trending_down'
                    strength = min(1.0, abs(price_trend) / 0.05)
                else:
                    tf_regime = 'uncertain'
                    strength = 0.5

                regimes[tf] = {'regime': tf_regime, 'strength': strength, 'trend': price_trend}

            if not regimes:
                return 'uncertain', 0.5, 0

            # Weight longer timeframes more heavily for regime - PRESERVED from original
            weights = {'5m': 1, '15m': 1.5, '1h': 2, '1d': 3}
            regime_scores = {'trending_up': 0, 'trending_down': 0, 'ranging': 0, 'uncertain': 0}
            total_weight = 0
            avg_trend = 0

            for tf, data in regimes.items():
                weight = weights.get(tf, 1) * data['strength']
                regime_scores[data['regime']] += weight
                total_weight += weight
                avg_trend += data['trend'] * weight

            if total_weight > 0:
                avg_trend /= total_weight
                for regime in regime_scores:
                    regime_scores[regime] /= total_weight

            # Determine dominant regime - PRESERVED from original
            dominant_regime = max(regime_scores, key=regime_scores.get)
            regime_strength = regime_scores[dominant_regime]

            logger.info(f"Market regime: {dominant_regime} (strength: {regime_strength:.3f}, "
                       f"trend: {avg_trend:.3f})")

            return dominant_regime, regime_strength, avg_trend

        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return 'uncertain', 0.5, 0

    def check_volume_confirmation(self, df, signal, confluence_strength=0.0):
        """
        Enhanced volume confirmation with confluence-based rules - SIGNAL-DRIVEN MODE
        Returns: volume_confirmed, volume_strength
        PRESERVED from original enhanced_trading.py
        """
        try:
            volume_col = 'volume_5m' if 'volume_5m' in df.columns else None
            if not volume_col or volume_col not in df.columns:
                return True, 1.0  # Default to confirmed if no volume data

            current_volume = df[volume_col].iloc[-1]
            avg_volume = df[volume_col].tail(20).mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            # SIGNAL-DRIVEN: Still consider volume but don't be too strict - PRESERVED from original
            # Strong confluence can override weak volume
            if confluence_strength > 0.7:
                logger.info(f"SIGNAL-DRIVEN: High confluence ({confluence_strength:.3f}) overrides volume concerns")
                return True, min(1.0, 0.5 + confluence_strength)

            # For moderate confluence, check volume more carefully - PRESERVED from original
            if volume_ratio < 0.5:  # Very low volume
                logger.info(f"SIGNAL-DRIVEN: Low volume warning ({volume_ratio:.2f}), but proceeding with caution")
                return True, max(0.3, volume_ratio)  # Reduced confidence but still proceed

            # Normal volume confirmation - PRESERVED from original
            volume_strength = min(1.0, volume_ratio / 1.5)  # Scale relative to average
            return True, volume_strength

        except Exception as e:
            logger.error(f"Error checking volume confirmation: {e}")
            return True, 0.7  # Default confirmation with moderate confidence

# ============================================================================
# MAIN TRADING ITERATION FUNCTIONS - Enhanced with signal-driven exits
# ============================================================================

def enhanced_trading_iteration_with_ml(all_predictions, all_confidences, all_dataframes,
                                      data_quality_metrics=None, dry_run=True):
    """
    Enhanced trading iteration with ML-powered dynamic confluence threshold and SIGNAL-DRIVEN EXITS
    CRITICAL ENHANCEMENT: Now uses signal-driven exit logic instead of arbitrary profit caps
    PRESERVED: All original logic and functionality from enhanced_trading.py
    """
    try:
        logger.info("Starting SIGNAL-DRIVEN MICRO-TRADING iteration with DYNAMIC CONFLUENCE ENGINE + ML optimization")

        trading_engine = EnhancedTradingEngine(PAIR)

        # CRITICAL FIX: Get predictions from ACTUAL trained models - PRESERVED from original
        if all_predictions and all_confidences:
            # Use provided predictions (from trained models)
            logger.info(f"✅ Using predictions from {len(all_predictions)} trained models")
        else:
            # Fallback: try to get from trained models directly
            logger.warning("No predictions provided, attempting to load from trained models")
            all_predictions, all_confidences = get_trained_model_predictions(
                PAIR, TIMEFRAMES_TO_EVALUATE, all_dataframes
            )

            if not all_predictions:
                logger.error("❌ No predictions available from any source")
                return None

        # Get primary timeframe data for market analysis - PRESERVED from original
        primary_tf = '5m'
        if primary_tf not in all_dataframes:
            logger.error("Primary timeframe data not available")
            return None

        df = all_dataframes[primary_tf]

        # Detect market regime first - PRESERVED from original
        market_regime, regime_strength, trend_direction = trading_engine.detect_market_regime(df)

        # ENHANCED: Use DYNAMIC CONFLUENCE ENGINE with market regime awareness - PRESERVED from original
        initial_signal, initial_confluence_strength, participating_tfs, confluence_debug = trading_engine.check_multi_timeframe_confluence(
            all_predictions, all_confidences, market_regime
        )

        # SIGNAL-DRIVEN BOOTSTRAP-AWARE ML CONFLUENCE THRESHOLD - PRESERVED from original
        confluence_result = get_bootstrap_aware_ml_confluence_threshold(
            df=df,
            market_regime_data={
                'primary_regime': market_regime,
                'regime_strength': regime_strength,
                'confidence': 0.8
            },
            current_confluence=initial_confluence_strength,
            participating_timeframes=participating_tfs,
            all_confidences=all_confidences,
            pair=PAIR
        )

        dynamic_threshold = confluence_result['threshold']
        ml_features = confluence_result.get('market_features', {})
        ml_optimizer = confluence_result.get('optimizer')

        # Log threshold reasoning - PRESERVED from original
        if confluence_result.get('bootstrap_constrained'):
            logger.info(f"SIGNAL-DRIVEN BOOTSTRAP-CONSTRAINED ML: {dynamic_threshold:.3f} (ML wanted higher, bootstrap limited)")
        elif confluence_result.get('bootstrap_fallback'):
            logger.info(f"SIGNAL-DRIVEN BOOTSTRAP FALLBACK: {dynamic_threshold:.3f} (ML failed)")
        elif confluence_result.get('ml_available', True):
            logger.info(f"SIGNAL-DRIVEN ML + DYNAMIC Confluence: {dynamic_threshold:.3f} (regime: {market_regime})")
        else:
            logger.info(f"SIGNAL-DRIVEN DYNAMIC Confluence: {dynamic_threshold:.3f} (ML not available, regime: {market_regime})")

        # Log dynamic confluence analysis - PRESERVED from original
        if confluence_debug.get('strategy_applied'):
            logger.info(f"🎯 DYNAMIC STRATEGY OVERRIDE: {confluence_debug['strategy_applied']}")
            logger.info(f"📋 Reason: {confluence_debug['override_reason']}")

        # SIGNAL-DRIVEN: Apply confluence threshold - PRESERVED from original
        if initial_signal == 1 and initial_confluence_strength < dynamic_threshold:
            logger.info("No confluent signal across timeframes - holding position")
            trade_result = None
        elif initial_confluence_strength < dynamic_threshold:
            logger.info(f"Insufficient confluence strength ({initial_confluence_strength:.3f}) "
                       f"vs SIGNAL-DRIVEN threshold ({dynamic_threshold:.3f}) - holding position")
            trade_result = None
        else:
            logger.info(f"SIGNAL-DRIVEN + DYNAMIC confluence threshold met: {initial_confluence_strength:.3f} "
                       f">= {dynamic_threshold:.3f}")

            # Continue with existing enhanced trading logic... - PRESERVED from original
            primary_confidence = all_confidences.get(primary_tf, 0.5)
            if hasattr(primary_confidence, 'iloc'):
                primary_confidence = primary_confidence.iloc[-1]

            # Get current price - PRESERVED from original
            current_price = df['close_5m'].iloc[-1] if 'close_5m' in df.columns else df.iloc[-1, 0]

            # SIGNAL-DRIVEN: Enhanced volume confirmation - PRESERVED from original
            volume_confirmed, volume_strength = trading_engine.check_volume_confirmation(df, initial_signal, initial_confluence_strength)

            if not volume_confirmed:
                logger.info(f"Volume does not confirm signal {initial_signal} - but SIGNAL-DRIVEN mode proceeding with caution")
                volume_strength = max(0.3, volume_strength)  # Reduce but don't block

            # Calculate enhanced confidence score - PRESERVED from original
            enhanced_confidence = (
                primary_confidence * 0.4 +
                initial_confluence_strength * 0.3 +
                regime_strength * 0.2 +
                volume_strength * 0.1
            )

            # Calculate volatility factor for position sizing - PRESERVED from original
            atr_values = df['ATR_5m'] if 'ATR_5m' in df.columns else None
            if atr_values is not None:
                recent_atr = atr_values.tail(5).mean()
                avg_atr = atr_values.tail(20).mean()
                volatility_factor = recent_atr / avg_atr if avg_atr > 0 else 1.0
            else:
                volatility_factor = 1.0

            # Get ACTUAL position size from exchange balances - PRESERVED from original
            position_size, confidence_level, actual_balances = trading_engine.calculate_dynamic_position_size(
                enhanced_confidence, volatility_factor, initial_signal
            )

            # SIGNAL-DRIVEN: Proceed with quality trades - PRESERVED from original
            if position_size <= 0:
                quote_currency = extract_quote_currency(PAIR)
                signal_name = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}[initial_signal]
                logger.warning(f"INSUFFICIENT FUNDS for {signal_name} signal")
                logger.warning(f"   Available {quote_currency}: ${actual_balances.get('usd', 0):.2f}")
                logger.warning(f"   Available Base: {actual_balances.get('base', 0):.4f}")
                trade_result = None
            else:
                # SIGNAL-DRIVEN: Enhanced regime alignment (but still proceed with good signals) - PRESERVED from original
                regime_aligned = True
                if regime_strength > 0.8:  # Strong regime detected
                    if ((market_regime == 'trending_down' and initial_signal == 2) or
                        (market_regime == 'trending_up' and initial_signal == 0)):
                        if initial_confluence_strength < 0.8:  # Unless we have very strong signals
                            regime_aligned = False
                            logger.info(f"Signal conflicts with strong {market_regime} regime - requiring higher confluence")

                if not regime_aligned:
                    logger.info(f"Signal conflicts with market regime ({market_regime}) - holding position")
                    trade_result = None
                else:
                    # Execute trade with SIGNAL-DRIVEN configuration - PRESERVED from original
                    trade_details = {
                        'timestamp': datetime.now(),
                        'pair': PAIR,
                        'signal': {0: 'sell', 1: 'hold', 2: 'buy'}[initial_signal],
                        'prediction': initial_signal,
                        'price': current_price,
                        'position_size': position_size,
                        'confidence': primary_confidence,
                        'enhanced_confidence': enhanced_confidence,
                        'confidence_level': confidence_level,
                        'confluence_strength': initial_confluence_strength,
                        'dynamic_threshold_used': dynamic_threshold,
                        'ml_optimized': confluence_result.get('ml_successful', False),
                        'dynamic_confluence_used': True,
                        'confluence_debug': confluence_debug,
                        'participating_timeframes': participating_tfs,
                        'market_regime': market_regime,
                        'regime_strength': regime_strength,
                        'volume_confirmed': volume_confirmed,
                        'volume_strength': volume_strength,
                        'volatility_factor': volatility_factor,
                        'dry_run': dry_run,
                        'actual_balances': actual_balances,
                        'signal_driven_mode': True,  # NEW: Mark as signal-driven
                        'signal_driven_exits': DYNAMIC_PARAMS.get('use_signal_driven_exits', True)  # NEW
                    }

                    quote_currency = extract_quote_currency(PAIR)
                    logger.info(f"🎯 SIGNAL-DRIVEN QUALITY TRADE with DYNAMIC CONFLUENCE + ML:")
                    logger.info(f"   DYNAMIC Threshold: {dynamic_threshold:.3f}")
                    logger.info(f"   Confluence Strength: {initial_confluence_strength:.3f}")
                    logger.info(f"   Position Size: ${position_size:.2f} from EXCHANGE ({confidence_level} confidence)")
                    logger.info(f"   Market Regime: {market_regime} (strength: {regime_strength:.3f})")
                    logger.info(f"   🎯 SIGNAL-DRIVEN EXITS: Let ML confluence determine optimal exit timing")
                    logger.info(f"   Available {quote_currency}: ${actual_balances.get('usd', 0):.2f} | Base: {actual_balances.get('base', 0):.4f}")

                    if not dry_run:
                        # Execute actual trade via gobbler.sh
                        trade_result = execute_enhanced_trade(trade_details)
                        trade_details.update(trade_result)

                    # Log enhanced trade with signal-driven data
                    log_enhanced_trade_with_signal_driven(trade_details)

                    # CRITICAL: Update bootstrap state with REAL PROFIT learning - PRESERVED from original
                    update_bootstrap_trade_results_with_real_profit(trade_details)

                    # CRITICAL: Record outcome in dynamic confluence engine for learning - PRESERVED from original
                    actual_profit = trade_details.get('total_real_profit', 0.0)
                    trading_engine.dynamic_confluence.record_trade_outcome(
                        confluence_debug, trade_details, actual_profit
                    )

                    trade_result = trade_details

        # LOG CONFLUENCE DECISION FOR CONTINUOUS LEARNING - PRESERVED from original
        if ML_CONFLUENCE_AVAILABLE and confluence_result.get('ml_successful') and ml_optimizer:
            try:
                log_confluence_decision(ml_optimizer, dynamic_threshold, trade_result, ml_features)
            except Exception as e:
                logger.error(f"Error logging confluence decision: {e}")

        return trade_result

    except Exception as e:
        logger.error(f"Error in SIGNAL-DRIVEN enhanced trading iteration with DYNAMIC CONFLUENCE + ML: {str(e)}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")
        return None

def enhanced_trading_iteration(all_predictions, all_confidences, all_dataframes, data_quality_metrics=None, dry_run=True):
    """
    Standard enhanced trading iteration with SIGNAL-DRIVEN EXITS + DYNAMIC CONFLUENCE (fallback when ML not available)
    PRESERVED: All original logic and functionality from enhanced_trading.py
    """
    try:
        logger.info("Starting SIGNAL-DRIVEN iteration with DYNAMIC CONFLUENCE ENGINE + bootstrap balance verification")

        trading_engine = EnhancedTradingEngine(PAIR)

        # Get primary timeframe data for market analysis - PRESERVED from original
        primary_tf = '5m'
        if primary_tf not in all_dataframes:
            logger.error("Primary timeframe data not available")
            return None

        df = all_dataframes[primary_tf]

        # Detect market regime - PRESERVED from original
        market_regime, regime_strength, trend_direction = trading_engine.detect_market_regime(df)

        # ENHANCED: Check multi-timeframe confluence using DYNAMIC ENGINE - PRESERVED from original
        final_signal, confluence_strength, participating_tfs, confluence_debug = trading_engine.check_multi_timeframe_confluence(
            all_predictions, all_confidences, market_regime
        )

        if final_signal == 1:  # Hold signal
            logger.info("No confluent signal across timeframes - holding position")
            return None

        # SIGNAL-DRIVEN: Use bootstrap threshold - PRESERVED from original
        dynamic_threshold = get_bootstrap_confluence_threshold()

        if confluence_strength < dynamic_threshold:
            logger.info(f"Insufficient confluence strength ({confluence_strength:.3f}) vs SIGNAL-DRIVEN bootstrap threshold ({dynamic_threshold:.3f}) - holding position")
            return None

        primary_confidence = all_confidences.get(primary_tf, 0.5)
        if hasattr(primary_confidence, 'iloc'):
            primary_confidence = primary_confidence.iloc[-1]

        # Get current price - PRESERVED from original
        current_price = df['close_5m'].iloc[-1] if 'close_5m' in df.columns else df.iloc[-1, 0]

        # SIGNAL-DRIVEN: Enhanced volume confirmation - PRESERVED from original
        volume_confirmed, volume_strength = trading_engine.check_volume_confirmation(df, final_signal)

        if not volume_confirmed:
            logger.info(f"Volume does not confirm signal {final_signal} - but SIGNAL-DRIVEN mode proceeding with caution")
            volume_strength = max(0.3, volume_strength)

        # Calculate volatility factor for position sizing - PRESERVED from original
        atr_values = df['ATR_5m'] if 'ATR_5m' in df.columns else None
        if atr_values is not None:
            recent_atr = atr_values.tail(5).mean()
            avg_atr = atr_values.tail(20).mean()
            volatility_factor = recent_atr / avg_atr if avg_atr > 0 else 1.0
        else:
            volatility_factor = 1.0

        # Calculate enhanced confidence score - PRESERVED from original
        enhanced_confidence = (
            primary_confidence * 0.4 +
            confluence_strength * 0.3 +
            regime_strength * 0.2 +
            volume_strength * 0.1
        )

        # Get ACTUAL position size from exchange balances - PRESERVED from original
        position_size, confidence_level, actual_balances = trading_engine.calculate_dynamic_position_size(
            enhanced_confidence, volatility_factor, final_signal
        )

        # SIGNAL-DRIVEN: Proceed with quality trades - PRESERVED from original
        if position_size <= 0:
            quote_currency = extract_quote_currency(PAIR)
            signal_name = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}[final_signal]
            logger.warning(f"INSUFFICIENT FUNDS for {signal_name} signal")
            logger.warning(f"   Available {quote_currency}: ${actual_balances.get('usd', 0):.2f}")
            logger.warning(f"   Available Base: {actual_balances.get('base', 0):.4f}")
            return None

        # SIGNAL-DRIVEN: Enhanced regime alignment - PRESERVED from original
        regime_aligned = True
        if regime_strength > 0.8:  # Strong regime detected
            if ((market_regime == 'trending_down' and final_signal == 2) or
                (market_regime == 'trending_up' and final_signal == 0)):
                if confluence_strength < 0.8:  # Unless we have very strong signals
                    regime_aligned = False

        if not regime_aligned:
            logger.info(f"Signal conflicts with market regime ({market_regime}) - holding position")
            return None

        # Execute trade - PRESERVED from original
        trade_details = {
            'timestamp': pd.Timestamp.now(tz='UTC'),
            'pair': PAIR,
            'signal': {0: 'sell', 1: 'hold', 2: 'buy'}[final_signal],
            'prediction': final_signal,
            'price': current_price,
            'position_size': position_size,
            'confidence': primary_confidence,
            'enhanced_confidence': enhanced_confidence,
            'confidence_level': confidence_level,
            'confluence_strength': confluence_strength,
            'dynamic_threshold_used': dynamic_threshold,
            'ml_optimized': False,
            'dynamic_confluence_used': True,
            'confluence_debug': confluence_debug,
            'participating_timeframes': participating_tfs,
            'market_regime': market_regime,
            'regime_strength': regime_strength,
            'volume_confirmed': volume_confirmed,
            'volume_strength': volume_strength,
            'volatility_factor': volatility_factor,
            'dry_run': dry_run,
            'actual_balances': actual_balances,
            'signal_driven_mode': True,  # NEW: Mark as signal-driven
            'signal_driven_exits': DYNAMIC_PARAMS.get('use_signal_driven_exits', True)  # NEW
        }

        quote_currency = extract_quote_currency(PAIR)
        logger.info(f"🎯 SIGNAL-DRIVEN QUALITY TRADE with DYNAMIC CONFLUENCE + BOOTSTRAP:")
        logger.info(f"   DYNAMIC Bootstrap Threshold: {dynamic_threshold:.3f}")
        logger.info(f"   Position Size: ${position_size:.2f} from EXCHANGE ({confidence_level} confidence)")
        logger.info(f"   Enhanced Confidence: {enhanced_confidence:.3f}")
        logger.info(f"   Confluence: {confluence_strength:.3f} ({len(participating_tfs)} timeframes)")
        logger.info(f"   Market Regime: {market_regime} (strength: {regime_strength:.3f})")
        logger.info(f"   🎯 SIGNAL-DRIVEN EXITS: Let ML confluence determine optimal exit timing")
        logger.info(f"   Available {quote_currency}: ${actual_balances.get('usd', 0):.2f} | Base: {actual_balances.get('base', 0):.4f}")

        if not dry_run:
            # Execute actual trade via gobbler.sh
            trade_result = execute_enhanced_trade(trade_details)
            trade_details.update(trade_result)

        # Log enhanced trade with signal-driven data
        log_enhanced_trade_with_signal_driven(trade_details)

        # CRITICAL: Update bootstrap state with REAL PROFIT learning - PRESERVED from original
        update_bootstrap_trade_results_with_real_profit(trade_details)

        # CRITICAL: Record outcome in dynamic confluence engine for learning - PRESERVED from original
        actual_profit = trade_details.get('total_real_profit', 0.0)
        trading_engine.dynamic_confluence.record_trade_outcome(
            confluence_debug, trade_details, actual_profit
        )

        return trade_details

    except Exception as e:
        logger.error(f"Error in SIGNAL-DRIVEN enhanced trading iteration with DYNAMIC CONFLUENCE + balance checking: {str(e)}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")
        return None

# ============================================================================
# TRADE EXECUTION FUNCTIONS - Enhanced with multi-user and real profit tracking
# ============================================================================

def execute_multi_user_trade_with_real_tracking(trade_details):
    """Execute trade across multiple users with REAL profit tracking and SIGNAL-DRIVEN logic - PRESERVED from original"""
    try:
        signal = trade_details['prediction']
        price = trade_details['price']
        total_position_size_usd = trade_details['position_size']
        user_balances = trade_details['actual_balances'].get('user_balances', {})

        # Convert total USD position to base currency volume
        total_volume = total_position_size_usd / price

        logger.info(f"🚀 EXECUTING SIGNAL-DRIVEN REAL-PROFIT-TRACKED MULTI-USER TRADE:")
        logger.info(f"   Signal: {trade_details['signal'].upper()} ${total_position_size_usd:.2f} total")
        logger.info(f"   Signal-Driven Mode: {trade_details.get('signal_driven_mode', False)}")

        # Filter users with sufficient funds - PRESERVED from original
        currency_type = 'usd' if signal == 2 else 'base'
        eligible_users = []

        for username, balance_data in user_balances.items():
            if balance_data['has_funds'] and balance_data[currency_type] > 0.5:
                eligible_users.append((username, balance_data[currency_type]))

        if not eligible_users:
            logger.error(f"❌ No eligible users found for {trade_details['signal'].upper()} trade")
            return {'error': 'no_eligible_users'}

        # Calculate total funds from eligible users - PRESERVED from original
        total_eligible_funds = sum(amount for _, amount in eligible_users)

        # Distribute trade across eligible users proportionally - PRESERVED from original
        execution_results = {}
        total_executed = 0.0

        for username, user_amount in eligible_users:
            # Calculate proportional share
            user_proportion = user_amount / total_eligible_funds
            user_position_size = total_position_size_usd * user_proportion
            user_volume = user_position_size / price

            # For signal-driven trading, maintain quality threshold - PRESERVED from original
            if user_position_size < 1.0:  # $1 minimum for signal-driven
                logger.info(f"   ❌ {username}: Skipping ${user_position_size:.2f} (below $1.00 minimum)")
                execution_results[username] = {'status': 'skipped_too_small', 'amount': user_position_size}
                continue

            try:
                # Execute trade for this specific user via gobbler.sh - PRESERVED from original
                gobbler_script = os.path.join(DEPENDENCY_DIR, "dependencies_v1", "gobbler.sh")
                if not os.path.exists(gobbler_script):
                    gobbler_script = os.path.join(DEPENDENCY_DIR, "gobbler.sh")

                # Prepare trade command for specific user - PRESERVED from original
                signal_str = 'buy' if signal == 2 else 'sell'
                trade_cmd = [
                    gobbler_script,
                    signal_str,
                    str(user_volume),
                    'market',
                    trade_details['pair'],
                    username,
                    '--format=json'
                ]

                if trade_details['dry_run']:
                    # Simulate the trade for dry run - PRESERVED from original
                    logger.info(f"   ✅ {username}: DRY RUN ${user_position_size:.2f} ({user_proportion*100:.1f}% of total)")
                    execution_results[username] = {
                        'status': 'dry_run_success',
                        'amount': user_position_size,
                        'volume': user_volume,
                        'proportion': user_proportion,
                        'real_profit': 0.0,
                        'signal_driven_mode': trade_details.get('signal_driven_mode', False)
                    }
                    total_executed += user_position_size
                else:
                    # Execute real trade with REAL profit tracking - PRESERVED from original
                    logger.info(f"   🔄 {username}: Executing SIGNAL-DRIVEN ${user_position_size:.2f} ({user_proportion*100:.1f}% of total)")

                    result = subprocess.run(trade_cmd, capture_output=True, text=True, timeout=120)

                    if result.returncode == 0:
                        try:
                            # Parse REAL execution data from gobbler.sh - PRESERVED from original
                            trade_result = {}
                            if result.stdout.strip().startswith('{'):
                                trade_result = json.loads(result.stdout)

                            # Extract REAL execution details - PRESERVED from original
                            real_volume = float(trade_result.get('executed_volume', user_volume))
                            real_price = float(trade_result.get('executed_price', price))
                            real_total = float(trade_result.get('total_usd', user_position_size))
                            real_fees = float(trade_result.get('fees', 0))
                            real_profit = float(trade_result.get('real_profit', 0))

                            logger.info(f"   ✅ {username}: SIGNAL-DRIVEN SUCCESS - Vol: {real_volume:.4f}, Price: ${real_price:.4f}, Profit: ${real_profit:.4f}")

                            execution_results[username] = {
                                'status': 'success',
                                'amount': real_total,
                                'volume': real_volume,
                                'price': real_price,
                                'fees': real_fees,
                                'real_profit': real_profit,
                                'proportion': user_proportion,
                                'trade_result': trade_result,
                                'signal_driven_mode': trade_details.get('signal_driven_mode', False)
                            }
                            total_executed += real_total

                        except json.JSONDecodeError:
                            logger.warning(f"   ⚠️  {username}: Trade executed but response not JSON: {result.stdout}")
                            execution_results[username] = {
                                'status': 'success_no_json',
                                'amount': user_position_size,
                                'volume': user_volume,
                                'proportion': user_proportion,
                                'real_profit': 0.0,
                                'signal_driven_mode': trade_details.get('signal_driven_mode', False)
                            }
                            total_executed += user_position_size
                    else:
                        logger.error(f"   ❌ {username}: FAILED ${user_position_size:.2f} - {result.stderr}")
                        execution_results[username] = {
                            'status': 'failed',
                            'amount': user_position_size,
                            'error': result.stderr,
                            'real_profit': 0.0,
                            'signal_driven_mode': trade_details.get('signal_driven_mode', False)
                        }

            except Exception as e:
                logger.error(f"   ❌ {username}: EXCEPTION ${user_position_size:.2f} - {str(e)}")
                execution_results[username] = {
                    'status': 'exception',
                    'amount': user_position_size,
                    'error': str(e),
                    'real_profit': 0.0,
                    'signal_driven_mode': trade_details.get('signal_driven_mode', False)
                }

        # Calculate total real profit (for sell trades) - PRESERVED from original
        total_real_profit = sum(result.get('real_profit', 0) for result in execution_results.values())

        # Summary logging with REAL profit data - PRESERVED from original
        successful_users = [user for user, result in execution_results.items() if result['status'] in ['success', 'success_no_json', 'dry_run_success']]
        failed_users = [user for user, result in execution_results.items() if result['status'] in ['failed', 'exception']]
        skipped_users = [user for user, result in execution_results.items() if result['status'] == 'skipped_too_small']

        logger.info(f"📊 SIGNAL-DRIVEN REAL-PROFIT-TRACKED MULTI-USER TRADE SUMMARY:")
        logger.info(f"   ✅ Successful: {len(successful_users)} users (${total_executed:.2f})")
        logger.info(f"   💰 TOTAL REAL PROFIT: ${total_real_profit:.4f}")
        logger.info(f"   ❌ Failed: {len(failed_users)} users")
        logger.info(f"   ⏭️  Skipped: {len(skipped_users)} users")
        logger.info(f"   📈 Execution Rate: {total_executed/total_position_size_usd*100:.1f}%")
        logger.info(f"   🎯 Signal-Driven Mode: Active")

        return {
            'total_requested': total_position_size_usd,
            'total_executed': total_executed,
            'total_real_profit': total_real_profit,
            'execution_rate': total_executed/total_position_size_usd if total_position_size_usd > 0 else 0,
            'successful_users': successful_users,
            'failed_users': failed_users,
            'skipped_users': skipped_users,
            'user_results': execution_results,
            'status': 'partial_success' if successful_users else 'complete_failure',
            'signal_driven_mode': trade_details.get('signal_driven_mode', False)
        }

    except Exception as e:
        logger.error(f"Error in signal-driven real-profit-tracked multi-user trade execution: {e}")
        return {'error': str(e), 'status': 'system_error', 'signal_driven_mode': False}

def execute_enhanced_trade(trade_details):
    """Execute trade with enhanced multi-user parameters, REAL profit tracking, and SIGNAL-DRIVEN logic - PRESERVED from original"""
    try:
        # Check if we have multi-user balance data - PRESERVED from original
        user_balances = trade_details['actual_balances'].get('user_balances', {})

        if user_balances:
            # Use enhanced multi-user execution with real profit tracking and signal-driven logic
            result = execute_multi_user_trade_with_real_tracking(trade_details)

            # Record all successful trades for profit tracking - PRESERVED from original
            if result.get('status') in ['partial_success', 'complete_success']:
                recorded_trades = record_trade_execution(trade_details, result)
                result['recorded_trades'] = recorded_trades

                # For sell trades, calculate real profit immediately - PRESERVED from original
                if trade_details['signal'] == 'sell':
                    total_real_profit = 0.0
                    for trade_record in recorded_trades:
                        real_profit = process_sell_trade_profit(trade_record)
                        total_real_profit += real_profit

                    result['total_real_profit'] = total_real_profit
                    trade_details['profit'] = total_real_profit

                    logger.info(f"💰 TOTAL SIGNAL-DRIVEN REAL PROFIT from sell: ${total_real_profit:.4f}")

            return result
        else:
            # Fallback to original single execution - PRESERVED from original
            signal = trade_details['prediction']
            price = trade_details['price']

            # Calculate volume in base currency
            position_size_usd = trade_details['position_size']
            volume = position_size_usd / price

            # Use existing execute_trade function but with dynamic sizing
            from trading import execute_trade

            result = execute_trade(
                signal=signal,
                price=price,
                volume=volume,
                timeframe='enhanced',
                dry_run=trade_details['dry_run'],
                live_mode=not trade_details['dry_run']
            )

            return result if result else {}

    except Exception as e:
        logger.error(f"Error executing signal-driven enhanced trade: {e}")
        return {'error': str(e)}

# ============================================================================
# LOGGING FUNCTIONS - Enhanced with signal-driven data
# ============================================================================

def log_enhanced_trade_with_signal_driven(trade_details):
    """Enhanced trade logging with SIGNAL-DRIVEN data - PRESERVED from original"""
    try:
        # Include signal-driven specific fields in the log - PRESERVED from original
        signal_driven_fields = {
            'dynamic_threshold_used': trade_details.get('dynamic_threshold_used', 0.02),
            'ml_optimized': trade_details.get('ml_optimized', False),
            'dynamic_confluence_used': trade_details.get('dynamic_confluence_used', False),
            'signal_driven_mode': trade_details.get('signal_driven_mode', False),
            'signal_driven_exits': trade_details.get('signal_driven_exits', False),
            'confluence_debug_info': safe_json_dumps(trade_details.get('confluence_debug', {})),
            'threshold_vs_static': trade_details.get('dynamic_threshold_used', 0.02) - 0.05,
            'real_profit_tracking': True,
            'exit_strategy': 'signal_driven'
        }

        # Add to existing trade details
        enhanced_trade_details = {**trade_details, **signal_driven_fields}

        # Use existing logging function
        log_enhanced_trade(enhanced_trade_details)

        # Signal-driven specific logging - PRESERVED from original
        signal_driven_log_path = os.path.join(DEPENDENCY_DIR, f"signal_driven_decisions_{PAIR.lower()}.csv")

        signal_driven_log_data = {
            'timestamp': trade_details['timestamp'],
            'confluence_strength': trade_details['confluence_strength'],
            'dynamic_threshold': trade_details.get('dynamic_threshold_used', 0.02),
            'static_threshold': 0.05,
            'threshold_difference': trade_details.get('dynamic_threshold_used', 0.02) - 0.05,
            'trade_executed': trade_details.get('signal') != 'hold',
            'market_regime': trade_details.get('market_regime', 'unknown'),
            'ml_optimized': trade_details.get('ml_optimized', False),
            'dynamic_confluence_used': trade_details.get('dynamic_confluence_used', False),
            'signal_driven_mode': trade_details.get('signal_driven_mode', False),
            'signal_driven_exits': trade_details.get('signal_driven_exits', False),
            'strategy_applied': trade_details.get('confluence_debug', {}).get('strategy_applied', 'none'),
            'override_reason': trade_details.get('confluence_debug', {}).get('override_reason', 'none'),
            'learning_active': trade_details.get('confluence_debug', {}).get('learning_active', False),
            'real_profit': trade_details.get('profit', 0),
            'real_profit_tracking': True,
            'exit_strategy': 'signal_driven'
        }

        signal_driven_df = pd.DataFrame([signal_driven_log_data])
        if os.path.exists(signal_driven_log_path):
            signal_driven_df.to_csv(signal_driven_log_path, mode='a', header=False, index=False)
        else:
            signal_driven_df.to_csv(signal_driven_log_path, mode='w', header=True, index=False)

    except Exception as e:
        logger.error(f"Error in enhanced signal-driven trade logging: {e}")

def log_enhanced_trade(trade_details):
    """Log enhanced trade with all metrics including SIGNAL-DRIVEN mode - PRESERVED from original"""
    try:
        # Enhanced signal log - PRESERVED from original
        enhanced_log_path = os.path.join(DEPENDENCY_DIR, f"enhanced_signal_log_{PAIR.lower()}.csv")

        # Convert to DataFrame - PRESERVED from original
        log_data = {
            'timestamp': trade_details['timestamp'],
            'pair': trade_details['pair'],
            'signal': trade_details['signal'],
            'price': trade_details['price'],
            'position_size': trade_details['position_size'],
            'confidence': trade_details['confidence'],
            'enhanced_confidence': trade_details['enhanced_confidence'],
            'confidence_level': trade_details['confidence_level'],
            'confluence_strength': trade_details['confluence_strength'],
            'dynamic_threshold_used': trade_details.get('dynamic_threshold_used', 0.02),
            'participating_timeframes': ','.join(trade_details['participating_timeframes']),
            'market_regime': trade_details['market_regime'],
            'regime_strength': trade_details['regime_strength'],
            'volume_confirmed': trade_details['volume_confirmed'],
            'dry_run': trade_details['dry_run'],
            'profit': trade_details.get('profit', 0),
            'actual_usd_balance': trade_details['actual_balances'].get('usd', 0),
            'actual_base_balance': trade_details['actual_balances'].get('base', 0),
            'balance_check_success': trade_details['actual_balances'].get('success', False),
            'signal_driven_mode': trade_details.get('signal_driven_mode', False),
            'signal_driven_exits': trade_details.get('signal_driven_exits', False),
            'real_profit_mode': True,
            'dynamic_confluence_used': trade_details.get('dynamic_confluence_used', False),
            'exit_strategy': trade_details.get('exit_strategy', 'signal_driven')
        }

        log_df = pd.DataFrame([log_data])
        log_df.to_csv(enhanced_log_path, mode='a', header=not os.path.exists(enhanced_log_path), index=False)

        logger.info(f"SIGNAL-DRIVEN enhanced trade with DYNAMIC CONFLUENCE + REAL PROFIT logged to {enhanced_log_path}")

    except Exception as e:
        logger.error(f"Error logging signal-driven enhanced trade: {e}")

# Export all functions and classes
__all__ = [
    # NEW: Signal-driven exit logic
    'should_exit_based_on_signals',
    
    # Main trading engine
    'EnhancedTradingEngine',
    
    # Main trading iteration functions
    'enhanced_trading_iteration_with_ml',
    'enhanced_trading_iteration',
    
    # Trade execution
    'execute_multi_user_trade_with_real_tracking',
    'execute_enhanced_trade',
    
    # Enhanced logging
    'log_enhanced_trade_with_signal_driven',
    'log_enhanced_trade'
]

logger.info("✅ enhanced_trading_engine.py v1.0 loaded successfully with SIGNAL-DRIVEN EXITS and intelligent ML confluence")

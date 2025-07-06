# dynamic_confluence_engine.py
# Version: 1.0 - Enhanced Dynamic Confluence Engine with Profit Attribution + Weight Optimization + Learning Recommendations
# Contains: DynamicConfluenceEngine class with all learning capabilities and atomic JSON protection
# CRITICAL: Preserves all existing functionality while adding profit attribution tracking and weight optimization

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from config import args, PAIR, DYNAMIC_PARAMS, DEPENDENCY_DIR, RUN_ID, TIMEFRAMES_TO_EVALUATE
from logging_setup import logger, debug_logger
import traceback

# Import atomic JSON functions from core
from enhanced_trading_core import (
    atomic_json_write, 
    safe_backup_and_write, 
    safe_json_convert,
    safe_json_dumps
)

class DynamicConfluenceEngine:
    """
    Fully dynamic confluence calculation engine that learns from market behavior
    ENHANCED: Now includes profit attribution tracking, weight optimization analysis, 
    and enhanced logging WITHOUT losing any existing functionality
    """

    def __init__(self, pair, dependency_dir):
        self.pair = pair
        self.dependency_dir = dependency_dir
        
        # File paths with consistent naming
        pair_clean = pair.lower().replace('/', '').replace('usdt', '').replace('usd', '')
        self.weights_file = os.path.join(dependency_dir, f"confluence_weights_{pair_clean}.json")
        self.performance_file = os.path.join(dependency_dir, f"confluence_performance_{pair_clean}.json")

        # NEW: Enhanced tracking files
        self.profit_attribution_file = os.path.join(dependency_dir, f"profit_attribution_{pair_clean}.json")
        self.weight_optimization_file = os.path.join(dependency_dir, f"weight_optimization_{pair_clean}.json")
        self.learning_log_file = os.path.join(dependency_dir, f"confluence_learning_{pair_clean}.log")

        # Market-aware base weights (logical hierarchy) - PRESERVED from original
        self.base_weights = {
            '4h': 3.0,   # Primary trend direction
            '1h': 2.2,   # Secondary trend
            '30m': 1.8,  # Local trend strength
            '15m': 1.4,  # Entry timing
            '5m': 1.0    # Execution timing
        }

        # Load learned weights and performance data - PRESERVED functionality
        self.learned_weights = self.load_learned_weights()
        self.performance_history = self.load_performance_history()
        self.market_conditions = {'volatility_regime': 'medium'}

        # Dynamic learning parameters - PRESERVED from original
        self.learning_rate = 0.03
        self.min_trades_for_learning = 15

        # NEW: Enhanced tracking data
        self.profit_attribution_data = self.load_profit_attribution_data()
        self.weight_optimization_history = self.load_weight_optimization_history()
        self.regime_specific_weights = {}

        logger.debug(f"DynamicConfluenceEngine initialized for {pair}")

    def load_learned_weights(self):
        """Load dynamically learned weights - PRESERVED original logic"""
        try:
            if os.path.exists(self.weights_file):
                with open(self.weights_file, 'r') as f:
                    data = json.load(f)
                    weights = data.get('weights', self.base_weights.copy())

                    # Validate weights are reasonable - PRESERVED validation
                    for tf in self.base_weights.keys():
                        if tf not in weights or weights[tf] < 0.1 or weights[tf] > 5.0:
                            weights[tf] = self.base_weights[tf]

                    logger.debug(f"Loaded learned weights: {weights}")
                    return weights
            return self.base_weights.copy()
        except Exception as e:
            logger.warning(f"Error loading weights, using base: {e}")
            return self.base_weights.copy()

    def load_performance_history(self):
        """Load performance history for continuous learning - PRESERVED original logic"""
        try:
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r') as f:
                    history = json.load(f)
                    # Keep only recent 100 trades - PRESERVED limit
                    return history[-100:] if len(history) > 100 else history
            return []
        except Exception as e:
            logger.warning(f"Error loading performance history: {e}")
            return []

    # NEW: Load profit attribution data
    def load_profit_attribution_data(self):
        """Load profit attribution tracking data"""
        try:
            if os.path.exists(self.profit_attribution_file):
                with open(self.profit_attribution_file, 'r') as f:
                    return json.load(f)
            return {
                'timeframe_performance': {},
                'weight_performance': {},
                'regime_performance': {},
                'last_analysis': None
            }
        except Exception as e:
            logger.warning(f"Error loading profit attribution data: {e}")
            return {'timeframe_performance': {}, 'weight_performance': {}, 'regime_performance': {}, 'last_analysis': None}

    # NEW: Load weight optimization history
    def load_weight_optimization_history(self):
        """Load weight optimization analysis history"""
        try:
            if os.path.exists(self.weight_optimization_file):
                with open(self.weight_optimization_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.warning(f"Error loading weight optimization history: {e}")
            return []

    # NEW: Enhanced logging function
    def log_learning_event(self, event_type, details):
        """Log learning events for analysis"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] {event_type}: {details}\n"

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.learning_log_file), exist_ok=True)

            with open(self.learning_log_file, 'a') as f:
                f.write(log_entry)

            # Also log to main logger for immediate visibility
            logger.info(f"🧠 LEARNING: {event_type} - {details}")

        except Exception as e:
            logger.warning(f"Error logging learning event: {e}")

    def calculate_dynamic_confluence(self, all_predictions, all_confidences, market_regime=None):
        """
        CORE FUNCTION: Calculate confluence with full dynamic adaptation
        ENHANCED: Now includes profit attribution tracking
        PRESERVED: All original logic and functionality
        """

        debug_info = {
            'market_regime': market_regime,
            'weights_used': {},
            'individual_contributions': {},
            'voting_analysis': {},
            'strategy_applied': None,
            'override_reason': None,
            'learning_active': len(self.performance_history) >= self.min_trades_for_learning,
            'profit_attribution_active': True,  # NEW
            'weight_optimization_active': True  # NEW
        }

        if not all_predictions or not all_confidences:
            logger.debug("No predictions or confidences provided")
            return 1, 0.0, [], debug_info

        # Use learned weights with market adaptations - PRESERVED original logic
        adaptive_weights = self.get_adaptive_weights(all_confidences, market_regime)
        debug_info['weights_used'] = adaptive_weights

        # NEW: Track timeframe contributions for profit attribution
        timeframe_contributions = {}

        # Analyze raw voting patterns - PRESERVED original logic
        vote_analysis = self.analyze_voting_patterns(all_predictions, all_confidences)
        debug_info['voting_analysis'] = vote_analysis

        # Check for strong consensus patterns - PRESERVED original logic
        consensus_result = self.check_consensus_patterns(all_predictions, all_confidences, vote_analysis)

        if consensus_result['override']:
            debug_info['strategy_applied'] = consensus_result['strategy']
            debug_info['override_reason'] = consensus_result['reason']

            # NEW: Log strategy override for learning
            self.log_learning_event("STRATEGY_OVERRIDE",
                f"Strategy: {consensus_result['strategy']}, Reason: {consensus_result['reason']}")

            return consensus_result['signal'], consensus_result['strength'], consensus_result['timeframes'], debug_info

        # Calculate weighted confluence - PRESERVED original logic
        total_weight = 0
        weighted_signal_sum = 0
        participating_timeframes = []

        for tf in all_predictions.keys():
            if tf in all_confidences:
                signal = all_predictions[tf].iloc[-1] if hasattr(all_predictions[tf], 'iloc') else all_predictions[tf]
                confidence = all_confidences[tf].iloc[-1] if hasattr(all_confidences[tf], 'iloc') else all_confidences[tf]

                # Dynamic minimum confidence - PRESERVED original threshold
                min_confidence = 0.15

                if confidence >= min_confidence:
                    weight = adaptive_weights.get(tf, 1.0) * confidence
                    contribution = signal * weight

                    weighted_signal_sum += contribution
                    total_weight += weight
                    participating_timeframes.append(tf)

                    debug_info['individual_contributions'][tf] = {
                        'signal': signal,
                        'confidence': confidence,
                        'weight': weight,
                        'contribution': contribution
                    }

                    # NEW: Track for profit attribution
                    timeframe_contributions[tf] = {
                        'signal': signal,
                        'confidence': confidence,
                        'weight_used': weight,
                        'contribution': contribution,
                        'market_regime': market_regime
                    }

        if total_weight == 0:
            logger.debug("No valid signals after filtering")
            return 1, 0.0, [], debug_info

        # Calculate weighted average - PRESERVED original logic
        weighted_average = weighted_signal_sum / total_weight

        # Dynamic thresholds - PRESERVED original values
        sell_threshold = 0.8
        buy_threshold = 1.2

        # Determine final signal - PRESERVED original logic
        if weighted_average < sell_threshold:
            final_signal = 0  # SELL
        elif weighted_average > buy_threshold:
            final_signal = 2  # BUY
        else:
            final_signal = 1  # HOLD

        # Calculate confluence strength - PRESERVED original logic
        confluence_strength = self.calculate_confluence_strength(
            final_signal, debug_info['individual_contributions'], total_weight
        )

        debug_info['final_calculation'] = {
            'weighted_average': weighted_average,
            'sell_threshold': sell_threshold,
            'buy_threshold': buy_threshold,
            'final_signal': final_signal
        }

        # NEW: Store timeframe contributions for later profit attribution
        debug_info['timeframe_contributions'] = timeframe_contributions

        logger.debug(f"Dynamic confluence calculated: signal={final_signal}, strength={confluence_strength:.3f}")

        return final_signal, confluence_strength, participating_timeframes, debug_info

    def get_adaptive_weights(self, all_confidences, market_regime=None):
        """Get dynamically adapted weights - ENHANCED with regime-specific learning - PRESERVED original logic"""

        # NEW: Use regime-specific weights if available and proven profitable
        if market_regime and market_regime in self.regime_specific_weights:
            regime_weights = self.regime_specific_weights[market_regime]
            if regime_weights.get('proven_profitable', False):
                base_weights = regime_weights['weights'].copy()
                self.log_learning_event("REGIME_WEIGHTS_USED",
                    f"Using proven {market_regime} weights: {base_weights}")
            else:
                base_weights = self.learned_weights.copy()
        else:
            base_weights = self.learned_weights.copy()

        adaptive_weights = base_weights.copy()

        # Confidence-based adjustments - PRESERVED original logic
        for tf, confidence in all_confidences.items():
            if tf in adaptive_weights:
                conf_value = confidence.iloc[-1] if hasattr(confidence, 'iloc') else confidence

                # High confidence gets more weight - PRESERVED original multipliers
                if conf_value > 0.75:
                    adaptive_weights[tf] *= 1.3
                elif conf_value < 0.3:
                    adaptive_weights[tf] *= 0.7

                # Keep within bounds - PRESERVED original bounds
                adaptive_weights[tf] = max(0.2, min(4.0, adaptive_weights[tf]))

        return adaptive_weights

    def analyze_voting_patterns(self, all_predictions, all_confidences):
        """Analyze raw voting patterns across timeframes - PRESERVED original logic"""
        vote_counts = {'buy': 0, 'sell': 0, 'hold': 0}
        timeframe_signals = {}

        for tf in all_predictions.keys():
            if tf in all_confidences:
                signal = all_predictions[tf].iloc[-1] if hasattr(all_predictions[tf], 'iloc') else all_predictions[tf]
                confidence = all_confidences[tf].iloc[-1] if hasattr(all_confidences[tf], 'iloc') else all_confidences[tf]

                timeframe_signals[tf] = {'signal': signal, 'confidence': confidence}

                # PRESERVED original signal categorization
                if signal == 0: vote_counts['sell'] += 1
                elif signal == 2: vote_counts['buy'] += 1
                else: vote_counts['hold'] += 1

        return {
            'vote_counts': vote_counts,
            'timeframe_signals': timeframe_signals,
            'total_timeframes': len(timeframe_signals)
        }

    def check_consensus_patterns(self, all_predictions, all_confidences, vote_analysis):
        """
        Check for strong consensus patterns - PRESERVED original scalping scenario detector
        """
        timeframe_signals = vote_analysis['timeframe_signals']

        # PRESERVED: Short-term scalping consensus detection
        short_term_tfs = ['5m', '15m', '30m']
        short_term_signals = []
        short_term_confidences = []

        for tf in short_term_tfs:
            if tf in timeframe_signals:
                short_term_signals.append(timeframe_signals[tf]['signal'])
                short_term_confidences.append(timeframe_signals[tf]['confidence'])

        # Check for strong short-term consensus - PRESERVED original logic
        if len(short_term_signals) >= 3:
            unique_signals = set(short_term_signals)

            if len(unique_signals) == 1:  # All agree
                consensus_signal = short_term_signals[0]
                avg_confidence = np.mean(short_term_confidences)

                # Strong consensus requirements - PRESERVED original thresholds
                strong_30m = timeframe_signals.get('30m', {}).get('confidence', 0) > 0.7

                if avg_confidence > 0.6 and strong_30m and consensus_signal != 1:
                    return {
                        'override': True,
                        'signal': consensus_signal,
                        'strength': avg_confidence,
                        'timeframes': short_term_tfs,
                        'strategy': 'short_term_scalping_consensus',
                        'reason': f"Strong {short_term_tfs} consensus with 30m confidence {strong_30m}"
                    }

        # Check for overwhelming majority - PRESERVED original logic
        vote_counts = vote_analysis['vote_counts']
        total_votes = vote_analysis['total_timeframes']

        if vote_counts['buy'] >= max(4, total_votes * 0.8):
            return {
                'override': True,
                'signal': 2,
                'strength': 0.8,
                'timeframes': [tf for tf, data in timeframe_signals.items() if data['signal'] == 2],
                'strategy': 'overwhelming_buy_majority',
                'reason': f"{vote_counts['buy']}/{total_votes} BUY votes"
            }

        elif vote_counts['sell'] >= max(4, total_votes * 0.8):
            return {
                'override': True,
                'signal': 0,
                'strength': 0.8,
                'timeframes': [tf for tf, data in timeframe_signals.items() if data['signal'] == 0],
                'strategy': 'overwhelming_sell_majority',
                'reason': f"{vote_counts['sell']}/{total_votes} SELL votes"
            }

        # No override needed
        return {'override': False}

    def calculate_confluence_strength(self, final_signal, contributions, total_weight):
        """Calculate how strong the confluence is for the final signal - PRESERVED original logic"""
        if final_signal == 1:  # HOLD
            # Calculate agreement strength for HOLD signals - PRESERVED original calculation
            deviation_sum = 0
            for tf_data in contributions.values():
                deviation = abs(tf_data["signal"] - 1.0)
                deviation_sum += deviation * tf_data["weight"]
            avg_deviation = deviation_sum / total_weight if total_weight > 0 else 0
            return max(0.0, 1.0 - avg_deviation)

        # Sum weights of timeframes that agree with final signal - PRESERVED original logic
        agreement_weight = 0
        for tf, contrib_data in contributions.items():
            # Categorize individual signal the same way as final signal - PRESERVED original categorization
            individual_signal = contrib_data["signal"]
            if individual_signal < 0.8:  # SELL category
                individual_category = 0
            elif individual_signal > 1.2:  # BUY category
                individual_category = 2
            else:  # HOLD category
                individual_category = 1

            if individual_category == final_signal:
                agreement_weight += contrib_data['weight']

        return agreement_weight / total_weight if total_weight > 0 else 0.0

    # NEW: Profit Attribution Analysis
    def analyze_timeframe_profit_contribution(self):
        """Track which timeframes contribute most to profitable trades"""
        try:
            if len(self.performance_history) < 10:
                self.log_learning_event("PROFIT_ATTRIBUTION_SKIP", "Insufficient trade history for analysis")
                return

            timeframe_performance = {}

            # Initialize timeframe tracking
            for tf in self.base_weights.keys():
                timeframe_performance[tf] = {
                    'total_profit': 0.0,
                    'profitable_trades': 0,
                    'total_trades': 0,
                    'avg_profit': 0.0,
                    'win_rate': 0.0,
                    'contribution_score': 0.0
                }

            # Analyze each trade's timeframe contributions
            for trade in self.performance_history:
                if not trade.get('debug_info') or not trade.get('actual_profit'):
                    continue

                actual_profit = trade['actual_profit']
                timeframe_contributions = trade.get('debug_info', {}).get('timeframe_contributions', {})

                for tf, contribution_data in timeframe_contributions.items():
                    if tf in timeframe_performance:
                        # Weight the profit by this timeframe's contribution strength
                        contribution_weight = contribution_data.get('weight_used', 1.0)
                        confidence = contribution_data.get('confidence', 0.5)

                        # Calculate this timeframe's attribution for this trade
                        attribution_factor = (contribution_weight * confidence) / 10.0  # Normalize
                        attributed_profit = actual_profit * attribution_factor

                        timeframe_performance[tf]['total_profit'] += attributed_profit
                        timeframe_performance[tf]['total_trades'] += 1

                        if attributed_profit > 0:
                            timeframe_performance[tf]['profitable_trades'] += 1

            # Calculate final metrics
            for tf, perf in timeframe_performance.items():
                if perf['total_trades'] > 0:
                    perf['avg_profit'] = perf['total_profit'] / perf['total_trades']
                    perf['win_rate'] = perf['profitable_trades'] / perf['total_trades']
                    perf['contribution_score'] = perf['avg_profit'] * perf['win_rate']

            # Update stored data with atomic write
            self.profit_attribution_data['timeframe_performance'] = timeframe_performance
            self.profit_attribution_data['last_analysis'] = datetime.now().isoformat()

            # Log results
            sorted_tfs = sorted(timeframe_performance.items(),
                              key=lambda x: x[1]['contribution_score'], reverse=True)

            self.log_learning_event("PROFIT_ATTRIBUTION_ANALYSIS",
                f"Best performing timeframes: {[(tf, round(perf['contribution_score'], 4)) for tf, perf in sorted_tfs[:3]]}")

            logger.info("📊 PROFIT ATTRIBUTION ANALYSIS:")
            for tf, perf in sorted_tfs:
                logger.info(f"   {tf}: Score={perf['contribution_score']:.4f}, "
                          f"Win Rate={perf['win_rate']:.2%}, "
                          f"Avg Profit=${perf['avg_profit']:.4f}")

            return timeframe_performance

        except Exception as e:
            logger.error(f"Error in profit attribution analysis: {e}")
            self.log_learning_event("PROFIT_ATTRIBUTION_ERROR", str(e))
            return {}

    # NEW: Weight Optimization Analysis
    def analyze_optimal_weight_scenarios(self):
        """Analyze what weight combinations would have maximized profits"""
        try:
            if len(self.performance_history) < 15:
                self.log_learning_event("WEIGHT_OPTIMIZATION_SKIP", "Insufficient trade history for optimization")
                return

            # Get recent profitable and unprofitable trades
            recent_trades = self.performance_history[-30:]  # Last 30 trades
            profitable_trades = [t for t in recent_trades if t.get('actual_profit', 0) > 0]

            if len(profitable_trades) < 5:
                self.log_learning_event("WEIGHT_OPTIMIZATION_SKIP", "Insufficient profitable trades for optimization")
                return

            # Test different weight scenarios
            weight_scenarios = self.generate_weight_scenarios()
            scenario_results = []

            for scenario_name, weights in weight_scenarios.items():
                scenario_score = self.evaluate_weight_scenario(weights, recent_trades)
                scenario_results.append({
                    'scenario': scenario_name,
                    'weights': weights,
                    'theoretical_profit': scenario_score['total_profit'],
                    'theoretical_win_rate': scenario_score['win_rate'],
                    'trades_taken': scenario_score['trades_taken'],
                    'score': scenario_score['total_profit'] * scenario_score['win_rate']
                })

            # Find best performing scenario
            best_scenario = max(scenario_results, key=lambda x: x['score'])
            current_scenario_score = self.evaluate_weight_scenario(self.learned_weights, recent_trades)

            # Log optimization results
            optimization_result = {
                'timestamp': datetime.now().isoformat(),
                'current_weights': self.learned_weights.copy(),
                'current_performance': current_scenario_score,
                'best_scenario': best_scenario,
                'improvement_potential': best_scenario['score'] - current_scenario_score['total_profit'],
                'all_scenarios': scenario_results
            }

            self.weight_optimization_history.append(optimization_result)

            # Keep only recent optimization history
            if len(self.weight_optimization_history) > 20:
                self.weight_optimization_history = self.weight_optimization_history[-20:]

            improvement = best_scenario['theoretical_profit'] - current_scenario_score['total_profit']

            self.log_learning_event("WEIGHT_OPTIMIZATION_ANALYSIS",
                f"Best scenario: {best_scenario['scenario']}, "
                f"Improvement potential: ${improvement:.4f}, "
                f"Current profit: ${current_scenario_score['total_profit']:.4f}")

            # If significant improvement potential, suggest weight update
            if improvement > 1.0:  # $1+ improvement potential
                self.log_learning_event("WEIGHT_OPTIMIZATION_SUGGESTION",
                    f"Consider adopting {best_scenario['scenario']} weights: {best_scenario['weights']}")

                logger.info(f"🎯 WEIGHT OPTIMIZATION: {best_scenario['scenario']} could improve profits by ${improvement:.2f}")
                logger.info(f"   Current weights: {self.learned_weights}")
                logger.info(f"   Suggested weights: {best_scenario['weights']}")

            return optimization_result

        except Exception as e:
            logger.error(f"Error in weight optimization analysis: {e}")
            self.log_learning_event("WEIGHT_OPTIMIZATION_ERROR", str(e))
            return {}

    # NEW: Generate weight scenarios for testing
    def generate_weight_scenarios(self):
        """Generate different weight scenarios to test"""
        scenarios = {
            'short_term_focused': {'5m': 2.5, '15m': 2.0, '30m': 1.5, '1h': 1.0, '4h': 0.8},
            'medium_term_focused': {'5m': 1.0, '15m': 1.5, '30m': 2.5, '1h': 2.0, '4h': 1.8},
            'long_term_focused': {'5m': 0.8, '15m': 1.0, '30m': 1.5, '1h': 2.5, '4h': 3.0},
            'balanced_equal': {'5m': 1.5, '15m': 1.5, '30m': 1.5, '1h': 1.5, '4h': 1.5},
            'scalping_optimized': {'5m': 3.0, '15m': 2.5, '30m': 2.0, '1h': 1.0, '4h': 0.5},
            'trend_following': {'5m': 0.5, '15m': 1.0, '30m': 1.5, '1h': 2.5, '4h': 3.5},
            'current_learned': self.learned_weights.copy()
        }
        return scenarios

    # NEW: Evaluate weight scenario performance
    def evaluate_weight_scenario(self, weights, trades):
        """Evaluate how a weight scenario would have performed"""
        total_profit = 0.0
        profitable_trades = 0
        trades_taken = 0

        for trade in trades:
            if not trade.get('debug_info') or not trade.get('actual_profit'):
                continue

            # Recalculate confluence with these weights
            timeframe_contributions = trade.get('debug_info', {}).get('timeframe_contributions', {})

            if not timeframe_contributions:
                continue

            # Simulate confluence calculation with new weights
            total_weight = 0
            weighted_signal_sum = 0

            for tf, contribution in timeframe_contributions.items():
                if tf in weights:
                    weight = weights[tf] * contribution.get('confidence', 0.5)
                    weighted_signal_sum += contribution.get('signal', 1) * weight
                    total_weight += weight

            if total_weight == 0:
                continue

            weighted_average = weighted_signal_sum / total_weight

            # Would this scenario have taken the trade? - PRESERVED original thresholds
            would_take_trade = False
            if weighted_average < 0.8:  # SELL threshold
                would_take_trade = True
            elif weighted_average > 1.2:  # BUY threshold
                would_take_trade = True

            if would_take_trade:
                trades_taken += 1
                actual_profit = trade['actual_profit']
                total_profit += actual_profit

                if actual_profit > 0:
                    profitable_trades += 1

        win_rate = profitable_trades / trades_taken if trades_taken > 0 else 0

        return {
            'total_profit': total_profit,
            'win_rate': win_rate,
            'trades_taken': trades_taken,
            'profitable_trades': profitable_trades
        }

    # NEW: Learn regime-specific optimal weights
    def learn_regime_specific_weights(self, market_regime):
        """Learn optimal weights for specific market regimes"""
        try:
            regime_trades = [
                trade for trade in self.performance_history
                if trade.get('debug_info', {}).get('market_regime') == market_regime
            ]

            if len(regime_trades) < 10:
                return

            # Test weight scenarios specifically for this regime
            weight_scenarios = self.generate_weight_scenarios()
            best_scenario = None
            best_score = -float('inf')

            for scenario_name, weights in weight_scenarios.items():
                scenario_performance = self.evaluate_weight_scenario(weights, regime_trades)
                score = scenario_performance['total_profit'] * scenario_performance['win_rate']

                if score > best_score:
                    best_score = score
                    best_scenario = {
                        'scenario': scenario_name,
                        'weights': weights,
                        'performance': scenario_performance
                    }

            if best_scenario and best_scenario['performance']['total_profit'] > 0:
                self.regime_specific_weights[market_regime] = {
                    'weights': best_scenario['weights'],
                    'performance': best_scenario['performance'],
                    'proven_profitable': True,
                    'learned_date': datetime.now().isoformat()
                }

                self.log_learning_event("REGIME_WEIGHTS_LEARNED",
                    f"Learned optimal weights for {market_regime}: {best_scenario['weights']}")

        except Exception as e:
            logger.error(f"Error learning regime-specific weights: {e}")

    def record_trade_outcome(self, debug_info, trade_result, actual_profit):
        """Record trade outcome for continuous learning - ENHANCED with profit attribution - PRESERVED original logic"""

        outcome_record = {
            'timestamp': datetime.now().isoformat(),
            'debug_info': debug_info,
            'trade_executed': trade_result is not None,
            'actual_profit': actual_profit,
            'success': actual_profit > 0,
            'weights_used': debug_info.get('weights_used', {}),
            'market_regime': debug_info.get('market_regime', 'unknown'),  # NEW
            'timeframe_contributions': debug_info.get('timeframe_contributions', {})  # NEW
        }

        self.performance_history.append(outcome_record)

        # Keep recent history - PRESERVED original limit
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        # NEW: Trigger analysis every 10 trades
        if len(self.performance_history) % 10 == 0:
            self.log_learning_event("PERIODIC_ANALYSIS_TRIGGER", f"Running analysis after trade #{len(self.performance_history)}")

            # Run profit attribution analysis
            self.analyze_timeframe_profit_contribution()

            # Run weight optimization analysis
            self.analyze_optimal_weight_scenarios()

            # Learn regime-specific weights if we have enough data
            market_regime = debug_info.get('market_regime')
            if market_regime and market_regime != 'unknown':
                self.learn_regime_specific_weights(market_regime)

        # Save performance data with atomic writes
        self.save_performance_data()

    def save_performance_data(self):
        """Save performance history and learned weights with atomic writes - ENHANCED"""
        try:
            # Save performance history atomically
            if not safe_backup_and_write(self.performance_file, self.performance_history):
                logger.warning(f"Failed to save performance history to {self.performance_file}")
                return False

            # Save learned weights atomically
            weights_data = {
                'weights': self.learned_weights,
                'last_updated': datetime.now().isoformat(),
                'total_trades_learned': len(self.performance_history),
                'regime_specific_weights': self.regime_specific_weights  # NEW
            }

            if not safe_backup_and_write(self.weights_file, weights_data):
                logger.warning(f"Failed to save weights to {self.weights_file}")
                return False

            # NEW: Save profit attribution data atomically
            if not safe_backup_and_write(self.profit_attribution_file, self.profit_attribution_data):
                logger.warning(f"Failed to save profit attribution to {self.profit_attribution_file}")

            # NEW: Save weight optimization history atomically
            if not safe_backup_and_write(self.weight_optimization_file, self.weight_optimization_history):
                logger.warning(f"Failed to save weight optimization to {self.weight_optimization_file}")

            logger.debug("All performance data saved successfully with atomic writes")
            return True

        except Exception as e:
            logger.error(f"Error in save_performance_data: {e}")
            return False

    # NEW: Get learning status report
    def get_learning_status_report(self):
        """Generate comprehensive learning status report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_trades_learned': len(self.performance_history),
                'learning_active': len(self.performance_history) >= self.min_trades_for_learning,
                'current_weights': self.learned_weights.copy(),
                'base_weights': self.base_weights.copy(),
                'weight_changes': {},
                'profit_attribution': {},
                'optimization_status': {},
                'regime_learning': {}
            }

            # Calculate weight changes from base
            for tf in self.base_weights:
                base_weight = self.base_weights[tf]
                current_weight = self.learned_weights.get(tf, base_weight)
                change_pct = ((current_weight - base_weight) / base_weight * 100) if base_weight > 0 else 0
                report['weight_changes'][tf] = {
                    'base': base_weight,
                    'current': current_weight,
                    'change_percent': change_pct
                }

            # Add profit attribution summary
            if self.profit_attribution_data.get('timeframe_performance'):
                tf_perf = self.profit_attribution_data['timeframe_performance']
                best_tf = max(tf_perf.items(), key=lambda x: x[1].get('contribution_score', 0))
                worst_tf = min(tf_perf.items(), key=lambda x: x[1].get('contribution_score', 0))

                report['profit_attribution'] = {
                    'best_timeframe': best_tf[0],
                    'best_score': best_tf[1].get('contribution_score', 0),
                    'worst_timeframe': worst_tf[0],
                    'worst_score': worst_tf[1].get('contribution_score', 0),
                    'last_analysis': self.profit_attribution_data.get('last_analysis')
                }

            # Add optimization status
            if self.weight_optimization_history:
                latest_opt = self.weight_optimization_history[-1]
                report['optimization_status'] = {
                    'last_analysis': latest_opt.get('timestamp'),
                    'improvement_potential': latest_opt.get('improvement_potential', 0),
                    'best_scenario': latest_opt.get('best_scenario', {}).get('scenario', 'unknown')
                }

            # Add regime learning status
            report['regime_learning'] = {
                'regimes_learned': list(self.regime_specific_weights.keys()),
                'total_regimes': len(self.regime_specific_weights)
            }

            return report

        except Exception as e:
            logger.error(f"Error generating learning status report: {e}")
            return {'error': str(e)}

    # NEW: Advanced learning recommendations
    def get_learning_recommendations(self):
        """Get actionable learning recommendations"""
        try:
            recommendations = []

            # Check if we need more data
            if len(self.performance_history) < self.min_trades_for_learning:
                recommendations.append({
                    'type': 'data_collection',
                    'priority': 'high',
                    'message': f"Need {self.min_trades_for_learning - len(self.performance_history)} more trades for active learning"
                })

            # Check for significant weight optimization opportunities
            if self.weight_optimization_history:
                latest_opt = self.weight_optimization_history[-1]
                improvement = latest_opt.get('improvement_potential', 0)

                if improvement > 2.0:
                    recommendations.append({
                        'type': 'weight_optimization',
                        'priority': 'high',
                        'message': f"Significant improvement potential: ${improvement:.2f} with {latest_opt.get('best_scenario', {}).get('scenario', 'unknown')} weights"
                    })
                elif improvement > 0.5:
                    recommendations.append({
                        'type': 'weight_optimization',
                        'priority': 'medium',
                        'message': f"Moderate improvement potential: ${improvement:.2f}"
                    })

            # Check profit attribution insights
            if self.profit_attribution_data.get('timeframe_performance'):
                tf_perf = self.profit_attribution_data['timeframe_performance']

                # Find underperforming timeframes with high weights
                for tf, perf in tf_perf.items():
                    current_weight = self.learned_weights.get(tf, 1.0)
                    contribution_score = perf.get('contribution_score', 0)

                    if current_weight > 2.0 and contribution_score < 0:
                        recommendations.append({
                            'type': 'weight_adjustment',
                            'priority': 'medium',
                            'message': f"Consider reducing {tf} weight (currently {current_weight:.1f}, poor performance: {contribution_score:.4f})"
                        })

            # Check regime learning opportunities
            available_regimes = set()
            for trade in self.performance_history:
                regime = trade.get('debug_info', {}).get('market_regime')
                if regime and regime != 'unknown':
                    available_regimes.add(regime)

            for regime in available_regimes:
                if regime not in self.regime_specific_weights:
                    regime_trades = [t for t in self.performance_history
                                   if t.get('debug_info', {}).get('market_regime') == regime]
                    if len(regime_trades) >= 10:
                        recommendations.append({
                            'type': 'regime_learning',
                            'priority': 'low',
                            'message': f"Ready to learn {regime} specific weights ({len(regime_trades)} trades available)"
                        })

            return recommendations

        except Exception as e:
            logger.error(f"Error generating learning recommendations: {e}")
            return [{'type': 'error', 'priority': 'high', 'message': f"Error generating recommendations: {e}"}]

# Export the main class
__all__ = ['DynamicConfluenceEngine']

logger.info("✅ dynamic_confluence_engine.py v1.0 loaded successfully with profit attribution and weight optimization")

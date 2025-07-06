# Version: 2.0 - COMPLETE ADAPTIVE Shadow Trading System with Dynamic Strategy Learning
# This system tracks EVERY trading signal, learns what works, and dynamically adapts the main system
# Features: All indicators analysis, harmonic patterns, adaptive thresholds, strategy optimization
# CRITICAL: Includes adaptive learning that changes main system behavior based on profitable patterns

import pandas as pd
import numpy as np
import os
import json
import time
from datetime import datetime, timedelta
from config import PAIR, DEPENDENCY_DIR, DYNAMIC_PARAMS
from logging_setup import logger
import threading
from collections import defaultdict

class AdaptiveStrategyLearner:
    """
    Learns which strategies are most profitable and adapts main system behavior
    """
    
    def __init__(self, pair):
        self.pair = pair
        self.adaptation_file = os.path.join(DEPENDENCY_DIR, f"adaptive_strategy_{pair.lower()}.json")
        self.min_trades_for_adaptation = 20
        self.confidence_threshold = 0.75  # Require 75% confidence before adapting
        self.adaptation_history = []
        self.current_adaptations = {}
        self.load_adaptation_state()
    
    def load_adaptation_state(self):
        """Load existing adaptation state"""
        try:
            if os.path.exists(self.adaptation_file):
                with open(self.adaptation_file, 'r') as f:
                    data = json.load(f)
                    self.adaptation_history = data.get('adaptation_history', [])
                    self.current_adaptations = data.get('current_adaptations', {})
                    logger.info(f"Loaded adaptation state: {len(self.adaptation_history)} adaptations, "
                               f"{len(self.current_adaptations)} active")
        except Exception as e:
            logger.error(f"Error loading adaptation state: {e}")
            self.adaptation_history = []
            self.current_adaptations = {}
    
    def save_adaptation_state(self):
        """Save adaptation state"""
        try:
            data = {
                'adaptation_history': self.adaptation_history,
                'current_adaptations': self.current_adaptations,
                'last_updated': datetime.now().isoformat(),
                'pair': self.pair
            }
            with open(self.adaptation_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving adaptation state: {e}")
    
    def analyze_strategy_performance(self, shadow_data):
        """Analyze which strategies are performing best"""
        try:
            if len(shadow_data) < self.min_trades_for_adaptation:
                return None
            
            strategy_performance = {}
            
            # Group by strategy and analyze outcomes
            for strategy_name in ['oscillator_divergence', 'trend_alignment', 'mean_reversion_volume', 
                                'harmonic_patterns', 'breakout_momentum', 'multi_indicator_confluence', 
                                'advanced_patterns']:
                
                # Find signals from this strategy
                strategy_signals = []
                for record in shadow_data:
                    if (record.get('type') == 'comprehensive_shadow' and 
                        strategy_name in str(record.get('reasoning', []))):
                        strategy_signals.append(record)
                
                if len(strategy_signals) >= 5:  # Minimum for analysis
                    profits = [s.get('theoretical_profit_15m', 0) for s in strategy_signals if 'theoretical_profit_15m' in s]
                    
                    if profits:
                        win_rate = sum(1 for p in profits if p > 0) / len(profits)
                        avg_profit = np.mean(profits)
                        total_profit = sum(profits)
                        
                        strategy_performance[strategy_name] = {
                            'signals': len(strategy_signals),
                            'win_rate': win_rate,
                            'avg_profit': avg_profit,
                            'total_profit': total_profit,
                            'score': win_rate * avg_profit * len(strategy_signals),  # Combined score
                            'last_updated': datetime.now().isoformat()
                        }
            
            return strategy_performance
        
        except Exception as e:
            logger.error(f"Error analyzing strategy performance: {e}")
            return None
    
    def determine_adaptations(self, strategy_performance):
        """Determine what adaptations to make based on performance"""
        try:
            adaptations = {}
            
            if not strategy_performance:
                return adaptations
            
            # Sort strategies by performance score
            sorted_strategies = sorted(
                strategy_performance.items(), 
                key=lambda x: x[1]['score'], 
                reverse=True
            )
            
            best_strategy = sorted_strategies[0]
            best_name, best_stats = best_strategy
            
            # Only adapt if the best strategy is significantly better
            if (best_stats['win_rate'] > 0.7 and 
                best_stats['avg_profit'] > 0.02 and 
                best_stats['signals'] >= 10):
                
                logger.info(f"🎯 ADAPTATION CANDIDATE: {best_name}")
                logger.info(f"   Performance: {best_stats['win_rate']:.1%} win rate, "
                           f"{best_stats['avg_profit']:+.2%} avg profit, {best_stats['signals']} signals")
                
                # Determine specific adaptations based on strategy
                if best_name == 'oscillator_divergence':
                    adaptations.update({
                        'lower_rsi_threshold': 35,  # More sensitive to RSI
                        'enable_stoch_signals': True,
                        'oscillator_weight': 1.5,
                        'reason': f'Oscillator strategy shows {best_stats["win_rate"]:.1%} win rate'
                    })
                
                elif best_name == 'trend_alignment':
                    adaptations.update({
                        'increase_trend_weight': 1.4,
                        'enable_macd_crossovers': True,
                        'adx_threshold': 20,  # Lower ADX requirement
                        'reason': f'Trend alignment strategy shows {best_stats["win_rate"]:.1%} win rate'
                    })
                
                elif best_name == 'harmonic_patterns':
                    adaptations.update({
                        'enable_harmonic_trading': True,
                        'harmonic_confidence_threshold': 0.6,
                        'harmonic_weight': 2.0,
                        'reason': f'Harmonic patterns show {best_stats["win_rate"]:.1%} win rate'
                    })
                
                elif best_name == 'mean_reversion_volume':
                    adaptations.update({
                        'enable_bollinger_signals': True,
                        'volume_confirmation_required': True,
                        'bb_threshold': 0.02,  # Closer to bands
                        'reason': f'Mean reversion shows {best_stats["win_rate"]:.1%} win rate'
                    })
                
                elif best_name == 'breakout_momentum':
                    adaptations.update({
                        'enable_breakout_trading': True,
                        'breakout_threshold': 0.995,  # More sensitive
                        'momentum_confirmation': True,
                        'reason': f'Breakout strategy shows {best_stats["win_rate"]:.1%} win rate'
                    })
                
                elif best_name == 'multi_indicator_confluence':
                    adaptations.update({
                        'lower_confluence_threshold': True,
                        'indicator_confluence_weight': 1.3,
                        'multi_indicator_mode': True,
                        'reason': f'Multi-indicator confluence shows {best_stats["win_rate"]:.1%} win rate'
                    })
                
                # Add confidence and performance metrics
                adaptations['adaptation_confidence'] = min(1.0, best_stats['score'] / 10.0)
                adaptations['based_on_signals'] = best_stats['signals']
                adaptations['timestamp'] = datetime.now().isoformat()
            
            return adaptations
        
        except Exception as e:
            logger.error(f"Error determining adaptations: {e}")
            return {}
    
    def apply_adaptations(self, adaptations):
        """Apply adaptations to the main trading system"""
        try:
            if not adaptations or adaptations.get('adaptation_confidence', 0) < self.confidence_threshold:
                return False
            
            # Store current adaptations
            self.current_adaptations = adaptations.copy()
            
            # Log the adaptation
            adaptation_record = {
                'timestamp': datetime.now().isoformat(),
                'adaptations': adaptations,
                'confidence': adaptations.get('adaptation_confidence', 0),
                'reason': adaptations.get('reason', 'Unknown'),
                'signals_analyzed': adaptations.get('based_on_signals', 0)
            }
            
            self.adaptation_history.append(adaptation_record)
            
            # Keep only recent adaptations
            if len(self.adaptation_history) > 50:
                self.adaptation_history = self.adaptation_history[-50:]
            
            # Save state
            self.save_adaptation_state()
            
            logger.warning(f"🚀 SYSTEM ADAPTATION APPLIED!")
            logger.warning(f"   Reason: {adaptations.get('reason', 'Performance optimization')}")
            logger.warning(f"   Confidence: {adaptations.get('adaptation_confidence', 0):.1%}")
            logger.warning(f"   Based on: {adaptations.get('based_on_signals', 0)} signals")
            
            # Apply to DYNAMIC_PARAMS (this affects the main trading system)
            self._update_dynamic_params(adaptations)
            
            return True
        
        except Exception as e:
            logger.error(f"Error applying adaptations: {e}")
            return False
    
    def _update_dynamic_params(self, adaptations):
        """Update DYNAMIC_PARAMS based on adaptations"""
        try:
            global DYNAMIC_PARAMS
            
            # Apply specific adaptations
            if adaptations.get('lower_rsi_threshold'):
                DYNAMIC_PARAMS['rsi_overbought_1'] = adaptations['lower_rsi_threshold'] + 35  # 70 becomes 70
                DYNAMIC_PARAMS['rsi_oversold_2'] = adaptations['lower_rsi_threshold'] - 5   # 30 becomes 30
                logger.info(f"   ✅ Adapted RSI thresholds: {adaptations['lower_rsi_threshold']}")
            
            if adaptations.get('lower_confluence_threshold'):
                DYNAMIC_PARAMS['min_confluence'] *= 0.8  # Lower by 20%
                logger.info(f"   ✅ Lowered confluence threshold to {DYNAMIC_PARAMS['min_confluence']:.3f}")
            
            if adaptations.get('enable_harmonic_trading'):
                DYNAMIC_PARAMS['harmonic_threshold'] = adaptations.get('harmonic_confidence_threshold', 0.6)
                logger.info(f"   ✅ Enabled harmonic trading with threshold {DYNAMIC_PARAMS['harmonic_threshold']}")
            
            if adaptations.get('enable_bollinger_signals'):
                DYNAMIC_PARAMS['use_bollinger_signals'] = True
                DYNAMIC_PARAMS['bb_sensitivity'] = adaptations.get('bb_threshold', 0.02)
                logger.info(f"   ✅ Enabled Bollinger Band signals")
            
            if adaptations.get('volume_confirmation_required'):
                DYNAMIC_PARAMS['volume_confirmation_required'] = True
                logger.info(f"   ✅ Enabled volume confirmation")
            
            if adaptations.get('enable_breakout_trading'):
                DYNAMIC_PARAMS['breakout_trading_enabled'] = True
                DYNAMIC_PARAMS['breakout_sensitivity'] = adaptations.get('breakout_threshold', 0.995)
                logger.info(f"   ✅ Enabled breakout trading")
            
            # Update confidence requirements
            if adaptations.get('adaptation_confidence', 0) > 0.8:
                DYNAMIC_PARAMS['confidence_requirement'] *= 0.9  # Slightly more aggressive
                logger.info(f"   ✅ Lowered confidence requirement to {DYNAMIC_PARAMS['confidence_requirement']:.3f}")
            
        except Exception as e:
            logger.error(f"Error updating dynamic params: {e}")
    
    def get_adaptation_status(self):
        """Get current adaptation status"""
        return {
            'active_adaptations': self.current_adaptations,
            'adaptation_count': len(self.adaptation_history),
            'last_adaptation': self.adaptation_history[-1] if self.adaptation_history else None,
            'adaptation_confidence': self.current_adaptations.get('adaptation_confidence', 0)
        }

class AdvancedIndicatorShadowAnalyzer:
    """
    Advanced shadow analyzer that uses ALL available indicators to find missed trades
    """
    
    def __init__(self, pair):
        self.pair = pair
        self.indicator_weights = {
            # Oscillators (mean reversion signals)
            'RSI': 0.25, 'STOCH_k': 0.20, 'STOCH_d': 0.15, 'WilliamsR': 0.15,
            'CCI': 0.20, 'UO': 0.15, 'VW_RSI': 0.25,
            
            # Trend indicators
            'MACD': 0.30, 'Signal': 0.20, 'PPO': 0.25, 'PPO_Signal': 0.15,
            'ADX': 0.20, 'Plus_DI': 0.15, 'Minus_DI': 0.15, 'ROC': 0.20,
            'EMA_slope': 0.25, 'momentum': 0.20, 'Trend_Strength': 0.30,
            
            # Volatility and channels
            'BB_Upper': 0.20, 'BB_Lower': 0.20, 'KC_Upper': 0.15, 'KC_Lower': 0.15,
            'ATR': 0.10,
            
            # Volume indicators
            'VW_MACD': 0.25, 'VW_Signal': 0.20, 'KO': 0.20,
            
            # Pattern indicators
            'Bull_Engulfing': 0.40, 'Bear_Engulfing': 0.40, 'STC': 0.20,
            'VI_Plus': 0.15, 'VI_Minus': 0.15,
            
            # Moving averages
            'SMA': 0.15, 'EMA': 0.20
        }
        
        # Harmonic pattern weights
        self.harmonic_weights = {
            'gartley': 0.35, 'bat': 0.40, 'butterfly': 0.45, 'crab': 0.50,
            'cypher': 0.30, 'abcd': 0.25, 'shark': 0.35, 'deep_crab': 0.45
        }

    def comprehensive_shadow_analysis(self, all_dataframes, current_price, main_system_decision):
        """
        COMPREHENSIVE analysis using ALL indicators to find what the main system missed
        """
        try:
            shadow_results = {
                'timestamp': datetime.now(),
                'current_price': current_price,
                'main_decision': main_system_decision,
                'shadow_strategies': {},
                'best_shadow_signal': None,
                'missed_opportunities': []
            }
            
            # Strategy 1: Oscillator Divergence Strategy
            osc_strategy = self._oscillator_divergence_strategy(all_dataframes)
            shadow_results['shadow_strategies']['oscillator_divergence'] = osc_strategy
            
            # Strategy 2: Multi-Timeframe Trend Alignment  
            trend_strategy = self._trend_alignment_strategy(all_dataframes)
            shadow_results['shadow_strategies']['trend_alignment'] = trend_strategy
            
            # Strategy 3: Mean Reversion + Volume Strategy
            mean_rev_strategy = self._mean_reversion_volume_strategy(all_dataframes)
            shadow_results['shadow_strategies']['mean_reversion_volume'] = mean_rev_strategy
            
            # Strategy 4: Harmonic Pattern Strategy
            harmonic_strategy = self._harmonic_pattern_strategy(all_dataframes)
            shadow_results['shadow_strategies']['harmonic_patterns'] = harmonic_strategy
            
            # Strategy 5: Breakout + Momentum Strategy
            breakout_strategy = self._breakout_momentum_strategy(all_dataframes)
            shadow_results['shadow_strategies']['breakout_momentum'] = breakout_strategy
            
            # Strategy 6: Multi-Indicator Confluence Strategy
            confluence_strategy = self._multi_indicator_confluence_strategy(all_dataframes)
            shadow_results['shadow_strategies']['multi_indicator_confluence'] = confluence_strategy
            
            # Strategy 7: Advanced Pattern Recognition
            pattern_strategy = self._advanced_pattern_strategy(all_dataframes)
            shadow_results['shadow_strategies']['advanced_patterns'] = pattern_strategy
            
            # Find the best shadow signal
            best_signal = self._find_best_shadow_signal(shadow_results['shadow_strategies'])
            shadow_results['best_shadow_signal'] = best_signal
            
            # Compare with main system
            missed_opportunities = self._identify_missed_opportunities(
                shadow_results, main_system_decision
            )
            shadow_results['missed_opportunities'] = missed_opportunities
            
            # Log comprehensive results
            self._log_comprehensive_analysis(shadow_results)
            
            return shadow_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive shadow analysis: {e}")
            return None

    def _oscillator_divergence_strategy(self, dataframes):
        """Strategy: Look for divergences in oscillators across timeframes"""
        try:
            strategy = {
                'name': 'Oscillator Divergence',
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            for tf, df in dataframes.items():
                if df is None or df.empty or len(df) < 10:
                    continue
                    
                tf_signals = {'buy_signals': 0, 'sell_signals': 0, 'strength': 0}
                
                # RSI analysis
                rsi_col = f'RSI_{tf}'
                if rsi_col in df.columns:
                    rsi = df[rsi_col].iloc[-1]
                    
                    if rsi < 25:  # Extreme oversold
                        tf_signals['buy_signals'] += 2
                        tf_signals['strength'] += 0.4
                        strategy['reasoning'].append(f'{tf}: RSI extreme oversold ({rsi:.1f})')
                    elif rsi < 35:  # Oversold
                        tf_signals['buy_signals'] += 1
                        tf_signals['strength'] += 0.2
                        strategy['reasoning'].append(f'{tf}: RSI oversold ({rsi:.1f})')
                    elif rsi > 75:  # Extreme overbought
                        tf_signals['sell_signals'] += 2
                        tf_signals['strength'] += 0.4
                        strategy['reasoning'].append(f'{tf}: RSI extreme overbought ({rsi:.1f})')
                    elif rsi > 65:  # Overbought
                        tf_signals['sell_signals'] += 1
                        tf_signals['strength'] += 0.2
                        strategy['reasoning'].append(f'{tf}: RSI overbought ({rsi:.1f})')
                
                # Stochastic analysis
                stoch_k_col = f'STOCH_k_{tf}'
                stoch_d_col = f'STOCH_d_{tf}'
                if stoch_k_col in df.columns and stoch_d_col in df.columns:
                    stoch_k = df[stoch_k_col].iloc[-1]
                    stoch_d = df[stoch_d_col].iloc[-1]
                    
                    if stoch_k < 20 and stoch_d < 20:  # Both oversold
                        tf_signals['buy_signals'] += 1
                        tf_signals['strength'] += 0.3
                        strategy['reasoning'].append(f'{tf}: Stoch double oversold')
                    elif stoch_k > 80 and stoch_d > 80:  # Both overbought
                        tf_signals['sell_signals'] += 1
                        tf_signals['strength'] += 0.3
                        strategy['reasoning'].append(f'{tf}: Stoch double overbought')
                    elif stoch_k > stoch_d and stoch_k < 50:  # Bullish crossover in oversold
                        tf_signals['buy_signals'] += 1
                        tf_signals['strength'] += 0.25
                        strategy['reasoning'].append(f'{tf}: Stoch bullish crossover')
                
                # Williams %R analysis
                williams_col = f'WilliamsR_{tf}'
                if williams_col in df.columns:
                    williams = df[williams_col].iloc[-1]
                    if williams < -80:  # Oversold
                        tf_signals['buy_signals'] += 1
                        tf_signals['strength'] += 0.2
                        strategy['reasoning'].append(f'{tf}: Williams %R oversold')
                    elif williams > -20:  # Overbought
                        tf_signals['sell_signals'] += 1
                        tf_signals['strength'] += 0.2
                        strategy['reasoning'].append(f'{tf}: Williams %R overbought')
                
                # CCI analysis
                cci_col = f'CCI_{tf}'
                if cci_col in df.columns:
                    cci = df[cci_col].iloc[-1]
                    if cci < -200:  # Extreme oversold
                        tf_signals['buy_signals'] += 2
                        tf_signals['strength'] += 0.3
                        strategy['reasoning'].append(f'{tf}: CCI extreme oversold ({cci:.0f})')
                    elif cci > 200:  # Extreme overbought
                        tf_signals['sell_signals'] += 2
                        tf_signals['strength'] += 0.3
                        strategy['reasoning'].append(f'{tf}: CCI extreme overbought ({cci:.0f})')
                
                strategy['signals'][tf] = tf_signals
            
            # Determine overall signal
            total_buy = sum(s['buy_signals'] for s in strategy['signals'].values())
            total_sell = sum(s['sell_signals'] for s in strategy['signals'].values())
            total_strength = sum(s['strength'] for s in strategy['signals'].values())
            
            if total_buy > total_sell and total_strength > 1.0:
                strategy['overall_signal'] = 'buy'
                strategy['confidence'] = min(1.0, total_strength / 3.0)
            elif total_sell > total_buy and total_strength > 1.0:
                strategy['overall_signal'] = 'sell'
                strategy['confidence'] = min(1.0, total_strength / 3.0)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in oscillator divergence strategy: {e}")
            return {'name': 'Oscillator Divergence', 'overall_signal': 'hold', 'confidence': 0.0}

    def _trend_alignment_strategy(self, dataframes):
        """Strategy: Multi-timeframe trend alignment using all trend indicators"""
        try:
            strategy = {
                'name': 'Trend Alignment',
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            timeframe_weights = {'5m': 1.0, '15m': 1.2, '30m': 1.4, '1h': 1.6, '4h': 1.8, '6h': 2.0}
            
            for tf, df in dataframes.items():
                if df is None or df.empty or len(df) < 10:
                    continue
                    
                tf_weight = timeframe_weights.get(tf, 1.0)
                tf_signals = {'trend_score': 0, 'strength': 0}
                
                # MACD analysis
                macd_col = f'MACD_{tf}'
                signal_col = f'Signal_{tf}'
                if macd_col in df.columns and signal_col in df.columns:
                    macd = df[macd_col].iloc[-1]
                    signal_line = df[signal_col].iloc[-1]
                    macd_prev = df[macd_col].iloc[-2] if len(df) >= 2 else macd
                    signal_prev = df[signal_col].iloc[-2] if len(df) >= 2 else signal_line
                    
                    if macd > signal_line:
                        tf_signals['trend_score'] += 1 * tf_weight
                        if macd_prev <= signal_prev:  # Fresh crossover
                            tf_signals['trend_score'] += 0.5 * tf_weight
                            strategy['reasoning'].append(f'{tf}: MACD bullish crossover')
                    elif macd < signal_line:
                        tf_signals['trend_score'] -= 1 * tf_weight
                        if macd_prev >= signal_prev:  # Fresh crossover
                            tf_signals['trend_score'] -= 0.5 * tf_weight
                            strategy['reasoning'].append(f'{tf}: MACD bearish crossover')
                
                # ADX + DI analysis
                adx_col = f'ADX_{tf}'
                plus_di_col = f'Plus_DI_{tf}'
                minus_di_col = f'Minus_DI_{tf}'
                if all(col in df.columns for col in [adx_col, plus_di_col, minus_di_col]):
                    adx = df[adx_col].iloc[-1]
                    plus_di = df[plus_di_col].iloc[-1]
                    minus_di = df[minus_di_col].iloc[-1]
                    
                    if adx > 25:  # Strong trend
                        if plus_di > minus_di:
                            tf_signals['trend_score'] += 0.8 * tf_weight
                            strategy['reasoning'].append(f'{tf}: Strong uptrend (ADX={adx:.0f})')
                        else:
                            tf_signals['trend_score'] -= 0.8 * tf_weight
                            strategy['reasoning'].append(f'{tf}: Strong downtrend (ADX={adx:.0f})')
                
                # EMA slope analysis
                ema_slope_col = f'EMA_slope_{tf}'
                if ema_slope_col in df.columns:
                    ema_slope = df[ema_slope_col].iloc[-1]
                    if ema_slope > 0.5:
                        tf_signals['trend_score'] += 0.6 * tf_weight
                        strategy['reasoning'].append(f'{tf}: Strong EMA upslope')
                    elif ema_slope < -0.5:
                        tf_signals['trend_score'] -= 0.6 * tf_weight
                        strategy['reasoning'].append(f'{tf}: Strong EMA downslope')
                
                # ROC analysis
                roc_col = f'ROC_{tf}'
                if roc_col in df.columns:
                    roc = df[roc_col].iloc[-1]
                    if roc > 2:
                        tf_signals['trend_score'] += 0.4 * tf_weight
                        strategy['reasoning'].append(f'{tf}: Strong momentum (ROC={roc:.1f})')
                    elif roc < -2:
                        tf_signals['trend_score'] -= 0.4 * tf_weight
                        strategy['reasoning'].append(f'{tf}: Strong negative momentum')
                
                tf_signals['strength'] = abs(tf_signals['trend_score'])
                strategy['signals'][tf] = tf_signals
            
            # Calculate overall trend alignment
            total_trend_score = sum(s['trend_score'] for s in strategy['signals'].values())
            total_strength = sum(s['strength'] for s in strategy['signals'].values())
            
            if total_trend_score > 2.0:
                strategy['overall_signal'] = 'buy'
                strategy['confidence'] = min(1.0, total_strength / 8.0)
            elif total_trend_score < -2.0:
                strategy['overall_signal'] = 'sell'
                strategy['confidence'] = min(1.0, total_strength / 8.0)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in trend alignment strategy: {e}")
            return {'name': 'Trend Alignment', 'overall_signal': 'hold', 'confidence': 0.0}

    def _harmonic_pattern_strategy(self, dataframes):
        """Strategy: Advanced harmonic pattern detection across all timeframes"""
        try:
            strategy = {
                'name': 'Harmonic Patterns',
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            for tf, df in dataframes.items():
                if df is None or df.empty:
                    continue
                    
                tf_signals = {'patterns': [], 'max_confidence': 0, 'direction': 'hold'}
                
                # Check for harmonic pattern columns
                pattern_cols = [col for col in df.columns if 'harmonic' in col.lower() or 'pattern' in col.lower()]
                
                if pattern_cols:
                    for col in pattern_cols:
                        try:
                            pattern_data = df[col].iloc[-1]
                            if pd.notna(pattern_data) and pattern_data != 'None':
                                # Extract pattern info
                                if isinstance(pattern_data, str) and '_' in pattern_data:
                                    direction, pattern_type = pattern_data.split('_', 1)
                                    
                                    # Get pattern confidence if available
                                    conf_col = col.replace('pattern', 'confidence')
                                    confidence = 0.7  # Default
                                    if conf_col in df.columns:
                                        confidence = df[conf_col].iloc[-1]
                                        if pd.isna(confidence):
                                            confidence = 0.7
                                    
                                    pattern_weight = self.harmonic_weights.get(pattern_type, 0.3)
                                    weighted_confidence = confidence * pattern_weight
                                    
                                    tf_signals['patterns'].append({
                                        'type': pattern_type,
                                        'direction': direction,
                                        'confidence': confidence,
                                        'weighted_confidence': weighted_confidence
                                    })
                                    
                                    if weighted_confidence > tf_signals['max_confidence']:
                                        tf_signals['max_confidence'] = weighted_confidence
                                        tf_signals['direction'] = direction
                                    
                                    strategy['reasoning'].append(
                                        f'{tf}: {direction} {pattern_type} pattern (conf: {confidence:.2f})'
                                    )
                        except Exception as e:
                            logger.debug(f"Error processing pattern column {col}: {e}")
                            continue
                
                # Also check for specific harmonic pattern indicators
                harmonic_indicators = [
                    'Bull_Engulfing', 'Bear_Engulfing', 'entry_price', 'target_1', 'target_2', 'stop_loss'
                ]
                
                for indicator in harmonic_indicators:
                    indicator_col = f'{indicator}_{tf}'
                    if indicator_col in df.columns:
                        value = df[indicator_col].iloc[-1]
                        if pd.notna(value) and value != 0:
                            if 'Bull' in indicator:
                                tf_signals['patterns'].append({
                                    'type': 'engulfing',
                                    'direction': 'bullish',
                                    'confidence': 0.6,
                                    'weighted_confidence': 0.24
                                })
                                strategy['reasoning'].append(f'{tf}: Bullish engulfing pattern')
                            elif 'Bear' in indicator:
                                tf_signals['patterns'].append({
                                    'type': 'engulfing', 
                                    'direction': 'bearish',
                                    'confidence': 0.6,
                                    'weighted_confidence': 0.24
                                })
                                strategy['reasoning'].append(f'{tf}: Bearish engulfing pattern')
                
                strategy['signals'][tf] = tf_signals
            
            # Determine overall harmonic signal
            bullish_signals = []
            bearish_signals = []
            
            for tf, signals in strategy['signals'].items():
                for pattern in signals['patterns']:
                    if pattern['direction'] in ['bullish', 'buy']:
                        bullish_signals.append(pattern['weighted_confidence'])
                    elif pattern['direction'] in ['bearish', 'sell']:
                        bearish_signals.append(pattern['weighted_confidence'])
            
            total_bullish = sum(bullish_signals)
            total_bearish = sum(bearish_signals)
            
            if total_bullish > total_bearish and total_bullish > 0.5:
                strategy['overall_signal'] = 'buy'
                strategy['confidence'] = min(1.0, total_bullish)
            elif total_bearish > total_bullish and total_bearish > 0.5:
                strategy['overall_signal'] = 'sell'
                strategy['confidence'] = min(1.0, total_bearish)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in harmonic pattern strategy: {e}")
            return {'name': 'Harmonic Patterns', 'overall_signal': 'hold', 'confidence': 0.0}

    def _mean_reversion_volume_strategy(self, dataframes):
        """Strategy: Mean reversion with volume confirmation"""
        try:
            strategy = {
                'name': 'Mean Reversion + Volume',
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            for tf, df in dataframes.items():
                if df is None or df.empty or len(df) < 20:
                    continue
                    
                tf_signals = {'reversion_score': 0, 'volume_score': 0, 'total_score': 0}
                
                # Bollinger Bands analysis
                bb_upper_col = f'BB_Upper_{tf}'
                bb_lower_col = f'BB_Lower_{tf}'
                close_col = f'close_{tf}'
                
                if all(col in df.columns for col in [bb_upper_col, bb_lower_col, close_col]):
                    bb_upper = df[bb_upper_col].iloc[-1]
                    bb_lower = df[bb_lower_col].iloc[-1]
                    close = df[close_col].iloc[-1]
                    bb_middle = (bb_upper + bb_lower) / 2
                    
                    if close <= bb_lower * 1.005:  # Very close to lower band
                        tf_signals['reversion_score'] += 2
                        strategy['reasoning'].append(f'{tf}: Price at BB lower band')
                    elif close <= bb_middle * 0.99:  # Below middle
                        tf_signals['reversion_score'] += 1
                        strategy['reasoning'].append(f'{tf}: Price below BB middle')
                    elif close >= bb_upper * 0.995:  # Very close to upper band
                        tf_signals['reversion_score'] -= 2
                        strategy['reasoning'].append(f'{tf}: Price at BB upper band')
                    elif close >= bb_middle * 1.01:  # Above middle
                        tf_signals['reversion_score'] -= 1
                        strategy['reasoning'].append(f'{tf}: Price above BB middle')
                
                # Volume analysis
                volume_col = f'volume_{tf}'
                if volume_col in df.columns and len(df) >= 20:
                    current_volume = df[volume_col].iloc[-1]
                    avg_volume_20 = df[volume_col].tail(20).mean()
                    
                    volume_ratio = current_volume / avg_volume_20
                    
                    if volume_ratio > 2.0:  # Very high volume
                        tf_signals['volume_score'] += 2
                        strategy['reasoning'].append(f'{tf}: Very high volume ({volume_ratio:.1f}x)')
                    elif volume_ratio > 1.5:  # High volume
                        tf_signals['volume_score'] += 1
                        strategy['reasoning'].append(f'{tf}: High volume ({volume_ratio:.1f}x)')
                    elif volume_ratio < 0.5:  # Low volume
                        tf_signals['volume_score'] -= 1
                
                # Combine reversion and volume scores
                if tf_signals['reversion_score'] > 0 and tf_signals['volume_score'] > 0:
                    tf_signals['total_score'] = tf_signals['reversion_score'] * tf_signals['volume_score']
                elif tf_signals['reversion_score'] < 0 and tf_signals['volume_score'] > 0:
                    tf_signals['total_score'] = tf_signals['reversion_score'] * tf_signals['volume_score']
                else:
                    tf_signals['total_score'] = 0
                
                strategy['signals'][tf] = tf_signals
            
            # Calculate overall mean reversion signal
            total_score = sum(s['total_score'] for s in strategy['signals'].values())
            max_possible_score = len(strategy['signals']) * 4  # Max score per timeframe = 4
            
            if total_score > 2:
                strategy['overall_signal'] = 'buy'
                strategy['confidence'] = min(1.0, total_score / max_possible_score * 2)
            elif total_score < -2:
                strategy['overall_signal'] = 'sell'
                strategy['confidence'] = min(1.0, abs(total_score) / max_possible_score * 2)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in mean reversion volume strategy: {e}")
            return {'name': 'Mean Reversion + Volume', 'overall_signal': 'hold', 'confidence': 0.0}

    def _breakout_momentum_strategy(self, dataframes):
        """Strategy: Breakout detection with momentum confirmation"""
        try:
            strategy = {
                'name': 'Breakout + Momentum',
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            for tf, df in dataframes.items():
                if df is None or df.empty or len(df) < 20:
                    continue
                    
                tf_signals = {'breakout_score': 0, 'momentum_score': 0, 'volatility_score': 0}
                
                close_col = f'close_{tf}'
                high_col = f'high_{tf}'
                low_col = f'low_{tf}'
                
                if all(col in df.columns for col in [close_col, high_col, low_col]):
                    close = df[close_col].iloc[-1]
                    
                    # Recent highs and lows
                    recent_high_20 = df[high_col].tail(20).max()
                    recent_low_20 = df[low_col].tail(20).min()
                    recent_high_10 = df[high_col].tail(10).max()
                    recent_low_10 = df[low_col].tail(10).min()
                    
                    # Breakout detection
                    if close >= recent_high_20 * 0.999:  # Breaking recent high
                        tf_signals['breakout_score'] += 2
                        strategy['reasoning'].append(f'{tf}: Breaking 20-period high')
                    elif close >= recent_high_10 * 0.999:  # Breaking 10-period high
                        tf_signals['breakout_score'] += 1
                        strategy['reasoning'].append(f'{tf}: Breaking 10-period high')
                    elif close <= recent_low_20 * 1.001:  # Breaking recent low
                        tf_signals['breakout_score'] -= 2
                        strategy['reasoning'].append(f'{tf}: Breaking 20-period low')
                    elif close <= recent_low_10 * 1.001:  # Breaking 10-period low
                        tf_signals['breakout_score'] -= 1
                        strategy['reasoning'].append(f'{tf}: Breaking 10-period low')
                
                # Momentum confirmation
                momentum_col = f'momentum_{tf}'
                if momentum_col in df.columns:
                    momentum = df[momentum_col].iloc[-1]
                    momentum_prev = df[momentum_col].iloc[-5] if len(df) >= 5 else momentum
                    
                    if momentum > 0 and momentum > momentum_prev:
                        tf_signals['momentum_score'] += 1
                        strategy['reasoning'].append(f'{tf}: Positive momentum acceleration')
                    elif momentum < 0 and momentum < momentum_prev:
                        tf_signals['momentum_score'] -= 1
                        strategy['reasoning'].append(f'{tf}: Negative momentum acceleration')
                
                strategy['signals'][tf] = tf_signals
            
            # Calculate overall breakout signal
            total_breakout = sum(s['breakout_score'] for s in strategy['signals'].values())
            total_momentum = sum(s['momentum_score'] for s in strategy['signals'].values())
            
            # Require both breakout and momentum confirmation
            if total_breakout > 1 and total_momentum > 0:
                strategy['overall_signal'] = 'buy'
                combined_score = total_breakout + total_momentum
                strategy['confidence'] = min(1.0, combined_score / 8.0)
            elif total_breakout < -1 and total_momentum < 0:
                strategy['overall_signal'] = 'sell'
                combined_score = abs(total_breakout) + abs(total_momentum)
                strategy['confidence'] = min(1.0, combined_score / 8.0)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in breakout momentum strategy: {e}")
            return {'name': 'Breakout + Momentum', 'overall_signal': 'hold', 'confidence': 0.0}

    def _multi_indicator_confluence_strategy(self, dataframes):
        """Strategy: Multi-indicator confluence with dynamic weighting"""
        try:
            strategy = {
                'name': 'Multi-Indicator Confluence',
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            for tf, df in dataframes.items():
                if df is None or df.empty:
                    continue
                    
                tf_signals = {'indicator_votes': {'buy': 0, 'sell': 0}, 'weighted_score': 0}
                
                # Check all available indicators
                for indicator, weight in self.indicator_weights.items():
                    indicator_col = f'{indicator}_{tf}'
                    if indicator_col not in df.columns:
                        continue
                        
                    try:
                        current_value = df[indicator_col].iloc[-1]
                        if pd.isna(current_value):
                            continue
                            
                        # Analyze indicator based on its type
                        signal, confidence = self._analyze_individual_indicator(
                            indicator, current_value, df, tf
                        )
                        
                        if signal == 'buy' and confidence > 0.3:
                            tf_signals['indicator_votes']['buy'] += weight * confidence
                            tf_signals['weighted_score'] += weight * confidence
                            strategy['reasoning'].append(f'{tf}: {indicator} bullish ({confidence:.2f})')
                        elif signal == 'sell' and confidence > 0.3:
                            tf_signals['indicator_votes']['sell'] += weight * confidence
                            tf_signals['weighted_score'] -= weight * confidence
                            strategy['reasoning'].append(f'{tf}: {indicator} bearish ({confidence:.2f})')
                            
                    except Exception as e:
                        logger.debug(f"Error analyzing {indicator} for {tf}: {e}")
                        continue
                
                strategy['signals'][tf] = tf_signals
            
            # Calculate overall confluence
            total_weighted_score = sum(s['weighted_score'] for s in strategy['signals'].values())
            total_possible_weight = sum(self.indicator_weights.values()) * len(strategy['signals'])
            
            if total_weighted_score > 1.0:
                strategy['overall_signal'] = 'buy'
                strategy['confidence'] = min(1.0, total_weighted_score / (total_possible_weight * 0.3))
            elif total_weighted_score < -1.0:
                strategy['overall_signal'] = 'sell'
                strategy['confidence'] = min(1.0, abs(total_weighted_score) / (total_possible_weight * 0.3))
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in multi-indicator confluence strategy: {e}")
            return {'name': 'Multi-Indicator Confluence', 'overall_signal': 'hold', 'confidence': 0.0}

    def _advanced_pattern_strategy(self, dataframes):
        """Strategy: Advanced pattern recognition using multiple pattern types"""
        try:
            strategy = {
                'name': 'Advanced Patterns',
                'signals': {},
                'overall_signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            for tf, df in dataframes.items():
                if df is None or df.empty or len(df) < 10:
                    continue
                    
                tf_signals = {'pattern_score': 0, 'patterns_found': []}
                
                # Check for existing engulfing patterns
                bull_engulf_col = f'Bull_Engulfing_{tf}'
                bear_engulf_col = f'Bear_Engulfing_{tf}'
                
                if bull_engulf_col in df.columns:
                    bull_engulf = df[bull_engulf_col].iloc[-1]
                    if bull_engulf == 1:
                        tf_signals['pattern_score'] += 0.6
                        strategy['reasoning'].append(f'{tf}: Bullish engulfing detected')
                        
                if bear_engulf_col in df.columns:
                    bear_engulf = df[bear_engulf_col].iloc[-1]
                    if bear_engulf == 1:
                        tf_signals['pattern_score'] -= 0.6
                        strategy['reasoning'].append(f'{tf}: Bearish engulfing detected')
                
                # STC (Schaff Trend Cycle) pattern analysis
                stc_col = f'STC_{tf}'
                if stc_col in df.columns and len(df) >= 5:
                    stc = df[stc_col].iloc[-1]
                    stc_prev = df[stc_col].iloc[-5]
                    
                    if stc > 75 and stc_prev <= 75:
                        tf_signals['pattern_score'] -= 0.4
                        strategy['reasoning'].append(f'{tf}: STC overbought signal')
                    elif stc < 25 and stc_prev >= 25:
                        tf_signals['pattern_score'] += 0.4
                        strategy['reasoning'].append(f'{tf}: STC oversold signal')
                
                strategy['signals'][tf] = tf_signals
            
            # Calculate overall pattern signal
            total_pattern_score = sum(s['pattern_score'] for s in strategy['signals'].values())
            max_possible_score = len(strategy['signals']) * 2  # Max 2 points per timeframe
            
            if total_pattern_score > 0.8:
                strategy['overall_signal'] = 'buy'
                strategy['confidence'] = min(1.0, total_pattern_score / max_possible_score)
            elif total_pattern_score < -0.8:
                strategy['overall_signal'] = 'sell'
                strategy['confidence'] = min(1.0, abs(total_pattern_score) / max_possible_score)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in advanced pattern strategy: {e}")
            return {'name': 'Advanced Patterns', 'overall_signal': 'hold', 'confidence': 0.0}

    def _analyze_individual_indicator(self, indicator_name, current_value, df, timeframe):
        """Analyze individual indicator and return signal + confidence"""
        try:
            signal = 'hold'
            confidence = 0.0
            
            # RSI analysis
            if indicator_name == 'RSI':
                if current_value < 20:
                    signal, confidence = 'buy', 0.9
                elif current_value < 30:
                    signal, confidence = 'buy', 0.7
                elif current_value < 40:
                    signal, confidence = 'buy', 0.4
                elif current_value > 80:
                    signal, confidence = 'sell', 0.9
                elif current_value > 70:
                    signal, confidence = 'sell', 0.7
                elif current_value > 60:
                    signal, confidence = 'sell', 0.4
            
            # Stochastic analysis
            elif indicator_name in ['STOCH_k', 'STOCH_d']:
                if current_value < 15:
                    signal, confidence = 'buy', 0.8
                elif current_value < 25:
                    signal, confidence = 'buy', 0.6
                elif current_value > 85:
                    signal, confidence = 'sell', 0.8
                elif current_value > 75:
                    signal, confidence = 'sell', 0.6
            
            # MACD analysis (requires previous value)
            elif indicator_name == 'MACD':
                signal_col = f'Signal_{timeframe}'
                if signal_col in df.columns and len(df) >= 2:
                    signal_line = df[signal_col].iloc[-1]
                    prev_macd = df[f'MACD_{timeframe}'].iloc[-2]
                    prev_signal = df[signal_col].iloc[-2]
                    
                    if current_value > signal_line and prev_macd <= prev_signal:
                        signal, confidence = 'buy', 0.8
                    elif current_value < signal_line and prev_macd >= prev_signal:
                        signal, confidence = 'sell', 0.8
                    elif current_value > signal_line:
                        signal, confidence = 'buy', 0.4
                    elif current_value < signal_line:
                        signal, confidence = 'sell', 0.4
            
            # CCI analysis
            elif indicator_name == 'CCI':
                if current_value < -200:
                    signal, confidence = 'buy', 0.9
                elif current_value < -100:
                    signal, confidence = 'buy', 0.6
                elif current_value > 200:
                    signal, confidence = 'sell', 0.9
                elif current_value > 100:
                    signal, confidence = 'sell', 0.6
            
            # ADX analysis
            elif indicator_name == 'ADX':
                plus_di_col = f'Plus_DI_{timeframe}'
                minus_di_col = f'Minus_DI_{timeframe}'
                if plus_di_col in df.columns and minus_di_col in df.columns:
                    plus_di = df[plus_di_col].iloc[-1]
                    minus_di = df[minus_di_col].iloc[-1]
                    
                    if current_value > 25:  # Strong trend
                        if plus_di > minus_di:
                            signal, confidence = 'buy', min(0.9, current_value / 40)
                        else:
                            signal, confidence = 'sell', min(0.9, current_value / 40)
            
            return signal, confidence
            
        except Exception as e:
            logger.debug(f"Error analyzing {indicator_name}: {e}")
            return 'hold', 0.0

    def _find_best_shadow_signal(self, strategies):
        """Find the best signal from all shadow strategies"""
        try:
            best_signal = {
                'strategy': 'none',
                'signal': 'hold',
                'confidence': 0.0,
                'reasoning': []
            }
            
            # Weight strategies by reliability
            strategy_weights = {
                'multi_indicator_confluence': 1.0,
                'trend_alignment': 0.9,
                'oscillator_divergence': 0.8,
                'breakout_momentum': 0.7,
                'mean_reversion_volume': 0.6,
                'harmonic_patterns': 0.8,
                'advanced_patterns': 0.5
            }
            
            weighted_scores = {'buy': 0, 'sell': 0}
            all_reasoning = []
            
            for strategy_name, strategy_data in strategies.items():
                if strategy_data['overall_signal'] == 'hold':
                    continue
                    
                weight = strategy_weights.get(strategy_name, 0.5)
                confidence = strategy_data['confidence']
                weighted_confidence = weight * confidence
                
                if strategy_data['overall_signal'] == 'buy':
                    weighted_scores['buy'] += weighted_confidence
                elif strategy_data['overall_signal'] == 'sell':
                    weighted_scores['sell'] += weighted_confidence
                
                all_reasoning.extend([
                    f"{strategy_name}: {reason}" 
                    for reason in strategy_data.get('reasoning', [])[:2]  # Top 2 reasons
                ])
            
            # Determine best signal
            if weighted_scores['buy'] > weighted_scores['sell'] and weighted_scores['buy'] > 0.5:
                best_signal = {
                    'strategy': 'combined',
                    'signal': 'buy',
                    'confidence': min(1.0, weighted_scores['buy']),
                    'reasoning': all_reasoning
                }
            elif weighted_scores['sell'] > weighted_scores['buy'] and weighted_scores['sell'] > 0.5:
                best_signal = {
                    'strategy': 'combined',
                    'signal': 'sell',
                    'confidence': min(1.0, weighted_scores['sell']),
                    'reasoning': all_reasoning
                }
            
            return best_signal
            
        except Exception as e:
            logger.error(f"Error finding best shadow signal: {e}")
            return {'strategy': 'none', 'signal': 'hold', 'confidence': 0.0, 'reasoning': []}

    def _identify_missed_opportunities(self, shadow_results, main_decision):
        """Identify what opportunities the main system missed"""
        try:
            missed_opportunities = []
            
            best_shadow = shadow_results.get('best_shadow_signal', {})
            shadow_signal = best_shadow.get('signal', 'hold')
            shadow_confidence = best_shadow.get('confidence', 0.0)
            
            # Compare with main system decision
            main_signal = main_decision.get('signal', 'hold') if main_decision else 'hold'
            
            if shadow_signal != 'hold' and main_signal == 'hold' and shadow_confidence > 0.6:
                missed_opportunities.append({
                    'type': 'signal_mismatch',
                    'shadow_signal': shadow_signal,
                    'shadow_confidence': shadow_confidence,
                    'main_signal': main_signal,
                    'opportunity_score': shadow_confidence,
                    'reasoning': best_shadow.get('reasoning', [])[:3],  # Top 3 reasons
                    'strategies_agreeing': [
                        name for name, data in shadow_results['shadow_strategies'].items()
                        if data['overall_signal'] == shadow_signal and data['confidence'] > 0.4
                    ]
                })
            
            return missed_opportunities
            
        except Exception as e:
            logger.error(f"Error identifying missed opportunities: {e}")
            return []

    def _log_comprehensive_analysis(self, shadow_results):
        """Log comprehensive shadow analysis results"""
        try:
            best_shadow = shadow_results.get('best_shadow_signal', {})
            missed_opps = shadow_results.get('missed_opportunities', [])
            
            if best_shadow.get('signal') != 'hold':
                logger.info(f"🔮 ADVANCED Shadow Analysis: {best_shadow['signal'].upper()} "
                           f"(confidence: {best_shadow['confidence']:.3f})")
                
                # Log top strategies that agree
                agreeing_strategies = []
                for name, data in shadow_results.get('shadow_strategies', {}).items():
                    if data['overall_signal'] == best_shadow['signal'] and data['confidence'] > 0.4:
                        agreeing_strategies.append(f"{name}({data['confidence']:.2f})")
                
                if agreeing_strategies:
                    logger.info(f"   Agreeing strategies: {', '.join(agreeing_strategies[:3])}")
                
                # Log top reasoning
                top_reasoning = best_shadow.get('reasoning', [])[:3]
                if top_reasoning:
                    logger.info(f"   Key indicators: {'; '.join(top_reasoning)}")
            
            # Log missed opportunities
            high_value_missed = [opp for opp in missed_opps if opp.get('opportunity_score', 0) > 0.7]
            if high_value_missed:
                logger.warning(f"🚨 HIGH-VALUE MISSED OPPORTUNITIES: {len(high_value_missed)} detected")
                for opp in high_value_missed[:2]:  # Top 2
                    logger.warning(f"   {opp.get('shadow_signal', '').upper()}: "
                                 f"{opp.get('opportunity_score', 0):.3f} confidence "
                                 f"({opp.get('type', 'unknown')})")
            
        except Exception as e:
            logger.error(f"Error logging comprehensive analysis: {e}")

class ShadowTradingSystem:
    """
    Complete adaptive shadow trading system that tracks all signals and learns what works
    """

    def __init__(self, pair):
        self.pair = pair
        self.pair_clean = pair.lower().replace('/', '').replace('-', '')

        # File paths
        self.shadow_log_file = os.path.join(DEPENDENCY_DIR, f"shadow_trades_{self.pair_clean}.csv")
        self.analysis_file = os.path.join(DEPENDENCY_DIR, f"shadow_analysis_{self.pair_clean}.json")
        self.recommendations_file = os.path.join(DEPENDENCY_DIR, f"shadow_recommendations_{self.pair_clean}.json")

        # In-memory tracking
        self.pending_signals = {}  # Signals waiting for outcome evaluation
        self.monitoring_active = False
        self.price_history = []  # For outcome calculation
        self.lock = threading.Lock()

        # Analysis parameters
        self.evaluation_periods = [5, 15, 30, 60]  # Minutes to evaluate signal outcomes
        self.min_signals_for_analysis = 20
        self.lookback_days = 7

        # Advanced components
        self.advanced_analyzer = AdvancedIndicatorShadowAnalyzer(pair)
        self.adaptive_learner = AdaptiveStrategyLearner(pair)

        # Initialize files
        self._initialize_files()

        logger.info(f"🔮 Advanced Adaptive Shadow Trading System initialized for {pair}")

    def _initialize_files(self):
        """Initialize CSV files with headers if they don't exist"""
        try:
            if not os.path.exists(self.shadow_log_file):
                headers = [
                    'timestamp', 'signal_id', 'pair', 'signal_type', 'prediction',
                    'confidence', 'enhanced_confidence', 'confluence_strength',
                    'market_regime', 'regime_strength', 'entry_price', 'stop_loss',
                    'take_profit', 'position_size', 'executed', 'rejection_reason',
                    'volume_confirmed', 'risk_reward_ratio', 'participating_timeframes',
                    'outcome_5m', 'outcome_15m', 'outcome_30m', 'outcome_60m',
                    'theoretical_profit_5m', 'theoretical_profit_15m',
                    'theoretical_profit_30m', 'theoretical_profit_60m',
                    'would_have_hit_stop', 'would_have_hit_target', 'max_favorable_move',
                    'max_adverse_move', 'evaluation_complete', 'shadow_strategy',
                    'shadow_confidence', 'shadow_reasoning'
                ]

                df = pd.DataFrame(columns=headers)
                df.to_csv(self.shadow_log_file, index=False)
                logger.info(f"Created shadow trading log: {self.shadow_log_file}")

        except Exception as e:
            logger.error(f"Error initializing shadow trading files: {e}")

    def start_monitoring(self):
        """Start the background monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitor_thread.start()
            logger.info("🔮 Advanced shadow trading monitoring started")

    def stop_monitoring(self):
        """Stop the background monitoring"""
        self.monitoring_active = False
        logger.info("Shadow trading monitoring stopped")

    def _safe_convert_numeric(self, value, default=0.0):
        """Safely convert value to float with fallback"""
        try:
            if value is None or value == '' or value == 'nan':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_convert_bool(self, value, default=False):
        """Safely convert value to bool with fallback"""
        try:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def log_signal(self, signal_data, executed=False, rejection_reason=None):
        """Log any trading signal for shadow tracking with safe type conversion"""
        try:
            signal_id = f"{signal_data.get('timestamp', datetime.now()).isoformat()}_{signal_data.get('signal', 'unknown')}"

            # Create comprehensive signal record with safe type conversion
            shadow_record = {
                'signal_id': signal_id,
                'timestamp': signal_data.get('timestamp', datetime.now()),
                'pair': str(self.pair),
                'signal_type': str(signal_data.get('signal', 'unknown')),
                'prediction': self._safe_convert_numeric(signal_data.get('prediction', 1)),
                'confidence': self._safe_convert_numeric(signal_data.get('confidence', 0.5)),
                'enhanced_confidence': self._safe_convert_numeric(signal_data.get('enhanced_confidence', 0.5)),
                'confluence_strength': self._safe_convert_numeric(signal_data.get('confluence_strength', 0.0)),
                'market_regime': str(signal_data.get('market_regime', 'unknown')),
                'regime_strength': self._safe_convert_numeric(signal_data.get('regime_strength', 0.0)),
                'entry_price': self._safe_convert_numeric(signal_data.get('price', 0.0)),
                'stop_loss': self._safe_convert_numeric(signal_data.get('stop_loss', 0.0)),
                'take_profit': self._safe_convert_numeric(signal_data.get('take_profit', 0.0)),
                'position_size': self._safe_convert_numeric(signal_data.get('position_size', 0.0)),
                'executed': self._safe_convert_bool(executed),
                'rejection_reason': str(rejection_reason or 'none'),
                'volume_confirmed': self._safe_convert_bool(signal_data.get('volume_confirmed', False)),
                'risk_reward_ratio': self._safe_convert_numeric(signal_data.get('risk_reward_ratio', 0.0)),
                'participating_timeframes': ','.join(str(tf) for tf in signal_data.get('participating_timeframes', [])),
                'logged_at': datetime.now()
            }

            # Add to pending signals for outcome evaluation
            with self.lock:
                self.pending_signals[signal_id] = shadow_record

            logger.info(f"🔮 Shadow system logged {'EXECUTED' if executed else 'FILTERED'} signal: "
                       f"{shadow_record['signal_type']} at {shadow_record['entry_price']:.4f} "
                       f"(confidence: {shadow_record['enhanced_confidence']:.3f})")

            if not executed and rejection_reason:
                logger.info(f"   Rejection reason: {rejection_reason}")

        except Exception as e:
            logger.error(f"Error logging signal to shadow system: {e}")

    def log_executed_trade(self, trade_result):
        """Log an executed trade (convenience method)"""
        if trade_result:
            self.log_signal(trade_result, executed=True)

    def log_filtered_signal(self, signal_data, rejection_reason):
        """Log a filtered/rejected signal (convenience method)"""
        self.log_signal(signal_data, executed=False, rejection_reason=rejection_reason)

    def update_price_data(self, current_price, timestamp=None):
        """Update current price for outcome calculation"""
        try:
            if timestamp is None:
                timestamp = datetime.now()

            # Safe price conversion
            safe_price = self._safe_convert_numeric(current_price, 0.0)
            if safe_price <= 0:
                logger.warning(f"Invalid price data: {current_price}")
                return

            with self.lock:
                self.price_history.append({
                    'timestamp': timestamp,
                    'price': safe_price
                })

                # Keep only recent price history (2 hours)
                cutoff_time = timestamp - timedelta(hours=2)
                self.price_history = [
                    p for p in self.price_history
                    if p['timestamp'] >= cutoff_time
                ]
        except Exception as e:
            logger.error(f"Error updating price data: {e}")

    def run_comprehensive_shadow_analysis(self, all_dataframes, current_price, main_system_decision):
        """🚀 NEW: Run comprehensive shadow analysis using ALL indicators + harmonics"""
        try:
            # Run the comprehensive analysis
            shadow_results = self.advanced_analyzer.comprehensive_shadow_analysis(
                all_dataframes, current_price, main_system_decision
            )
            
            # Store results for outcome tracking
            if shadow_results and shadow_results.get('best_shadow_signal', {}).get('signal') != 'hold':
                shadow_signal = shadow_results['best_shadow_signal']
                
                # Create shadow trade record for tracking
                shadow_trade_record = {
                    'timestamp': datetime.now(),
                    'type': 'comprehensive_shadow',
                    'signal': shadow_signal['signal'],
                    'confidence': shadow_signal['confidence'],
                    'price': current_price,
                    'strategy': shadow_signal['strategy'],
                    'reasoning': shadow_signal.get('reasoning', [])[:5],  # Top 5 reasons
                    'missed_opportunities': shadow_results.get('missed_opportunities', [])
                }
                
                # Add to pending for outcome evaluation
                with self.lock:
                    shadow_id = f"comprehensive_{datetime.now().isoformat()}_{shadow_signal['signal']}"
                    self.pending_signals[shadow_id] = shadow_trade_record
            
            # 🎯 ADAPTIVE LEARNING: Analyze if we should adapt our strategy
            self._run_adaptive_learning_analysis()
            
            return shadow_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive shadow analysis: {e}")
            return None

    def _run_adaptive_learning_analysis(self):
        """🎯 NEW: Run adaptive learning to adjust main system based on what works"""
        try:
            # Only run adaptive analysis periodically
            if not hasattr(self, '_last_adaptation_check'):
                self._last_adaptation_check = datetime.now()
            
            time_since_last_check = (datetime.now() - self._last_adaptation_check).total_seconds()
            if time_since_last_check < 3600:  # Only check every hour
                return
            
            self._last_adaptation_check = datetime.now()
            
            # Load recent shadow data for analysis
            if not os.path.exists(self.shadow_log_file):
                return
            
            try:
                df = pd.read_csv(self.shadow_log_file, parse_dates=['timestamp'])
                
                # Only analyze recent data
                cutoff_time = datetime.now() - timedelta(days=self.lookback_days)
                recent_data = df[df['timestamp'] >= cutoff_time]
                
                if len(recent_data) < self.adaptive_learner.min_trades_for_adaptation:
                    logger.debug(f"Not enough data for adaptation: {len(recent_data)} signals")
                    return
                
                # Convert to list of records for analysis
                recent_records = recent_data.to_dict('records')
                
                # Analyze strategy performance
                strategy_performance = self.adaptive_learner.analyze_strategy_performance(recent_records)
                
                if strategy_performance:
                    logger.info(f"🎯 ADAPTIVE ANALYSIS: Analyzed {len(strategy_performance)} strategies")
                    
                    # Determine what adaptations to make
                    adaptations = self.adaptive_learner.determine_adaptations(strategy_performance)
                    
                    if adaptations and adaptations.get('adaptation_confidence', 0) >= self.adaptive_learner.confidence_threshold:
                        # Apply the adaptations
                        success = self.adaptive_learner.apply_adaptations(adaptations)
                        
                        if success:
                            logger.warning(f"🚀 SYSTEM ADAPTED! Main trading strategy updated based on shadow learning")
                            logger.warning(f"   Adaptation confidence: {adaptations.get('adaptation_confidence', 0):.1%}")
                            logger.warning(f"   Reason: {adaptations.get('reason', 'Performance optimization')}")
                            
                            # Log to the main trading system that adaptation occurred
                            adaptation_signal = {
                                'timestamp': datetime.now(),
                                'type': 'system_adaptation',
                                'adaptations_applied': adaptations,
                                'confidence': adaptations.get('adaptation_confidence', 0),
                                'based_on_signals': adaptations.get('based_on_signals', 0)
                            }
                            
                            # Store adaptation for tracking
                            with self.lock:
                                adaptation_id = f"adaptation_{datetime.now().isoformat()}"
                                self.pending_signals[adaptation_id] = adaptation_signal
                    else:
                        logger.debug(f"Adaptation confidence too low: {adaptations.get('adaptation_confidence', 0):.1%}")
                
            except Exception as e:
                logger.error(f"Error in adaptive learning analysis: {e}")
                
        except Exception as e:
            logger.error(f"Error running adaptive learning: {e}")

    def _monitoring_loop(self):
        """Background loop to evaluate pending signals and run adaptive learning"""
        while self.monitoring_active:
            try:
                self._evaluate_pending_signals()
                self._perform_periodic_analysis()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in shadow monitoring loop: {e}")
                time.sleep(60)

    def _evaluate_pending_signals(self):
        """Evaluate outcomes for pending signals"""
        try:
            current_time = datetime.now()
            completed_signals = []

            with self.lock:
                for signal_id, signal_record in self.pending_signals.items():
                    try:
                        signal_time = signal_record['logged_at'] if 'logged_at' in signal_record else signal_record.get('timestamp', current_time)

                        # Check if enough time has passed for evaluation
                        time_elapsed = (current_time - signal_time).total_seconds() / 60

                        if time_elapsed >= max(self.evaluation_periods):
                            # Calculate outcomes for all periods
                            outcomes = self._calculate_signal_outcomes(signal_record, signal_time)

                            if outcomes:
                                # Update signal record with outcomes
                                signal_record.update(outcomes)
                                signal_record['evaluation_complete'] = True

                                # Save to CSV
                                self._save_signal_to_csv(signal_record)
                                completed_signals.append(signal_id)

                                # Log the outcome
                                self._log_signal_outcome(signal_record)
                    except Exception as e:
                        logger.error(f"Error evaluating signal {signal_id}: {e}")
                        # Mark as completed to prevent infinite retries
                        completed_signals.append(signal_id)

                # Remove completed signals from pending
                for signal_id in completed_signals:
                    if signal_id in self.pending_signals:
                        del self.pending_signals[signal_id]

        except Exception as e:
            logger.error(f"Error evaluating pending signals: {e}")

    def _calculate_signal_outcomes(self, signal_record, signal_time):
        """Calculate theoretical outcomes for a signal at different time periods"""
        try:
            entry_price = self._safe_convert_numeric(signal_record.get('entry_price', signal_record.get('price', 0)))
            signal_type = str(signal_record.get('signal_type', signal_record.get('signal', 'hold')))
            stop_loss = self._safe_convert_numeric(signal_record.get('stop_loss', 0))
            take_profit = self._safe_convert_numeric(signal_record.get('take_profit', 0))

            if entry_price <= 0:
                logger.warning(f"Invalid entry price for signal outcome calculation: {entry_price}")
                return None

            outcomes = {}

            # Find relevant price data
            relevant_prices = [
                p for p in self.price_history
                if p['timestamp'] >= signal_time
            ]

            if not relevant_prices:
                logger.debug("No relevant price data for outcome calculation")
                return None

            # Calculate outcomes for each evaluation period
            for period in self.evaluation_periods:
                try:
                    period_end = signal_time + timedelta(minutes=period)

                    # Find prices within this period
                    period_prices = [
                        self._safe_convert_numeric(p['price']) for p in relevant_prices
                        if p['timestamp'] <= period_end and self._safe_convert_numeric(p['price']) > 0
                    ]

                    if period_prices:
                        outcome = self._calculate_period_outcome(
                            entry_price, period_prices, signal_type, stop_loss, take_profit
                        )

                        outcomes[f'outcome_{period}m'] = outcome['outcome']
                        outcomes[f'theoretical_profit_{period}m'] = outcome['profit_pct']
                except Exception as e:
                    logger.error(f"Error calculating outcome for period {period}m: {e}")
                    outcomes[f'outcome_{period}m'] = 'error'
                    outcomes[f'theoretical_profit_{period}m'] = 0.0

            return outcomes

        except Exception as e:
            logger.error(f"Error calculating signal outcomes: {e}")
            return None

    def _calculate_period_outcome(self, entry_price, period_prices, signal_type, stop_loss, take_profit):
        """Calculate outcome for a specific time period"""
        try:
            if not period_prices or entry_price <= 0:
                return {'outcome': 'no_data', 'profit_pct': 0.0}

            exit_price = period_prices[-1]  # Final price in period

            # Check if stop/target hit during period
            if stop_loss > 0 or take_profit > 0:
                for price in period_prices:
                    if signal_type in ['buy', 'BUY', '2']:
                        if stop_loss > 0 and price <= stop_loss:
                            exit_price = stop_loss
                            break
                        if take_profit > 0 and price >= take_profit:
                            exit_price = take_profit
                            break
                    else:  # sell
                        if stop_loss > 0 and price >= stop_loss:
                            exit_price = stop_loss
                            break
                        if take_profit > 0 and price <= take_profit:
                            exit_price = take_profit
                            break

            # Calculate profit percentage
            if signal_type in ['buy', 'BUY', '2']:
                profit_pct = (exit_price - entry_price) / entry_price
                outcome = 'profit' if profit_pct > 0 else 'loss'
            else:  # sell
                profit_pct = (entry_price - exit_price) / entry_price
                outcome = 'profit' if profit_pct > 0 else 'loss'

            return {'outcome': outcome, 'profit_pct': profit_pct}

        except Exception as e:
            logger.error(f"Error calculating period outcome: {e}")
            return {'outcome': 'error', 'profit_pct': 0.0}

    def _save_signal_to_csv(self, signal_record):
        """Save completed signal evaluation to CSV"""
        try:
            # Convert to DataFrame row with safe type conversion
            row_data = {
                'timestamp': signal_record['timestamp'].isoformat() if hasattr(signal_record['timestamp'], 'isoformat') else str(signal_record['timestamp']),
                'signal_id': str(signal_record.get('signal_id', '')),
                'pair': str(signal_record.get('pair', self.pair)),
                'signal_type': str(signal_record.get('signal_type', signal_record.get('signal', 'hold'))),
                'prediction': self._safe_convert_numeric(signal_record.get('prediction', 1)),
                'confidence': self._safe_convert_numeric(signal_record.get('confidence', 0.5)),
                'enhanced_confidence': self._safe_convert_numeric(signal_record.get('enhanced_confidence', 0.5)),
                'confluence_strength': self._safe_convert_numeric(signal_record.get('confluence_strength', 0)),
                'market_regime': str(signal_record.get('market_regime', 'unknown')),
                'regime_strength': self._safe_convert_numeric(signal_record.get('regime_strength', 0)),
                'entry_price': self._safe_convert_numeric(signal_record.get('entry_price', signal_record.get('price', 0))),
                'stop_loss': self._safe_convert_numeric(signal_record.get('stop_loss', 0)),
                'take_profit': self._safe_convert_numeric(signal_record.get('take_profit', 0)),
                'position_size': self._safe_convert_numeric(signal_record.get('position_size', 0)),
                'executed': self._safe_convert_bool(signal_record.get('executed', False)),
                'rejection_reason': str(signal_record.get('rejection_reason', 'none')),
                'volume_confirmed': self._safe_convert_bool(signal_record.get('volume_confirmed', False)),
                'risk_reward_ratio': self._safe_convert_numeric(signal_record.get('risk_reward_ratio', 0)),
                'participating_timeframes': str(signal_record.get('participating_timeframes', '')),
                'evaluation_complete': True,
                'shadow_strategy': str(signal_record.get('strategy', '')),
                'shadow_confidence': self._safe_convert_numeric(signal_record.get('confidence', 0)),
                'shadow_reasoning': str(signal_record.get('reasoning', [])[:3])  # Top 3 reasons
            }

            # Add outcome data with safe conversion
            for period in self.evaluation_periods:
                row_data[f'outcome_{period}m'] = str(signal_record.get(f'outcome_{period}m', 'no_data'))
                row_data[f'theoretical_profit_{period}m'] = self._safe_convert_numeric(signal_record.get(f'theoretical_profit_{period}m', 0.0))

            # Add additional metrics with safe conversion
            row_data['would_have_hit_stop'] = self._safe_convert_bool(signal_record.get('would_have_hit_stop', False))
            row_data['would_have_hit_target'] = self._safe_convert_bool(signal_record.get('would_have_hit_target', False))
            row_data['max_favorable_move'] = self._safe_convert_numeric(signal_record.get('max_favorable_move', 0.0))
            row_data['max_adverse_move'] = self._safe_convert_numeric(signal_record.get('max_adverse_move', 0.0))

            # Append to CSV
            df = pd.DataFrame([row_data])
            df.to_csv(self.shadow_log_file, mode='a', header=False, index=False)

        except Exception as e:
            logger.error(f"Error saving signal to CSV: {e}")

    def _log_signal_outcome(self, signal_record):
        """Log the outcome of a signal evaluation"""
        try:
            signal_type = str(signal_record.get('signal_type', signal_record.get('signal', 'hold')))
            executed = self._safe_convert_bool(signal_record.get('executed', False))
            rejection_reason = str(signal_record.get('rejection_reason', 'none'))

            # Get 15-minute outcome as primary metric
            outcome_15m = str(signal_record.get('outcome_15m', 'no_data'))
            profit_15m = self._safe_convert_numeric(signal_record.get('theoretical_profit_15m', 0.0))

            status = "EXECUTED" if executed else "FILTERED"
            outcome_msg = f"{outcome_15m} ({profit_15m:+.2%})" if outcome_15m != 'no_data' else "no_data"

            logger.info(f"🔮 Shadow outcome: {status} {signal_type} → {outcome_msg}")

            if not executed and outcome_15m == 'profit' and profit_15m > 0.02:  # Significant missed opportunity
                logger.warning(f"   🚨 MISSED OPPORTUNITY: {rejection_reason} → would have gained {profit_15m:+.2%}")
            elif executed and outcome_15m == 'loss':
                logger.info(f"   ✅ Good execution despite loss: {profit_15m:+.2%}")

        except Exception as e:
            logger.error(f"Error logging signal outcome: {e}")

    def _perform_periodic_analysis(self):
        """Perform periodic analysis and generate recommendations"""
        try:
            # Only run analysis every 10 minutes
            if hasattr(self, '_last_analysis_time'):
                if (datetime.now() - self._last_analysis_time).total_seconds() < 600:
                    return

            self._last_analysis_time = datetime.now()

            # Load recent shadow data
            if not os.path.exists(self.shadow_log_file):
                return

            df = pd.read_csv(self.shadow_log_file, parse_dates=['timestamp'])

            if len(df) < self.min_signals_for_analysis:
                return

            # Analyze recent data
            cutoff_time = datetime.now() - timedelta(days=self.lookback_days)
            recent_df = df[df['timestamp'] >= cutoff_time]

            if len(recent_df) >= 10:  # Minimum for meaningful analysis
                analysis = self._analyze_shadow_performance(recent_df)
                recommendations = self._generate_recommendations(analysis)

                # Save analysis and recommendations
                self._save_analysis(analysis, recommendations)

                # Log key insights
                self._log_analysis_insights(analysis, recommendations)

        except Exception as e:
            logger.error(f"Error in periodic analysis: {e}")

    def _analyze_shadow_performance(self, df):
        """Analyze shadow trading performance with robust error handling"""
        try:
            # Ensure all numeric columns are properly typed
            numeric_columns = ['confidence', 'enhanced_confidence', 'confluence_strength', 'entry_price', 
                             'theoretical_profit_15m', 'theoretical_profit_5m', 'theoretical_profit_30m', 'theoretical_profit_60m']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            # Ensure boolean columns are properly typed
            boolean_columns = ['executed', 'volume_confirmed', 'would_have_hit_stop', 'would_have_hit_target']
            for col in boolean_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.lower().isin(['true', '1', 'yes'])

            analysis = {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_signals': len(df),
                'executed_signals': int(df['executed'].sum()) if 'executed' in df.columns else 0,
                'filtered_signals': int((~df['executed']).sum()) if 'executed' in df.columns else 0,
                'execution_rate': float(df['executed'].mean()) if 'executed' in df.columns and len(df) > 0 else 0.0,
            }

            # Analyze outcomes by execution status
            if 'executed' in df.columns:
                executed_df = df[df['executed'] == True]
                filtered_df = df[df['executed'] == False]

                # Executed signal performance
                if len(executed_df) > 0 and 'theoretical_profit_15m' in executed_df.columns:
                    executed_profits = executed_df['theoretical_profit_15m'].dropna()
                    if len(executed_profits) > 0:
                        analysis['executed_performance'] = {
                            'count': len(executed_df),
                            'win_rate': float((executed_profits > 0).mean()),
                            'avg_profit': float(executed_profits.mean()),
                            'total_profit': float(executed_profits.sum())
                        }

                # Filtered signal performance (missed opportunities)
                if len(filtered_df) > 0 and 'theoretical_profit_15m' in filtered_df.columns:
                    filtered_profits = filtered_df['theoretical_profit_15m'].dropna()
                    if len(filtered_profits) > 0:
                        analysis['filtered_performance'] = {
                            'count': len(filtered_df),
                            'win_rate': float((filtered_profits > 0).mean()),
                            'avg_profit': float(filtered_profits.mean()),
                            'total_missed_profit': float(filtered_profits.sum())
                        }

                    # Analyze rejection reasons
                    if 'rejection_reason' in filtered_df.columns:
                        rejection_analysis = {}
                        for reason in filtered_df['rejection_reason'].unique():
                            if pd.notna(reason):
                                reason_df = filtered_df[filtered_df['rejection_reason'] == reason]
                                if 'theoretical_profit_15m' in reason_df.columns:
                                    reason_profits = reason_df['theoretical_profit_15m'].dropna()

                                    if len(reason_profits) > 0:
                                        rejection_analysis[str(reason)] = {
                                            'count': len(reason_df),
                                            'win_rate': float((reason_profits > 0).mean()),
                                            'avg_profit': float(reason_profits.mean()),
                                            'total_missed': float(reason_profits.sum())
                                        }

                        analysis['rejection_analysis'] = rejection_analysis

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing shadow performance: {e}")
            return {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_signals': 0,
                'error': str(e)
            }

    def _generate_recommendations(self, analysis):
        """Generate recommendations based on shadow analysis"""
        try:
            recommendations = {
                'timestamp': datetime.now().isoformat(),
                'recommendations': [],
                'threshold_adjustments': {},
                'confidence_level': 'medium'
            }

            # Analyze missed opportunities
            if 'filtered_performance' in analysis:
                filtered_perf = analysis['filtered_performance']

                if (self._safe_convert_numeric(filtered_perf.get('win_rate', 0)) > 0.6 and 
                    self._safe_convert_numeric(filtered_perf.get('total_missed_profit', 0)) > 0.05):
                    
                    recommendations['recommendations'].append({
                        'priority': 'high',
                        'type': 'threshold_relaxation',
                        'message': f"High-quality signals being filtered: {filtered_perf['win_rate']:.1%} win rate, "
                                  f"{filtered_perf['total_missed_profit']:+.2%} missed profit",
                        'suggested_action': 'Consider relaxing filtering criteria'
                    })

                    recommendations['confidence_level'] = 'high'

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'recommendations': [],
                'error': str(e)
            }

    def _save_analysis(self, analysis, recommendations):
        """Save analysis and recommendations to files"""
        try:
            with open(self.analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)

            with open(self.recommendations_file, 'w') as f:
                json.dump(recommendations, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving analysis: {e}")

    def _log_analysis_insights(self, analysis, recommendations):
        """Log key insights from analysis"""
        try:
            if 'total_signals' in analysis:
                exec_rate = self._safe_convert_numeric(analysis.get('execution_rate', 0))
                total_signals = int(analysis.get('total_signals', 0))

                logger.info(f"🔮 Shadow Analysis: {total_signals} signals, {exec_rate:.1%} execution rate")

                if 'filtered_performance' in analysis:
                    filt_perf = analysis['filtered_performance']
                    win_rate = self._safe_convert_numeric(filt_perf.get('win_rate', 0))
                    missed_profit = self._safe_convert_numeric(filt_perf.get('total_missed_profit', 0))
                    logger.info(f"   Filtered signals: {win_rate:.1%} win rate, {missed_profit:+.2%} missed profit")

                # Log high-priority recommendations
                high_priority_recs = [
                    r for r in recommendations.get('recommendations', [])
                    if r.get('priority') == 'high'
                ]

                for rec in high_priority_recs:
                    logger.warning(f"🎯 Shadow Recommendation: {rec.get('message', 'No message')}")

        except Exception as e:
            logger.error(f"Error logging analysis insights: {e}")

    def get_recent_analysis(self):
        """Get the most recent analysis results"""
        try:
            if os.path.exists(self.analysis_file):
                with open(self.analysis_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading recent analysis: {e}")
            return {}

    def get_recommendations(self):
        """Get current recommendations"""
        try:
            if os.path.exists(self.recommendations_file):
                with open(self.recommendations_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading recommendations: {e}")
            return {}

    def get_adaptation_status(self):
        """Get current adaptation status"""
        try:
            return self.adaptive_learner.get_adaptation_status()
        except Exception as e:
            logger.error(f"Error getting adaptation status: {e}")
            return {}

    def get_performance_summary(self, days=7):
        """Get performance summary for the last N days"""
        try:
            if not os.path.exists(self.shadow_log_file):
                return {}

            df = pd.read_csv(self.shadow_log_file, parse_dates=['timestamp'])
            cutoff_time = datetime.now() - timedelta(days=days)
            recent_df = df[df['timestamp'] >= cutoff_time]

            if len(recent_df) == 0:
                return {}

            # Ensure proper data types
            if 'executed' in recent_df.columns:
                recent_df['executed'] = recent_df['executed'].astype(str).str.lower().isin(['true', '1', 'yes'])
            
            if 'theoretical_profit_15m' in recent_df.columns:
                recent_df['theoretical_profit_15m'] = pd.to_numeric(recent_df['theoretical_profit_15m'], errors='coerce').fillna(0.0)

            summary = {
                'period_days': days,
                'total_signals': len(recent_df),
                'executed_count': int(recent_df['executed'].sum()) if 'executed' in recent_df.columns else 0,
                'filtered_count': int((~recent_df['executed']).sum()) if 'executed' in recent_df.columns else 0,
                'execution_rate': float(recent_df['executed'].mean()) if 'executed' in recent_df.columns else 0.0,
                'adaptation_status': self.get_adaptation_status()
            }

            # Add profitability metrics
            if 'theoretical_profit_15m' in recent_df.columns:
                profits_15m = recent_df['theoretical_profit_15m'].dropna()
                if len(profits_15m) > 0:
                    summary['overall_win_rate'] = float((profits_15m > 0).mean())
                    summary['avg_profit'] = float(profits_15m.mean())
                    summary['total_theoretical_profit'] = float(profits_15m.sum())

            return summary

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

# Utility functions for integration
def create_shadow_system(pair):
    """Factory function to create shadow trading system"""
    return ShadowTradingSystem(pair)

def log_signal_to_shadow(shadow_system, signal_data, executed=False, rejection_reason=None):
    """Utility function to log signals to shadow system"""
    if shadow_system:
        shadow_system.log_signal(signal_data, executed, rejection_reason)

def get_shadow_trading_summary(pair="ADAUSDT"):
    """Get a summary of what the shadow trading system has discovered"""
    try:
        import os
        shadow_file = f"dependencies_v1/shadow_trades_{pair.lower()}.csv"
        
        if os.path.exists(shadow_file):
            import pandas as pd
            df = pd.read_csv(shadow_file)
            
            print(f"\n🔮 ADAPTIVE SHADOW TRADING SUMMARY for {pair}")
            print("=" * 60)
            
            # Basic stats
            total_signals = len(df)
            executed = len(df[df['executed'] == True]) if 'executed' in df.columns else 0
            filtered = len(df[df['executed'] == False]) if 'executed' in df.columns else 0
            
            print(f"Total Signals Analyzed: {total_signals}")
            print(f"Executed by Main System: {executed}")
            print(f"Filtered by Main System: {filtered}")
            print(f"Execution Rate: {executed/total_signals:.1%}" if total_signals > 0 else "No data")
            
            # Profitability analysis
            if 'theoretical_profit_15m' in df.columns:
                all_profits = df['theoretical_profit_15m'].dropna()
                executed_profits = df[df['executed'] == True]['theoretical_profit_15m'].dropna() if 'executed' in df.columns else pd.Series()
                filtered_profits = df[df['executed'] == False]['theoretical_profit_15m'].dropna() if 'executed' in df.columns else pd.Series()
                
                print(f"\n📊 PROFITABILITY ANALYSIS:")
                if len(all_profits) > 0:
                    print(f"Overall Win Rate: {(all_profits > 0).mean():.1%}")
                    print(f"Overall Avg Profit: {all_profits.mean():+.2%}")
                
                if len(executed_profits) > 0:
                    print(f"Executed Win Rate: {(executed_profits > 0).mean():.1%}")
                    print(f"Executed Avg Profit: {executed_profits.mean():+.2%}")
                
                if len(filtered_profits) > 0:
                    print(f"Filtered Win Rate: {(filtered_profits > 0).mean():.1%}")
                    print(f"Filtered Avg Profit: {filtered_profits.mean():+.2%}")
                    
                    # Missed opportunities
                    missed_profit = filtered_profits.sum()
                    if missed_profit > 0:
                        print(f"🚨 TOTAL MISSED PROFIT: {missed_profit:+.2%}")
            
            # Adaptation status
            print(f"\n🎯 ADAPTIVE LEARNING STATUS:")
            adaptation_file = f"dependencies_v1/adaptive_strategy_{pair.lower()}.json"
            if os.path.exists(adaptation_file):
                with open(adaptation_file, 'r') as f:
                    adaptation_data = json.load(f)
                    adaptations = adaptation_data.get('current_adaptations', {})
                    if adaptations:
                        print(f"  Current Adaptations: {len(adaptations)} active")
                        print(f"  Adaptation Confidence: {adaptations.get('adaptation_confidence', 0):.1%}")
                        print(f"  Last Adaptation Reason: {adaptations.get('reason', 'None')}")
                    else:
                        print(f"  No adaptations currently active")
            else:
                print(f"  Adaptive learning file not found")
            
            print("\n" + "=" * 60)
        else:
            print(f"No shadow trading data found for {pair}")
            
    except Exception as e:
        print(f"Error getting shadow summary: {e}")

logger.info("🔮 COMPLETE Adaptive Shadow Trading System loaded - tracks all signals, learns patterns, and adapts main system!")

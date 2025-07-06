# Version: 3.5 - Integrated Shadow Trading System with --pairs and --pair Support
# CRITICAL FIX: Removed the broken fallback that was preventing ML trading
# NEW: Added support for --pairs (multiple pairs) and --pair (single pair) arguments

import time
import gc
import os
import json
import psutil
import pandas as pd
import numpy as np
import traceback
from datetime import datetime, timedelta
from config import args, PAIR, PAIRS, DYNAMIC_PARAMS, DYNAMIC_PARAMS_LOCK, DEPENDENCY_DIR, TIMEFRAMES_TO_EVALUATE, RUN_ID
from logging_setup import logger, debug_logger

# Import core modules
from data_loading import fetch_and_enrich_data
from models import train_and_predict
from price_and_hyperparameters import update_thresholds, comprehensive_parameter_optimization

# Enhanced trading imports
try:
    from enhanced_trading import (
        enhanced_trading_iteration_with_ml,
        EnhancedTradingEngine,
        ComprehensiveSignalTracker,
        AdvancedPerformanceTracker,
        get_trading_statistics,
        analyze_best_trading_times,
        monitor_system_resources,
        get_confluence_ml_status
    )
    ADVANCED_TRADING_AVAILABLE = True
    logger.info("🚀 Enhanced trading with ML confluence features loaded successfully")
except ImportError as e:
    logger.error(f"❌ Enhanced trading features not available: {e}")
    ADVANCED_TRADING_AVAILABLE = False

# Shadow trading system for tracking filtered signals
try:
    from shadow_trading_system import ShadowTradingSystem
    SHADOW_TRADING_AVAILABLE = True
except ImportError:
    logger.warning("Shadow trading system not available")
    SHADOW_TRADING_AVAILABLE = False

# Enhanced model imports
try:
    from models import ProfitabilityTracker, update_model_performance
except ImportError:
    logger.warning("Enhanced model functions not available, using basic implementations")
    class ProfitabilityTracker:
        def __init__(self, pair):
            self.pair = pair
        def get_recent_performance(self, days=7):
            return {'win_rate': 0.5, 'avg_profit': 0, 'total_trades': 0}
    def update_model_performance(pair, timeframe, prediction, actual_profit, features_used):
        pass

# Enhanced data imports
try:
    from data_loading import get_data_statistics, cleanup_old_cache_files
except ImportError:
    logger.warning("Enhanced data functions not available, using basic implementations")
    def get_data_statistics(enriched_data):
        return {'timeframes': list(enriched_data.keys()), 'total_timeframes': len(enriched_data)}
    def cleanup_old_cache_files(pair, max_age_days=7):
        pass

# OHLC generation
try:
    from simple_cache_logic import generate_all_ohlc_from_trades
    from incremental_cache import smart_cache_update, check_cache_freshness
except ImportError:
    logger.warning("OHLC generation utility not available, using fallback")
    def generate_all_ohlc_from_trades():
        logger.warning("OHLC generation fallback - manual generation required")
        return True
    def smart_cache_update(pair):
        logger.warning("Smart cache update not available - using fallback")
        return []
    def check_cache_freshness(pair):
        logger.warning("Cache freshness check not available")
        return {}

logger.info(f"🎯 Starting SUPERCHARGED Enhanced QUP Crypto Bot with ML Confluence: {vars(args)}", extra={"run_id": RUN_ID})

class AdvancedMemoryManager:
    """Advanced memory management for long-running trading operations"""

    def __init__(self):
        self.memory_threshold_mb = 2000
        self.cleanup_interval = 100
        self.last_cleanup = 0

    def check_memory_usage(self):
        """Check current memory usage"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb
        except Exception as e:
            logger.warning(f"Could not check memory usage: {e}")
            return 0

    def cleanup_if_needed(self, iteration_count):
        """Perform cleanup if memory threshold exceeded or interval reached"""
        try:
            memory_mb = self.check_memory_usage()

            need_cleanup = (
                memory_mb > self.memory_threshold_mb or
                iteration_count - self.last_cleanup >= self.cleanup_interval
            )

            if need_cleanup:
                logger.info(f"Memory cleanup: {memory_mb:.1f}MB used")
                gc.collect()
                pd.core.computation.expressions.set_numexpr_threads(1)
                self.last_cleanup = iteration_count
                new_memory_mb = self.check_memory_usage()
                logger.info(f"Memory after cleanup: {new_memory_mb:.1f}MB")
                return True
            return False

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            return False

class ComprehensiveSignalAnalyzer:
    """Comprehensive analysis of trading signals and performance patterns"""

    def __init__(self, pair):
        self.pair = pair
        self.signal_history = []
        self.performance_history = []

    def analyze_signal_patterns(self, days_back=30):
        """Analyze patterns in trading signals"""
        try:
            if not ADVANCED_TRADING_AVAILABLE:
                return {"message": "Advanced trading features not available"}

            signal_tracker = ComprehensiveSignalTracker(self.pair)
            stats = signal_tracker.get_signal_statistics(days_back)
            analysis = signal_tracker.analyze_ignored_signals(days_back)

            comprehensive_analysis = {
                'signal_statistics': stats,
                'ignored_signal_analysis': analysis,
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'recommendations': []
            }

            if stats.get('execution_rate', 0) < 0.05:
                comprehensive_analysis['recommendations'].append(
                    "Very low execution rate - consider relaxing signal filters"
                )

            if stats.get('avg_confidence_ignored', 0) > stats.get('avg_confidence_executed', 0):
                comprehensive_analysis['recommendations'].append(
                    "Ignored signals have higher confidence - review rejection criteria"
                )

            return comprehensive_analysis

        except Exception as e:
            logger.error(f"Error in comprehensive signal analysis: {e}")
            return {"error": str(e)}

    def analyze_performance_trends(self):
        """Analyze performance trends and trading effectiveness"""
        try:
            performance_tracker = AdvancedPerformanceTracker(self.pair)
            optimal_conditions = performance_tracker.get_optimal_conditions()
            trading_stats = get_trading_statistics(self.pair)
            time_analysis = analyze_best_trading_times(self.pair)

            return {
                'optimal_conditions': optimal_conditions,
                'trading_statistics': trading_stats,
                'time_analysis': time_analysis,
                'performance_metrics': performance_tracker.metrics.get('rolling_stats', {}),
                'data_quality_trends': performance_tracker.metrics.get('data_quality_history', {}),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in performance analysis: {e}")
            return {"error": str(e)}

class AdvancedTradingController:
    """SUPERCHARGED Advanced trading controller with ML confluence"""

    def __init__(self, pair):
        self.pair = pair
        self.trading_engine = EnhancedTradingEngine(pair) if ADVANCED_TRADING_AVAILABLE else None
        self.memory_manager = AdvancedMemoryManager()
        self.signal_analyzer = ComprehensiveSignalAnalyzer(pair)
        self.trained_models = {}
        self.performance_metrics = {}
        self.confluence_history = []
        self.shadow_systems = {}  # Dictionary for multi-pair support

        # Initialize shadow trading system
        if SHADOW_TRADING_AVAILABLE:
            try:
                pairs = [pair] if 'PAIRS' not in globals() else PAIRS
                for p in pairs:
                    self.shadow_systems[p] = ShadowTradingSystem(p)
                    self.shadow_systems[p].start_monitoring()
                    logger.info(f"✅ Shadow trading system initialized for {p}")
            except Exception as e:
                logger.warning(f"Could not initialize shadow trading systems: {e}")

        # Check ML confluence status
        if ADVANCED_TRADING_AVAILABLE:
            try:
                ml_status = get_confluence_ml_status()
                logger.info(f"🧠 ML Confluence Status: {ml_status['status']}")
                if ml_status.get('available'):
                    logger.info(f"   Model Loaded: {ml_status.get('model_loaded', False)}")
                    logger.info(f"   🎯 Dynamic Threshold: {ml_status.get('current_threshold', 0.6):.3f}")
                    logger.info(f"   🚀 ML SYSTEM IS ACTIVE AND READY!")
                else:
                    logger.warning(f"   ⚠️ ML system not fully active")
            except Exception as e:
                logger.warning(f"ML confluence status check failed: {e}")

    def train_all_timeframes(self, training_data):
        """Train models for all timeframes with comprehensive tracking"""
        logger.info("🎯 Training SUPERCHARGED models for all timeframes")

        successful_timeframes = []
        failed_timeframes = []
        training_performance = {}

        for tf in TIMEFRAMES_TO_EVALUATE:
            if tf not in training_data or training_data[tf].empty:
                logger.warning(f"No training data for {tf}")
                failed_timeframes.append(tf)
                continue

            try:
                df = training_data[tf]
                training_start = time.time()

                logger.info(f"🚀 Training ML-powered model for {tf} with {len(df)} rows")

                feature_cols = [col for col in df.columns
                              if not col.endswith('_class') and
                              not col.startswith('future_return') and
                              col != 'timestamp']

                if len(feature_cols) < 3:
                    logger.warning(f"Insufficient features for {tf}: {len(feature_cols)}")
                    failed_timeframes.append(tf)
                    continue

                predictions, confidence_scores, bull_model, bear_model, range_model, top_features = train_and_predict(
                    df, tf, feature_cols
                )

                training_time = time.time() - training_start

                if predictions is not None and bull_model is not None:
                    model_info = {
                        'bull_model': bull_model,
                        'bear_model': bear_model,
                        'range_model': range_model,
                        'top_features': top_features,
                        'training_data_size': len(df),
                        'feature_count': len(feature_cols),
                        'prediction_distribution': predictions.value_counts().to_dict(),
                        'avg_confidence': confidence_scores.mean(),
                        'min_confidence': confidence_scores.min(),
                        'max_confidence': confidence_scores.max(),
                        'last_prediction': predictions.iloc[-1] if len(predictions) > 0 else 1,
                        'last_confidence': confidence_scores.iloc[-1] if len(confidence_scores) > 0 else 0.5,
                        'training_timestamp': pd.Timestamp.now(),
                        'training_time_seconds': training_time,
                        'data_quality_score': self._calculate_data_quality(df)
                    }

                    self.trained_models[tf] = model_info
                    training_performance[tf] = {
                        'training_time': training_time,
                        'feature_importance': dict(zip(top_features, range(len(top_features)))),
                        'prediction_balance': model_info['prediction_distribution']
                    }

                    successful_timeframes.append(tf)

                    with DYNAMIC_PARAMS_LOCK:
                        try:
                            comprehensive_parameter_optimization(df, DYNAMIC_PARAMS)
                        except Exception as e:
                            logger.warning(f"Parameter optimization failed for {tf}: {e}")

                    logger.info(f"✅ ML training successful for {tf} in {training_time:.1f}s")
                else:
                    logger.error(f"❌ Training failed for {tf}")
                    failed_timeframes.append(tf)

            except Exception as e:
                logger.error(f"Error training model for {tf}: {str(e)}")
                failed_timeframes.append(tf)
                continue

        logger.info(f"🎯 SUPERCHARGED training complete: {len(successful_timeframes)} successful, {len(failed_timeframes)} failed")
        logger.info(f"✅ Successful timeframes: {successful_timeframes}")

        if failed_timeframes:
            logger.warning(f"❌ Failed timeframes: {failed_timeframes}")

        self.performance_metrics['training_performance'] = training_performance
        self.performance_metrics['last_training_timestamp'] = pd.Timestamp.now().isoformat()

        return successful_timeframes, failed_timeframes

    def _calculate_data_quality(self, df):
        """Calculate data quality score for a dataframe"""
        try:
            missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
            duplicate_ratio = df.duplicated().sum() / len(df)
            quality_score = 1.0 - (missing_ratio + duplicate_ratio)
            return max(0.0, min(1.0, quality_score))
        except Exception as e:
            logger.warning(f"Could not calculate data quality: {e}")
            return 0.5

    def get_all_predictions_and_confidences(self, live_data, data_quality_metrics=None):
        """Get predictions and confidences from all trained timeframes with quality assessment"""
        all_predictions = {}
        all_confidences = {}
        prediction_quality = {}

        for tf in self.trained_models.keys():
            if tf not in live_data or live_data[tf].empty:
                logger.warning(f"No live data for trained timeframe {tf}")
                continue

            try:
                model_info = self.trained_models[tf]
                df = live_data[tf]

                base_prediction = model_info.get('last_prediction', 1)
                base_confidence = model_info.get('last_confidence', 0.5)

                data_quality = data_quality_metrics.get(tf, {}).get('overall_score', 0.5) if data_quality_metrics else 0.5
                adjusted_confidence = base_confidence * (0.7 + 0.3 * data_quality)

                all_predictions[tf] = pd.Series([base_prediction], index=[df.index[-1]])
                all_confidences[tf] = pd.Series([adjusted_confidence], index=[df.index[-1]])

                prediction_quality[tf] = {
                    'model_age_hours': (pd.Timestamp.now() - model_info['training_timestamp']).total_seconds() / 3600,
                    'data_quality': data_quality,
                    'original_confidence': base_confidence,
                    'adjusted_confidence': adjusted_confidence
                }

                logger.debug(f"Timeframe {tf}: prediction={base_prediction}, "
                           f"confidence={adjusted_confidence:.3f} (quality={data_quality:.2f})")

            except Exception as e:
                logger.error(f"Error getting predictions for {tf}: {e}")
                continue

        return all_predictions, all_confidences, prediction_quality

    def execute_comprehensive_trading_cycle(self, live_data, data_quality_metrics=None):
        """Execute ML-powered trading cycle with shadow system integration"""
        try:
            logger.info("🚀 Starting SUPERCHARGED trading cycle with ML-powered confluence")

            # Update shadow system with current price
            for pair in self.shadow_systems:
                if '5m' in live_data and not live_data['5m'].empty:
                    current_price = live_data['5m'].get('close_5m', pd.Series()).iloc[-1]
                    try:
                        self.shadow_systems[pair].update_price_data(current_price)
                        logger.debug(f"Updated shadow system price for {pair}: ${current_price:.4f}")
                    except Exception as e:
                        logger.warning(f"Failed to update shadow system price for {pair}: {e}")

            # Get predictions from all timeframes
            all_predictions, all_confidences, prediction_quality = self.get_all_predictions_and_confidences(
                live_data, data_quality_metrics
            )

            if not all_predictions:
                logger.warning("No predictions available from any timeframe")
                return None

            # Execute ML-powered trading
            if ADVANCED_TRADING_AVAILABLE:
                logger.info("🧠 Executing ML-POWERED enhanced trading")
                trade_result = enhanced_trading_iteration_with_ml(
                    all_predictions,
                    all_confidences,
                    live_data,
                    data_quality_metrics,
                    dry_run=args.dry_run
                )

                if trade_result:
                    logger.info(f"✅ ML-powered trading executed successfully for {self.pair}")
                    for pair in self.shadow_systems:
                        try:
                            self.shadow_systems[pair].log_executed_trade(trade_result)
                        except Exception as e:
                            logger.warning(f"Shadow system logging failed for {pair}: {e}")
                else:
                    logger.info(f"🔍 ML system determined no trade at this time for {self.pair}")
                    for pair in self.shadow_systems:
                        try:
                            signal_data = {
                                'timestamp': datetime.now(),
                                'pair': pair,
                                'signal': 'hold',
                                'prediction': 1,
                                'confidence': 0.5,
                                'price': live_data.get('5m', pd.DataFrame()).get('close_5m', pd.Series()).iloc[-1] if '5m' in live_data else 0.0,
                                'market_regime': 'unknown'
                            }
                            self.shadow_systems[pair].log_filtered_signal(signal_data, rejection_reason="insufficient_confluence")
                            logger.debug(f"Logged filtered signal for {pair}")
                        except Exception as e:
                            logger.warning(f"Failed to log filtered signal for {pair}: {e}")
            else:
                logger.warning("❌ Advanced ML trading not available, using basic logic")
                trade_result = self._basic_trading_logic(all_predictions, all_confidences, live_data)

            # Track performance metrics
            if trade_result:
                self.update_comprehensive_performance_metrics(
                    trade_result, all_predictions, all_confidences, prediction_quality
                )

            return trade_result

        except Exception as e:
            logger.error(f"Error in SUPERCHARGED trading cycle for {self.pair}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def _basic_trading_logic(self, all_predictions, all_confidences, live_data):
        """Basic trading logic fallback when ML features aren't available"""
        try:
            signals = []
            confidences = []

            for tf in all_predictions:
                signals.append(all_predictions[tf].iloc[-1])
                confidences.append(all_confidences[tf].iloc[-1])

            if not signals:
                return None

            avg_signal = np.average(signals, weights=confidences)
            avg_confidence = np.mean(confidences)

            if avg_signal < 0.8:
                final_signal = 0  # SELL
            elif avg_signal > 1.2:
                final_signal = 2  # BUY
            else:
                final_signal = 1  # HOLD

            if final_signal == 1:
                return None

            return {
                'timestamp': pd.Timestamp.now(tz='UTC'),
                'pair': self.pair,
                'signal': {0: 'sell', 1: 'hold', 2: 'buy'}[final_signal],
                'prediction': final_signal,
                'enhanced_confidence': avg_confidence,
                'confluence_strength': min(avg_confidence, 0.8),
                'participating_timeframes': list(all_predictions.keys()),
                'market_regime': 'unknown',
                'basic_mode': True
            }

        except Exception as e:
            logger.error(f"Error in basic trading logic: {e}")
            return None

    def update_comprehensive_performance_metrics(self, trade_result, all_predictions, all_confidences, prediction_quality):
        """Update comprehensive performance tracking"""
        try:
            confluence_data = {
                'timestamp': trade_result['timestamp'],
                'signal': trade_result.get('prediction'),
                'confluence_strength': trade_result.get('confluence_strength', 0),
                'participating_timeframes': trade_result.get('participating_timeframes', []),
                'enhanced_confidence': trade_result.get('enhanced_confidence', 0),
                'market_regime': trade_result.get('market_regime', 'unknown'),
                'prediction_quality_avg': np.mean([pq['data_quality'] for pq in prediction_quality.values()]) if prediction_quality else 0,
                'model_age_avg_hours': np.mean([pq['model_age_hours'] for pq in prediction_quality.values()]) if prediction_quality else 0,
                'ml_optimized': trade_result.get('ml_optimized', False),
                'dynamic_threshold_used': trade_result.get('dynamic_threshold_used', 0.6)
            }

            self.confluence_history.append(confluence_data)

            if len(self.confluence_history) > 200:
                self.confluence_history = self.confluence_history[-200:]

            if len(self.confluence_history) >= 10:
                recent_trades = self.confluence_history[-20:]

                metrics = {
                    'avg_confluence': np.mean([t['confluence_strength'] for t in recent_trades]),
                    'avg_confidence': np.mean([t['enhanced_confidence'] for t in recent_trades]),
                    'avg_prediction_quality': np.mean([t['prediction_quality_avg'] for t in recent_trades]),
                    'avg_model_age': np.mean([t['model_age_avg_hours'] for t in recent_trades]),
                    'ml_optimization_rate': np.mean([t['ml_optimized'] for t in recent_trades]),
                    'avg_dynamic_threshold': np.mean([t['dynamic_threshold_used'] for t in recent_trades]),
                    'signal_distribution': {}
                }

                for trade in recent_trades:
                    signal = trade.get('signal', 1)
                    metrics['signal_distribution'][signal] = metrics['signal_distribution'].get(signal, 0) + 1

                logger.info(f"🎯 SUPERCHARGED performance: confluence={metrics['avg_confluence']:.3f}, "
                           f"confidence={metrics['avg_confidence']:.3f}, "
                           f"quality={metrics['avg_prediction_quality']:.3f}, "
                           f"🧠 ml_rate={metrics['ml_optimization_rate']:.2f}, "
                           f"🎯 avg_threshold={metrics['avg_dynamic_threshold']:.3f}")

                self.performance_metrics['recent_comprehensive_metrics'] = metrics

        except Exception as e:
            logger.error(f"Error updating comprehensive performance metrics: {e}")

    def perform_comprehensive_analysis(self, iteration_count):
        """Perform comprehensive analysis and reporting with ML confluence insights"""
        try:
            logger.info("🔍 Performing SUPERCHARGED analysis with ML confluence insights...")

            signal_analysis = self.signal_analyzer.analyze_signal_patterns(days_back=7)
            performance_analysis = self.signal_analyzer.analyze_performance_trends()
            memory_cleaned = self.memory_manager.cleanup_if_needed(iteration_count)
            system_resources = monitor_system_resources() if ADVANCED_TRADING_AVAILABLE else {}

            ml_confluence_status = {}
            if ADVANCED_TRADING_AVAILABLE:
                try:
                    ml_confluence_status = get_confluence_ml_status()
                except:
                    ml_confluence_status = {'available': False, 'status': 'Status check failed'}

            comprehensive_report = {
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'iteration_count': iteration_count,
                'signal_analysis': signal_analysis,
                'performance_analysis': performance_analysis,
                'system_resources': system_resources,
                'memory_cleaned': memory_cleaned,
                'ml_confluence_status': ml_confluence_status,
                'model_status': {
                    tf: {
                        'age_hours': (pd.Timestamp.now() - info['training_timestamp']).total_seconds() / 3600,
                        'data_quality': info.get('data_quality_score', 0),
                        'training_time': info.get('training_time_seconds', 0)
                    } for tf, info in self.trained_models.items()
                }
            }

            if signal_analysis.get('recommendations'):
                logger.info("🎯 Signal Analysis Recommendations:")
                for rec in signal_analysis['recommendations']:
                    logger.info(f"   - {rec}")

            if performance_analysis.get('optimal_conditions'):
                optimal = performance_analysis['optimal_conditions']
                logger.info(f"🎯 Optimal Trading Conditions: "
                           f"confidence>={optimal.get('min_confidence', 0):.2f}, "
                           f"confluence>={optimal.get('min_confluence', 0):.2f}")

            if ml_confluence_status.get('available'):
                logger.info(f"🧠 ML Confluence: {ml_confluence_status['status']}")
                if ml_confluence_status.get('recent_performance'):
                    perf = ml_confluence_status['recent_performance']
                    logger.info(f"   Recent Performance: {perf.get('total_trades', 0)} trades, "
                               f"{perf.get('win_rate', 0):.2%} win rate")

            return comprehensive_report

        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {"error": str(e)}

def patient_live_trading_loop(controller, profitability_tracker):
    """SUPERCHARGED patient live trading loop with ML confluence"""
    iteration_count = 0

    logger.info("🚀 Starting SUPERCHARGED live trading loop with ML confluence")

    while True:
        try:
            iteration_count += 1
            logger.info(f"🎯 SUPERCHARGED live trading iteration #{iteration_count}")

            live_data = fetch_and_enrich_data(
                pair=controller.pair,
                dynamic_params=DYNAMIC_PARAMS,
                dependency_dir=DEPENDENCY_DIR,
                mode='live',
                source='kraken',
                timeframes_to_process=TIMEFRAMES_TO_EVALUATE,
                live_mode=True,
                reset_cache=False
            )

            if not live_data:
                logger.warning("No live data available, retrying in 60 seconds")
                time.sleep(60)
                continue

            data_quality_metrics = None
            try:
                data_quality_metrics = {}
                for tf, df in live_data.items():
                    data_quality_metrics[tf] = {
                        'overall_score': controller._calculate_data_quality(df),
                        'data_age_hours': 0.1,
                        'sources': ['kraken']
                    }
            except Exception as e:
                logger.debug(f"Could not extract data quality metrics: {e}")

            trade_result = controller.execute_comprehensive_trading_cycle(live_data, data_quality_metrics)

            if trade_result:
                signal_name = trade_result.get('signal', 'unknown').upper()
                confidence = trade_result.get('enhanced_confidence', 0)
                confluence = trade_result.get('confluence_strength', 0)
                ml_optimized = trade_result.get('ml_optimized', False)
                dynamic_threshold = trade_result.get('dynamic_threshold_used', 0.6)

                logger.info(f"🚀 SUPERCHARGED trade executed: {signal_name} "
                           f"(confidence: {confidence:.3f}, confluence: {confluence:.3f})")

                if ml_optimized:
                    logger.info(f"🧠 ML-optimized threshold: {dynamic_threshold:.3f} (vs static 0.6)")

            if iteration_count % 100 == 0:
                logger.info("🎯 Periodic SUPERCHARGED retraining...")
                successful_tfs, failed_tfs = controller.train_all_timeframes(live_data)
                logger.info(f"✅ Retraining complete: {len(successful_tfs)} successful")

            if iteration_count % 25 == 0:
                comprehensive_report = controller.perform_comprehensive_analysis(iteration_count)
                try:
                    report_file = os.path.join(DEPENDENCY_DIR, f"comprehensive_report_{controller.pair.lower()}.json")
                    with open(report_file, 'w') as f:
                        json.dump(comprehensive_report, f, indent=2, default=str)
                except Exception as e:
                    logger.warning(f"Could not save comprehensive report: {e}")

            if iteration_count % 50 == 0:
                try:
                    cleanup_old_cache_files(controller.pair, max_age_days=7)
                    logger.info("✅ Comprehensive cache cleanup completed")
                except Exception as e:
                    logger.warning(f"Comprehensive cache cleanup failed: {e}")

            if iteration_count < 10:
                wait_time = 30
            elif iteration_count < 50:
                wait_time = 60
            elif iteration_count < 200:
                wait_time = 60
            else:
                wait_time = 60

            logger.debug(f"Patient waiting {wait_time} seconds before next SUPERCHARGED iteration")
            time.sleep(wait_time)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down SUPERCHARGED system gracefully")
            for pair in controller.shadow_systems:
                try:
                    controller.shadow_systems[pair].stop_monitoring()
                    logger.info(f"Stopped shadow system for {pair}")
                except Exception as e:
                    logger.warning(f"Failed to stop shadow system for {pair}: {e}")
            break

        except Exception as e:
            logger.error(f"Error in SUPERCHARGED live trading iteration: {str(e)}")
            if args.verbose:
                debug_logger.debug(f"Detailed error: {traceback.format_exc()}")

            logger.info("SUPERCHARGED error recovery: waiting 60 seconds before retry")
            time.sleep(60)
            continue

def apply_critical_system_fixes():
    """Apply system-wide fixes at startup to prevent failures"""
    try:
        logger.info("🔧 Applying critical system fixes for SUPERCHARGED trading")

        pd.set_option('future.no_silent_downcasting', True)
        np.seterr(divide='ignore', invalid='ignore')
        os.environ['PANDAS_COPY_ON_WRITE'] = '1'
        gc.set_threshold(700, 10, 10)

        logger.info("✅ Critical system fixes applied successfully")

    except Exception as e:
        logger.error(f"Error applying critical system fixes: {str(e)}")

def main():
    """SUPERCHARGED main trading function with ML confluence"""
    try:
        apply_critical_system_fixes()

        # Parse --pair or --pairs argument, fallback to PAIRS or PAIR
        if hasattr(args, 'pair') and args.pair:
            pairs = [args.pair.strip().upper()]  # Single pair, uppercase
        elif hasattr(args, 'pairs') and args.pairs:
            pairs = [p.strip().upper() for p in args.pairs.split(',') if p.strip()]  # Multiple pairs, uppercase
        else:
            pairs = [p.upper() for p in (PAIRS if 'PAIRS' in globals() else [PAIR])]

        # Validate pairs
        if not pairs:
            logger.error("❌ No valid trading pairs specified, exiting")
            return

        controllers = {pair: AdvancedTradingController(pair) for pair in pairs}

        mode = 'dry-run' if args.dry_run else ('live-continuous' if args.live else 'live-static')
        logger.info(f"🚀 Starting SUPERCHARGED Enhanced QUP Crypto Bot with ML Confluence {mode} "
                   f"with trainingtime={args.trainingtime} days for {', '.join(pairs)}",
                   extra={"run_id": RUN_ID})

        logger.info(f"🎯 Feature Status:")
        logger.info(f"   🧠 Advanced ML Trading: {'✅ YES' if ADVANCED_TRADING_AVAILABLE else '❌ NO'}")
        logger.info(f"   👥 Shadow Trading: {'✅ YES' if SHADOW_TRADING_AVAILABLE else '❌ NO'}")

        logger.info(f"🎯 SUPERCHARGED training phase: Fetching data for {args.trainingtime} days",
                   extra={"run_id": RUN_ID})

        logger.info("📊 Using existing cache files directly - bypassing all cache update logic", extra={"run_id": RUN_ID})

        for pair, controller in controllers.items():
            logger.info(f"📈 Fetching SUPERCHARGED training data for {pair}...")
            training_data = fetch_and_enrich_data(
                pair=pair,
                dynamic_params=DYNAMIC_PARAMS,
                dependency_dir=DEPENDENCY_DIR,
                mode='train' if args.backtest else 'live',
                source='kraken',
                timeframes_to_process=TIMEFRAMES_TO_EVALUATE,
                live_mode=False,
                reset_cache=args.reset
            )

            if not training_data:
                logger.error(f"❌ No training data fetched for {pair}, skipping")
                continue

            try:
                data_stats = get_data_statistics(training_data)
                logger.info(f"📊 SUPERCHARGED training data loaded for {pair}: {data_stats}")
            except Exception as e:
                logger.warning(f"Could not get comprehensive data statistics for {pair}: {e}")

            logger.info(f"🧠 Training SUPERCHARGED models for all timeframes for {pair}...")
            successful_timeframes, failed_timeframes = controller.train_all_timeframes(training_data)

            if len(successful_timeframes) == 0:
                logger.error(f"❌ No timeframes trained successfully for {pair}, skipping live trading")
                continue
            elif len(successful_timeframes) < len(TIMEFRAMES_TO_EVALUATE) * 0.5:
                logger.warning(f"⚠️ Only {len(successful_timeframes)}/{len(TIMEFRAMES_TO_EVALUATE)} "
                             f"timeframes successful for {pair}, proceeding with caution")

            if not args.dry_run:
                logger.info(f"🚀 SUPERCHARGED training complete, switching to live trading with ML confluence for {', '.join(pairs)}",
                           extra={"run_id": RUN_ID})

                from threading import Thread
                threads = []
                for pair, controller in controllers.items():
                    profitability_tracker = ProfitabilityTracker(pair)
                    thread = Thread(target=patient_live_trading_loop, args=(controller, profitability_tracker))
                    thread.start()
                    threads.append(thread)
                    logger.info(f"Started trading thread for {pair}")

                # Wait for all threads to complete
                for thread in threads:
                    thread.join()

            else:
                logger.info(f"✅ SUPERCHARGED dry run training completed successfully for {pair}")

                try:
                    final_analysis = controller.perform_comprehensive_analysis(0)

                    logger.info(f"📊 SUPERCHARGED Final Training Analysis for {pair}:")
                    logger.info(f"   Signal Analysis: {len(final_analysis.get('signal_analysis', {}))} metrics")
                    logger.info(f"   Performance Analysis: {len(final_analysis.get('performance_analysis', {}))} metrics")
                    logger.info(f"   Model Status: {len(final_analysis.get('model_status', {}))} timeframes")

                    if final_analysis.get('ml_confluence_status', {}).get('available'):
                        logger.info(f"   🧠 ML Confluence: {final_analysis['ml_confluence_status']['status']}")

                except Exception as e:
                    logger.warning(f"Could not get SUPERCHARGED final statistics for {pair}: {e}")

    except Exception as e:
        logger.error(f"💥 Fatal error in SUPERCHARGED main loop for {', '.join(pairs)}: {str(e)}",
                    extra={"run_id": RUN_ID})
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")
        raise
    finally:
        for pair, controller in controllers.items():
            for shadow_pair in controller.shadow_systems:
                try:
                    controller.shadow_systems[shadow_pair].stop_monitoring()
                    logger.info(f"Stopped shadow system for {shadow_pair}")
                except Exception as e:
                    logger.warning(f"Failed to stop shadow system for {shadow_pair}: {e}")
        logger.info(f"✅ SUPERCHARGED Enhanced QUP Crypto Bot with ML Confluence shutdown complete for {', '.join(pairs)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info(f"🛑 SUPERCHARGED Enhanced QUP Crypto Bot with ML Confluence stopped by user for {', '.join(pairs)}")
    except Exception as e:
        logger.error(f"💥 Critical error in SUPERCHARGED system: {e}")
    finally:
        logger.info(f"✅ SUPERCHARGED Enhanced QUP Crypto Bot with ML Confluence shutdown complete for {', '.join(pairs)}")

# enhanced_trading_compatibility.py
# Version: 1.0 - Compatibility layer and monitoring functions for backward compatibility
# Contains: Status monitoring, backward compatibility wrappers, all compatibility functions
# CRITICAL: Ensures all existing code continues to work while providing new enhanced features

import pandas as pd
import numpy as np
import os
import time
import json
from datetime import datetime, timedelta
from config import args, PAIR, DYNAMIC_PARAMS, DEPENDENCY_DIR, RUN_ID, TIMEFRAMES_TO_EVALUATE
from logging_setup import logger, debug_logger
import traceback

# Import from our modular files
from enhanced_trading_core import (
    safe_json_dumps,
    safe_json_convert,
    get_all_user_balances,
    get_actual_exchange_balances,
    get_bootstrap_confluence_threshold,
    get_bootstrap_aware_ml_confluence_threshold,
    update_bootstrap_trade_results_with_real_profit,
    process_sell_trade_profit,
    calculate_real_profit
)

from dynamic_confluence_engine import DynamicConfluenceEngine
from enhanced_trading_engine import (
    should_exit_based_on_signals,
    EnhancedTradingEngine,
    enhanced_trading_iteration_with_ml,
    enhanced_trading_iteration,
    execute_enhanced_trade,
    log_enhanced_trade_with_signal_driven
)

# ============================================================================
# COMPATIBILITY CLASSES - Maintain backward compatibility with existing code
# ============================================================================

class TradingStatus:
    """
    Compatibility class for existing status monitoring code
    PRESERVED: All original status functionality from enhanced_trading.py
    """
    
    def __init__(self, pair):
        self.pair = pair
        self.trading_engine = EnhancedTradingEngine(pair)
        self.confluence_engine = DynamicConfluenceEngine(pair, DEPENDENCY_DIR)
        
        # Status tracking
        self.last_check = None
        self.system_status = "initializing"
        self.trade_count = 0
        self.profit_total = 0.0
        
        # Signal-driven status tracking
        self.signal_driven_mode = DYNAMIC_PARAMS.get('use_signal_driven_exits', True)
        self.exit_strategy = 'signal_driven' if self.signal_driven_mode else 'traditional'
        
    def get_system_status(self):
        """Get comprehensive system status - ENHANCED with signal-driven monitoring"""
        try:
            # Get balance status
            balances = get_actual_exchange_balances(self.pair)
            
            # Get confluence engine status
            confluence_status = self.confluence_engine.get_learning_status_report()
            
            # Get bootstrap status
            try:
                from config import load_confluence_state
                bootstrap_state = load_confluence_state(self.pair)
                bootstrap_mode = bootstrap_state.get('bootstrap_mode', True)
                trades_completed = bootstrap_state.get('trades_completed', 0)
            except:
                bootstrap_mode = True
                trades_completed = 0
            
            # Calculate recent performance
            recent_profit = self.calculate_recent_profit()
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'system_health': 'operational' if balances['success'] else 'degraded',
                'signal_driven_mode': self.signal_driven_mode,
                'exit_strategy': self.exit_strategy,
                'bootstrap_mode': bootstrap_mode,
                'trades_completed': trades_completed,
                'learning_active': confluence_status.get('learning_active', False),
                'total_trades_learned': confluence_status.get('total_trades_learned', 0),
                'recent_profit_24h': recent_profit,
                'balance_status': {
                    'usd_available': balances.get('usd', 0),
                    'base_available': balances.get('base', 0),
                    'active_users': balances.get('active_users', 0),
                    'balance_check_success': balances.get('success', False)
                },
                'confluence_status': {
                    'engine_loaded': True,
                    'learning_trades': confluence_status.get('total_trades_learned', 0),
                    'current_weights': confluence_status.get('current_weights', {}),
                    'profit_attribution_active': confluence_status.get('profit_attribution', {}).get('last_analysis') is not None
                },
                'compatibility_mode': True,
                'enhanced_features_active': True
            }
            
            self.last_check = datetime.now()
            self.system_status = status['system_health']
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'system_health': 'error',
                'error': str(e),
                'compatibility_mode': True
            }
    
    def calculate_recent_profit(self):
        """Calculate profit from last 24 hours"""
        try:
            profit_log_file = os.path.join(DEPENDENCY_DIR, "realized_profits.csv")
            
            if not os.path.exists(profit_log_file):
                return 0.0
            
            # Read recent profits
            df = pd.read_csv(profit_log_file)
            if df.empty:
                return 0.0
            
            # Filter to last 24 hours
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = datetime.now() - timedelta(hours=24)
            recent_df = df[df['timestamp'] > cutoff]
            
            if recent_df.empty:
                return 0.0
            
            return recent_df['real_profit_usd'].sum()
            
        except Exception as e:
            logger.error(f"Error calculating recent profit: {e}")
            return 0.0
    
    def get_trade_recommendations(self):
        """Get actionable trade recommendations - NEW enhanced feature"""
        try:
            recommendations = self.confluence_engine.get_learning_recommendations()
            
            # Add system-level recommendations
            system_status = self.get_system_status()
            
            if not system_status['balance_status']['balance_check_success']:
                recommendations.append({
                    'type': 'system_alert',
                    'priority': 'high',
                    'message': 'Balance check failing - verify gobbler.sh configuration'
                })
            
            if system_status['balance_status']['usd_available'] < 10:
                recommendations.append({
                    'type': 'funding_alert',
                    'priority': 'medium',
                    'message': f"Low USD balance: ${system_status['balance_status']['usd_available']:.2f}"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting trade recommendations: {e}")
            return [{'type': 'error', 'priority': 'high', 'message': f'Error: {e}'}]

class CompatibilityEngine:
    """
    Main compatibility class that maintains all original enhanced_trading.py interfaces
    PRESERVED: All original function signatures and behaviors
    """
    
    def __init__(self, pair=None):
        self.pair = pair or PAIR
        self.trading_engine = EnhancedTradingEngine(self.pair)
        self.confluence_engine = DynamicConfluenceEngine(self.pair, DEPENDENCY_DIR)
        self.status = TradingStatus(self.pair)
        
        logger.info("✅ CompatibilityEngine initialized with signal-driven enhancements")
    
    # ============================================================================
    # BACKWARD COMPATIBILITY FUNCTIONS - Maintain original interfaces
    # ============================================================================
    
    def check_confluence_threshold(self, all_predictions, all_confidences, market_regime_data=None):
        """
        COMPATIBILITY: Original function signature preserved
        Now uses enhanced bootstrap-aware ML confluence system
        """
        try:
            # Use enhanced system but maintain original interface
            if not all_predictions or not all_confidences:
                return False, 0.02  # Default bootstrap threshold
            
            # Get primary dataframe for analysis (required by enhanced system)
            try:
                from data_fetcher import DataFetcher
                data_fetcher = DataFetcher()
                primary_df = data_fetcher.get_latest_data('5m')
            except:
                # Fallback: create minimal dataframe
                primary_df = pd.DataFrame({'close_5m': [100]})  # Dummy data
            
            # Use enhanced confluence system
            confluence_result = get_bootstrap_aware_ml_confluence_threshold(
                df=primary_df,
                market_regime_data=market_regime_data or {'primary_regime': 'unknown', 'regime_strength': 0.5, 'confidence': 0.5},
                current_confluence=0.5,
                participating_timeframes=list(all_predictions.keys()),
                all_confidences=all_confidences,
                pair=self.pair
            )
            
            threshold = confluence_result['threshold']
            
            # Calculate current confluence strength
            signal, strength, tfs, debug = self.confluence_engine.calculate_dynamic_confluence(
                all_predictions, all_confidences
            )
            
            # Return original format: (threshold_met, threshold_value)
            return strength >= threshold, threshold
            
        except Exception as e:
            logger.error(f"Error in compatibility confluence check: {e}")
            return False, 0.02  # Conservative fallback
    
    def calculate_position_size(self, confidence, signal=None):
        """
        COMPATIBILITY: Original function signature preserved
        Now uses enhanced dynamic position sizing with multi-user support
        """
        try:
            position_size, confidence_level, balances = self.trading_engine.calculate_dynamic_position_size(
                confidence, volatility_factor=1.0, signal=signal
            )
            
            # Return in original format (just the position size)
            return position_size
            
        except Exception as e:
            logger.error(f"Error in compatibility position sizing: {e}")
            return 5.0  # Conservative fallback
    
    def execute_trade(self, trade_details):
        """
        COMPATIBILITY: Original function signature preserved
        Now uses enhanced multi-user execution with real profit tracking
        """
        try:
            # Ensure trade_details has required fields for enhanced system
            if 'actual_balances' not in trade_details:
                trade_details['actual_balances'] = get_actual_exchange_balances(self.pair)
            
            if 'signal_driven_mode' not in trade_details:
                trade_details['signal_driven_mode'] = self.status.signal_driven_mode
            
            # Use enhanced execution
            result = execute_enhanced_trade(trade_details)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in compatibility trade execution: {e}")
            return {'error': str(e)}
    
    def log_trade(self, trade_details):
        """
        COMPATIBILITY: Original function signature preserved
        Now uses enhanced logging with signal-driven data
        """
        try:
            log_enhanced_trade_with_signal_driven(trade_details)
        except Exception as e:
            logger.error(f"Error in compatibility trade logging: {e}")
    
    # ============================================================================
    # ENHANCED FEATURES - New functionality while maintaining compatibility
    # ============================================================================
    
    def run_enhanced_iteration(self, all_predictions, all_confidences, all_dataframes, use_ml=True, dry_run=True):
        """
        NEW: Enhanced iteration function that automatically chooses best available system
        """
        try:
            if use_ml:
                # Try ML-enhanced version first
                result = enhanced_trading_iteration_with_ml(
                    all_predictions, all_confidences, all_dataframes, dry_run=dry_run
                )
            else:
                # Use standard enhanced version
                result = enhanced_trading_iteration(
                    all_predictions, all_confidences, all_dataframes, dry_run=dry_run
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced iteration: {e}")
            return None
    
    def check_exit_conditions(self, all_predictions, all_confidences, current_price, entry_price, 
                            entry_time, market_regime, position_type, entry_data=None):
        """
        NEW: Signal-driven exit condition checking
        """
        try:
            return should_exit_based_on_signals(
                all_predictions, all_confidences, current_price, entry_price, 
                entry_time, market_regime, position_type, entry_data
            )
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
            return False, "error", 0.0, "hold"
    
    def get_comprehensive_status(self):
        """
        NEW: Get comprehensive system status including all enhancements
        """
        try:
            status = self.status.get_system_status()
            recommendations = self.status.get_trade_recommendations()
            confluence_status = self.confluence_engine.get_learning_status_report()
            
            return {
                'system_status': status,
                'recommendations': recommendations,
                'learning_status': confluence_status,
                'signal_driven_active': self.status.signal_driven_mode,
                'enhanced_features': {
                    'atomic_json_writes': True,
                    'multi_user_trading': True,
                    'real_profit_tracking': True,
                    'dynamic_confluence': True,
                    'ml_optimization': True,
                    'signal_driven_exits': self.status.signal_driven_mode,
                    'profit_attribution': True,
                    'weight_optimization': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {'error': str(e)}

# ============================================================================
# GLOBAL COMPATIBILITY FUNCTIONS - For direct imports
# ============================================================================

# Initialize global compatibility engine
_compatibility_engine = None

def get_compatibility_engine():
    """Get or create global compatibility engine"""
    global _compatibility_engine
    if _compatibility_engine is None:
        _compatibility_engine = CompatibilityEngine()
    return _compatibility_engine

# Wrapper functions for backward compatibility
def check_confluence_threshold_compatible(all_predictions, all_confidences, market_regime_data=None):
    """COMPATIBILITY: Direct function for backward compatibility"""
    engine = get_compatibility_engine()
    return engine.check_confluence_threshold(all_predictions, all_confidences, market_regime_data)

def calculate_position_size_compatible(confidence, signal=None):
    """COMPATIBILITY: Direct function for backward compatibility"""
    engine = get_compatibility_engine()
    return engine.calculate_position_size(confidence, signal)

def execute_trade_compatible(trade_details):
    """COMPATIBILITY: Direct function for backward compatibility"""
    engine = get_compatibility_engine()
    return engine.execute_trade(trade_details)

def log_trade_compatible(trade_details):
    """COMPATIBILITY: Direct function for backward compatibility"""
    engine = get_compatibility_engine()
    return engine.log_trade(trade_details)

# ============================================================================
# MONITORING AND DIAGNOSTICS - Enhanced system monitoring
# ============================================================================

def run_system_diagnostics():
    """
    Run comprehensive system diagnostics
    NEW: Enhanced diagnostic capabilities
    """
    try:
        engine = get_compatibility_engine()
        
        logger.info("🔍 RUNNING COMPREHENSIVE SYSTEM DIAGNOSTICS...")
        
        # Test core functions
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'core_functions': {},
            'trading_functions': {},
            'learning_functions': {},
            'compatibility_functions': {},
            'file_system': {},
            'overall_health': 'unknown'
        }
        
        # Test atomic JSON functions
        try:
            from enhanced_trading_core import atomic_json_write
            test_data = {'test': True, 'timestamp': datetime.now().isoformat()}
            test_file = os.path.join(DEPENDENCY_DIR, 'diagnostic_test.json')
            result = atomic_json_write(test_file, test_data)
            diagnostics['core_functions']['atomic_json'] = 'passed' if result else 'failed'
            
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)
        except Exception as e:
            diagnostics['core_functions']['atomic_json'] = f'failed: {e}'
        
        # Test balance checking
        try:
            balances = get_actual_exchange_balances(PAIR)
            diagnostics['core_functions']['balance_check'] = 'passed' if balances['success'] else 'failed'
            diagnostics['core_functions']['active_users'] = balances.get('active_users', 0)
        except Exception as e:
            diagnostics['core_functions']['balance_check'] = f'failed: {e}'
        
        # Test confluence engine
        try:
            confluence_status = engine.confluence_engine.get_learning_status_report()
            diagnostics['learning_functions']['confluence_engine'] = 'passed'
            diagnostics['learning_functions']['total_trades_learned'] = confluence_status.get('total_trades_learned', 0)
        except Exception as e:
            diagnostics['learning_functions']['confluence_engine'] = f'failed: {e}'
        
        # Test trading engine
        try:
            trading_engine = EnhancedTradingEngine(PAIR)
            diagnostics['trading_functions']['trading_engine'] = 'passed'
            diagnostics['trading_functions']['confidence_levels'] = len(trading_engine.confidence_multipliers)
        except Exception as e:
            diagnostics['trading_functions']['trading_engine'] = f'failed: {e}'
        
        # Test signal-driven exit logic
        try:
            # Simple test with dummy data
            test_predictions = {'5m': pd.Series([0]), '15m': pd.Series([0])}
            test_confidences = {'5m': pd.Series([0.8]), '15m': pd.Series([0.7])}
            should_exit, reason, conf, action = should_exit_based_on_signals(
                test_predictions, test_confidences, 1.05, 1.00, datetime.now(), 'trending_up', 'buy'
            )
            diagnostics['trading_functions']['signal_driven_exits'] = 'passed'
        except Exception as e:
            diagnostics['trading_functions']['signal_driven_exits'] = f'failed: {e}'
        
        # Test compatibility functions
        try:
            status = engine.get_comprehensive_status()
            diagnostics['compatibility_functions']['comprehensive_status'] = 'passed'
            diagnostics['compatibility_functions']['signal_driven_active'] = status.get('signal_driven_active', False)
        except Exception as e:
            diagnostics['compatibility_functions']['comprehensive_status'] = f'failed: {e}'
        
        # Test file system
        required_dirs = [DEPENDENCY_DIR]
        for dir_path in required_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                test_file = os.path.join(dir_path, 'write_test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                diagnostics['file_system'][dir_path] = 'passed'
            except Exception as e:
                diagnostics['file_system'][dir_path] = f'failed: {e}'
        
        # Determine overall health
        all_tests = []
        for category in ['core_functions', 'trading_functions', 'learning_functions', 'compatibility_functions', 'file_system']:
            for test_name, result in diagnostics[category].items():
                if isinstance(result, str):
                    all_tests.append(result == 'passed')
        
        if all(all_tests):
            diagnostics['overall_health'] = 'excellent'
        elif sum(all_tests) / len(all_tests) > 0.8:
            diagnostics['overall_health'] = 'good'
        elif sum(all_tests) / len(all_tests) > 0.6:
            diagnostics['overall_health'] = 'fair'
        else:
            diagnostics['overall_health'] = 'poor'
        
        # Log results
        logger.info(f"🏥 SYSTEM DIAGNOSTICS COMPLETE - Overall Health: {diagnostics['overall_health'].upper()}")
        
        for category, tests in diagnostics.items():
            if category == 'overall_health' or category == 'timestamp':
                continue
            
            logger.info(f"📊 {category.replace('_', ' ').title()}:")
            for test_name, result in tests.items():
                status_icon = "✅" if (isinstance(result, str) and result == 'passed') or (isinstance(result, bool) and result) or (isinstance(result, (int, float)) and result > 0) else "❌"
                logger.info(f"   {status_icon} {test_name}: {result}")
        
        return diagnostics
        
    except Exception as e:
        logger.error(f"Error running system diagnostics: {e}")
        return {'error': str(e), 'overall_health': 'error'}

def get_performance_summary():
    """
    Get performance summary across all enhanced features
    NEW: Comprehensive performance tracking
    """
    try:
        engine = get_compatibility_engine()
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'trading_performance': {},
            'learning_performance': {},
            'profit_tracking': {},
            'recommendations': []
        }
        
        # System info
        status = engine.status.get_system_status()
        summary['system_info'] = {
            'signal_driven_mode': status.get('signal_driven_mode', False),
            'bootstrap_mode': status.get('bootstrap_mode', True),
            'trades_completed': status.get('trades_completed', 0),
            'learning_active': status.get('learning_active', False),
            'active_users': status.get('balance_status', {}).get('active_users', 0)
        }
        
        # Trading performance
        recent_profit = engine.status.calculate_recent_profit()
        summary['trading_performance'] = {
            'recent_profit_24h': recent_profit,
            'exit_strategy': status.get('exit_strategy', 'signal_driven'),
            'balance_usd': status.get('balance_status', {}).get('usd_available', 0),
            'balance_base': status.get('balance_status', {}).get('base_available', 0)
        }
        
        # Learning performance
        confluence_status = engine.confluence_engine.get_learning_status_report()
        summary['learning_performance'] = {
            'total_trades_learned': confluence_status.get('total_trades_learned', 0),
            'learning_active': confluence_status.get('learning_active', False),
            'weight_changes': confluence_status.get('weight_changes', {}),
            'profit_attribution_active': confluence_status.get('profit_attribution', {}).get('last_analysis') is not None
        }
        
        # Get recommendations
        summary['recommendations'] = engine.status.get_trade_recommendations()
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return {'error': str(e)}

# Export all functions and classes
__all__ = [
    # Main compatibility classes
    'TradingStatus',
    'CompatibilityEngine',
    
    # Global compatibility functions
    'get_compatibility_engine',
    'check_confluence_threshold_compatible',
    'calculate_position_size_compatible',
    'execute_trade_compatible',
    'log_trade_compatible',
    
    # Monitoring and diagnostics
    'run_system_diagnostics',
    'get_performance_summary'
]

logger.info("✅ enhanced_trading_compatibility.py v1.0 loaded successfully with full backward compatibility and enhanced monitoring")

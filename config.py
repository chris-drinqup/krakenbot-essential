# Version: 2.2 - Enhanced config.py with Shadow Trading and Multi-Pair Support
# MAJOR UPDATE: Added PAIRS variable and --pairs argument while preserving all existing functionality
# NEW FEATURES: Shadow trading compatibility, multi-pair support
# PRESERVED: All aggressive trading settings, signal-driven mode, existing functionality

import os
import argparse
from threading import Lock
import json

def parse_args():
    parser = argparse.ArgumentParser(description='Quebot configuration - SIGNAL-DRIVEN TRADING MODE with Shadow Trading')
    parser.add_argument('--pair', type=str, help='Single trading pair (e.g., ADAUSDT)')
    parser.add_argument('--pairs', type=str, help='Comma-separated list of trading pairs (e.g., ADAUSDT,BTCUSDT,ETHUSDT)')
    parser.add_argument('--trainingtime', type=int, default=150, help='Number of days for data')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--noise', action='store_true', help='Add noise to indicators')
    parser.add_argument('--reset', action='store_true', help='Reset cache')
    parser.add_argument('--export_indicators', action='store_true', help='Export indicators to parquet')
    parser.add_argument('--no-nohup', action='store_true', help='Disable nohup console output')
    parser.add_argument('--harmonics', action='store_true', help='Enable harmonic pattern detection')
    parser.add_argument('--runalltimes', action='store_true', help='Process all timeframes')
    parser.add_argument('--grok', action='store_true', help='Use Grok for AI validation')
    parser.add_argument('--openai', action='store_true', help='Use OpenAI for AI validation')
    parser.add_argument('--allai', action='store_true', help='Use all AI models for validation')
    parser.add_argument('--order_type', type=str, default='market', help='Order type (market/limit)')
    parser.add_argument('--dry_run', action='store_true', help='Simulate trades without execution')
    parser.add_argument('--live', action='store_true', help='Run in live trading mode')
    parser.add_argument('--backtest', action='store_true', help='Run in backtest mode')
    parser.add_argument('--run_id', type=str, default='quebot_run', help='Unique run identifier')
    parser.add_argument('--loose_filtering', action='store_true', help='Enable loose trade filtering')
    parser.add_argument('--aggressive', action='store_true', help='Enable AGGRESSIVE micro-trading mode')
    return parser.parse_args()

args = parse_args()

DEPENDENCY_DIR = os.path.join(os.path.dirname(__file__), 'dependencies_v1')

# ENHANCED: Multi-pair support with backward compatibility
# Default pairs for shadow trading and multi-pair support
DEFAULT_PAIRS = ["ADAUSDT", "BTCUSDT", "ETHUSDT"]

# Determine PAIR and PAIRS based on arguments
if args.pair:
    PAIR = args.pair.upper()
    PAIRS = [PAIR]  # Single pair as list for compatibility
elif args.pairs:
    pairs_list = [p.strip().upper() for p in args.pairs.split(',') if p.strip()]
    PAIRS = pairs_list
    PAIR = pairs_list[0] if pairs_list else "ADAUSDT"  # First pair as primary
else:
    # No arguments provided - use defaults
    PAIR = "ADAUSDT"
    PAIRS = DEFAULT_PAIRS

# Ensure PAIRS is always a list
if not isinstance(PAIRS, list):
    PAIRS = [PAIRS]

RUN_ID = args.run_id
TRAINING_DAYS = args.trainingtime
SPARSITY_THRESHOLD = 0.5
SAMPLES_SINCE_UPDATE = 0
MODEL_UPDATE_INFO = {'samples_since_update': 0}

TIMEFRAMES = {
    '5m': 5,
    '15m': 15,
    '30m': 30,
    '1h': 60,
    '4h': 240,
    '6h': 360,
    '1d': 1440,
}

# AGGRESSIVE: Reduced minimum trades for faster updates
TIMEFRAME_MIN_TRADES = {
    '5m': 2,     # AGGRESSIVE: Reduced from 5 - very responsive
    '15m': 3,    # AGGRESSIVE: Reduced from 8 - quick updates
    '30m': 4,    # AGGRESSIVE: Reduced from 12 - balanced
    '1h': 6,     # AGGRESSIVE: Reduced from 18 - good data quality
    '4h': 8,     # AGGRESSIVE: Reduced from 25 - trend confirmation
    '6h': 10,    # AGGRESSIVE: Reduced from 35 - structure analysis
    '1d': 15     # AGGRESSIVE: Reduced from 45 - long-term view
}

def get_min_trades_for_timeframe(timeframe):
    """Get minimum trades required for timeframe update"""
    return TIMEFRAME_MIN_TRADES.get(timeframe, 5)  # AGGRESSIVE: Lower default fallback

TIMEFRAMES_TO_EVALUATE = ['5m', '15m', '30m', '1h', '4h', '6h']
HARMONIC_TIMEFRAMES = ['5m', '15m', '30m']
FEATURE_CACHE_ENABLED = True

ENABLE_TRADE_LEARNING = True
TRADE_RESULTS_FILE = os.path.join(DEPENDENCY_DIR, f'trade_results_{PAIR.lower().replace("/", "")}.json')
MODEL_PERFORMANCE_FILE = os.path.join(DEPENDENCY_DIR, f'model_performance_{PAIR.lower().replace("/", "")}.json')

# AGGRESSIVE: More permissive live trading configuration
LIVE_TRADING_CONFIG = {
    'min_confidence_threshold': 0.2,  # AGGRESSIVE: Reduced from 0.7 to 0.2
    'max_trades_per_timeframe': 100,  # AGGRESSIVE: Increased from 1 to 100 for micro-trading
    'trade_volume_usd': 50.0,  # AGGRESSIVE: Reduced from 1000.0 to 50.0 for micro-trades
    'update_interval_seconds': 60,  # AGGRESSIVE: Reduced from 300 to 60 for faster updates
    'performance_check_interval': 24,
    'min_win_rate_threshold': 0.1,  # AGGRESSIVE: Reduced from 0.3 to 0.1
    'min_trades_for_evaluation': 3  # AGGRESSIVE: Reduced from 10 to 3
}

POSITION_STATE_DIR = DEPENDENCY_DIR
GOBBLER_SCRIPT_PATH = os.path.join(DEPENDENCY_DIR, "gobbler.sh")

# SIGNAL-DRIVEN TRADING PARAMETERS - Let ML confluence determine all exits
DYNAMIC_PARAMS = {
    # AGGRESSIVE CONFLUENCE SETTINGS
    'min_confluence': 0.01,              # AGGRESSIVE: Ultra-low (was 0.25) - accept almost any signal
    'confidence_requirement': 0.05,      # AGGRESSIVE: Ultra-low (was 0.40) - trade on weak signals
    'min_timeframes': 1,                 # AGGRESSIVE: Only need 1 timeframe (was 1)
    'buy_threshold': 0.95,               # AGGRESSIVE: Easier to trigger (was 1.0)
    'sell_threshold': 1.05,              # AGGRESSIVE: Easier to trigger (was 1.0)

    # AGGRESSIVE BOOTSTRAP SETTINGS
    'bootstrap_mode': True,
    'bootstrap_trades_needed': 5,        # AGGRESSIVE: Immediate bootstrap completion (was 3)
    'target_min_confluence': 0.05,       # AGGRESSIVE: Ultra-low target (was 0.55)
    'target_confidence_requirement': 0.15, # AGGRESSIVE: Ultra-low target (was 0.65)
    'target_min_timeframes': 1,          # AGGRESSIVE: Single timeframe OK (was 2)
    'target_buy_threshold': 0.98,        # AGGRESSIVE: Easier targets (was 1.07)
    'target_sell_threshold': 1.02,       # AGGRESSIVE: Easier targets (was 0.93)

    # AGGRESSIVE TRADING PHILOSOPHY
    'patient_mode': False,               # AGGRESSIVE: Disable patience for maximum activity
    'max_consecutive_no_signals': 5,    # AGGRESSIVE: Much lower (was 1000)
    'log_patience_every_n_signals': 5,   # AGGRESSIVE: More frequent logging (was 50)

    # ALL INDICATORS ACTIVE FOR MAXIMUM SIGNAL GENERATION
    'active_indicators': [
        'RSI', 'VW_RSI', 'SMA', 'EMA', 'EMA_slope', 'MACD', 'Signal',
        'VW_MACD', 'VW_Signal', 'BB_Upper', 'BB_Lower', 'ATR', 'momentum',
        'ADX', 'Plus_DI', 'Minus_DI', 'ROC', 'PPO', 'PPO_Signal', 'CCI',
        'KO', 'VI_Plus', 'VI_Minus', 'STC', 'UO', 'STOCH_k', 'STOCH_d',
        'WilliamsR', 'Trend_Strength', 'Bull_Engulfing', 'Bear_Engulfing',
        'KC_Upper', 'KC_Lower'
    ],

    # SIGNAL-DRIVEN EXIT STRATEGY - REMOVED ARTIFICIAL PROFIT CAPS
    'use_signal_driven_exits': True,                # NEW: Let signals determine exits
    'signal_driven_stop_loss': True,               # NEW: Let signals predict continued drops
    'min_profit_after_fees': 0.004,                # NEW: 0.4% minimum after fees (0.3% trading fee)
    'emergency_stop_loss': 0.03,                   # NEW: 3% emergency stop only
    'max_hold_time_hours': 72,                     # NEW: 3 days max hold (safety)

    # REMOVED: These artificial caps that were limiting profits
    # 'profit_percentage_1': 0.005,        # REMOVED - was capping at 0.5%
    # 'profit_percentage_2': 0.008,        # REMOVED - was capping at 0.8%
    # 'stop_loss_percentage_1': 0.003,     # REMOVED - was too tight at 0.3%

    # SIGNAL CONFIDENCE REQUIREMENTS FOR EXITS
    'sell_signal_confidence_min': 0.6,             # Only sell on confident sell signals
    'profit_protection_confidence': 0.75,          # Higher confidence for profit protection
    'loss_prevention_confidence': 0.5,             # Lower confidence for loss prevention

    # TRAILING STOP PARAMETERS
    'trailing_stop_enabled': True,                 # Enable trailing stops for large gains
    'trailing_stop_distance': 0.005,               # 0.5% trailing distance
    'trail_only_after_profit': 0.015,              # Only trail after 1.5% profit

    'rsi_overbought_1': 75,              # AGGRESSIVE: More relaxed (was 70)
    'rsi_oversold_2': 25,                # AGGRESSIVE: More relaxed (was 30)

    # AGGRESSIVE HARMONIC SETTINGS
    'harmonic_threshold': 0.05,          # AGGRESSIVE: More sensitive (was 0.1)
    'point_distance_threshold': 0.001,   # AGGRESSIVE: More sensitive (was 0.0005)
    'selected_timeframe': '5m',
    'active_harmonics': [
        'bull_gartley', 'bear_gartley', 'bull_butterfly', 'bear_butterfly',
        'bull_bat', 'bear_bat', 'bull_crab', 'bear_crab', 'bull_shark',
        'bear_shark', 'bull_cypher', 'bear_cypher', 'bull_alt_bat',
        'bear_alt_bat', 'bull_deep_crab', 'bear_deep_crab', 'bull_nen_star',
        'bear_nen_star', 'bull_3_drive', 'bear_3_drive', 'bull_abcd', 'bear_abcd'
    ],

    # AGGRESSIVE POSITION SIZING
    'portfolio_size': 1000.0,
    'risk_threshold': 2.0,               # AGGRESSIVE: Higher risk tolerance (was 1.0)
    'max_position_size_pct': 25.0,       # AGGRESSIVE: Larger positions (was 15.0)
    'min_position_size': 25.0,           # AGGRESSIVE: Smaller minimum (was 50.0)
    'min_data_quality_score': 0.3,       # AGGRESSIVE: Much lower requirement (was 0.6)
    'quality_confidence_adjustment': 0.05, # AGGRESSIVE: Less penalty (was 0.1)

    # AGGRESSIVE SOURCE RELIABILITY (more permissive)
    'source_reliability_weights': {
        'kraken': 1.0,
        'binance': 1.0,                  # AGGRESSIVE: Equal weight (was 0.95)
        'coinbase': 1.0,                 # AGGRESSIVE: Equal weight (was 0.9)
        'cache': 1.0                     # AGGRESSIVE: Equal weight (was 0.85)
    },

    # AGGRESSIVE VOLUME SETTINGS (disabled barriers)
    'volume_confirmation_required': True,  # AGGRESSIVE: Completely disabled
    'min_volume_strength': 0.3,          # AGGRESSIVE: Much lower (was 0.5)
    'volume_surge_threshold': 1.2,       # AGGRESSIVE: Much lower (was 1.5)
    'large_trade_percentile': 0.85,      # AGGRESSIVE: Lower threshold (was 0.95)

    # AGGRESSIVE PERFORMANCE SETTINGS
    'performance_lookback_trades': 5,     # AGGRESSIVE: Shorter memory (was 20)
    'min_win_rate_strict': 0.1,          # AGGRESSIVE: Much lower (was 0.4)
    'good_win_rate_threshold': 0.4,      # AGGRESSIVE: Much lower (was 0.7)
    'execution_ratio_low': 0.01,         # AGGRESSIVE: Much lower (was 0.05)
    'execution_ratio_high': 0.8,         # AGGRESSIVE: Much higher (was 0.3)

    # AGGRESSIVE TIME-BASED SETTINGS (trade anytime)
    'market_hours_adjustment': 1.0,      # AGGRESSIVE: No penalty (was 1.05)
    'off_hours_adjustment': 1.0,         # AGGRESSIVE: No penalty (was 0.95)
    'weekend_adjustment': 1.0,           # AGGRESSIVE: No penalty (was 0.9)

    # AGGRESSIVE VOLATILITY SETTINGS
    'high_volatility_threshold': 0.05,   # AGGRESSIVE: Higher tolerance (was 0.03)
    'low_volatility_threshold': 0.005,   # AGGRESSIVE: Lower threshold (was 0.01)
    'volatility_confidence_adjustment': 0.05, # AGGRESSIVE: Less penalty (was 0.1)

    # AGGRESSIVE ADAPTATION SETTINGS
    'adaptation_enabled': True,
    'adaptation_frequency': 2,           # AGGRESSIVE: More frequent (was 5)
    'max_confluence_adjustment': 0.1,    # AGGRESSIVE: Smaller adjustments (was 0.2)
    'max_confidence_adjustment': 0.08,   # AGGRESSIVE: Smaller adjustments (was 0.15)
}

DYNAMIC_PARAMS_LOCK = Lock()
MODEL_UPDATE_LOCK = Lock()
TRADE_RESULTS_LOCK = Lock()
POSITION_STATE_LOCK = Lock()
CONFLUENCE_ADAPTATION_LOCK = Lock()

pid_file = os.path.join(DEPENDENCY_DIR, 'QUE_v1.pid')
os.makedirs(DEPENDENCY_DIR, exist_ok=True)
with open(pid_file, 'w') as f:
    f.write(str(os.getpid()))

def get_trade_learning_files(pair):
    pair_clean = pair.lower().replace('/', '').replace('-', '')
    return {
        'trade_results': os.path.join(DEPENDENCY_DIR, f'trade_results_{pair_clean}.json'),
        'model_performance': os.path.join(DEPENDENCY_DIR, f'model_performance_{pair_clean}.json'),
        'position_states': os.path.join(DEPENDENCY_DIR, f'position_states_{pair_clean}.json'),
        'learning_log': os.path.join(DEPENDENCY_DIR, f'trade_learning_{pair_clean}.log'),
        'confluence_adaptation': os.path.join(DEPENDENCY_DIR, f'confluence_adaptation_{pair_clean}.json')
    }

def get_confluence_adaptation_file(pair):
    pair_clean = pair.lower().replace('/', '').replace('-', '')
    return os.path.join(DEPENDENCY_DIR, f'confluence_adaptation_{pair_clean}.json')

def load_confluence_state(pair):
    confluence_file = get_confluence_adaptation_file(pair)
    if os.path.exists(confluence_file):
        try:
            with open(confluence_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    # AGGRESSIVE: Start with ultra-low bootstrap parameters
    return {
        'bootstrap_mode': True,
        'trades_completed': 0,
        'signals_generated': 0,
        'current_parameters': {
            'min_confluence': DYNAMIC_PARAMS['min_confluence'],
            'confidence_requirement': DYNAMIC_PARAMS['confidence_requirement'],
            'min_timeframes': DYNAMIC_PARAMS['min_timeframes'],
            'buy_threshold': DYNAMIC_PARAMS['buy_threshold'],
            'sell_threshold': DYNAMIC_PARAMS['sell_threshold']
        },
        'performance_history': [],
        'last_adaptation': None,
        'aggressive_mode': True,  # Mark as aggressive mode
        'signal_driven_mode': True  # NEW: Mark as signal-driven
    }

def save_confluence_state(pair, state):
    confluence_file = get_confluence_adaptation_file(pair)
    try:
        with CONFLUENCE_ADAPTATION_LOCK:
            # Ensure aggressive and signal-driven mode is marked
            state['aggressive_mode'] = True
            state['signal_driven_mode'] = True
            with open(confluence_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: Could not save confluence state: {e}")

# AGGRESSIVE DATA FETCHING CONFIG - Optimized for speed and volume
DATA_FETCHING_CONFIG = {
    'version': '2.9.0',
    'live_cache_age_seconds': 1800,      # AGGRESSIVE: Shorter cache (was 3600)
    'min_trades_per_ohlc_row': 1,        # AGGRESSIVE: Accept any trade data (was 3)
    'training_cache_age_hours': 12,      # AGGRESSIVE: Shorter cache (was 24)
    'max_fetch_retries': 5,              # AGGRESSIVE: More retries (was 3)
    'fetch_timeout_seconds': 15,         # AGGRESSIVE: Shorter timeout (was 30)
    'enable_multi_source': True,
    'primary_source': 'kraken',
    'fallback_sources': ['binance', 'coinbase'],
    'data_quality_checks': False,        # AGGRESSIVE: Disable quality checks for speed
    'anomaly_detection': False,          # AGGRESSIVE: Disable for speed
    'gap_filling': True,
    'adaptive_ohlc_generation': True,
    'adaptive_min_trades': True,
    'min_trades_base': 1,                # AGGRESSIVE: Accept minimal trades (was 3)
    'min_trades_volatility_factor': 1.0, # AGGRESSIVE: No volatility factor (was 1.5)
    'max_historical_days': None          # Uncapped training time
}

# AGGRESSIVE LIVE DATA CONFIG - Maximum refresh frequency
LIVE_DATA_CONFIG = {
    'refresh_interval_seconds': 30,      # AGGRESSIVE: Faster refresh (was 60)
    'lookback_hours': 12,                # AGGRESSIVE: Shorter lookback (was 24)
    'cache_management': True,
    'priority_timeframes': ['5m', '15m', '1h'],
    'background_refresh': True,
    'stale_data_threshold_minutes': 5,   # AGGRESSIVE: Shorter threshold (was 15)
    'emergency_fetch_timeout': 5         # AGGRESSIVE: Shorter timeout (was 10)
}

# AGGRESSIVE DATA QUALITY CONFIG - Minimal requirements
DATA_QUALITY_CONFIG = {
    'enabled': False,                    # AGGRESSIVE: Disabled for maximum trading
    'min_quality_score': 0.1,           # AGGRESSIVE: Ultra-low (was DYNAMIC_PARAMS['min_data_quality_score'])
    'quality_impact_on_confidence': False, # AGGRESSIVE: Disabled
    'source_preference_order': ['kraken', 'binance', 'coinbase', 'cache'],
    'freshness_penalty_hours': 24,       # AGGRESSIVE: More tolerant (was 6)
    'density_requirement': 0.5,          # AGGRESSIVE: Lower requirement (was 1.5)
    'anomaly_tolerance': 0.1,            # AGGRESSIVE: Higher tolerance (was 0.02)
    'gap_tolerance': 0.2,                # AGGRESSIVE: Higher tolerance (was 0.05)
    'track_source_performance': True,
    'adaptive_quality_thresholds': False # AGGRESSIVE: Disabled
}

# AGGRESSIVE BOOTSTRAP CONFIG - Instant bootstrap completion
BOOTSTRAP_CONFIG = {
    'enabled': True,
    'required_trades': 1,                # AGGRESSIVE: Only 1 trade needed (was 10)
    'no_time_limit': True,
    'quality_over_quantity': False,      # AGGRESSIVE: Quantity over quality
    'patient_learning': False,           # AGGRESSIVE: Impatient learning
    'philosophy': 'Signal-driven trading, learn fast, let confluence determine exits',  # NEW philosophy
    'initial_parameters': {
        'min_confluence': DYNAMIC_PARAMS['min_confluence'],
        'confidence_requirement': DYNAMIC_PARAMS['confidence_requirement'],
        'min_timeframes': DYNAMIC_PARAMS['min_timeframes'],
        'buy_threshold': DYNAMIC_PARAMS['buy_threshold'],
        'sell_threshold': DYNAMIC_PARAMS['sell_threshold']
    },
    'target_parameters': {
        'min_confluence': DYNAMIC_PARAMS['target_min_confluence'],
        'confidence_requirement': DYNAMIC_PARAMS['target_confidence_requirement'],
        'min_timeframes': DYNAMIC_PARAMS['target_min_timeframes'],
        'buy_threshold': 0.98,             # AGGRESSIVE targets
        'sell_threshold': 1.02
    },
    'progress_tracking': True,
    'interpolation_method': 'linear',     # AGGRESSIVE: Linear for fast progression
    'fast_learning_mode': True,          # AGGRESSIVE: Fast learning enabled
    'early_adaptation': True
}

# SIGNAL-DRIVEN PERFORMANCE MONITORING - Minimal oversight, let signals work
PERFORMANCE_MONITORING = {
    'enabled': True,
    'check_frequency': 1,                # AGGRESSIVE: Check every trade (was 3)
    'min_trades_for_analysis': 2,        # AGGRESSIVE: Minimal trades needed (was 5)
    'win_rate_threshold_low': 0.1,       # AGGRESSIVE: Very low bar (was 0.25)
    'win_rate_threshold_high': 0.9,      # AGGRESSIVE: High bar (was 0.65)
    'execution_ratio_threshold_low': 0.01, # AGGRESSIVE: Very low (was 0.03)
    'execution_ratio_threshold_high': 0.9,  # AGGRESSIVE: Very high (was 0.4)
    'adaptation_sensitivity': 0.05,      # AGGRESSIVE: Less sensitive (was 0.15)
    'max_adjustment_per_cycle': 0.1,     # AGGRESSIVE: Smaller adjustments (was 0.2)
    'rollback_on_poor_performance': False, # AGGRESSIVE: No rollbacks
    'preserve_good_parameters': False,   # AGGRESSIVE: Always adapt
    'fast_adaptation_mode': True,        # AGGRESSIVE: Fast adaptation
    'emergency_relaxation': False,       # No emergency relaxation
    'signal_driven_monitoring': True     # NEW: Monitor signal-driven performance
}

RESOURCE_MONITORING = {
    'enabled': True,
    'memory_check_frequency': 10,
    'max_memory_mb': 2048,
    'cleanup_frequency': 20,
    'log_resource_usage': True,
    'auto_cleanup_on_high_memory': True,
    'process_monitoring': True,
    'disk_space_monitoring': True,
    'min_disk_space_gb': 1.0
}

# AGGRESSIVE DYNAMIC INTERVALS - Minimum wait times
DYNAMIC_INTERVALS = {
    'enabled': True,
    'base_interval_seconds': 60,         # AGGRESSIVE: Faster base (was 300)
    'patient_interval_seconds': 60,      # AGGRESSIVE: No patience (was 600)
    'max_interval_seconds': 300,         # AGGRESSIVE: Much shorter max (was 1800)
    'min_interval_seconds': 15,          # AGGRESSIVE: Very short min (was 60)
    'extend_on_no_signals': False,       # AGGRESSIVE: Don't extend
    'adaptive_intervals': False          # AGGRESSIVE: Fixed intervals
}

EMERGENCY_CONFIG = {
    'enabled': False,                    # AGGRESSIVE: Disabled
    'manual_only': True,
    'no_time_pressure': True,
    'patient_mode': False                # AGGRESSIVE: No patience
}

CACHE_PROTECTION = {
    'never_delete_in_live_mode': True,
    'preserve_trained_models': True,
    'incremental_updates_only': True,
    'backup_before_training': False,
    'protect_confluence_data': True
}

MODEL_CONFIG = {
    'save_after_training': True,
    'load_existing_models': True,
    'model_file_pattern': 'xgb_model_{pair}_{timeframe}.pkl',
    'feature_file_pattern': 'features_{pair}_{timeframe}_training.csv.gz',
    'performance_tracking': True,
    'confluence_tracking': True
}

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available - memory monitoring disabled")

# FINAL SIGNAL-DRIVEN OVERRIDE - REMOVE ALL REMAINING BARRIERS
print("SIGNAL-DRIVEN TRADING MODE WITH SHADOW TRADING ACTIVATED")
print("Target: Let ML confluence determine all entry and exit timing")
print("Philosophy: Signals decide profits, not arbitrary percentage caps")
print("Enhancement: Intelligent stop-losses based on confluence predictions")
print(f"Pairs configured: {PAIRS}")
print(f"Primary pair: {PAIR}")

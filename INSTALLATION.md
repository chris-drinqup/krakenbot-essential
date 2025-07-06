# Crypto Trading Bot Installation Guide

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- pip package manager

### 2. External Dependencies

#### Required External Binary
- **DP Trading Tool**: `/home/code/dp`
  - This is a custom trading execution binary
  - Must be installed separately and accessible at `/home/code/dp`
  - Contact the developer for access to this tool

#### API Keys Setup

#### Required Directories
- `)

        # Ensure the directory exists
        os.makedirs(DEPENDENCY_DIR, exist_ok=True)

        with open(param_file, ` - Will be created automatically
- `)
                    with open(report_file, ` - Will be created automatically
- `dependencies_v1` - Will be created automatically
- `)
                
                logger.info(f` - Will be created automatically
- `)
                    
                    # Fetch new trades
                    new_trades_result = dynamic_fetch_trades(
                        pair=pair,
                        cache_file=trades_cache_file,
                        since=since,
                        live_mode=True,
                        source=` - Will be created automatically
- `)
                    new_ohlc = trades_to_ohlc(new_trades_filtered, timeframe, new_ohlc_file)
                    
                    if new_ohlc.empty:
                        logger.warning(f` - Will be created automatically
- `)
            
            if os.path.exists(cache_file):
                last_timestamp = get_last_cache_timestamp(cache_file)
                
                if last_timestamp:
                    if last_timestamp.tz is None:
                        last_timestamp = last_timestamp.tz_localize(` - Will be created automatically
- `)
        self.performance_file = os.path.join(dependency_dir, f` - Will be created automatically
- `)
        self.weight_optimization_file = os.path.join(dependency_dir, f` - Will be created automatically
- `)

        # Market-aware base weights (logical hierarchy) - PRESERVED from original
        self.base_weights = {
            ` - Will be created automatically
- `)
        
        if not os.path.exists(trades_cache_file):
            logger.error(f` - Will be created automatically
- `)
                
                # Check if OHLC already exists and is recent
                if os.path.exists(ohlc_cache_file):
                    try:
                        existing_ohlc = pd.read_csv(ohlc_cache_file, parse_dates=[` - Will be created automatically
- `)
            
            if os.path.exists(ohlc_cache_file):
                try:
                    ohlc_df = pd.read_csv(ohlc_cache_file, nrows=5)  # Just check if readable
                    if not ohlc_df.empty:
                        existing_timeframes.append(timeframe)
                    else:
                        missing_timeframes.append(timeframe)
                except:
                    missing_timeframes.append(timeframe)
            else:
                missing_timeframes.append(timeframe)
                
        logger.info(f` - Will be created automatically
- `)
os.makedirs(DEPENDENCY_DIR, exist_ok=True)
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter(` - Will be created automatically
- `)
debug_handler = RotatingFileHandler(debug_file, maxBytes=10*1024*1024, backupCount=5)
debug_handler.setFormatter(logging.Formatter(` - Will be created automatically
- `)
    try:
        os.makedirs(DEPENDENCY_DIR, exist_ok=True)
        entry = [f` - Will be created automatically
- `,
            file_name=` - Will be created automatically
- `)
                            combined_trades_copy.to_csv(main_cache, index=False)
                            logger.info(f` - Will be created automatically
- `)
                
                # Backup existing cache
                if os.path.exists(main_cache):
                    backup_path = f` - Will be created automatically
- `)
                ohlc_cache_file = os.path.join(dependency_dir, f` - Will be created automatically
- `)
        try:
            model_data = {
                ` - Will be created automatically
- `)

    if not os.path.exists(model_path):
        return None, [], {}, {}

    try:
        with open(model_path, ` - Will be created automatically
- `)

    def get_recent_performance(self, days=7):
        ` - Will be created automatically
- `)

        performance_data = {
            ` - Will be created automatically
- `)
        self.min_trades_for_adaptation = 20
        self.confidence_threshold = 0.75  # Require 75% confidence before adapting
        self.adaptation_history = []
        self.current_adaptations = {}
        self.load_adaptation_state()
    
    def load_adaptation_state(self):
        ` - Will be created automatically
- `)
        self.analysis_file = os.path.join(DEPENDENCY_DIR, f` - Will be created automatically
- `)

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

        logger.info(f` - Will be created automatically
- `)
        ohlc_cache_file = os.path.join(DEPENDENCY_DIR, f` - Will be created automatically
- `
    PAIR = ` - Will be created automatically
- `)
        self.performance_file = os.path.join(DEPENDENCY_DIR, f` - Will be created automatically
- `)
        self.model = None
        self.loaded = False
        self.creation_time = datetime.now()
        
        # Enhanced ML parameters
        self.feature_weights = {
            ` - Will be created automatically
- `)
            
            # Create CSV if it doesn` - Will be created automatically
- `)

# ENHANCED: Multi-pair support with backward compatibility
# Default pairs for shadow trading and multi-pair support
DEFAULT_PAIRS = [` - Will be created automatically
- `)
MODEL_PERFORMANCE_FILE = os.path.join(DEPENDENCY_DIR, f` - Will be created automatically
- `)

# SIGNAL-DRIVEN TRADING PARAMETERS - Let ML confluence determine all exits
DYNAMIC_PARAMS = {
    # AGGRESSIVE CONFLUENCE SETTINGS
    ` - Will be created automatically
- `)
os.makedirs(DEPENDENCY_DIR, exist_ok=True)
with open(pid_file, ` - Will be created automatically
- `),
        ` - Will be created automatically
- `)
    }

def get_confluence_adaptation_file(pair):
    pair_clean = pair.lower().replace(` - Will be created automatically
- `)

def load_confluence_state(pair):
    confluence_file = get_confluence_adaptation_file(pair)
    if os.path.exists(confluence_file):
        try:
            with open(confluence_file, ` - Will be created automatically

## Installation Steps

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd crypto-trading-bot
```

### 2. Create Virtual Environment
```bash
python3 -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup External Dependencies
- Install the DP trading tool at `/home/code/dp`
- Setup API key directories
- Ensure `gobbler.sh` is executable: `chmod +x gobbler.sh`

### 5. Configuration
- Edit `config.py` with your trading preferences
- Set up your exchange API credentials
- Configure trading pairs and parameters

### 6. Test Installation
```bash
# Dry run test
python main.py --pair ADAUSDT --trainingtime 30 --dry_run --verbose

# Check system status
python check_main_version.py
```

## Usage

### Basic Commands
```bash
# Live trading
python main.py --pair ADAUSDT --trainingtime 150 --live --verbose

# Backtest mode
python main.py --pair BTCUSDT --trainingtime 30 --backtest --verbose

# Multiple pairs
python main.py --pairs ADAUSDT,BTCUSDT,ETHUSDT --live
```

### Configuration Options
- `--pair`: Single trading pair
- `--pairs`: Multiple trading pairs (comma-separated)
- `--trainingtime`: Days of historical data for training
- `--live`: Enable live trading
- `--dry_run`: Simulate trades without execution
- `--verbose`: Enable detailed logging

## Important Notes

1. **Risk Warning**: This is trading software that can lose money. Use at your own risk.
2. **External Binary**: The bot requires the `/home/code/dp` binary which is not included.
3. **API Keys**: Secure your API keys and never commit them to version control.
4. **Testing**: Always test with `--dry_run` first before live trading.

## Troubleshooting

- Check `dependencies_v1/krakenbot.log` for detailed logs
- Ensure all required directories exist
- Verify API key permissions
- Test external binary access: `/home/code/dp --help`

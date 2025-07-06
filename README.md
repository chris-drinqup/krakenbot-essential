# KrakenBot - Advanced Crypto Trading System

## 🚀 Features
- **Multi-timeframe Analysis**: 5m, 15m, 30m, 1h, 4h, 6h, 1d
- **ML-Powered Confluence**: Dynamic threshold optimization
- **Bootstrap Learning**: Progressive threshold adjustment
- **Real Balance Integration**: Live exchange balance checking
- **Risk Management**: Adaptive stops, position sizing
- **Advanced Technical Analysis**: 33+ indicators per timeframe

## 📋 Prerequisites
- Python 3.8+
- TA-Lib (technical analysis library)
- Exchange API access (configured in config.py)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd krakenbot
```

### 2. Create Virtual Environment
```bash
python3 -m venv myenv
source myenv/bin/activate  # Linux/Mac
# or
myenv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install TA-Lib
**Ubuntu/Debian:**
```bash
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

**macOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

**Windows:**
Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

### 5. Configure Settings
```bash
cp config_template.py config.py
# Edit config.py with your API keys and settings
```

### 6. Make Scripts Executable
```bash
chmod +x dependencies_v1/gobbler.sh
```

## 🎯 Usage

### Training Mode
```bash
python3 main.py --trainingtime 200 --verbose --harmonics --runalltimes --pair ADAUSDT
```

### Live Trading
```bash
python3 main.py --live --pair ADAUSDT --trainingtime 200 --verbose --harmonics --runalltimes
```

### Paper Trading
```bash
python3 main.py --live --dry-run --pair ADAUSDT
```

## 🔧 Key Components

### Core Files
- `main.py` - Main application entry point
- `enhanced_trading.py` - Advanced trading engine with ML confluence
- `dynamic_confluence_ml.py` - ML-powered threshold optimization
- `config.py` - Configuration and API settings
- `logging_setup.py` - Comprehensive logging system

### Dependencies
- `gobbler.sh` - Exchange interface script (CRITICAL)
- `requirements.txt` - Python dependencies

## 📊 Trading Modes

### Bootstrap Mode (First 10 trades)
- Relaxed confluence threshold (0.35)
- Learning from market behavior
- Progressive threshold tightening

### Regular Mode (After bootstrap)
- ML-optimized thresholds
- Adaptive to market conditions
- Continuous learning and improvement

## ⚠️ Important Notes

1. **ALWAYS test in paper trading mode first**
2. **Ensure gobbler.sh has proper exchange API configuration**
3. **Monitor logs for system health**
4. **Start with small position sizes**
5. **Keep API keys secure**

## 📈 Performance Tracking
- Enhanced trade logging in `dependencies_v1/`
- ML confluence decisions logged
- Bootstrap progress tracking
- Performance metrics and analytics

## 🛡️ Risk Management
- Dynamic position sizing based on confidence
- Adaptive stop-loss and take-profit
- Market regime detection
- Volume confirmation requirements

## 🆘 Troubleshooting

### Common Issues
1. **TA-Lib installation fails**: Follow platform-specific installation
2. **API connection errors**: Check config.py settings
3. **Missing gobbler.sh**: Ensure script is present and executable
4. **Import errors**: Verify all requirements installed

### Support
Check logs in `dependencies_v1/krakenbot.log` for detailed error information.

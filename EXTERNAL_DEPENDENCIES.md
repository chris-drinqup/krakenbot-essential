# External Dependencies and Setup

## Included Binary
- **File**: `dp` (included in repository)
- **Purpose**: Trading execution tool for Kraken exchange
- **Setup**: Automatically executable after cloning

Edit file paths for keys and put in your own api key for trading on Kraken requires two lines public on top and private on bottom


/home/chris/keys/
├── funboy      # API key file for user 'funboy'
├── mason       # API key file for user 'mason'
├── josh        # API key file for user 'josh'
└── rick        # API key file for user 'rick'

## Log Directory Structure
/home/chris/dp_logs/
├── funboy.log, mason.log, josh.log, rick.log   # Trading logs

## Additional Python Packages
Not included in git - users install separately:
- pandas-ta (technical analysis)
- yfinance (market data)
- ccxt (exchange integration)  
- optuna (optimization)
- shap (ML explainability)
- matplotlib, seaborn, plotly (visualization)

## Setup Instructions
1. Clone repository: `git clone https://github.com/chris-drinqup/krakenbot.git`
2. Install Python packages: `pip install -r requirements.txt`
3. Install additional packages: `pip install pandas-ta yfinance ccxt optuna shap matplotlib seaborn plotly psutil`
4. Create API key directories with your exchange keys
5. Make sure `dp` and `gobbler.sh` are executable (should be automatic)
6. Test with: `python main.py --dry_run --verbose`

See INSTALLATION.md for complete setup instructions.
EOF

# 3. Add both files to git
git add dp EXTERNAL_DEPENDENCIES.md

# 4. Commit everything
git commit -m "🚀 Complete Self-Contained Crypto Trading Bot

✅ FULLY SELF-CONTAINED:
- All Python modules included (40+ files)
- dp trading binary included (no external setup needed)
- gobbler.sh execution script included
- Complete documentation and installation guides

🤖 FEATURES:
- Multi-timeframe ML confluence trading
- Dynamic position sizing and risk management
- Market regime detection and adaptive strategies
- Signal-driven exits with intelligent stop-losses
- Multi-user trading capabilities

📦 READY TO USE:
- Clone and install Python packages
- Set up API keys
- Start trading immediately
- No external binaries to install"

# 5. Push to GitHub
git push origin production-deployment-20250606-104657

echo "✅ SELF-CONTAINED DEPLOYMENT COMPLETE!"
echo "🌐 Repository: https://github.com/chris-drinqup/krakenbot.git"
echo "📋 Users can now clone and use immediately (just need Python packages + API keys)"

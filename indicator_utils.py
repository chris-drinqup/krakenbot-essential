# Version: 1.4 - CRITICAL FIX for file path creation bug
# Fixed the save_parameters function that was creating invalid file paths

import pandas as pd
import numpy as np
import os
import json
from config import args, DEPENDENCY_DIR, PAIR
from logging_setup import logger, debug_logger
import traceback

def validate_data(df, timeframe, min_periods=26):
    """Validate DataFrame for indicator calculations"""
    if df is None or df.empty:
        return False, "DataFrame is empty"

    required_cols = [f'open_{timeframe}', f'high_{timeframe}', f'low_{timeframe}',
                    f'close_{timeframe}', f'volume_{timeframe}']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns: {missing_cols}"

    if len(df) < min_periods:
        return False, f"Insufficient data: {len(df)} rows, need {min_periods}"

    nan_cols = []
    nan_counts = {}
    for col in required_cols:
        series = pd.to_numeric(df[col], errors='coerce')
        nan_counts[col] = series.isna().sum()
        if series.isna().all():
            nan_cols.append(col)
        if series.std() < 1e-4 and timeframe != '1w':
            logger.warning(f"Column {col} has low variance: {series.std():.8f}")
        valid_count = series.dropna().shape[0]
        if valid_count < min_periods and timeframe != '1w':
            return False, f"Column {col} has insufficient valid data: {valid_count} rows, need {min_periods}"

    if timeframe == '1w':
        if nan_cols:
            logger.warning(f"NaN columns for 1w: {nan_cols}, counts: {nan_counts}")
            return True, "1w data contains NaNs, proceeding with warning"
    else:
        if nan_cols:
            logger.error(f"Columns with all NaN values: {nan_cols}, counts: {nan_counts}")
            return False, f"Columns with all NaN values: {nan_cols}"

    logger.debug(f"Validation for {timeframe}: NaN columns={nan_cols}, counts={nan_counts}, rows={len(df)}")
    return True, "Data validated successfully"

def safe_indicator_calculation(func, df, *args, **kwargs):
    """Safely calculate indicators with comprehensive error handling"""
    try:
        result = func(df, *args, **kwargs)
        if result is None:
            logger.warning(f"{func.__name__} returned None for {args}")
            if func.__name__ in ('macd', 'volume_weighted_macd', 'bollinger_bands', 'vortex_indicator',
                               'percentage_price_oscillator', 'stochastic_oscillator', 'keltner_channels'):
                return pd.Series(0, index=df.index), pd.Series(0, index=df.index)
            elif func.__name__ == 'adx':
                return pd.Series(0, index=df.index), pd.Series(0, index=df.index), pd.Series(0, index=df.index)
            return pd.Series(0, index=df.index)
        return result
    except ValueError as ve:
        logger.error(f"Value error in {func.__name__}: {str(ve)}")
    except TypeError as te:
        logger.error(f"Type error in {func.__name__}: {str(te)}")
    except KeyError as ke:
        logger.error(f"Key error in {func.__name__}: {str(ke)}")
    except Exception as e:
        logger.error(f"General error in {func.__name__}: {str(e)}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")

    if func.__name__ in ('macd', 'volume_weighted_macd', 'bollinger_bands', 'vortex_indicator',
                        'percentage_price_oscillator', 'stochastic_oscillator', 'keltner_channels'):
        return pd.Series(0, index=df.index), pd.Series(0, index=df.index)
    elif func.__name__ == 'adx':
        return pd.Series(0, index=df.index), pd.Series(0, index=df.index), pd.Series(0, index=df.index)
    return pd.Series(0, index=df.index)

def save_parameters(params, pair, timeframe):
    """CRITICAL FIX: Save optimized indicator parameters to a JSON file with proper file path handling."""
    try:
        # CRITICAL FIX: Clean the pair name to remove invalid characters for file paths
        pair_clean = pair.lower().replace('/', '').replace('-', '')
        param_file = os.path.join(DEPENDENCY_DIR, f"params_{pair_clean}_{timeframe}.json")

        # Ensure the directory exists
        os.makedirs(DEPENDENCY_DIR, exist_ok=True)

        with open(param_file, 'w') as f:
            json.dump(params, f, indent=2)
        logger.info(f"Saved parameters to {param_file}")
    except Exception as e:
        logger.error(f"Failed to save parameters to {param_file}: {str(e)}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")

def calculate_non_zero_ratio(series):
    """Calculate the proportion of non-zero values in a series."""
    try:
        if series.empty:
            logger.warning("Empty series provided to calculate_non_zero_ratio")
            return 0.0

        series = pd.to_numeric(series, errors='coerce')
        non_zero_count = (series != 0).sum()
        total_count = series.dropna().shape[0]

        if total_count == 0:
            logger.warning("No valid data in series for non_zero_ratio calculation")
            return 0.0

        ratio = non_zero_count / total_count
        logger.debug(f"Non-zero ratio for series: {ratio:.4f} (non_zero={non_zero_count}, total={total_count})")
        return ratio

    except Exception as e:
        logger.error(f"Error in calculate_non_zero_ratio: {str(e)}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")
        return 0.0

def get_default_parameters(timeframe):
    """Get default parameters for indicators"""
    return {
        'rsi_period': 14, 'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
        'bb_period': 20, 'atr_period': 14, 'adx_period': 14, 'roc_period': 10,
        'cci_period': 20, 'ko_fast': 34, 'ko_slow': 55, 'vi_period': 14,
        'stc_fast': 23, 'stc_slow': 50, 'uo_fast': 7, 'uo_medium': 14,
        'uo_slow': 28, 'stoch_k_period': 14, 'stoch_d_period': 3, 'stoch_smooth': 3,
        'willr_period': 14
    }

def detect_candlestick_patterns(df, timeframe):
    """Detect basic candlestick patterns"""
    logger.info(f"Detecting candlestick patterns for {timeframe}")
    try:
        required_cols = [f'open_{timeframe}', f'close_{timeframe}']
        if not all(col in df.columns for col in required_cols):
            logger.warning(f"Missing required columns for pattern detection in {timeframe}")
            return pd.DataFrame(index=df.index)

        open_prices = pd.to_numeric(df[f'open_{timeframe}'], errors='coerce')
        close_prices = pd.to_numeric(df[f'close_{timeframe}'], errors='coerce')

        patterns = pd.DataFrame(index=df.index)

        bull_engulfing = pd.Series(False, index=df.index)
        bear_engulfing = pd.Series(False, index=df.index)

        for i in range(1, len(df)):
            # Bull Engulfing
            if (close_prices.iloc[i-1] < open_prices.iloc[i-1] and
                close_prices.iloc[i] > open_prices.iloc[i] and
                open_prices.iloc[i] <= close_prices.iloc[i-1] and
                close_prices.iloc[i] >= open_prices.iloc[i-1]):
                bull_engulfing.iloc[i] = True

            # Bear Engulfing
            if (close_prices.iloc[i-1] > open_prices.iloc[i-1] and
                close_prices.iloc[i] < open_prices.iloc[i] and
                open_prices.iloc[i] >= close_prices.iloc[i-1] and
                close_prices.iloc[i] <= open_prices.iloc[i-1]):
                bear_engulfing.iloc[i] = True

        patterns[f'Bull_Engulfing_{timeframe}'] = bull_engulfing
        patterns[f'Bear_Engulfing_{timeframe}'] = bear_engulfing

        logger.debug(f"Candlestick patterns for {timeframe}: "
                    f"bull_engulfing={bull_engulfing.sum()}, bear_engulfing={bear_engulfing.sum()}")

        return patterns

    except Exception as e:
        logger.error(f"Error in detect_candlestick_patterns for {timeframe}: {str(e)}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")
        return pd.DataFrame(index=df.index)

def log_indicator_statistics(indicators, timeframe):
    """Log statistics about calculated indicators"""
    stats = {}
    for col, series in indicators.items():
        try:
            if series.dtype == bool:
                stats[col] = {
                    'non_zero_ratio': series.mean(),
                    'nan_count': series.isna().sum(),
                }
            else:
                valid_series = series.dropna()
                stats[col] = {
                    'mean': valid_series.mean() if len(valid_series) > 0 else np.nan,
                    'std': valid_series.std() if len(valid_series) > 0 else np.nan,
                    'non_zero_ratio': (series != 0).mean(),
                    'nan_count': series.isna().sum(),
                }
            if stats[col]['non_zero_ratio'] < 0.5 and not col.startswith(('Bull_Engulfing', 'Bear_Engulfing')):
                logger.warning(f"Indicator {col} is sparse: non-zero ratio={stats[col]['non_zero_ratio']:.2f}")
        except Exception as e:
            logger.error(f"Error calculating stats for {col}: {str(e)}")

    logger.debug(f"Indicator stats for {timeframe}: processed {len(stats)} indicators")

def select_adaptive_parameters(df, timeframe):
    """Select adaptive parameters based on market conditions"""
    logger.info(f"Selecting adaptive parameters for {timeframe}")
    try:
        if f'close_{timeframe}' not in df.columns:
            logger.warning(f"Missing close_{timeframe}, using default parameters")
            return get_default_parameters(timeframe)

        close = pd.to_numeric(df[f'close_{timeframe}'], errors='coerce')
        returns = close.pct_change().dropna()
        volatility = returns.std() * 100

        market_type = ("low_volatility" if volatility < 0.5 else
                      "high_volatility" if volatility > 1.5 else
                      "normal_volatility")

        logger.info(f"Detected market type for {timeframe}: {market_type} (volatility: {volatility:.2f}%)")

        params = get_default_parameters(timeframe)

        if market_type == "low_volatility":
            params.update({
                'rsi_period': params['rsi_period'] + 2,
                'macd_slow': params['macd_slow'] + 4,
                'bb_period': params['bb_period'] + 5,
            })
        elif market_type == "high_volatility":
            params.update({
                'rsi_period': max(params['rsi_period'] - 2, 5),
                'macd_fast': max(params['macd_fast'] - 2, 6),
                'macd_slow': max(params['macd_slow'] - 4, 16),
                'bb_period': max(params['bb_period'] - 5, 10),
            })

        return params

    except Exception as e:
        logger.error(f"Error in select_adaptive_parameters: {str(e)}")
        if args.verbose:
            debug_logger.debug(f"Detailed error: {traceback.format_exc()}")
        return get_default_parameters(timeframe)

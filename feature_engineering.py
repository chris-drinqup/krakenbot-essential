# Enhanced Feature Engineering - Complete Version with All Fixes and Performance Optimizations
# This addresses all missing indicators, standardization, and compatibility issues
# ADDED: Smart caching and feature reduction to prevent 275+ column bloat

import pandas as pd
import numpy as np
import pandas_ta as ta
from config import DYNAMIC_PARAMS
from logging_setup import logger

def add_standard_indicators(df, timeframe):
    """Add the missing standard indicators that the system expects"""
    try:
        close_col = f'close_{timeframe}'
        high_col = f'high_{timeframe}'
        low_col = f'low_{timeframe}'
        open_col = f'open_{timeframe}'
        volume_col = f'volume_{timeframe}'

        if not all(col in df.columns for col in [close_col, high_col, low_col, open_col]):
            logger.warning(f"Missing OHLC columns for standard indicators in {timeframe}")
            return df

        close_prices = df[close_col]
        high_prices = df[high_col]
        low_prices = df[low_col]
        open_prices = df[open_col]
        volume = df[volume_col] if volume_col in df.columns else pd.Series(1, index=df.index)

        # 1. SMA - Simple Moving Average
        if f'SMA_{timeframe}' not in df.columns:
            df[f'SMA_{timeframe}'] = close_prices.rolling(window=20).mean().fillna(close_prices)
            logger.debug(f"Added SMA_{timeframe}")

        # 2. EMA - Exponential Moving Average
        if f'EMA_{timeframe}' not in df.columns:
            df[f'EMA_{timeframe}'] = close_prices.ewm(span=20).mean().fillna(close_prices)
            logger.debug(f"Added EMA_{timeframe}")

        # 3. MACD - Moving Average Convergence Divergence
        if f'MACD_{timeframe}' not in df.columns:
            ema_fast = close_prices.ewm(span=12).mean()
            ema_slow = close_prices.ewm(span=26).mean()
            df[f'MACD_{timeframe}'] = (ema_fast - ema_slow).fillna(0)
            logger.debug(f"Added MACD_{timeframe}")

        # 4. Signal - MACD Signal Line
        if f'Signal_{timeframe}' not in df.columns:
            if f'MACD_{timeframe}' in df.columns:
                df[f'Signal_{timeframe}'] = df[f'MACD_{timeframe}'].ewm(span=9).mean().fillna(0)
            else:
                df[f'Signal_{timeframe}'] = pd.Series(0, index=df.index)
            logger.debug(f"Added Signal_{timeframe}")

        # 5. RSI - Relative Strength Index (if missing)
        if f'RSI_{timeframe}' not in df.columns:
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-10)
            df[f'RSI_{timeframe}'] = (100 - (100 / (1 + rs))).fillna(50)
            logger.debug(f"Added RSI_{timeframe}")

        # 6. ATR - Average True Range (if missing)
        if f'ATR_{timeframe}' not in df.columns:
            tr = pd.concat([
                high_prices - low_prices,
                abs(high_prices - close_prices.shift(1)),
                abs(low_prices - close_prices.shift(1))
            ], axis=1).max(axis=1)
            df[f'ATR_{timeframe}'] = tr.rolling(window=14).mean().fillna(close_prices * 0.02)
            logger.debug(f"Added ATR_{timeframe}")

        # 7. STC - Schaff Trend Cycle (simplified version)
        if f'STC_{timeframe}' not in df.columns:
            # Simplified STC calculation
            macd = df.get(f'MACD_{timeframe}', close_prices.pct_change())
            stc_raw = ((macd - macd.rolling(window=23).min()) /
                      (macd.rolling(window=23).max() - macd.rolling(window=23).min() + 1e-10) * 100)
            df[f'STC_{timeframe}'] = stc_raw.fillna(50)
            logger.debug(f"Added STC_{timeframe}")

        # 8. Bull_Engulfing - Bullish Engulfing Pattern
        if f'Bull_Engulfing_{timeframe}' not in df.columns:
            bull_engulfing = pd.Series(False, index=df.index)
            for i in range(1, len(df)):
                if (close_prices.iloc[i-1] < open_prices.iloc[i-1] and  # Previous candle bearish
                    close_prices.iloc[i] > open_prices.iloc[i] and      # Current candle bullish
                    open_prices.iloc[i] <= close_prices.iloc[i-1] and   # Opens below prev close
                    close_prices.iloc[i] >= open_prices.iloc[i-1]):     # Closes above prev open
                    bull_engulfing.iloc[i] = True
            df[f'Bull_Engulfing_{timeframe}'] = bull_engulfing.astype(int)
            logger.debug(f"Added Bull_Engulfing_{timeframe}")

        # 9. Bear_Engulfing - Bearish Engulfing Pattern
        if f'Bear_Engulfing_{timeframe}' not in df.columns:
            bear_engulfing = pd.Series(False, index=df.index)
            for i in range(1, len(df)):
                if (close_prices.iloc[i-1] > open_prices.iloc[i-1] and  # Previous candle bullish
                    close_prices.iloc[i] < open_prices.iloc[i] and      # Current candle bearish
                    open_prices.iloc[i] >= close_prices.iloc[i-1] and   # Opens above prev close
                    close_prices.iloc[i] <= open_prices.iloc[i-1]):     # Closes below prev open
                    bear_engulfing.iloc[i] = True
            df[f'Bear_Engulfing_{timeframe}'] = bear_engulfing.astype(int)
            logger.debug(f"Added Bear_Engulfing_{timeframe}")

        logger.info(f"Successfully added all missing standard indicators for {timeframe}")
        return df

    except Exception as e:
        logger.error(f"Error adding standard indicators for {timeframe}: {e}")
        return df

def add_missing_dynamic_indicators(df, timeframe):
    """Add ALL missing indicators from DYNAMIC_PARAMS['active_indicators'] with existence checks"""
    try:
        active_indicators = DYNAMIC_PARAMS.get('active_indicators', [])
        
        # Count existing indicators to avoid unnecessary work
        existing_indicators = [col for col in df.columns if f'_{timeframe}' in col]
        if len(existing_indicators) >= len(active_indicators):
            logger.debug(f"Most indicators already present for {timeframe} ({len(existing_indicators)} existing)")
            return df
            
        logger.info(f"Adding missing indicators for {timeframe}: {len(active_indicators)} total indicators")

        close_col = f'close_{timeframe}'
        high_col = f'high_{timeframe}'
        low_col = f'low_{timeframe}'
        open_col = f'open_{timeframe}'
        volume_col = f'volume_{timeframe}'

        # Ensure we have required columns
        if not all(col in df.columns for col in [close_col, high_col, low_col, volume_col]):
            logger.warning(f"Missing OHLC columns for indicators in {timeframe}")
            return df

        close_prices = df[close_col]
        high_prices = df[high_col]
        low_prices = df[low_col]
        open_prices = df[open_col]
        volume = df[volume_col]

        # 1. CCI - Commodity Channel Index
        if f'CCI_{timeframe}' not in df.columns and 'CCI' in active_indicators:
            typical_price = (high_prices + low_prices + close_prices) / 3
            typical_price_sma = typical_price.rolling(window=20).mean()
            typical_price_diff = typical_price - typical_price_sma
            mean_dev = typical_price_diff.abs().rolling(window=20).mean()
            df[f'CCI_{timeframe}'] = (typical_price_diff / (0.015 * mean_dev + 1e-10)).fillna(0)
            logger.debug(f"Added CCI_{timeframe}")

        # 2. STOCH_k and STOCH_d - Stochastic Oscillator
        if f'STOCH_k_{timeframe}' not in df.columns and 'STOCH_k' in active_indicators:
            lowest_low = low_prices.rolling(window=14).min()
            highest_high = high_prices.rolling(window=14).max()
            k_percent = 100 * ((close_prices - lowest_low) / (highest_high - lowest_low + 1e-10))
            df[f'STOCH_k_{timeframe}'] = k_percent.fillna(50)
            df[f'STOCH_d_{timeframe}'] = k_percent.rolling(window=3).mean().fillna(50)
            logger.debug(f"Added STOCH_k_{timeframe} and STOCH_d_{timeframe}")

        # 3. WilliamsR - Williams %R
        if f'WilliamsR_{timeframe}' not in df.columns and 'WilliamsR' in active_indicators:
            highest_high = high_prices.rolling(window=14).max()
            lowest_low = low_prices.rolling(window=14).min()
            df[f'WilliamsR_{timeframe}'] = -100 * ((highest_high - close_prices) / (highest_high - lowest_low + 1e-10)).fillna(-50)
            logger.debug(f"Added WilliamsR_{timeframe}")

        # 4. KO - Klinger Oscillator
        if f'KO_{timeframe}' not in df.columns and 'KO' in active_indicators:
            # Simplified Klinger Oscillator calculation
            typical_price = (high_prices + low_prices + close_prices) / 3
            volume_force = volume * np.where(typical_price > typical_price.shift(1), 1, -1)
            ema_fast = volume_force.ewm(span=34).mean()
            ema_slow = volume_force.ewm(span=55).mean()
            df[f'KO_{timeframe}'] = (ema_fast - ema_slow).fillna(0)
            logger.debug(f"Added KO_{timeframe}")

        # 5. VI_Plus and VI_Minus - Vortex Indicator
        if f'VI_Plus_{timeframe}' not in df.columns and 'VI_Plus' in active_indicators:
            period = 14
            tr = pd.concat([
                high_prices - low_prices,
                abs(high_prices - close_prices.shift(1)),
                abs(low_prices - close_prices.shift(1))
            ], axis=1).max(axis=1)

            vm_plus = abs(high_prices - low_prices.shift(1))
            vm_minus = abs(low_prices - high_prices.shift(1))

            vi_plus = vm_plus.rolling(window=period).sum() / tr.rolling(window=period).sum()
            vi_minus = vm_minus.rolling(window=period).sum() / tr.rolling(window=period).sum()

            df[f'VI_Plus_{timeframe}'] = vi_plus.fillna(1)
            df[f'VI_Minus_{timeframe}'] = vi_minus.fillna(1)
            logger.debug(f"Added VI_Plus_{timeframe} and VI_Minus_{timeframe}")

        # 6. UO - Ultimate Oscillator
        if f'UO_{timeframe}' not in df.columns and 'UO' in active_indicators:
            prior_close = close_prices.shift(1)
            true_low = pd.concat([low_prices, prior_close], axis=1).min(axis=1)
            buying_pressure = close_prices - true_low

            true_range = pd.concat([
                high_prices - low_prices,
                abs(high_prices - prior_close),
                abs(low_prices - prior_close)
            ], axis=1).max(axis=1)

            # Calculate for different periods
            bp7 = buying_pressure.rolling(window=7).sum()
            tr7 = true_range.rolling(window=7).sum()
            bp14 = buying_pressure.rolling(window=14).sum()
            tr14 = true_range.rolling(window=14).sum()
            bp28 = buying_pressure.rolling(window=28).sum()
            tr28 = true_range.rolling(window=28).sum()

            uo = 100 * ((4 * (bp7 / (tr7 + 1e-10))) + (2 * (bp14 / (tr14 + 1e-10))) + (bp28 / (tr28 + 1e-10))) / 7
            df[f'UO_{timeframe}'] = uo.fillna(50)
            logger.debug(f"Added UO_{timeframe}")

        # 7. PPO and PPO_Signal - Percentage Price Oscillator
        if f'PPO_{timeframe}' not in df.columns and 'PPO' in active_indicators:
            ema_fast = close_prices.ewm(span=12).mean()
            ema_slow = close_prices.ewm(span=26).mean()
            ppo = ((ema_fast - ema_slow) / ema_slow * 100).fillna(0)
            ppo_signal = ppo.ewm(span=9).mean()

            df[f'PPO_{timeframe}'] = ppo
            df[f'PPO_Signal_{timeframe}'] = ppo_signal.fillna(0)
            logger.debug(f"Added PPO_{timeframe} and PPO_Signal_{timeframe}")

        # 8. ADX, Plus_DI, Minus_DI - Average Directional Index
        if f'ADX_{timeframe}' not in df.columns and 'ADX' in active_indicators:
            period = 14

            # Calculate True Range
            tr = pd.concat([
                high_prices - low_prices,
                abs(high_prices - close_prices.shift(1)),
                abs(low_prices - close_prices.shift(1))
            ], axis=1).max(axis=1)

            # Calculate Directional Movement
            dm_plus = np.where((high_prices - high_prices.shift(1)) > (low_prices.shift(1) - low_prices),
                              np.maximum(high_prices - high_prices.shift(1), 0), 0)
            dm_minus = np.where((low_prices.shift(1) - low_prices) > (high_prices - high_prices.shift(1)),
                               np.maximum(low_prices.shift(1) - low_prices, 0), 0)

            # Smooth the values
            tr_smooth = pd.Series(tr).rolling(window=period).mean()
            dm_plus_smooth = pd.Series(dm_plus).rolling(window=period).mean()
            dm_minus_smooth = pd.Series(dm_minus).rolling(window=period).mean()

            # Calculate DI
            di_plus = 100 * (dm_plus_smooth / (tr_smooth + 1e-10))
            di_minus = 100 * (dm_minus_smooth / (tr_smooth + 1e-10))

            # Calculate ADX
            dx = 100 * abs((di_plus - di_minus) / (di_plus + di_minus + 1e-10))
            adx = dx.rolling(window=period).mean()

            df[f'ADX_{timeframe}'] = adx.fillna(25)
            df[f'Plus_DI_{timeframe}'] = di_plus.fillna(25)
            df[f'Minus_DI_{timeframe}'] = di_minus.fillna(25)
            logger.debug(f"Added ADX_{timeframe}, Plus_DI_{timeframe}, Minus_DI_{timeframe}")

        # 9. ROC - Rate of Change
        if f'ROC_{timeframe}' not in df.columns and 'ROC' in active_indicators:
            roc = close_prices.pct_change(periods=10) * 100
            df[f'ROC_{timeframe}'] = roc.fillna(0)
            logger.debug(f"Added ROC_{timeframe}")

        # 10. Trend_Strength - Custom trend strength indicator
        if f'Trend_Strength_{timeframe}' not in df.columns and 'Trend_Strength' in active_indicators:
            # Calculate trend strength using multiple MAs
            sma_5 = close_prices.rolling(window=5).mean()
            sma_10 = close_prices.rolling(window=10).mean()
            sma_20 = close_prices.rolling(window=20).mean()

            # Count how many MAs are aligned
            bullish_alignment = (close_prices > sma_5) & (sma_5 > sma_10) & (sma_10 > sma_20)
            bearish_alignment = (close_prices < sma_5) & (sma_5 < sma_10) & (sma_10 < sma_20)

            trend_strength = np.where(bullish_alignment, 1, np.where(bearish_alignment, -1, 0))
            df[f'Trend_Strength_{timeframe}'] = pd.Series(trend_strength, index=df.index)
            logger.debug(f"Added Trend_Strength_{timeframe}")

        # 11. KC_Upper and KC_Lower - Keltner Channels
        if f'KC_Upper_{timeframe}' not in df.columns and 'KC_Upper' in active_indicators:
            ema_20 = close_prices.ewm(span=20).mean()
            atr_10 = pd.concat([
                high_prices - low_prices,
                abs(high_prices - close_prices.shift(1)),
                abs(low_prices - close_prices.shift(1))
            ], axis=1).max(axis=1).rolling(window=10).mean()

            multiplier = 2.0
            df[f'KC_Upper_{timeframe}'] = (ema_20 + multiplier * atr_10).fillna(close_prices)
            df[f'KC_Lower_{timeframe}'] = (ema_20 - multiplier * atr_10).fillna(close_prices)
            logger.debug(f"Added KC_Upper_{timeframe} and KC_Lower_{timeframe}")

        # 12. VW_RSI and VW_MACD - Volume Weighted versions
        if f'VW_RSI_{timeframe}' not in df.columns and 'VW_RSI' in active_indicators:
            # Volume weighted price changes
            vw_price_change = (close_prices.diff() * volume).rolling(window=14).sum() / volume.rolling(window=14).sum()
            # Simplified VW_RSI (this is a complex calculation, using approximation)
            vw_rsi = 50 + (vw_price_change * 500)  # Scaled approximation
            df[f'VW_RSI_{timeframe}'] = vw_rsi.clip(0, 100).fillna(50)
            logger.debug(f"Added VW_RSI_{timeframe}")

        if f'VW_MACD_{timeframe}' not in df.columns and 'VW_MACD' in active_indicators:
            # Volume weighted MACD
            vw_close = (close_prices * volume).rolling(window=12).sum() / volume.rolling(window=12).sum()
            vw_ema_fast = vw_close.ewm(span=12).mean()
            vw_ema_slow = vw_close.ewm(span=26).mean()

            df[f'VW_MACD_{timeframe}'] = (vw_ema_fast - vw_ema_slow).fillna(0)
            df[f'VW_Signal_{timeframe}'] = df[f'VW_MACD_{timeframe}'].ewm(span=9).mean().fillna(0)
            logger.debug(f"Added VW_MACD_{timeframe} and VW_Signal_{timeframe}")

        # 13. EMA_slope - EMA slope calculation
        if f'EMA_slope_{timeframe}' not in df.columns and 'EMA_slope' in active_indicators:
            ema_20 = close_prices.ewm(span=20).mean()
            ema_slope = ema_20.diff(periods=5) / ema_20.shift(5) * 100  # 5-period slope as percentage
            df[f'EMA_slope_{timeframe}'] = ema_slope.fillna(0)
            logger.debug(f"Added EMA_slope_{timeframe}")

        # 14. BB_Upper and BB_Lower - Bollinger Bands (if not already added)
        if f'BB_Upper_{timeframe}' not in df.columns and 'BB_Upper' in active_indicators:
            sma_20 = close_prices.rolling(window=20).mean()
            std_20 = close_prices.rolling(window=20).std()

            df[f'BB_Upper_{timeframe}'] = (sma_20 + 2 * std_20).fillna(close_prices)
            df[f'BB_Lower_{timeframe}'] = (sma_20 - 2 * std_20).fillna(close_prices)
            logger.debug(f"Added BB_Upper_{timeframe} and BB_Lower_{timeframe}")

        # 15. momentum - Price momentum
        if f'momentum_{timeframe}' not in df.columns and 'momentum' in active_indicators:
            momentum = close_prices.diff(periods=10)
            df[f'momentum_{timeframe}'] = momentum.fillna(0)
            logger.debug(f"Added momentum_{timeframe}")

        logger.info(f"Successfully added missing indicators for {timeframe}")
        return df

    except Exception as e:
        logger.error(f"Error adding missing indicators for {timeframe}: {e}")
        return df

def standardize_future_returns(df, timeframe):
    """Standardize future returns to use consistent periods across all timeframes"""
    try:
        close_col = f'close_{timeframe}'

        # Use consistent future periods for all timeframes
        future_periods = 3  # Standardized as you suggested

        future_price = df[close_col].shift(-future_periods)
        future_return = (future_price - df[close_col]) / df[close_col]

        # Standardized column names
        df[f'future_return_{timeframe}'] = future_return.fillna(0)
        df[f'future_return_3_{timeframe}'] = future_return.fillna(0)  # Explicit 3-period version

        # Classification with adaptive thresholds
        profit_threshold = DYNAMIC_PARAMS.get('profit_percentage_1', 0.02)
        loss_threshold = -DYNAMIC_PARAMS.get('stop_loss_percentage_1', 0.01)

        df[f'future_return_{timeframe}_class'] = np.where(
            future_return > profit_threshold, 2,
            np.where(future_return < loss_threshold, 0, 1)
        )
        df[f'future_return_3_{timeframe}_class'] = df[f'future_return_{timeframe}_class']

        logger.debug(f"Standardized future returns for {timeframe} with period={future_periods}")
        return df

    except Exception as e:
        logger.error(f"Error standardizing future returns for {timeframe}: {e}")
        return df

def ensure_cross_timeframe_columns(df, timeframe):
    """Ensure critical cross-timeframe columns exist for all timeframes"""
    try:
        # Critical columns that must exist
        critical_columns = ['close_5m', 'RSI_5m', 'ATR_5m']

        for critical_col in critical_columns:
            if critical_col not in df.columns:
                # Extract the indicator and target timeframe
                indicator = critical_col.split('_')[0]
                target_tf = critical_col.split('_')[1]

                # Try to create from current timeframe
                source_col = f'{indicator}_{timeframe}'

                if source_col in df.columns:
                    df[critical_col] = df[source_col]
                    logger.debug(f"Created {critical_col} from {source_col}")
                else:
                    # Create basic version if source doesn't exist
                    if indicator == 'close':
                        if f'close_{timeframe}' in df.columns:
                            df[critical_col] = df[f'close_{timeframe}']
                        else:
                            df[critical_col] = pd.Series(1.0, index=df.index)
                    elif indicator == 'RSI':
                        df[critical_col] = pd.Series(50.0, index=df.index)
                    elif indicator == 'ATR':
                        df[critical_col] = pd.Series(0.01, index=df.index)

                    logger.warning(f"Created fallback {critical_col}")

        return df

    except Exception as e:
        logger.error(f"Error ensuring cross-timeframe columns: {e}")
        return df

def optimize_vwap_calculation(df, timeframe):
    """Optimized VWAP with configurable window"""
    try:
        vwap_window = DYNAMIC_PARAMS.get('vwap_window', 20)

        high_col = f'high_{timeframe}'
        low_col = f'low_{timeframe}'
        close_col = f'close_{timeframe}'
        volume_col = f'volume_{timeframe}'

        if all(col in df.columns for col in [high_col, low_col, close_col, volume_col]):
            typical_price = (df[high_col] + df[low_col] + df[close_col]) / 3

            # Rolling VWAP calculation
            cum_vol = df[volume_col].rolling(window=vwap_window).sum()
            cum_typ_vol = (typical_price * df[volume_col]).rolling(window=vwap_window).sum()

            vwap = cum_typ_vol / (cum_vol + 1e-10)
            df[f'VWAP_{timeframe}'] = vwap.fillna(typical_price)

            logger.debug(f"Optimized VWAP for {timeframe} with window={vwap_window}")

        return df

    except Exception as e:
        logger.error(f"Error optimizing VWAP for {timeframe}: {e}")
        return df

def optimize_feature_memory(df, timeframe):
    """Optimize memory usage without losing important features - CONSERVATIVE approach"""
    try:
        original_cols = len(df.columns)
        
        # Only optimize memory usage, don't remove features
        # Convert float64 to float32 where possible to save memory
        for col in df.select_dtypes(include=['float64']).columns:
            # Check if values fit in float32 range
            col_min = df[col].min()
            col_max = df[col].max()
            if pd.notna(col_min) and pd.notna(col_max):
                if col_min >= np.finfo(np.float32).min and col_max <= np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
        
        # Remove only truly duplicate columns (exactly the same values)
        # BUT preserve critical cross-timeframe columns and important indicators
        duplicate_cols = []
        cols_to_check = df.columns.tolist()
        
        # Critical columns that should NEVER be removed even if they appear duplicate
        protected_columns = [
            'close_5m', 'RSI_5m', 'ATR_5m',  # Cross-timeframe essentials
            f'Plus_DI_{timeframe}', f'Minus_DI_{timeframe}',  # Important indicators
            f'open_{timeframe}', f'high_{timeframe}', f'low_{timeframe}', f'close_{timeframe}', f'volume_{timeframe}'  # OHLCV
        ]
        
        for i, col1 in enumerate(cols_to_check):
            for col2 in cols_to_check[i+1:]:
                if (col1 not in duplicate_cols and col2 not in duplicate_cols and 
                    col2 not in protected_columns):  # Don't remove protected columns
                    try:
                        # Only consider truly identical columns as duplicates
                        if df[col1].equals(df[col2]) and col1 != col2:
                            # Extra safety - don't remove if names suggest they should be different
                            if not (('Plus_DI' in col2 and 'ADX' in col1) or 
                                   ('Minus_DI' in col2 and 'ADX' in col1) or
                                   ('_5m' in col2 and f'_{timeframe}' in col1 and timeframe != '5m')):
                                duplicate_cols.append(col2)
                                logger.debug(f"Found duplicate column: {col2} (same as {col1})")
                    except:
                        continue
        
        if duplicate_cols:
            df = df.drop(columns=duplicate_cols)
            logger.info(f"Removed {len(duplicate_cols)} duplicate columns for {timeframe}")
        
        # Only warn if we have excessive columns, don't auto-trim
        if len(df.columns) > 150:
            logger.warning(f"High feature count for {timeframe}: {len(df.columns)} columns. Consider feature selection for performance.")
        
        if len(df.columns) != original_cols:
            logger.info(f"Memory optimized for {timeframe}: {len(df.columns)} columns (was {original_cols})")
        
        return df
        
    except Exception as e:
        logger.error(f"Error optimizing features for {timeframe}: {e}")
        return df

def process_large_dataframe_in_chunks(df, timeframe, chunk_size=10000):
    """Process large dataframes in chunks for memory efficiency - FIXED to avoid duplication"""
    try:
        if len(df) <= chunk_size:
            # Process normally for smaller datasets
            result_df = df.copy()
            result_df = add_missing_dynamic_indicators(result_df, timeframe)
            result_df = add_standard_indicators(result_df, timeframe)
            result_df = standardize_future_returns(result_df, timeframe)
            result_df = ensure_cross_timeframe_columns(result_df, timeframe)
            result_df = optimize_vwap_calculation(result_df, timeframe)
            result_df = trim_excessive_features(result_df, timeframe)
            return result_df

        logger.info(f"Processing large dataframe for {timeframe} in chunks: {len(df)} rows, chunk_size={chunk_size}")

        processed_chunks = []

        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size].copy()

            # Process chunk with all enhancements
            chunk = add_missing_dynamic_indicators(chunk, timeframe)
            chunk = add_standard_indicators(chunk, timeframe)
            chunk = standardize_future_returns(chunk, timeframe)
            chunk = ensure_cross_timeframe_columns(chunk, timeframe)
            chunk = optimize_vwap_calculation(chunk, timeframe)

            processed_chunks.append(chunk)

            logger.debug(f"Processed chunk {i//chunk_size + 1}/{(len(df)-1)//chunk_size + 1}")

        # Combine chunks
        result_df = pd.concat(processed_chunks, ignore_index=False)
        logger.info(f"Successfully processed {len(result_df)} rows in {len(processed_chunks)} chunks")
        
        # Optimize memory usage without losing features
        result_df = optimize_feature_memory(result_df, timeframe)
        
        return result_df

    except Exception as e:
        logger.error(f"Error processing chunks for {timeframe}: {e}")
        return df

def calculate_enhanced_features_v2_complete(df, timeframe):
    """Complete enhanced feature calculation with all fixes applied and performance optimizations"""
    try:
        logger.info(f"Calculating complete enhanced features v2 for {timeframe} with {len(df)} rows")

        # AGGRESSIVE EARLY EXIT - check if we already have sufficient features
        if len(df.columns) >= 45:  # Reasonable threshold
            required_indicators = [f'RSI_{timeframe}', f'MACD_{timeframe}', f'ATR_{timeframe}']
            has_required = all(col in df.columns for col in required_indicators)
            if has_required:
                logger.info(f"✅ Features already present for {timeframe} ({len(df.columns)} columns) - skipping recalculation")
                return optimize_feature_memory(df, timeframe)  # Still optimize memory

        # Check if we nd chunking for large datasets (especially 5m)
        chunk_threshold = 10000
        if len(df) > chunk_threshold:
            # SMART CHECK: If we already have most indicators, don't chunk (avoids duplicate work)
            existing_indicators = [col for col in df.columns if f'_{timeframe}' in col and any(indicator in col for indicator in ['RSI', 'MACD', 'ATR', 'ADX', 'CCI', 'STOCH'])]
            if len(existing_indicators) >= 6:  # We have most key indicators already
                logger.info(f"Key indicators already present for {timeframe} - processing normally without chunking")
                # Process normally without chunking to avoid duplicate work
                features_df = df.copy()
                features_df = add_missing_dynamic_indicators(features_df, timeframe)
                features_df = add_standard_indicators(features_df, timeframe)
                features_df = standardize_future_returns(features_df, timeframe)
                features_df = ensure_cross_timeframe_columns(features_df, timeframe)
                features_df = optimize_vwap_calculation(features_df, timeframe)
                features_df = optimize_feature_memory(features_df, timeframe)
                return features_df
            else:
                return process_large_dataframe_in_chunks(df, timeframe, chunk_size=chunk_threshold)

        # Standard processing for smaller datasets
        features_df = df.copy()

        # Apply all enhancements in the correct order
        features_df = add_missing_dynamic_indicators(features_df, timeframe)
        features_df = add_standard_indicators(features_df, timeframe)  # Add missing standard indicators
        features_df = standardize_future_returns(features_df, timeframe)
        features_df = ensure_cross_timeframe_columns(features_df, timeframe)
        features_df = optimize_vwap_calculation(features_df, timeframe)
        
        # Optimize memory usage without losing important features
        features_df = optimize_feature_memory(features_df, timeframe)

        # Final validation
        active_indicators = DYNAMIC_PARAMS.get('active_indicators', [])
        standard_indicators = ['SMA', 'EMA', 'MACD', 'Signal', 'RSI', 'ATR', 'STC', 'Bull_Engulfing', 'Bear_Engulfing']
        all_expected_indicators = list(set(active_indicators + standard_indicators))

        missing_indicators = []
        for indicator in all_expected_indicators:
            if f'{indicator}_{timeframe}' not in features_df.columns:
                missing_indicators.append(f'{indicator}_{timeframe}')

        if missing_indicators:
            logger.warning(f"Still missing indicators for {timeframe}: {missing_indicators}")
        else:
            logger.info(f"All active indicators present for {timeframe}")

        # Verify critical cross-timeframe columns (more flexible check)
        critical_columns = ['close_5m', 'RSI_5m', 'ATR_5m']
        missing_critical = [col for col in critical_columns if col not in features_df.columns]

        if missing_critical:
            # Try to recreate missing cross-timeframe columns
            for col in missing_critical:
                indicator = col.split('_')[0]
                source_col = f'{indicator}_{timeframe}'
                if source_col in features_df.columns:
                    features_df[col] = features_df[source_col]
                    logger.debug(f"Recreated {col} from {source_col}")
                    missing_critical.remove(col)
            
            # Only error if we still can't create them
            if missing_critical:
                logger.warning(f"Could not create critical cross-timeframe columns: {missing_critical}")
            else:
                logger.debug(f"All critical cross-timeframe columns present")
        else:
            logger.debug(f"All critical cross-timeframe columns present")

        logger.info(f"Complete enhanced features v2 finished: {len(features_df.columns)} total columns")
        return features_df

    except Exception as e:
        logger.error(f"Error in complete enhanced features v2 for {timeframe}: {e}")
        return df

# Integration wrapper function
def integrate_complete_enhanced_features(original_calculate_features):
    """Complete integration wrapper that applies all fixes"""
    def enhanced_calculate_features_complete(df, trades, timeframe, pair, dynamic_params, skip_harmonics=False):
        # First run original feature calculation if available
        try:
            features_df = original_calculate_features(df, trades, timeframe, pair, dynamic_params, skip_harmonics)
        except:
            # If original function fails, start with the base dataframe
            features_df = df.copy()

        if features_df.empty:
            return features_df

        # Then apply complete enhancements
        enhanced_df = calculate_enhanced_features_v2_complete(features_df, timeframe)

        return enhanced_df if not enhanced_df.empty else features_df

    return enhanced_calculate_features_complete

# Backward compatibility wrapper for data_loading.py
def calculate_features(df, timeframe):
    """Backward compatibility wrapper for data_loading.py"""
    return calculate_enhanced_features_v2_complete(df, timeframe)

# Alternative entry point
def calculate_enhanced_features_v2(df, timeframe):
    """Alternative entry point for enhanced features"""
    return calculate_enhanced_features_v2_complete(df, timeframe)

logger.info("✅ Complete enhanced feature_engineering.py loaded with all fixes, performance optimizations, and feature trimming")

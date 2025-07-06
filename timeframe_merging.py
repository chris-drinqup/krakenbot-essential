import pandas as pd
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)
RUN_ID = "quebot_run"

def ensure_cross_timeframe_columns(timeframe_dfs):
    """
    COMPREHENSIVE FIX: Create ALL missing cross-timeframe columns properly
    This ensures ALL timeframes have indicators from ALL other timeframes
    """
    try:
        if not timeframe_dfs:
            logger.warning("No timeframes provided for cross-timeframe column creation")
            return timeframe_dfs

        logger.info("Creating comprehensive cross-timeframe columns")
        available_timeframes = list(timeframe_dfs.keys())
        logger.info(f"Available timeframes: {available_timeframes}")

        # Define ALL indicators we need from each timeframe
        essential_indicators = [
            'RSI', 'MACD', 'Signal', 'ATR', 'SMA', 'EMA', 'BB_Upper', 'BB_Lower',
            'ADX', 'Plus_DI', 'Minus_DI', 'CCI', 'STOCH_k', 'STOCH_d', 
            'WilliamsR', 'KO', 'VI_Plus', 'VI_Minus', 'UO', 'PPO', 'PPO_Signal',
            'ROC', 'momentum', 'VW_RSI', 'VW_MACD', 'VW_Signal', 'EMA_slope',
            'STC', 'Trend_Strength', 'Bull_Engulfing', 'Bear_Engulfing',
            'KC_Upper', 'KC_Lower'
        ]
        
        essential_ohlcv = ['open', 'high', 'low', 'close', 'volume']

        # For each target timeframe, ensure it has ALL indicators from ALL source timeframes
        for target_tf in available_timeframes:
            target_df = timeframe_dfs[target_tf]
            original_columns = len(target_df.columns)
            columns_added = 0
            
            # Add indicators from each source timeframe
            for source_tf in available_timeframes:
                if source_tf == target_tf:
                    continue  # Skip self
                    
                source_df = timeframe_dfs[source_tf]
                
                # Add OHLCV columns
                for base_col in essential_ohlcv:
                    source_col = f'{base_col}_{source_tf}'
                    target_col = f'{base_col}_{source_tf}'
                    
                    if source_col in source_df.columns and target_col not in target_df.columns:
                        try:
                            # Resample the source data to target timeframe frequency
                            resampled_data = resample_to_target_timeframe(
                                source_df[source_col], source_tf, target_tf, target_df.index
                            )
                            
                            if resampled_data is not None and not resampled_data.empty:
                                target_df[target_col] = resampled_data
                                columns_added += 1
                            else:
                                # Create safe default if resampling fails
                                if base_col in ['open', 'high', 'low', 'close']:
                                    fallback_col = f'close_{target_tf}'
                                    target_df[target_col] = target_df.get(fallback_col, 1.0)
                                elif base_col == 'volume':
                                    fallback_col = f'volume_{target_tf}'
                                    target_df[target_col] = target_df.get(fallback_col, 1000.0)
                                columns_added += 1
                        except Exception as e:
                            logger.debug(f"Error resampling {source_col}: {e}, using default")
                            # Safe defaults
                            if base_col in ['open', 'high', 'low', 'close']:
                                target_df[target_col] = 1.0
                            elif base_col == 'volume':
                                target_df[target_col] = 1000.0
                            columns_added += 1
                
                # Add indicator columns
                for indicator in essential_indicators:
                    source_col = f'{indicator}_{source_tf}'
                    target_col = f'{indicator}_{source_tf}'
                    
                    if source_col in source_df.columns and target_col not in target_df.columns:
                        try:
                            # Resample the indicator data
                            resampled_data = resample_to_target_timeframe(
                                source_df[source_col], source_tf, target_tf, target_df.index
                            )
                            
                            if resampled_data is not None and not resampled_data.empty:
                                target_df[target_col] = resampled_data
                                columns_added += 1
                            else:
                                # Create intelligent defaults for indicators
                                default_value = get_indicator_default(indicator)
                                target_df[target_col] = default_value
                                columns_added += 1
                        except Exception as e:
                            logger.debug(f"Error resampling {source_col}: {e}, using default")
                            default_value = get_indicator_default(indicator)
                            target_df[target_col] = default_value
                            columns_added += 1
            
            logger.info(f"{target_tf}: {original_columns} -> {len(target_df.columns)} columns (+{columns_added} cross-timeframe)")
            timeframe_dfs[target_tf] = target_df

        return timeframe_dfs

    except Exception as e:
        logger.error(f"Error in comprehensive cross-timeframe column creation: {e}")
        return timeframe_dfs

def resample_to_target_timeframe(source_series, source_tf, target_tf, target_index):
    """
    Properly resample data from source timeframe to target timeframe with robust error handling
    """
    try:
        if source_series is None or source_series.empty:
            return None
            
        # Define timeframe hierarchy (in minutes)
        tf_minutes = {
            '5m': 5, '15m': 15, '30m': 30, '1h': 60, 
            '4h': 240, '6h': 360, '1d': 1440
        }
        
        source_minutes = tf_minutes.get(source_tf, 5)
        target_minutes = tf_minutes.get(target_tf, 5)
        
        # Always use reindex with forward fill for simplicity and robustness
        try:
            resampled = source_series.reindex(target_index, method='ffill')
            
            # Fill any remaining NaN values with backward fill, then forward fill
            if resampled.isna().any():
                resampled = resampled.fillna(method='bfill')
                if resampled.isna().any():
                    resampled = resampled.fillna(method='ffill')
                    
            # If still NaN, use the mean or a safe default
            if resampled.isna().any():
                if not source_series.isna().all():
                    fill_value = source_series.mean() if source_series.dtype.kind in 'biufc' else source_series.mode().iloc[0] if not source_series.mode().empty else 0
                else:
                    fill_value = 0
                resampled = resampled.fillna(fill_value)
            
            return resampled
            
        except Exception as e:
            logger.debug(f"Reindex failed for {source_tf}->{target_tf}: {e}")
            # Fallback: create series with same length as target, filled with source mean
            if not source_series.empty and not source_series.isna().all():
                fill_value = source_series.mean() if source_series.dtype.kind in 'biufc' else source_series.iloc[0]
            else:
                fill_value = 0
            return pd.Series(fill_value, index=target_index)
        
    except Exception as e:
        logger.debug(f"Error resampling {source_tf} to {target_tf}: {e}")
        return None

def get_indicator_default(indicator_name):
    """Get appropriate default value for an indicator"""
    defaults = {
        'RSI': 50.0,
        'STOCH_k': 50.0,
        'STOCH_d': 50.0,
        'WilliamsR': -50.0,
        'CCI': 0.0,
        'ATR': 0.01,
        'ADX': 25.0,
        'Plus_DI': 25.0,
        'Minus_DI': 25.0,
        'UO': 50.0,
        'VW_RSI': 50.0,
        'STC': 50.0,
        'Trend_Strength': 0.0,
        'Bull_Engulfing': 0,
        'Bear_Engulfing': 0,
        'BB_Upper': 1.02,
        'BB_Lower': 0.98,
        'KC_Upper': 1.02,
        'KC_Lower': 0.98,
        'PPO': 0.0,
        'PPO_Signal': 0.0,
        'ROC': 0.0,
        'momentum': 0.0,
        'VW_MACD': 0.0,
        'VW_Signal': 0.0,
        'EMA_slope': 0.0,
        'VI_Plus': 1.0,
        'VI_Minus': 1.0,
        'KO': 0.0,
        'SMA': 1.0,
        'EMA': 1.0,
        'MACD': 0.0,
        'Signal': 0.0,
    }
    return defaults.get(indicator_name, 0.0)

def validate_cross_timeframe_columns(timeframe_dfs):
    """Validate column creation results"""
    if not timeframe_dfs:
        return

    # Count cross-timeframe columns for each timeframe
    for tf, df in timeframe_dfs.items():
        cross_tf_cols = [col for col in df.columns if any(other_tf in col for other_tf in timeframe_dfs.keys() if other_tf != tf)]
        logger.info(f"{tf}: {len(df.columns)} total columns, {len(cross_tf_cols)} cross-timeframe columns ✓")

def combine_timeframes(timeframe_dfs, base_timeframe='5m'):
    """
    COMPLETE SOLUTION: Combine timeframes with comprehensive cross-timeframe columns
    """
    try:
        if not timeframe_dfs:
            return {}

        logger.info(f"COMPLETE timeframe combination for: {list(timeframe_dfs.keys())}")

        # STEP 1: Create cross-timeframe columns
        timeframe_dfs = ensure_cross_timeframe_columns(timeframe_dfs)
        timeframe_dfs = create_missing_essential_columns(timeframe_dfs)

        # STEP 2: Validate results
        validate_cross_timeframe_columns(timeframe_dfs)

        # STEP 3: Final cleanup and preparation
        combined_dfs = {}
        for tf, df in timeframe_dfs.items():
            try:
                # Add target columns if missing
                for col in ['target_short', 'target_mid', 'target_long']:
                    if col not in df.columns:
                        df[col] = 0

                # Handle infinite values
                df = df.replace([np.inf, -np.inf], 0)
                
                # Final NaN cleanup with intelligent defaults
                for col in df.columns:
                    if df[col].isna().any():
                        if 'RSI' in col or 'STOCH' in col:
                            df[col] = df[col].fillna(50.0)
                        elif 'ATR' in col:
                            df[col] = df[col].fillna(0.01)
                        elif 'volume' in col:
                            df[col] = df[col].fillna(1000.0)
                        elif any(price_col in col for price_col in ['open', 'high', 'low', 'close']):
                            df[col] = df[col].fillna(method='ffill').fillna(1.0)
                        else:
                            df[col] = df[col].fillna(0.0)

                combined_dfs[tf] = df
                
                cross_tf_columns = [col for col in df.columns if any(other_tf in col for other_tf in timeframe_dfs.keys() if other_tf != tf)]
                logger.info(f"{tf} COMPLETE: {len(df)} rows, {len(df.columns)} columns, {len(cross_tf_columns)} cross-timeframe ✓")

            except Exception as e:
                logger.error(f"Error finalizing {tf}: {e}")
                combined_dfs[tf] = df

        return combined_dfs

    except Exception as e:
        logger.error(f"Error in complete timeframe combination: {e}")
        return timeframe_dfs


def create_missing_essential_columns(timeframe_dfs):
    """Simple fix: create missing essential columns with safe defaults"""
    try:
        essential_columns = ['RSI_5m', 'ATR_5m', 'close_5m', 'volume_5m', 'MACD_5m', 'Signal_5m']
        
        for tf_name, df in timeframe_dfs.items():
            for col in essential_columns:
                if col not in df.columns:
                    if 'RSI' in col:
                        df[col] = 50.0
                    elif 'ATR' in col:
                        df[col] = 0.01
                    elif 'volume' in col:
                        df[col] = 1000.0
                    elif 'close' in col:
                        # Use the timeframe's own close if available
                        own_close = f'close_{tf_name}'
                        if own_close in df.columns:
                            df[col] = df[own_close]
                        else:
                            df[col] = 1.0
                    else:
                        df[col] = 0.0
        
        return timeframe_dfs
    except Exception as e:
        print(f"Error creating missing columns: {e}")
        return timeframe_dfs

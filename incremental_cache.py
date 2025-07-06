# Incremental Cache Update Module
# Preserves existing cache and only fetches new data since last timestamp

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from config import DEPENDENCY_DIR, PAIR, TIMEFRAMES_TO_EVALUATE
from logging_setup import logger

def get_last_cache_timestamp(cache_file):
    """Get the last timestamp from existing cache file"""
    try:
        if not os.path.exists(cache_file):
            return None
        
        df = pd.read_csv(cache_file)
        if df.empty:
            return None
        
        # Try different timestamp column names
        timestamp_cols = ['timestamp', 'Unnamed: 0']
        for col in timestamp_cols:
            if col in df.columns:
                timestamps = pd.to_datetime(df[col], errors='coerce')
                valid_timestamps = timestamps.dropna()
                if not valid_timestamps.empty:
                    last_timestamp = valid_timestamps.max()
                    logger.info(f"📅 Last cache timestamp: {last_timestamp}")
                    return last_timestamp
        
        return None
        
    except Exception as e:
        logger.error(f"Error reading cache timestamp: {e}")
        return None

def update_ohlc_cache_incrementally(pair, timeframes_to_update=None):
    """Update OHLC cache with only new data since last timestamp"""
    try:
        if timeframes_to_update is None:
            timeframes_to_update = TIMEFRAMES_TO_EVALUATE
        
        logger.info(f"🔄 Updating OHLC cache incrementally for {pair}")
        
        updated_timeframes = []
        
        for timeframe in timeframes_to_update:
            try:
                pair_clean = pair.lower().replace('/', '').replace('-', '')
                cache_file = os.path.join(DEPENDENCY_DIR, f"ohlc_cache_{pair_clean}_{timeframe}.csv")
                
                logger.info(f"   📊 Checking {timeframe} cache...")
                
                # Check if cache exists and get last timestamp
                last_timestamp = get_last_cache_timestamp(cache_file)
                
                if last_timestamp is not None:
                    # Calculate time since last update
                    current_time = pd.Timestamp.now(tz='UTC')
                    if last_timestamp.tz is None:
                        last_timestamp = last_timestamp.tz_localize('UTC')
                    
                    time_gap = current_time - last_timestamp
                    hours_gap = time_gap.total_seconds() / 3600
                    
                    logger.info(f"   📈 {timeframe}: {hours_gap:.1f} hours since last update")
                    
                    # Only update if gap is significant (more than 1 hour for short timeframes)
                    min_gap_hours = {'5m': 1, '15m': 1, '30m': 2, '1h': 4, '4h': 8, '6h': 12, '1d': 24}
                    required_gap = min_gap_hours.get(timeframe, 1)
                    
                    if hours_gap < required_gap:
                        logger.info(f"   ✅ {timeframe}: Cache is fresh enough (gap: {hours_gap:.1f}h < {required_gap}h)")
                        updated_timeframes.append(timeframe)
                        continue
                    
                    # Fetch new trades since last timestamp
                    logger.info(f"   🔄 Fetching new trades since {last_timestamp}")
                    
                    # Import here to avoid circular imports
                    from data_fetching import dynamic_fetch_trades, trades_to_ohlc
                    
                    # Set since time to slightly before last timestamp to avoid gaps
                    since = last_timestamp - timedelta(hours=1)
                    
                    trades_cache_file = os.path.join(DEPENDENCY_DIR, f"trades_cache_{pair_clean}_{timeframe}.csv")
                    
                    # Fetch new trades
                    new_trades_result = dynamic_fetch_trades(
                        pair=pair,
                        cache_file=trades_cache_file,
                        since=since,
                        live_mode=True,
                        source='kraken',
                        reset_cache=False  # Don't reset - we want to preserve existing data
                    )
                    
                    # Handle both old and new return formats
                    if isinstance(new_trades_result, tuple):
                        new_trades, quality_metrics = new_trades_result
                    else:
                        new_trades = new_trades_result
                    
                    if new_trades.empty:
                        logger.info(f"   ✅ {timeframe}: No new trades found")
                        updated_timeframes.append(timeframe)
                        continue
                    
                    # Filter trades to only those after last timestamp
                    new_trades_filtered = new_trades[new_trades.index > last_timestamp]
                    
                    if new_trades_filtered.empty:
                        logger.info(f"   ✅ {timeframe}: No new trades after {last_timestamp}")
                        updated_timeframes.append(timeframe)
                        continue
                    
                    # Generate OHLC for new trades
                    new_ohlc_file = os.path.join(DEPENDENCY_DIR, f"new_ohlc_{pair_clean}_{timeframe}.csv")
                    new_ohlc = trades_to_ohlc(new_trades_filtered, timeframe, new_ohlc_file)
                    
                    if new_ohlc.empty:
                        logger.warning(f"   ⚠️ {timeframe}: Failed to generate new OHLC")
                        continue
                    
                    # Load existing cache
                    existing_df = pd.read_csv(cache_file)
                    
                    # Ensure timestamp column
                    if 'timestamp' not in existing_df.columns and 'Unnamed: 0' in existing_df.columns:
                        existing_df = existing_df.rename(columns={'Unnamed: 0': 'timestamp'})
                    
                    if 'timestamp' not in new_ohlc.columns:
                        new_ohlc = new_ohlc.reset_index()
                        if 'timestamp' not in new_ohlc.columns and new_ohlc.index.name == 'timestamp':
                            new_ohlc = new_ohlc.reset_index()
                    
                    # Combine old and new data
                    combined_df = pd.concat([existing_df, new_ohlc], ignore_index=True)
                    
                    # Remove duplicates based on timestamp
                    if 'timestamp' in combined_df.columns:
                        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                        combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
                        combined_df = combined_df.sort_values('timestamp')
                    
                    # Save updated cache
                    combined_df.to_csv(cache_file, index=False)
                    
                    # Clean up temporary file
                    if os.path.exists(new_ohlc_file):
                        os.remove(new_ohlc_file)
                    
                    rows_added = len(new_ohlc)
                    total_rows = len(combined_df)
                    
                    logger.info(f"   ✅ {timeframe}: Added {rows_added} new rows, total: {total_rows}")
                    updated_timeframes.append(timeframe)
                    
                else:
                    # No existing cache - need to generate from scratch
                    logger.info(f"   🆕 {timeframe}: No existing cache, generating from scratch")
                    
                    from generate_all_ohlc import generate_ohlc_for_timeframe
                    
                    if generate_ohlc_for_timeframe(pair, timeframe):
                        updated_timeframes.append(timeframe)
                        logger.info(f"   ✅ {timeframe}: Generated new cache")
                    else:
                        logger.warning(f"   ❌ {timeframe}: Failed to generate cache")
                
            except Exception as e:
                logger.error(f"Error updating {timeframe} cache: {e}")
                continue
        
        logger.info(f"✅ Incremental cache update complete: {len(updated_timeframes)} timeframes updated")
        return updated_timeframes
        
    except Exception as e:
        logger.error(f"Error in incremental cache update: {e}")
        return []

def check_cache_freshness(pair):
    """Check how fresh the existing cache is"""
    try:
        cache_status = {}
        current_time = pd.Timestamp.now(tz='UTC')
        
        for timeframe in TIMEFRAMES_TO_EVALUATE:
            pair_clean = pair.lower().replace('/', '').replace('-', '')
            cache_file = os.path.join(DEPENDENCY_DIR, f"ohlc_cache_{pair_clean}_{timeframe}.csv")
            
            if os.path.exists(cache_file):
                last_timestamp = get_last_cache_timestamp(cache_file)
                
                if last_timestamp:
                    if last_timestamp.tz is None:
                        last_timestamp = last_timestamp.tz_localize('UTC')
                    
                    hours_old = (current_time - last_timestamp).total_seconds() / 3600
                    
                    # Get row count
                    df = pd.read_csv(cache_file)
                    row_count = len(df)
                    
                    cache_status[timeframe] = {
                        'exists': True,
                        'last_timestamp': last_timestamp,
                        'hours_old': hours_old,
                        'row_count': row_count,
                        'file_size_mb': os.path.getsize(cache_file) / 1024 / 1024
                    }
                else:
                    cache_status[timeframe] = {'exists': True, 'readable': False}
            else:
                cache_status[timeframe] = {'exists': False}
        
        # Log summary
        logger.info("📊 Cache freshness summary:")
        for tf, status in cache_status.items():
            if status.get('exists') and status.get('row_count'):
                hours = status.get('hours_old', 0)
                rows = status.get('row_count', 0)
                size = status.get('file_size_mb', 0)
                logger.info(f"   {tf}: {rows:,} rows, {hours:.1f}h old, {size:.1f}MB")
            else:
                logger.info(f"   {tf}: Missing or unreadable")
        
        return cache_status
        
    except Exception as e:
        logger.error(f"Error checking cache freshness: {e}")
        return {}

def smart_cache_update(pair):
    """Smart cache update that only updates what's needed"""
    try:
        # Check current cache status
        cache_status = check_cache_freshness(pair)
        
        # Determine which timeframes need updating
        timeframes_to_update = []
        
        for timeframe, status in cache_status.items():
            if not status.get('exists'):
                timeframes_to_update.append(timeframe)
                logger.info(f"📋 {timeframe}: Needs creation (missing)")
            elif not status.get('readable'):
                timeframes_to_update.append(timeframe)
                logger.info(f"📋 {timeframe}: Needs recreation (unreadable)")
            elif status.get('hours_old', 0) > 6:  # More than 6 hours old
                timeframes_to_update.append(timeframe)
                logger.info(f"📋 {timeframe}: Needs update ({status['hours_old']:.1f}h old)")
            else:
                logger.info(f"✅ {timeframe}: Cache is fresh ({status['hours_old']:.1f}h old)")
        
        if timeframes_to_update:
            logger.info(f"🔄 Updating {len(timeframes_to_update)} timeframes: {timeframes_to_update}")
            return update_ohlc_cache_incrementally(pair, timeframes_to_update)
        else:
            logger.info("✅ All caches are fresh, no updates needed")
            return list(cache_status.keys())
            
    except Exception as e:
        logger.error(f"Error in smart cache update: {e}")
        return []

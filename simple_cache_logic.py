#!/usr/bin/env python3
"""
Simple Cache Logic: If cache exists, don't regenerate. If not, generate.
"""

import os
import pandas as pd
from logging_setup import logger

def simple_cache_check_wrapper(*args, **kwargs):
    """Simple wrapper: cache exists = skip, no cache = generate"""
    
    pair = "ADAUSDT"  # Make this dynamic if needed
    timeframes = ['5m', '15m', '30m', '1h', '4h', '6h', '1d']
    
    existing_caches = 0
    total_rows = 0
    
    # Check each timeframe
    for tf in timeframes:
        cache_file = f"dependencies_v1/ohlc_cache_{pair.lower()}_{tf}.csv"
        
        if os.path.exists(cache_file):
            try:
                df = pd.read_csv(cache_file)
                if not df.empty:
                    existing_caches += 1
                    total_rows += len(df)
            except:
                continue
    
    # Simple decision: if ANY substantial cache exists, don't regenerate
    if existing_caches > 0 and total_rows > 50:
        logger.info(f"CACHE EXISTS: Found {total_rows} rows across {existing_caches} timeframes")
        logger.info("Skipping OHLC generation - using existing cache files")
        return True
    else:
        logger.info(f"NO CACHE or insufficient data: {total_rows} rows across {existing_caches} timeframes")
        logger.info("Proceeding with OHLC generation")
        
        # Call original function if available
        try:
            from generate_all_ohlc import generate_all_ohlc_from_trades as original_func
            return original_func(*args, **kwargs)
        except ImportError:
            logger.warning("Original OHLC function not available")
            return False

# Store this function to be imported
generate_all_ohlc_from_trades = simple_cache_check_wrapper

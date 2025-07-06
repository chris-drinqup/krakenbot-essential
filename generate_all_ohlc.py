# Version: 1.0 - OHLC Generation Utility
# This utility ensures all timeframes have OHLC data generated from trades

import os
import pandas as pd
from config import PAIR, DEPENDENCY_DIR, TIMEFRAMES, RUN_ID
from logging_setup import logger
from data_fetching import trades_to_ohlc

def generate_all_ohlc_from_trades():
    """
    Generate OHLC data for all timeframes from trades cache
    This fixes the critical issue where some timeframes were missing OHLC data
    """
    try:
        logger.info(f"Generating OHLC for all timeframes from trades cache for {PAIR}", extra={"run_id": RUN_ID})
        
        # Load trades cache
        trades_cache_file = os.path.join(DEPENDENCY_DIR, f"trades_cache_{PAIR.lower().replace('/', '')}.csv")
        
        if not os.path.exists(trades_cache_file):
            logger.error(f"Trades cache not found: {trades_cache_file}")
            return False
            
        try:
            trades_df = pd.read_csv(trades_cache_file, parse_dates=['timestamp'], index_col='timestamp')
            logger.info(f"Loaded {len(trades_df)} trades from cache")
        except Exception as e:
            logger.error(f"Failed to load trades cache: {str(e)}")
            return False
            
        if trades_df.empty:
            logger.error("Trades cache is empty")
            return False
            
        # Generate OHLC for each timeframe
        success_count = 0
        
        for timeframe in TIMEFRAMES:
            try:
                ohlc_cache_file = os.path.join(DEPENDENCY_DIR, f"ohlc_cache_{PAIR.lower().replace('/', '')}_{timeframe}.csv")
                
                # Check if OHLC already exists and is recent
                if os.path.exists(ohlc_cache_file):
                    try:
                        existing_ohlc = pd.read_csv(ohlc_cache_file, parse_dates=['timestamp'], index_col='timestamp')
                        if not existing_ohlc.empty and len(existing_ohlc) > 50:
                            logger.debug(f"OHLC for {timeframe} already exists with {len(existing_ohlc)} rows")
                            success_count += 1
                            continue
                    except Exception as e:
                        logger.warning(f"Existing OHLC file for {timeframe} is corrupted: {e}")
                
                # Generate OHLC
                logger.info(f"Generating OHLC for timeframe {timeframe}")
                ohlc_df = trades_to_ohlc(trades_df, timeframe, ohlc_cache_file)
                
                if not ohlc_df.empty:
                    logger.info(f"Successfully generated OHLC for {timeframe}: {len(ohlc_df)} rows")
                    success_count += 1
                else:
                    logger.warning(f"Generated empty OHLC for {timeframe}")
                    
            except Exception as e:
                logger.error(f"Failed to generate OHLC for {timeframe}: {str(e)}")
                continue
                
        logger.info(f"OHLC generation complete: {success_count}/{len(TIMEFRAMES)} timeframes successful")
        
        # Return True if at least half the timeframes were successful
        return success_count >= len(TIMEFRAMES) // 2
        
    except Exception as e:
        logger.error(f"Critical error in generate_all_ohlc_from_trades: {str(e)}")
        return False

def check_ohlc_completeness():
    """
    Check which timeframes have OHLC data and which are missing
    """
    try:
        missing_timeframes = []
        existing_timeframes = []
        
        for timeframe in TIMEFRAMES:
            ohlc_cache_file = os.path.join(DEPENDENCY_DIR, f"ohlc_cache_{PAIR.lower().replace('/', '')}_{timeframe}.csv")
            
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
                
        logger.info(f"OHLC completeness check: Existing: {existing_timeframes}, Missing: {missing_timeframes}")
        
        return existing_timeframes, missing_timeframes
        
    except Exception as e:
        logger.error(f"Error checking OHLC completeness: {str(e)}")
        return [], list(TIMEFRAMES)

def ensure_minimum_ohlc_data():
    """
    Ensure we have at least the basic timeframes needed for trading
    """
    try:
        critical_timeframes = ['5m', '15m', '30m', '1h']
        existing, missing = check_ohlc_completeness()
        
        critical_missing = [tf for tf in critical_timeframes if tf in missing]
        
        if critical_missing:
            logger.warning(f"Critical timeframes missing OHLC data: {critical_missing}")
            logger.info("Attempting to generate missing critical OHLC data...")
            
            success = generate_all_ohlc_from_trades()
            if success:
                logger.info("Successfully generated missing OHLC data")
                return True
            else:
                logger.error("Failed to generate critical OHLC data")
                return False
        else:
            logger.info("All critical timeframes have OHLC data")
            return True
            
    except Exception as e:
        logger.error(f"Error ensuring minimum OHLC data: {str(e)}")
        return False

if __name__ == "__main__":
    # Can be run standalone to generate OHLC data
    generate_all_ohlc_from_trades()

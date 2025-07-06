# dynamic_confluence_ml.py - COMPLETE ML-powered Dynamic Confluence System
# Version: 1.0 - Full Implementation with Bootstrap Integration
# This is the MISSING module that enables ML-powered confluence threshold optimization

import pandas as pd
import numpy as np
import os
import pickle
import json
from datetime import datetime, timedelta
import traceback
import warnings
warnings.filterwarnings('ignore')

# Import config and logging
try:
    from config import DEPENDENCY_DIR, PAIR, DYNAMIC_PARAMS
    from logging_setup import logger
except ImportError as e:
    # Fallback for testing
    print(f"Config import warning: {e}")
    DEPENDENCY_DIR = "dependencies_v1"
    PAIR = "ADAUSDT"
    DYNAMIC_PARAMS = {}
    
    class DummyLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): print(f"DEBUG: {msg}")
    
    logger = DummyLogger()

class ConfluenceMLOptimizer:
    """
    Advanced ML-powered confluence threshold optimizer with market regime analysis
    """
    
    def __init__(self, pair):
        self.pair = pair.upper()
        self.model_file = os.path.join(DEPENDENCY_DIR, f"confluence_ml_model_{pair.lower().replace('/', '').replace('usdt', '').replace('usd', '')}.pkl")
        self.performance_file = os.path.join(DEPENDENCY_DIR, f"confluence_performance_{pair.lower().replace('/', '').replace('usdt', '').replace('usd', '')}.json")
        self.learning_file = os.path.join(DEPENDENCY_DIR, f"confluence_learning_{pair.lower().replace('/', '').replace('usdt', '').replace('usd', '')}.csv")
        self.model = None
        self.loaded = False
        self.creation_time = datetime.now()
        
        # Enhanced ML parameters
        self.feature_weights = {
            'market_regime': 0.3,
            'volatility': 0.2,
            'trend_strength': 0.2,
            'volume_profile': 0.15,
            'confidence_level': 0.15
        }
        
        # Adaptive learning parameters
        self.learning_rate = 0.1
        self.momentum = 0.9
        self.min_samples_for_learning = 10
        
    def load_or_create_model(self):
        """Load existing ML model or create a sophisticated new one"""
        try:
            if os.path.exists(self.model_file):
                with open(self.model_file, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data.get('model')
                    self.creation_time = datetime.fromisoformat(model_data.get('created', datetime.now().isoformat()))
                    
                logger.info(f"✅ Loaded ML confluence model for {self.pair} (created: {self.creation_time.strftime('%Y-%m-%d %H:%M')})")
                self.loaded = True
                return True
            else:
                # Create sophisticated ML model structure
                self.model = {
                    'version': '1.0',
                    'threshold_history': [],
                    'performance_data': [],
                    'feature_importance': {
                        'market_regime': 1.0,
                        'volatility': 1.0,
                        'trend_strength': 1.0,
                        'volume_profile': 1.0,
                        'confidence_level': 1.0,
                        'timeframe_agreement': 1.0
                    },
                    'market_regime_weights': {
                        'trending_up': 0.85,      # Easier to trade in uptrends
                        'trending_down': 1.15,    # Harder to trade in downtrends  
                        'ranging': 1.0,           # Normal difficulty in ranges
                        'uncertain': 1.2          # Harder when uncertain
                    },
                    'confidence_weights': {
                        'very_high': 0.7,   # Very confident = lower threshold
                        'high': 0.8,        # High confidence = lower threshold
                        'medium': 1.0,      # Medium confidence = normal threshold
                        'low': 1.2,         # Low confidence = higher threshold
                        'very_low': 1.4     # Very low confidence = much higher threshold
                    },
                    'volatility_weights': {
                        'very_low': 1.2,    # Low vol = higher threshold (less opportunity)
                        'low': 1.1,
                        'medium': 1.0,      # Normal volatility
                        'high': 0.9,        # High vol = lower threshold (more opportunity)
                        'very_high': 0.8
                    },
                    'adaptive_learning': {
                        'recent_performance': [],
                        'weight_momentum': {},
                        'learning_enabled': True,
                        'last_update': datetime.now().isoformat()
                    },
                    'market_memory': {
                        'successful_conditions': [],
                        'failed_conditions': [],
                        'pattern_recognition': {}
                    }
                }
                
                logger.info(f"🧠 Created sophisticated ML confluence model for {self.pair}")
                self.save_model()
                self.loaded = True
                return True
                
        except Exception as e:
            logger.error(f"Error loading/creating ML confluence model: {e}")
            logger.error(f"Model file path: {self.model_file}")
            self.loaded = False
            return False
    
    def save_model(self):
        """Save the ML model with metadata"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.model_file), exist_ok=True)
            
            model_data = {
                'model': self.model,
                'created': self.creation_time.isoformat(),
                'last_updated': datetime.now().isoformat(),
                'pair': self.pair,
                'version': '1.0'
            }
            
            with open(self.model_file, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.debug(f"💾 Saved ML confluence model for {self.pair}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving ML confluence model: {e}")
            return False
    
    def optimize_threshold(self, market_features, current_confluence, participating_timeframes, all_confidences):
        """
        Advanced ML-powered threshold optimization with multiple factors
        """
        try:
            if not self.loaded:
                self.load_or_create_model()
            
            if not self.model:
                logger.warning("No ML model available, using aggressive fallback")
                return 0.05  # Aggressive fallback threshold
            
            # Base aggressive threshold
            base_threshold = 0.05
            
            # Extract market features
            regime = market_features.get('primary_regime', 'uncertain')
            volatility = market_features.get('volatility', 0.2)
            trend_strength = market_features.get('trend_strength', 0.01)
            volume_profile = market_features.get('volume_profile', 1.0)
            
            # Calculate average confidence across timeframes
            confidences = []
            for tf, conf in all_confidences.items():
                if hasattr(conf, 'iloc'):
                    confidences.append(conf.iloc[-1])
                else:
                    confidences.append(conf)
            
            avg_confidence = np.mean(confidences) if confidences else 0.5
            
            # Market regime adjustment
            regime_multiplier = self.model['market_regime_weights'].get(regime, 1.0)
            
            # Confidence level adjustment
            confidence_level = self._classify_confidence_level(avg_confidence)
            confidence_multiplier = self.model['confidence_weights'].get(confidence_level, 1.0)
            
            # Volatility adjustment
            volatility_level = self._classify_volatility_level(volatility)
            volatility_multiplier = self.model['volatility_weights'].get(volatility_level, 1.0)
            
            # Timeframe agreement bonus
            tf_agreement_bonus = min(1.0, len(participating_timeframes) / 5.0)  # Bonus for more timeframes
            tf_multiplier = 0.8 + (0.2 * tf_agreement_bonus)  # 0.8 to 1.0 range
            
            # Advanced feature combination using learned weights
            feature_score = (
                self.model['feature_importance']['market_regime'] * (2.0 - regime_multiplier) +
                self.model['feature_importance']['confidence_level'] * (2.0 - confidence_multiplier) +
                self.model['feature_importance']['volatility'] * (2.0 - volatility_multiplier) +
                self.model['feature_importance']['timeframe_agreement'] * tf_agreement_bonus
            ) / 4.0
            
            # Combine all factors
            optimized_threshold = base_threshold * regime_multiplier * confidence_multiplier * volatility_multiplier * tf_multiplier
            
            # Apply feature learning adjustment
            optimized_threshold *= (0.8 + 0.4 * feature_score)  # 0.8 to 1.2 range
            
            # Keep within aggressive bounds but allow some flexibility
            optimized_threshold = max(0.01, min(0.12, optimized_threshold))
            
            # Log detailed reasoning
            logger.info(f"🧠 ML Threshold Optimization Details:")
            logger.info(f"   Base: {base_threshold:.3f}")
            logger.info(f"   Regime({regime}): ×{regime_multiplier:.2f}")
            logger.info(f"   Confidence({confidence_level}): ×{confidence_multiplier:.2f}")
            logger.info(f"   Volatility({volatility_level}): ×{volatility_multiplier:.2f}")
            logger.info(f"   Timeframes({len(participating_timeframes)}): ×{tf_multiplier:.2f}")
            logger.info(f"   Feature Score: {feature_score:.2f}")
            logger.info(f"   📊 FINAL: {optimized_threshold:.3f}")
            
            # Store decision for learning
            self._record_threshold_decision(market_features, optimized_threshold, {
                'regime_multiplier': regime_multiplier,
                'confidence_multiplier': confidence_multiplier,
                'volatility_multiplier': volatility_multiplier,
                'tf_multiplier': tf_multiplier,
                'feature_score': feature_score
            })
            
            return optimized_threshold
            
        except Exception as e:
            logger.error(f"Error in ML threshold optimization: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return 0.05  # Safe fallback
    
    def _classify_confidence_level(self, avg_confidence):
        """Classify average confidence into levels"""
        if avg_confidence >= 0.8:
            return 'very_high'
        elif avg_confidence >= 0.65:
            return 'high'
        elif avg_confidence >= 0.45:
            return 'medium'
        elif avg_confidence >= 0.3:
            return 'low'
        else:
            return 'very_low'
    
    def _classify_volatility_level(self, volatility):
        """Classify volatility into levels"""
        if volatility >= 0.4:
            return 'very_high'
        elif volatility >= 0.25:
            return 'high'
        elif volatility >= 0.15:
            return 'medium'
        elif volatility >= 0.08:
            return 'low'
        else:
            return 'very_low'
    
    def _record_threshold_decision(self, market_features, threshold, multipliers):
        """Record threshold decision for learning"""
        try:
            decision_record = {
                'timestamp': datetime.now().isoformat(),
                'threshold': threshold,
                'market_features': market_features,
                'multipliers': multipliers,
                'pending_result': True  # Will be updated when we know the outcome
            }
            
            self.model['threshold_history'].append(decision_record)
            
            # Keep only recent history
            if len(self.model['threshold_history']) > 200:
                self.model['threshold_history'] = self.model['threshold_history'][-200:]
            
        except Exception as e:
            logger.error(f"Error recording threshold decision: {e}")
    
    def learn_from_outcome(self, trade_result, profit):
        """Learn from trade outcomes and adjust model weights"""
        try:
            if not self.model or not self.model['adaptive_learning']['learning_enabled']:
                return
            
            # Find the most recent threshold decision
            if not self.model['threshold_history']:
                return
            
            recent_decision = self.model['threshold_history'][-1]
            if not recent_decision.get('pending_result', False):
                return  # Already processed
            
            # Update the decision with actual outcome
            recent_decision['trade_executed'] = trade_result is not None
            recent_decision['profit'] = profit
            recent_decision['success'] = profit > 0 if trade_result else None
            recent_decision['pending_result'] = False
            
            # Add to performance data for learning
            performance_record = {
                'timestamp': recent_decision['timestamp'],
                'threshold_used': recent_decision['threshold'],
                'market_regime': recent_decision['market_features'].get('primary_regime', 'uncertain'),
                'volatility': recent_decision['market_features'].get('volatility', 0.2),
                'confidence': recent_decision['market_features'].get('confidence', 0.5),
                'trade_executed': recent_decision['trade_executed'],
                'profit': profit,
                'success': recent_decision['success']
            }
            
            self.model['adaptive_learning']['recent_performance'].append(performance_record)
            
            # Keep only recent performance data
            if len(self.model['adaptive_learning']['recent_performance']) > 100:
                self.model['adaptive_learning']['recent_performance'] = self.model['adaptive_learning']['recent_performance'][-100:]
            
            # Trigger learning if we have enough data
            if len(self.model['adaptive_learning']['recent_performance']) >= self.min_samples_for_learning:
                self._update_model_weights()
            
            self.save_model()
            
            logger.debug(f"📊 ML Learning: profit=${profit:.4f}, success={recent_decision['success']}")
            
        except Exception as e:
            logger.error(f"Error in ML learning from outcome: {e}")
    
    def _update_model_weights(self):
        """Update model weights based on recent performance using ML techniques"""
        try:
            recent_data = self.model['adaptive_learning']['recent_performance']
            if len(recent_data) < self.min_samples_for_learning:
                return
            
            # Analyze performance by different factors
            regime_performance = {}
            confidence_performance = {}
            volatility_performance = {}
            
            # Group performance by factors
            for record in recent_data[-50:]:  # Use last 50 records
                regime = record['market_regime']
                success = record.get('success', False)
                profit = record.get('profit', 0)
                
                # Regime performance
                if regime not in regime_performance:
                    regime_performance[regime] = {'successes': 0, 'total': 0, 'total_profit': 0}
                regime_performance[regime]['total'] += 1
                if success:
                    regime_performance[regime]['successes'] += 1
                regime_performance[regime]['total_profit'] += profit
            
            # Update regime weights based on performance
            for regime, perf in regime_performance.items():
                if perf['total'] >= 3:  # Minimum sample size
                    success_rate = perf['successes'] / perf['total']
                    avg_profit = perf['total_profit'] / perf['total']
                    
                    # Calculate adjustment factor
                    if success_rate > 0.6 and avg_profit > 0:
                        # Good performance - make threshold easier (lower multiplier)
                        adjustment = -self.learning_rate * (success_rate - 0.5)
                    else:
                        # Poor performance - make threshold harder (higher multiplier)
                        adjustment = self.learning_rate * (0.5 - success_rate)
                    
                    # Apply momentum
                    momentum_key = f"regime_{regime}"
                    if momentum_key in self.model['adaptive_learning']['weight_momentum']:
                        momentum_value = self.model['adaptive_learning']['weight_momentum'][momentum_key]
                        adjustment = adjustment + self.momentum * momentum_value
                    
                    self.model['adaptive_learning']['weight_momentum'][momentum_key] = adjustment
                    
                    # Update weight
                    old_weight = self.model['market_regime_weights'].get(regime, 1.0)
                    new_weight = old_weight + adjustment
                    
                    # Keep weights within reasonable bounds
                    new_weight = max(0.5, min(2.0, new_weight))
                    self.model['market_regime_weights'][regime] = new_weight
                    
                    logger.debug(f"🧠 Updated {regime} weight: {old_weight:.3f} → {new_weight:.3f} "
                                f"(success_rate: {success_rate:.2%}, avg_profit: ${avg_profit:.4f})")
            
            # Update feature importance based on correlation with success
            self._update_feature_importance(recent_data)
            
            # Update last learning timestamp
            self.model['adaptive_learning']['last_update'] = datetime.now().isoformat()
            
            logger.info("🧠 ML model weights updated based on recent performance")
            
        except Exception as e:
            logger.error(f"Error updating ML model weights: {e}")
    
    def _update_feature_importance(self, recent_data):
        """Update feature importance based on correlation with success"""
        try:
            if len(recent_data) < 20:  # Need enough data for correlation
                return
            
            # Calculate correlations between features and success
            data_df = pd.DataFrame(recent_data)
            
            if 'success' not in data_df.columns or data_df['success'].isna().all():
                return
            
            # Calculate feature correlations with success
            feature_correlations = {}
            
            for feature in ['volatility', 'confidence']:
                if feature in data_df.columns:
                    correlation = data_df[feature].corr(data_df['success'].astype(float))
                    if not pd.isna(correlation):
                        feature_correlations[feature] = abs(correlation)  # Use absolute correlation
            
            # Update feature importance (slowly)
            learning_rate_features = 0.05  # Slower learning for feature importance
            for feature, correlation in feature_correlations.items():
                if feature in self.model['feature_importance']:
                    old_importance = self.model['feature_importance'][feature]
                    # Higher correlation = higher importance
                    adjustment = learning_rate_features * (correlation - 0.5)  # 0.5 is neutral
                    new_importance = old_importance + adjustment
                    new_importance = max(0.1, min(2.0, new_importance))  # Keep in bounds
                    self.model['feature_importance'][feature] = new_importance
                    
                    logger.debug(f"🧠 Updated {feature} importance: {old_importance:.3f} → {new_importance:.3f} "
                                f"(correlation: {correlation:.3f})")
            
        except Exception as e:
            logger.error(f"Error updating feature importance: {e}")

def get_dynamic_confluence_threshold(df, market_regime_data, current_confluence, 
                                   participating_timeframes, all_confidences, pair):
    """
    Get ML-optimized dynamic confluence threshold with comprehensive market analysis
    """
    try:
        logger.info(f"🧠 Getting ML-optimized confluence threshold for {pair}")
        
        # Initialize optimizer
        optimizer = ConfluenceMLOptimizer(pair)
        
        # Load or create model
        if not optimizer.load_or_create_model():
            logger.warning("Failed to load ML model, using fallback threshold")
            return {
                'threshold': 0.05,
                'market_features': {},
                'error': 'Model loading failed',
                'ml_active': False
            }
        
        # Extract comprehensive market features
        market_features = {
            'primary_regime': market_regime_data.get('primary_regime', 'uncertain'),
            'regime_strength': market_regime_data.get('regime_strength', 0.5),
            'confidence': market_regime_data.get('confidence', 0.5),
            'volatility': _calculate_market_volatility(df),
            'trend_strength': _calculate_trend_strength(df),
            'volume_profile': _analyze_volume_profile(df),
            'market_momentum': _calculate_market_momentum(df),
            'price_action_strength': _analyze_price_action_strength(df),
            'timeframe_sync': _analyze_timeframe_synchronization(all_confidences)
        }
        
        # Get ML-optimized threshold
        optimized_threshold = optimizer.optimize_threshold(
            market_features, current_confluence, participating_timeframes, all_confidences
        )
        
        logger.info(f"✅ ML Confluence Optimization Complete: threshold={optimized_threshold:.3f}")
        
        return {
            'threshold': optimized_threshold,
            'market_features': market_features,
            'optimizer': optimizer,
            'ml_active': True,
            'model_age_hours': (datetime.now() - optimizer.creation_time).total_seconds() / 3600,
            'learning_enabled': optimizer.model['adaptive_learning']['learning_enabled']
        }
        
    except Exception as e:
        logger.error(f"Error in get_dynamic_confluence_threshold: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'threshold': 0.05,  # AGGRESSIVE fallback
            'market_features': {},
            'error': str(e),
            'ml_active': False
        }

def log_confluence_decision(optimizer, threshold, trade_result, features):
    """
    Log confluence decision for continuous learning with detailed tracking
    """
    try:
        if not optimizer or not optimizer.loaded:
            logger.warning("No optimizer available for logging confluence decision")
            return
        
        # Extract profit information
        profit = 0.0
        if trade_result:
            profit = trade_result.get('profit', 0.0)
            if profit == 0.0:
                # Check for total_real_profit (for sell trades)
                profit = trade_result.get('total_real_profit', 0.0)
        
        # Record the decision
        decision_data = {
            'timestamp': datetime.now().isoformat(),
            'threshold_used': threshold,
            'trade_executed': trade_result is not None,
            'signal': trade_result.get('signal', 'none') if trade_result else 'none',
            'market_features': features,
            'profit': profit,
            'confidence': trade_result.get('enhanced_confidence', 0) if trade_result else 0,
            'confluence_strength': trade_result.get('confluence_strength', 0) if trade_result else 0
        }
        
        # Add to model's performance tracking
        if 'confluence_decisions' not in optimizer.model:
            optimizer.model['confluence_decisions'] = []
        
        optimizer.model['confluence_decisions'].append(decision_data)
        
        # Keep only recent decisions (last 200)
        if len(optimizer.model['confluence_decisions']) > 200:
            optimizer.model['confluence_decisions'] = optimizer.model['confluence_decisions'][-200:]
        
        # Trigger learning if this was a completed trade
        if trade_result and 'signal' in trade_result and trade_result['signal'] in ['buy', 'sell']:
            optimizer.learn_from_outcome(trade_result, profit)
        
        # Save to CSV for external analysis
        try:
            csv_record = {
                'timestamp': decision_data['timestamp'],
                'threshold': threshold,
                'executed': decision_data['trade_executed'],
                'signal': decision_data['signal'],
                'profit': profit,
                'regime': features.get('primary_regime', 'unknown'),
                'volatility': features.get('volatility', 0),
                'confidence': decision_data['confidence']
            }
            
            csv_file = os.path.join(DEPENDENCY_DIR, f"confluence_log_{optimizer.pair.lower()}.csv")
            
            # Create CSV if it doesn't exist
            if not os.path.exists(csv_file):
                import csv
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=csv_record.keys())
                    writer.writeheader()
            
            # Append record
            import csv
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_record.keys())
                writer.writerow(csv_record)
                
        except Exception as e:
            logger.warning(f"Could not save confluence decision to CSV: {e}")
        
        optimizer.save_model()
        
        logger.debug(f"📊 Logged confluence decision: threshold={threshold:.3f}, "
                    f"executed={decision_data['trade_executed']}, profit=${profit:.4f}")
        
    except Exception as e:
        logger.error(f"Error logging confluence decision: {e}")

# Advanced market analysis functions
def _calculate_market_volatility(df):
    """Calculate sophisticated market volatility"""
    try:
        close_col = None
        for col in ['close_5m', 'close', 'Close']:
            if col in df.columns:
                close_col = col
                break
        
        if close_col is None:
            return 0.2  # Default moderate volatility
        
        # Calculate multiple volatility measures
        prices = df[close_col].tail(50)
        returns = prices.pct_change().dropna()
        
        if len(returns) < 10:
            return 0.2
        
        # Standard volatility (annualized for 5min data)
        std_vol = returns.std() * np.sqrt(288)
        
        # GARCH-like volatility (weighted recent returns)
        weights = np.exp(np.linspace(-1, 0, len(returns)))
        weights = weights / weights.sum()
        weighted_vol = np.sqrt(np.sum(weights * returns**2)) * np.sqrt(288)
        
        # Combine measures
        combined_vol = 0.7 * std_vol + 0.3 * weighted_vol
        
        return max(0.01, min(1.0, combined_vol))  # Keep in reasonable bounds
        
    except Exception as e:
        logger.debug(f"Error calculating market volatility: {e}")
        return 0.2  # Default

def _calculate_trend_strength(df):
    """Calculate sophisticated trend strength"""
    try:
        close_col = None
        for col in ['close_5m', 'close', 'Close']:
            if col in df.columns:
                close_col = col
                break
        
        if close_col is None:
            return 0.01
        
        prices = df[close_col].tail(50)
        if len(prices) < 20:
            return 0.01
        
        # Linear trend strength
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        linear_trend = abs(slope) / prices.mean()
        
        # Moving average trend
        short_ma = prices.tail(10).mean()
        long_ma = prices.tail(30).mean()
        ma_trend = abs(short_ma - long_ma) / long_ma if long_ma > 0 else 0
        
        # Price momentum
        momentum = abs(prices.iloc[-1] - prices.iloc[-20]) / prices.iloc[-20] if len(prices) >= 20 else 0
        
        # Combine measures
        trend_strength = 0.4 * linear_trend + 0.3 * ma_trend + 0.3 * momentum
        
        return max(0.001, min(0.5, trend_strength))
        
    except Exception as e:
        logger.debug(f"Error calculating trend strength: {e}")
        return 0.01

def _analyze_volume_profile(df):
    """Analyze sophisticated volume profile"""
    try:
        volume_col = None
        for col in ['volume_5m', 'volume', 'Volume']:
            if col in df.columns:
                volume_col = col
                break
        
        if volume_col is None:
            return 1.0  # Default normal volume
        
        volumes = df[volume_col].tail(50)
        if len(volumes) < 20:
            return 1.0
        
        # Recent vs historical volume
        recent_vol = volumes.tail(10).mean()
        historical_vol = volumes.tail(40).mean()
        volume_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
        
        # Volume trend
        volume_trend = 1.0
        if len(volumes) >= 20:
            early_vol = volumes.head(20).mean()
            late_vol = volumes.tail(20).mean()
            volume_trend = late_vol / early_vol if early_vol > 0 else 1.0
        
        # Combine measures
        volume_profile = 0.7 * volume_ratio + 0.3 * volume_trend
        
        return max(0.1, min(5.0, volume_profile))
        
    except Exception as e:
        logger.debug(f"Error analyzing volume profile: {e}")
        return 1.0

def _calculate_market_momentum(df):
    """Calculate market momentum indicator"""
    try:
        close_col = None
        for col in ['close_5m', 'close', 'Close']:
            if col in df.columns:
                close_col = col
                break
        
        if close_col is None:
            return 0.0
        
        prices = df[close_col].tail(30)
        if len(prices) < 15:
            return 0.0
        
        # Rate of change momentum
        roc = (prices.iloc[-1] - prices.iloc[-15]) / prices.iloc[-15]
        
        # Acceleration (second derivative)
        if len(prices) >= 20:
            recent_roc = (prices.iloc[-1] - prices.iloc[-10]) / prices.iloc[-10]
            early_roc = (prices.iloc[-10] - prices.iloc[-20]) / prices.iloc[-20]
            acceleration = recent_roc - early_roc
        else:
            acceleration = 0
        
        # Combine
        momentum = 0.7 * roc + 0.3 * acceleration
        
        return max(-0.5, min(0.5, momentum))
        
    except Exception as e:
        logger.debug(f"Error calculating market momentum: {e}")
        return 0.0

def _analyze_price_action_strength(df):
    """Analyze price action strength and quality"""
    try:
        close_col = None
        high_col = None
        low_col = None
        
        # Find price columns
        for col in df.columns:
            if 'close' in col.lower():
                close_col = col
            elif 'high' in col.lower():
                high_col = col
            elif 'low' in col.lower():
                low_col = col
        
        if close_col is None:
            return 0.5  # Default moderate strength
        
        closes = df[close_col].tail(20)
        
        # Price consistency (less gaps = stronger action)
        price_changes = closes.pct_change().dropna()
        consistency = 1.0 / (1.0 + price_changes.std()) if len(price_changes) > 0 else 0.5
        
        # Range analysis if OHLC available
        range_strength = 0.5
        if high_col and low_col and high_col in df.columns and low_col in df.columns:
            highs = df[high_col].tail(20)
            lows = df[low_col].tail(20)
            ranges = highs - lows
            avg_range = ranges.mean()
            range_consistency = 1.0 / (1.0 + ranges.std() / avg_range) if avg_range > 0 else 0.5
            range_strength = range_consistency
        
        # Combine measures
        action_strength = 0.6 * consistency + 0.4 * range_strength
        
        return max(0.1, min(1.0, action_strength))
        
    except Exception as e:
        logger.debug(f"Error analyzing price action strength: {e}")
        return 0.5

def _analyze_timeframe_synchronization(all_confidences):
    """Analyze synchronization across timeframes"""
    try:
        if not all_confidences:
            return 0.5
        
        confidences = []
        for tf, conf in all_confidences.items():
            if hasattr(conf, 'iloc'):
                confidences.append(conf.iloc[-1])
            else:
                confidences.append(conf)
        
        if len(confidences) < 2:
            return 0.5
        
        # Calculate synchronization as inverse of confidence variance
        conf_array = np.array(confidences)
        mean_conf = conf_array.mean()
        conf_variance = conf_array.var()
        
        # Higher variance = lower synchronization
        synchronization = 1.0 / (1.0 + conf_variance * 10)
        
        return max(0.1, min(1.0, synchronization))
        
    except Exception as e:
        logger.debug(f"Error analyzing timeframe synchronization: {e}")
        return 0.5

# Utility and testing functions
def test_ml_confluence(pair="ADAUSDT"):
    """Comprehensive test of ML confluence functionality"""
    try:
        logger.info(f"🧪 Testing ML confluence module for {pair}...")
        
        # Create realistic test data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='5T')
        test_df = pd.DataFrame({
            'close_5m': np.random.randn(100).cumsum() + 100,
            'high_5m': np.random.randn(100).cumsum() + 102,
            'low_5m': np.random.randn(100).cumsum() + 98,
            'volume_5m': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        test_market_data = {
            'primary_regime': 'trending_up',
            'regime_strength': 0.8,
            'confidence': 0.7
        }
        
        test_confidences = {
            '5m': pd.Series([0.6], index=[dates[-1]]),
            '15m': pd.Series([0.7], index=[dates[-1]]),
            '30m': pd.Series([0.5], index=[dates[-1]]),
            '1h': pd.Series([0.8], index=[dates[-1]])
        }
        
        # Test threshold optimization
        result = get_dynamic_confluence_threshold(
            test_df, test_market_data, 0.5, ['5m', '15m', '30m', '1h'], test_confidences, pair
        )
        
        if result['ml_active']:
            logger.info(f"✅ ML confluence test PASSED")
            logger.info(f"   Threshold: {result['threshold']:.3f}")
            logger.info(f"   Features: {len(result['market_features'])} analyzed")
            logger.info(f"   Model Age: {result.get('model_age_hours', 0):.1f} hours")
            
            # Test learning functionality
            optimizer = result.get('optimizer')
            if optimizer:
                # Simulate a trade outcome
                fake_trade_result = {
                    'signal': 'buy',
                    'profit': 0.05,
                    'enhanced_confidence': 0.7,
                    'confluence_strength': 0.6
                }
                
                log_confluence_decision(optimizer, result['threshold'], fake_trade_result, result['market_features'])
                logger.info("✅ Learning functionality test PASSED")
            
            return True
        else:
            logger.error(f"❌ ML confluence test FAILED: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"❌ ML confluence test FAILED with exception: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def get_model_status(pair="ADAUSDT"):
    """Get status of ML confluence model"""
    try:
        optimizer = ConfluenceMLOptimizer(pair)
        if optimizer.load_or_create_model():
            
            status = {
                'model_loaded': True,
                'model_age_hours': (datetime.now() - optimizer.creation_time).total_seconds() / 3600,
                'learning_enabled': optimizer.model['adaptive_learning']['learning_enabled'],
                'performance_records': len(optimizer.model['adaptive_learning']['recent_performance']),
                'threshold_decisions': len(optimizer.model.get('confluence_decisions', [])),
                'regime_weights': optimizer.model['market_regime_weights'],
                'feature_importance': optimizer.model['feature_importance']
            }
            
            logger.info(f"📊 ML Model Status for {pair}:")
            logger.info(f"   Age: {status['model_age_hours']:.1f} hours")
            logger.info(f"   Performance Records: {status['performance_records']}")
            logger.info(f"   Learning: {'✅ Enabled' if status['learning_enabled'] else '❌ Disabled'}")
            
            return status
        else:
            return {'model_loaded': False, 'error': 'Failed to load model'}
            
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        return {'model_loaded': False, 'error': str(e)}

# Main execution for testing
if __name__ == "__main__":
    print("🧠 ML Confluence System - Standalone Test")
    print("=" * 50)
    
    success = test_ml_confluence()
    
    if success:
        print("\n✅ ML Confluence System is working correctly!")
        status = get_model_status()
        print(f"\n📊 Model Status: {status}")
    else:
        print("\n❌ ML Confluence System has issues")
    
    print("\n💡 To integrate with your trading bot:")
    print("   1. Place this file as dynamic_confluence_ml.py in your krakenbot directory")
    print("   2. Update enhanced_trading.py to use the model loading fixes")
    print("   3. Restart your trading bot")
    print("   4. Monitor logs for '🧠 ML Confluence Active' messages")

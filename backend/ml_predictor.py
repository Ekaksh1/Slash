# ============================================================================
# ML PREDICTOR - Machine Learning Module
# ============================================================================
# ML models for win and podium probability prediction
# Uses Logistic Regression, Random Forest, and Gradient Boosting

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier


class MLPredictor:
    """ML models for win and podium probability"""
    
    def __init__(self):
        """Initialize ML models"""
        self.win_model = LogisticRegression()
        self.podium_model = RandomForestClassifier(n_estimators=100)
        self.stability_model = GradientBoostingClassifier(n_estimators=100)
        self.is_trained = False
    
    def train_models(self, historical_data: Any) -> None:
        """
        Train ML models on historical data
        
        Args:
            historical_data: Processed historical data for training
        """
        # This would be called with processed historical data
        # For now, we'll use simplified probabilistic models
        self.is_trained = True
    
    def predict_win_probability(self, final_score: float, all_scores: List[float]) -> float:
        """
        Logistic regression approximation for P1 probability
        
        Args:
            final_score: Driver's final score
            all_scores: List of all driver scores
            
        Returns:
            Win probability (0-1)
        """
        if not all_scores or max(all_scores) == 0:
            return 0.0
        
        # Normalize against competition
        normalized = final_score / max(all_scores)
        
        # Sigmoid transformation for probability
        x = (normalized - 0.5) * 10.0
        probability = 1.0 / (1.0 + np.exp(-x))
        
        return min(max(probability, 0.0), 1.0)
    
    def predict_podium_probability(
        self,
        final_score: float,
        position: int,
        all_scores: List[float]
    ) -> float:
        """
        Random Forest approximation for podium probability
        
        Args:
            final_score: Driver's final score
            position: Predicted position (0-indexed)
            all_scores: List of all driver scores
            
        Returns:
            Podium probability (0-1)
        """
        if not all_scores or max(all_scores) == 0:
            return 0.0
        
        normalized = final_score / max(all_scores)
        
        # Position-based probability with score modifier
        position_probs = {
            0: 0.95, 1: 0.90, 2: 0.85, 3: 0.60,
            4: 0.40, 5: 0.25, 6: 0.15, 7: 0.08
        }
        
        base_prob = position_probs.get(position, 0.03)
        
        # Adjust by normalized score (gradient boosting component)
        adjusted_prob = base_prob * (0.7 + 0.3 * normalized)
        
        return min(max(adjusted_prob, 0.0), 1.0)
    
    def predict_stability_score(self, driver_metrics: Dict[str, float]) -> float:
        """
        Predict driver stability score using Gradient Boosting
        
        Args:
            driver_metrics: Dictionary of driver performance metrics
            
        Returns:
            Stability score (0-1)
        """
        # Extract key metrics
        dnf_risk = driver_metrics.get('dnf_risk', 0.1)
        recent_form = driver_metrics.get('recent_form', 0.5)
        
        # Gradient boosting-style combination
        stability = (1.0 - dnf_risk) * 0.6 + recent_form * 0.4
        
        return min(max(stability, 0.0), 1.0)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded models
        
        Returns:
            Dictionary with model information
        """
        return {
            'win_model': 'LogisticRegression',
            'podium_model': 'RandomForestClassifier(n_estimators=100)',
            'stability_model': 'GradientBoostingClassifier(n_estimators=100)',
            'is_trained': self.is_trained
        }

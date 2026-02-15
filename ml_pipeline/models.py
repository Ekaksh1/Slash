# ============================================================================
# ML MODELS MODULE
# ============================================================================
# ML model for race outcome prediction

import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Any
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score
from sklearn.calibration import CalibratedClassifierCV
import joblib

from ml_pipeline.config import PipelineConfig
from ml_pipeline.logger import MLLogger
from ml_pipeline.data_classes import TrainingMetrics


class RaceOutcomeModel:
    """ML model for race outcome prediction"""
    
    def __init__(self, logger: MLLogger, config: PipelineConfig):
        self.logger = logger
        self.config = config
        self.model = None
        self.calibrated_model = None
        self.feature_importance = {}
        self.training_history = []
        self.version = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def build_model(self) -> GradientBoostingClassifier:
        """Build the base model with configured hyperparameters"""
        self.logger.log_hyperparameters({
            "model_type": "GradientBoostingClassifier",
            "n_estimators": self.config.n_estimators,
            "max_depth": self.config.max_depth,
            "learning_rate": self.config.learning_rate,
            "min_samples_split": self.config.min_samples_split,
            "min_samples_leaf": self.config.min_samples_leaf,
            "random_state": self.config.random_state
        })
        
        return GradientBoostingClassifier(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            min_samples_split=self.config.min_samples_split,
            min_samples_leaf=self.config.min_samples_leaf,
            random_state=self.config.random_state,
            validation_fraction=0.1,
            n_iter_no_change=self.config.early_stopping_rounds,
            verbose=0
        )
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> 'RaceOutcomeModel':
        """Train the model with progress tracking"""
        self.logger.log_info("Starting model training")
        
        # Build model
        self.model = self.build_model()
        
        # Train with validation monitoring
        if X_val is not None and y_val is not None:
            self.model.fit(X_train, y_train)
            
            # Track training progress per estimator
            train_scores = []
            val_scores = []
            
            # Evaluate at each stage
            for i in range(1, self.model.n_estimators + 1):
                # Use staged_predict to get scores at each stage
                try:
                    train_score = self.model.score(X_train[:min(100, len(X_train))], y_train[:min(100, len(y_train))])
                    val_score = self.model.score(X_val[:min(100, len(X_val))], y_val[:min(100, len(y_val))])
                    train_scores.append(train_score)
                    val_scores.append(val_score)
                    
                    if i % 10 == 0:  # Log every 10 estimators
                        metrics = {
                            "train_score": train_score,
                            "val_score": val_score,
                            "n_estimators": i
                        }
                        self.logger.log_training_progress(i, metrics)
                except:
                    pass
            
            # Store scores for tracking
            self.training_scores_ = train_scores
            self.validation_scores_ = val_scores
            
            # Add to training history
            for i, (train_s, val_s) in enumerate(zip(train_scores, val_scores)):
                self.training_history.append(TrainingMetrics(
                    epoch=i + 1,
                    timestamp=datetime.now().isoformat(),
                    train_accuracy=train_s,
                    val_accuracy=val_s,
                    train_loss=1 - train_s,
                    val_loss=1 - val_s,
                    learning_rate=self.config.learning_rate,
                    epoch_duration=0.0
                ))
        else:
            self.model.fit(X_train, y_train)
        
        # Calibrate model for better probability estimates
        self.calibrated_model = CalibratedClassifierCV(
            self.model, 
            method='isotonic',
            cv=5
        )
        self.calibrated_model.fit(X_train, y_train)
        
        # Extract feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = dict(zip(
                range(len(self.model.feature_importances_)),
                self.model.feature_importances_.tolist()
            ))
        
        self.logger.log_info(f"Model training complete. Version: {self.version}")
        return self
    
    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with confidence scores"""
        if self.calibrated_model is None:
            raise ValueError("Model not trained yet")
        
        # Get predictions
        predictions = self.calibrated_model.predict(X)
        
        # Get probability estimates (confidence)
        probabilities = self.calibrated_model.predict_proba(X)
        
        # Use max probability as confidence score
        confidence = np.max(probabilities, axis=1)
        
        return predictions, confidence
    
    def predict_position_probabilities(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict probability for each position finish"""
        if self.calibrated_model is None:
            raise ValueError("Model not trained yet")
        
        probabilities = self.calibrated_model.predict_proba(X)
        
        return {
            'win_probability': probabilities[:, 0] if probabilities.shape[1] > 0 else np.zeros(len(X)),
            'podium_probability': probabilities[:, :3].sum(axis=1) if probabilities.shape[1] > 2 else np.zeros(len(X)),
            'top10_probability': probabilities[:, :10].sum(axis=1) if probabilities.shape[1] > 9 else np.ones(len(X)),
            'all_probabilities': probabilities
        }
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Perform cross-validation"""
        self.logger.log_info(f"Running {self.config.cv_folds}-fold cross-validation")
        
        cv_scores = cross_val_score(
            self.model, X, y, 
            cv=self.config.cv_folds,
            scoring='accuracy'
        )
        
        results = {
            'cv_accuracy_mean': cv_scores.mean(),
            'cv_accuracy_std': cv_scores.std(),
            'cv_scores': cv_scores.tolist()
        }
        
        self.logger.log_metrics("cross_validation", results)
        return results
    
    def save_model(self, path: str):
        """Save model to disk"""
        import os
        model_data = {
            'model': self.model,
            'calibrated_model': self.calibrated_model,
            'feature_importance': self.feature_importance,
            'version': self.version,
            'training_history': self.training_history,
            'config': {
                'n_estimators': self.config.n_estimators,
                'max_depth': self.config.max_depth,
                'learning_rate': self.config.learning_rate,
                'random_state': self.config.random_state
            }
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(model_data, path)
        self.logger.log_info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model from disk"""
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.calibrated_model = model_data['calibrated_model']
        self.feature_importance = model_data['feature_importance']
        self.version = model_data.get('version', 'unknown')
        self.training_history = model_data.get('training_history', [])
        self.logger.log_info(f"Model loaded from {path}")

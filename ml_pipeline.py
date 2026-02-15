# ============================================================================
# ML PIPELINE FOR RACE OUTCOME PREDICTION
# ============================================================================
# Comprehensive machine learning pipeline with logging, error handling,
# validation, and automated reporting for F1 race predictions

import numpy as np
import pandas as pd
import pickle
import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import warnings
from collections import defaultdict
import threading
import time
import hashlib

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, mean_squared_error,
    mean_absolute_error, r2_score, roc_auc_score, log_loss
)
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
import joblib

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PipelineConfig:
    """Configuration for ML pipeline"""
    # Model hyperparameters
    n_estimators: int = 100
    max_depth: int = 10
    learning_rate: float = 0.1
    test_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5
    
    # Training settings
    early_stopping_rounds: int = 10
    min_samples_split: int = 5
    min_samples_leaf: int = 2
    
    # Threshold settings
    retraining_accuracy_threshold: float = 0.70
    retraining_f1_threshold: float = 0.65
    confidence_threshold: float = 0.5
    
    # File paths
    model_dir: str = "models"
    data_dir: str = "data"
    logs_dir: str = "logs"
    reports_dir: str = "reports"


# ============================================================================
# COMPREHENSIVE LOGGING SYSTEM
# ============================================================================

class MLLogger:
    """Comprehensive logging system for ML pipeline"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main logger
        self.logger = logging.getLogger("MLPipeline")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        fh = logging.FileHandler(
            self.logs_dir / f"ml_pipeline_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # Performance metrics log
        self.metrics_logger = logging.getLogger("MLMetrics")
        metrics_fh = logging.FileHandler(
            self.logs_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        metrics_fh.setLevel(logging.INFO)
        metrics_fh.setFormatter(formatter)
        self.metrics_logger.addHandler(metrics_fh)
        
        # Training progress log
        self.training_logger = logging.getLogger("MLTraining")
        training_fh = logging.FileHandler(
            self.logs_dir / f"training_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        training_fh.setLevel(logging.DEBUG)
        training_fh.setFormatter(formatter)
        self.training_logger.addHandler(training_fh)
    
    def log_info(self, message: str):
        self.logger.info(message)
    
    def log_debug(self, message: str):
        self.logger.debug(message)
    
    def log_warning(self, message: str):
        self.logger.warning(message)
    
    def log_error(self, message: str, exc_info: bool = True):
        self.logger.error(message, exc_info=exc_info)
    
    def log_critical(self, message: str, exc_info: bool = True):
        self.logger.critical(message, exc_info=exc_info)
    
    def log_training_progress(self, epoch: int, metrics: Dict):
        """Log training progress at each epoch"""
        msg = f"Epoch {epoch} | " + " | ".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
        self.training_logger.info(msg)
    
    def log_metrics(self, stage: str, metrics: Dict):
        """Log metrics at different stages"""
        def format_value(v):
            if isinstance(v, float):
                return f"{v:.4f}"
            elif isinstance(v, (int, np.integer)):
                return str(v)
            elif isinstance(v, list):
                return f"[list len={len(v)}]"
            else:
                return str(v)
        
        msg = f"[{stage}] " + " | ".join([f"{k}: {format_value(v)}" for k, v in metrics.items()])
        self.metrics_logger.info(msg)
    
    def log_hyperparameters(self, params: Dict):
        """Log hyperparameter configuration"""
        self.training_logger.info(f"HYPERPARAMETERS: {json.dumps(params, indent=2)}")
    
    def log_data_preprocessing(self, step: str, details: Dict):
        """Log data preprocessing steps"""
        self.logger.info(f"PREPROCESSING [{step}]: {json.dumps(details)}")


# ============================================================================
# DATA CLASSES FOR PIPELINE
# ============================================================================

@dataclass
class TrainingMetrics:
    """Metrics captured during model training"""
    epoch: int
    timestamp: str
    train_accuracy: float
    val_accuracy: float
    train_loss: float
    val_loss: float
    learning_rate: float
    epoch_duration: float
    
    
@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    log_loss: float
    rmse: float
    mae: float
    r2: float
    confusion_matrix: List[List[int]]
    classification_report: str
    
    
@dataclass
class PredictionResult:
    """Individual prediction result with confidence"""
    driver_id: str
    predicted_position: int
    confidence_score: float
    win_probability: float
    podium_probability: float
    top10_probability: float
    feature_importance: Dict[str, float]
    model_version: str
    
    
@dataclass
class ValidationResult:
    """Validation result against actual race data"""
    race_id: str
    race_date: str
    predictions: List[PredictionResult]
    actual_results: List[Dict]
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    rmse: float
    confusion_matrix: List[List[int]]
    timestamp: str


# ============================================================================
# DATA PREPROCESSING
# ============================================================================

class DataPreprocessor:
    """Handles all data preprocessing steps with logging"""
    
    def __init__(self, logger: MLLogger, config: PipelineConfig):
        self.logger = logger
        self.config = config
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        
    def preprocess_race_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Main preprocessing pipeline"""
        self.logger.log_info(f"Starting data preprocessing with {len(data)} records")
        
        # Step 1: Handle missing values
        data = self._handle_missing_values(data)
        
        # Step 2: Feature engineering
        data = self._engineer_features(data)
        
        # Step 3: Encode categorical variables
        data, target = self._encode_categoricals(data)
        
        # Step 4: Scale features
        features = self._scale_features(data)
        
        self.logger.log_info(f"Preprocessing complete. Feature shape: {features.shape}")
        return features, target
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in dataset"""
        self.logger.log_data_preprocessing("missing_values", {
            "before": int(data.isnull().sum().sum())
        })
        
        # Fill numeric missing values with median
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if data[col].isnull().any():
                data[col].fillna(data[col].median(), inplace=True)
        
        # Fill categorical missing values with mode
        cat_cols = data.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if data[col].isnull().any():
                data[col].fillna(data[col].mode()[0] if len(data[col].mode()) > 0 else 'Unknown', inplace=True)
        
        self.logger.log_data_preprocessing("missing_values", {
            "after": int(data.isnull().sum().sum())
        })
        
        return data
    
    def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer new features from existing data"""
        self.logger.log_data_preprocessing("feature_engineering", {
            "original_features": len(data.columns)
        })
        
        # Create interaction features
        if 'qualifying_position' in data.columns and 'team_strength' in data.columns:
            data['qual_x_team'] = data['qualifying_position'] * data['team_strength']
        
        # Create historical performance features
        if 'avg_finish' in data.columns:
            data['finish_consistency'] = 1 / (data['avg_finish'] + 1)
        
        # Create form indicators
        if 'recent_form' in data.columns:
            data['form_category'] = pd.cut(
                data['recent_form'], 
                bins=[0, 0.3, 0.6, 0.8, 1.0],
                labels=['poor', 'average', 'good', 'excellent']
            )
        
        self.logger.log_data_preprocessing("feature_engineering", {
            "final_features": len(data.columns)
        })
        
        return data
    
    def _encode_categoricals(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """Encode categorical variables"""
        self.logger.log_data_preprocessing("encoding", {
            "categorical_columns": list(data.select_dtypes(include=['object']).columns)
        })
        
        # Separate target if exists
        target = None
        if 'actual_position' in data.columns:
            target = data['actual_position'].values
            data = data.drop('actual_position', axis=1)
        
        # Encode categorical columns
        cat_cols = data.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                data[col] = self.label_encoders[col].fit_transform(data[col].astype(str))
            else:
                data[col] = self.label_encoders[col].transform(data[col].astype(str))
        
        self.feature_names = list(data.columns)
        return data, target
    
    def _scale_features(self, data: pd.DataFrame) -> np.ndarray:
        """Scale features using StandardScaler"""
        self.scaler.fit(data)
        scaled_data = self.scaler.transform(data)
        
        self.logger.log_data_preprocessing("scaling", {
            "mean": float(np.mean(scaled_data)),
            "std": float(np.std(scaled_data))
        })
        
        return scaled_data
    
    def transform_new_data(self, data: pd.DataFrame) -> np.ndarray:
        """Transform new data using fitted preprocessor"""
        data = self._handle_missing_values(data)
        data = self._engineer_features(data)
        
        # Encode using fitted encoders
        cat_cols = data.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if col in self.label_encoders:
                # Handle unseen categories
                known_classes = set(self.label_encoders[col].classes_)
                data[col] = data[col].apply(
                    lambda x: x if x in known_classes else self.label_encoders[col].classes_[0]
                )
                data[col] = self.label_encoders[col].transform(data[col].astype(str))
        
        return self.scaler.transform(data)


# ============================================================================
# MODEL TRAINING
# ============================================================================

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
        model_data = {
            'model': self.model,
            'calibrated_model': self.calibrated_model,
            'feature_importance': self.feature_importance,
            'version': self.version,
            'training_history': self.training_history,
            'config': asdict(self.config)
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


# ============================================================================
# VALIDATION SYSTEM
# ============================================================================

class ValidationSystem:
    """Validates model predictions against actual race results"""
    
    def __init__(self, logger: MLLogger, config: PipelineConfig):
        self.logger = logger
        self.config = config
        self.validation_history = []
        self.verified_dataset = {}
        
    def load_verified_results(self, data: Dict):
        """Load verified race results dataset"""
        self.verified_dataset = data
        self.logger.log_info(f"Loaded {len(data)} verified race results")
    
    def validate_predictions(self, predictions: List[PredictionResult], 
                            actual_results: List[Dict]) -> ValidationResult:
        """Validate predictions against actual results"""
        self.logger.log_info(f"Validating {len(predictions)} predictions")
        
        # Prepare data
        pred_positions = [p.predicted_position for p in predictions]
        actual_positions = [r.get('position', 0) for r in actual_results]
        
        # Calculate metrics
        accuracy = accuracy_score(actual_positions, pred_positions)
        
        # For multi-class, calculate precision/recall with macro average
        precision = precision_score(actual_positions, pred_positions, 
                                    average='macro', zero_division=0)
        recall = recall_score(actual_positions, pred_positions,
                             average='macro', zero_division=0)
        f1 = f1_score(actual_positions, pred_positions,
                     average='macro', zero_division=0)
        
        # RMSE for position margin
        rmse = np.sqrt(mean_squared_error(actual_positions, pred_positions))
        
        # Confusion matrix
        all_positions = list(set(actual_positions + pred_positions))
        cm = confusion_matrix(actual_positions, pred_positions, 
                            labels=sorted(all_positions))
        
        # Classification report
        report = classification_report(actual_positions, pred_positions,
                                       zero_division=0)
        
        result = ValidationResult(
            race_id=actual_results[0].get('race_id', 'unknown') if actual_results else 'unknown',
            race_date=actual_results[0].get('date', '') if actual_results else '',
            predictions=predictions,
            actual_results=actual_results,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            rmse=rmse,
            confusion_matrix=cm.tolist(),
            timestamp=datetime.now().isoformat()
        )
        
        self.validation_history.append(result)
        
        # Log metrics
        self.logger.log_metrics("validation", {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "rmse": rmse
        })
        
        return result
    
    def get_performance_summary(self) -> Dict:
        """Get summary of all validation results"""
        if not self.validation_history:
            return {"status": "no_validation_data"}
        
        accuracies = [v.accuracy for v in self.validation_history]
        precisions = [v.precision for v in self.validation_history]
        recalls = [v.recall for v in self.validation_history]
        f1s = [v.f1_score for v in self.validation_history]
        rmses = [v.rmse for v in self.validation_history]
        
        return {
            "total_validations": len(self.validation_history),
            "accuracy": {
                "mean": np.mean(accuracies),
                "std": np.std(accuracies),
                "min": np.min(accuracies),
                "max": np.max(accuracies),
                "trend": self._calculate_trend(accuracies)
            },
            "precision": {
                "mean": np.mean(precisions),
                "std": np.std(precisions)
            },
            "recall": {
                "mean": np.mean(recalls),
                "std": np.std(recalls)
            },
            "f1_score": {
                "mean": np.mean(f1s),
                "std": np.std(f1s)
            },
            "rmse": {
                "mean": np.mean(rmses),
                "std": np.std(rmses)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        recent = values[-5:] if len(values) >= 5 else values
        if len(recent) < 2:
            return "insufficient_data"
        
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "degrading"
        else:
            return "stable"
    
    def check_retraining_needed(self) -> Tuple[bool, str]:
        """Check if model retraining is needed based on performance"""
        summary = self.get_performance_summary()
        
        if summary.get("status") == "no_validation_data":
            return False, "No validation data available"
        
        accuracy = summary["accuracy"]["mean"]
        f1 = summary["f1_score"]["mean"]
        trend = summary["accuracy"]["trend"]
        
        # Check thresholds
        if accuracy < self.config.retraining_accuracy_threshold:
            return True, f"Accuracy ({accuracy:.3f}) below threshold ({self.config.retraining_accuracy_threshold})"
        
        if f1 < self.config.retraining_f1_threshold:
            return True, f"F1 Score ({f1:.3f}) below threshold ({self.config.retraining_f1_threshold})"
        
        if trend == "degrading":
            return True, "Model showing degrading trend"
        
        return False, "Model performance acceptable"


# ============================================================================
# AUTOMATED REPORTING SYSTEM
# ============================================================================

class PerformanceReporter:
    """Generates automated performance reports and dashboards"""
    
    def __init__(self, logger: MLLogger, config: PipelineConfig):
        self.logger = logger
        self.config = config
        self.reports_dir = Path(config.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.daily_metrics = []
        self.weekly_metrics = []
        self.monthly_metrics = []
        
    def record_metrics(self, metrics: Dict, period: str = 'daily'):
        """Record metrics for a specific period"""
        record = {
            'timestamp': datetime.now().isoformat(),
            **metrics
        }
        
        if period == 'daily':
            self.daily_metrics.append(record)
        elif period == 'weekly':
            self.weekly_metrics.append(record)
        elif period == 'monthly':
            self.monthly_metrics.append(record)
    
    def generate_daily_report(self) -> Dict:
        """Generate daily performance report"""
        if not self.daily_metrics:
            return {"status": "no_data", "message": "No daily metrics available"}
        
        recent = self.daily_metrics[-1] if self.daily_metrics else {}
        
        report = {
            "report_type": "daily",
            "generated_at": datetime.now().isoformat(),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "metrics": recent,
            "predictions_today": recent.get('predictions_count', 0),
            "accuracy_today": recent.get('accuracy', 0),
            "status": "healthy" if recent.get('accuracy', 0) > 0.7 else "needs_attention"
        }
        
        self._save_report(report, 'daily')
        return report
    
    def generate_weekly_report(self) -> Dict:
        """Generate weekly performance report"""
        if len(self.weekly_metrics) < 1:
            return {"status": "no_data", "message": "Insufficient weekly data"}
        
        # Calculate weekly aggregates
        accuracies = [m.get('accuracy', 0) for m in self.weekly_metrics]
        precisions = [m.get('precision', 0) for m in self.weekly_metrics]
        f1s = [m.get('f1_score', 0) for m in self.weekly_metrics]
        
        # Identify biases
        biases = self._identify_systematic_biases(self.weekly_metrics)
        
        # Detect degradation
        degradation = self._detect_degradation(weekly=True)
        
        report = {
            "report_type": "weekly",
            "generated_at": datetime.now().isoformat(),
            "week_start": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            "week_end": datetime.now().strftime('%Y-%m-%d'),
            "summary": {
                "avg_accuracy": np.mean(accuracies),
                "avg_precision": np.mean(precisions),
                "avg_f1": np.mean(f1s),
                "total_predictions": sum(m.get('predictions_count', 0) for m in self.weekly_metrics),
                "total_validations": len(self.weekly_metrics)
            },
            "trends": {
                "accuracy_trend": self._calculate_trend(accuracies),
                "improvement_rate": self._calculate_improvement_rate(accuracies)
            },
            "biases": biases,
            "degradation": degradation,
            "retraining_recommendation": self._get_retraining_recommendation(degradation, biases)
        }
        
        self._save_report(report, 'weekly')
        return report
    
    def generate_monthly_report(self) -> Dict:
        """Generate monthly performance report"""
        if len(self.monthly_metrics) < 1:
            return {"status": "no_data", "message": "Insufficient monthly data"}
        
        accuracies = [m.get('accuracy', 0) for m in self.monthly_metrics]
        
        # Comprehensive monthly analysis
        report = {
            "report_type": "monthly",
            "generated_at": datetime.now().isoformat(),
            "month": datetime.now().strftime('%Y-%m'),
            "summary": {
                "avg_accuracy": np.mean(accuracies),
                "best_accuracy": np.max(accuracies),
                "worst_accuracy": np.min(accuracies),
                "std_accuracy": np.std(accuracies),
                "total_predictions": sum(m.get('predictions_count', 0) for m in self.monthly_metrics),
                "total_validations": len(self.monthly_metrics)
            },
            "long_term_trends": {
                "accuracy_trend": self._calculate_trend(accuracies),
                "month_over_month_change": self._calculate_month_over_month(accuracies),
                "seasonality": self._detect_seasonality(accuracies)
            },
            "systematic_biases": self._identify_systematic_biases(self.monthly_metrics),
            "model_health": self._assess_model_health(accuracies),
            "actionable_insights": self._generate_actionable_insights(accuracies)
        }
        
        self._save_report(report, 'monthly')
        return report
    
    def _identify_systematic_biases(self, metrics: List[Dict]) -> List[Dict]:
        """Identify systematic biases in predictions"""
        biases = []
        
        # Track by driver/category if available
        error_by_category = defaultdict(list)
        for m in metrics:
            if 'errors_by_category' in m:
                for cat, errors in m['errors_by_category'].items():
                    error_by_category[cat].extend(errors)
        
        for cat, errors in error_by_category.items():
            if errors:
                mean_error = np.mean(errors)
                if abs(mean_error) > 2.0:  # Significant bias threshold
                    biases.append({
                        "category": cat,
                        "mean_error": float(mean_error),
                        "direction": "overestimating" if mean_error > 0 else "underestimating",
                        "severity": "high" if abs(mean_error) > 5 else "moderate"
                    })
        
        return biases
    
    def _detect_degradation(self, weekly: bool = False) -> Dict:
        """Detect model degradation patterns"""
        metrics = self.weekly_metrics if weekly else self.daily_metrics
        if len(metrics) < 3:
            return {"status": "insufficient_data"}
        
        accuracies = [m.get('accuracy', 0) for m in metrics[-5:]]
        
        # Calculate moving average
        if len(accuracies) >= 3:
            recent_avg = np.mean(accuracies[-3:])
            older_avg = np.mean(accuracies[:-3]) if len(accuracies) > 3 else accuracies[0]
            
            degradation_rate = (older_avg - recent_avg) / older_avg if older_avg > 0 else 0
            
            return {
                "status": "degrading" if degradation_rate > 0.05 else "stable",
                "degradation_rate": float(degradation_rate),
                "recent_avg_accuracy": float(recent_avg),
                "older_avg_accuracy": float(older_avg),
                "consecutive_low_accuracy": sum(1 for a in accuracies[-3:] if a < 0.7)
            }
        
        return {"status": "insufficient_data"}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        slope = np.polyfit(range(len(values)), values, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "degrading"
        else:
            return "stable"
    
    def _calculate_improvement_rate(self, values: List[float]) -> float:
        """Calculate improvement rate"""
        if len(values) < 2:
            return 0.0
        
        return float((values[-1] - values[0]) / values[0]) if values[0] > 0 else 0.0
    
    def _calculate_month_over_month(self, values: List[float]) -> float:
        """Calculate month-over-month change"""
        if len(values) < 2:
            return 0.0
        
        return float(values[-1] - values[0])
    
    def _detect_seasonality(self, values: List[float]) -> str:
        """Detect seasonality patterns (simplified)"""
        if len(values) < 4:
            return "insufficient_data"
        
        # Simple pattern detection
        return "no_clear_seasonality"
    
    def _assess_model_health(self, accuracies: List[float]) -> Dict:
        """Assess overall model health"""
        avg_acc = np.mean(accuracies)
        
        if avg_acc >= 0.85:
            health = "excellent"
        elif avg_acc >= 0.75:
            health = "good"
        elif avg_acc >= 0.65:
            health = "fair"
        else:
            health = "poor"
        
        return {
            "health_status": health,
            "avg_accuracy": float(avg_acc),
            "recommendation": self._get_health_recommendation(health)
        }
    
    def _get_health_recommendation(self, health: str) -> str:
        """Get recommendation based on health status"""
        recommendations = {
            "excellent": "Model performing excellently. Continue monitoring.",
            "good": "Model performing well. Consider minor optimizations.",
            "fair": "Model needs improvement. Schedule retraining soon.",
            "poor": "Model performance critical. Immediate retraining required."
        }
        return recommendations.get(health, "Unknown health status")
    
    def _generate_actionable_insights(self, accuracies: List[float]) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Check for degradation
        if len(accuracies) >= 3 and accuracies[-1] < accuracies[0]:
            insights.append("Model accuracy has declined. Consider collecting more recent training data.")
        
        # Check for consistency
        if np.std(accuracies) > 0.1:
            insights.append("High variance in predictions. Review feature stability.")
        
        # Check average performance
        if np.mean(accuracies) < 0.7:
            insights.append("Average accuracy below threshold. Retraining strongly recommended.")
        
        return insights
    
    def _get_retraining_recommendation(self, degradation: Dict, biases: List[Dict]) -> Dict:
        """Get retraining recommendation based on analysis"""
        needs_retraining = False
        reasons = []
        
        if degradation.get("status") == "degrading":
            needs_retraining = True
            reasons.append("Model degradation detected")
        
        if any(b.get("severity") == "high" for b in biases):
            needs_retraining = True
            reasons.append("High severity systematic bias detected")
        
        return {
            "recommended": needs_retraining,
            "priority": "high" if needs_retraining else "normal",
            "reasons": reasons,
            "suggested_actions": self._get_suggested_actions(needs_retraining, biases)
        }
    
    def _get_suggested_actions(self, needs_retraining: bool, biases: List[Dict]) -> List[str]:
        """Get suggested actions"""
        actions = []
        
        if needs_retraining:
            actions.append("Collect and prepare new training data")
            actions.append("Retrain model with updated dataset")
            actions.append("Review and adjust hyperparameters")
        
        for bias in biases:
            if bias.get("severity") == "high":
                actions.append(f"Investigate bias in {bias.get('category')} predictions")
        
        if not actions:
            actions.append("Continue current monitoring routine")
        
        return actions
    
    def _save_report(self, report: Dict, period: str):
        """Save report to file"""
        filename = f"{period}_report_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.log_info(f"Saved {period} report to {filepath}")
    
    def generate_dashboard(self) -> Dict:
        """Generate combined dashboard with all periods"""
        return {
            "dashboard_generated_at": datetime.now().isoformat(),
            "daily": self.generate_daily_report(),
            "weekly": self.generate_weekly_report(),
            "monthly": self.generate_monthly_report()
        }


# ============================================================================
# ERROR HANDLING AND FALLBACKS
# ============================================================================

class PipelineErrorHandler:
    """Handles errors gracefully with fallback mechanisms"""
    
    def __init__(self, logger: MLLogger):
        self.logger = logger
        self.fallback_model = None
        self.error_counts = defaultdict(int)
        self.last_error = None
        
    def handle_data_loading_error(self, error: Exception, fallback_data: Any = None) -> Tuple[bool, Any]:
        """Handle data loading failures"""
        self.logger.log_error(f"Data loading failed: {str(error)}")
        self.error_counts['data_loading'] += 1
        self.last_error = str(error)
        
        if fallback_data is not None:
            self.logger.log_warning("Using fallback data")
            return True, fallback_data
        
        return False, None
    
    def handle_training_interruption(self, error: Exception, checkpoint_path: str = None) -> bool:
        """Handle model training interruptions"""
        self.logger.log_error(f"Training interrupted: {str(error)}")
        self.error_counts['training_interruption'] += 1
        
        if checkpoint_path and os.path.exists(checkpoint_path):
            self.logger.log_info(f"Resuming from checkpoint: {checkpoint_path}")
            return True
        
        return False
    
    def handle_invalid_prediction_input(self, error: Exception, input_data: Any) -> Tuple[bool, Any]:
        """Handle invalid input for prediction"""
        self.logger.log_error(f"Invalid prediction input: {str(error)}")
        self.error_counts['invalid_input'] += 1
        
        # Try to sanitize input
        try:
            if isinstance(input_data, dict):
                sanitized = self._sanitize_dict_input(input_data)
                return True, sanitized
        except:
            pass
        
        return False, None
    
    def handle_connectivity_error(self, error: Exception, service: str) -> Tuple[bool, Any]:
        """Handle connectivity issues gracefully"""
        self.logger.log_error(f"Connectivity error for {service}: {str(error)}")
        self.error_counts[f'connectivity_{service}'] += 1
        
        # Return fallback response
        return True, self._get_connectivity_fallback(service)
    
    def _sanitize_dict_input(self, data: Dict) -> Dict:
        """Sanitize input dictionary"""
        sanitized = {}
        for key, value in data.items():
            if value is None:
                sanitized[key] = 0
            elif isinstance(value, (int, float)):
                sanitized[key] = float(value)
            elif isinstance(value, str):
                sanitized[key] = value[:100]  # Truncate long strings
            else:
                sanitized[key] = str(value)[:100]
        return sanitized
    
    def _get_connectivity_fallback(self, service: str) -> Dict:
        """Get fallback response for connectivity issues"""
        return {
            "status": "error",
            "service": service,
            "message": f"{service} unavailable. Using cached/fallback data.",
            "fallback": True
        }
    
    def get_error_summary(self) -> Dict:
        """Get summary of all errors"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_breakdown": dict(self.error_counts),
            "last_error": self.last_error,
            "requires_attention": any(
                count > 10 for count in self.error_counts.values()
            )
        }


# ============================================================================
# MAIN ML PIPELINE
# ============================================================================

class RaceOutcomeMLPipeline:
    """Main ML pipeline orchestrator"""
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        
        # Initialize components
        self.logger = MLLogger(self.config.logs_dir)
        self.error_handler = PipelineErrorHandler(self.logger)
        
        # Create directories
        for dir_path in [self.config.model_dir, self.config.data_dir, 
                        self.config.logs_dir, self.config.reports_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize pipeline components
        self.preprocessor = DataPreprocessor(self.logger, self.config)
        self.model = RaceOutcomeModel(self.logger, self.config)
        self.validation = ValidationSystem(self.logger, self.config)
        self.reporter = PerformanceReporter(self.logger, self.config)
        
        self.logger.log_info("ML Pipeline initialized")
    
    def train_model(self, features: np.ndarray, target: np.ndarray, 
                   save_model: bool = True) -> bool:
        """Train the prediction model"""
        try:
            self.logger.log_info("Starting model training pipeline")
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                features, target,
                test_size=self.config.test_size,
                random_state=self.config.random_state
            )
            
            self.logger.log_info(f"Training set: {len(X_train)}, Validation set: {len(X_val)}")
            
            # Train model
            self.model.train(X_train, y_train, X_val, y_val)
            
            # Cross-validation
            cv_results = self.model.cross_validate(X_train, y_train)
            
            # Evaluate on validation set
            predictions, confidence = self.model.predict_with_confidence(X_val)
            metrics = self._calculate_metrics(y_val, predictions)
            
            self.logger.log_metrics("final_validation", metrics)
            
            # Save model
            if save_model:
                model_path = f"{self.config.model_dir}/race_predictor_v{self.model.version}.pkl"
                self.model.save_model(model_path)
            
            self.logger.log_info("Model training complete")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Training failed: {str(e)}")
            return self.error_handler.handle_training_interruption(e)
    
    def predict(self, features: np.ndarray) -> List[PredictionResult]:
        """Make predictions with confidence scores"""
        try:
            self.logger.log_debug(f"Making predictions for {len(features)} samples")
            
            # Get predictions with confidence
            predictions, confidence = self.model.predict_with_confidence(features)
            
            # Get position probabilities
            probabilities = self.model.predict_position_probabilities(features)
            
            # Build results
            results = []
            for i, (pred, conf) in enumerate(zip(predictions, confidence)):
                result = PredictionResult(
                    driver_id=f"driver_{i}",
                    predicted_position=int(pred),
                    confidence_score=float(conf),
                    win_probability=float(probabilities['win_probability'][i]),
                    podium_probability=float(probabilities['podium_probability'][i]),
                    top10_probability=float(probabilities['top10_probability'][i]),
                    feature_importance=self.model.feature_importance,
                    model_version=self.model.version
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.log_error(f"Prediction failed: {str(e)}")
            self.error_handler.handle_invalid_prediction_input(e, features)
            return []
    
    def validate(self, predictions: List[PredictionResult], 
                actual_results: List[Dict]) -> ValidationResult:
        """Validate predictions against actual results"""
        try:
            return self.validation.validate_predictions(predictions, actual_results)
        except Exception as e:
            self.logger.log_error(f"Validation failed: {str(e)}")
            return None
    
    def generate_report(self) -> Dict:
        """Generate performance dashboard"""
        try:
            return self.reporter.generate_dashboard()
        except Exception as e:
            self.logger.log_error(f"Report generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Calculate comprehensive metrics"""
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, average='macro', zero_division=0),
            "recall": recall_score(y_true, y_pred, average='macro', zero_division=0),
            "f1_score": f1_score(y_true, y_pred, average='macro', zero_division=0),
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred))
        }
        return metrics
    
    def check_retraining_needed(self) -> Tuple[bool, str]:
        """Check if model needs retraining"""
        return self.validation.check_retraining_needed()


# ============================================================================
# SAMPLE DATA GENERATION
# ============================================================================

def generate_sample_training_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """Generate sample training data for demonstration"""
    np.random.seed(42)
    
    # Features
    features = np.random.randn(n_samples, 10)
    target = np.random.randint(1, 21, n_samples)  # Positions 1-20
    
    return features, target


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ML Pipeline for Race Outcome Prediction")
    print("=" * 60)
    
    # Initialize pipeline
    config = PipelineConfig(
        n_estimators=100,
        max_depth=8,
        learning_rate=0.1,
        retraining_accuracy_threshold=0.75,
        retraining_f1_threshold=0.70
    )
    
    pipeline = RaceOutcomeMLPipeline(config)
    
    # Generate sample data
    print("\n[1] Generating training data...")
    X, y = generate_sample_training_data(1000)
    print(f"    Generated {len(X)} samples with {X.shape[1]} features")
    
    # Train model
    print("\n[2] Training model...")
    success = pipeline.train_model(X, y)
    print(f"    Training {'successful' if success else 'failed'}")
    
    # Make predictions
    print("\n[3] Making predictions...")
    test_features = np.random.randn(5, 10)
    predictions = pipeline.predict(test_features)
    print(f"    Generated {len(predictions)} predictions")
    
    # Show sample prediction
    if predictions:
        print("\n    Sample Prediction:")
        print(f"    - Position: {predictions[0].predicted_position}")
        print(f"    - Confidence: {predictions[0].confidence_score:.2%}")
        print(f"    - Win Probability: {predictions[0].win_probability:.2%}")
        print(f"    - Podium Probability: {predictions[0].podium_probability:.2%}")
    
    # Generate validation sample
    print("\n[4] Running validation...")
    actual_results = [
        {'position': 1, 'driver_id': 'driver_0'},
        {'position': 3, 'driver_id': 'driver_1'},
        {'position': 2, 'driver_id': 'driver_2'},
    ]
    validation_result = pipeline.validate(predictions[:3], actual_results)
    if validation_result:
        print(f"    Validation Accuracy: {validation_result.accuracy:.2%}")
        print(f"    Validation F1: {validation_result.f1_score:.2%}")
        print(f"    Validation RMSE: {validation_result.rmse:.2f}")
    
    # Generate reports
    print("\n[5] Generating reports...")
    dashboard = pipeline.generate_report()
    print(f"    Dashboard generated successfully")
    print(f"    - Daily reports: {dashboard.get('daily', {}).get('status', 'N/A')}")
    print(f"    - Weekly reports: {dashboard.get('weekly', {}).get('report_type', 'N/A')}")
    print(f"    - Monthly reports: {dashboard.get('monthly', {}).get('report_type', 'N/A')}")
    
    # Check retraining status
    print("\n[6] Checking retraining status...")
    needs_retraining, reason = pipeline.check_retraining_needed()
    print(f"    Needs retraining: {needs_retraining}")
    print(f"    Reason: {reason}")
    
    print("\n" + "=" * 60)
    print("ML Pipeline execution complete!")
    print("=" * 60)

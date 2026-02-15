# ============================================================================
# DATA CLASSES FOR PIPELINE
# ============================================================================
# Dataclasses for representing ML pipeline data structures

from dataclasses import dataclass, field
from typing import List, Dict, Any


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

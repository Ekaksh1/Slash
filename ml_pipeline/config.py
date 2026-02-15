# ============================================================================
# ML PIPELINE CONFIGURATION
# ============================================================================
# Configuration dataclass for ML pipeline settings

from dataclasses import dataclass, field


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

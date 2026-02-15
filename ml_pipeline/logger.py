# ============================================================================
# ML PIPELINE LOGGER
# ============================================================================
# Comprehensive logging system for ML pipeline

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


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
        """Log info message"""
        self.logger.info(message)
    
    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_error(self, message: str, exc_info: bool = True):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def log_critical(self, message: str, exc_info: bool = True):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)
    
    def log_training_progress(self, epoch: int, metrics: Dict):
        """Log training progress at each epoch"""
        msg = f"Epoch {epoch} | " + " | ".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
        self.training_logger.info(msg)
    
    def log_metrics(self, stage: str, metrics: Dict):
        """Log metrics at different stages"""
        import numpy as np
        
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

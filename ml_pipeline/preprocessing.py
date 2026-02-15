# ============================================================================
# DATA PREPROCESSING MODULE
# ============================================================================
# Handles all data preprocessing steps with logging

import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.preprocessing import StandardScaler, LabelEncoder
from ml_pipeline.config import PipelineConfig
from ml_pipeline.logger import MLLogger


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

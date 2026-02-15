// ============================================================================
// DATA PREPROCESSING - Rust Implementation
// ============================================================================
// High-performance data preprocessing functions for ML pipeline

use rayon::prelude::*;

/// Handle missing values in numeric array by filling with median
pub fn handle_missing_values_numeric(values: &[f64]) -> Vec<f64> {
    // Find finite values to calculate median
    let finite_values: Vec<f64> = values.iter()
        .filter(|&&v| v.is_finite())
        .cloned()
        .collect();
    
    if finite_values.is_empty() {
        return values.to_vec();
    }
    
    // Calculate median
    let mut sorted = finite_values.clone();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    
    let median = if sorted.len() % 2 == 0 {
        (sorted[sorted.len() / 2 - 1] + sorted[sorted.len() / 2]) / 2.0
    } else {
        sorted[sorted.len() / 2]
    };
    
    // Replace NaN and Inf with median
    values.iter()
        .map(|&v| if v.is_finite() { v } else { median })
        .collect()
}

/// Standardize features using z-score normalization
pub fn standardize_features(values: &[f64]) -> (Vec<f64>, f64, f64) {
    let n = values.len() as f64;
    if n == 0.0 {
        return (vec![], 0.0, 0.0);
    }
    
    // Calculate mean
    let sum: f64 = values.iter().sum();
    let mean = sum / n;
    
    // Calculate standard deviation
    let variance: f64 = values.iter()
        .map(|&v| (v - mean).powi(2))
        .sum::<f64>() / n;
    let std = variance.sqrt();
    
    // Standardize
    let standardized = if std > 0.0 {
        values.iter()
            .map(|&v| (v - mean) / std)
            .collect()
    } else {
        values.to_vec()
    };
    
    (standardized, mean, std)
}

/// Apply min-max scaling to values
pub fn min_max_scale(values: &[f64], min_val: f64, max_val: f64) -> Vec<f64> {
    let range = max_val - min_val;
    if range == 0.0 {
        return values.iter().map(|_| 0.5).collect();
    }
    
    values.iter()
        .map(|&v| (v - min_val) / range)
        .collect()
}

/// Encode categorical values as integers using label encoding
pub fn encode_categorical(values: &[String]) -> (Vec<i32>, Vec<String>) {
    // Get unique categories preserving order
    let mut categories: Vec<&String> = Vec::new();
    for v in values {
        if !categories.contains(&v) {
            categories.push(v);
        }
    }
    
    // Create encoding map
    let encoding: std::collections::HashMap<&String, i32> = categories.iter()
        .enumerate()
        .map(|(i, &s)| (s, i as i32))
        .collect();
    
    // Encode values
    let encoded: Vec<i32> = values.iter()
        .map(|v| *encoding.get(v).unwrap_or(&0))
        .collect();
    
    (encoded, categories.iter().map(|s| (*s).clone()).collect())
}

/// Calculate feature interactions (multiplication of two features)
pub fn calculate_feature_interaction(feature1: &[f64], feature2: &[f64]) -> Vec<f64> {
    let n = feature1.len().min(feature2.len());
    
    (0..n)
        .into_par_iter()
        .map(|i| feature1[i] * feature2[i])
        .collect()
}

/// Calculate consistency score: 1 / (avg_finish + 1)
pub fn calculate_consistency_score(avg_finish: f64) -> f64 {
    1.0 / (avg_finish + 1.0)
}

/// Calculate rolling average using simple moving average
#[allow(dead_code)]
pub fn calculate_rolling_average(values: &[f64], window: usize) -> Vec<f64> {
    if values.is_empty() || window == 0 {
        return vec![];
    }
    
    let n = values.len();
    let mut result = Vec::with_capacity(n);
    
    for i in 0..n {
        let start = if i >= window { i - window + 1 } else { 0 };
        let window_values = &values[start..=i];
        let avg = window_values.iter().sum::<f64>() / window_values.len() as f64;
        result.push(avg);
    }
    
    result
}

/// Detect outliers using IQR method
#[allow(dead_code)]
pub fn detect_outliers(values: &[f64]) -> Vec<bool> {
    if values.len() < 4 {
        return vec![false; values.len()];
    }
    
    // Sort for quartile calculation
    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    
    let q1_idx = sorted.len() / 4;
    let q3_idx = 3 * sorted.len() / 4;
    
    let q1 = sorted[q1_idx];
    let q3 = sorted[q3_idx];
    let iqr = q3 - q1;
    
    let lower_bound = q1 - 1.5 * iqr;
    let upper_bound = q3 + 1.5 * iqr;
    
    values.iter()
        .map(|&v| v < lower_bound || v > upper_bound)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_missing_values() {
        let values = vec![1.0, 2.0, f64::NAN, 4.0, f64::INFINITY];
        let result = handle_missing_values_numeric(&values);
        assert!(result.iter().all(|v| v.is_finite()));
    }
    
    #[test]
    fn test_standardize() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let (standardized, mean, std) = standardize_features(&values);
        
        assert!((mean - 3.0).abs() < 0.001);
        assert!(std > 0.0);
        // Mean of standardized should be ~0
        let standardized_mean: f64 = standardized.iter().sum::<f64>() / standardized.len() as f64;
        assert!(standardized_mean.abs() < 0.001);
    }
    
    #[test]
    fn test_min_max_scale() {
        let values = vec![0.0, 25.0, 50.0, 75.0, 100.0];
        let scaled = min_max_scale(&values, 0.0, 100.0);
        
        assert!((scaled[0] - 0.0).abs() < 0.001);
        assert!((scaled[4] - 1.0).abs() < 0.001);
    }
    
    #[test]
    fn test_categorical_encoding() {
        let values = vec!["red".to_string(), "blue".to_string(), "red".to_string(), "green".to_string()];
        let (encoded, categories) = encode_categorical(&values);
        
        assert_eq!(encoded, vec![0, 1, 0, 2]);
        assert_eq!(categories.len(), 3);
    }
    
    #[test]
    fn test_feature_interaction() {
        let f1 = vec![1.0, 2.0, 3.0];
        let f2 = vec![4.0, 5.0, 6.0];
        let result = calculate_feature_interaction(&f1, &f2);
        
        assert_eq!(result, vec![4.0, 10.0, 18.0]);
    }
    
    #[test]
    fn test_consistency_score() {
        let score1 = calculate_consistency_score(1.0);
        let score2 = calculate_consistency_score(5.0);
        
        assert!(score1 > score2); // Lower finish = higher consistency
    }
}

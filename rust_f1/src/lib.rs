// ============================================================================
// F1 RUST MODULE - High Performance Scoring Engine
// ============================================================================
// Rust implementation of performance-critical components using PyO3
// Provides Python bindings for scoring calculations and data preprocessing

use pyo3::prelude::*;
use pyo3::types::IntoPyDict;
use numpy::{Array2, Array1};

mod scoring;
mod preprocessing;

/// Calculate driver score using the formula from spec:
/// Driver Score = (0.4 × Avg Race Finish) + (0.3 × Qualifying) + (0.2 × Form) - (0.1 × DNF Risk)
/// + Track Affinity Bonus
#[pyfunction]
fn calculate_driver_score(
    avg_finish: f64,
    qualifying_avg: f64,
    recent_form: f64,
    dnf_risk: f64,
    track_affinity: f64,
    rain: bool,
) -> f64 {
    scoring::calculate_driver_score(avg_finish, qualifying_avg, recent_form, dnf_risk, track_affinity, rain)
}

/// Calculate team score using formula from spec:
/// Team Score = (0.5 × Constructor Form) + (0.3 × Pit Efficiency) + (0.2 × Reliability)
#[pyfunction]
fn calculate_team_score(
    constructor_form: f64,
    pit_efficiency: f64,
    reliability: f64,
) -> f64 {
    scoring::calculate_team_score(constructor_form, pit_efficiency, reliability)
}

/// Total Score = Driver Score × Team Score
#[pyfunction]
fn calculate_final_score(driver_score: f64, team_score: f64) -> f64 {
    scoring::calculate_final_score(driver_score, team_score)
}

/// Calculate track affinity based on historical performance
#[pyfunction]
fn calculate_track_affinity(positions: Vec<i32>, podiums: i32) -> f64 {
    scoring::calculate_track_affinity(&positions, podiums)
}

/// Normalize finishing positions to scores
#[pyfunction]
fn normalize_finish_scores(positions: Vec<f64>, max_position: f64) -> Vec<f64> {
    scoring::normalize_finish_scores(&positions, max_position)
}

/// Apply sigmoid transformation for probability
#[pyfunction]
fn sigmoid_probability(value: f64) -> f64 {
    scoring::sigmoid_probability(value)
}

/// Calculate win probability using logistic regression-style transformation
#[pyfunction]
fn calculate_win_probability(final_score: f64, max_score: f64) -> f64 {
    scoring::calculate_win_probability(final_score, max_score)
}

/// Calculate podium probability based on position and score
#[pyfunction]
fn calculate_podium_probability(position: i32, normalized_score: f64) -> f64 {
    scoring::calculate_podium_probability(position, normalized_score)
}

// ============================================================================
// DATA PREPROCESSING FUNCTIONS
// ============================================================================

/// Handle missing values in numeric array by filling with median
#[pyfunction]
fn handle_missing_values_numeric(values: Vec<f64>) -> Vec<f64> {
    preprocessing::handle_missing_values_numeric(&values)
}

/// Standardize features using z-score normalization
#[pyfunction]
fn standardize_features(values: Vec<f64>) -> (Vec<f64>, f64, f64) {
    preprocessing::standardize_features(&values)
}

/// Apply min-max scaling to values
#[pyfunction]
fn min_max_scale(values: Vec<f64>, min_val: f64, max_val: f64) -> Vec<f64> {
    preprocessing::min_max_scale(&values, min_val, max_val)
}

/// Encode categorical values as integers
#[pyfunction]
fn encode_categorical(values: Vec<String>) -> (Vec<i32>, Vec<String>) {
    preprocessing::encode_categorical(&values)
}

/// Calculate feature interactions (multiplication)
#[pyfunction]
fn calculate_feature_interaction(feature1: Vec<f64>, feature2: Vec<f64>) -> Vec<f64> {
    preprocessing::calculate_feature_interaction(&feature1, &feature2)
}

/// Calculate consistency score (1 / (avg_finish + 1))
#[pyfunction]
fn calculate_consistency_score(avg_finish: f64) -> f64 {
    preprocessing::calculate_consistency_score(avg_finish)
}

// ============================================================================
// PARALLEL PROCESSING HELPERS
// ============================================================================

/// Calculate scores for multiple drivers in parallel using Rayon
#[pyfunction]
fn calculate_batch_driver_scores(
    avg_finishes: Vec<f64>,
    qualifying_avgs: Vec<f64>,
    recent_forms: Vec<f64>,
    dnf_risks: Vec<f64>,
    track_affinities: Vec<f64>,
    rain: bool,
) -> Vec<f64> {
    scoring::calculate_batch_driver_scores(
        &avg_finishes,
        &qualifying_avgs,
        &recent_forms,
        &dnf_risks,
        &track_affinities,
        rain,
    )
}

/// Batch calculate final scores
#[pyfunction]
fn calculate_batch_final_scores(driver_scores: Vec<f64>, team_scores: Vec<f64>) -> Vec<f64> {
    scoring::calculate_batch_final_scores(&driver_scores, &team_scores)
}

// ============================================================================
// PYTHON MODULE DEFINITION
// ============================================================================

#[pymodule]
fn f1_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Scoring functions
    m.add_function(wrap_pyfunction!(calculate_driver_score, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_team_score, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_final_score, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_track_affinity, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_finish_scores, m)?)?;
    m.add_function(wrap_pyfunction!(sigmoid_probability, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_win_probability, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_podium_probability, m)?)?;
    
    // Preprocessing functions
    m.add_function(wrap_pyfunction!(handle_missing_values_numeric, m)?)?;
    m.add_function(wrap_pyfunction!(standardize_features, m)?)?;
    m.add_function(wrap_pyfunction!(min_max_scale, m)?)?;
    m.add_function(wrap_pyfunction!(encode_categorical, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_feature_interaction, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_consistency_score, m)?)?;
    
    // Batch/parallel functions
    m.add_function(wrap_pyfunction!(calculate_batch_driver_scores, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_batch_final_scores, m)?)?;
    
    Ok(())
}

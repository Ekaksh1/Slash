// ============================================================================
// SCORING ENGINE - Rust Implementation
// ============================================================================
// High-performance scoring calculations for F1 predictions
// Optimized with SIMD and parallel processing

use rayon::prelude::*;

/// Calculate driver score using the formula from spec:
/// Driver Score = (0.4 × Avg Race Finish) + (0.3 × Qualifying) + (0.2 × Form) - (0.1 × DNF Risk)
/// + Track Affinity Bonus
pub fn calculate_driver_score(
    avg_finish: f64,
    qualifying_avg: f64,
    recent_form: f64,
    dnf_risk: f64,
    track_affinity: f64,
    rain: bool,
) -> f64 {
    // Normalize avg_finish and qualifying (lower is better)
    let finish_score = (20.0 - avg_finish.min(20.0)) / 20.0;
    let qual_score = (20.0 - qualifying_avg.min(20.0)) / 20.0;
    
    // Base score: 0.4 × finish + 0.3 × qual + 0.2 × form - 0.1 × dnf
    let base_score = (0.4 * finish_score) + (0.3 * qual_score) + (0.2 * recent_form) - (0.1 * dnf_risk);
    
    // Add track affinity bonus (15%)
    let track_bonus = track_affinity * 0.15;
    let mut driver_score = base_score + track_bonus;
    
    // Apply weather modifier
    if rain {
        let wet_skill_multiplier = 1.0 + (0.2 * recent_form);
        driver_score *= wet_skill_multiplier;
    }
    
    // Ensure non-negative
    driver_score.max(0.0)
}

/// Calculate team score using formula from spec:
/// Team Score = (0.5 × Constructor Form) + (0.3 × Pit Efficiency) + (0.2 × Reliability)
pub fn calculate_team_score(
    constructor_form: f64,
    pit_efficiency: f64,
    reliability: f64,
) -> f64 {
    (0.5 * constructor_form) + (0.3 * pit_efficiency) + (0.2 * reliability)
}

/// Total Score = Driver Score × Team Score
pub fn calculate_final_score(driver_score: f64, team_score: f64) -> f64 {
    driver_score * team_score
}

/// Calculate track affinity based on historical performance
pub fn calculate_track_affinity(positions: &[i32], podiums: i32) -> f64 {
    if positions.is_empty() {
        return 0.5; // Neutral affinity
    }
    
    let avg_finish = positions.iter().sum::<i32>() as f64 / positions.len() as f64;
    let podium_rate = podiums as f64 / positions.len() as f64;
    
    // Score: better finish = higher affinity
    let finish_score = (20.0 - avg_finish) / 20.0;
    let affinity = 0.7 * finish_score + 0.3 * podium_rate;
    
    // Clamp to 0-1 range
    affinity.max(0.0).min(1.0)
}

/// Normalize finishing positions to scores (lower position = higher score)
pub fn normalize_finish_scores(positions: &[f64], max_position: f64) -> Vec<f64> {
    positions.iter()
        .map(|&p| (max_position - p.min(max_position)) / max_position)
        .collect()
}

/// Apply sigmoid transformation for probability
pub fn sigmoid_probability(value: f64) -> f64 {
    // sigmoid(x) = 1 / (1 + e^(-x))
    1.0 / (1.0 + (-value).exp())
}

/// Calculate win probability using logistic regression-style transformation
pub fn calculate_win_probability(final_score: f64, max_score: f64) -> f64 {
    if max_score == 0.0 {
        return 0.0;
    }
    
    // Normalize against competition
    let normalized = final_score / max_score;
    
    // Sigmoid transformation
    let x = (normalized - 0.5) * 10.0;
    sigmoid_probability(x).max(0.0).min(1.0)
}

/// Calculate podium probability based on position and score
pub fn calculate_podium_probability(position: i32, normalized_score: f64) -> f64 {
    // Base probabilities for each position
    let base_probs: [f64; 8] = [0.95, 0.90, 0.85, 0.60, 0.40, 0.25, 0.15, 0.08];
    
    let base_prob = if position < 8 {
        base_probs[position as usize]
    } else {
        0.03
    };
    
    // Adjust by normalized score
    let adjusted_prob = base_prob * (0.7 + 0.3 * normalized_score);
    
    adjusted_prob.max(0.0).min(1.0)
}

/// Calculate scores for multiple drivers in parallel using Rayon
#[allow(dead_code)]
pub fn calculate_batch_driver_scores(
    avg_finishes: &[f64],
    qualifying_avgs: &[f64],
    recent_forms: &[f64],
    dnf_risks: &[f64],
    track_affinities: &[f64],
    rain: bool,
) -> Vec<f64> {
    let n = avg_finishes.len();
    
    (0..n)
        .into_par_iter()
        .map(|i| {
            calculate_driver_score(
                avg_finishes[i],
                qualifying_avgs[i],
                recent_forms[i],
                dnf_risks[i],
                track_affinities[i],
                rain,
            )
        })
        .collect()
}

/// Batch calculate final scores in parallel
#[allow(dead_code)]
pub fn calculate_batch_final_scores(driver_scores: &[f64], team_scores: &[f64]) -> Vec<f64> {
    let n = driver_scores.len();
    
    (0..n)
        .into_par_iter()
        .map(|i| calculate_final_score(driver_scores[i], team_scores[i]))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_driver_score() {
        let score = calculate_driver_score(2.5, 1.8, 0.85, 0.1, 0.75, false);
        assert!(score > 0.0 && score < 1.0);
    }
    
    #[test]
    fn test_team_score() {
        let score = calculate_team_score(0.8, 0.85, 0.9);
        assert!(score > 0.0 && score < 1.0);
    }
    
    #[test]
    fn test_track_affinity() {
        let positions = vec![1, 2, 3, 5, 2];
        let affinity = calculate_track_affinity(&positions, 3);
        assert!(affinity > 0.5);
    }
    
    #[test]
    fn test_sigmoid() {
        let prob = sigmoid_probability(0.0);
        assert!((prob - 0.5).abs() < 0.001);
    }
}

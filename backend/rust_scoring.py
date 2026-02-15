# ============================================================================
# RUST SCORING WRAPPER
# ============================================================================
# Python wrapper for Rust scoring engine
# Falls back to pure Python if Rust module not available

import os
import sys

# Try to import Rust module, fall back to pure Python
USE_RUST = False

try:
    from f1_rust import (
        calculate_driver_score as rust_calculate_driver_score,
        calculate_team_score as rust_calculate_team_score,
        calculate_final_score as rust_calculate_final_score,
        calculate_track_affinity as rust_calculate_track_affinity,
        sigmoid_probability as rust_sigmoid_probability,
        calculate_win_probability as rust_calculate_win_probability,
        calculate_podium_probability as rust_calculate_podium_probability,
        calculate_batch_driver_scores,
        calculate_batch_final_scores,
    )
    USE_RUST = True
    print("[Rust] Using Rust-accelerated scoring engine")
except ImportError:
    print("[Python] Using pure Python scoring engine (install Rust module for加速)")
    USE_RUST = False


def calculate_driver_score(
    avg_finish: float,
    qualifying_avg: float,
    recent_form: float,
    dnf_risk: float,
    track_affinity: float,
    weather_conditions: dict
) -> float:
    """
    Calculate driver score using the formula from spec
    """
    if USE_RUST:
        return rust_calculate_driver_score(
            avg_finish,
            qualifying_avg,
            recent_form,
            dnf_risk,
            track_affinity,
            weather_conditions.get('rain', False)
        )
    
    # Pure Python fallback
    rain = weather_conditions.get('rain', False)
    
    # Normalize avg_finish and qualifying (lower is better)
    finish_score = (20.0 - min(avg_finish, 20.0)) / 20.0
    qual_score = (20.0 - min(qualifying_avg, 20.0)) / 20.0
    
    # Base score
    base_score = (0.4 * finish_score) + (0.3 * qual_score) + (0.2 * recent_form) - (0.1 * dnf_risk)
    
    # Add track affinity bonus
    track_bonus = track_affinity * 0.15
    driver_score = base_score + track_bonus
    
    # Apply weather modifier
    if rain:
        wet_skill_multiplier = 1.0 + (0.2 * recent_form)
        driver_score *= wet_skill_multiplier
    
    return max(0.0, driver_score)


def calculate_team_score(
    constructor_form: float,
    pit_efficiency: float = 0.8,
    reliability: float = 0.85
) -> float:
    """
    Calculate team score using formula from spec
    """
    if USE_RUST:
        return rust_calculate_team_score(constructor_form, pit_efficiency, reliability)
    
    return (0.5 * constructor_form) + (0.3 * pit_efficiency) + (0.2 * reliability)


def calculate_final_score(driver_score: float, team_score: float) -> float:
    """Total Score = Driver Score × Team Score"""
    if USE_RUST:
        return rust_calculate_final_score(driver_score, team_score)
    
    return driver_score * team_score


def calculate_track_affinity(positions: list, podiums: int) -> float:
    """Calculate driver's historical performance at specific circuit"""
    if USE_RUST:
        return rust_calculate_track_affinity(positions, podiums)
    
    if not positions:
        return 0.5
    
    avg_finish = sum(positions) / len(positions)
    podium_rate = podiums / len(positions)
    
    finish_score = (20 - avg_finish) / 20.0
    affinity = 0.7 * finish_score + 0.3 * podium_rate
    
    return max(0.0, min(1.0, affinity))


def sigmoid_probability(value: float) -> float:
    """Apply sigmoid transformation"""
    if USE_RUST:
        return rust_sigmoid_probability(value)
    
    return 1.0 / (1.0 + (-value).exp())


def calculate_win_probability(final_score: float, all_scores: list) -> float:
    """Calculate win probability"""
    if not all_scores or max(all_scores) == 0:
        return 0.0
    
    if USE_RUST:
        return rust_calculate_win_probability(final_score, max(all_scores))
    
    normalized = final_score / max(all_scores)
    x = (normalized - 0.5) * 10.0
    probability = sigmoid_probability(x)
    
    return min(max(probability, 0.0), 1.0)


def calculate_podium_probability(final_score: float, position: int, all_scores: list) -> float:
    """Calculate podium probability"""
    if not all_scores or max(all_scores) == 0:
        return 0.0
    
    if USE_RUST:
        return rust_calculate_podium_probability(position, final_score / max(all_scores))
    
    normalized = final_score / max(all_scores)
    
    position_probs = {
        0: 0.95, 1: 0.90, 2: 0.85, 3: 0.60,
        4: 0.40, 5: 0.25, 6: 0.15, 7: 0.08
    }
    
    base_prob = position_probs.get(position, 0.03)
    adjusted_prob = base_prob * (0.7 + 0.3 * normalized)
    
    return min(max(adjusted_prob, 0.0), 1.0)


def calculate_batch_driver_scores(driver_metrics: list, rain: bool = False) -> list:
    """
    Calculate scores for multiple drivers in batch
    
    Args:
        driver_metrics: List of dicts with keys:
            - avg_finish
            - qualifying_avg
            - recent_form
            - dnf_risk
            - track_affinity
        rain: Whether it's raining
    """
    if USE_RUST:
        avg_finishes = [m['avg_finish'] for m in driver_metrics]
        qualifying_avgs = [m['qualifying_avg'] for m in driver_metrics]
        recent_forms = [m['recent_form'] for m in driver_metrics]
        dnf_risks = [m['dnf_risk'] for m in driver_metrics]
        track_affinities = [m['track_affinity'] for m in driver_metrics]
        
        return calculate_batch_driver_scores(
            avg_finishes, qualifying_avgs, recent_forms, dnf_risks, track_affinities, rain
        )
    
    # Pure Python fallback
    return [
        calculate_driver_score(
            m['avg_finish'],
            m['qualifying_avg'],
            m['recent_form'],
            m['dnf_risk'],
            m['track_affinity'],
            {'rain': rain}
        )
        for m in driver_metrics
    ]


def calculate_batch_final_scores(driver_scores: list, team_scores: list) -> list:
    """Calculate final scores in batch"""
    if USE_RUST:
        return calculate_batch_final_scores(driver_scores, team_scores)
    
    return [ds * ts for ds, ts in zip(driver_scores, team_scores)]


def is_using_rust() -> bool:
    """Check if Rust module is being used"""
    return USE_RUST

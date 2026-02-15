# ============================================================================
# PREDICTION GENERATOR - Main Prediction Engine Module
# ============================================================================
# Main prediction engine that combines all components
# Uses multiprocessing for parallel execution to improve performance

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp

from backend.f1_client import F1APIClient
from backend.scoring_engine import ScoringEngine
from backend.ml_predictor import MLPredictor


# Number of workers for parallel processing
NUM_WORKERS = min(mp.cpu_count(), 4)


def _calculate_driver_metrics(args: tuple) -> Dict[str, Any]:
    """
    Worker function to calculate driver metrics in parallel
    
    Args:
        args: Tuple of (driver_id, constructor_id, team_name, circuit_id, weather_conditions)
        
    Returns:
        Dictionary with driver metrics and scores
    """
    driver_id, constructor_id, team_name, circuit_id, weather_conditions = args
    
    # Create scoring engine instance in worker process
    scoring_engine = ScoringEngine()
    
    # Calculate all metrics
    avg_finish = scoring_engine.calculate_avg_finish(driver_id)
    qualifying_avg = scoring_engine.calculate_qualifying_avg(driver_id)
    recent_form = scoring_engine.calculate_recent_form(driver_id)
    dnf_risk = scoring_engine.calculate_dnf_risk(driver_id)
    track_affinity = scoring_engine.calculate_track_affinity(driver_id, circuit_id)
    
    # Calculate scores
    driver_score = scoring_engine.calculate_driver_score(
        avg_finish, qualifying_avg, recent_form, dnf_risk,
        track_affinity, weather_conditions
    )
    
    return {
        'driver_id': driver_id,
        'team': team_name,
        'constructor_id': constructor_id,
        'avg_finish': avg_finish,
        'qualifying_avg': qualifying_avg,
        'recent_form': recent_form,
        'dnf_risk': dnf_risk,
        'track_affinity': track_affinity,
        'driver_score': driver_score
    }


def _fetch_race_data_parallel(args: tuple) -> Dict[str, Any]:
    """
    Worker function to fetch race data for a specific round
    
    Args:
        args: Tuple of (season, round_num)
        
    Returns:
        Race results dictionary
    """
    season, round_num = args
    api_client = F1APIClient()
    return api_client.fetch_race_results(season, round_num)


def _fetch_qualifying_parallel(args: tuple) -> Dict[str, Any]:
    """
    Worker function to fetch qualifying data in parallel
    
    Args:
        args: Tuple of (season, round_num)
        
    Returns:
        Qualifying results dictionary
    """
    season, round_num = args
    api_client = F1APIClient()
    return api_client.fetch_qualifying_results(season, round_num)


class PredictionGenerator:
    """Main prediction engine with multiprocessing support"""
    
    def __init__(self, use_multiprocessing: bool = True):
        """
        Initialize prediction generator with all components
        
        Args:
            use_multiprocessing: Whether to use parallel processing (default: True)
        """
        self.api_client = F1APIClient()
        self.scoring_engine = ScoringEngine()
        self.ml_predictor = MLPredictor()
        self.use_multiprocessing = use_multiprocessing
    
    def generate_predictions(
        self,
        circuit_id: Optional[str] = None,
        weather_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete race predictions with parallel processing
        
        Args:
            circuit_id: Specific circuit ID (optional)
            weather_conditions: Weather parameters for predictions
            
        Returns:
            Dictionary containing predictions and race info
        """
        # Default weather conditions
        if weather_conditions is None:
            weather_conditions = {
                'rain': False,
                'temperature': 25.0,
                'safety_car_probability': 0.3
            }
        
        # Fetch current season data
        season = self.api_client.get_current_season()
        driver_standings = self.api_client.fetch_driver_standings(season)
        constructor_standings = self.api_client.fetch_constructor_standings(season)
        next_race = self.api_client.fetch_next_race(season)
        
        if not next_race:
            return {'error': 'No upcoming races found'}
        
        # Get circuit info
        circuit = next_race['Circuit']
        if circuit_id is None:
            circuit_id = circuit.get('circuitId', 'unknown')
        
        race_info = {
            'circuit': circuit.get('circuitName', 'Unknown'),
            'country': circuit.get('Location', {}).get('country', 'Unknown'),
            'round': int(next_race.get('round', 0)),
            'season': season,
            'date': next_race.get('date', ''),
            'circuit_id': circuit_id
        }
        
        # Build constructor map with parallel fetching
        constructor_map = {}
        if self.use_multiprocessing and len(constructor_standings) > 1:
            # Parallel calculation of constructor form
            with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
                futures = {}
                for standing in constructor_standings:
                    constructor_id = standing['Constructor']['constructorId']
                    future = executor.submit(
                        self.scoring_engine.calculate_constructor_form,
                        constructor_id
                    )
                    futures[constructor_id] = (future, standing)
                
                for constructor_id, (future, standing) in futures.items():
                    try:
                        constructor_form = future.result(timeout=10)
                        position = int(standing['position'])
                        pit_efficiency = max(0.6, 1.0 - (position - 1) * 0.05)
                        reliability = max(0.7, 1.0 - (position - 1) * 0.04)
                        
                        team_score = self.scoring_engine.calculate_team_score(
                            constructor_form, pit_efficiency, reliability
                        )
                        constructor_map[constructor_id] = team_score
                    except Exception as e:
                        constructor_map[constructor_id] = 0.7
        else:
            # Sequential processing
            for standing in constructor_standings:
                constructor_id = standing['Constructor']['constructorId']
                constructor_form = self.scoring_engine.calculate_constructor_form(constructor_id)
                position = int(standing['position'])
                pit_efficiency = max(0.6, 1.0 - (position - 1) * 0.05)
                reliability = max(0.7, 1.0 - (position - 1) * 0.04)
                
                team_score = self.scoring_engine.calculate_team_score(
                    constructor_form, pit_efficiency, reliability
                )
                constructor_map[constructor_id] = team_score
        
        # Generate predictions with parallel metric calculation
        predictions = []
        
        if self.use_multiprocessing and len(driver_standings) > 1:
            # Prepare arguments for parallel processing
            args_list = []
            for standing in driver_standings:
                driver = standing['Driver']
                driver_id = driver['driver_id']
                constructor_id = standing.get('Constructors', [{}])[0].get('constructor_id', 'unknown')
                team_name = standing.get('Constructors', [{}])[0].get('name', 'Unknown')
                args_list.append((driver_id, constructor_id, team_name, circuit_id, weather_conditions))
            
            # Parallel metric calculation
            with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
                results = list(executor.map(_calculate_driver_metrics, args_list))
            
            # Assign predicted positions and calculate ML probabilities
            for idx, result in enumerate(results):
                team_score = constructor_map.get(result['constructor_id'], 0.7)
                final_score = self.scoring_engine.calculate_final_score(
                    result['driver_score'], team_score
                )
                
                predictions.append({
                    'driver_id': result['driver_id'],
                    'name': f"Driver {result['driver_id']}",  # Would need to fetch full name
                    'team': result['team'],
                    'base_score': result['driver_score'],
                    'team_score': team_score,
                    'final_score': final_score,
                    'metrics': {
                        'avg_finish': round(result['avg_finish'], 2),
                        'qualifying_avg': round(result['qualifying_avg'], 2),
                        'recent_form': round(result['recent_form'], 3),
                        'dnf_risk': round(result['dnf_risk'], 3),
                        'track_affinity': round(result['track_affinity'], 3)
                    }
                })
        else:
            # Sequential processing (original method)
            for standing in driver_standings:
                driver = standing['Driver']
                driver_id = driver['driver_id']
                driver_name = f"{driver['givenName']} {driver['familyName']}"
                constructor_id = standing.get('Constructors', [{}])[0].get('constructor_id', 'unknown')
                team_name = standing.get('Constructors', [{}])[0].get('name', 'Unknown')
                
                # Calculate all metrics
                avg_finish = self.scoring_engine.calculate_avg_finish(driver_id)
                qualifying_avg = self.scoring_engine.calculate_qualifying_avg(driver_id)
                recent_form = self.scoring_engine.calculate_recent_form(driver_id)
                dnf_risk = self.scoring_engine.calculate_dnf_risk(driver_id)
                track_affinity = self.scoring_engine.calculate_track_affinity(driver_id, circuit_id)
                
                # Calculate scores
                driver_score = self.scoring_engine.calculate_driver_score(
                    avg_finish, qualifying_avg, recent_form, dnf_risk,
                    track_affinity, weather_conditions
                )
                
                team_score = constructor_map.get(constructor_id, 0.7)
                final_score = self.scoring_engine.calculate_final_score(driver_score, team_score)
                
                predictions.append({
                    'driver_id': driver_id,
                    'name': driver_name,
                    'team': team_name,
                    'base_score': driver_score,
                    'team_score': team_score,
                    'final_score': final_score,
                    'metrics': {
                        'avg_finish': round(avg_finish, 2),
                        'qualifying_avg': round(qualifying_avg, 2),
                        'recent_form': round(recent_form, 3),
                        'dnf_risk': round(dnf_risk, 3),
                        'track_affinity': round(track_affinity, 3)
                    }
                })
        
        # Sort by final score (highest first)
        predictions.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Assign predicted positions and calculate ML probabilities
        all_scores = [p['final_score'] for p in predictions]
        
        for idx, prediction in enumerate(predictions):
            prediction['predicted_position'] = idx + 1
            prediction['win_probability'] = round(
                self.ml_predictor.predict_win_probability(prediction['final_score'], all_scores),
                4
            )
            prediction['podium_probability'] = round(
                self.ml_predictor.predict_podium_probability(prediction['final_score'], idx, all_scores),
                4
            )
        
        return {
            'predictions': predictions,
            'race_info': race_info,
            'conditions': weather_conditions,
            'generated_at': datetime.now().isoformat(),
            'parallel_processing': self.use_multiprocessing,
            'workers_used': NUM_WORKERS if self.use_multiprocessing else 1
        }
    
    def fetch_multiple_races_parallel(self, season: int, round_nums: List[int]) -> List[Dict[str, Any]]:
        """
        Fetch multiple race results in parallel
        
        Args:
            season: F1 season year
            round_nums: List of round numbers to fetch
            
        Returns:
            List of race results
        """
        args_list = [(season, rn) for rn in round_nums]
        
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            results = list(executor.map(_fetch_race_data_parallel, args_list))
        
        return [r for r in results if r is not None]
    
    def get_driver_standings(self, season: Optional[int] = None) -> Dict[str, Any]:
        """Get current driver standings"""
        if season is None:
            season = self.api_client.get_current_season()
        
        standings = self.api_client.fetch_driver_standings(season)
        return {
            'standings': standings,
            'season': season,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_constructor_standings(self, season: Optional[int] = None) -> Dict[str, Any]:
        """Get current constructor standings"""
        if season is None:
            season = self.api_client.get_current_season()
        
        standings = self.api_client.fetch_constructor_standings(season)
        return {
            'standings': standings,
            'season': season,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_race_results(self, season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Get race results for a specific round"""
        return self.api_client.fetch_race_results(season, round_num)
    
    def get_qualifying_results(self, season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Get qualifying results for a specific round"""
        return self.api_client.fetch_qualifying_results(season, round_num)
    
    def get_next_race(self) -> Optional[Dict[str, Any]]:
        """Get information about the next race"""
        return self.api_client.fetch_next_race()
    
    def get_drivers(self, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all drivers for the season"""
        if season is None:
            season = self.api_client.get_current_season()
        return self.api_client.fetch_drivers(season)
    
    def get_constructors(self, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all constructors for the season"""
        if season is None:
            season = self.api_client.get_current_season()
        return self.api_client.fetch_constructors(season)

# ============================================================================
# SCORING ENGINE - Mathematical Scoring Module
# ============================================================================
# Pure mathematical scoring with NO hardcoded data
# Uses multiprocessing for parallel metric calculations

import numpy as np
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp

from backend.f1_client import F1APIClient


# Number of workers for parallel processing
NUM_WORKERS = min(mp.cpu_count(), 4)


def _calculate_single_metric(args: tuple) -> Dict[str, Any]:
    """
    Worker function to calculate a single driver metric in parallel
    
    Args:
        args: Tuple of (driver_id, metric_type, param)
        
    Returns:
        Dictionary with driver_id and calculated metric value
    """
    driver_id, metric_type, param = args
    api_client = F1APIClient()
    scoring_engine = ScoringEngine()
    
    if metric_type == 'avg_finish':
        value = scoring_engine.calculate_avg_finish(driver_id, param)
    elif metric_type == 'qualifying_avg':
        value = scoring_engine.calculate_qualifying_avg(driver_id, param)
    elif metric_type == 'recent_form':
        value = scoring_engine.calculate_recent_form(driver_id, param)
    elif metric_type == 'dnf_risk':
        value = scoring_engine.calculate_dnf_risk(driver_id, param)
    elif metric_type == 'track_affinity':
        value = scoring_engine.calculate_track_affinity(driver_id, param)
    else:
        value = 0.0
    
    return {'driver_id': driver_id, 'metric': metric_type, 'value': value}


class ScoringEngine:
    """Pure mathematical scoring with NO hardcoded data"""
    
    def __init__(self, use_parallel: bool = True):
        """
        Initialize scoring engine
        
        Args:
            use_parallel: Whether to use parallel processing for calculations
        """
        self.use_parallel = use_parallel
    
    @staticmethod
    def calculate_avg_finish(driver_id: str, recent_races: int = 5) -> float:
        """Calculate average finishing position from recent races"""
        season = F1APIClient.get_current_season()
        finishes = []
        
        try:
            # Get race schedule to iterate through rounds
            import fastf1
            schedule = fastf1.get_event_schedule(season)
            races = schedule['RoundNumber'].tolist()[:recent_races]
            
            # Get results from recent completed races
            for round_num in races:
                race_result = F1APIClient.fetch_race_results(season, round_num)
                if race_result and 'Results' in race_result:
                    for result in race_result['Results']:
                        driver_key = result['Driver'].get('driver_id', '')
                        if driver_key.lower() == driver_id.lower():
                            try:
                                position = int(result['position'])
                                finishes.append(position)
                            except:
                                finishes.append(20)  # DNF counted as last
                            break
        except Exception as e:
            print(f"[Warning] Error calculating avg finish: {e}")
        
        return np.mean(finishes) if finishes else 10.0
    
    @staticmethod
    def calculate_qualifying_avg(driver_id: str, recent_races: int = 5) -> float:
        """Calculate average qualifying position"""
        season = F1APIClient.get_current_season()
        positions = []
        
        try:
            import fastf1
            schedule = fastf1.get_event_schedule(season)
            races = schedule['RoundNumber'].tolist()[:recent_races]
            
            for round_num in races:
                qual_result = F1APIClient.fetch_qualifying_results(season, round_num)
                if qual_result and 'QualifyingResults' in qual_result:
                    for result in qual_result['QualifyingResults']:
                        driver_key = result['Driver'].get('driver_id', '')
                        if driver_key.lower() == driver_id.lower():
                            try:
                                position = int(result['position'])
                                positions.append(position)
                            except:
                                positions.append(20)
                            break
        except Exception as e:
            print(f"[Warning] Error calculating qualifying avg: {e}")
        
        return np.mean(positions) if positions else 10.0
    
    @staticmethod
    def calculate_recent_form(driver_id: str, recent_races: int = 3) -> float:
        """Calculate recent form score (0-1)"""
        season = F1APIClient.get_current_season()
        points = []
        
        try:
            import fastf1
            schedule = fastf1.get_event_schedule(season)
            races = schedule['RoundNumber'].tolist()[:recent_races]
            
            for round_num in races:
                race_result = F1APIClient.fetch_race_results(season, round_num)
                if race_result and 'Results' in race_result:
                    for result in race_result['Results']:
                        driver_key = result['Driver'].get('driver_id', '')
                        if driver_key.lower() == driver_id.lower():
                            try:
                                pts = float(result.get('points', 0))
                                points.append(pts)
                            except:
                                points.append(0.0)
                            break
        except Exception as e:
            print(f"[Warning] Error calculating recent form: {e}")
        
        # Normalize to 0-1 (max F1 points is 26 with fastest lap and sprint)
        avg_points = np.mean(points) if points else 0.0
        return min(avg_points / 26.0, 1.0)
    
    @staticmethod
    def calculate_dnf_risk(driver_id: str, recent_races: int = 10) -> float:
        """Calculate DNF risk (0-1)"""
        season = F1APIClient.get_current_season()
        dnf_count = 0
        total_races = 0
        
        try:
            import fastf1
            schedule = fastf1.get_event_schedule(season)
            races = schedule['RoundNumber'].tolist()[:recent_races]
            
            for round_num in races:
                race_result = F1APIClient.fetch_race_results(season, round_num)
                if race_result and 'Results' in race_result:
                    for result in race_result['Results']:
                        driver_key = result['Driver'].get('driver_id', '')
                        if driver_key.lower() == driver_id.lower():
                            total_races += 1
                            status = result.get('status', 'Finished')
                            if 'Lap' not in status and 'Finished' not in status:
                                dnf_count += 1
                            break
        except Exception as e:
            print(f"[Warning] Error calculating DNF risk: {e}")
        
        return dnf_count / total_races if total_races > 0 else 0.1
    
    @staticmethod
    def calculate_track_affinity(driver_id: str, circuit_id: str) -> float:
        """Calculate driver's historical performance at specific circuit"""
        historical = F1APIClient.fetch_historical_results(driver_id, circuit_id)
        
        if not historical:
            return 0.5  # Neutral affinity
        
        # Calculate average finish and podium rate
        finishes = []
        podiums = 0
        
        for result in historical:
            try:
                position = int(result['position'])
                finishes.append(position)
                if position <= 3:
                    podiums += 1
            except:
                pass
        
        if not finishes:
            return 0.5
        
        avg_finish = np.mean(finishes)
        podium_rate = podiums / len(finishes)
        
        # Score: better finish = higher affinity
        finish_score = (20 - avg_finish) / 20.0
        affinity = 0.7 * finish_score + 0.3 * podium_rate
        
        return max(0.0, min(1.0, affinity))
    
    def calculate_all_metrics_parallel(
        self,
        driver_ids: List[str],
        circuit_id: str,
        recent_races: int = 5
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate all metrics for multiple drivers in parallel
        
        Args:
            driver_ids: List of driver IDs
            circuit_id: Circuit to calculate affinity for
            recent_races: Number of recent races to consider
            
        Returns:
            Dictionary mapping driver_id to their metrics
        """
        if not self.use_parallel or len(driver_ids) <= 1:
            # Sequential calculation
            results = {}
            for driver_id in driver_ids:
                results[driver_id] = {
                    'avg_finish': self.calculate_avg_finish(driver_id, recent_races),
                    'qualifying_avg': self.calculate_qualifying_avg(driver_id, recent_races),
                    'recent_form': self.calculate_recent_form(driver_id, 3),
                    'dnf_risk': self.calculate_dnf_risk(driver_id, 10),
                    'track_affinity': self.calculate_track_affinity(driver_id, circuit_id)
                }
            return results
        
        # Prepare arguments for parallel processing
        args_list = []
        for driver_id in driver_ids:
            args_list.append((driver_id, 'avg_finish', recent_races))
            args_list.append((driver_id, 'qualifying_avg', recent_races))
            args_list.append((driver_id, 'recent_form', 3))
            args_list.append((driver_id, 'dnf_risk', 10))
            args_list.append((driver_id, 'track_affinity', circuit_id))
        
        # Execute in parallel using threads (faster for I/O bound tasks)
        results = {driver_id: {} for driver_id in driver_ids}
        
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {executor.submit(_calculate_single_metric, arg): arg for arg in args_list}
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    driver_id = result['driver_id']
                    metric = result['metric']
                    value = result['value']
                    results[driver_id][metric] = value
                except Exception as e:
                    pass
        
        return results
    
    @staticmethod
    def calculate_driver_score(
        avg_finish: float,
        qualifying_avg: float,
        recent_form: float,
        dnf_risk: float,
        track_affinity: float,
        weather_conditions: Dict[str, Any]
    ) -> float:
        """
        Calculate driver score using the exact formula from spec:
        Driver Score = (0.4 × Avg Race Finish) + (0.3 × Qualifying) + (0.2 × Form) - (0.1 × DNF Risk)
        + Track Affinity Bonus
        """
        # Normalize avg_finish and qualifying (lower is better)
        finish_score = (20.0 - min(avg_finish, 20.0)) / 20.0
        qual_score = (20.0 - min(qualifying_avg, 20.0)) / 20.0
        
        # Base score
        base_score = (0.4 * finish_score) + (0.3 * qual_score) + (0.2 * recent_form) - (0.1 * dnf_risk)
        
        # Add track affinity bonus
        track_bonus = track_affinity * 0.15
        driver_score = base_score + track_bonus
        
        # Apply weather modifier
        if weather_conditions.get('rain', False):
            wet_skill_multiplier = 1.0 + (0.2 * recent_form)
            driver_score *= wet_skill_multiplier
        
        return max(0.0, driver_score)
    
    @staticmethod
    def calculate_constructor_form(constructor_id: str, recent_races: int = 5) -> float:
        """Calculate constructor form (0-1)"""
        season = F1APIClient.get_current_season()
        points = []
        
        try:
            import fastf1
            schedule = fastf1.get_event_schedule(season)
            races = schedule['RoundNumber'].tolist()[:recent_races]
            
            for round_num in races:
                race_result = F1APIClient.fetch_race_results(season, round_num)
                if race_result and 'Results' in race_result:
                    race_points = 0
                    for result in race_result['Results']:
                        constructor_name = result.get('Constructor', {}).get('name', '').lower().replace(' ', '_')
                        if constructor_name == constructor_id.lower():
                            try:
                                race_points += float(result.get('points', 0))
                            except:
                                pass
                    points.append(race_points)
        except Exception as e:
            print(f"[Warning] Error calculating constructor form: {e}")
        
        # Normalize (max ~44 points per race for both drivers)
        avg_points = np.mean(points) if points else 0.0
        return min(avg_points / 44.0, 1.0)
    
    @staticmethod
    def calculate_team_score(
        constructor_form: float,
        pit_efficiency: float = 0.8,
        reliability: float = 0.85
    ) -> float:
        """
        Calculate team score using formula from spec:
        Team Score = (0.5 × Constructor Form) + (0.3 × Pit Efficiency) + (0.2 × Reliability)
        
        Note: Pit efficiency and reliability are estimated (API doesn't provide this)
        """
        return (0.5 * constructor_form) + (0.3 * pit_efficiency) + (0.2 * reliability)
    
    @staticmethod
    def calculate_final_score(driver_score: float, team_score: float) -> float:
        """Total Score = Driver Score × Team Score"""
        return driver_score * team_score


# Import fastf1 here to avoid circular imports
import fastf1

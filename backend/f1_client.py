# ============================================================================
# F1 API CLIENT - Data Fetching Module
# ============================================================================
# Dynamic F1 data fetcher using fastf1 library - NO hardcoded data
# This module handles all communication with the F1 data source

import fastf1
import fastf1.plotting
from datetime import datetime
from typing import List, Dict, Optional, Any

# Initialize fastf1 plotting
fastf1.plotting.setup_mpl()


class F1APIClient:
    """Dynamic F1 data fetcher using fastf1 library - NO hardcoded data"""
    
    @staticmethod
    def get_current_season() -> int:
        """Get current F1 season year"""
        return datetime.now().year
    
    @staticmethod
    def fetch_drivers(season: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all drivers for a season"""
        if season is None:
            season = F1APIClient.get_current_season()
        
        try:
            schedule = fastf1.get_event_schedule(season)
            drivers = []
            # Get drivers from the first race weekend
            session = fastf1.get_session(season, 1, 'Q')
            session.load()
            for driver in session.results:
                drivers.append({
                    'driverId': driver['Abbreviation'],
                    'givenName': driver['FirstName'],
                    'familyName': driver['LastName'],
                    'nationality': driver['TeamName'],
                    'permanentNumber': str(driver['TeamId'])
                })
            return drivers
        except Exception as e:
            print(f"[Warning] Error fetching drivers: {e}")
            return []
    
    @staticmethod
    def fetch_constructors(season: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all constructors for a season"""
        if season is None:
            season = F1APIClient.get_current_season()
        
        try:
            session = fastf1.get_session(season, 1, 'Q')
            session.load()
            constructors = []
            seen_teams = set()
            for driver in session.results:
                team = driver['TeamName']
                if team not in seen_teams:
                    seen_teams.add(team)
                    constructors.append({
                        'constructorId': team.lower().replace(' ', '_'),
                        'name': team,
                        'nationality': 'Unknown'
                    })
            return constructors
        except Exception as e:
            print(f"[Warning] Error fetching constructors: {e}")
            return []
    
    @staticmethod
    def fetch_driver_standings(season: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch current driver standings"""
        if season is None:
            season = F1APIClient.get_current_season()
        
        try:
            session = fastf1.get_session(season, 'latest', 'R')
            session.load()
            standings = []
            for idx, driver in enumerate(session.results.itertuples(), 1):
                standings.append({
                    'position': str(idx),
                    'points': str(getattr(driver, 'Points', 0)),
                    'Driver': {
                        'driverId': driver.Abbreviation,
                        'givenName': driver.FirstName,
                        'familyName': driver.LastName
                    }
                })
            return standings
        except Exception as e:
            print(f"[Warning] Error fetching driver standings: {e}")
            return []
    
    @staticmethod
    def fetch_constructor_standings(season: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch current constructor standings"""
        if season is None:
            season = F1APIClient.get_current_season()
        
        try:
            # fastf1 doesn't have direct constructor standings, derive from driver data
            session = fastf1.get_session(season, 'latest', 'R')
            session.load()
            
            team_points = {}
            for driver in session.results.itertuples():
                team = driver.TeamName
                points = getattr(driver, 'Points', 0)
                if team in team_points:
                    team_points[team] += points
                else:
                    team_points[team] = points
            
            standings = []
            for idx, (team, points) in enumerate(sorted(team_points.items(), key=lambda x: x[1], reverse=True), 1):
                standings.append({
                    'position': str(idx),
                    'points': str(points),
                    'Constructor': {
                        'constructorId': team.lower().replace(' ', '_'),
                        'name': team
                    }
                })
            return standings
        except Exception as e:
            print(f"[Warning] Error fetching constructor standings: {e}")
            return []
    
    @staticmethod
    def fetch_race_results(season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Fetch results for a specific race"""
        try:
            session = fastf1.get_session(season, round_num, 'R')
            session.load()
            
            results = []
            for driver in session.results.itertuples():
                results.append({
                    'position': str(getattr(driver, 'Position', 0)),
                    'Driver': {
                        'driverId': driver.Abbreviation,
                        'givenName': driver.FirstName,
                        'familyName': driver.LastName
                    },
                    'Constructor': {
                        'name': driver.TeamName
                    },
                    'points': str(getattr(driver, 'Points', 0)),
                    'status': getattr(driver, 'Status', 'Finished')
                })
            
            return {'Results': results, 'season': season, 'round': round_num}
        except Exception as e:
            print(f"[Warning] Error fetching race results: {e}")
            return None
    
    @staticmethod
    def fetch_qualifying_results(season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Fetch qualifying results for a specific race"""
        try:
            session = fastf1.get_session(season, round_num, 'Q')
            session.load()
            
            results = []
            for driver in session.results.itertuples():
                results.append({
                    'position': str(getattr(driver, 'Position', 0)),
                    'Driver': {
                        'driverId': driver.Abbreviation,
                        'givenName': driver.FirstName,
                        'familyName': driver.LastName
                    },
                    'Q1': str(getattr(driver, 'Q1', '')),
                    'Q2': str(getattr(driver, 'Q2', '')),
                    'Q3': str(getattr(driver, 'Q3', ''))
                })
            
            return {'QualifyingResults': results, 'season': season, 'round': round_num}
        except Exception as e:
            print(f"[Warning] Error fetching qualifying results: {e}")
            return None
    
    @staticmethod
    def fetch_next_race(season: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch next upcoming race"""
        if season is None:
            season = F1APIClient.get_current_season()
        
        try:
            schedule = fastf1.get_event_schedule(season)
            now = datetime.now()
            
            for _, event in schedule.iterrows():
                event_date = event['EventDate']
                if hasattr(event_date, 'tz_localize'):
                    event_date = event_date.tz_localize(None)
                if event_date > now:
                    return {
                        'season': str(season),
                        'round': str(event['RoundNumber']),
                        'raceName': event['EventName'],
                        'date': event['EventDate'].strftime('%Y-%m-%d') if hasattr(event['EventDate'], 'strftime') else str(event['EventDate'])[:10],
                        'time': '12:00:00Z',
                        'Circuit': {
                            'circuitName': event.get('Location', 'Unknown')
                        }
                    }
            return None
        except Exception as e:
            print(f"[Warning] Error fetching next race: {e}")
            return None
    
    @staticmethod
    def fetch_historical_results(driver_id: str, circuit_id: str, seasons: int = 5) -> List[Dict[str, Any]]:
        """Fetch historical results for driver at specific circuit"""
        results = []
        current_season = F1APIClient.get_current_season()
        
        for year in range(current_season - seasons, current_season):
            try:
                schedule = fastf1.get_event_schedule(year)
                # Find the race at the requested circuit
                for round_num in range(1, len(schedule) + 1):
                    session = fastf1.get_session(year, round_num, 'R')
                    session.load()
                    
                    for driver in session.results.itertuples():
                        if driver.Abbreviation.lower() == driver_id.lower():
                            results.append({
                                'season': year,
                                'round': round_num,
                                'position': getattr(driver, 'Position', 0),
                                'points': getattr(driver, 'Points', 0)
                            })
                            break
            except Exception as e:
                print(f"[Warning] Error fetching historical data for {year}: {e}")
        
        return results

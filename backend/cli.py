# ============================================================================
# CLI INTERFACE - Terminal Output Module
# ============================================================================
# CLI functions for displaying predictions in terminal
# Handles all terminal output formatting

from typing import Dict, Any, List
from datetime import datetime


def print_predictions_cli(result: Dict[str, Any]) -> None:
    """
    Print predictions in a formatted way to terminal
    
    Args:
        result: Prediction result dictionary
    """
    if 'error' in result:
        print(f"\n[!] Error: {result['error']}")
        return
    
    race_info = result.get('race_info', {})
    predictions = result.get('predictions', [])
    conditions = result.get('conditions', {})
    generated_at = result.get('generated_at', '')
    
    print("\n" + "="*80)
    print("[F1] RACE PREDICTIONS")
    print("="*80)
    print(f"\n[Circuit] {race_info.get('circuit', 'N/A')}")
    print(f"[Country] {race_info.get('country', 'N/A')}")
    print(f"[Round]   {race_info.get('round', 'N/A')} | Season: {race_info.get('season', 'N/A')}")
    print(f"[Date]    {race_info.get('date', 'N/A')}")
    
    # Weather conditions
    rain_status = "RAIN" if conditions.get('rain', False) else "DRY"
    temp = conditions.get('temperature', 25.0)
    print(f"\n[Weather] {rain_status} | Temperature: {temp}C")
    
    print("\n" + "-"*80)
    print(f"{'POS':<4} {'DRIVER':<22} {'TEAM':<18} {'SCORE':<8} {'WIN%':<8} {'POD%':<8}")
    print("-"*80)
    
    for pred in predictions[:20]:  # Show top 20
        pos = pred.get('predicted_position', 0)
        name = pred.get('name', 'N/A')[:20]
        team = pred.get('team', 'N/A')[:16]
        score = pred.get('final_score', 0)
        win_prob = pred.get('win_probability', 0) * 100
        podium_prob = pred.get('podium_probability', 0) * 100
        
        # Add medal indicators for top 3
        medal = "1st" if pos == 1 else "2nd" if pos == 2 else "3rd" if pos == 3 else f"{pos}th"
        
        print(f"{medal:<4} {name:<22} {team:<18} {score:<8.4f} {win_prob:<7.1f}% {podium_prob:<7.1f}%")
    
    print("-"*80)
    print(f"\n[Generated] {generated_at}")
    print("="*80 + "\n")


def get_demo_predictions() -> Dict[str, Any]:
    """
    Generate demo predictions when API is unavailable
    
    Returns:
        Demo prediction data
    """
    import random
    
    # Get a realistic future date (next Sunday roughly)
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_race_date = today + datetime.timedelta(days=days_until_sunday)
    
    demo_drivers = [
        ("max_verstappen", "Max Verstappen", "Red Bull Racing"),
        ("lando_norris", "Lando Norris", "McLaren"),
        ("charles_leclerc", "Charles Leclerc", "Ferrari"),
        ("george_russell", "George Russell", "Mercedes"),
        ("oscar_piastri", "Oscar Piastri", "McLaren"),
        ("carlos_sainz", "Carlos Sainz", "Ferrari"),
        ("lewis_hamilton", "Lewis Hamilton", "Ferrari"),
        ("fernando_alonso", "Fernando Alonso", "Aston Martin"),
        ("pierre_gasly", "Pierre Gasly", "Alpine"),
        ("alex_albon", "Alex Albon", "Williams"),
    ]
    
    predictions = []
    for idx, (driver_id, name, team) in enumerate(demo_drivers):
        base_score = random.uniform(0.6, 0.9)
        team_score = random.uniform(0.7, 0.95)
        final_score = base_score * team_score
        
        predictions.append({
            'driver_id': driver_id,
            'name': name,
            'team': team,
            'base_score': base_score,
            'team_score': team_score,
            'final_score': final_score,
            'predicted_position': idx + 1,
            'win_probability': max(0, 0.4 - idx * 0.04) if idx < 5 else 0.01,
            'podium_probability': max(0, 0.9 - idx * 0.08) if idx < 10 else 0.01,
            'metrics': {
                'avg_finish': round(random.uniform(1.5, 12.0), 2),
                'qualifying_avg': round(random.uniform(1.0, 15.0), 2),
                'recent_form': round(random.uniform(0.3, 0.9), 3),
                'dnf_risk': round(random.uniform(0.02, 0.15), 3),
                'track_affinity': round(random.uniform(0.4, 0.9), 3)
            }
        })
    
    return {
        'predictions': predictions,
        'race_info': {
            'circuit': 'Next F1 Circuit (API Unavailable)',
            'country': 'TBD',
            'round': 1,
            'season': datetime.now().year,
            'date': next_race_date.strftime('%Y-%m-%d')
        },
        'conditions': {'rain': False, 'temperature': 25.0},
        'generated_at': datetime.now().isoformat()
    }


def print_driver_standings(standings: List[Dict[str, Any]]) -> None:
    """
    Print driver standings in terminal
    
    Args:
        standings: List of driver standings
    """
    print("\n" + "="*60)
    print("[F1] DRIVER STANDINGS")
    print("="*60)
    print(f"{'POS':<4} {'DRIVER':<25} {'POINTS':<10}")
    print("-"*60)
    
    for standing in standings[:20]:
        pos = standing.get('position', '0')
        driver = standing.get('Driver', {})
        name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}"
        points = standing.get('points', '0')
        
        print(f"{pos:<4} {name:<25} {points:<10}")
    
    print("="*60 + "\n")


def print_constructor_standings(standings: List[Dict[str, Any]]) -> None:
    """
    Print constructor standings in terminal
    
    Args:
        standings: List of constructor standings
    """
    print("\n" + "="*60)
    print("[F1] CONSTRUCTOR STANDINGS")
    print("="*60)
    print(f"{'POS':<4} {'TEAM':<25} {'POINTS':<10}")
    print("-"*60)
    
    for standing in standings[:10]:
        pos = standing.get('position', '0')
        constructor = standing.get('Constructor', {})
        name = constructor.get('name', 'Unknown')
        points = standing.get('points', '0')
        
        print(f"{pos:<4} {name:<25} {points:<10}")
    
    print("="*60 + "\n")

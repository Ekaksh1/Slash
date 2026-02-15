# ============================================================================
# F1 RACE PREDICTOR - MAIN APPLICATION
# ============================================================================
# Flask REST API server with CLI support
# Uses multiprocessing for parallel execution to improve performance

import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Flask imports
from flask import Flask, request, jsonify
from flask_cors import CORS

# Backend module imports
from backend.prediction_generator import PredictionGenerator
from backend.f1_client import F1APIClient
from backend.cli import print_predictions_cli, get_demo_predictions

# ============================================================================
# FLASK APP CONFIGURATION
# ============================================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize prediction generator with multiprocessing enabled
# Set use_multiprocessing=False to disable parallel processing
prediction_generator = PredictionGenerator(use_multiprocessing=True)

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    import multiprocessing as mp
    return jsonify({
        'status': 'healthy',
        'service': 'F1 Race Predictor',
        'version': '1.0.0',
        'multiprocessing': {
            'enabled': prediction_generator.use_multiprocessing,
            'cpu_count': mp.cpu_count(),
            'workers': min(mp.cpu_count(), 4)
        }
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Generate race predictions
    
    Request Body:
    {
        "circuit_id": "monza" (optional),
        "weather_conditions": {
            "rain": false,
            "temperature": 25,
            "safety_car_probability": 0.3
        } (optional)
    }
    
    Response includes:
    {
        "predictions": [...],
        "race_info": {...},
        "conditions": {...},
        "generated_at": "...",
        "parallel_processing": true/false,
        "workers_used": 4
    }
    """
    try:
        data = request.get_json() or {}
        
        circuit_id = data.get('circuit_id')
        weather_conditions = data.get('weather_conditions')
        
        result = prediction_generator.generate_predictions(
            circuit_id=circuit_id,
            weather_conditions=weather_conditions
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': 'prediction_failed',
            'message': str(e)
        }), 500


@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    """Get all drivers for current season"""
    try:
        season = request.args.get('season', type=int)
        drivers = prediction_generator.get_drivers(season)
        
        return jsonify({
            'drivers': drivers,
            'season': season or F1APIClient.get_current_season(),
            'count': len(drivers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/constructors', methods=['GET'])
def get_constructors():
    """Get all constructors for current season"""
    try:
        season = request.args.get('season', type=int)
        constructors = prediction_generator.get_constructors(season)
        
        return jsonify({
            'constructors': constructors,
            'season': season or F1APIClient.get_current_season(),
            'count': len(constructors)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/standings/drivers', methods=['GET'])
def get_driver_standings():
    """Get current driver standings"""
    try:
        season = request.args.get('season', type=int)
        round_num = request.args.get('round', type=int)
        
        standings = prediction_generator.get_driver_standings(season)
        
        return jsonify({
            'StandingsTable': {
                'StandingsLists': [{
                    'season': str(standings.get('season', '')),
                    'round': str(round_num or ''),
                    'DriverStandings': standings.get('standings', [])
                }]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/standings/constructors', methods=['GET'])
def get_constructor_standings():
    """Get current constructor standings"""
    try:
        season = request.args.get('season', type=int)
        
        standings = prediction_generator.get_constructor_standings(season)
        
        return jsonify({
            'StandingsTable': {
                'StandingsLists': [{
                    'season': str(standings.get('season', '')),
                    'ConstructorStandings': standings.get('standings', [])
                }]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/next-race', methods=['GET'])
def get_next_race():
    """Get next upcoming race"""
    try:
        season = request.args.get('season', type=int)
        if season:
            next_race = F1APIClient.fetch_next_race(season)
        else:
            next_race = prediction_generator.get_next_race()
        
        if next_race:
            return jsonify(next_race)
        return jsonify({'error': 'No upcoming races found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/results/<int:season>/<int:round_num>', methods=['GET'])
def get_race_results(season, round_num):
    """Get race results for a specific round"""
    try:
        results = prediction_generator.get_race_results(season, round_num)
        if results:
            return jsonify(results)
        return jsonify({'error': 'Results not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/qualifying/<int:season>/<int:round_num>', methods=['GET'])
def get_qualifying_results(season, round_num):
    """Get qualifying results for a specific round"""
    try:
        results = prediction_generator.get_qualifying_results(season, round_num)
        if results:
            return jsonify(results)
        return jsonify({'error': 'Qualifying results not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CLI MODE
# ============================================================================

def run_cli_mode():
    """Run in CLI mode - generate and display predictions in terminal"""
    print("\n[F1] Race Predictor - CLI Mode")
    print("Fetching data from fastf1 F1 API...\n")
    
    # Generate predictions    
    try:
        result = prediction_generator.generate_predictions()
        
        # Print to terminal
        print_predictions_cli(result)
        
        # Print performance info
        if result.get('parallel_processing'):
            print(f"[Info] Parallel processing enabled: {result.get('workers_used')} workers")
        
        return True
    except Exception as e:
        print(f"\n[!] API Error: The fastf1 F1 API may be unavailable.")
        print(f"    Error details: {e}")
        print(f"\n    Running with demo data instead...\n")
        
        # Use demo data to show CLI output works
        demo_result = get_demo_predictions()
        print_predictions_cli(demo_result)
        return False


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    import argparse
    import multiprocessing as mp
    
    parser = argparse.ArgumentParser(description='F1 Race Predictor')
    parser.add_argument('--mode', choices=['cli', 'server'], default='server',
                        help='Run in CLI or server mode')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port for Flask server')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host for Flask server')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--no-parallel', action='store_true',
                        help='Disable parallel processing')
    
    args = parser.parse_args()
    
    # Configure multiprocessing
    if args.no_parallel:
        prediction_generator.use_multiprocessing = False
        print("[Info] Parallel processing disabled")
    else:
        print(f"[Info] Parallel processing enabled with {min(mp.cpu_count(), 4)} workers")
    
    if args.mode == 'cli':
        # Run CLI mode
        run_cli_mode()
    else:
        # Run Flask server
        print(f"\n[F1] Race Predictor - API Server")
        print(f"Starting server on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop\n")
        
        app.run(host=args.host, port=args.port, debug=args.debug)

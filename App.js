import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [weatherConditions, setWeatherConditions] = useState({
    rain: false,
    temperature: 25,
    safety_car_probability: 0.3
  });

  const fetchPredictions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5000/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          weather_conditions: weatherConditions
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch predictions');
      }
      
      const data = await response.json();
      setPredictions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, []);

  const getPositionColor = (position) => {
    if (position === 1) return '#FFD700';
    if (position === 2) return '#C0C0C0';
    if (position === 3) return '#CD7F32';
    if (position <= 10) return '#00ff88';
    return '#666';
  };

  const getProbabilityColor = (prob) => {
    if (prob > 0.7) return '#00ff88';
    if (prob > 0.4) return '#ffd700';
    if (prob > 0.2) return '#ff6b35';
    return '#ff3366';
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="speed-lines"></div>
            <h1 className="title">
              <span className="title-f1">F1</span>
              <span className="title-race">RACE</span>
              <span className="title-predictor">PREDICTOR</span>
            </h1>
            <div className="subtitle">AI-Powered Race Analysis System</div>
          </div>
          
          <div className="live-indicator">
            <div className="live-dot"></div>
            <span>LIVE PREDICTIONS</span>
          </div>
        </div>
      </header>

      {/* Race Info Banner */}
      {predictions && predictions.race_info && (
        <div className="race-info-banner">
          <div className="race-info-content">
            <div className="race-info-item">
              <span className="race-info-label">CIRCUIT</span>
              <span className="race-info-value">{predictions.race_info.circuit}</span>
            </div>
            <div className="race-info-divider"></div>
            <div className="race-info-item">
              <span className="race-info-label">COUNTRY</span>
              <span className="race-info-value">{predictions.race_info.country}</span>
            </div>
            <div className="race-info-divider"></div>
            <div className="race-info-item">
              <span className="race-info-label">ROUND</span>
              <span className="race-info-value">{predictions.race_info.round}</span>
            </div>
            <div className="race-info-divider"></div>
            <div className="race-info-item">
              <span className="race-info-label">SEASON</span>
              <span className="race-info-value">{predictions.race_info.season}</span>
            </div>
          </div>
        </div>
      )}

      {/* Weather Controls */}
      <div className="controls-section">
        <div className="controls-container">
          <h3 className="controls-title">RACE CONDITIONS</h3>
          
          <div className="controls-grid">
            <div className="control-item">
              <label className="control-label">
                <input
                  type="checkbox"
                  checked={weatherConditions.rain}
                  onChange={(e) => setWeatherConditions({
                    ...weatherConditions,
                    rain: e.target.checked
                  })}
                />
                <span className="checkbox-custom"></span>
                Rain Expected
              </label>
            </div>
            
            <div className="control-item">
              <label className="control-label">Temperature: {weatherConditions.temperature}°C</label>
              <input
                type="range"
                min="0"
                max="45"
                value={weatherConditions.temperature}
                onChange={(e) => setWeatherConditions({
                  ...weatherConditions,
                  temperature: parseInt(e.target.value)
                })}
                className="slider"
              />
            </div>
            
            <div className="control-item">
              <label className="control-label">
                Safety Car Probability: {(weatherConditions.safety_car_probability * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weatherConditions.safety_car_probability}
                onChange={(e) => setWeatherConditions({
                  ...weatherConditions,
                  safety_car_probability: parseFloat(e.target.value)
                })}
                className="slider"
              />
            </div>
          </div>
          
          <button onClick={fetchPredictions} className="predict-button" disabled={loading}>
            {loading ? 'CALCULATING...' : 'GENERATE PREDICTIONS'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p className="loading-text">Analyzing race data...</p>
          </div>
        )}

        {error && (
          <div className="error-container">
            <p className="error-text">⚠️ {error}</p>
            <button onClick={fetchPredictions} className="retry-button">Retry</button>
          </div>
        )}

        {predictions && predictions.predictions && (
          <div className="predictions-container">
            <div className="predictions-header">
              <h2 className="predictions-title">PREDICTED RACE RESULTS</h2>
              <div className="predictions-meta">
                Generated: {new Date(predictions.generated_at).toLocaleString()}
              </div>
            </div>

            {/* Podium Spotlight */}
            <div className="podium-section">
              {predictions.predictions.slice(0, 3).map((driver, idx) => (
                <div key={driver.driver_id} className={`podium-card podium-${idx + 1}`}>
                  <div className="podium-position">{idx + 1}</div>
                  <div className="podium-driver-name">{driver.name}</div>
                  <div className="podium-team">{driver.team}</div>
                  <div className="podium-stats">
                    <div className="podium-stat">
                      <span className="stat-label">WIN</span>
                      <span className="stat-value">{(driver.win_probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="podium-stat">
                      <span className="stat-label">PODIUM</span>
                      <span className="stat-value">{(driver.podium_probability * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Full Grid */}
            <div className="grid-section">
              <table className="predictions-table">
                <thead>
                  <tr>
                    <th>POS</th>
                    <th>DRIVER</th>
                    <th>TEAM</th>
                    <th>SCORE</th>
                    <th>WIN %</th>
                    <th>PODIUM %</th>
                    <th>METRICS</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.predictions.map((driver) => (
                    <tr key={driver.driver_id} className="driver-row">
                      <td>
                        <div 
                          className="position-badge"
                          style={{ borderColor: getPositionColor(driver.predicted_position) }}
                        >
                          {driver.predicted_position}
                        </div>
                      </td>
                      <td className="driver-name">{driver.name}</td>
                      <td className="team-name">{driver.team}</td>
                      <td>
                        <div className="score-bar-container">
                          <div 
                            className="score-bar"
                            style={{ width: `${(driver.final_score * 100)}%` }}
                          ></div>
                          <span className="score-text">{driver.final_score.toFixed(3)}</span>
                        </div>
                      </td>
                      <td>
                        <span 
                          className="probability-badge"
                          style={{ 
                            backgroundColor: getProbabilityColor(driver.win_probability),
                            color: '#000'
                          }}
                        >
                          {(driver.win_probability * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td>
                        <span 
                          className="probability-badge"
                          style={{ 
                            backgroundColor: getProbabilityColor(driver.podium_probability),
                            color: '#000'
                          }}
                        >
                          {(driver.podium_probability * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td>
                        <div className="metrics-cell">
                          <span title="Average Finish">
                            Finish: {driver.metrics.avg_finish}
                          </span>
                          <span title="Qualifying Average">
                            Qual: {driver.metrics.qualifying_avg}
                          </span>
                          <span title="Recent Form">
                            Form: {(driver.metrics.recent_form * 100).toFixed(0)}%
                          </span>
                          <span title="Track Affinity">
                            Track: {(driver.metrics.track_affinity * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Footer Info */}
            <div className="footer-info">
              <div className="footer-section">
                <h4>Mathematical Model</h4>
                <p>Driver Score = (0.4 × Race Finish) + (0.3 × Qualifying) + (0.2 × Form) - (0.1 × DNF Risk) + Track Affinity</p>
              </div>
              <div className="footer-section">
                <h4>Machine Learning</h4>
                <p>Logistic Regression (Win) • Random Forest (Podium) • Gradient Boosting (Stability)</p>
              </div>
              <div className="footer-section">
                <h4>Data Source</h4>
                <p>Live F1 API (Ergast) • No Hardcoded Data • Real-time Analysis</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

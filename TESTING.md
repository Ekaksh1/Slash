# 🧪 Testing Guide - F1 Race Predictor

Complete testing documentation for ensuring system reliability.

## 📋 Testing Strategy

### Testing Pyramid
```
        /\
       /  \
      / UI \         10% - End-to-End Tests
     /------\
    /        \       30% - Integration Tests
   / API/Int \
  /------------\
 /              \    60% - Unit Tests
/   Unit Tests  \
------------------
```

## 🔬 Unit Tests

### Backend Unit Tests

Create `backend/tests/test_scoring.py`:

```python
import unittest
from app import ScoringEngine

class TestScoringEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = ScoringEngine()
    
    def test_driver_score_calculation(self):
        """Test driver score formula"""
        score = self.engine.calculate_driver_score(
            avg_finish=2.0,
            qualifying_avg=1.5,
            recent_form=0.9,
            dnf_risk=0.05,
            track_affinity=0.8,
            weather_conditions={'rain': False}
        )
        
        # Score should be between 0 and 1
        self.assertGreater(score, 0)
        self.assertLess(score, 1)
        
        # Higher values for good metrics
        self.assertGreater(score, 0.7)
    
    def test_team_score_calculation(self):
        """Test team score formula"""
        score = self.engine.calculate_team_score(
            constructor_form=0.9,
            pit_efficiency=0.85,
            reliability=0.9
        )
        
        # Weighted average should match formula
        expected = (0.5 * 0.9) + (0.3 * 0.85) + (0.2 * 0.9)
        self.assertAlmostEqual(score, expected, places=2)
    
    def test_final_score_calculation(self):
        """Test final score = driver × team"""
        driver_score = 0.8
        team_score = 0.9
        final = self.engine.calculate_final_score(driver_score, team_score)
        
        self.assertAlmostEqual(final, 0.72, places=2)
    
    def test_rain_modifier(self):
        """Test rain conditions increase skilled driver scores"""
        dry_score = self.engine.calculate_driver_score(
            avg_finish=2.0,
            qualifying_avg=1.5,
            recent_form=0.9,
            dnf_risk=0.05,
            track_affinity=0.8,
            weather_conditions={'rain': False}
        )
        
        wet_score = self.engine.calculate_driver_score(
            avg_finish=2.0,
            qualifying_avg=1.5,
            recent_form=0.9,
            dnf_risk=0.05,
            track_affinity=0.8,
            weather_conditions={'rain': True}
        )
        
        # Wet score should be higher for skilled driver
        self.assertGreater(wet_score, dry_score)
    
    def test_dnf_risk_penalty(self):
        """Test DNF risk decreases score"""
        low_risk_score = self.engine.calculate_driver_score(
            avg_finish=5.0,
            qualifying_avg=5.0,
            recent_form=0.7,
            dnf_risk=0.05,
            track_affinity=0.5,
            weather_conditions={'rain': False}
        )
        
        high_risk_score = self.engine.calculate_driver_score(
            avg_finish=5.0,
            qualifying_avg=5.0,
            recent_form=0.7,
            dnf_risk=0.3,
            track_affinity=0.5,
            weather_conditions={'rain': False}
        )
        
        # Higher DNF risk should lower score
        self.assertGreater(low_risk_score, high_risk_score)

if __name__ == '__main__':
    unittest.main()
```

Create `backend/tests/test_ml.py`:

```python
import unittest
import numpy as np
from app import MLPredictor

class TestMLPredictor(unittest.TestCase):
    
    def setUp(self):
        self.predictor = MLPredictor()
    
    def test_win_probability_range(self):
        """Test win probability is between 0 and 1"""
        all_scores = [0.9, 0.8, 0.7, 0.6, 0.5]
        
        for score in all_scores:
            prob = self.predictor.predict_win_probability(score, all_scores)
            self.assertGreaterEqual(prob, 0.0)
            self.assertLessEqual(prob, 1.0)
    
    def test_win_probability_ordering(self):
        """Test highest score gets highest probability"""
        all_scores = [0.9, 0.8, 0.7, 0.6, 0.5]
        
        probs = [
            self.predictor.predict_win_probability(score, all_scores)
            for score in all_scores
        ]
        
        # Probabilities should be in descending order
        for i in range(len(probs) - 1):
            self.assertGreater(probs[i], probs[i + 1])
    
    def test_podium_probability_position_effect(self):
        """Test position affects podium probability"""
        all_scores = [0.9, 0.8, 0.7, 0.6, 0.5]
        score = 0.7
        
        prob_p1 = self.predictor.predict_podium_probability(score, 0, all_scores)
        prob_p10 = self.predictor.predict_podium_probability(score, 9, all_scores)
        
        # P1 should have higher podium probability than P10
        self.assertGreater(prob_p1, prob_p10)

if __name__ == '__main__':
    unittest.main()
```

### Running Backend Tests

```bash
cd backend

# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=app tests/

# Run specific test file
python -m unittest tests.test_scoring
```

## 🔗 Integration Tests

### API Integration Tests

Create `backend/tests/test_api.py`:

```python
import unittest
import json
from app import app

class TestAPI(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/api/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'F1 Race Predictor')
    
    def test_predict_endpoint_get(self):
        """Test predict endpoint GET request"""
        response = self.app.get('/api/predict')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('predictions', data)
        self.assertIn('race_info', data)
        self.assertIn('conditions', data)
    
    def test_predict_endpoint_post(self):
        """Test predict endpoint with custom conditions"""
        payload = {
            'weather_conditions': {
                'rain': True,
                'temperature': 15,
                'safety_car_probability': 0.6
            }
        }
        
        response = self.app.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['conditions']['rain'], True)
        self.assertEqual(data['conditions']['temperature'], 15)
    
    def test_predictions_structure(self):
        """Test prediction response structure"""
        response = self.app.get('/api/predict')
        data = json.loads(response.data)
        
        # Check predictions array
        self.assertIsInstance(data['predictions'], list)
        self.assertGreater(len(data['predictions']), 0)
        
        # Check first prediction structure
        prediction = data['predictions'][0]
        required_fields = [
            'driver_id', 'name', 'team', 'predicted_position',
            'base_score', 'final_score', 'win_probability',
            'podium_probability', 'metrics'
        ]
        
        for field in required_fields:
            self.assertIn(field, prediction)
    
    def test_drivers_endpoint(self):
        """Test drivers endpoint"""
        response = self.app.get('/api/drivers')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('drivers', data)
    
    def test_standings_endpoint(self):
        """Test standings endpoints"""
        # Driver standings
        response = self.app.get('/api/standings/drivers')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('standings', data)
        
        # Constructor standings
        response = self.app.get('/api/standings/constructors')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('standings', data)
    
    def test_next_race_endpoint(self):
        """Test next race endpoint"""
        response = self.app.get('/api/next-race')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('race', data)
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.app.get('/api/health')
        
        self.assertIn('Access-Control-Allow-Origin', response.headers)

if __name__ == '__main__':
    unittest.main()
```

### External API Tests

Create `backend/tests/test_f1_api.py`:

```python
import unittest
from app import F1APIClient

class TestF1APIClient(unittest.TestCase):
    
    def setUp(self):
        self.client = F1APIClient()
    
    def test_fetch_drivers(self):
        """Test fetching current drivers"""
        drivers = self.client.fetch_drivers()
        
        self.assertIsInstance(drivers, list)
        self.assertGreater(len(drivers), 0)
        
        # Check driver structure
        if drivers:
            driver = drivers[0]
            self.assertIn('driverId', driver)
            self.assertIn('givenName', driver)
            self.assertIn('familyName', driver)
    
    def test_fetch_constructors(self):
        """Test fetching current constructors"""
        constructors = self.client.fetch_constructors()
        
        self.assertIsInstance(constructors, list)
        self.assertGreater(len(constructors), 0)
    
    def test_fetch_driver_standings(self):
        """Test fetching driver standings"""
        standings = self.client.fetch_driver_standings()
        
        self.assertIsInstance(standings, list)
        
        if standings:
            standing = standings[0]
            self.assertIn('Driver', standing)
            self.assertIn('Constructors', standing)
            self.assertIn('points', standing)
    
    def test_api_error_handling(self):
        """Test API handles errors gracefully"""
        # Test with invalid season
        drivers = self.client.fetch_drivers(season=1900)
        
        # Should return empty list or handle gracefully
        self.assertIsInstance(drivers, list)

if __name__ == '__main__':
    unittest.main()
```

## 🎭 Frontend Tests

### Component Tests

Create `frontend/src/App.test.js`:

```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

// Mock fetch
global.fetch = jest.fn();

beforeEach(() => {
  fetch.mockClear();
});

test('renders app title', () => {
  render(<App />);
  const titleElement = screen.getByText(/F1/i);
  expect(titleElement).toBeInTheDocument();
});

test('displays loading state', async () => {
  fetch.mockImplementationOnce(() => 
    new Promise(resolve => setTimeout(() => resolve({
      ok: true,
      json: async () => ({ predictions: [] })
    }), 100))
  );
  
  render(<App />);
  
  const loadingText = screen.getByText(/Analyzing race data/i);
  expect(loadingText).toBeInTheDocument();
});

test('fetches and displays predictions', async () => {
  const mockData = {
    predictions: [
      {
        driver_id: 'verstappen',
        name: 'Max Verstappen',
        team: 'Red Bull Racing',
        predicted_position: 1,
        final_score: 0.85,
        win_probability: 0.75,
        podium_probability: 0.95,
        metrics: {
          avg_finish: 2.1,
          qualifying_avg: 1.8,
          recent_form: 0.92,
          dnf_risk: 0.08,
          track_affinity: 0.85
        }
      }
    ],
    race_info: {
      circuit: 'Monza',
      country: 'Italy',
      round: 16,
      season: 2025
    },
    conditions: {
      rain: false,
      temperature: 25,
      safety_car_probability: 0.3
    }
  };
  
  fetch.mockImplementationOnce(() =>
    Promise.resolve({
      ok: true,
      json: async () => mockData
    })
  );
  
  render(<App />);
  
  await waitFor(() => {
    expect(screen.getByText('Max Verstappen')).toBeInTheDocument();
    expect(screen.getByText('Red Bull Racing')).toBeInTheDocument();
  });
});

test('toggles rain condition', async () => {
  fetch.mockImplementation(() =>
    Promise.resolve({
      ok: true,
      json: async () => ({ predictions: [], race_info: {}, conditions: {} })
    })
  );
  
  render(<App />);
  
  const rainCheckbox = screen.getByLabelText(/Rain Expected/i);
  
  expect(rainCheckbox).not.toBeChecked();
  
  fireEvent.click(rainCheckbox);
  
  expect(rainCheckbox).toBeChecked();
});

test('handles API errors', async () => {
  fetch.mockImplementationOnce(() =>
    Promise.reject(new Error('API Error'))
  );
  
  render(<App />);
  
  await waitFor(() => {
    expect(screen.getByText(/API Error/i)).toBeInTheDocument();
  });
});
```

### Running Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## 🔄 End-to-End Tests

### Playwright E2E Tests

Create `tests/e2e/test_full_flow.spec.js`:

```javascript
const { test, expect } = require('@playwright/test');

test.describe('F1 Race Predictor E2E', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });
  
  test('full prediction flow', async ({ page }) => {
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('F1');
    
    // Wait for initial predictions
    await page.waitForSelector('.predictions-table', { timeout: 10000 });
    
    // Check race info is displayed
    await expect(page.locator('.race-info-banner')).toBeVisible();
    
    // Toggle rain
    await page.click('input[type="checkbox"]');
    
    // Adjust temperature
    await page.locator('input[type="range"]').first().fill('30');
    
    // Click generate predictions
    await page.click('text=GENERATE PREDICTIONS');
    
    // Wait for new predictions
    await page.waitForSelector('.loading-spinner');
    await page.waitForSelector('.predictions-table', { timeout: 10000 });
    
    // Verify predictions are displayed
    const rows = await page.locator('.driver-row').count();
    expect(rows).toBeGreaterThan(0);
    
    // Check podium section
    await expect(page.locator('.podium-section')).toBeVisible();
    
    // Verify probability badges
    const probBadges = await page.locator('.probability-badge').count();
    expect(probBadges).toBeGreaterThan(0);
  });
  
  test('displays driver details', async ({ page }) => {
    await page.waitForSelector('.predictions-table', { timeout: 10000 });
    
    // Get first driver row
    const firstRow = page.locator('.driver-row').first();
    
    // Check all required fields
    await expect(firstRow.locator('.driver-name')).toBeVisible();
    await expect(firstRow.locator('.team-name')).toBeVisible();
    await expect(firstRow.locator('.position-badge')).toBeVisible();
    await expect(firstRow.locator('.probability-badge')).toHaveCount(2);
  });
  
  test('weather controls work', async ({ page }) => {
    // Temperature slider
    const tempSlider = page.locator('input[type="range"]').first();
    await tempSlider.fill('35');
    
    const tempLabel = page.locator('text=/Temperature: \\d+°C/');
    await expect(tempLabel).toContainText('35');
    
    // Safety car slider
    const scSlider = page.locator('input[type="range"]').nth(1);
    await scSlider.fill('0.8');
    
    const scLabel = page.locator('text=/Safety Car Probability: \\d+%/');
    await expect(scLabel).toContainText('80');
  });
});
```

### Running E2E Tests

```bash
# Install Playwright
npm install -D @playwright/test

# Run tests
npx playwright test

# Run with UI
npx playwright test --ui

# Generate report
npx playwright show-report
```

## 📊 Performance Tests

### Load Testing with Locust

Create `backend/tests/locustfile.py`:

```python
from locust import HttpUser, task, between

class F1PredictorUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(10)
    def get_predictions(self):
        self.client.get("/api/predict")
    
    @task(3)
    def get_health(self):
        self.client.get("/api/health")
    
    @task(2)
    def post_predictions(self):
        self.client.post("/api/predict", json={
            "weather_conditions": {
                "rain": True,
                "temperature": 20,
                "safety_car_probability": 0.5
            }
        })
    
    @task(1)
    def get_standings(self):
        self.client.get("/api/standings/drivers")
```

Run load tests:
```bash
locust -f backend/tests/locustfile.py --host=http://localhost:5000
```

## ✅ Test Coverage Goals

### Backend
- Unit Tests: > 80%
- Integration Tests: > 70%
- API Tests: 100% of endpoints

### Frontend
- Component Tests: > 70%
- Integration Tests: > 60%
- E2E Tests: Critical paths

## 🔍 Continuous Testing

### Pre-commit Hooks

Create `.githooks/pre-commit`:
```bash
#!/bin/sh

# Run backend tests
cd backend
python -m pytest tests/ || exit 1

# Run frontend tests
cd ../frontend
npm test -- --watchAll=false || exit 1

echo "All tests passed!"
```

Make executable:
```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

## 📝 Testing Checklist

Before deployment:

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] API endpoints tested
- [ ] Frontend components tested
- [ ] E2E critical paths tested
- [ ] Load testing completed
- [ ] Error handling tested
- [ ] Security testing done
- [ ] Cross-browser testing done
- [ ] Mobile responsiveness tested

## 🎯 Test Maintenance

### Regular Tasks
- Update tests when adding features
- Remove obsolete tests
- Monitor test execution time
- Review coverage reports
- Update mocks for API changes

---

**Remember**: Good tests = reliable software = happy users! 🚀

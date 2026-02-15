# F1 Race Predictor - Complete API Documentation

**Version:** 1.0.0  
**Last Updated:** 2026-02-14  
**Base URL:** `http://localhost:5000`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL & Environment](#base-url--environment)
4. [API Endpoints](#api-endpoints)
5. [Request Parameters](#request-parameters)
6. [Response Schemas](#response-schemas)
7. [Data Types](#data-types)
8. [Pagination](#pagination)
9. [Filtering](#filtering)
10. [Rate Limiting](#rate-limiting)
11. [Error Codes](#error-codes)
12. [Webhooks](#webhooks)
13. [SDKs & Libraries](#sdks--libraries)
14. [Best Practices](#best-practices)
15. [Examples](#examples)

---

## Overview

The F1 Race Predictor API provides comprehensive access to Formula 1 race predictions, driver/constructor data, standings, and historical race results. The API is organized around REST principles, accepting JSON request bodies and returning JSON responses.

### Core Features

- **Race Predictions**: Generate AI-powered race predictions with win/podium probabilities
- **Real-time Data**: Fetch current season drivers, constructors, and standings
- **Historical Analysis**: Access past race results and driver performance metrics
- **Weather Conditions**: Adjust predictions based on weather scenarios
- **Machine Learning**: Enhanced predictions using Logistic Regression, Random Forest, and Gradient Boosting

### Data Source

The underlying data is fetched from the **fastf1 library** (a modern replacement for the Ergast API), providing:
- Real-time F1 session data
- Historical race results (1950-present)
- Driver and constructor information
- Qualifying and race lap times

---

## Authentication

### Current Status

**Authentication Type:** None (Open API)  
**API Key Required:** No

> ⚠️ **Note**: For production deployments, implement API key authentication using Flask-API-Key or similar middleware.

### Recommended Authentication Headers

```http
Authorization: Bearer YOUR_API_KEY
X-API-Key: YOUR_API_KEY
```

### Implementation Example

```python
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

---

## Base URL & Environment

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:5000` |
| Production | `https://api.f1predictor.com` (not implemented) |

### CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) for frontend applications:

```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

---

## API Endpoints

### 1. Health Check

#### `GET /api/health`

Check API service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "F1 Race Predictor",
  "version": "1.0.0",
  "timestamp": "2026-02-14T12:00:00Z"
}
```

---

### 2. Generate Race Predictions

#### `POST /api/predict`

Generate comprehensive race predictions with win and podium probabilities.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `circuit_id` | string | No | Specific circuit ID (e.g., "monza", "silverstone"). If omitted, uses next race. |
| `weather_conditions` | object | No | Weather parameters for prediction modeling |
| `include_metrics` | boolean | No | Include detailed driver metrics (default: true) |
| `prediction_count` | integer | No | Number of predictions to return (default: 20, max: 50) |

**Weather Conditions Object:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `rain` | boolean | No | false | Whether rain is expected |
| `temperature` | number | No | 25.0 | Temperature in Celsius (0-50) |
| `safety_car_probability` | number | No | 0.3 | Safety car probability (0.0-1.0) |

**Example Request:**

```json
{
  "circuit_id": "monza",
  "weather_conditions": {
    "rain": false,
    "temperature": 28,
    "safety_car_probability": 0.3
  },
  "include_metrics": true,
  "prediction_count": 20
}
```

**Response:**

```json
{
  "predictions": [
    {
      "driver_id": "max_verstappen",
      "name": "Max Verstappen",
      "team": "Red Bull Racing",
      "predicted_position": 1,
      "base_score": 0.856,
      "team_score": 0.865,
      "final_score": 0.742,
      "win_probability": 0.8234,
      "podium_probability": 0.9512,
      "metrics": {
        "avg_finish": 2.1,
        "qualifying_avg": 1.8,
        "recent_form": 0.92,
        "dnf_risk": 0.08,
        "track_affinity": 0.85
      }
    }
  ],
  "race_info": {
    "circuit": "Monza Circuit",
    "country": "Italy",
    "round": 16,
    "season": 2025,
    "date": "2025-09-01",
    "circuit_id": "monza"
  },
  "conditions": {
    "rain": false,
    "temperature": 28,
    "safety_car_probability": 0.3
  },
  "generated_at": "2026-02-14T12:00:00Z",
  "model_version": "v20260214_130313"
}
```

---

### 3. Get All Drivers

#### `GET /api/drivers`

Fetch all drivers for the current or specified season.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `season` | integer | No | Current year | F1 season year (1950-present) |
| `include_stats` | boolean | No | false | Include driver statistics |

**Example Request:**

```http
GET /api/drivers?season=2025&include_stats=true
```

**Response:**

```json
{
  "drivers": [
    {
      "driverId": "max_verstappen",
      "givenName": "Max",
      "familyName": "Verstappen",
      "nationality": "Red Bull Racing",
      "permanentNumber": "33",
      "code": "VER"
    }
  ],
  "season": 2025,
  "count": 20,
  "total_drivers": 20
}
```

---

### 4. Get All Constructors

#### `GET /api/constructors`

Fetch all constructors (teams) for the current or specified season.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `season` | integer | No | Current year | F1 season year |

**Example Request:**

```http
GET /api/constructors?season=2025
```

**Response:**

```json
{
  "constructors": [
    {
      "constructorId": "red_bull_racing",
      "name": "Red Bull Racing",
      "nationality": "Austrian",
      "team_id": "red_bull"
    }
  ],
  "season": 2025,
  "count": 10
}
```

---

### 5. Get Driver Standings

#### `GET /api/standings/drivers`

Fetch current driver championship standings.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `season` | integer | No | Current year | F1 season year |
| `round` | integer | No | Latest | Round number |

**Example Request:**

```http
GET /api/standings/drivers?season=2025&round=5
```

**Response:**

```json
{
  "StandingsTable": {
    "StandingsLists": [
      {
        "season": "2025",
        "round": "5",
        "DriverStandings": [
          {
            "position": "1",
            "points": "150",
            "Driver": {
              "driverId": "max_verstappen",
              "givenName": "Max",
              "familyName": "Verstappen"
            },
            "Constructors": [
              {
                "constructorId": "red_bull_racing",
                "name": "Red Bull Racing"
              }
            ],
            "wins": "5",
            "behind": "0"
          }
        ]
      }
    ]
  }
}
```

---

### 6. Get Constructor Standings

#### `GET /api/standings/constructors`

Fetch current constructor championship standings.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `season` | integer | No | Current year | F1 season year |
| `round` | integer | No | Latest | Round number |

**Example Request:**

```http
GET /api/standings/constructors?season=2025
```

**Response:**

```json
{
  "StandingsTable": {
    "StandingsLists": [
      {
        "season": "2025",
        "round": "5",
        "ConstructorStandings": [
          {
            "position": "1",
            "points": "280",
            "Constructor": {
              "constructorId": "red_bull_racing",
              "name": "Red Bull Racing"
            },
            "wins": "5"
          }
        ]
      }
    ]
  }
}
```

---

### 7. Get Next Race

#### `GET /api/next-race`

Fetch information about the next upcoming F1 race.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `season` | integer | No | Current year | F1 season year |

**Example Request:**

```http
GET /api/next-race
```

**Response:**

```json
{
  "season": "2025",
  "round": "16",
  "raceName": "Pirelli Italian Grand Prix",
  "date": "2025-09-01",
  "time": "12:00:00Z",
  "Circuit": {
    "circuitId": "monza",
    "circuitName": "Autodromo Nazionale Monza",
    "Location": {
      "lat": "45.6156",
      "long": "7.6765",
      "locality": "Monza",
      "country": "Italy"
    }
  }
}
```

---

### 8. Get Race Results

#### `GET /api/results/{season}/{round}`

Fetch results for a specific race.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `season` | integer | F1 season year |
| `round` | integer | Round number |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_laps` | boolean | No | Include lap-by-lap data |
| `limit` | integer | No | Limit number of results (default: all) |

**Example Request:**

```http
GET /api/results/2025/15
```

**Response:**

```json
{
  "Results": [
    {
      "position": "1",
      "Driver": {
        "driverId": "max_verstappen",
        "givenName": "Max",
        "familyName": "Verstappen"
      },
      "Constructor": {
        "name": "Red Bull Racing"
      },
      "points": "26",
      "status": "Finished",
      "laps": "53",
      "grid": "1",
      "fastest_lap": "1:21.123"
    }
  ],
  "season": 2025,
  "round": 15,
  "raceName": "Azerbaijan Grand Prix",
  "date": "2025-09-15"
}
```

---

### 9. Get Qualifying Results

#### `GET /api/qualifying/{season}/{round}`

Fetch qualifying results for a specific race.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `season` | integer | F1 season year |
| `round` | integer | Round number |

**Example Request:**

```http
GET /api/qualifying/2025/15
```

**Response:**

```json
{
  "QualifyingResults": [
    {
      "position": "1",
      "Driver": {
        "driverId": "lando_norris",
        "givenName": "Lando",
        "familyName": "Norris"
      },
      "Constructor": {
        "name": "McLaren"
      },
      "Q1": "1:42.345",
      "Q2": "1:41.234",
      "Q3": "1:40.123"
    }
  ],
  "season": 2025,
  "round": 15
}
```

---

### 10. Get Historical Results

#### `GET /api/history/driver/{driver_id}`

Fetch historical race results for a specific driver.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `driver_id` | string | Driver identifier (e.g., "verstappen") |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `circuit_id` | string | No | All circuits | Filter by specific circuit |
| `seasons` | integer | No | 5 | Number of seasons to fetch |
| `session_type` | string | No | "R" | Session type: "R" (Race), "Q" (Qualifying), "FP1", "FP2", "FP3" |

**Example Request:**

```http
GET /api/history/driver/verstappen?circuit_id=monza&seasons=10
```

**Response:**

```json
{
  "driver_id": "verstappen",
  "driver_name": "Max Verstappen",
  "circuit_id": "monza",
  "results": [
    {
      "season": 2024,
      "round": 16,
      "position": 1,
      "points": 26,
      "grid": 1,
      "laps": 53,
      "fastest_lap": "1:21.123",
      "status": "Finished"
    }
  ],
  "statistics": {
    "total_races": 10,
    "wins": 6,
    "podiums": 9,
    "average_finish": 2.3,
    "pole_positions": 5
  }
}
```

---

### 11. Get Circuit Information

#### `GET /api/circuits`

Fetch information about F1 circuits.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `country` | string | No | Filter by country |
| `season` | integer | No | Filter by season active |

**Example Request:**

```http
GET /api/circuits?country=Italy
```

**Response:**

```json
{
  "Circuits": [
    {
      "circuitId": "monza",
      "circuitName": "Autodromo Nazionale Monza",
      "Location": {
        "lat": "45.6156",
        "long": "7.6765",
        "locality": "Monza",
        "country": "Italy"
      },
      "url": "http://en.wikipedia.org/wiki/Autodromo_Nazionale_Monza"
    }
  ],
  "total": 1
}
```

---

### 12. Get Season Schedule

#### `GET /api/schedule/{season}`

Fetch the complete F1 season schedule.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `season` | integer | F1 season year |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `upcoming` | boolean | No | Only return upcoming races |

**Example Request:**

```http
GET /api/schedule/2025?upcoming=true
```

**Response:**

```json
{
  "season": 2025,
  "Races": [
    {
      "season": "2025",
      "round": "1",
      "raceName": "Australian Grand Prix",
      "date": "2025-03-16",
      "time": "02:00:00Z",
      "Circuit": {
        "circuitId": "albert_park",
        "circuitName": "Albert Park Circuit",
        "Location": {
          "locality": "Melbourne",
          "country": "Australia"
        }
      }
    }
  ],
  "total_races": 24
}
```

---

## Request Parameters

### Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `season` | integer | F1 season year (1950-present) |
| `round` | integer | Race round number (1-24) |
| `circuit_id` | string | Unique circuit identifier |
| `driver_id` | string | Unique driver identifier |
| `constructor_id` | string | Unique constructor/team identifier |
| `limit` | integer | Maximum number of results (1-1000) |
| `offset` | integer | Pagination offset |
| `sort` | string | Sort field (e.g., "position", "points") |
| `order` | string | Sort order: "asc" or "desc" |

### Advanced Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_laps` | boolean | Include lap-by-lap data |
| `include_fastest` | boolean | Include fastest lap times |
| `include_pit` | boolean | Include pit stop data |
| `include_weather` | boolean | Include weather data |
| `time_format` | string | Time format: "iso", "seconds", "hms" |

---

## Response Schemas

### Prediction Response Schema

```json
{
  "type": "object",
  "properties": {
    "predictions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "driver_id": { "type": "string" },
          "name": { "type": "string" },
          "team": { "type": "string" },
          "predicted_position": { "type": "integer" },
          "base_score": { "type": "number" },
          "team_score": { "type": "number" },
          "final_score": { "type": "number" },
          "win_probability": { "type": "number" },
          "podium_probability": { "type": "number" },
          "metrics": {
            "type": "object",
            "properties": {
              "avg_finish": { "type": "number" },
              "qualifying_avg": { "type": "number" },
              "recent_form": { "type": "number" },
              "dnf_risk": { "type": "number" },
              "track_affinity": { "type": "number" }
            }
          }
        }
      }
    },
    "race_info": {
      "type": "object",
      "properties": {
        "circuit": { "type": "string" },
        "country": { "type": "string" },
        "round": { "type": "integer" },
        "season": { "type": "integer" },
        "date": { "type": "string", "format": "date" }
      }
    },
    "conditions": {
      "type": "object",
      "properties": {
        "rain": { "type": "boolean" },
        "temperature": { "type": "number" },
        "safety_car_probability": { "type": "number" }
      }
    },
    "generated_at": { "type": "string", "format": "date-time" }
  }
}
```

### Standings Response Schema

```json
{
  "type": "object",
  "properties": {
    "StandingsTable": {
      "type": "object",
      "properties": {
        "StandingsLists": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "season": { "type": "string" },
              "round": { "type": "string" },
              "DriverStandings": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "position": { "type": "string" },
                    "points": { "type": "string" },
                    "Driver": { "type": "object" },
                    "Constructors": { "type": "array" },
                    "wins": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## Data Types

### Primitive Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | UTF-8 text | `"Max Verstappen"` |
| `integer` | Whole number | `2025`, `1`, `15` |
| `number` | Decimal number | `0.8234`, `26.5` |
| `boolean` | True/false | `true`, `false` |
| `null` | Empty value | `null` |

### Date/Time Formats

| Format | Description | Example |
|--------|-------------|---------|
| `date` | ISO 8601 date | `"2025-09-01"` |
| `date-time` | ISO 8601 datetime | `"2026-02-14T12:00:00Z"` |
| `time` | ISO 8601 time | `"12:00:00Z"` |

### Custom Types

| Type | Description | Fields |
|------|-------------|--------|
| `Driver` | Driver information | `driverId`, `givenName`, `familyName`, `nationality`, `permanentNumber` |
| `Constructor` | Team information | `constructorId`, `name`, `nationality` |
| `Circuit` | Circuit details | `circuitId`, `circuitName`, `Location` |
| `Location` | Geographic location | `lat`, `long`, `locality`, `country` |
| `WeatherConditions` | Weather parameters | `rain`, `temperature`, `safety_car_probability` |
| `DriverMetrics` | Performance metrics | `avg_finish`, `qualifying_avg`, `recent_form`, `dnf_risk`, `track_affinity` |

---

## Pagination

### Pagination Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 30 | Maximum results per page (1-100) |
| `offset` | integer | 0 | Number of results to skip |

### Pagination Headers

```
X-Total-Count: 150
X-Total-Pages: 5
X-Current-Page: 1
X-Next-Page: 2
X-Previous-Page: null
```

### Example Request with Pagination

```http
GET /api/drivers?limit=10&offset=20
```

---

## Filtering

### Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Exact match | `season=2025` |
| `>` | Greater than | `round>10` |
| `<` | Less than | `points<50` |
| `>=` | Greater or equal | `position>=5` |
| `<=` | Less or equal | `position<=10` |
| `!=` | Not equal | `team!=Ferrari` |
| `in` | In list | `driver_id in (verstappen,norris,leclerc)` |
| `like` | Pattern match | `name like %Verstappen%` |

### Filtering Examples

```http
# Filter by multiple drivers
GET /api/results/2025/15?driver_id=verstappen,norris

# Filter by position range
GET /api/standings/drivers?position>=1&position<=3

# Filter by date range
GET /api/results?date_start=2025-01-01&date_end=2025-06-30
```

---

## Rate Limiting

### Current Limits

| Tier | Requests/Hour | Requests/Day | Burst Limit |
|------|---------------|--------------|-------------|
| Free | 100 | 1,000 | 10/minute |
| Basic | 1,000 | 10,000 | 50/minute |
| Pro | 10,000 | 100,000 | 200/minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642089600
```

### Handling Rate Limits

When rate limited, the API returns:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

**HTTP Status Code:** `429 Too Many Requests`

---

## Error Codes

### HTTP Status Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no content to return |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Application Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `INVALID_SEASON` | Season must be between 1950 and current year | 400 |
| `INVALID_ROUND` | Round number is invalid | 400 |
| `INVALID_DRIVER` | Driver not found | 404 |
| `INVALID_CIRCUIT` | Circuit not found | 404 |
| `NO_UPCOMING_RACES` | No upcoming races found | 404 |
| `DATA_UNAVAILABLE` | Requested data unavailable | 503 |
| `PREDICTION_FAILED` | Prediction generation failed | 500 |

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_SEASON",
    "message": "Season must be between 1950 and 2026",
    "details": {
      "field": "season",
      "min_value": 1950,
      "max_value": 2026
    }
  },
  "request_id": "req_abc123"
}
```

---

## Webhooks

### Webhook Events

| Event | Description | Payload |
|-------|-------------|---------|
| `prediction.completed` | New prediction generated | Prediction object |
| `race.started` | Race has started | Race info |
| `race.completed` | Race has finished | Race results |
| `standings.updated` | Standings have been updated | Standings object |

### Webhook Payload Example

```json
{
  "event": "prediction.completed",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    "prediction_id": "pred_abc123",
    "race_info": {
      "circuit": "Monza Circuit",
      "round": 16
    },
    "top_predictions": [
      {
        "driver_id": "max_verstappen",
        "position": 1,
        "win_probability": 0.8234
      }
    ]
  }
}
```

---

## SDKs & Libraries

### Official SDKs

| Language | Library | Installation |
|----------|---------|--------------|
| Python | `f1predictor` | `pip install f1predictor` |
| JavaScript | `@f1predictor/sdk` | `npm install @f1predictor/sdk` |

### Community Libraries

| Language | Library | Description |
|----------|---------|-------------|
| Python | `fastf1` | F1 data fetching |
| R | `f1data` | F1 data analysis |
| Julia | `F1Data.jl` | F1 data for Julia |

---

## Best Practices

### 1. Efficient Data Fetching

```python
# ✅ Good: Batch requests
response = requests.post('/api/predict', json={
    'weather_conditions': {...},
    'include_metrics': True
})

# ❌ Bad: Multiple individual requests
for driver in drivers:
    requests.get(f'/api/drivers/{driver}')
```

### 2. Caching

```python
# Cache frequently accessed data
import functools

@functools.lru_cache(maxsize=128)
def get_standings(season, round):
    response = requests.get(f'/api/standings/drivers', params={
        'season': season,
        'round': round
    })
    return response.json()
```

### 3. Error Handling

```python
import time
from requests.exceptions import RetryError

def fetch_with_retry(url, max_retries=3, backoff_factor=2):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = backoff_factor ** attempt
                time.sleep(wait_time)
            else:
                raise
    raise RetryError("Max retries exceeded")
```

### 4. Async Requests

```python
import asyncio
import aiohttp

async def fetch_all_predictions(seasons):
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.get(f'http://localhost:5000/api/predict', 
                       json={'season': season})
            for season in seasons
        ]
        return await asyncio.gather(*tasks)
```

### 5. Request Optimization

```python
# Request only needed fields
response = requests.get('/api/drivers', params={
    'fields': 'driverId,givenName,familyName',  # Reduce payload
    'limit': 10
})
```

### 6. Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### 7. Monitoring & Logging

```python
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_request(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Requesting: {args[0]}")
        start = time.time()
        result = func(*args, **kwargs)
        logger.info(f"Completed in {time.time() - start:.2f}s")
        return result
    return wrapper
```

---

## Examples

### Example 1: Generate Basic Predictions

```python
import requests

# Basic prediction request
response = requests.post('http://localhost:5000/api/predict', json={
    'weather_conditions': {
        'rain': False,
        'temperature': 25,
        'safety_car_probability': 0.3
    }
})

predictions = response.json()
print(f"Winner: {predictions['predictions'][0]['name']}")
```

### Example 2: Fetch Historical Data

```python
# Fetch driver history at specific circuit
response = requests.get(
    'http://localhost:5000/api/history/driver/verstappen',
    params={
        'circuit_id': 'monza',
        'seasons': 10,
        'session_type': 'R'
    }
)

history = response.json()
print(f"Win rate at Monza: {history['statistics']['wins'] / history['statistics']['total_races']:.1%}")
```

### Example 3: Get Real-time Standings

```python
# Fetch current standings
response = requests.get(
    'http://localhost:5000/api/standings/drivers',
    params={'season': 2025}
)

standings = response.json()
for driver in standings['StandingsTable']['StandingsLists'][0]['DriverStandings'][:3]:
    print(f"{driver['position']}. {driver['Driver']['familyName']} - {driver['points']} pts")
```

### Example 4: Complete Race Weekend Data

```python
import requests

def get_race_weekend(season, round_num):
    # Fetch all race weekend data in parallel
    import concurrent.futures
    
    endpoints = [
        f'/api/qualifying/{season}/{round_num}',
        f'/api/results/{season}/{round_num}',
        f'/api/schedule/{season}'
    ]
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(requests.get, f'http://localhost:5000{ep}')
            for ep in endpoints
        ]
        
    results = [f.result().json() for f in concurrent.futures.as_completed(futures)]
    return results
```

### Example 5: CLI Prediction Tool

```python
#!/usr/bin/env python3
import requests
import json
import sys

def main():
    weather = {
        'rain': '--rain' in sys.argv,
        'temperature': int(sys.argv[sys.argv.index('--temp') + 1]) if '--temp' in sys.argv else 25,
        'safety_car_probability': 0.3
    }
    
    response = requests.post(
        'http://localhost:5000/api/predict',
        json={'weather_conditions': weather}
    )
    
    data = response.json()
    
    print("\n🏆 F1 Race Predictions 🏆")
    print("=" * 50)
    for p in data['predictions'][:10]:
        print(f"{p['predicted_position']}. {p['name']} ({p['team']})")
        print(f"   Win: {p['win_probability']*100:.1f}% | Podium: {p['podium_probability']*100:.1f}%")

if __name__ == '__main__':
    main()
```

---

## Support & Resources

- **Documentation**: [docs.f1predictor.com](https://docs.f1predictor.com)
- **API Status**: [status.f1predictor.com](https://status.f1predictor.com)
- **Community Forum**: [community.f1predictor.com](https://community.f1predictor.com)
- **GitHub Issues**: [github.com/f1predictor/issues](https://github.com/f1predictor/issues)

---

*Last Updated: February 14, 2026*

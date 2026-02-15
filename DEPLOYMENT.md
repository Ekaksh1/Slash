# 🚀 Deployment Guide - F1 Race Predictor

Complete guide for deploying your F1 Race Predictor to production.

## 📋 Pre-Deployment Checklist

- [ ] Backend tested locally
- [ ] Frontend tested locally
- [ ] API endpoints working
- [ ] Environment variables configured
- [ ] Dependencies documented
- [ ] Error handling implemented
- [ ] CORS configured properly

## 🌐 Deployment Options

### Option 1: Heroku (Recommended for Beginners)

#### Backend Deployment

1. **Install Heroku CLI**
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

2. **Create Heroku App**
```bash
cd backend
heroku login
heroku create f1-predictor-backend
```

3. **Create Procfile**
```bash
echo "web: python app.py" > Procfile
```

4. **Update app.py for production**
```python
# Replace the last line in app.py:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

5. **Deploy**
```bash
git init
git add .
git commit -m "Initial backend deployment"
heroku git:remote -a f1-predictor-backend
git push heroku main
```

6. **Open your backend**
```bash
heroku open
# Visit /api/health to verify
```

#### Frontend Deployment (Vercel)

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Update API URL**
```javascript
// In frontend/src/App.js, replace:
const response = await fetch('http://localhost:5000/api/predict', {

// With your Heroku backend URL:
const response = await fetch('https://f1-predictor-backend.herokuapp.com/api/predict', {
```

3. **Deploy to Vercel**
```bash
cd frontend
vercel login
vercel
```

4. **Follow prompts**
- Setup and deploy: Yes
- Which scope: Your account
- Link to existing project: No
- Project name: f1-race-predictor
- Directory: ./
- Override settings: No

### Option 2: AWS (Advanced)

#### Backend on EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t2.micro (free tier)
   - Security Group: Allow ports 22, 80, 5000

2. **SSH into instance**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. **Setup Python environment**
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx -y

# Clone your repo
git clone https://github.com/yourusername/f1-predictor.git
cd f1-predictor/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Setup Gunicorn**
```bash
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/f1predictor.service
```

Add:
```ini
[Unit]
Description=F1 Race Predictor Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/f1-predictor/backend
Environment="PATH=/home/ubuntu/f1-predictor/backend/venv/bin"
ExecStart=/home/ubuntu/f1-predictor/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

5. **Start service**
```bash
sudo systemctl start f1predictor
sudo systemctl enable f1predictor
```

6. **Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/f1predictor
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/f1predictor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Frontend on S3 + CloudFront

1. **Build React app**
```bash
cd frontend
npm run build
```

2. **Create S3 bucket**
```bash
aws s3 mb s3://f1-predictor-frontend
```

3. **Enable static website hosting**
```bash
aws s3 website s3://f1-predictor-frontend/ --index-document index.html
```

4. **Upload build files**
```bash
aws s3 sync build/ s3://f1-predictor-frontend/
```

5. **Setup CloudFront distribution**
   - Origin: Your S3 bucket
   - Default root object: index.html
   - Custom error response: 404 → /index.html (for React Router)

### Option 3: DigitalOcean App Platform

#### Full Stack Deployment

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/f1-predictor.git
git push -u origin main
```

2. **Create App on DigitalOcean**
   - Go to https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Connect to GitHub repository
   - Select your repository

3. **Configure Backend Component**
   - Type: Web Service
   - Source Directory: `/backend`
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `python app.py`
   - HTTP Port: 5000

4. **Configure Frontend Component**
   - Type: Static Site
   - Source Directory: `/frontend`
   - Build Command: `npm install && npm run build`
   - Output Directory: `build`

5. **Add Environment Variables**
   - `FLASK_ENV=production`
   - `CORS_ORIGINS=https://your-frontend-url.ondigitalocean.app`

6. **Deploy**
   - Click "Create Resources"
   - Wait for deployment
   - Visit your app URL

### Option 4: Docker (All Platforms)

#### Create Dockerfiles

**Backend Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
```

#### Deploy with Docker
```bash
docker-compose up -d
```

## 🔒 Security Best Practices

### 1. Environment Variables

Create `.env` file:
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://your-frontend-domain.com
API_RATE_LIMIT=100
```

Load in app.py:
```python
from dotenv import load_dotenv
import os

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
```

### 2. CORS Configuration

```python
# Update CORS in app.py for production
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ORIGINS', '*').split(','),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 3. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/predict')
@limiter.limit("10 per minute")
def predict_race():
    # ... existing code
```

### 4. Error Handling

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
```

### 5. HTTPS

Always use HTTPS in production:
- Heroku: Automatic
- AWS: Use ACM + Load Balancer
- DigitalOcean: Built-in
- Custom: Use Let's Encrypt + Certbot

## 📊 Monitoring & Logging

### Application Monitoring

**Add logging to app.py:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/api/predict')
def predict_race():
    logger.info('Prediction request received')
    # ... existing code
    logger.info(f'Prediction generated for {len(predictions)} drivers')
```

### Health Checks

Add comprehensive health check:
```python
@app.route('/api/health/detailed', methods=['GET'])
def detailed_health():
    try:
        # Test API connection
        drivers = F1APIClient.fetch_drivers()
        api_status = 'healthy' if drivers else 'degraded'
        
        return jsonify({
            'status': 'healthy',
            'api_connection': api_status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

### External Monitoring

**Recommended Tools:**
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **APM**: New Relic, Datadog
- **Error Tracking**: Sentry
- **Logs**: LogDNA, Papertrail

## 🚀 Performance Optimization

### Backend Caching

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@app.route('/api/predict')
@cache.cached(timeout=60, query_string=True)
def predict_race():
    # ... existing code
```

### Database for Historical Data

For production, consider caching historical data:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_driver_data(driver_id):
    cached = redis_client.get(f'driver:{driver_id}')
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    data = fetch_driver_data(driver_id)
    
    # Cache for 1 hour
    redis_client.setex(f'driver:{driver_id}', 3600, json.dumps(data))
    
    return data
```

### Frontend Optimization

1. **Code Splitting**
```javascript
import React, { lazy, Suspense } from 'react';

const PredictionsTable = lazy(() => import('./PredictionsTable'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PredictionsTable />
    </Suspense>
  );
}
```

2. **Build Optimization**
```bash
# Production build with optimizations
GENERATE_SOURCEMAP=false npm run build
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "f1-predictor-backend"
          heroku_email: "your-email@example.com"
          appdir: "backend"

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID}}
          vercel-project-id: ${{ secrets.PROJECT_ID}}
          working-directory: ./frontend
```

## 📝 Post-Deployment Checklist

- [ ] Health check endpoint responding
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Monitoring setup
- [ ] Error tracking configured
- [ ] Backups scheduled
- [ ] Documentation updated
- [ ] DNS configured
- [ ] SSL certificate valid

## 🐛 Troubleshooting Deployment

### Common Issues

**Issue**: CORS errors in production

**Solution**:
```python
# Update CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-frontend-domain.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})
```

**Issue**: API calls timing out

**Solution**:
```python
# Add timeout to API requests
response = requests.get(url, timeout=5)
```

**Issue**: High memory usage

**Solution**:
- Implement caching
- Reduce historical data range
- Use pagination for large datasets

## 📞 Support

For deployment issues:
1. Check logs: `heroku logs --tail`
2. Monitor resource usage
3. Test endpoints individually
4. Review error tracking service

---

🎉 **Congratulations on deploying your F1 Race Predictor!**

Remember to monitor performance and user feedback for continuous improvement.

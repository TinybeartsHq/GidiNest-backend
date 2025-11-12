# GidiNest Backend Deployment Guide

This guide will help you deploy your Django GidiNest backend to production.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Variables](#environment-variables)
3. [Database Setup](#database-setup)
4. [Deployment Options](#deployment-options)
   - [Railway (Recommended)](#option-1-railway-recommended)
   - [Heroku](#option-2-heroku)
   - [DigitalOcean App Platform](#option-3-digitalocean-app-platform)
   - [AWS EC2](#option-4-aws-ec2)
   - [Render](#option-5-render)
5. [Post-Deployment Steps](#post-deployment-steps)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Pre-Deployment Checklist

### 1. Update Django Settings for Production

Check your `gidinest_backend/settings.py`:

```python
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Update ALLOWED_HOSTS
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Database - Use production database URL
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}

# Static files configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Security settings
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True') == 'True'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### 2. Install Required Packages

Ensure these are in your `requirements.txt`:

```bash
pip freeze > requirements.txt
```

Key packages needed:
- `gunicorn` - Production WSGI server
- `dj-database-url` - Database URL parsing
- `psycopg2-binary` - PostgreSQL adapter
- `whitenoise` - Static file serving
- `python-decouple` - Environment variables

### 3. Create/Update Key Files

**Procfile** (for Heroku/Railway):
```
web: gunicorn gidinest_backend.wsgi --log-file -
worker: celery -A gidinest_backend worker -l info
```

**runtime.txt** (specify Python version):
```
python-3.11.0
```

**.gitignore** (ensure sensitive files are excluded):
```
.env
*.pyc
__pycache__/
db.sqlite3
staticfiles/
media/
*.log
```

---

## Environment Variables

Create these environment variables in your deployment platform:

### Required Variables

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Embedly Production
EMBEDLY_API_KEY_PRODUCTION=your_embedly_production_api_key
EMBEDLY_ORGANIZATION_ID_PRODUCTION=your_embedly_org_id
EMBEDLY_CUSTOMER_TYPE_ID_INDIVIDUAL=your_customer_type_id
EMBEDLY_COUNTRY_ID_NIGERIA=your_country_id

# Prembly
PREMBLY_API_KEY=your_prembly_api_key

# Email Configuration (for password reset, etc.)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# AWS S3 (if using for file storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=us-east-1

# Redis (for Celery)
REDIS_URL=redis://localhost:6379

# CORS Settings
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## Database Setup

### PostgreSQL (Recommended for Production)

Most platforms provide managed PostgreSQL. Once provisioned:

1. Get the `DATABASE_URL` from your platform
2. Add it to environment variables
3. Run migrations:

```bash
python manage.py migrate
```

4. Create superuser:

```bash
python manage.py createsuperuser
```

---

## Deployment Options

## Option 1: Railway (Recommended - Easy & Free Tier)

### Why Railway?
- Free tier with 500 hours/month
- Built-in PostgreSQL
- Easy deployment from GitHub
- Automatic HTTPS

### Steps:

1. **Sign up at [Railway.app](https://railway.app)**

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GidiNest-backend repository

3. **Add PostgreSQL Database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create `DATABASE_URL`

4. **Add Redis (for Celery)**
   - Click "New" → "Database" → "Add Redis"
   - Railway will automatically create `REDIS_URL`

5. **Configure Environment Variables**
   - Click on your service
   - Go to "Variables" tab
   - Add all variables from the [Environment Variables](#environment-variables) section

6. **Configure Build & Start Commands**
   - Railway auto-detects Django
   - Or manually set in `railway.toml`:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python manage.py migrate && gunicorn gidinest_backend.wsgi"
restartPolicyType = "always"
```

7. **Deploy**
   - Railway will automatically deploy on push to main branch
   - Get your public URL from Railway dashboard

---

## Option 2: Heroku

### Steps:

1. **Install Heroku CLI**
```bash
# Windows
choco install heroku-cli

# Mac
brew tap heroku/brew && brew install heroku
```

2. **Login to Heroku**
```bash
heroku login
```

3. **Create Heroku App**
```bash
heroku create gidinest-backend
```

4. **Add PostgreSQL**
```bash
heroku addons:create heroku-postgresql:mini
```

5. **Add Redis (for Celery)**
```bash
heroku addons:create heroku-redis:mini
```

6. **Set Environment Variables**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set EMBEDLY_API_KEY_PRODUCTION=your-key
# ... add all other variables
```

7. **Deploy**
```bash
git push heroku main
```

8. **Run Migrations**
```bash
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

9. **Open Your App**
```bash
heroku open
```

---

## Option 3: DigitalOcean App Platform

### Steps:

1. **Create Account** at [DigitalOcean](https://www.digitalocean.com)

2. **Create New App**
   - Go to "App Platform" → "Create App"
   - Connect your GitHub repository

3. **Configure App**
   - Detected framework: Python (Django)
   - Build command: `pip install -r requirements.txt`
   - Run command: `gunicorn gidinest_backend.wsgi`

4. **Add Database**
   - Add "Dev Database" (PostgreSQL)
   - Connection string auto-added as `DATABASE_URL`

5. **Add Environment Variables**
   - Go to "Settings" → "App-Level Environment Variables"
   - Add all required variables

6. **Deploy**
   - Click "Deploy"
   - App will be live at `your-app.ondigitalocean.app`

---

## Option 4: AWS EC2 (Advanced)

### Steps (High-Level):

1. **Launch EC2 Instance**
   - Ubuntu Server 22.04 LTS
   - t2.micro (free tier eligible)

2. **SSH into Instance**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

3. **Install Dependencies**
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql
```

4. **Clone Repository**
```bash
git clone https://github.com/yourusername/GidiNest-backend.git
cd GidiNest-backend
```

5. **Setup Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

6. **Configure PostgreSQL**
```bash
sudo -u postgres psql
CREATE DATABASE gidinest;
CREATE USER gidinest_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE gidinest TO gidinest_user;
\q
```

7. **Setup Environment Variables**
```bash
nano .env
# Add all environment variables
```

8. **Run Migrations**
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

9. **Configure Gunicorn**
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=Gunicorn daemon for GidiNest
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/GidiNest-backend
ExecStart=/home/ubuntu/GidiNest-backend/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/ubuntu/GidiNest-backend/gidinest.sock \
    gidinest_backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

10. **Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/gidinest
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/ubuntu/GidiNest-backend;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/GidiNest-backend/gidinest.sock;
    }
}
```

11. **Enable and Start Services**
```bash
sudo ln -s /etc/nginx/sites-available/gidinest /etc/nginx/sites-enabled
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl restart nginx
```

12. **Setup SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Option 5: Render

### Steps:

1. **Sign up at [Render.com](https://render.com)**

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure Service**
   - Name: gidinest-backend
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn gidinest_backend.wsgi:application`

4. **Add PostgreSQL Database**
   - Dashboard → "New +" → "PostgreSQL"
   - Copy the "Internal Database URL"

5. **Add Environment Variables**
   - Go to service → "Environment"
   - Add `DATABASE_URL` and all other variables

6. **Deploy**
   - Render auto-deploys on git push
   - Get your URL: `https://gidinest-backend.onrender.com`

---

## Post-Deployment Steps

### 1. Run Migrations
```bash
python manage.py migrate
```

### 2. Create Superuser
```bash
python manage.py createsuperuser
```

### 3. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 4. Test Your API
```bash
curl https://your-domain.com/api/v1/health/
```

### 5. Setup Celery Worker (if using background tasks)

**For Railway/Heroku:**
Add a worker process in your Procfile:
```
worker: celery -A gidinest_backend worker -l info
```

**For EC2:**
Create a systemd service for Celery.

### 6. Configure CORS for Frontend

Update in settings.py:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]
```

### 7. Update Frontend API Base URL

Point your frontend to: `https://your-backend-domain.com/api/v1/`

---

## Monitoring & Maintenance

### 1. Setup Error Monitoring

**Sentry (Recommended):**
```bash
pip install sentry-sdk
```

In `settings.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

### 2. Database Backups

- **Railway/Heroku**: Automatic daily backups
- **AWS RDS**: Configure automated snapshots
- **Manual**: Use `pg_dump` for PostgreSQL

### 3. Monitor Logs

```bash
# Railway
railway logs

# Heroku
heroku logs --tail

# EC2
sudo journalctl -u gunicorn -f
```

### 4. Health Check Endpoint

Create a health check endpoint:

```python
# urls.py
path('api/v1/health/', health_check, name='health_check'),

# views.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })
```

### 5. Regular Maintenance

- Update dependencies monthly
- Review logs for errors
- Monitor API performance
- Check database size and optimize queries

---

## Troubleshooting

### Common Issues:

**1. Static files not loading**
```bash
python manage.py collectstatic --noinput
```

**2. Database connection errors**
- Verify `DATABASE_URL` is correct
- Check database credentials
- Ensure database service is running

**3. 502 Bad Gateway**
- Check gunicorn is running
- Verify nginx configuration
- Check application logs

**4. Environment variables not loading**
- Ensure `.env` file is not in production (use platform variables)
- Verify variable names match exactly
- Restart the application after adding variables

---

## Security Best Practices

1. ✅ Never commit `.env` file
2. ✅ Use strong `SECRET_KEY`
3. ✅ Set `DEBUG=False` in production
4. ✅ Use HTTPS (SSL certificate)
5. ✅ Implement rate limiting
6. ✅ Regular security updates
7. ✅ Use environment variables for all secrets
8. ✅ Enable CORS only for trusted domains
9. ✅ Regular database backups
10. ✅ Monitor logs for suspicious activity

---

## Need Help?

- Django Documentation: https://docs.djangoproject.com/
- Railway Docs: https://docs.railway.app/
- Heroku Django Guide: https://devcenter.heroku.com/articles/django-app-configuration

---

**Your GidiNest backend is now ready for production! 🚀**

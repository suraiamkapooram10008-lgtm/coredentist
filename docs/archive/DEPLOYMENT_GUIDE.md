# CoreDent SaaS - Production Deployment Guide

This guide walks you through deploying CoreDent to production.

---

## Prerequisites

- PostgreSQL 15+ database
- Redis instance
- AWS S3 bucket (for file storage)
- Email service (SendGrid/AWS SES)
- Domain with SSL certificate
- Railway/Heroku/AWS account

---

## Step 1: Generate Secrets

```bash
# Generate SECRET_KEY (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate MONITORING_TOKEN
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

**⚠️ CRITICAL**: Store these securely (1Password, AWS Secrets Manager, etc.)

---

## Step 2: Set Up Database

### Option A: Railway PostgreSQL
```bash
# Railway automatically provisions PostgreSQL
# Get connection string from Railway dashboard
```

### Option B: AWS RDS
```bash
# Create PostgreSQL 15 instance
# Enable automated backups
# Configure security groups
# Get connection string
```

### Option C: Supabase
```bash
# Create project at supabase.com
# Get connection string from Settings > Database
```

---

## Step 3: Configure Environment Variables

### Backend (.env.production)

```bash
# Application
APP_NAME=CoreDent API
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@host:5432/coredent
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0

# Security (REQUIRED - Use generated secrets)
SECRET_KEY=<your-generated-secret-key>
ENCRYPTION_KEY=<your-generated-encryption-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://app.coredent.com,https://www.coredent.com

# Allowed Hosts
ALLOWED_HOSTS=api.coredent.com,coredent-api.railway.app

# Frontend URL
FRONTEND_URL=https://app.coredent.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Email (SendGrid example)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>
SMTP_FROM=noreply@coredent.com
SMTP_FROM_NAME=CoreDent PMS

# AWS S3
AWS_ACCESS_KEY_ID=<aws-access-key>
AWS_SECRET_ACCESS_KEY=<aws-secret-key>
AWS_S3_BUCKET=coredent-production-files
AWS_REGION=us-east-1

# Redis
REDIS_URL=redis://default:password@host:6379
REDIS_CACHE_TTL=3600

# Sentry (Error Tracking)
SENTRY_DSN=https://...@sentry.io/...

# Stripe (if using)
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# HIPAA Compliance
AUDIT_LOG_ENABLED=True
SESSION_TIMEOUT_MINUTES=15
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=True
PASSWORD_REQUIRE_LOWERCASE=True
PASSWORD_REQUIRE_DIGIT=True
PASSWORD_REQUIRE_SPECIAL=True
PASSWORD_EXPIRE_DAYS=90

# Monitoring
MONITORING_TOKEN=<your-monitoring-token>

# Cookie Settings
COOKIE_SAMESITE=none
COOKIE_SECURE=true
```

### Frontend (.env.production)

```bash
# API
VITE_API_BASE_URL=https://api.coredent.com/api/v1

# Feature Flags
VITE_ENABLE_DEMO_MODE=false
VITE_DEV_BYPASS_AUTH=false

# Analytics
VITE_ANALYTICS_ENABLED=true
VITE_POSTHOG_KEY=<posthog-key>

# Error Monitoring
VITE_SENTRY_DSN=<sentry-dsn>
VITE_SENTRY_ENVIRONMENT=production

# Payments
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Features
VITE_ENABLE_PUSH_NOTIFICATIONS=true
VITE_ENABLE_EMAIL_NOTIFICATIONS=true
VITE_ENABLE_SMS_NOTIFICATIONS=true
VITE_ENABLE_MFA=true

# Debug
VITE_DEBUG=false
VITE_ENABLE_DEVTOOLS=false
```

---

## Step 4: Deploy Backend

### Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Set environment variables
railway variables set SECRET_KEY=<your-secret>
railway variables set DATABASE_URL=<your-db-url>
# ... set all other variables

# Deploy
railway up
```

### Docker Deployment

```bash
# Build image
docker build -t coredent-api:latest ./coredent-api

# Push to registry
docker tag coredent-api:latest registry.example.com/coredent-api:latest
docker push registry.example.com/coredent-api:latest

# Deploy (example with docker-compose)
docker-compose -f docker-compose.prod.yml up -d
```

---

## Step 5: Run Database Migrations

```bash
# SSH into production server or use Railway CLI
railway run alembic upgrade head

# Verify migrations
railway run alembic current
```

---

## Step 6: Deploy Frontend

### Railway/Vercel Deployment

```bash
# Build frontend
cd coredent-style-main
npm run build:prod

# Deploy to Railway
railway up

# Or deploy to Vercel
vercel --prod
```

### Nginx Deployment

```bash
# Build
npm run build:prod

# Copy to server
scp -r dist/* user@server:/var/www/coredent

# Nginx config
server {
    listen 443 ssl http2;
    server_name app.coredent.com;
    
    ssl_certificate /etc/letsencrypt/live/app.coredent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.coredent.com/privkey.pem;
    
    root /var/www/coredent;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

---

## Step 7: Verify Deployment

### Health Checks

```bash
# Backend health
curl https://api.coredent.com/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  }
}

# Frontend
curl https://app.coredent.com

# Should return HTML
```

### Test Authentication

```bash
# Test login
curl -X POST https://api.coredent.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

---

## Step 8: Set Up Monitoring

### Sentry

1. Create project at sentry.io
2. Copy DSN
3. Set `SENTRY_DSN` environment variable
4. Verify errors are being tracked

### Uptime Monitoring

1. Set up UptimeRobot or Pingdom
2. Monitor:
   - `https://api.coredent.com/health`
   - `https://app.coredent.com`
3. Configure alerts (email, Slack, PagerDuty)

### Log Aggregation

```bash
# Option 1: Papertrail
# Add log drain in Railway dashboard

# Option 2: AWS CloudWatch
# Configure CloudWatch agent

# Option 3: Datadog
# Install Datadog agent
```

---

## Step 9: Configure Backups

### Database Backups

```bash
# Automated backups (Railway)
# Enabled by default, 7-day retention

# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20260504.sql
```

### S3 Versioning

```bash
# Enable versioning on S3 bucket
aws s3api put-bucket-versioning \
  --bucket coredent-production-files \
  --versioning-configuration Status=Enabled
```

---

## Step 10: SSL/TLS Configuration

### Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.coredent.com -d app.coredent.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Cloudflare (Recommended)

1. Add domain to Cloudflare
2. Enable "Full (strict)" SSL mode
3. Enable "Always Use HTTPS"
4. Enable "Automatic HTTPS Rewrites"
5. Configure firewall rules

---

## Step 11: Create Admin User

```bash
# SSH into production
railway run python

# In Python shell:
from app.models.user import User
from app.models.practice import Practice
from app.core.security import get_password_hash
from app.core.database import SessionLocal

db = SessionLocal()

# Create practice
practice = Practice(
    name="Admin Practice",
    email="admin@coredent.com"
)
db.add(practice)
db.commit()

# Create admin user
admin = User(
    email="admin@coredent.com",
    password_hash=get_password_hash("ChangeMe123!"),
    first_name="Admin",
    last_name="User",
    role="owner",
    practice_id=practice.id,
    is_active=True,
    is_email_verified=True
)
db.add(admin)
db.commit()

print(f"Admin user created: {admin.email}")
```

---

## Step 12: Post-Deployment Checklist

- [ ] Health endpoints responding
- [ ] Authentication working
- [ ] Email delivery working
- [ ] File uploads to S3 working
- [ ] Database migrations applied
- [ ] Redis caching working
- [ ] Sentry receiving errors
- [ ] Monitoring alerts configured
- [ ] Backups scheduled
- [ ] SSL certificate valid
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Audit logging enabled
- [ ] Admin user created
- [ ] Documentation updated

---

## Troubleshooting

### Issue: App won't start

```bash
# Check logs
railway logs

# Common causes:
# 1. Missing environment variables
# 2. Database connection failed
# 3. Invalid SECRET_KEY
```

### Issue: Database connection failed

```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check firewall rules
# Ensure Railway IP is whitelisted
```

### Issue: 502 Bad Gateway

```bash
# Check if app is running
railway status

# Check health endpoint
curl https://api.coredent.com/health

# Restart app
railway restart
```

### Issue: CORS errors

```bash
# Verify CORS_ORIGINS includes frontend URL
railway variables get CORS_ORIGINS

# Should include: https://app.coredent.com
```

---

## Rollback Procedure

### Rollback Application

```bash
# Railway: Use dashboard to rollback to previous deployment
# Or via CLI:
railway rollback

# Docker: Deploy previous image
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### Rollback Database

```bash
# Downgrade one migration
railway run alembic downgrade -1

# Restore from backup
psql $DATABASE_URL < backup_20260504.sql
```

---

## Scaling

### Horizontal Scaling

```bash
# Railway: Increase replicas in dashboard
# Or via CLI:
railway scale --replicas 3
```

### Database Scaling

```bash
# Add read replicas
# Configure connection pooling
# Consider PgBouncer for connection management
```

---

## Security Hardening

### Firewall Rules

```bash
# Allow only necessary ports
# 443 (HTTPS)
# 5432 (PostgreSQL - from app only)
# 6379 (Redis - from app only)
```

### Rate Limiting

```bash
# Already configured in app
# Additional: Use Cloudflare rate limiting
```

### DDoS Protection

```bash
# Use Cloudflare
# Enable "Under Attack" mode if needed
```

---

## Support

- **Documentation**: https://docs.coredent.com
- **Status Page**: https://status.coredent.com
- **Support Email**: support@coredent.com
- **Emergency**: +1-XXX-XXX-XXXX

---

**Last Updated**: May 4, 2026  
**Version**: 1.0.0

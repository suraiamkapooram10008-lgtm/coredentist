# CoreDent SaaS - Quick Start Guide

**For**: Developers deploying CoreDent for the first time  
**Time**: 30 minutes

---

## 🚀 Deploy in 5 Steps

### 1. Generate Secrets (2 min)

```bash
# Run these commands and save the output
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('MONITORING_TOKEN=' + secrets.token_urlsafe(16))"
```

### 2. Set Up Database (5 min)

**Option A: Railway (Easiest)**
```bash
railway login
railway init
railway add postgresql
# Copy DATABASE_URL from dashboard
```

**Option B: Supabase**
```bash
# 1. Go to supabase.com
# 2. Create project
# 3. Copy connection string from Settings > Database
```

### 3. Configure Environment (5 min)

Create `.env.production`:
```bash
# Copy from .env.example
cp coredent-api/.env.example coredent-api/.env.production

# Edit with your values
nano coredent-api/.env.production
```

**Minimum Required**:
- `SECRET_KEY` (from step 1)
- `ENCRYPTION_KEY` (from step 1)
- `DATABASE_URL` (from step 2)
- `CORS_ORIGINS` (your frontend URL)
- `FRONTEND_URL` (your frontend URL)

### 4. Deploy Backend (10 min)

```bash
cd coredent-api

# Run migrations
railway run alembic upgrade head

# Deploy
railway up

# Verify
curl https://your-app.railway.app/health
```

### 5. Deploy Frontend (8 min)

```bash
cd coredent-style-main

# Set API URL
echo "VITE_API_BASE_URL=https://your-api.railway.app/api/v1" > .env.production

# Build
npm run build:prod

# Deploy
railway up
# or
vercel --prod
```

---

## ✅ Verify Deployment

```bash
# 1. Check backend health
curl https://your-api.railway.app/health

# 2. Check frontend
curl https://your-app.railway.app

# 3. Test login
curl -X POST https://your-api.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

---

## 🔧 Common Issues

### "SECRET_KEY is not set"
```bash
# Make sure you set it in Railway dashboard
railway variables set SECRET_KEY=<your-secret>
```

### "Database connection failed"
```bash
# Verify DATABASE_URL
railway variables get DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### "CORS error"
```bash
# Add your frontend URL to CORS_ORIGINS
railway variables set CORS_ORIGINS=https://your-frontend.com
```

---

## 📚 Full Documentation

- **Production Readiness**: See `PRODUCTION_READINESS.md`
- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md`
- **Changes Made**: See `CHANGES_SUMMARY.md`

---

## 🆘 Need Help?

1. Check logs: `railway logs`
2. Review health: `curl https://your-api/health`
3. Read full guides above
4. Contact: support@coredent.com

---

**Next**: Create your first admin user (see DEPLOYMENT_GUIDE.md Step 11)

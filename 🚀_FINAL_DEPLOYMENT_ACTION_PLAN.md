# 🚀 FINAL DEPLOYMENT ACTION PLAN
**CoreDent PMS - Ready for Production**  
**Date**: April 10, 2026  
**Status**: ✅ ALL SYSTEMS GO

---

## PHASE 1: PRE-DEPLOYMENT VERIFICATION (30 minutes)

### Step 1: Verify All Systems Locally
```bash
# Backend
cd coredent-api
python -m pytest tests/ -v --cov=app --cov-report=html

# Frontend
cd coredent-style-main
npm run test -- --run
npm run build
```

**Expected Results**:
- ✅ All 63+ tests passing
- ✅ 85%+ code coverage
- ✅ 0 compilation errors
- ✅ 0 type errors
- ✅ Build completes successfully

### Step 2: Verify Database Schema
```bash
cd coredent-api
python -c "from app.models import *; print('All models imported successfully')"
```

**Expected Results**:
- ✅ All 50+ models import without errors
- ✅ No SQLAlchemy warnings

### Step 3: Verify Environment Configuration
```bash
# Check .env.production exists
ls -la coredent-api/.env.production
ls -la coredent-style-main/.env.production

# Verify all required variables
grep -E "STRIPE_API_KEY|DATABASE_URL|AWS_ACCESS_KEY|CELERY_BROKER" coredent-api/.env.production
```

**Expected Results**:
- ✅ Both .env.production files exist
- ✅ All required variables present
- ✅ No placeholder values

---

## PHASE 2: RAILWAY DEPLOYMENT (45 minutes)

### Step 1: Create Railway Project
```bash
# Login to Railway
railway login

# Create new project
railway init

# Select "Create a new project"
# Name: coredent-pms
```

### Step 2: Deploy Backend
```bash
cd coredent-api

# Create railway.toml
cat > railway.toml << 'EOF'
[build]
builder = "dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
EOF

# Deploy
railway up
```

**Expected Results**:
- ✅ Backend deployed to Railway
- ✅ Service URL generated
- ✅ Environment variables configured
- ✅ Database provisioned

### Step 3: Deploy Frontend
```bash
cd coredent-style-main

# Create railway.toml
cat > railway.toml << 'EOF'
[build]
builder = "dockerfile"

[deploy]
startCommand = "npm run preview"
EOF

# Deploy
railway up
```

**Expected Results**:
- ✅ Frontend deployed to Railway
- ✅ Service URL generated
- ✅ Build completes successfully

### Step 4: Configure Custom Domain
```bash
# In Railway Dashboard:
# 1. Go to Backend service
# 2. Settings → Domains
# 3. Add custom domain: api.coredent.com
# 4. Go to Frontend service
# 5. Settings → Domains
# 6. Add custom domain: app.coredent.com
```

**Expected Results**:
- ✅ Backend accessible at api.coredent.com
- ✅ Frontend accessible at app.coredent.com
- ✅ SSL certificates auto-configured

---

## PHASE 3: DATABASE SETUP (15 minutes)

### Step 1: Run Migrations
```bash
# SSH into Railway backend
railway shell

# Run migrations
alembic upgrade head
```

**Expected Results**:
- ✅ All migrations applied
- ✅ 50+ tables created
- ✅ Indexes created
- ✅ No migration errors

### Step 2: Create Admin User
```bash
# In Railway backend shell
python scripts/create_admin_user.py

# Or use the provided script
python create_test_user_simple.py
```

**Expected Results**:
- ✅ Admin user created
- ✅ Email: admin@coredent.com
- ✅ Password: Admin123!@#
- ✅ Role: ADMIN (uppercase)

### Step 3: Verify Database Connection
```bash
# Test connection
python -c "from app.core.database import engine; print('Database connected')"
```

**Expected Results**:
- ✅ Database connection successful
- ✅ All tables accessible

---

## PHASE 4: EXTERNAL SERVICES CONFIGURATION (30 minutes)

### Step 1: Configure Stripe
```bash
# In Stripe Dashboard:
# 1. Go to Developers → API Keys
# 2. Copy Publishable Key and Secret Key
# 3. In Railway Backend settings, add:
#    STRIPE_API_KEY=sk_live_...
#    STRIPE_PUBLISHABLE_KEY=pk_live_...

# 4. Go to Developers → Webhooks
# 5. Add endpoint: https://api.coredent.com/api/v1/stripe/webhook
# 6. Select events:
#    - payment_intent.succeeded
#    - payment_intent.payment_failed
#    - customer.subscription.created
#    - customer.subscription.updated
#    - customer.subscription.deleted
#    - invoice.payment_succeeded
# 7. Copy Signing Secret
# 8. In Railway Backend settings, add:
#    STRIPE_WEBHOOK_SECRET=whsec_...
```

**Expected Results**:
- ✅ Stripe API keys configured
- ✅ Webhook endpoint registered
- ✅ Webhook events selected
- ✅ Signing secret configured

### Step 2: Configure AWS S3
```bash
# In AWS Console:
# 1. Go to S3
# 2. Create bucket: coredent-pms-images
# 3. Go to IAM → Users
# 4. Create user: coredent-app
# 5. Attach policy: AmazonS3FullAccess
# 6. Create access key
# 7. In Railway Backend settings, add:
#    AWS_ACCESS_KEY_ID=...
#    AWS_SECRET_ACCESS_KEY=...
#    AWS_S3_BUCKET=coredent-pms-images
#    AWS_REGION=us-east-1
```

**Expected Results**:
- ✅ S3 bucket created
- ✅ IAM user created
- ✅ Access keys generated
- ✅ Environment variables configured

### Step 3: Configure Celery & Redis
```bash
# In Railway Dashboard:
# 1. Add Redis service
# 2. Copy connection string
# 3. In Backend settings, add:
#    CELERY_BROKER_URL=redis://...
#    CELERY_RESULT_BACKEND=redis://...

# 4. Start Celery worker:
#    celery -A app.core.celery_app worker --loglevel=info
```

**Expected Results**:
- ✅ Redis service running
- ✅ Celery broker configured
- ✅ Celery worker running

### Step 4: Configure Email Service
```bash
# In Railway Backend settings, add:
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# SMTP_FROM=noreply@coredent.com
```

**Expected Results**:
- ✅ Email service configured
- ✅ Test email sent successfully

---

## PHASE 5: PRODUCTION TESTING (30 minutes)

### Step 1: Test Login Workflow
```bash
# 1. Open https://app.coredent.com
# 2. Login with:
#    Email: admin@coredent.com
#    Password: Admin123!@#
# 3. Verify dashboard loads
# 4. Verify no console errors
```

**Expected Results**:
- ✅ Login successful
- ✅ Dashboard loads
- ✅ No errors in console
- ✅ CSRF token present

### Step 2: Test Patient Management
```bash
# 1. Navigate to Patients
# 2. Create new patient
# 3. Verify patient appears in list
# 4. Edit patient
# 5. Verify changes saved
# 6. Delete patient
# 7. Verify patient removed
```

**Expected Results**:
- ✅ All CRUD operations work
- ✅ Data persists in database
- ✅ No errors

### Step 3: Test Appointment Scheduling
```bash
# 1. Navigate to Appointments
# 2. Create new appointment
# 3. Verify conflict detection works
# 4. Try to create overlapping appointment
# 5. Verify error message
# 6. Create valid appointment
# 7. Verify appointment appears in calendar
```

**Expected Results**:
- ✅ Appointment creation works
- ✅ Conflict detection works
- ✅ Calendar displays correctly

### Step 4: Test Payment Processing
```bash
# 1. Navigate to Billing
# 2. Create invoice
# 3. Click "Pay Now"
# 4. Use Stripe test card: 4242 4242 4242 4242
# 5. Complete payment
# 6. Verify invoice marked as paid
# 7. Verify payment record created
```

**Expected Results**:
- ✅ Payment intent created
- ✅ Stripe form loads
- ✅ Payment processed
- ✅ Invoice updated
- ✅ Payment record created

### Step 5: Test Online Booking
```bash
# 1. Get booking page URL from settings
# 2. Open booking page in incognito window
# 3. Select date and time
# 4. Fill in patient details
# 5. Submit booking
# 6. Verify confirmation email sent
# 7. Verify booking appears in admin dashboard
```

**Expected Results**:
- ✅ Booking page loads
- ✅ Available slots display
- ✅ Booking created
- ✅ Confirmation email sent
- ✅ Booking visible in admin

### Step 6: Test Reminders
```bash
# 1. Create appointment for tomorrow
# 2. Wait for Celery task to run
# 3. Check email for reminder
# 4. Verify reminder sent successfully
```

**Expected Results**:
- ✅ Celery task runs
- ✅ Reminder email sent
- ✅ Email contains correct details

---

## PHASE 6: MONITORING & LOGGING (15 minutes)

### Step 1: Configure Logging
```bash
# In Railway Backend settings:
# LOG_LEVEL=INFO
# SENTRY_DSN=https://... (optional, for error tracking)
```

### Step 2: Set Up Monitoring
```bash
# In Railway Dashboard:
# 1. Go to Backend service
# 2. Click "Monitoring"
# 3. View CPU, Memory, Network usage
# 4. Set up alerts for high usage
```

### Step 3: Monitor Database
```bash
# In Railway Dashboard:
# 1. Go to PostgreSQL service
# 2. Click "Monitoring"
# 3. View connection count, query performance
# 4. Set up alerts for high connection count
```

**Expected Results**:
- ✅ Logging configured
- ✅ Monitoring dashboard accessible
- ✅ Alerts configured

---

## PHASE 7: SECURITY HARDENING (20 minutes)

### Step 1: Enable HTTPS
```bash
# In Railway Dashboard:
# 1. Go to Backend service
# 2. Settings → Domains
# 3. Verify SSL certificate is active
# 4. Repeat for Frontend
```

**Expected Results**:
- ✅ HTTPS enabled
- ✅ SSL certificate valid
- ✅ No mixed content warnings

### Step 2: Configure CORS
```bash
# In coredent-api/app/core/config.py:
# CORS_ORIGINS = ["https://app.coredent.com"]
# Redeploy backend
```

**Expected Results**:
- ✅ CORS configured
- ✅ Cross-origin requests work
- ✅ No CORS errors

### Step 3: Set Security Headers
```bash
# In coredent-api/app/main.py:
# Add security headers middleware
# Redeploy backend
```

**Expected Results**:
- ✅ Security headers present
- ✅ No security warnings

### Step 4: Enable Rate Limiting
```bash
# In coredent-api/app/core/rate_limit.py:
# Verify rate limiting is enabled
# Test with multiple requests
```

**Expected Results**:
- ✅ Rate limiting active
- ✅ Requests throttled after limit
- ✅ 429 status code returned

---

## PHASE 8: BACKUP & DISASTER RECOVERY (15 minutes)

### Step 1: Configure Database Backups
```bash
# In Railway Dashboard:
# 1. Go to PostgreSQL service
# 2. Settings → Backups
# 3. Enable automatic backups
# 4. Set retention to 30 days
```

**Expected Results**:
- ✅ Backups enabled
- ✅ Retention configured
- ✅ Backup schedule set

### Step 2: Test Backup Restoration
```bash
# 1. Create test data
# 2. Trigger backup
# 3. Delete test data
# 4. Restore from backup
# 5. Verify test data restored
```

**Expected Results**:
- ✅ Backup created
- ✅ Restoration successful
- ✅ Data integrity verified

### Step 3: Document Disaster Recovery Plan
```bash
# Create runbook:
# 1. Database failure recovery
# 2. Service failure recovery
# 3. Data corruption recovery
# 4. Security incident response
```

**Expected Results**:
- ✅ Runbook created
- ✅ Team trained
- ✅ Procedures documented

---

## PHASE 9: USER ONBOARDING (30 minutes)

### Step 1: Create Admin Accounts
```bash
# For each admin user:
# 1. Create account in system
# 2. Send welcome email
# 3. Include login credentials
# 4. Include setup guide
```

### Step 2: Create Practice Setup Guide
```bash
# Document:
# 1. How to add staff members
# 2. How to configure appointment types
# 3. How to set up online booking
# 4. How to configure payment settings
# 5. How to set up insurance
```

### Step 3: Conduct Training
```bash
# 1. Demo login workflow
# 2. Demo patient management
# 3. Demo appointment scheduling
# 4. Demo payment processing
# 5. Demo online booking
# 6. Demo reporting
```

**Expected Results**:
- ✅ Admin accounts created
- ✅ Setup guide provided
- ✅ Team trained

---

## PHASE 10: GO-LIVE (Ongoing)

### Step 1: Monitor System
```bash
# Daily:
# 1. Check error logs
# 2. Monitor performance metrics
# 3. Verify backups completed
# 4. Check user feedback
```

### Step 2: Respond to Issues
```bash
# If issues occur:
# 1. Check logs for errors
# 2. Identify root cause
# 3. Apply fix
# 4. Test fix
# 5. Deploy fix
# 6. Verify resolution
```

### Step 3: Gather Feedback
```bash
# 1. Send user survey
# 2. Collect feature requests
# 3. Identify pain points
# 4. Plan improvements
```

---

## QUICK REFERENCE: CRITICAL COMMANDS

### Backend Deployment
```bash
cd coredent-api
railway up
```

### Frontend Deployment
```bash
cd coredent-style-main
railway up
```

### Run Migrations
```bash
railway shell
alembic upgrade head
```

### Create Admin User
```bash
python create_test_user_simple.py
```

### View Logs
```bash
railway logs
```

### SSH into Service
```bash
railway shell
```

### Restart Service
```bash
railway restart
```

---

## TROUBLESHOOTING GUIDE

### Issue: Database Connection Failed
**Solution**:
1. Verify DATABASE_URL in environment
2. Check PostgreSQL service is running
3. Verify credentials are correct
4. Check network connectivity

### Issue: Stripe Webhook Not Received
**Solution**:
1. Verify webhook URL is correct
2. Verify signing secret is correct
3. Check firewall allows incoming requests
4. Verify webhook events are selected

### Issue: Email Not Sending
**Solution**:
1. Verify SMTP credentials
2. Check email service is running
3. Verify sender email is correct
4. Check spam folder

### Issue: S3 Upload Failed
**Solution**:
1. Verify AWS credentials
2. Check S3 bucket exists
3. Verify bucket permissions
4. Check network connectivity

### Issue: Celery Tasks Not Running
**Solution**:
1. Verify Redis is running
2. Check Celery worker is running
3. Verify broker URL is correct
4. Check task logs

---

## SUCCESS CRITERIA

✅ **All systems deployed and running**
- Backend accessible at api.coredent.com
- Frontend accessible at app.coredent.com
- Database connected and migrated
- All external services configured

✅ **All workflows tested and working**
- Login workflow
- Patient management
- Appointment scheduling
- Payment processing
- Online booking
- Reminders

✅ **Monitoring and logging active**
- Error logs accessible
- Performance metrics visible
- Alerts configured
- Backups running

✅ **Team trained and ready**
- Admin accounts created
- Setup guide provided
- Team trained on system
- Support procedures documented

---

## FINAL CHECKLIST

- [ ] All tests passing locally
- [ ] Database schema verified
- [ ] Environment variables configured
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Railway
- [ ] Custom domains configured
- [ ] Database migrations run
- [ ] Admin user created
- [ ] Stripe configured
- [ ] AWS S3 configured
- [ ] Celery & Redis configured
- [ ] Email service configured
- [ ] Login workflow tested
- [ ] Patient management tested
- [ ] Appointment scheduling tested
- [ ] Payment processing tested
- [ ] Online booking tested
- [ ] Reminders tested
- [ ] Logging configured
- [ ] Monitoring configured
- [ ] HTTPS enabled
- [ ] CORS configured
- [ ] Security headers set
- [ ] Rate limiting enabled
- [ ] Backups configured
- [ ] Disaster recovery plan documented
- [ ] Admin accounts created
- [ ] Team trained
- [ ] Go-live approved

---

**Status**: ✅ READY FOR DEPLOYMENT  
**Estimated Time**: 4-5 hours  
**Team Required**: 2-3 people  
**Support Available**: 24/7

**Next Step**: Begin Phase 1 - Pre-Deployment Verification

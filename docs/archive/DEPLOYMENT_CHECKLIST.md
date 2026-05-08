# CoreDent SaaS - Deployment Checklist

**Use this checklist to deploy CoreDent to production**

---

## ☑️ Pre-Deployment (1-2 Hours)

### 1. Generate Secrets
```bash
# Run these and save outputs securely
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('MONITORING_TOKEN=' + secrets.token_urlsafe(16))"
```
- [ ] SECRET_KEY generated (32+ characters)
- [ ] ENCRYPTION_KEY generated (32+ characters)
- [ ] MONITORING_TOKEN generated (16+ characters)
- [ ] Secrets stored in password manager

### 2. Set Up Infrastructure
- [ ] PostgreSQL database provisioned
- [ ] Redis instance provisioned (optional but recommended)
- [ ] AWS S3 bucket created
- [ ] Domain registered
- [ ] SSL certificate obtained
- [ ] Email service configured (SendGrid/AWS SES)

### 3. Configure Environment Variables
**Backend** (`coredent-api/.env.production`):
- [ ] `SECRET_KEY` set
- [ ] `ENCRYPTION_KEY` set
- [ ] `DATABASE_URL` set
- [ ] `REDIS_URL` set
- [ ] `CORS_ORIGINS` set (frontend URL)
- [ ] `FRONTEND_URL` set
- [ ] `SMTP_*` variables set
- [ ] `AWS_*` variables set
- [ ] `SENTRY_DSN` set
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=False`

**Frontend** (`coredent-style-main/.env.production`):
- [ ] `VITE_API_BASE_URL` set (backend URL)
- [ ] `VITE_ENABLE_DEMO_MODE=false`
- [ ] `VITE_SENTRY_DSN` set
- [ ] `VITE_ANALYTICS_ENABLED=true`

---

## ☑️ Deployment (30-60 Minutes)

### 4. Deploy Backend
```bash
cd coredent-api

# Option A: Railway
railway login
railway link
railway up

# Option B: Docker
docker build -t coredent-api:latest .
docker push registry.example.com/coredent-api:latest
```
- [ ] Backend deployed
- [ ] Health endpoint responding (`/health`)
- [ ] No startup errors in logs

### 5. Run Database Migrations
```bash
# Via Railway
railway run alembic upgrade head

# Via Docker
docker exec coredent-api alembic upgrade head
```
- [ ] Migrations completed successfully
- [ ] No migration errors
- [ ] Database schema verified

### 6. Deploy Frontend
```bash
cd coredent-style-main

# Build
npm run build:prod

# Deploy (Railway/Vercel)
railway up
# or
vercel --prod
```
- [ ] Frontend deployed
- [ ] Site loads correctly
- [ ] No console errors

---

## ☑️ Verification (15-30 Minutes)

### 7. Test Backend
```bash
# Health check
curl https://api.coredent.com/health

# Expected: {"status":"healthy",...}
```
- [ ] Health endpoint returns 200
- [ ] Database check passes
- [ ] Redis check passes (if configured)

### 8. Test Authentication
```bash
# Create admin user first (see step 9)
# Then test login
curl -X POST https://api.coredent.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@coredent.com","password":"YourPassword123!"}'
```
- [ ] Login returns access_token
- [ ] Login returns refresh_token
- [ ] Token works for authenticated endpoints

### 9. Create Admin User
```bash
# SSH into production or use Railway CLI
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
print(f"Admin created: {admin.email}")
```
- [ ] Admin user created
- [ ] Can login with admin credentials
- [ ] Admin has owner role

### 10. Test Core Features
- [ ] Login works
- [ ] Dashboard loads
- [ ] Can create patient
- [ ] Can create appointment
- [ ] Can create invoice
- [ ] Email delivery works
- [ ] File upload works (if S3 configured)

---

## ☑️ Monitoring Setup (30 Minutes)

### 11. Configure Monitoring
**Sentry**:
- [ ] Project created at sentry.io
- [ ] DSN configured in environment
- [ ] Test error sent and received

**Uptime Monitoring**:
- [ ] UptimeRobot/Pingdom configured
- [ ] Monitoring `/health` endpoint
- [ ] Alert email/Slack configured

**Logs**:
- [ ] Log aggregation configured (Papertrail/CloudWatch)
- [ ] Can view application logs
- [ ] Can search logs

### 12. Set Up Backups
- [ ] Database automated backups enabled
- [ ] Backup retention policy set (7+ days)
- [ ] Test backup restoration
- [ ] S3 versioning enabled

---

## ☑️ Security Hardening (15 Minutes)

### 13. Security Checks
- [ ] HTTPS working (no HTTP access)
- [ ] SSL certificate valid
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Audit logging enabled
- [ ] No default secrets in use
- [ ] Firewall rules configured

### 14. Access Control
- [ ] Admin password changed from default
- [ ] Database access restricted
- [ ] Redis access restricted (if used)
- [ ] S3 bucket not public
- [ ] API keys rotated

---

## ☑️ Documentation (15 Minutes)

### 15. Update Documentation
- [ ] Production URLs documented
- [ ] Admin credentials stored securely
- [ ] Deployment process documented
- [ ] Rollback procedure documented
- [ ] Support contacts listed

---

## ☑️ Post-Deployment (Ongoing)

### 16. Monitor for 48 Hours
**First 24 Hours**:
- [ ] Check logs every 2 hours
- [ ] Monitor error rates
- [ ] Watch response times
- [ ] Check uptime

**Next 24 Hours**:
- [ ] Check logs every 4 hours
- [ ] Review Sentry errors
- [ ] Check database performance
- [ ] Monitor disk usage

### 17. Onboard First User
- [ ] Create practice account
- [ ] Add sample patient
- [ ] Create test appointment
- [ ] Generate test invoice
- [ ] Gather feedback

---

## 🚨 Rollback Plan

### If Issues Occur:

**Application Rollback**:
```bash
# Railway
railway rollback

# Docker
docker-compose down
docker-compose up -d --force-recreate
```

**Database Rollback**:
```bash
# Downgrade one migration
alembic downgrade -1

# Or restore from backup
psql $DATABASE_URL < backup_YYYYMMDD.sql
```

**When to Rollback**:
- [ ] Critical security issue
- [ ] Data corruption
- [ ] >50% error rate
- [ ] Complete service outage
- [ ] Database migration failure

---

## ✅ Success Criteria

### Deployment Successful If:
- [x] All health checks passing
- [x] Admin can login
- [x] Core features work
- [x] No critical errors
- [x] Monitoring active
- [x] Backups configured

### Ready for Users If:
- [x] Deployment successful
- [x] 48-hour monitoring complete
- [x] No critical issues found
- [x] Support process ready
- [x] Documentation complete

---

## 📞 Emergency Contacts

**Technical Issues**:
- Developer: [Your contact]
- DevOps: [Your contact]
- Database: [Your contact]

**Service Providers**:
- Railway Support: support@railway.app
- Sentry Support: support@sentry.io
- AWS Support: [Your support plan]

**Escalation**:
1. Check logs and monitoring
2. Review this checklist
3. Check DEPLOYMENT_GUIDE.md
4. Contact technical team
5. Escalate to service providers

---

## 📝 Notes

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Backend URL**: _______________  
**Frontend URL**: _______________  
**Database**: _______________  
**Issues Encountered**: 

_______________________________________________
_______________________________________________
_______________________________________________

**Resolution**:

_______________________________________________
_______________________________________________
_______________________________________________

---

## 🎯 Next Steps After Deployment

### Week 1
- [ ] Monitor daily
- [ ] Fix any bugs
- [ ] Onboard 2-3 pilot practices
- [ ] Gather feedback

### Week 2-4
- [ ] Onboard 5-10 practices
- [ ] Iterate on feedback
- [ ] Add missing features
- [ ] Improve documentation

### Month 2-3
- [ ] Implement OAuth2
- [ ] Increase test coverage to 70%+
- [ ] Security audit
- [ ] Performance optimization
- [ ] Prepare for full launch

---

**Status**: ⬜ Not Started | ⏳ In Progress | ✅ Complete | ❌ Failed

**Last Updated**: _______________  
**Next Review**: _______________

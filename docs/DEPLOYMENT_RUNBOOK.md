# CoreDent Deployment Runbook

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (`pytest --cov=app --cov-fail-under=80`)
- [ ] Linting passed (`black app/ && flake8 app/`)
- [ ] Type checking passed (`mypy app/`)
- [ ] Security scan clean (`bandit -r app/`)
- [ ] Dependencies updated and audited (`safety check`)

### Database
- [ ] Migrations tested locally
- [ ] Backup created
- [ ] Rollback plan documented
- [ ] Index performance verified

### Configuration
- [ ] Environment variables set
- [ ] Secrets rotated (if needed)
- [ ] Feature flags configured
- [ ] Rate limits adjusted

### Monitoring
- [ ] Sentry configured
- [ ] Prometheus metrics enabled
- [ ] Log aggregation working
- [ ] Alerts configured

## Deployment Steps

### 1. Pre-Deployment

```bash
# 1.1 Create database backup
python scripts/backup_database.py --environment production

# 1.2 Verify backup
python scripts/verify_backup.py --file backup_YYYYMMDD.sql

# 1.3 Tag release
git tag -a v1.x.x -m "Release v1.x.x"
git push origin v1.x.x

# 1.4 Build Docker image
docker build -t coredent-api:v1.x.x ./coredent-api
docker tag coredent-api:v1.x.x coredent-api:latest
```

### 2. Staging Deployment

```bash
# 2.1 Deploy to staging
railway up --service coredent-api-staging

# 2.2 Run migrations
railway run --service coredent-api-staging alembic upgrade head

# 2.3 Smoke tests
curl https://staging-api.coredent.com/health
curl https://staging-api.coredent.com/api/v1/health

# 2.4 Run E2E tests
cd coredent-style-main
npm run test:e2e -- --config baseUrl=https://staging-api.coredent.com
```

### 3. Production Deployment

```bash
# 3.1 Enable maintenance mode (optional)
railway run --service coredent-api-production \
  python scripts/maintenance_mode.py --enable

# 3.2 Deploy application
railway up --service coredent-api-production

# 3.3 Run migrations
railway run --service coredent-api-production alembic upgrade head

# 3.4 Verify deployment
curl https://api.coredent.com/health

# 3.5 Disable maintenance mode
railway run --service coredent-api-production \
  python scripts/maintenance_mode.py --disable

# 3.6 Monitor for 15 minutes
# Watch error rates, latency, and logs
```

### 4. Post-Deployment

```bash
# 4.1 Verify critical paths
python scripts/smoke_tests.py --environment production

# 4.2 Check metrics
# - Error rate < 0.1%
# - P95 latency < 500ms
# - Database connections healthy

# 4.3 Notify team
# Send deployment notification to Slack

# 4.4 Update documentation
# Update CHANGELOG.md with release notes
```

## Rollback Procedure

### Quick Rollback (< 5 minutes)

```bash
# 1. Revert to previous Docker image
railway rollback --service coredent-api-production

# 2. Verify health
curl https://api.coredent.com/health

# 3. Notify team
echo "Rolled back to previous version"
```

### Database Rollback

```bash
# 1. Check current migration
railway run --service coredent-api-production alembic current

# 2. Downgrade migration
railway run --service coredent-api-production alembic downgrade -1

# 3. Verify database state
railway run --service coredent-api-production \
  python scripts/verify_database.py
```

### Full Rollback (> 5 minutes)

```bash
# 1. Stop application
railway down --service coredent-api-production

# 2. Restore database from backup
psql $DATABASE_URL < backup_YYYYMMDD.sql

# 3. Deploy previous version
git checkout v1.x.x-1
railway up --service coredent-api-production

# 4. Verify health
curl https://api.coredent.com/health
```

## Database Migration Guide

### Safe Migration Practices

1. **Additive Changes Only**
   - Add new columns as nullable
   - Add new tables
   - Add new indexes (CONCURRENTLY)

2. **Avoid in Production**
   - Dropping columns (use deprecation)
   - Renaming columns (use aliasing)
   - Changing column types

3. **Large Table Migrations**
   - Use batching for data migrations
   - Create indexes CONCURRENTLY
   - Monitor lock duration

### Migration Template

```python
"""migration description

Revision ID: YYYYMMDD_HHMM
Revises: previous_revision
Create Date: YYYY-MM-DD HH:MM:SS

"""
from alembic import op
import sqlalchemy as sa

revision = 'YYYYMMDD_HHMM'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add column as nullable first
    op.add_column('patients', 
        sa.Column('new_field', sa.String(255), nullable=True)
    )
    
    # Backfill data in batches
    # (Use separate script for large tables)
    
    # Make non-nullable if needed (after backfill)
    # op.alter_column('patients', 'new_field', nullable=False)

def downgrade() -> None:
    op.drop_column('patients', 'new_field')
```

### Running Migrations

```bash
# 1. Test locally
alembic upgrade head

# 2. Test on staging
railway run --service coredent-api-staging alembic upgrade head

# 3. Backup production
python scripts/backup_database.py --environment production

# 4. Run on production
railway run --service coredent-api-production alembic upgrade head

# 5. Verify
railway run --service coredent-api-production alembic current
```

## Monitoring During Deployment

### Key Metrics to Watch

1. **Error Rate**
   - Target: < 0.1%
   - Alert: > 1%
   - Critical: > 5%

2. **Response Time**
   - Target: P95 < 500ms
   - Alert: P95 > 1s
   - Critical: P95 > 2s

3. **Database**
   - Connection pool usage < 80%
   - Query time P95 < 100ms
   - Lock wait time < 10ms

4. **Cache**
   - Hit rate > 80%
   - Connection errors = 0

### Monitoring Commands

```bash
# Check error rate
curl https://api.coredent.com/metrics | grep error_rate

# Check response time
curl https://api.coredent.com/metrics | grep response_time

# Check database connections
railway run --service coredent-api-production \
  python scripts/check_db_connections.py

# Check Redis
redis-cli -h $REDIS_HOST ping
redis-cli -h $REDIS_HOST info stats
```

## Troubleshooting

### Common Issues

#### 1. Migration Fails

**Symptoms:** Alembic upgrade fails

**Solution:**
```bash
# Check current state
alembic current

# Check pending migrations
alembic heads

# Manual fix if needed
psql $DATABASE_URL
# Run SQL manually

# Stamp migration as complete
alembic stamp head
```

#### 2. High Error Rate

**Symptoms:** Error rate > 1%

**Solution:**
```bash
# Check logs
railway logs --service coredent-api-production

# Check Sentry
# Visit Sentry dashboard

# Rollback if critical
railway rollback --service coredent-api-production
```

#### 3. Database Connection Issues

**Symptoms:** Connection pool exhausted

**Solution:**
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE state = 'idle' 
  AND state_change < now() - interval '5 minutes';"

# Restart application
railway restart --service coredent-api-production
```

#### 4. Redis Connection Issues

**Symptoms:** Cache failures

**Solution:**
```bash
# Check Redis health
redis-cli -h $REDIS_HOST ping

# Check memory usage
redis-cli -h $REDIS_HOST info memory

# Clear cache if needed
redis-cli -h $REDIS_HOST FLUSHDB

# Restart application
railway restart --service coredent-api-production
```

## Emergency Procedures

### Complete System Failure

1. **Immediate Actions**
   ```bash
   # Enable maintenance page
   railway run python scripts/maintenance_mode.py --enable
   
   # Notify team
   # Post to #incidents Slack channel
   
   # Check status page
   # Update status.coredent.com
   ```

2. **Investigation**
   ```bash
   # Check logs
   railway logs --tail 1000
   
   # Check metrics
   # Visit Grafana dashboard
   
   # Check database
   psql $DATABASE_URL -c "SELECT 1;"
   
   # Check Redis
   redis-cli ping
   ```

3. **Recovery**
   ```bash
   # Rollback to last known good version
   railway rollback
   
   # Or restore from backup
   psql $DATABASE_URL < backup_latest.sql
   
   # Verify health
   curl https://api.coredent.com/health
   
   # Disable maintenance mode
   railway run python scripts/maintenance_mode.py --disable
   ```

### Data Corruption

1. **Stop writes immediately**
   ```bash
   railway run python scripts/read_only_mode.py --enable
   ```

2. **Assess damage**
   ```bash
   python scripts/data_integrity_check.py
   ```

3. **Restore from backup**
   ```bash
   # Restore to point-in-time before corruption
   python scripts/restore_backup.py --timestamp "2026-04-30 12:00:00"
   ```

## Contact Information

### On-Call Rotation
- Primary: [Name] - [Phone]
- Secondary: [Name] - [Phone]
- Escalation: [Name] - [Phone]

### External Services
- Railway Support: support@railway.app
- AWS Support: [Account Number]
- Sentry: support@sentry.io

### Internal Resources
- Runbook: https://docs.coredent.com/runbook
- Architecture: https://docs.coredent.com/architecture
- Slack: #engineering, #incidents

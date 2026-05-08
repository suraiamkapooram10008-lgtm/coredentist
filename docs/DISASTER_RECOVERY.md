# CoreDent Disaster Recovery Plan

## Overview

This document outlines procedures for recovering from catastrophic failures.

**Recovery Time Objective (RTO):** 4 hours  
**Recovery Point Objective (RPO):** 1 hour  
**Last Updated:** 2026-05-07
**Next Review:** 2026-08-07  
**Drill Schedule:** First Monday of each quarter  

## Disaster Scenarios

### 1. Complete Database Loss

**Scenario:** PostgreSQL database is corrupted or lost

**Impact:** Complete system outage

**Recovery Steps:**

```bash
# 1. Provision new database
railway create-database --name coredent-db-new

# 2. Restore from latest backup
export NEW_DB_URL="postgresql://..."
psql $NEW_DB_URL < backups/latest.sql

# 3. Verify data integrity
python scripts/verify_database.py --database $NEW_DB_URL

# 4. Update application configuration
railway env set DATABASE_URL=$NEW_DB_URL

# 5. Restart application
railway restart --service coredent-api-production

# 6. Verify health
curl https://api.coredent.com/health

# 7. Monitor for 1 hour
# Watch error rates and user reports
```

**Estimated Recovery Time:** 2-3 hours

### 2. Complete Application Failure

**Scenario:** Application servers are down

**Impact:** System unavailable

**Recovery Steps:**

```bash
# 1. Check infrastructure status
railway status

# 2. Redeploy application
railway up --service coredent-api-production

# 3. If deployment fails, use backup region
railway deploy --region us-west

# 4. Verify health
curl https://api.coredent.com/health

# 5. Update DNS if region changed
# Point api.coredent.com to new region
```

**Estimated Recovery Time:** 30 minutes - 1 hour

### 3. Data Center Outage

**Scenario:** Entire AWS region is down

**Impact:** Complete system outage

**Recovery Steps:**

```bash
# 1. Activate backup region
railway switch-region --to us-west

# 2. Restore database in new region
psql $BACKUP_DB_URL < backups/latest.sql

# 3. Deploy application to new region
railway up --region us-west

# 4. Update DNS
# Point api.coredent.com to new region IP

# 5. Verify health
curl https://api.coredent.com/health

# 6. Notify users
# Send email about temporary service disruption
```

**Estimated Recovery Time:** 3-4 hours

### 4. Security Breach

**Scenario:** Unauthorized access detected

**Impact:** Data confidentiality at risk

**Recovery Steps:**

```bash
# 1. IMMEDIATE: Isolate affected systems
railway down --service coredent-api-production

# 2. Rotate all secrets
python scripts/rotate_secrets.py --all

# 3. Audit access logs
python scripts/audit_access.py --since "24 hours ago"

# 4. Identify compromised data
python scripts/identify_breach.py

# 5. Notify affected users (HIPAA requirement)
python scripts/notify_breach.py --users affected_users.csv

# 6. Deploy patched version
railway up --service coredent-api-production

# 7. File breach report (if PHI affected)
# Report to HHS within 60 days
```

**Estimated Recovery Time:** 4-8 hours (investigation ongoing)

### 5. Ransomware Attack

**Scenario:** Systems encrypted by ransomware

**Impact:** Complete system outage

**Recovery Steps:**

```bash
# 1. DO NOT PAY RANSOM
# Paying does not guarantee data recovery

# 2. Isolate all systems
# Disconnect from network immediately

# 3. Assess damage
# Identify encrypted systems

# 4. Restore from clean backups
# Use backups from before infection

# 5. Rebuild infrastructure
railway create-project --name coredent-recovery

# 6. Deploy from clean source
git clone https://github.com/coredent/api.git
railway up

# 7. Restore database
psql $NEW_DB_URL < backups/clean_backup.sql

# 8. Security audit
# Scan all systems for malware

# 9. Notify authorities
# Report to FBI, local law enforcement
```

**Estimated Recovery Time:** 8-24 hours

## Backup Strategy

### Automated Backups

**Database Backups:**
- Frequency: Every 6 hours
- Retention: 30 days
- Location: AWS S3 (encrypted)
- Verification: Daily integrity checks

```bash
# Backup script (runs via cron)
0 */6 * * * python /app/scripts/backup_database.py
```

**File Backups:**
- Frequency: Daily
- Retention: 90 days
- Location: AWS S3 (versioned)

**Configuration Backups:**
- Frequency: On every change
- Retention: Indefinite
- Location: Git repository

### Manual Backup

```bash
# Create manual backup
python scripts/backup_database.py --manual --tag "pre-migration"

# Verify backup
python scripts/verify_backup.py --file backup_YYYYMMDD.sql

# Upload to S3
aws s3 cp backup_YYYYMMDD.sql s3://coredent-backups/manual/
```

### Backup Testing

**Monthly Test:**
```bash
# 1. Restore to test environment
python scripts/restore_backup.py --environment test --file latest.sql

# 2. Run integrity checks
python scripts/verify_database.py --environment test

# 3. Run smoke tests
pytest tests/smoke/ --environment test

# 4. Document results
echo "Backup test passed" >> backup_test_log.txt
```

## Recovery Procedures

### Database Recovery

#### Point-in-Time Recovery

```bash
# 1. Identify recovery point
# "We need to restore to 2026-04-30 14:30:00"

# 2. Find appropriate backup
ls -la backups/ | grep "2026-04-30"

# 3. Restore base backup
psql $DATABASE_URL < backups/backup_20260430_1200.sql

# 4. Apply WAL logs up to recovery point
# (If using continuous archiving)
pg_restore --target-time "2026-04-30 14:30:00"

# 5. Verify data
python scripts/verify_database.py
```

#### Partial Data Recovery

```bash
# 1. Restore to temporary database
psql $TEMP_DB_URL < backups/latest.sql

# 2. Export specific data
psql $TEMP_DB_URL -c "COPY (
  SELECT * FROM patients WHERE practice_id = 'xxx'
) TO '/tmp/patients.csv' CSV HEADER;"

# 3. Import to production
psql $DATABASE_URL -c "COPY patients FROM '/tmp/patients.csv' CSV HEADER;"

# 4. Verify import
psql $DATABASE_URL -c "SELECT count(*) FROM patients WHERE practice_id = 'xxx';"
```

### Application Recovery

#### Rollback to Previous Version

```bash
# 1. Identify last known good version
git log --oneline

# 2. Checkout version
git checkout v1.x.x

# 3. Deploy
railway up --service coredent-api-production

# 4. Verify
curl https://api.coredent.com/health
```

#### Rebuild from Source

```bash
# 1. Clone repository
git clone https://github.com/coredent/api.git
cd api

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Deploy
railway up

# 5. Verify
curl https://api.coredent.com/health
```

## Communication Plan

### Internal Communication

**Incident Severity Levels:**

- **P0 (Critical):** Complete system outage
  - Notify: All engineering, management, CEO
  - Channel: Phone + Slack #incidents
  - Response Time: Immediate

- **P1 (High):** Partial outage or data loss
  - Notify: Engineering team, management
  - Channel: Slack #incidents
  - Response Time: 15 minutes

- **P2 (Medium):** Degraded performance
  - Notify: Engineering team
  - Channel: Slack #engineering
  - Response Time: 1 hour

- **P3 (Low):** Minor issues
  - Notify: On-call engineer
  - Channel: Slack #engineering
  - Response Time: 4 hours

### External Communication

**Status Page Updates:**
> **CONFIGURE:** Replace `YOUR_PAGE_ID` and `YOUR_OAUTH_TOKEN` with actual Statuspage credentials
```bash
# Update status page
curl -X POST https://api.statuspage.io/v1/pages/YOUR_PAGE_ID/incidents \
  -H "Authorization: OAuth YOUR_OAUTH_TOKEN" \
  -d '{
    "incident": {
      "name": "Database Outage",
      "status": "investigating",
      "impact": "critical",
      "body": "We are investigating a database outage..."
    }
  }'
```

**User Notifications:**
```bash
# Send email to all users
python scripts/send_notification.py \
  --template "system_outage" \
  --severity "critical" \
  --message "We are experiencing technical difficulties..."
```

**HIPAA Breach Notification:**
- Timeline: Within 60 days of discovery
- Recipients: Affected individuals, HHS, media (if >500 affected)
- Method: Written notice via mail

## Testing & Drills

### Quarterly Disaster Recovery Drill

**Schedule:** First Monday of each quarter

**Procedure:**
1. Announce drill to team
2. Simulate disaster scenario
3. Execute recovery procedures
4. Document time to recovery
5. Identify improvements
6. Update runbook

**Scenarios to Test:**
- Q1: Database failure
- Q2: Application failure
- Q3: Region outage
- Q4: Security breach

### Annual Full Recovery Test

**Schedule:** Once per year

**Procedure:**
1. Schedule maintenance window
2. Take production snapshot
3. Simulate complete failure
4. Recover from backups
5. Verify all systems
6. Document lessons learned

## Contact Information

### Emergency Contacts

> **NOTE:** Replace all placeholder information with actual team contact details before production deployment.

**On-Call Engineer:**
- Primary: John Smith - (555) 123-4567 - john.smith@coredent.com
- Secondary: Sarah Johnson - (555) 987-6543 - sarah.johnson@coredent.com

**Engineering Management:**
- Engineering Manager: Michael Chen - (555) 456-7890 - michael.chen@coredent.com
- CTO: David Rodriguez - (555) 234-5678 - david.rodriguez@coredent.com

**Executive Management:**
- CEO: Robert Williams - (555) 345-6789 - robert.williams@coredent.com
- HIPAA Security Officer: Lisa Thompson - (555) 567-8901 - lisa.thompson@coredent.com
- Legal/Compliance: James Wilson - (555) 678-9012 - james.wilson@coredent.com

**External Services (Vendor Contacts):**
| Vendor | Service | Contact | Phone | Email |
|--------|---------|---------|-------|-------|
| Railway | Hosting | Support | | support@railway.app |
| AWS | Cloud Infrastructure | Support | 1-800-865-3210 | aws-support@amazon.com |
| Stripe | Payment Processing | Support | | support@stripe.com |
| Razorpay | Payment Processing | Support | | support@razorpay.com |
| Sentry | Error Tracking | Support | | support@sentry.io |
| SendGrid/AWS SES | Email Service | Support | | support@sendgrid.com |
| Twilio | SMS Service (if enabled) | Support | | help@twilio.com |

### Vendor BAA Status

> **CRITICAL:** Business Associate Agreements (BAAs) must be signed with ALL third-party vendors that handle PHI/ePHI before production deployment. Update this table as BAAs are signed.

| Vendor | BAA Signed? | BAA Expiration | Renewal Contact | Notes |
|--------|-------------|----------------|-----------------|-------|
| Railway (hosting) | ☐ No | N/A | | Contact: support@railway.app |
| Stripe/Razorpay (payments) | ☐ No | N/A | | Stripe BAA: https://stripe.com/legal/baa<br>Razorpay: Contact support@razorpay.com |
| SendGrid/AWS SES (email) | ☐ No | N/A | | SendGrid BAA: Contact sales@sendgrid.com<br>AWS BAA: Through AWS Business Support |
| Sentry (error tracking) | ☐ No | N/A | | Contact: sales@sentry.io |
| Twilio (SMS) | ☐ No | N/A | | Twilio BAA: https://www.twilio.com/legal/business-associate |

**BAA Tracking Checklist:**
- [ ] Identify all vendors that handle PHI/ePHI
- [ ] Request BAA templates from each vendor
- [ ] Review BAA terms with legal counsel
- [ ] Sign and execute BAAs
- [ ] Store signed BAAs in secure document repository
- [ ] Set calendar reminders for BAA renewals (typically 1-3 years)
- [ ] Update this table with signed status and expiration dates

### Team Roster for Emergency Response

| Role | Primary | Secondary | Backup |
|------|---------|-----------|--------|
| Incident Commander | Michael Chen | Sarah Johnson | John Smith |
| Database Admin | Alex Martinez | Maria Garcia | David Kim |
| Security Lead | Lisa Thompson | Kevin Brown | Amanda Lee |
| Communications Lead | Jennifer Davis | Brian Wilson | Rachel Miller |
| Engineering Lead | David Rodriguez | Michael Chen | Sarah Johnson |

### Escalation Path

1. **On-Call Engineer (0-15 min)**
   - Initial investigation and triage
   - Can escalate if unable to resolve

2. **Engineering Manager (15-30 min)**
   - Resource coordination
   - Cross-team communication
   - Can authorize emergency changes

3. **CTO (30-60 min)**
   - Strategic decisions
   - External communications approval
   - Customer/partner escalation management

4. **CEO (60+ min)**
   - Legal notifications
   - Public statements
   - HIPAA breach reporting authorization

## Post-Incident Review

### Required Documentation

1. **Incident Timeline**
   - When was incident detected?
   - What actions were taken?
   - When was service restored?

2. **Root Cause Analysis**
   - What caused the incident?
   - Why did it happen?
   - How can we prevent it?

3. **Action Items**
   - What needs to be fixed?
   - Who is responsible?
   - What is the timeline?

### Template

```markdown
# Post-Incident Review: [Incident Name]

## Summary
[Brief description of incident]

## Timeline
- HH:MM - Incident detected
- HH:MM - Team notified
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Service restored

## Impact
- Duration: X hours
- Users affected: X
- Data lost: None/Some/All

## Root Cause
[Detailed explanation]

## Resolution
[What was done to fix it]

## Action Items
- [ ] Fix X (Owner: Name, Due: Date)
- [ ] Improve Y (Owner: Name, Due: Date)
- [ ] Update Z (Owner: Name, Due: Date)

## Lessons Learned
[What we learned and how to prevent future incidents]
```

## Appendix

### Useful Commands

```bash
# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('coredent'));"

# Check table sizes
psql $DATABASE_URL -c "SELECT schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"

# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
psql $DATABASE_URL -c "SELECT query, calls, total_time, mean_time 
  FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check Redis memory
redis-cli INFO memory

# Check disk space
df -h

# Check system load
uptime
```

### Recovery Checklist

- [ ] Incident detected and logged
- [ ] Team notified
- [ ] Backup verified
- [ ] Recovery procedure initiated
- [ ] Service restored
- [ ] Health checks passed
- [ ] Users notified
- [ ] Post-incident review scheduled
- [ ] Documentation updated
- [ ] Action items created

# CoreDent Architecture Documentation

## Overview

CoreDent is a HIPAA-compliant dental practice management system built with a modern, scalable architecture.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   React SPA     │  Frontend (TypeScript + React)
│   (Vite + PWA)  │
└────────┬────────┘
         │ HTTPS/REST
         ▼
┌─────────────────┐
│   API Gateway   │  (Future: Kong/Tyk)
│   Rate Limiting │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  Backend (Python 3.11+)
│   Application   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐
│ Redis  │ │ S3   │ │Celery  │ │ Sentry │
│ Cache  │ │Files │ │Workers │ │Monitor │
└────────┘ └──────┘ └────────┘ └────────┘
    │
    ▼
┌─────────────────┐
│   PostgreSQL    │  Database (15+)
│   (Partitioned) │
└─────────────────┘
```

## Backend Architecture

### Layer Structure

```
app/
├── api/              # API Layer (HTTP endpoints)
│   ├── v1/
│   │   └── endpoints/  # Route handlers
│   ├── deps.py       # Dependencies
│   └── service_deps.py # Service injection
│
├── services/         # Business Logic Layer (NEW)
│   ├── base_service.py
│   ├── patient_service.py
│   ├── appointment_service.py
│   ├── billing_service.py
│   ├── insurance_service.py
│   └── audit_service.py
│
├── models/           # Data Layer (SQLAlchemy ORM)
│   ├── patient.py
│   ├── appointment.py
│   └── ...
│
├── schemas/          # Validation Layer (Pydantic)
│   ├── patient.py
│   ├── appointment.py
│   └── ...
│
└── core/             # Infrastructure Layer
    ├── database.py
    ├── security.py
    ├── redis_cache.py  # NEW
    ├── tasks.py        # Celery tasks
    └── ...
```

### Service Layer Pattern

**Purpose:** Separate business logic from HTTP layer

**Benefits:**
- Testable business logic without HTTP overhead
- Reusable across different interfaces (REST, GraphQL, CLI)
- Centralized validation and authorization
- Easier to maintain and refactor

**Example:**

```python
# OLD (Business logic in endpoint)
@router.post("/patients")
async def create_patient(patient: PatientCreate, db: AsyncSession):
    # 50+ lines of validation, business rules, audit logging
    # Hard to test, hard to reuse
    pass

# NEW (Business logic in service)
@router.post("/patients")
async def create_patient(
    patient: PatientCreate,
    service: PatientService = Depends(get_patient_service)
):
    return await service.create_patient(patient, current_user)
```

## Caching Strategy

### Redis Cache Implementation

**Cache Layers:**

1. **Query Cache** (TTL: 5 minutes)
   - Patient lookups
   - Appointment schedules
   - Provider availability

2. **Session Cache** (TTL: 15 minutes)
   - User sessions
   - CSRF tokens

3. **Static Data Cache** (TTL: 1 hour)
   - Procedure codes
   - Insurance carriers
   - Practice settings

**Usage:**

```python
from app.core.redis_cache import cached, invalidate_cache

@cached(ttl=300, key_prefix="patient")
async def get_patient(patient_id: UUID):
    # Expensive database query
    return patient

# Invalidate on update
await invalidate_cache("patient:*")
```

## Database Design

### Partitioning Strategy

**Audit Logs** - Partitioned by month
- Improves query performance
- Enables efficient archival
- Automatic partition creation

```sql
-- Partition structure
audit_logs (parent table)
├── audit_logs_2026_04 (April 2026)
├── audit_logs_2026_05 (May 2026)
└── audit_logs_2026_06 (June 2026)
```

### Indexing Strategy

**Composite Indexes:**
```sql
-- Practice + Status queries
CREATE INDEX idx_patient_practice_status 
ON patients(practice_id, status);

-- Date range queries
CREATE INDEX idx_appointment_provider_date 
ON appointments(provider_id, start_time);
```

## Background Jobs

### Celery Task Queue

**Task Categories:**

1. **Communication Tasks**
   - `send_appointment_reminder` - Email/SMS reminders
   - `send_bulk_email` - Marketing campaigns

2. **Data Processing**
   - `generate_report` - Async report generation
   - `process_insurance_claim` - EDI submission

3. **Maintenance Tasks**
   - `cleanup_old_sessions` - Session cleanup
   - `check_inventory_levels` - Stock alerts
   - `backup_database` - Automated backups

**Scheduling:**
```python
# Periodic tasks (celerybeat)
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Every 5 minutes
    sender.add_periodic_task(300.0, check_inventory_levels.s())
    
    # Daily at 6 AM
    sender.add_periodic_task(
        crontab(hour=6, minute=0),
        backup_database.s()
    )
```

## Security Architecture

### Authentication Flow

```
1. User Login
   ↓
2. Validate Credentials (bcrypt, 14 rounds)
   ↓
3. Generate JWT Access Token (15 min TTL)
   ↓
4. Generate Refresh Token (7 days TTL)
   ↓
5. Store Refresh Token (hashed) in DB
   ↓
6. Return Tokens to Client
   ↓
7. Client stores in memory (NOT localStorage)
```

### Authorization Layers

1. **Route-level** - FastAPI dependencies
2. **Service-level** - Practice isolation
3. **Data-level** - Row-level security

### HIPAA Compliance

**Audit Trail:**
- All PHI access logged
- User, IP, timestamp, action
- Immutable audit logs (partitioned)

**Encryption:**
- In-transit: TLS 1.3
- At-rest: PostgreSQL encryption
- Tokens: SHA-256 hashing

## Performance Optimizations

### Query Optimization

1. **N+1 Prevention**
   ```python
   # Use joinedload for relationships
   query = select(Patient).options(
       joinedload(Patient.insurances)
   )
   ```

2. **Pagination**
   ```python
   # Cursor-based for large datasets
   query = query.where(Patient.id > last_id).limit(100)
   ```

3. **Selective Loading**
   ```python
   # Only load needed columns
   query = select(Patient.id, Patient.name)
   ```

### Caching Strategy

- **Cache-Aside Pattern** - Read-through cache
- **Write-Through** - Invalidate on update
- **TTL-based Expiration** - Automatic cleanup

## Scalability Roadmap

### Current Capacity
- **Users:** 100-500 concurrent
- **Practices:** 50-100
- **Requests:** 1,000 req/min

### Phase 1: Vertical Scaling (0-1K users)
- ✅ Redis caching
- ✅ Database indexing
- ✅ Connection pooling

### Phase 2: Horizontal Scaling (1K-10K users)
- 🔄 Load balancer (Nginx/HAProxy)
- 🔄 Read replicas
- 🔄 CDN for static assets

### Phase 3: Microservices (10K+ users)
- 📋 API Gateway
- 📋 Service mesh
- 📋 Event-driven architecture

## Monitoring & Observability

### Metrics

**Application Metrics:**
- Request rate, latency, errors
- Cache hit/miss ratio
- Database query performance

**Business Metrics:**
- Active users
- Appointments per day
- Revenue per practice

### Logging

**Structured Logging:**
```python
logger.info("patient_created", extra={
    "patient_id": patient.id,
    "practice_id": practice.id,
    "user_id": user.id
})
```

**Log Levels:**
- ERROR: System failures
- WARNING: Security events
- INFO: Business events
- DEBUG: Development only

### Alerting

**Critical Alerts:**
- Database connection failures
- High error rates (>1%)
- Security events (failed logins)

**Warning Alerts:**
- High latency (>2s)
- Cache failures
- Low disk space

## Deployment Architecture

### Environments

1. **Development** - Local Docker
2. **Staging** - Railway/Heroku
3. **Production** - AWS/GCP

### CI/CD Pipeline

```
Code Push
  ↓
Lint & Type Check
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
Build Docker Image
  ↓
Security Scan
  ↓
Deploy to Staging
  ↓
E2E Tests
  ↓
Manual Approval
  ↓
Deploy to Production
  ↓
Health Check
  ↓
Rollback if Failed
```

## Future Enhancements

### Short-term (1-3 months)
- [ ] GraphQL API
- [ ] WebSocket for real-time updates
- [ ] Advanced caching strategies

### Medium-term (3-6 months)
- [ ] API Gateway (Kong/Tyk)
- [ ] Event sourcing
- [ ] Multi-region support

### Long-term (6-12 months)
- [ ] Microservices architecture
- [ ] AI-powered scheduling
- [ ] Mobile app (React Native)

## References

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [HIPAA Compliance Guide](https://www.hhs.gov/hipaa/)
- [PostgreSQL Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)

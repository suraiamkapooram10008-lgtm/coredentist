# Performance Profiling & Optimization Plan

**Priority**: MEDIUM  
**Estimated Effort**: 2-3 weeks  
**Status**: ⏳ **PENDING**

---

## 🎯 Why Performance Profiling?

### Business Impact
1. **User Experience**: Faster response times = happier users
2. **Scalability**: Identify bottlenecks before they become problems
3. **Cost Optimization**: Reduce infrastructure costs
4. **Competitive Advantage**: Faster than competitors

### Technical Goals
1. **Response Time**: < 300ms for 95th percentile
2. **Throughput**: Handle 100+ concurrent users
3. **Database**: Optimize slow queries
4. **Memory**: Prevent memory leaks
5. **CPU**: Identify CPU-intensive operations

---

## 📊 Current Performance Baseline

### Known Metrics
- **Target Response Time**: < 500ms (beta), < 300ms (production)
- **Target Uptime**: 99%+ (beta), 99.9% (production)
- **Target Error Rate**: < 1% (beta), < 0.1% (production)

### Unknown Metrics (Need to Measure)
- ⏳ Actual response times under load
- ⏳ Database query performance
- ⏳ Memory usage patterns
- ⏳ CPU utilization
- ⏳ Concurrent user capacity

---

## 🔧 Performance Profiling Tools

### 1. Application Performance Monitoring (APM)

**Recommended: New Relic or DataDog**

**Setup**:
```bash
# Install New Relic
pip install newrelic

# Configure
newrelic-admin generate-config YOUR_LICENSE_KEY newrelic.ini

# Run with New Relic
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn app.main:app
```

**Metrics to Track**:
- Request/response times
- Database query times
- External API calls
- Error rates
- Throughput (requests/second)

### 2. Database Query Profiling

**Tool: PostgreSQL EXPLAIN ANALYZE**

**Setup**:
```python
# Add to app/core/database.py
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger.debug("Start Query: %s", statement)

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.1:  # Log slow queries (> 100ms)
        logger.warning("Slow Query (%.2fs): %s", total, statement)
```

### 3. Load Testing

**Tool: Locust**

**Setup**:
```bash
pip install locust
```

**Create `locustfile.py`**:
```python
from locust import HttpUser, task, between

class CoreDentUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_patients(self):
        self.client.get("/api/v1/patients", headers=self.headers)
    
    @task(2)
    def list_appointments(self):
        self.client.get("/api/v1/appointments", headers=self.headers)
    
    @task(1)
    def create_appointment(self):
        self.client.post("/api/v1/appointments", headers=self.headers, json={
            "patient_id": "test-patient-id",
            "provider_id": "test-provider-id",
            "start_time": "2026-06-01T10:00:00",
            "end_time": "2026-06-01T11:00:00",
            "appointment_type": "cleaning"
        })
```

**Run Load Test**:
```bash
locust -f locustfile.py --host=https://api.coredent.com
```

### 4. Memory Profiling

**Tool: memory_profiler**

**Setup**:
```bash
pip install memory_profiler
```

**Usage**:
```python
from memory_profiler import profile

@profile
def expensive_function():
    # Function to profile
    pass
```

### 5. CPU Profiling

**Tool: py-spy**

**Setup**:
```bash
pip install py-spy
```

**Usage**:
```bash
# Profile running application
py-spy top --pid <PID>

# Generate flame graph
py-spy record -o profile.svg --pid <PID>
```

---

## 📋 Performance Profiling Checklist

### Week 1: Setup & Baseline

#### Day 1-2: Install APM
- [ ] Sign up for New Relic or DataDog
- [ ] Install APM agent
- [ ] Configure APM in production
- [ ] Verify metrics are being collected
- [ ] Set up dashboards

#### Day 3-4: Database Profiling
- [ ] Enable query logging
- [ ] Identify slow queries (> 100ms)
- [ ] Run EXPLAIN ANALYZE on slow queries
- [ ] Document query performance baseline

#### Day 5: Load Testing Setup
- [ ] Install Locust
- [ ] Create load test scenarios
- [ ] Run baseline load test (10 users)
- [ ] Document baseline metrics

### Week 2: Identify Bottlenecks

#### Day 6-7: API Endpoint Analysis
- [ ] Profile all API endpoints
- [ ] Identify slowest endpoints
- [ ] Measure database query times
- [ ] Measure external API call times
- [ ] Document findings

#### Day 8-9: Database Optimization
- [ ] Identify missing indexes
- [ ] Analyze query plans
- [ ] Identify N+1 query problems
- [ ] Document optimization opportunities

#### Day 10: Memory & CPU Analysis
- [ ] Profile memory usage
- [ ] Identify memory leaks
- [ ] Profile CPU usage
- [ ] Identify CPU hotspots

### Week 3: Optimization & Verification

#### Day 11-13: Implement Optimizations
- [ ] Add missing database indexes
- [ ] Optimize slow queries
- [ ] Implement caching where appropriate
- [ ] Fix N+1 query problems
- [ ] Optimize CPU-intensive operations

#### Day 14-15: Verification
- [ ] Re-run load tests
- [ ] Compare before/after metrics
- [ ] Verify improvements
- [ ] Document results

---

## 🎯 Optimization Strategies

### 1. Database Optimization

**Add Indexes**:
```sql
-- Identify missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;

-- Add indexes for common queries
CREATE INDEX idx_appointments_patient_date ON appointments(patient_id, start_time);
CREATE INDEX idx_appointments_provider_date ON appointments(provider_id, start_time);
CREATE INDEX idx_patients_practice_status ON patients(practice_id, status);
CREATE INDEX idx_invoices_patient_status ON invoices(patient_id, status);
```

**Optimize Queries**:
```python
# BAD: N+1 query problem
patients = await db.execute(select(Patient))
for patient in patients:
    appointments = await db.execute(
        select(Appointment).where(Appointment.patient_id == patient.id)
    )

# GOOD: Use joinedload
from sqlalchemy.orm import joinedload

patients = await db.execute(
    select(Patient).options(joinedload(Patient.appointments))
)
```

### 2. Caching Strategy

**Implement Redis Caching**:
```python
from app.core.redis_cache import cache_get, cache_set

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db)):
    # Try cache first
    cached = await cache_get(f"patient:{patient_id}")
    if cached:
        return cached
    
    # Query database
    patient = await db.get(Patient, patient_id)
    
    # Cache result
    await cache_set(f"patient:{patient_id}", patient.dict(), expire=300)
    
    return patient
```

**Cache Invalidation**:
```python
@router.put("/patients/{patient_id}")
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db)
):
    patient = await db.get(Patient, patient_id)
    # Update patient...
    await db.commit()
    
    # Invalidate cache
    await cache_delete(f"patient:{patient_id}")
    
    return patient
```

### 3. API Response Optimization

**Pagination**:
```python
@router.get("/patients")
async def list_patients(
    skip: int = 0,
    limit: int = 20,  # Default page size
    db: AsyncSession = Depends(get_db)
):
    patients = await db.execute(
        select(Patient).offset(skip).limit(limit)
    )
    return patients.scalars().all()
```

**Field Selection**:
```python
@router.get("/patients")
async def list_patients(
    fields: Optional[str] = None,  # e.g., "id,name,email"
    db: AsyncSession = Depends(get_db)
):
    if fields:
        selected_fields = [getattr(Patient, f) for f in fields.split(',')]
        query = select(*selected_fields)
    else:
        query = select(Patient)
    
    patients = await db.execute(query)
    return patients.all()
```

### 4. Async Optimization

**Parallel Queries**:
```python
import asyncio

# BAD: Sequential queries
patient = await db.get(Patient, patient_id)
appointments = await db.execute(
    select(Appointment).where(Appointment.patient_id == patient_id)
)
invoices = await db.execute(
    select(Invoice).where(Invoice.patient_id == patient_id)
)

# GOOD: Parallel queries
patient_task = db.get(Patient, patient_id)
appointments_task = db.execute(
    select(Appointment).where(Appointment.patient_id == patient_id)
)
invoices_task = db.execute(
    select(Invoice).where(Invoice.patient_id == patient_id)
)

patient, appointments, invoices = await asyncio.gather(
    patient_task, appointments_task, invoices_task
)
```

### 5. Frontend Optimization

**Code Splitting**:
```typescript
// Lazy load routes
const Patients = lazy(() => import('./pages/Patients'));
const Appointments = lazy(() => import('./pages/Appointments'));
```

**Image Optimization**:
```typescript
// Use WebP format
// Lazy load images
// Implement image CDN
```

**Bundle Size Reduction**:
```bash
# Analyze bundle
npm run build -- --analyze

# Remove unused dependencies
npm prune

# Use tree-shaking
```

---

## 📊 Performance Targets

### API Response Times
| Endpoint | Current | Target | Optimized |
|----------|---------|--------|-----------|
| GET /patients | ? | < 200ms | ? |
| GET /appointments | ? | < 200ms | ? |
| POST /appointments | ? | < 300ms | ? |
| GET /invoices | ? | < 200ms | ? |
| POST /invoices | ? | < 300ms | ? |

### Database Queries
| Query | Current | Target | Optimized |
|-------|---------|--------|-----------|
| List patients | ? | < 50ms | ? |
| List appointments | ? | < 50ms | ? |
| Patient details | ? | < 20ms | ? |
| Appointment details | ? | < 20ms | ? |

### Load Testing
| Metric | Current | Target | Optimized |
|--------|---------|--------|-----------|
| Concurrent Users | ? | 100+ | ? |
| Requests/Second | ? | 500+ | ? |
| Error Rate | ? | < 0.1% | ? |
| 95th Percentile | ? | < 300ms | ? |

---

## 🚀 Quick Wins (Implement First)

### 1. Add Database Indexes (1 day)
```sql
-- High-impact indexes
CREATE INDEX CONCURRENTLY idx_appointments_patient_date ON appointments(patient_id, start_time);
CREATE INDEX CONCURRENTLY idx_appointments_provider_date ON appointments(provider_id, start_time);
CREATE INDEX CONCURRENTLY idx_patients_practice_status ON patients(practice_id, status);
```

### 2. Enable Query Caching (1 day)
```python
# Cache frequently accessed data
- Patient details (5 min TTL)
- Appointment lists (1 min TTL)
- Practice settings (15 min TTL)
```

### 3. Implement Pagination (1 day)
```python
# Add pagination to all list endpoints
- Default page size: 20
- Max page size: 100
```

### 4. Optimize N+1 Queries (2 days)
```python
# Use joinedload for relationships
- Patient → Appointments
- Appointment → Patient, Provider
- Invoice → Patient, LineItems
```

---

## 📈 Monitoring Dashboard

### Key Metrics to Track
1. **Response Time**: P50, P95, P99
2. **Throughput**: Requests/second
3. **Error Rate**: 4xx, 5xx errors
4. **Database**: Query time, connection pool
5. **Memory**: Usage, leaks
6. **CPU**: Utilization, hotspots

### Alerts to Configure
- Response time > 1s
- Error rate > 1%
- Database connections > 80%
- Memory usage > 80%
- CPU usage > 80%

---

## ✅ Success Criteria

- [ ] APM installed and collecting metrics
- [ ] Baseline performance documented
- [ ] Slow queries identified and optimized
- [ ] Missing indexes added
- [ ] Caching implemented
- [ ] Load test passing (100+ concurrent users)
- [ ] 95th percentile < 300ms
- [ ] Error rate < 0.1%
- [ ] Performance improvements documented

---

## 📚 Resources

- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/faq/performance.html)
- [Locust Documentation](https://docs.locust.io/)
- [New Relic APM](https://docs.newrelic.com/docs/apm/)

---

**Status**: ⏳ **PENDING**  
**Priority**: MEDIUM  
**Estimated Completion**: 2-3 weeks  
**Blocker For**: Scaling to 100+ practices


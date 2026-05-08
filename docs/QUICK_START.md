# CoreDent Quick Start Guide

## For New Developers

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/coredent/api.git
cd coredent-api

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 5. Start PostgreSQL and Redis
docker-compose up -d postgres redis

# 6. Run migrations
alembic upgrade head

# 7. Create test data
python scripts/seed_database.py

# 8. Start development server
uvicorn app.main:app --reload --port 3000
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd coredent-style-main

# 2. Install dependencies
npm install

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Start development server
npm run dev
```

### Access Points

- **API:** http://localhost:3000
- **API Docs:** http://localhost:3000/docs
- **Frontend:** http://localhost:5173
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## Architecture Overview

### Service Layer Pattern

```python
# Services handle business logic
from app.services import PatientService

# Endpoints are thin wrappers
@router.post("/patients")
async def create_patient(
    patient: PatientCreate,
    service: PatientService = Depends(get_patient_service)
):
    return await service.create_patient(patient, current_user)
```

### Caching Pattern

```python
# Use decorator for caching
from app.core.redis_cache import cached

@cached(ttl=300, key_prefix="patient")
async def get_patient(patient_id: UUID):
    return await db.query(Patient).get(patient_id)

# Invalidate cache on update
from app.core.redis_cache import invalidate_cache
await invalidate_cache("patient:*")
```

### Background Jobs

```python
# Queue background tasks
from app.core.tasks import send_appointment_reminder

send_appointment_reminder.delay(appointment_id, channel="email")
```

## Common Tasks

### Running Tests

```bash
# Backend tests
cd coredent-api
pytest --cov=app --cov-report=html

# Frontend tests
cd coredent-style-main
npm run test
npm run test:e2e
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Backend
black app/
isort app/
flake8 app/
mypy app/

# Frontend
npm run lint
npm run format
npm run typecheck
```

## Debugging

### Backend Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use debugpy for VS Code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### Frontend Debugging

```typescript
// Use React DevTools
// Add debugger statement
debugger;

// Console logging
console.log('Debug:', data);
```

### Database Debugging

```bash
# Connect to database
psql $DATABASE_URL

# Check slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

# Check table sizes
SELECT schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
LIMIT 10;
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

#### 2. Redis Connection Error

```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli ping

# Check Redis URL
echo $REDIS_URL
```

#### 3. Migration Fails

```bash
# Check current version
alembic current

# Check pending migrations
alembic heads

# Reset to specific version
alembic downgrade <revision>
alembic upgrade head
```

#### 4. Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.11+
```

## Best Practices

### Code Style

- Follow PEP 8 for Python
- Use type hints everywhere
- Write docstrings for all functions
- Keep functions small (<50 lines)
- Use meaningful variable names

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

### Commit Messages

```
feat: add new feature
fix: fix bug
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: update dependencies
```

### Testing

- Write tests for all new features
- Aim for 70%+ coverage
- Test edge cases
- Use fixtures for test data
- Mock external services

### Security

- Never commit secrets
- Use environment variables
- Validate all inputs
- Sanitize user data
- Log security events

## Resources

### Documentation

- [Architecture](./ARCHITECTURE.md)
- [Deployment Runbook](./DEPLOYMENT_RUNBOOK.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)
- [API Documentation](http://localhost:3000/docs)

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Team Communication

- Slack: #engineering
- Email: engineering@coredent.com
- Wiki: https://wiki.coredent.com

## Getting Help

1. Check documentation
2. Search existing issues
3. Ask in #engineering Slack
4. Create GitHub issue
5. Contact team lead

## Next Steps

1. Read [Architecture Documentation](./ARCHITECTURE.md)
2. Complete onboarding tasks
3. Pick up first issue
4. Submit first PR
5. Attend team standup

Welcome to the team! 🎉

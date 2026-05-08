# Test Execution Troubleshooting Guide

**Issue**: Test suite timing out or running very slowly  
**Date**: May 4, 2026

---

## 🔍 Problem Description

The test suite is experiencing performance issues:
- Tests timing out after 60-180 seconds
- Cannot complete full test run
- Some tests passing, some failing
- 164 tests collected but not all executing

---

## 🎯 Quick Diagnosis

### Step 1: Check Database Connection
```bash
cd coredent-api

# Test database connection
python -c "from app.core.database import engine; print('Database URL:', engine.url)"

# Check if test database exists
python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('Connection successful')"
```

**Expected**: Should connect without errors

### Step 2: Run Single Test
```bash
# Run one simple test
pytest tests/test_auth.py::TestAuthEndpoints::test_login_invalid_credentials -v

# If that works, try a test that's failing
pytest tests/test_auth.py::TestAuthEndpoints::test_login_success -v
```

**Expected**: Should complete in < 5 seconds

### Step 3: Check Test Configuration
```bash
# View pytest configuration
cat pytest.ini

# Check conftest.py for issues
cat tests/conftest.py
```

---

## 🔧 Common Causes & Solutions

### Cause 1: Database Connection Issues

**Symptoms**:
- Tests hang indefinitely
- No error messages
- Database queries not completing

**Solution**:
```bash
# Use in-memory SQLite for tests
export DATABASE_URL="sqlite:///./test.db"
pytest tests/ -v

# Or use test-specific database
export DATABASE_URL="postgresql://user:pass@localhost/coredent_test"
pytest tests/ -v
```

**Fix in conftest.py**:
```python
# Add to conftest.py
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
```

---

### Cause 2: Async Test Configuration

**Symptoms**:
- Tests hang on async operations
- Event loop errors
- Timeout on API calls

**Solution**:
```bash
# Check asyncio mode
pytest tests/ -v --asyncio-mode=auto

# Or try strict mode
pytest tests/ -v --asyncio-mode=strict
```

**Fix in pytest.ini**:
```ini
[pytest]
asyncio_mode = auto
timeout = 30
```

---

### Cause 3: Fixture Cleanup Issues

**Symptoms**:
- Tests slow down over time
- Database locks
- Resource leaks

**Solution**:
```python
# Add to conftest.py
@pytest.fixture(autouse=True)
async def cleanup_db(db_session):
    """Clean up database after each test"""
    yield
    await db_session.rollback()
    await db_session.close()
```

---

### Cause 4: External Service Calls

**Symptoms**:
- Tests waiting for network responses
- Timeout on email/SMS/API calls
- Slow tests for external integrations

**Solution**:
```python
# Mock external services in conftest.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock all external service calls"""
    with patch('app.core.email.send_email', new_callable=AsyncMock) as mock_email, \
         patch('app.core.sms.send_sms', new_callable=AsyncMock) as mock_sms, \
         patch('app.core.s3_storage.upload_file', new_callable=AsyncMock) as mock_s3:
        
        mock_email.return_value = True
        mock_sms.return_value = True
        mock_s3.return_value = "https://example.com/file.pdf"
        
        yield {
            'email': mock_email,
            'sms': mock_sms,
            's3': mock_s3
        }
```

---

### Cause 5: Redis Connection Issues

**Symptoms**:
- Tests hang on cache operations
- Redis connection timeouts
- Rate limiting tests slow

**Solution**:
```python
# Mock Redis in conftest.py
@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis for tests"""
    with patch('app.core.redis_cache.redis_client') as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        yield mock
```

---

## 🚀 Recommended Test Configuration

### Updated `conftest.py`
```python
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock all external services"""
    with patch('app.core.email.send_email', new_callable=AsyncMock) as mock_email, \
         patch('app.core.sms.send_sms', new_callable=AsyncMock) as mock_sms, \
         patch('app.core.s3_storage.upload_file', new_callable=AsyncMock) as mock_s3:
        
        mock_email.return_value = True
        mock_sms.return_value = True
        mock_s3.return_value = "https://example.com/file.pdf"
        
        yield

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis"""
    with patch('app.core.redis_cache.redis_client') as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        yield mock
```

### Updated `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
timeout = 30
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

---

## 🧪 Testing Strategy

### 1. Run Tests in Stages

**Stage 1: Unit Tests (Fast)**
```bash
# Run only unit tests
pytest tests/ -m unit -v

# Should complete in < 1 minute
```

**Stage 2: Integration Tests (Slower)**
```bash
# Run integration tests
pytest tests/ -m integration -v

# Should complete in < 5 minutes
```

**Stage 3: Full Suite**
```bash
# Run all tests
pytest tests/ -v

# Should complete in < 10 minutes
```

### 2. Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/ -n auto

# Should be 2-4x faster
```

### 3. Incremental Testing

```bash
# Run only failed tests from last run
pytest tests/ --lf

# Run failed tests first, then others
pytest tests/ --ff
```

---

## 📊 Performance Benchmarks

### Expected Test Times

| Test Type | Count | Time | Per Test |
|-----------|-------|------|----------|
| Unit | 100 | 30s | 0.3s |
| Integration | 50 | 2min | 2.4s |
| E2E | 14 | 3min | 12.8s |
| **Total** | **164** | **5-6min** | **2-2.2s** |

### Current Performance Issues

| Issue | Impact | Priority |
|-------|--------|----------|
| Database connections | Tests hang | HIGH |
| External service calls | 10-30s timeout | HIGH |
| Fixture overhead | Slow setup | MEDIUM |
| No parallel execution | 2-4x slower | MEDIUM |

---

## ✅ Verification Steps

### After Applying Fixes

1. **Run Single Test**
```bash
pytest tests/test_auth.py::TestAuthEndpoints::test_login_invalid_credentials -v
# Expected: < 5 seconds
```

2. **Run Test File**
```bash
pytest tests/test_auth.py -v
# Expected: < 30 seconds for 17 tests
```

3. **Run Full Suite**
```bash
pytest tests/ -v
# Expected: < 10 minutes for 164 tests
```

4. **Check Coverage**
```bash
pytest tests/ --cov=app --cov-report=term
# Expected: 68%+ coverage
```

---

## 🔄 Iterative Debugging Process

### Step-by-Step Approach

1. **Isolate the Problem**
   - Run one test at a time
   - Identify which tests hang
   - Check for common patterns

2. **Add Timeouts**
   ```bash
   pytest tests/ -v --timeout=10
   ```
   - Tests that timeout are the problem
   - Focus on those first

3. **Add Debug Output**
   ```python
   # Add to test
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. **Check Database State**
   ```python
   # Add to test
   print(f"DB Session: {db_session}")
   print(f"DB Engine: {db_session.bind}")
   ```

5. **Mock Everything**
   - Start with all external services mocked
   - Gradually unmock to find the issue

---

## 📝 Next Steps

### Immediate Actions (Today)
1. [ ] Update `conftest.py` with recommended configuration
2. [ ] Update `pytest.ini` with timeout settings
3. [ ] Run single test to verify fixes
4. [ ] Run full suite to get coverage numbers

### Short-Term Actions (This Week)
1. [ ] Fix all failing tests
2. [ ] Optimize slow tests
3. [ ] Add parallel execution
4. [ ] Document test patterns

### Long-Term Actions (Next Month)
1. [ ] Add CI/CD test automation
2. [ ] Set up test coverage monitoring
3. [ ] Add performance benchmarks
4. [ ] Create test maintenance guide

---

## 🆘 If Still Having Issues

### Option 1: Skip Slow Tests Temporarily
```bash
# Mark slow tests
@pytest.mark.slow
def test_slow_operation():
    pass

# Run without slow tests
pytest tests/ -m "not slow" --cov=app
```

### Option 2: Use Docker for Tests
```bash
# Run tests in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Ensures clean environment
```

### Option 3: Simplify Test Database
```python
# Use in-memory SQLite
DATABASE_URL = "sqlite:///:memory:"

# Fastest option, but may have compatibility issues
```

---

## 📞 Support Resources

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy async](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)

### Common Commands
```bash
# Show test collection
pytest tests/ --collect-only

# Show fixtures
pytest tests/ --fixtures

# Show markers
pytest tests/ --markers

# Verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x
```

---

**Status**: 🔧 **Troubleshooting in Progress**  
**Priority**: HIGH  
**Estimated Fix Time**: 1-2 days


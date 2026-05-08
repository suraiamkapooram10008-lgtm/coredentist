# Quick Reference - Coverage Sprint

**Current**: 56.50% | **Target**: 68.00% | **Gap**: +11.5%

---

## 🚀 QUICK START (Copy & Paste)

### Create Test Directory
```bash
cd coredent-api
mkdir -p tests/test_services
```

### Run Current Coverage
```bash
pytest tests/ --cov=app --cov-report=term | grep "TOTAL"
```

### Run Specific Test with Coverage
```bash
pytest tests/test_services/test_appointment_service.py --cov=app.services.appointment_service --cov-report=term-missing -v
```

### Run All Tests
```bash
pytest tests/ -v --tb=short
```

### Generate HTML Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html
start htmlcov/index.html  # Windows
```

---

## 📋 3-DAY SPRINT CHECKLIST

### Day 1 (6 hours) - Core Services
- [ ] Create `tests/test_services/test_appointment_service.py` (2h)
  - [ ] test_create_appointment_with_duration
  - [ ] test_check_appointment_conflicts
  - [ ] test_get_available_slots
  - [ ] test_send_appointment_reminder
  - [ ] Run: `pytest tests/test_services/test_appointment_service.py -v`
  - [ ] Check coverage: Should be ~59.5%

- [ ] Create `tests/test_services/test_payment_processing.py` (2h)
  - [ ] test_process_credit_card_payment
  - [ ] test_process_ach_payment
  - [ ] test_handle_payment_failure
  - [ ] test_reconcile_payments
  - [ ] test_generate_payment_receipt
  - [ ] Run: `pytest tests/test_services/test_payment_processing.py -v`
  - [ ] Check coverage: Should be ~62.5%

- [ ] Create `tests/test_services/test_patient_service.py` (2h)
  - [ ] test_search_patients
  - [ ] test_merge_duplicate_patients
  - [ ] test_validate_patient_data
  - [ ] test_get_patient_history
  - [ ] Run: `pytest tests/test_services/test_patient_service.py -v`
  - [ ] Check coverage: Should be ~64.5%

**End of Day 1**: Run `pytest tests/ --cov=app --cov-report=term | grep "TOTAL"`  
**Expected**: ~64.5% coverage

---

### Day 2 (6 hours) - Business Services
- [ ] Create `tests/test_services/test_subscription_service.py` (3h)
  - [ ] test_create_subscription
  - [ ] test_cancel_subscription
  - [ ] test_upgrade_subscription
  - [ ] test_calculate_prorated_amount
  - [ ] test_handle_subscription_renewal
  - [ ] test_subscription_payment_failed
  - [ ] Run: `pytest tests/test_services/test_subscription_service.py -v`
  - [ ] Check coverage: Should be ~67.5%

- [ ] Create `tests/test_services/test_booking_service.py` (3h)
  - [ ] test_validate_booking_availability
  - [ ] test_create_online_booking
  - [ ] test_send_booking_confirmation
  - [ ] test_handle_booking_cancellation
  - [ ] Run: `pytest tests/test_services/test_booking_service.py -v`
  - [ ] Check coverage: Should be ~69.5%

**End of Day 2**: Run `pytest tests/ --cov=app --cov-report=term | grep "TOTAL"`  
**Expected**: ~69.5% coverage

---

### Day 3 (4 hours) - Communication Services
- [ ] Create `tests/test_services/test_insurance_service.py` (2h)
  - [ ] test_verify_insurance_eligibility
  - [ ] test_submit_insurance_claim
  - [ ] test_process_claim_response
  - [ ] test_calculate_patient_responsibility
  - [ ] Run: `pytest tests/test_services/test_insurance_service.py -v`
  - [ ] Check coverage: Should be ~71.5%

- [ ] Create `tests/test_services/test_communications_service.py` (2h)
  - [ ] test_send_email_notification
  - [ ] test_send_sms_notification
  - [ ] test_send_appointment_reminder
  - [ ] test_handle_communication_failure
  - [ ] Run: `pytest tests/test_services/test_communications_service.py -v`
  - [ ] Check coverage: Should be ~73.5%

**End of Day 3**: Run `pytest tests/ --cov=app --cov-report=term | grep "TOTAL"`  
**Expected**: ~73.5% coverage ✅

---

## 📊 COVERAGE CHECKPOINTS

### After Each Test File
```bash
# Check specific service coverage
pytest tests/test_services/test_X_service.py --cov=app.services.X_service --cov-report=term-missing

# Check overall coverage
pytest tests/ --cov=app --cov-report=term | grep "TOTAL"
```

### Expected Progress
```
Start:      56.50%
After Day 1: 64.50% (+8%)
After Day 2: 69.50% (+5%)
After Day 3: 73.50% (+4%)
Target:     68.00% ✅
```

---

## 🎯 TEST TEMPLATE

### Basic Service Test Template
```python
import pytest
from app.services.X_service import XService

class TestXService:
    @pytest.mark.asyncio
    async def test_operation_name(self, db_session, test_user):
        """Test description"""
        # Arrange
        service = XService(db_session)
        
        # Act
        result = await service.operation(params)
        
        # Assert
        assert result is not None
        assert result.field == expected_value
```

### With Mock External Service
```python
import pytest
from unittest.mock import Mock, patch
from app.services.X_service import XService

class TestXService:
    @pytest.mark.asyncio
    async def test_with_external_service(self, db_session, test_user):
        """Test with mocked external service"""
        # Arrange
        service = XService(db_session)
        
        with patch('app.services.X_service.external_api') as mock_api:
            mock_api.call.return_value = {"status": "success"}
            
            # Act
            result = await service.operation(params)
            
            # Assert
            assert result.status == "success"
            mock_api.call.assert_called_once()
```

---

## 🔍 DEBUGGING TIPS

### Test Fails?
```bash
# Run with verbose output
pytest tests/test_services/test_X.py -v -s

# Run with full traceback
pytest tests/test_services/test_X.py --tb=long

# Run single test
pytest tests/test_services/test_X.py::TestClass::test_method -v
```

### Coverage Not Increasing?
```bash
# Check what lines are missing
pytest tests/test_services/test_X.py --cov=app.services.X --cov-report=term-missing

# Generate HTML report for visual inspection
pytest tests/test_services/test_X.py --cov=app.services.X --cov-report=html
start htmlcov/index.html
```

### Import Errors?
```bash
# Check if service exists
ls app/services/X_service.py

# Check if __init__.py exists
ls app/services/__init__.py

# Try importing in Python
python -c "from app.services.X_service import XService; print('OK')"
```

---

## 📈 PROGRESS TRACKING

### Daily Status Update Template
```markdown
## Day X Progress - [Date]

**Hours Worked**: X hours
**Tests Added**: X tests
**Coverage Before**: X%
**Coverage After**: X%
**Coverage Gain**: +X%

### Completed
- [x] test_X
- [x] test_Y
- [x] test_Z

### Issues
- Issue 1: [Description] - [Resolution]
- Issue 2: [Description] - [Resolution]

### Next Steps
- [ ] Task 1
- [ ] Task 2
```

---

## 🎯 SUCCESS CRITERIA

### Must Have
- [ ] Overall coverage ≥ 68%
- [ ] Service layer coverage ≥ 60%
- [ ] All new tests passing
- [ ] No regressions in existing tests

### Should Have
- [ ] Service layer coverage ≥ 70%
- [ ] All tests passing (no failures)
- [ ] Fast execution (<10 minutes)
- [ ] Clear test names

### Could Have
- [ ] Integration tests
- [ ] Edge case tests
- [ ] Performance tests
- [ ] Documentation updated

---

## 🚨 COMMON ISSUES & SOLUTIONS

### Issue: "Event loop is closed" error
**Solution**: Ignore if tests pass, it's a teardown issue

### Issue: "MFA not enabled" 403 error
**Solution**: Check test_user fixture has `mfa_enabled=True`

### Issue: "Decimal is not JSON serializable"
**Solution**: Already fixed in main.py with DecimalJSONResponse

### Issue: Tests pass but coverage doesn't increase
**Solution**: Make sure you're testing the actual service logic, not just mocks

### Issue: Import errors
**Solution**: Check PYTHONPATH and make sure you're in coredent-api directory

---

## 📞 HELP & RESOURCES

### Documentation
- `ACTION_PLAN_TO_68_PERCENT.md` - Detailed 7-day plan
- `COVERAGE_ROADMAP.md` - Visual roadmap
- `CURRENT_STATUS_MAY_5_2026.md` - Current status
- `WHATS_REMAINING.md` - What's left to do
- `EXECUTIVE_SUMMARY_MAY_5_2026.md` - Executive summary

### Key Files
- `tests/conftest.py` - Test fixtures
- `app/services/` - Services to test
- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage configuration

### Commands Reference
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term

# Run specific test file
pytest tests/test_services/test_X.py -v

# Run specific test
pytest tests/test_services/test_X.py::TestClass::test_method -v

# Generate HTML report
pytest tests/ --cov=app --cov-report=html

# Run in parallel (faster)
pytest tests/ -n auto --cov=app
```

---

**Status**: 📋 READY TO START  
**Next Action**: Create `tests/test_services/test_appointment_service.py`  
**Expected Time**: 2 hours  
**Expected Impact**: +3% coverage  

**YOU GOT THIS! 💪**

# Next Steps - Action Plan to 68% Coverage
**Date**: May 5, 2026  
**Current Coverage**: 57.27%  
**Target Coverage**: 68%  
**Gap**: 10.73% (~1,235 lines)  
**Estimated Effort**: 72 hours (2 weeks)

---

## 🎯 EXECUTIVE SUMMARY

### Current Situation
- ✅ **Core modules working**: Auth, Patients, Billing, Appointments (100% test pass rate)
- ⚠️ **Service layer failing**: 78 failures + 22 errors in service tests
- ❌ **Coverage below target**: 57.27% vs 68% target
- ✅ **Recent wins**: Billing module complete, Decimal bug fixed, 128 new tests added

### The Plan
**2-week sprint** to reach 68% coverage:
- **Week 1**: Fix failing tests + add core service tests → 62-63% coverage
- **Week 2**: Add secondary service tests + integration tests → 68%+ coverage

---

## 📊 WEEK 1: FIX & STABILIZE (40 hours)

### Goal: 62-63% Coverage
**Focus**: Fix all failing tests, stabilize service layer, add core service tests

---

### DAY 1: Fix Booking Service Tests (8 hours)

#### Morning (4 hours): Debug Failing Tests
**Failing Tests**:
- `test_add_to_waitlist`
- `test_list_bookings`
- `test_get_booking_stats`

**Tasks**:
1. Read `app/services/booking_service.py` (if exists)
2. Read `tests/test_services/test_booking_service.py`
3. Identify root causes:
   - Missing service methods?
   - Incorrect mocks?
   - Database state issues?
4. Fix service implementations
5. Update test fixtures if needed

**Expected Result**: 3 booking tests passing

#### Afternoon (4 hours): Add Missing Booking Tests
**Tasks**:
1. Add tests for uncovered booking service methods
2. Add edge case tests (invalid data, not found, etc.)
3. Add error handling tests
4. Run coverage report for booking service

**Expected Result**: Booking service coverage 34% → 50%

---

### DAY 2: Fix Payment Processing Tests (8 hours)

#### Morning (4 hours): Fix Webhook Tests
**Failing Tests**:
- `test_verify_stripe_signature_valid`
- `test_verify_stripe_signature_invalid`
- `test_verify_razorpay_signature_valid`
- `test_verify_razorpay_signature_invalid`

**Tasks**:
1. Read `app/services/payment_processing.py`
2. Read `tests/test_services/test_payment_processing.py`
3. Add proper Stripe/Razorpay mocks
4. Fix webhook signature verification logic
5. Update test fixtures

**Expected Result**: 4 webhook tests passing

#### Afternoon (4 hours): Fix Stripe Payment Tests
**Failing/Error Tests** (10 tests):
- `test_create_payment_intent_success`
- `test_create_payment_intent_failure`
- `test_handle_payment_succeeded`
- `test_handle_payment_failed`
- `test_process_refund_success`
- `test_payment_exceeds_balance`
- And 4 more...

**Tasks**:
1. Add Stripe API mocks
2. Fix service implementations
3. Add proper error handling
4. Update test fixtures

**Expected Result**: 10 Stripe tests passing

---

### DAY 3: Fix Subscription Service Tests (8 hours)

#### Morning (4 hours): Debug 22 Errors
**Error Tests** (22 total):
- Subscription service errors (12)
- Subscription enhanced errors (4)
- Payment processing errors (6)

**Tasks**:
1. Read error messages carefully
2. Identify common patterns
3. Fix service implementations
4. Add missing dependencies
5. Update fixtures

**Expected Result**: 0 errors, tests either pass or fail cleanly

#### Afternoon (4 hours): Fix Subscription Tests
**Tasks**:
1. Fix subscription lifecycle tests
2. Fix proration calculation tests
3. Fix usage tracking tests
4. Add proper Stripe subscription mocks

**Expected Result**: 12+ subscription tests passing

---

### DAY 4: Add Core Service Tests (8 hours)

#### Morning (4 hours): Appointment Service Tests
**Current Coverage**: 25%  
**Target**: 50%

**Tests to Add**:
```python
# tests/test_services/test_appointment_service.py

async def test_check_provider_availability():
    """Test provider availability checking"""
    
async def test_calculate_appointment_duration():
    """Test duration calculation for different appointment types"""
    
async def test_detect_appointment_conflicts():
    """Test conflict detection logic"""
    
async def test_send_appointment_reminders():
    """Test reminder sending logic"""
    
async def test_handle_appointment_cancellation():
    """Test cancellation workflow"""
```

**Expected Result**: Appointment service 25% → 50%

#### Afternoon (4 hours): Patient Service Tests
**Current Coverage**: 29%  
**Target**: 50%

**Tests to Add**:
```python
# tests/test_services/test_patient_service.py

async def test_search_patients_by_name():
    """Test patient search by name"""
    
async def test_search_patients_by_phone():
    """Test patient search by phone"""
    
async def test_merge_duplicate_patients():
    """Test patient merge logic"""
    
async def test_validate_patient_data():
    """Test data validation"""
    
async def test_get_patient_history():
    """Test history retrieval"""
```

**Expected Result**: Patient service 29% → 50%

---

### DAY 5: Add Endpoint Tests (8 hours)

#### Morning (4 hours): Low-Coverage Endpoints
**Focus**: Booking (19%), Treatment (19%), Insurance (25%)

**Tasks**:
1. **Booking Endpoints** (2 hours)
   - Add tests for missing endpoints
   - Add error path tests
   - Target: 19% → 35%

2. **Treatment Endpoints** (2 hours)
   - Add tests for missing endpoints
   - Add validation tests
   - Target: 19% → 35%

#### Afternoon (4 hours): Auth & Patient Endpoints
**Focus**: Auth (34%), Patients (31%)

**Tasks**:
1. **Auth Endpoints** (2 hours)
   - Add error path tests
   - Add validation tests
   - Target: 34% → 50%

2. **Patient Endpoints** (2 hours)
   - Add edge case tests
   - Add permission tests
   - Target: 31% → 45%

**Expected Result**: 4 endpoints improved, +2% overall coverage

---

### END OF WEEK 1 CHECKPOINT

**Expected Metrics**:
- Coverage: **62-63%** (up from 57%)
- Test Pass Rate: **85%+** (up from 66%)
- Test Errors: **0** (down from 22)
- Failing Tests: **<30** (down from 78)

**Deliverables**:
- [ ] All service tests passing or failing cleanly (no errors)
- [ ] Booking service coverage 34% → 50%
- [ ] Payment processing tests fixed
- [ ] Subscription service tests fixed
- [ ] Core service tests added
- [ ] Low-coverage endpoints improved

---

## 📊 WEEK 2: EXPAND & COMPLETE (32 hours)

### Goal: 68%+ Coverage
**Focus**: Add secondary service tests, integration tests, fill remaining gaps

---

### DAY 6: Secondary Service Tests (8 hours)

#### Morning (4 hours): Communications Service
**Current Coverage**: 20%  
**Target**: 45%

**Tests to Add**:
```python
# tests/test_services/test_communications_service.py

async def test_send_email_notification():
    """Test email sending"""
    
async def test_send_sms_notification():
    """Test SMS sending"""
    
async def test_send_appointment_reminder():
    """Test reminder sending"""
    
async def test_handle_communication_failure():
    """Test failure handling"""
    
async def test_batch_send_notifications():
    """Test batch sending"""
```

**Expected Result**: Communications service 20% → 45%

#### Afternoon (4 hours): Insurance Service
**Current Coverage**: 35%  
**Target**: 55%

**Tests to Add**:
```python
# tests/test_services/test_insurance_service.py

async def test_verify_insurance_eligibility():
    """Test eligibility verification"""
    
async def test_submit_insurance_claim():
    """Test claim submission"""
    
async def test_process_claim_response():
    """Test response processing"""
    
async def test_calculate_patient_responsibility():
    """Test responsibility calculation"""
    
async def test_handle_claim_rejection():
    """Test rejection handling"""
```

**Expected Result**: Insurance service 35% → 55%

---

### DAY 7: More Secondary Services (8 hours)

#### Morning (4 hours): Treatment Service
**Current Coverage**: 29%  
**Target**: 50%

**Tests to Add**:
```python
# tests/test_services/test_treatment_service.py

async def test_create_treatment_plan():
    """Test treatment plan creation"""
    
async def test_add_procedure_to_plan():
    """Test procedure addition"""
    
async def test_calculate_treatment_cost():
    """Test cost calculation"""
    
async def test_approve_treatment_plan():
    """Test approval workflow"""
    
async def test_track_treatment_progress():
    """Test progress tracking"""
```

**Expected Result**: Treatment service 29% → 50%

#### Afternoon (4 hours): Imaging Service
**Current Coverage**: 29%  
**Target**: 50%

**Tests to Add**:
```python
# tests/test_services/test_imaging_service.py

async def test_upload_image():
    """Test image upload"""
    
async def test_process_image():
    """Test image processing"""
    
async def test_retrieve_image():
    """Test image retrieval"""
    
async def test_delete_image():
    """Test image deletion"""
    
async def test_validate_image_format():
    """Test format validation"""
```

**Expected Result**: Imaging service 29% → 50%

---

### DAY 8: Integration Tests (8 hours)

#### Morning (4 hours): Appointment Workflow
**Tests to Add**:
```python
# tests/test_integration/test_appointment_workflow.py

async def test_complete_appointment_workflow():
    """Test: Create → Confirm → Complete → Bill"""
    # 1. Create appointment
    # 2. Confirm appointment
    # 3. Complete appointment
    # 4. Generate invoice
    # 5. Verify all steps
    
async def test_appointment_cancellation_workflow():
    """Test: Create → Cancel → Refund"""
    # 1. Create appointment with payment
    # 2. Cancel appointment
    # 3. Process refund
    # 4. Verify cancellation
    
async def test_appointment_rescheduling_workflow():
    """Test: Create → Reschedule → Confirm"""
    # 1. Create appointment
    # 2. Reschedule to new time
    # 3. Confirm new appointment
    # 4. Verify old slot available
```

**Expected Result**: +1% coverage

#### Afternoon (4 hours): Billing Workflow
**Tests to Add**:
```python
# tests/test_integration/test_billing_workflow.py

async def test_complete_billing_workflow():
    """Test: Create Invoice → Send → Receive Payment → Close"""
    # 1. Create invoice
    # 2. Send invoice email
    # 3. Process payment
    # 4. Mark invoice as paid
    # 5. Generate receipt
    
async def test_partial_payment_workflow():
    """Test: Create Invoice → Partial Payment → Reminder → Final Payment"""
    # 1. Create invoice
    # 2. Process partial payment
    # 3. Send reminder
    # 4. Process final payment
    # 5. Verify invoice closed
    
async def test_refund_workflow():
    """Test: Payment → Refund Request → Process Refund"""
    # 1. Create payment
    # 2. Request refund
    # 3. Process refund
    # 4. Verify refund recorded
```

**Expected Result**: +1% coverage

---

### DAY 9: Fill Remaining Gaps (4 hours)

#### Morning (2 hours): Target Specific Uncovered Lines
**Tasks**:
1. Run coverage report with `--cov-report=term-missing`
2. Identify files with lowest coverage
3. Add targeted tests for uncovered lines
4. Focus on critical paths

**Expected Result**: +1% coverage

#### Afternoon (2 hours): Edge Cases & Error Paths
**Tasks**:
1. Add error handling tests
2. Add validation failure tests
3. Add permission denied tests
4. Add not found tests

**Expected Result**: +1% coverage

---

### DAY 10: Final Push (4 hours)

#### Morning (2 hours): Verify 68% Achieved
**Tasks**:
1. Run full test suite
2. Generate coverage report
3. Verify 68%+ coverage
4. Document remaining gaps

**Expected Result**: 68%+ coverage verified

#### Afternoon (2 hours): Documentation & Cleanup
**Tasks**:
1. Update WHATS_REMAINING.md
2. Update CURRENT_STATUS.md
3. Create PRODUCTION_READY.md
4. Update README with coverage badge

**Expected Result**: Documentation complete

---

## 📋 DAILY CHECKLIST

### Every Morning
- [ ] Pull latest code
- [ ] Run full test suite
- [ ] Check coverage report
- [ ] Review failing tests
- [ ] Plan day's work

### Every Afternoon
- [ ] Run tests for code written
- [ ] Check coverage improvement
- [ ] Commit and push changes
- [ ] Update progress tracking
- [ ] Plan next day

### Every Evening
- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Update status document
- [ ] Review progress vs plan
- [ ] Adjust plan if needed

---

## 🛠️ USEFUL COMMANDS

### Run Tests
```bash
# Full test suite with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing -v

# Specific test file
pytest tests/test_services/test_booking_service.py -v

# Specific test
pytest tests/test_services/test_booking_service.py::TestBookingService::test_add_to_waitlist -v

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s
```

### Coverage Reports
```bash
# HTML report (detailed)
pytest tests/ --cov=app --cov-report=html
start htmlcov/index.html  # Windows

# Terminal report with missing lines
pytest tests/ --cov=app --cov-report=term-missing

# JSON report (for parsing)
pytest tests/ --cov=app --cov-report=json

# Check total coverage
python -c 'import json; data = json.load(open("coverage.json")); print(f"Total Coverage: {data[\"totals\"][\"percent_covered\"]:.2f}%")'
```

### Debug Tests
```bash
# Run with verbose output
pytest tests/ -vv

# Show full error traces
pytest tests/ --tb=long

# Run with debugger
pytest tests/ --pdb

# Show slowest tests
pytest tests/ --durations=10
```

---

## 📊 PROGRESS TRACKING

### Week 1 Progress
| Day | Focus | Expected Coverage | Actual Coverage | Status |
|-----|-------|-------------------|-----------------|--------|
| 1 | Booking Service | 58% | | ⏳ |
| 2 | Payment Processing | 59% | | ⏳ |
| 3 | Subscription Service | 60% | | ⏳ |
| 4 | Core Services | 61% | | ⏳ |
| 5 | Endpoints | 62-63% | | ⏳ |

### Week 2 Progress
| Day | Focus | Expected Coverage | Actual Coverage | Status |
|-----|-------|-------------------|-----------------|--------|
| 6 | Secondary Services | 64% | | ⏳ |
| 7 | More Services | 65% | | ⏳ |
| 8 | Integration Tests | 66% | | ⏳ |
| 9 | Fill Gaps | 67% | | ⏳ |
| 10 | Final Push | 68%+ | | ⏳ |

---

## 🎯 SUCCESS CRITERIA

### Week 1 Goals
- [ ] Coverage ≥ 62%
- [ ] Test pass rate ≥ 85%
- [ ] Test errors = 0
- [ ] Failing tests < 30
- [ ] All service tests passing or failing cleanly

### Week 2 Goals
- [ ] Coverage ≥ 68%
- [ ] Test pass rate ≥ 90%
- [ ] Test errors = 0
- [ ] Failing tests < 20
- [ ] Integration tests added

### Final Goals
- [ ] Coverage ≥ 68%
- [ ] Test pass rate ≥ 90%
- [ ] All critical paths tested
- [ ] Documentation updated
- [ ] Production-ready

---

## 🚨 RISK MITIGATION

### If Behind Schedule
**Option 1**: Skip integration tests (save 8 hours)
- Focus on service layer only
- Target 66% instead of 68%
- Add integration tests later

**Option 2**: Skip secondary services (save 8 hours)
- Focus on core services only
- Target 65% instead of 68%
- Add secondary services later

**Option 3**: Extend timeline (add 1 week)
- Keep all goals
- More thorough testing
- Better quality

### If Ahead of Schedule
**Option 1**: Add more integration tests
- Test more workflows
- Better coverage
- Higher confidence

**Option 2**: Add performance tests
- Test under load
- Identify bottlenecks
- Optimize

**Option 3**: Add security tests
- Test auth flows
- Test permissions
- Test data access

---

## 📈 EXPECTED OUTCOMES

### After Week 1
- **Coverage**: 62-63%
- **Tests**: 250+ passing
- **Confidence**: MEDIUM-HIGH
- **Status**: Beta-ready

### After Week 2
- **Coverage**: 68%+
- **Tests**: 270+ passing
- **Confidence**: HIGH
- **Status**: Production-ready

---

## 🎉 COMPLETION CRITERIA

When you've reached 68%+ coverage:
1. ✅ Run full test suite (all pass)
2. ✅ Generate coverage report (≥68%)
3. ✅ Update documentation
4. ✅ Create production readiness report
5. ✅ Approve for full production deployment

---

**Status**: 📋 READY TO START  
**Start Date**: May 6, 2026  
**Target Completion**: May 19, 2026  
**Next Action**: Day 1 - Fix Booking Service Tests


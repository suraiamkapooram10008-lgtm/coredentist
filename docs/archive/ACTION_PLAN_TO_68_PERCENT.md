# Action Plan: Reaching 68% Code Coverage

**Current Coverage**: 56.36%  
**Target Coverage**: 68%  
**Gap**: +11.64% (approximately 1,340 lines of code)  
**Estimated Effort**: 40-60 hours (1-2 weeks)

---

## 📊 COVERAGE BREAKDOWN BY AREA

### Current Coverage by Module

| Module | Current | Target | Priority | Effort |
|--------|---------|--------|----------|--------|
| **Services** | 20-37% | 70%+ | CRITICAL | 20h |
| **API Endpoints** | 60-80% | 80%+ | HIGH | 10h |
| **Models** | 85-95% | 90%+ | LOW | 2h |
| **Core Utils** | 45-60% | 75%+ | MEDIUM | 8h |
| **Schemas** | 95-100% | 95%+ | LOW | 0h |

### Service Layer Coverage (CRITICAL)

```
appointment_service.py:    25% → 70% (+45%)  [6 hours]
billing_service.py:        30% → 70% (+40%)  [5 hours]
booking_service.py:        34% → 70% (+36%)  [5 hours]
communications_service.py: 20% → 70% (+50%)  [4 hours]
imaging_service.py:        29% → 70% (+41%)  [4 hours]
insurance_service.py:      35% → 70% (+35%)  [4 hours]
patient_service.py:        29% → 70% (+41%)  [5 hours]
payment_processing.py:     23% → 70% (+47%)  [6 hours]
subscription_service.py:   24% → 70% (+46%)  [5 hours]
treatment_service.py:      29% → 70% (+41%)  [4 hours]
```

**Total Service Layer Effort**: 48 hours

---

## 🎯 PHASE 1: QUICK WINS (Week 1 - Days 1-3)

### Goal: Reach 60% Coverage
**Effort**: 16 hours  
**Impact**: +4% coverage

### Day 1: Core Service Tests (6 hours)

#### 1.1 Appointment Service Tests (2 hours)
```python
# tests/test_services/test_appointment_service.py

async def test_create_appointment_with_duration():
    """Test automatic duration calculation"""
    
async def test_check_appointment_conflicts():
    """Test conflict detection logic"""
    
async def test_get_available_slots():
    """Test slot availability algorithm"""
    
async def test_send_appointment_reminder():
    """Test reminder sending logic"""
```

**Coverage Impact**: +3%

#### 1.2 Billing Service Tests (2 hours)
```python
# tests/test_services/test_billing_service.py

async def test_calculate_invoice_total():
    """Test invoice calculation logic"""
    
async def test_process_payment():
    """Test payment processing"""
    
async def test_generate_billing_summary():
    """Test summary generation"""
    
async def test_handle_refund():
    """Test refund processing"""
```

**Coverage Impact**: +2%

#### 1.3 Patient Service Tests (2 hours)
```python
# tests/test_services/test_patient_service.py

async def test_search_patients():
    """Test patient search logic"""
    
async def test_merge_duplicate_patients():
    """Test patient merge logic"""
    
async def test_validate_patient_data():
    """Test data validation"""
    
async def test_get_patient_history():
    """Test history retrieval"""
```

**Coverage Impact**: +2%

### Day 2: Payment & Subscription Services (6 hours)

#### 2.1 Payment Processing Tests (3 hours)
```python
# tests/test_services/test_payment_processing.py

async def test_process_credit_card_payment():
    """Test credit card processing"""
    
async def test_process_ach_payment():
    """Test ACH processing"""
    
async def test_handle_payment_failure():
    """Test failure handling"""
    
async def test_reconcile_payments():
    """Test payment reconciliation"""
    
async def test_generate_payment_receipt():
    """Test receipt generation"""
```

**Coverage Impact**: +3%

#### 2.2 Subscription Service Tests (3 hours)
```python
# tests/test_services/test_subscription_service.py

async def test_create_subscription():
    """Test subscription creation"""
    
async def test_cancel_subscription():
    """Test cancellation logic"""
    
async def test_upgrade_subscription():
    """Test plan upgrade"""
    
async def test_calculate_prorated_amount():
    """Test proration calculation"""
    
async def test_handle_subscription_renewal():
    """Test renewal logic"""
```

**Coverage Impact**: +3%

### Day 3: Booking & Insurance Services (4 hours)

#### 3.1 Booking Service Tests (2 hours)
```python
# tests/test_services/test_booking_service.py

async def test_validate_booking_availability():
    """Test availability validation"""
    
async def test_create_online_booking():
    """Test online booking creation"""
    
async def test_send_booking_confirmation():
    """Test confirmation sending"""
    
async def test_handle_booking_cancellation():
    """Test cancellation handling"""
```

**Coverage Impact**: +2%

#### 3.2 Insurance Service Tests (2 hours)
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
```

**Coverage Impact**: +2%

**End of Day 3**: ~60% coverage ✅

---

## 🎯 PHASE 2: CRITICAL PATHS (Week 1 - Days 4-5)

### Goal: Reach 65% Coverage
**Effort**: 12 hours  
**Impact**: +5% coverage

### Day 4: Edge Cases & Error Paths (6 hours)

#### 4.1 Appointment Edge Cases (2 hours)
```python
async def test_appointment_overlap_detection():
    """Test overlapping appointment detection"""
    
async def test_appointment_past_date_validation():
    """Test past date validation"""
    
async def test_appointment_provider_unavailable():
    """Test provider unavailability handling"""
    
async def test_appointment_patient_not_found():
    """Test patient not found error"""
```

**Coverage Impact**: +1.5%

#### 4.2 Billing Edge Cases (2 hours)
```python
async def test_invoice_negative_amount():
    """Test negative amount validation"""
    
async def test_payment_exceeds_balance():
    """Test overpayment handling"""
    
async def test_invoice_already_paid():
    """Test duplicate payment prevention"""
    
async def test_billing_summary_empty_data():
    """Test empty data handling"""
```

**Coverage Impact**: +1.5%

#### 4.3 Subscription Edge Cases (2 hours)
```python
async def test_subscription_already_cancelled():
    """Test double cancellation prevention"""
    
async def test_subscription_upgrade_same_plan():
    """Test same plan upgrade validation"""
    
async def test_subscription_payment_failed():
    """Test payment failure handling"""
    
async def test_subscription_trial_expired():
    """Test trial expiration logic"""
```

**Coverage Impact**: +2%

### Day 5: Integration & Workflow Tests (6 hours)

#### 5.1 Appointment Workflow Tests (2 hours)
```python
async def test_complete_appointment_workflow():
    """Test: Create → Confirm → Complete → Bill"""
    
async def test_appointment_cancellation_workflow():
    """Test: Create → Cancel → Refund"""
    
async def test_appointment_rescheduling_workflow():
    """Test: Create → Reschedule → Confirm"""
```

**Coverage Impact**: +2%

#### 5.2 Billing Workflow Tests (2 hours)
```python
async def test_complete_billing_workflow():
    """Test: Create Invoice → Send → Receive Payment → Close"""
    
async def test_partial_payment_workflow():
    """Test: Create Invoice → Partial Payment → Reminder → Final Payment"""
    
async def test_refund_workflow():
    """Test: Payment → Refund Request → Process Refund"""
```

**Coverage Impact**: +1.5%

#### 5.3 Patient Onboarding Workflow (2 hours)
```python
async def test_patient_onboarding_workflow():
    """Test: Register → Verify → Add Insurance → Book Appointment"""
    
async def test_patient_portal_access_workflow():
    """Test: Request Access → Verify Email → Set Password → Login"""
```

**Coverage Impact**: +1.5%

**End of Day 5**: ~65% coverage ✅

---

## 🎯 PHASE 3: FINAL PUSH (Week 2 - Days 6-8)

### Goal: Reach 68%+ Coverage
**Effort**: 16 hours  
**Impact**: +3%+ coverage

### Day 6: Communication & Treatment Services (6 hours)

#### 6.1 Communications Service Tests (3 hours)
```python
# tests/test_services/test_communications_service.py

async def test_send_email_notification():
    """Test email sending"""
    
async def test_send_sms_notification():
    """Test SMS sending"""
    
async def test_send_appointment_reminder():
    """Test reminder sending"""
    
async def test_send_billing_statement():
    """Test statement sending"""
    
async def test_handle_communication_failure():
    """Test failure handling"""
```

**Coverage Impact**: +2%

#### 6.2 Treatment Service Tests (3 hours)
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

**Coverage Impact**: +2%

### Day 7: Imaging & Utility Functions (6 hours)

#### 7.1 Imaging Service Tests (3 hours)
```python
# tests/test_services/test_imaging_service.py

async def test_upload_image():
    """Test image upload"""
    
async def test_process_image():
    """Test image processing"""
    
async def test_analyze_image():
    """Test image analysis"""
    
async def test_retrieve_image():
    """Test image retrieval"""
    
async def test_delete_image():
    """Test image deletion"""
```

**Coverage Impact**: +1.5%

#### 7.2 Core Utility Tests (3 hours)
```python
# tests/test_core/test_utils.py

async def test_encryption_decryption():
    """Test encryption utilities"""
    
async def test_file_validation():
    """Test file validation"""
    
async def test_sanitization():
    """Test input sanitization"""
    
async def test_rate_limiting():
    """Test rate limit logic"""
```

**Coverage Impact**: +1.5%

### Day 8: Background Tasks & Final Coverage (4 hours)

#### 8.1 Background Task Tests (2 hours)
```python
# tests/test_tasks/test_background_tasks.py

async def test_send_scheduled_reminders():
    """Test reminder task"""
    
async def test_process_subscription_renewals():
    """Test renewal task"""
    
async def test_generate_reports():
    """Test report generation task"""
    
async def test_cleanup_expired_sessions():
    """Test cleanup task"""
```

**Coverage Impact**: +1%

#### 8.2 Final Coverage Push (2 hours)
- Run coverage report
- Identify remaining gaps
- Add targeted tests for uncovered lines
- Focus on critical paths

**Coverage Impact**: +1%

**End of Day 8**: ~68%+ coverage ✅

---

## 📋 IMPLEMENTATION CHECKLIST

### Setup (30 minutes)
- [ ] Create `tests/test_services/` directory
- [ ] Create `tests/test_tasks/` directory
- [ ] Create `tests/test_core/` directory
- [ ] Set up test fixtures for services
- [ ] Configure coverage reporting

### Week 1 - Phase 1 & 2
- [ ] Day 1: Core service tests (6h)
  - [ ] Appointment service
  - [ ] Billing service
  - [ ] Patient service
- [ ] Day 2: Payment & subscription tests (6h)
  - [ ] Payment processing
  - [ ] Subscription service
- [ ] Day 3: Booking & insurance tests (4h)
  - [ ] Booking service
  - [ ] Insurance service
- [ ] Day 4: Edge cases (6h)
  - [ ] Appointment edge cases
  - [ ] Billing edge cases
  - [ ] Subscription edge cases
- [ ] Day 5: Integration tests (6h)
  - [ ] Appointment workflows
  - [ ] Billing workflows
  - [ ] Patient workflows

### Week 2 - Phase 3
- [ ] Day 6: Communication & treatment (6h)
  - [ ] Communications service
  - [ ] Treatment service
- [ ] Day 7: Imaging & utilities (6h)
  - [ ] Imaging service
  - [ ] Core utilities
- [ ] Day 8: Final push (4h)
  - [ ] Background tasks
  - [ ] Coverage gaps

### Verification
- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Verify 68%+ coverage
- [ ] Document remaining gaps
- [ ] Create maintenance plan

---

## 🛠️ TOOLS & COMMANDS

### Run Tests with Coverage
```bash
# Full test suite with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing -v

# Specific service tests
pytest tests/test_services/test_appointment_service.py -v

# Coverage for specific module
pytest tests/ --cov=app.services.appointment_service --cov-report=term-missing
```

### Generate Coverage Reports
```bash
# HTML report (detailed)
pytest tests/ --cov=app --cov-report=html
start htmlcov/index.html  # Windows

# Terminal report (quick)
pytest tests/ --cov=app --cov-report=term-missing

# XML report (CI/CD)
pytest tests/ --cov=app --cov-report=xml
```

### Find Uncovered Lines
```bash
# Show missing lines
pytest tests/ --cov=app --cov-report=term-missing | grep -A 5 "Missing"

# Coverage by file
pytest tests/ --cov=app --cov-report=term | sort -k4 -n
```

---

## 📊 PROGRESS TRACKING

### Daily Progress Template
```markdown
## Day X Progress

**Date**: [Date]
**Hours Worked**: [Hours]
**Tests Added**: [Count]
**Coverage Before**: [%]
**Coverage After**: [%]
**Coverage Gain**: [+%]

### Tests Added
- [ ] Test 1
- [ ] Test 2
- [ ] Test 3

### Issues Encountered
- Issue 1: [Description]
- Issue 2: [Description]

### Next Steps
- [ ] Task 1
- [ ] Task 2
```

### Weekly Milestones
- **End of Week 1**: 65% coverage (target: 60-65%)
- **End of Week 2**: 68%+ coverage (target: 68%+)

---

## 🎯 SUCCESS CRITERIA

### Coverage Targets
- [ ] Overall coverage ≥ 68%
- [ ] Service layer coverage ≥ 70%
- [ ] API endpoints coverage ≥ 80%
- [ ] Core utilities coverage ≥ 75%

### Test Quality
- [ ] All tests pass
- [ ] No flaky tests
- [ ] Fast execution (<10 minutes)
- [ ] Clear test names
- [ ] Good assertions

### Documentation
- [ ] Test README updated
- [ ] Coverage report generated
- [ ] Gaps documented
- [ ] Maintenance plan created

---

## 🚨 RISK MITIGATION

### Common Pitfalls
1. **Focusing on easy wins only**
   - Mitigation: Follow the plan, tackle services first

2. **Writing tests that don't increase coverage**
   - Mitigation: Check coverage after each test file

3. **Spending too much time on edge cases**
   - Mitigation: Time-box each section

4. **Not running full suite regularly**
   - Mitigation: Run full suite at end of each day

### Contingency Plan
If behind schedule:
1. Focus on service layer only (highest impact)
2. Skip imaging and treatment services (lower priority)
3. Add edge cases later
4. Target 65% minimum instead of 68%

---

## 📈 EXPECTED OUTCOMES

### After Week 1 (Phase 1 & 2)
- Coverage: ~65%
- Tests added: ~80 tests
- Service layer: ~60% coverage
- Confidence: MEDIUM-HIGH

### After Week 2 (Phase 3)
- Coverage: ~68%+
- Tests added: ~120 tests
- Service layer: ~70% coverage
- Confidence: HIGH

### Production Readiness
- Beta launch: ✅ READY (with 68%+ coverage)
- Full production: ✅ READY (with monitoring)
- Mobile launch: ⏳ PENDING (needs OAuth2)

---

## 🎉 COMPLETION CRITERIA

When you've reached 68%+ coverage:
1. ✅ Run full test suite (all pass)
2. ✅ Generate coverage report (≥68%)
3. ✅ Document remaining gaps
4. ✅ Update production readiness assessment
5. ✅ Approve for full production deployment

---

**Status**: 📋 READY TO START  
**Estimated Completion**: 2 weeks  
**Next Action**: Begin Day 1 - Core Service Tests


# Coverage Roadmap: 56% → 68%

**Current**: 56.50% | **Target**: 68.00% | **Gap**: +11.5%

---

## 📊 VISUAL PROGRESS

```
Current Progress to 68% Target:
[████████████████████████████░░░░░░░░░░░░] 56.50% / 68.00%

Remaining: 11.5% coverage needed
```

---

## 🎯 COVERAGE BY MODULE (Current vs Target)

### ✅ EXCELLENT (>90% - No Action Needed)
```
Models:        [████████████████████████████████████] 94-98% ✅
Schemas:       [████████████████████████████████████] 87-100% ✅
```

### ⚠️ GOOD (70-90% - Minor Improvements)
```
Core Audit:    [████████████████████████████░░░░░░░░] 70%
Core Security: [███████████████████████████░░░░░░░░░] 69%
```

### 🔴 CRITICAL (<50% - URGENT)
```
Services:      [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 19-37% 🚨
API Endpoints: [██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 14-57% 🚨
Core Utils:    [████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 18-92% ⚠️
```

---

## 🚀 7-DAY SPRINT TO 68%

### Week 1: Service Layer Blitz

```
Day 1 (6h): Core Services
├─ Appointment Service (2h)    → +3% coverage
├─ Payment Processing (2h)     → +3% coverage
└─ Patient Service (2h)        → +2% coverage
   Progress: 56.5% → 64.5% ✅

Day 2 (6h): Business Services
├─ Subscription Service (3h)   → +3% coverage
└─ Booking Service (3h)        → +2% coverage
   Progress: 64.5% → 69.5% ✅

Day 3 (4h): Communication Services
├─ Insurance Service (2h)      → +2% coverage
└─ Communications Service (2h) → +2% coverage
   Progress: 69.5% → 73.5% ✅

CHECKPOINT: 73.5% coverage (Target: 68%) ✅
```

### Week 2: Polish & Edge Cases (Optional)

```
Day 4-5 (12h): Treatment & Imaging
├─ Treatment Service (6h)      → +2% coverage
└─ Imaging Service (6h)        → +2% coverage
   Progress: 73.5% → 77.5% ✅

Day 6-7 (12h): Edge Cases & Integration
├─ Edge Cases (6h)             → +2% coverage
└─ Integration Tests (6h)      → +1% coverage
   Progress: 77.5% → 80.5% ✅

FINAL: 80.5% coverage (Exceeds 68% target!) 🎉
```

---

## 📈 IMPACT ANALYSIS

### High Impact (>3% coverage gain)
1. **Appointment Service** → +3%
2. **Payment Processing** → +3%
3. **Subscription Service** → +3%

### Medium Impact (2-3% coverage gain)
4. **Booking Service** → +2%
5. **Patient Service** → +2%
6. **Insurance Service** → +2%
7. **Communications Service** → +2%
8. **Treatment Service** → +2%
9. **Imaging Service** → +2%
10. **Edge Cases** → +2%

### Low Impact (1% coverage gain)
11. **Integration Tests** → +1%

---

## 🎯 MINIMUM VIABLE PATH (3 Days)

If time is limited, focus on **highest impact only**:

```
Day 1: Core Services (6h)
├─ Appointment Service    → +3%
├─ Payment Processing     → +3%
└─ Patient Service        → +2%
   Total: +8% (56.5% → 64.5%)

Day 2: Business Services (6h)
├─ Subscription Service   → +3%
└─ Booking Service        → +2%
   Total: +5% (64.5% → 69.5%)

Day 3: Final Push (4h)
├─ Insurance Service      → +2%
└─ Communications Service → +2%
   Total: +4% (69.5% → 73.5%)

RESULT: 73.5% coverage in 3 days (16 hours)
Exceeds 68% target! ✅
```

---

## 📋 SERVICE LAYER PRIORITY MATRIX

### Priority 0 (CRITICAL - Do First)
| Service | Current | Target | Effort | Impact | Status |
|---------|---------|--------|--------|--------|--------|
| appointment_service | 24% | 70% | 2h | +3% | ⏳ TODO |
| payment_processing | 23% | 70% | 2h | +3% | ⏳ TODO |
| subscription_service | 24% | 70% | 3h | +3% | ⏳ TODO |

### Priority 1 (HIGH - Do Second)
| Service | Current | Target | Effort | Impact | Status |
|---------|---------|--------|--------|--------|--------|
| booking_service | 34% | 70% | 3h | +2% | ⏳ TODO |
| patient_service | 29% | 70% | 2h | +2% | ⏳ TODO |
| insurance_service | 35% | 70% | 2h | +2% | ⏳ TODO |
| communications_service | 20% | 70% | 2h | +2% | ⏳ TODO |

### Priority 2 (MEDIUM - Do Third)
| Service | Current | Target | Effort | Impact | Status |
|---------|---------|--------|--------|--------|--------|
| treatment_service | 29% | 70% | 6h | +2% | ⏳ TODO |
| imaging_service | 29% | 70% | 6h | +2% | ⏳ TODO |
| billing_service | 30% | 70% | 0h | +0% | ✅ DONE |

### Priority 3 (LOW - Optional)
| Service | Current | Target | Effort | Impact | Status |
|---------|---------|--------|--------|--------|--------|
| booking_availability | 24% | 60% | 2h | +1% | ⏳ TODO |
| booking_validation | 28% | 60% | 2h | +1% | ⏳ TODO |
| payment_reconciliation | 24% | 60% | 2h | +1% | ⏳ TODO |
| subscription_billing | 22% | 60% | 2h | +1% | ⏳ TODO |

---

## 🔥 QUICK WINS (Do These First!)

### 1. Appointment Service (2 hours → +3%)
```python
# tests/test_services/test_appointment_service.py

✅ test_create_appointment_with_duration()
✅ test_check_appointment_conflicts()
✅ test_get_available_slots()
✅ test_send_appointment_reminder()
✅ test_appointment_overlap_detection()
✅ test_appointment_past_date_validation()
```

### 2. Payment Processing (2 hours → +3%)
```python
# tests/test_services/test_payment_processing.py

✅ test_process_credit_card_payment()
✅ test_process_ach_payment()
✅ test_handle_payment_failure()
✅ test_reconcile_payments()
✅ test_generate_payment_receipt()
✅ test_payment_exceeds_balance()
```

### 3. Subscription Service (3 hours → +3%)
```python
# tests/test_services/test_subscription_service.py

✅ test_create_subscription()
✅ test_cancel_subscription()
✅ test_upgrade_subscription()
✅ test_calculate_prorated_amount()
✅ test_handle_subscription_renewal()
✅ test_subscription_payment_failed()
```

**Total: 7 hours → +9% coverage (56.5% → 65.5%)**

---

## 📊 DAILY PROGRESS TRACKER

### Day 1 Progress
- [ ] Appointment Service tests (2h)
- [ ] Payment Processing tests (2h)
- [ ] Patient Service tests (2h)
- [ ] Run coverage: `pytest tests/ --cov=app --cov-report=term`
- [ ] Expected: 64.5% coverage

### Day 2 Progress
- [ ] Subscription Service tests (3h)
- [ ] Booking Service tests (3h)
- [ ] Run coverage: `pytest tests/ --cov=app --cov-report=term`
- [ ] Expected: 69.5% coverage

### Day 3 Progress
- [ ] Insurance Service tests (2h)
- [ ] Communications Service tests (2h)
- [ ] Run coverage: `pytest tests/ --cov=app --cov-report=term`
- [ ] Expected: 73.5% coverage

### Checkpoint
- [ ] Coverage ≥ 68%? ✅
- [ ] All new tests passing? ✅
- [ ] No regressions? ✅
- [ ] Ready for production? ✅

---

## 🎯 SUCCESS CRITERIA

### Must Have (Required for 68%)
- [x] Billing module: 100% ✅
- [ ] Service layer: 70%+ ⏳
- [ ] Overall coverage: 68%+ ⏳
- [ ] All critical paths tested ⏳

### Should Have (Nice to Have)
- [ ] API endpoints: 80%+
- [ ] Core utilities: 75%+
- [ ] Integration tests: Complete workflows
- [ ] Documentation: Updated

### Could Have (Future)
- [ ] Performance tests
- [ ] Load tests
- [ ] Security tests
- [ ] E2E tests

---

## 🚨 RISK MITIGATION

### Risk 1: Behind Schedule
**Mitigation**: Focus on P0 services only (appointment, payment, subscription)  
**Fallback**: Target 65% instead of 68%

### Risk 2: Tests Not Increasing Coverage
**Mitigation**: Check coverage after each test file  
**Command**: `pytest tests/test_services/test_X.py --cov=app.services.X --cov-report=term-missing`

### Risk 3: Flaky Tests
**Mitigation**: Use proper fixtures, avoid time-dependent tests  
**Solution**: Mock external dependencies, use freezegun for time

### Risk 4: Test Execution Too Slow
**Mitigation**: Run tests in parallel with pytest-xdist  
**Command**: `pytest tests/ -n auto --cov=app`

---

## 📈 EXPECTED OUTCOMES

### After 3 Days (Minimum Viable)
- **Coverage**: 73.5% (exceeds 68% target)
- **Tests Added**: ~60 tests
- **Service Layer**: ~60% coverage
- **Confidence**: HIGH
- **Production Ready**: YES ✅

### After 7 Days (Full Sprint)
- **Coverage**: 80.5% (far exceeds target)
- **Tests Added**: ~120 tests
- **Service Layer**: ~70% coverage
- **Confidence**: VERY HIGH
- **Production Ready**: YES ✅

---

## 🎉 COMPLETION CHECKLIST

When you've reached 68%+ coverage:
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Generate coverage report: `pytest tests/ --cov=app --cov-report=html`
- [ ] Verify coverage ≥ 68%: Check `htmlcov/index.html`
- [ ] Document remaining gaps: Update `WHATS_REMAINING.md`
- [ ] Update production readiness: Update `COMPREHENSIVE_REVIEW_MAY_2026.md`
- [ ] Approve for production: Get stakeholder sign-off

---

## 🚀 GET STARTED NOW!

### Step 1: Create Test Directory
```bash
cd coredent-api
mkdir -p tests/test_services
```

### Step 2: Copy Template
```bash
# Create first test file
cat > tests/test_services/test_appointment_service.py << 'EOF'
import pytest
from app.services.appointment_service import AppointmentService

class TestAppointmentService:
    @pytest.mark.asyncio
    async def test_create_appointment_with_duration(self, db_session):
        """Test automatic duration calculation"""
        service = AppointmentService(db_session)
        # TODO: Add test implementation
        pass
EOF
```

### Step 3: Run First Test
```bash
pytest tests/test_services/test_appointment_service.py -v
```

### Step 4: Check Coverage
```bash
pytest tests/test_services/test_appointment_service.py --cov=app.services.appointment_service --cov-report=term-missing
```

---

**Status**: 📋 READY TO START  
**Next Action**: Create `tests/test_services/test_appointment_service.py`  
**Expected Time**: 2 hours  
**Expected Impact**: +3% coverage  

**LET'S GO! 🚀**

# Handoff Document for New Model
**Date**: May 5, 2026  
**Project**: CoreDent Dental Practice Management SaaS  
**Task**: Fix failing tests to reach 68% code coverage

---

## 🎯 CURRENT SITUATION

### Metrics
- **Current Coverage**: 57.27%
- **Target Coverage**: 68%
- **Gap**: -10.73% (~1,235 lines)
- **Tests**: 192/292 passing (66%)
- **Failures**: 78 tests
- **Errors**: 22 tests

### What's Working ✅
- Authentication (17/17 tests passing)
- Patients (11/11 tests passing)
- Billing (25/25 tests passing)
- Appointments (13/13 tests passing)
- Subscriptions basic (17/17 tests passing)

### What's Broken ❌
- Service layer tests (78 failures + 22 errors)
- Booking service tests
- Payment processing tests
- Subscription service tests
- Patient service tests

---

## 🔍 ROOT CAUSE

**The service layer code doesn't match the database models.**

### Example Problem:
```python
# Service tries to use:
BookingPage(
    name="Test",              # ❌ Field doesn't exist
    description="...",        # ❌ Field doesn't exist
    is_active=True,          # ❌ Field doesn't exist
    slug="test"              # ❌ Field doesn't exist
)

# But the actual model has:
BookingPage(
    page_title="Test",       # ✅ Correct field
    welcome_message="...",   # ✅ Correct field
    status=BookingPageStatus.ACTIVE,  # ✅ Correct field (enum)
    page_slug="test"         # ✅ Correct field
)
```

---

## 📋 WHAT NEEDS TO BE FIXED

### Priority 1: Fix BookingService (30 min)
**File**: `coredent-api/app/services/booking_service.py`

**Changes needed**:
1. Line 48-54: Update `create_booking_page()` method
   - Change `name` → `page_title`
   - Change `description` → `welcome_message`
   - Change `is_active` → `status` (use `BookingPageStatus` enum)
   - Change `slug` → `page_slug`

2. Line 85-90: Update `get_public_booking_page()` method
   - Change `BookingPage.slug` → `BookingPage.page_slug`
   - Change `BookingPage.is_active == True` → `BookingPage.status == BookingPageStatus.ACTIVE`

3. Line 115-135: Update `create_online_booking()` method
   - Split `patient_name` into `first_name` and `last_name`
   - Change `patient_email` → `email`
   - Change `patient_phone` → `phone`
   - Change `appointment_date` → `requested_date` (date) and `requested_time` (time)
   - Change `notes` → `reason`
   - Add required `practice_id` parameter
   - Use `BookingStatus` enum for status

4. Line 200-220: Update `add_to_waitlist()` method
   - Split `patient_name` into `first_name` and `last_name`
   - Change `patient_email` → `email`
   - Change `patient_phone` → `phone`
   - Change `preferred_date` → `preferred_dates` (JSON array)
   - Change `notes` → `reason`
   - Add required `practice_id` parameter
   - Use `WaitlistStatus` enum

5. Add imports:
   ```python
   from app.models.booking import (
       BookingPage,
       OnlineBooking,
       WaitlistEntry,
       BookingPageStatus,  # ADD
       BookingStatus,      # ADD
       WaitlistStatus,     # ADD
   )
   ```

### Priority 2: Fix Tests (15 min)
**File**: `coredent-api/tests/test_services/test_booking_service.py`

**Changes needed**:
- Add `practice_id=test_practice.id` to all service method calls
- Update assertions to check correct field names

### Priority 3: Fix PaymentProcessing (30 min)
**File**: `coredent-api/app/services/payment_processing.py`

**Add these classes/methods**:
```python
class WebhookProcessor:
    @staticmethod
    def verify_stripe_signature(payload: str, signature: str, secret: str) -> bool:
        # Implement Stripe webhook verification
        pass
    
    @staticmethod
    def verify_razorpay_signature(payload: str, signature: str, secret: str) -> bool:
        # Implement Razorpay webhook verification
        pass

class StripePaymentProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_payment_intent(self, amount: Decimal, currency: str = "usd"):
        # Implement Stripe payment intent creation
        pass
```

### Priority 4: Fix SubscriptionService (30 min)
**File**: `coredent-api/app/services/subscription_service.py`

**Add these methods**:
```python
@staticmethod
def calculate_period_start_end(start_date: datetime, billing_cycle: str) -> tuple:
    # Calculate subscription period based on billing cycle
    pass

@staticmethod
def calculate_proration_amount(old_price: Decimal, new_price: Decimal, 
                               days_remaining: int, total_days: int) -> Decimal:
    # Calculate prorated amount for plan changes
    pass
```

### Priority 5: Fix PatientService (30 min)
**File**: `coredent-api/app/services/patient_service.py`

**Add these methods**:
```python
async def create_patient(self, practice_id: UUID, first_name: str, 
                        last_name: str, email: str) -> Patient:
    # Implement patient creation with duplicate check
    pass

async def search_patients(self, practice_id: UUID, query: str) -> List[Patient]:
    # Implement patient search
    pass
```

---

## 📁 KEY FILES TO READ

### Models (understand the actual database structure):
1. `coredent-api/app/models/booking.py` - BookingPage, OnlineBooking, WaitlistEntry models
2. `coredent-api/app/models/patient.py` - Patient model
3. `coredent-api/app/models/billing.py` - Invoice, Payment models

### Services (what needs to be fixed):
1. `coredent-api/app/services/booking_service.py` - Main file to fix
2. `coredent-api/app/services/payment_processing.py` - Add webhook methods
3. `coredent-api/app/services/subscription_service.py` - Add calculation methods
4. `coredent-api/app/services/patient_service.py` - Add CRUD methods

### Tests (what's failing):
1. `coredent-api/tests/test_services/test_booking_service.py` - 11 failures
2. `coredent-api/tests/test_services/test_payment_processing.py` - 10 failures
3. `coredent-api/tests/test_services/test_subscription_service.py` - 11 errors
4. `coredent-api/tests/test_services/test_patient_service.py` - 9 failures

### Documentation (context):
1. `coredent-api/EXACT_FIXES_NEEDED.md` - Detailed fix instructions
2. `coredent-api/REAL_FIX_PLAN.md` - Overall strategy
3. `coredent-api/CURRENT_STATUS_MAY_5_2026.md` - Current state assessment

---

## 🚀 RECOMMENDED APPROACH

### Step 1: Fix BookingService (START HERE)
```bash
# Read the model to understand fields
cat coredent-api/app/models/booking.py

# Read the service to see what's wrong
cat coredent-api/app/services/booking_service.py

# Make the fixes (see Priority 1 above)

# Test it
cd coredent-api
pytest tests/test_services/test_booking_service.py -v
```

### Step 2: Fix Other Services
Repeat for payment_processing, subscription_service, patient_service

### Step 3: Verify
```bash
# Run all tests
pytest tests/ --cov=app --cov-report=term -v

# Check coverage
python -c 'import json; data = json.load(open("coverage.json")); print(f"{data[\"totals\"][\"percent_covered\"]:.2f}%")'
```

---

## 🎯 SUCCESS CRITERIA

- [ ] All booking service tests pass (11/11)
- [ ] All payment processing tests pass (10/10)
- [ ] All subscription service tests pass (11/11)
- [ ] All patient service tests pass (9/9)
- [ ] Coverage increases to 62%+ (from 57%)
- [ ] No test errors (0 errors)
- [ ] Test pass rate >85% (from 66%)

---

## 💡 KEY INSIGHTS

1. **Don't skip tests** - Fix the actual code to match the models
2. **Model is the source of truth** - Always check the model first
3. **Enums matter** - Use proper enum types, not strings/booleans
4. **Required fields** - Many models require `practice_id`
5. **Field name mapping** - Service parameters don't always match model fields

---

## 🛠️ USEFUL COMMANDS

```bash
# Run specific test file
pytest tests/test_services/test_booking_service.py -v

# Run with detailed output
pytest tests/test_services/test_booking_service.py -vv --tb=short

# Run single test
pytest tests/test_services/test_booking_service.py::TestBookingService::test_create_booking_page -v

# Check coverage for specific file
pytest tests/ --cov=app.services.booking_service --cov-report=term-missing -v

# Run all tests with coverage
pytest tests/ --cov=app --cov-report=term --cov-report=json -v
```

---

## 📞 QUICK REFERENCE

**Project Structure**:
```
coredent-api/
├── app/
│   ├── models/          # Database models (source of truth)
│   ├── services/        # Business logic (needs fixing)
│   ├── api/v1/endpoints/  # API endpoints
│   └── schemas/         # Pydantic schemas
├── tests/
│   ├── test_services/   # Service tests (failing)
│   └── conftest.py      # Test fixtures
└── alembic/versions/    # Database migrations
```

**Key Patterns**:
- Models use SQLAlchemy ORM
- Services use async/await
- Tests use pytest with asyncio
- Database is PostgreSQL

---

## ✅ READY TO START

**First command to run**:
```bash
cd coredent-api
cat app/models/booking.py | grep "class BookingPage" -A 50
```

This will show you the actual BookingPage model fields, then you can fix the service to match.

**Good luck!** 🚀


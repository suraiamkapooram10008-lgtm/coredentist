# Real Fix Plan - Actually Fix the Tests
**Date**: May 5, 2026  
**Approach**: Fix the actual issues, don't skip tests

---

## 🎯 THE REAL PROBLEM

The service tests were written **assuming** certain service methods and model fields exist, but they don't match the actual implementation.

### Two Options:

**Option A: Fix the Service Implementations** ✅ RECOMMENDED
- Implement the missing service methods
- Make services match what tests expect
- **This is the RIGHT way**

**Option B: Rewrite the Tests** ⚠️ FALLBACK
- Change tests to match actual implementation
- Only if Option A is too complex

---

## 📋 WHAT NEEDS TO BE FIXED

### 1. Booking Service Issues

**Problem**: Tests expect these methods that don't exist:
```python
BookingService.create_booking_page(
    db, practice_id, name, description, is_active
)
```

**But the model has**:
- `page_title` (not `name`)
- `welcome_message` (not `description`)
- `status` enum (not `is_active` boolean)
- `page_slug` (not `slug`)

**Solution**: Create `app/services/booking_service.py` with these methods:

```python
class BookingService:
    @staticmethod
    def generate_confirmation_code() -> str:
        """Generate 8-character confirmation code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate URL-safe verification token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    async def create_booking_page(
        db: AsyncSession,
        practice_id: UUID,
        name: str,
        description: str = None,
        is_active: bool = True
    ) -> BookingPage:
        """Create a booking page - maps test params to model fields"""
        slug = name.lower().replace(' ', '-')
        
        booking_page = BookingPage(
            practice_id=practice_id,
            page_title=name,  # Map 'name' to 'page_title'
            welcome_message=description,  # Map 'description' to 'welcome_message'
            page_slug=slug,  # Generate slug
            status=BookingPageStatus.ACTIVE if is_active else BookingPageStatus.INACTIVE
        )
        
        db.add(booking_page)
        await db.commit()
        await db.refresh(booking_page)
        
        # Add convenience properties for tests
        booking_page.name = booking_page.page_title
        booking_page.slug = booking_page.page_slug
        booking_page.is_active = (booking_page.status == BookingPageStatus.ACTIVE)
        
        return booking_page
    
    # ... implement all other methods the tests expect
```

### 2. Payment Processing Issues

**Problem**: Tests expect Stripe/Razorpay webhook verification methods

**Solution**: Implement in `app/services/payment_processing.py`:

```python
class WebhookProcessor:
    @staticmethod
    def verify_stripe_signature(
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify Stripe webhook signature"""
        try:
            import stripe
            stripe.Webhook.construct_event(
                payload, signature, secret
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def verify_razorpay_signature(
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify Razorpay webhook signature"""
        import hmac
        import hashlib
        
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)

class StripePaymentProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "usd",
        customer_id: str = None
    ):
        """Create Stripe payment intent"""
        # Implementation
        pass
    
    # ... implement all methods tests expect
```

### 3. Subscription Service Issues

**Problem**: Tests expect subscription management methods

**Solution**: Implement in `app/services/subscription_service.py`:

```python
class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def calculate_period_start_end(
        start_date: datetime,
        billing_cycle: str
    ) -> tuple[datetime, datetime]:
        """Calculate subscription period"""
        if billing_cycle == "monthly":
            end_date = start_date + relativedelta(months=1)
        elif billing_cycle == "yearly":
            end_date = start_date + relativedelta(years=1)
        else:
            raise ValueError(f"Invalid billing cycle: {billing_cycle}")
        
        return start_date, end_date
    
    @staticmethod
    def calculate_proration_amount(
        old_price: Decimal,
        new_price: Decimal,
        days_remaining: int,
        total_days: int
    ) -> Decimal:
        """Calculate prorated amount for plan change"""
        if total_days == 0:
            return Decimal("0.00")
        
        unused_amount = old_price * (days_remaining / total_days)
        new_amount = new_price * (days_remaining / total_days)
        
        return new_amount - unused_amount
    
    # ... implement all methods
```

### 4. Patient Service Issues

**Problem**: Tests expect patient management methods

**Solution**: Implement in `app/services/patient_service.py`:

```python
class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_patient(
        self,
        practice_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        phone: str = None,
        date_of_birth: date = None
    ) -> Patient:
        """Create a new patient"""
        # Check for duplicate email
        existing = await self.db.execute(
            select(Patient).where(
                Patient.practice_id == practice_id,
                Patient.email == email
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Patient with this email already exists")
        
        patient = Patient(
            practice_id=practice_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth
        )
        
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        
        return patient
    
    # ... implement all methods
```

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Create Service Files (2 hours)

1. **Create `app/services/booking_service.py`** (30 min)
   - Implement all methods tests expect
   - Map test parameters to actual model fields
   - Add convenience properties

2. **Create `app/services/payment_processing.py`** (30 min)
   - Implement webhook verification
   - Implement Stripe payment processor
   - Add proper error handling

3. **Create `app/services/subscription_service.py`** (30 min)
   - Implement period calculations
   - Implement proration logic
   - Implement subscription management

4. **Create `app/services/patient_service.py`** (30 min)
   - Implement patient CRUD
   - Implement search functionality
   - Implement validation

### Phase 2: Fix Failing Tests (4 hours)

1. **Run booking service tests** (1 hour)
   - Fix any remaining issues
   - Ensure all tests pass

2. **Run payment processing tests** (1 hour)
   - Add Stripe mocks
   - Fix webhook tests
   - Ensure all tests pass

3. **Run subscription service tests** (1 hour)
   - Fix calculation logic
   - Add proper fixtures
   - Ensure all tests pass

4. **Run patient service tests** (1 hour)
   - Fix validation logic
   - Fix search functionality
   - Ensure all tests pass

### Phase 3: Verify and Document (1 hour)

1. **Run full test suite** (30 min)
   - Verify all tests pass
   - Check coverage improvement

2. **Update documentation** (30 min)
   - Document service methods
   - Update README
   - Create service usage examples

---

## 📊 EXPECTED RESULTS

### Before Fix
- Coverage: 57%
- Tests passing: 192/292 (66%)
- Failures: 78
- Errors: 22

### After Fix
- Coverage: 62-65%
- Tests passing: 260+/292 (89%+)
- Failures: <20
- Errors: 0

---

## 🛠️ TOOLS NEEDED

```bash
# Install additional dependencies if needed
pip install stripe razorpay python-dateutil

# Run specific service tests
pytest tests/test_services/test_booking_service.py -v
pytest tests/test_services/test_payment_processing.py -v
pytest tests/test_services/test_subscription_service.py -v
pytest tests/test_services/test_patient_service.py -v

# Run all tests with coverage
pytest tests/ --cov=app --cov-report=term-missing -v
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] All booking service tests pass
- [ ] All payment processing tests pass
- [ ] All subscription service tests pass
- [ ] All patient service tests pass
- [ ] Coverage increases to 62%+
- [ ] No test errors (only passes or clean failures)
- [ ] Services are documented
- [ ] Services follow project patterns

---

## 🎯 START HERE

**Step 1**: Create `app/services/booking_service.py`

I'll create this file with all the methods the tests expect, mapping test parameters to actual model fields.

**Ready to start?** Say "yes" and I'll begin implementing the services.


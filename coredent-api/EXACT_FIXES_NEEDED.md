# Exact Fixes Needed - Step by Step
**Date**: May 5, 2026

---

## 🎯 THE CORE ISSUE

The `BookingService` (and other services) use field names that **don't exist** on the models.

### Example:
```python
# Service tries to do this:
booking_page = BookingPage(
    name=name,              # ❌ BookingPage has no 'name' field
    description=description, # ❌ BookingPage has no 'description' field
    is_active=is_active,    # ❌ BookingPage has no 'is_active' field
    slug=slug               # ❌ BookingPage has no 'slug' field
)
```

### But the model actually has:
```python
class BookingPage(Base):
    page_title = Column(String(255))      # ✅ Use this instead of 'name'
    welcome_message = Column(Text)        # ✅ Use this instead of 'description'
    status = Column(Enum(BookingPageStatus))  # ✅ Use this instead of 'is_active'
    page_slug = Column(String(100))       # ✅ Use this instead of 'slug'
```

---

## 📋 FIX #1: Update BookingService

**File**: `coredent-api/app/services/booking_service.py`

### Change 1: Fix `create_booking_page` method

**Current (BROKEN)**:
```python
booking_page = BookingPage(
    practice_id=practice_id,
    name=name,
    description=description,
    is_active=is_active,
    slug=name.lower().replace(" ", "-"),
)
```

**Fixed**:
```python
from app.models.booking import BookingPageStatus

booking_page = BookingPage(
    practice_id=practice_id,
    page_title=name,  # ✅ Changed from 'name'
    welcome_message=description,  # ✅ Changed from 'description'
    status=BookingPageStatus.ACTIVE if is_active else BookingPageStatus.INACTIVE,  # ✅ Changed from 'is_active'
    page_slug=name.lower().replace(" ", "-"),  # ✅ Changed from 'slug'
)
```

### Change 2: Fix `get_public_booking_page` method

**Current (BROKEN)**:
```python
select(BookingPage).where(
    BookingPage.slug == slug,
    BookingPage.is_active == True,
)
```

**Fixed**:
```python
select(BookingPage).where(
    BookingPage.page_slug == slug,  # ✅ Changed from 'slug'
    BookingPage.status == BookingPageStatus.ACTIVE,  # ✅ Changed from 'is_active'
)
```

---

## 📋 FIX #2: Update OnlineBooking Fields

**File**: `coredent-api/app/services/booking_service.py`

### Issue: OnlineBooking model fields don't match

**Current model has**:
```python
class OnlineBooking(Base):
    first_name = Column(String(100))  # ✅ Separate first/last name
    last_name = Column(String(100))
    requested_date = Column(Date)     # ✅ Not 'appointment_date'
    requested_time = Column(Time)     # ✅ Separate date and time
    reason = Column(Text)             # ✅ Not 'notes'
```

### Change: Fix `create_online_booking` method

**Current (BROKEN)**:
```python
booking = OnlineBooking(
    booking_page_id=booking_page_id,
    patient_name=patient_name,  # ❌ No 'patient_name' field
    patient_email=patient_email,
    patient_phone=patient_phone,
    appointment_date=appointment_date,  # ❌ No 'appointment_date' field
    appointment_type=appointment_type,  # ❌ Wrong field
    notes=notes,  # ❌ Should be 'reason'
    confirmation_code=confirmation_code,
    verification_token=verification_token,
    status="pending",
)
```

**Fixed**:
```python
# Split patient_name into first_name and last_name
name_parts = patient_name.split(' ', 1)
first_name = name_parts[0]
last_name = name_parts[1] if len(name_parts) > 1 else ''

booking = OnlineBooking(
    booking_page_id=booking_page_id,
    practice_id=practice_id,  # ✅ Add practice_id (required)
    first_name=first_name,  # ✅ Changed from 'patient_name'
    last_name=last_name,  # ✅ Added
    email=patient_email,  # ✅ Changed from 'patient_email'
    phone=patient_phone,  # ✅ Changed from 'patient_phone'
    requested_date=appointment_date.date(),  # ✅ Changed from 'appointment_date'
    requested_time=appointment_date.time(),  # ✅ Added
    reason=notes,  # ✅ Changed from 'notes'
    confirmation_code=confirmation_code,
    email_verification_token=verification_token,  # ✅ Changed field name
    status=BookingStatus.PENDING,  # ✅ Use enum
)
```

---

## 📋 FIX #3: Update Waitlist Fields

**File**: `coredent-api/app/services/booking_service.py`

### Issue: Waitlist model fields don't match

**Current model has**:
```python
class WaitlistEntry(Base):
    first_name = Column(String(100))  # ✅ Separate first/last name
    last_name = Column(String(100))
    preferred_dates = Column(JSON)    # ✅ Array, not single date
    reason = Column(Text)             # ✅ Not 'notes'
```

### Change: Fix `add_to_waitlist` method

**Current (BROKEN)**:
```python
waitlist_entry = Waitlist(
    booking_page_id=booking_page_id,
    patient_name=patient_name,  # ❌ No 'patient_name' field
    patient_email=patient_email,  # ❌ Should be 'email'
    patient_phone=patient_phone,  # ❌ Should be 'phone'
    preferred_date=preferred_date,  # ❌ Should be 'preferred_dates' (array)
    notes=notes,  # ❌ Should be 'reason'
    status="active",
)
```

**Fixed**:
```python
# Split patient_name
name_parts = patient_name.split(' ', 1)
first_name = name_parts[0]
last_name = name_parts[1] if len(name_parts) > 1 else ''

waitlist_entry = WaitlistEntry(
    booking_page_id=booking_page_id,
    practice_id=practice_id,  # ✅ Add practice_id (required)
    first_name=first_name,  # ✅ Changed from 'patient_name'
    last_name=last_name,  # ✅ Added
    email=patient_email,  # ✅ Changed from 'patient_email'
    phone=patient_phone,  # ✅ Changed from 'patient_phone'
    preferred_dates=[preferred_date.isoformat()] if preferred_date else [],  # ✅ Changed to array
    reason=notes,  # ✅ Changed from 'notes'
    status=WaitlistStatus.ACTIVE,  # ✅ Use enum
)
```

---

## 📋 FIX #4: Add Missing practice_id

**Issue**: Many methods don't pass `practice_id` which is required

### Update `create_online_booking` signature:
```python
@staticmethod
async def create_online_booking(
    db: AsyncSession,
    booking_page_id: UUID,
    practice_id: UUID,  # ✅ ADD THIS
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    appointment_date: datetime,
    appointment_type: str,
    notes: Optional[str] = None,
) -> OnlineBooking:
```

### Update `add_to_waitlist` signature:
```python
@staticmethod
async def add_to_waitlist(
    db: AsyncSession,
    booking_page_id: UUID,
    practice_id: UUID,  # ✅ ADD THIS
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    preferred_date: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> WaitlistEntry:
```

---

## 📋 FIX #5: Update Tests to Pass practice_id

**File**: `coredent-api/tests/test_services/test_booking_service.py`

### Update all test calls to include practice_id:

```python
# Before
booking = await BookingService.create_online_booking(
    db=db_session,
    booking_page_id=booking_page.id,
    patient_name="John Doe",
    ...
)

# After
booking = await BookingService.create_online_booking(
    db=db_session,
    booking_page_id=booking_page.id,
    practice_id=test_practice.id,  # ✅ ADD THIS
    patient_name="John Doe",
    ...
)
```

---

## 📋 FIX #6: Import Required Enums

**File**: `coredent-api/app/services/booking_service.py`

### Add to imports:
```python
from app.models.booking import (
    BookingPage,
    OnlineBooking,
    WaitlistEntry,  # ✅ Changed from Waitlist
    BookingPageStatus,  # ✅ ADD THIS
    BookingStatus,  # ✅ ADD THIS
    WaitlistStatus,  # ✅ ADD THIS
)
```

---

## 🚀 IMPLEMENTATION ORDER

### Step 1: Fix BookingService (30 minutes)
1. Update imports
2. Fix `create_booking_page` method
3. Fix `get_public_booking_page` method
4. Fix `create_online_booking` method
5. Fix `add_to_waitlist` method

### Step 2: Update Tests (15 minutes)
1. Add `practice_id` to all test calls
2. Run tests to verify

### Step 3: Fix Other Services (2 hours)
1. Fix `payment_processing.py` - add webhook methods
2. Fix `subscription_service.py` - add calculation methods
3. Fix `patient_service.py` - add CRUD methods

### Step 4: Verify (15 minutes)
1. Run full test suite
2. Check coverage
3. Document changes

---

## ✅ READY TO START?

Say "fix booking service" and I'll implement all the changes to `booking_service.py` right now.


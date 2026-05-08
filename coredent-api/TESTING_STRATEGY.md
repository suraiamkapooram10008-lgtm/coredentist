# Testing Strategy to Reach 68% Coverage

**Current Status**: 56.36% coverage  
**Target**: 68% coverage  
**Gap**: +11.64% (~1,340 lines)

## Current Coverage by File (from test run)

### Critical Low Coverage Files (Priority 1)
- `auth.py`: 23% (212 stmts, 163 miss) - **CRITICAL**
- `billing.py`: 22% (163 stmts, 127 miss) - **CRITICAL**
- `booking.py`: 14% (448 stmts, 387 miss) - **CRITICAL**
- `communications.py`: 24% (248 stmts, 189 miss) - **HIGH**
- `payments.py`: Need to check
- `insurance.py`: Need to check

### Medium Coverage Files (Priority 2)
- `appointments.py`: 41% (128 stmts, 75 miss) - **MEDIUM**
- `accounting.py`: 35% (79 stmts, 51 miss) - **MEDIUM**
- `deps.py`: 46% (76 stmts, 41 miss) - **MEDIUM**
- `clinic.py`: 31% (51 stmts, 35 miss) - **MEDIUM**
- `clinical.py`: 40% (43 stmts, 26 miss) - **MEDIUM**
- `compliance.py`: 38% (42 stmts, 26 miss) - **MEDIUM**

### Good Coverage Files (Priority 3)
- `api.py`: 100% ✅
- `__init__.py`: 100% ✅

## Implementation Plan

### Phase 1: Auth Endpoints (Highest Impact)
**File**: `app/api/v1/endpoints/auth.py`  
**Current**: 23% (163 lines uncovered)  
**Target**: 70%+  
**Impact**: +10% overall coverage

Tests to add:
1. Password reset flow (request + confirm)
2. Email verification flow
3. Token refresh
4. MFA enrollment and verification
5. Account lockout scenarios
6. Session management

### Phase 2: Billing Endpoints
**File**: `app/api/v1/endpoints/billing.py`  
**Current**: 22% (127 lines uncovered)  
**Target**: 70%+  
**Impact**: +8% overall coverage

Tests to add:
1. Invoice CRUD operations
2. Payment processing
3. Billing summary generation
4. GST/tax calculations
5. Payment methods
6. Refund processing

### Phase 3: Booking Endpoints
**File**: `app/api/v1/endpoints/booking.py`  
**Current**: 14% (387 lines uncovered)  
**Target**: 60%+  
**Impact**: +20% overall coverage (HUGE)

Tests to add:
1. Online booking creation
2. Availability checking
3. Booking confirmation
4. Booking cancellation
5. Booking settings management
6. Public booking endpoints

### Phase 4: Communications Endpoints
**File**: `app/api/v1/endpoints/communications.py`  
**Current**: 24% (189 lines uncovered)  
**Target**: 65%+  
**Impact**: +10% overall coverage

Tests to add:
1. Email sending
2. SMS sending
3. Notification management
4. Template management
5. Communication history

### Phase 5: Remaining Endpoints
- Appointments (41% → 70%): +4%
- Accounting (35% → 70%): +3%
- Insurance: +5%
- Payments: +5%

## Execution Order

1. **Day 1**: Auth tests (10% gain)
2. **Day 2**: Booking tests (20% gain) - HUGE IMPACT
3. **Day 3**: Billing tests (8% gain)
4. **Day 4**: Communications tests (10% gain)
5. **Day 5**: Polish and remaining gaps

**Expected Result**: 56% + 48% = **104%** (realistically 75-80% due to overlaps)

## Next Steps

1. Start with `tests/test_auth_comprehensive.py`
2. Then `tests/test_booking_comprehensive.py` (biggest impact)
3. Then `tests/test_billing_comprehensive.py`
4. Then `tests/test_communications_comprehensive.py`
5. Run coverage after each file to track progress

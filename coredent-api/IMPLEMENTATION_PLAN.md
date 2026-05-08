# Implementation Plan - Reaching 68% Coverage

## Current Status
- **Coverage**: 55.97%
- **Target**: 68%
- **Gap**: -12.03%
- **Tests**: 97 passing, 37 failing

## Analysis of Failing Tests

### Billing Tests (12 failing)
**Status**: ✅ **ENDPOINTS EXIST** - Just need minor fixes
- Endpoints are implemented
- Tests failing due to schema/field mismatches
- **Effort**: 2-4 hours
- **Impact**: +4% coverage

**Fixes Needed**:
1. Fix schema field names (subtotal vs total_amount)
2. Add missing response fields
3. Fix validation logic

### Booking Tests (25 failing)
**Status**: ⚠️ **PARTIALLY IMPLEMENTED** - Need completion
- Some endpoints exist but incomplete
- Missing public booking endpoints
- **Effort**: 1-2 days
- **Impact**: +8% coverage

**Fixes Needed**:
1. Complete booking page CRUD
2. Implement public booking creation
3. Add waitlist endpoints
4. Fix response schemas

### Auth Tests (5 failing)
**Status**: ✅ **MOSTLY IMPLEMENTED** - Minor gaps
- Login/logout working
- Token refresh needs CSRF fix
- Password reset partially implemented
- **Effort**: 4-6 hours
- **Impact**: +2% coverage

**Fixes Needed**:
1. Fix token refresh CSRF handling
2. Complete password reset flow
3. Add password strength validation

## Revised Implementation Plan

### Phase 1: Quick Wins (4-6 hours) - Target: +6% coverage

#### 1.1 Fix Billing Endpoints (2 hours)
- [ ] Fix invoice schema field names
- [ ] Add missing validation
- [ ] Fix payment creation logic
- [ ] Add refund endpoint stub
- [ ] Fix billing summary calculations

**Expected**: 12 tests pass → +4% coverage

#### 1.2 Fix Auth Endpoints (2 hours)
- [ ] Fix token refresh CSRF handling
- [ ] Complete password reset endpoint
- [ ] Add password strength validation
- [ ] Fix account lockout logic

**Expected**: 5 tests pass → +2% coverage

### Phase 2: Booking Endpoints (1-2 days) - Target: +8% coverage

#### 2.1 Complete Booking Page Management (4 hours)
- [ ] Fix booking page CRUD operations
- [ ] Add proper validation
- [ ] Fix response schemas
- [ ] Add error handling

#### 2.2 Implement Public Booking (4 hours)
- [ ] Add public booking creation endpoint
- [ ] Add availability checking
- [ ] Add email verification
- [ ] Add rate limiting

#### 2.3 Add Waitlist Endpoints (2 hours)
- [ ] Implement waitlist CRUD
- [ ] Add status management
- [ ] Add notifications

**Expected**: 25 tests pass → +8% coverage

### Phase 3: Verification (1 hour) - Confirm 68%+

- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Verify 68%+ achieved
- [ ] Document remaining gaps

## Total Effort Estimate

- **Phase 1**: 4-6 hours (Quick wins)
- **Phase 2**: 8-10 hours (Booking completion)
- **Phase 3**: 1 hour (Verification)
- **Total**: 13-17 hours (~2 days)

## Expected Outcome

- **Starting Coverage**: 55.97%
- **Phase 1 Gain**: +6% → 61.97%
- **Phase 2 Gain**: +8% → 69.97%
- **Final Coverage**: **~70%** ✅ (exceeds 68% target)

## Implementation Order

1. **Start**: Fix billing endpoints (highest business value, quickest win)
2. **Next**: Fix auth endpoints (security critical, quick win)
3. **Then**: Complete booking endpoints (largest impact)
4. **Finally**: Verify and document

## Success Criteria

- [ ] Coverage ≥ 68%
- [ ] All critical endpoint tests passing
- [ ] No regressions in existing tests
- [ ] Documentation updated

---

**Status**: 📋 READY TO START  
**Next Action**: Begin Phase 1.1 - Fix Billing Endpoints  
**Timeline**: 2 days to 70% coverage

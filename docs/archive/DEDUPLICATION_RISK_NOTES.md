# Code Deduplication - Risk Assessment & Mitigation

**Date:** 2026  
**Status:** Phase 2 Assessment Complete

---

## RISK MATRIX

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|-----------|
| Breaking API contracts | Low | High | Medium | Comprehensive testing, gradual rollout |
| Performance regression | Low | Medium | Low | Benchmarking before/after |
| Audit logging gaps | Medium | High | High | Decorator testing, audit trail verification |
| Over-abstraction | Medium | Medium | Medium | Code review, keep thin wrappers |
| Integration issues | Low | High | Medium | Integration tests, E2E tests |
| Maintenance complexity | Low | Medium | Low | Documentation, examples |

---

## DETAILED RISK ANALYSIS

### 1. API Service Factory Risk

**Risk:** Breaking existing API contracts or changing behavior

**Probability:** Low  
**Impact:** High (all services affected)  
**Severity:** Medium

**Mitigation:**
- ✅ Factory generates identical code to current services
- ✅ Thin wrappers maintain existing API surface
- ✅ Comprehensive unit tests for each service
- ✅ Integration tests verify API responses
- ✅ Gradual rollout (one service at a time)

**Testing Strategy:**
```typescript
// Before: appointmentsApi.ts
export const listAppointments = async (params?: AppointmentListParams) => {
  // ... manual implementation
};

// After: appointmentsApi.ts
export const appointmentsApi = createApiService<Appointment>('appointments');
export const listAppointments = appointmentsApi.list;

// Test: Verify identical behavior
test('listAppointments returns same result', async () => {
  const oldResult = await oldListAppointments({ page: 1 });
  const newResult = await newListAppointments({ page: 1 });
  expect(oldResult).toEqual(newResult);
});
```

---

### 2. React Query Hook Factory Risk

**Risk:** Hooks behave differently or lose functionality

**Probability:** Low  
**Impact:** High (all hooks affected)  
**Severity:** Medium

**Mitigation:**
- ✅ Factory generates identical hook code
- ✅ Thin wrappers maintain existing API surface
- ✅ Query key structure preserved
- ✅ Stale time and cache settings preserved
- ✅ Comprehensive hook tests

**Testing Strategy:**
```typescript
// Test: Verify hook behavior identical
test('useAppointments hook returns same data', async () => {
  const { result: oldResult } = renderHook(() => useOldAppointments());
  const { result: newResult } = renderHook(() => useNewAppointments());
  
  await waitFor(() => {
    expect(oldResult.current.data).toEqual(newResult.current.data);
  });
});

// Test: Verify cache invalidation works
test('useCreateAppointment invalidates cache', async () => {
  const { result } = renderHook(() => useCreateAppointment());
  
  act(() => {
    result.current.mutate({ /* data */ });
  });
  
  await waitFor(() => {
    expect(queryClient.getQueryData(['appointments'])).toBeUndefined();
  });
});
```

---

### 3. Base CRUD Endpoint Risk

**Risk:** Endpoints behave differently or lose functionality

**Probability:** Medium  
**Impact:** High (all endpoints affected)  
**Severity:** High

**Mitigation:**
- ✅ Mixin preserves all existing logic
- ✅ Endpoints inherit from mixin, don't replace
- ✅ Comprehensive endpoint tests
- ✅ Integration tests verify API responses
- ✅ Gradual rollout (one endpoint at a time)
- ✅ Parallel testing (old vs. new)

**Testing Strategy:**
```python
# Test: Verify list endpoint behavior identical
@pytest.mark.asyncio
async def test_list_patients_behavior_identical():
    # Old implementation
    old_response = await old_list_patients(db, practice_id, pagination)
    
    # New implementation using mixin
    new_response = await new_list_patients(db, practice_id, pagination)
    
    assert old_response.total == new_response.total
    assert len(old_response.items) == len(new_response.items)
    assert old_response.items[0].id == new_response.items[0].id

# Test: Verify filtering works
@pytest.mark.asyncio
async def test_list_patients_filtering():
    response = await list_patients(
        db, practice_id, pagination,
        filters={'status': 'active'}
    )
    
    assert all(p.status == 'active' for p in response.items)

# Test: Verify pagination works
@pytest.mark.asyncio
async def test_list_patients_pagination():
    response1 = await list_patients(db, practice_id, Pagination(page=1, limit=10))
    response2 = await list_patients(db, practice_id, Pagination(page=2, limit=10))
    
    assert response1.items[0].id != response2.items[0].id
```

---

### 4. Audit Logging Decorator Risk

**Risk:** Audit events not logged or logged incorrectly

**Probability:** Medium  
**Impact:** High (HIPAA compliance)  
**Severity:** High

**Mitigation:**
- ✅ Decorator preserves all audit logging
- ✅ Comprehensive audit logging tests
- ✅ Audit trail verification
- ✅ Gradual rollout with monitoring
- ✅ Fallback to manual logging if needed

**Testing Strategy:**
```python
# Test: Verify audit event logged
@pytest.mark.asyncio
async def test_audit_log_decorator():
    @audit_log("patient_viewed", "patient")
    async def get_patient(patient_id, current_user, db, request):
        return {"id": patient_id}
    
    result = await get_patient(
        patient_id="123",
        current_user=mock_user,
        db=mock_db,
        request=mock_request
    )
    
    # Verify audit event was logged
    audit_events = await db.execute(select(AuditLog))
    assert len(audit_events) > 0
    assert audit_events[-1].event_type == "patient_viewed"
    assert audit_events[-1].resource_id == "123"

# Test: Verify audit event contains correct data
@pytest.mark.asyncio
async def test_audit_log_contains_correct_data():
    # ... verify user_id, timestamp, resource_type, etc.
```

---

### 5. Form Validation Hook Risk

**Risk:** Validation errors not displayed or displayed incorrectly

**Probability:** Low  
**Impact:** Medium (UX issue)  
**Severity:** Low

**Mitigation:**
- ✅ Hook preserves all validation logic
- ✅ Comprehensive validation tests
- ✅ Component tests verify error display
- ✅ Gradual rollout (one component at a time)

**Testing Strategy:**
```typescript
// Test: Verify validation errors displayed
test('useFormValidation displays errors', async () => {
  const { result } = renderHook(() => useFormValidation(schema));
  
  act(() => {
    result.current.validate({ email: 'invalid' });
  });
  
  expect(result.current.errors.email).toBeDefined();
  expect(result.current.errors.email).toContain('Invalid email');
});

// Test: Verify validation passes for valid data
test('useFormValidation passes for valid data', async () => {
  const { result } = renderHook(() => useFormValidation(schema));
  
  const isValid = act(() => {
    return result.current.validate({ email: 'test@example.com' });
  });
  
  expect(isValid).toBe(true);
  expect(result.current.errors).toEqual({});
});
```

---

### 6. Generic Dialog Component Risk

**Risk:** Dialog behavior changes or loses functionality

**Probability:** Low  
**Impact:** Medium (UX issue)  
**Severity:** Low

**Mitigation:**
- ✅ Component preserves all dialog functionality
- ✅ Comprehensive component tests
- ✅ E2E tests verify dialog interactions
- ✅ Gradual rollout (one dialog at a time)

**Testing Strategy:**
```typescript
// Test: Verify dialog opens/closes
test('GenericDialog opens and closes', async () => {
  const { rerender } = render(
    <GenericDialog open={true} onOpenChange={jest.fn()} {...props} />
  );
  
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  
  rerender(
    <GenericDialog open={false} onOpenChange={jest.fn()} {...props} />
  );
  
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

// Test: Verify form submission
test('GenericDialog submits form', async () => {
  const onSubmit = jest.fn();
  render(
    <GenericDialog
      open={true}
      onOpenChange={jest.fn()}
      onSubmit={onSubmit}
      {...props}
    />
  );
  
  const submitButton = screen.getByRole('button', { name: /save/i });
  await userEvent.click(submitButton);
  
  expect(onSubmit).toHaveBeenCalled();
});
```

---

### 7. Cross-Stack Validation Risk

**Risk:** Validation logic diverges between frontend and backend

**Probability:** Low  
**Impact:** Medium (data integrity)  
**Severity:** Low

**Mitigation:**
- ✅ Shared validators module ensures consistency
- ✅ Comprehensive validation tests
- ✅ Integration tests verify frontend/backend agreement
- ✅ Documentation of validation rules

**Testing Strategy:**
```typescript
// Test: Verify frontend/backend validation agreement
test('frontend and backend validation agree', async () => {
  const testCases = [
    { email: 'valid@example.com', valid: true },
    { email: 'invalid', valid: false },
    { email: '', valid: false },
  ];
  
  for (const testCase of testCases) {
    // Frontend validation
    const frontendValid = isValidEmail(testCase.email);
    
    // Backend validation
    const backendValid = await validateEmailBackend(testCase.email);
    
    expect(frontendValid).toBe(testCase.valid);
    expect(backendValid).toBe(testCase.valid);
  }
});
```

---

## IMPLEMENTATION RISKS

### Risk 1: Over-Abstraction

**Description:** Creating too many layers of abstraction makes code harder to understand

**Probability:** Medium  
**Impact:** Medium (maintenance burden)  
**Severity:** Medium

**Mitigation:**
- ✅ Keep thin wrappers for each service/hook
- ✅ Avoid 3+ levels of indirection
- ✅ Document factory patterns
- ✅ Code review for abstraction levels
- ✅ Provide examples for common use cases

**Example - Good Abstraction:**
```typescript
// Level 1: Factory (generic)
export function createApiService<T>(endpoint: string) { ... }

// Level 2: Wrapper (specific)
export const appointmentsApi = createApiService<Appointment>('appointments');

// Level 3: Usage (clear)
export const listAppointments = appointmentsApi.list;
```

**Example - Bad Abstraction (avoid):**
```typescript
// Too many levels
const factory = createFactory();
const builder = factory.createBuilder();
const service = builder.withEndpoint('appointments').build();
const api = service.getApi();
const list = api.getList();
```

---

### Risk 2: Performance Regression

**Description:** Factories or decorators add overhead

**Probability:** Low  
**Impact:** Low (minimal overhead)  
**Severity:** Low

**Mitigation:**
- ✅ Factories are zero-cost abstractions (compile-time)
- ✅ Decorators add minimal runtime overhead
- ✅ Benchmark before and after
- ✅ Monitor performance in production
- ✅ Optimize if needed

**Benchmarking Strategy:**
```typescript
// Before
console.time('listAppointments');
const result = await listAppointments({ page: 1 });
console.timeEnd('listAppointments');

// After
console.time('listAppointments');
const result = await appointmentsApi.list({ page: 1 });
console.timeEnd('listAppointments');

// Expected: No significant difference
```

---

### Risk 3: Integration Issues

**Description:** Factories/decorators don't work well with existing code

**Probability:** Low  
**Impact:** High (breaking changes)  
**Severity:** Medium

**Mitigation:**
- ✅ Comprehensive integration tests
- ✅ E2E tests verify full workflows
- ✅ Gradual rollout (one service at a time)
- ✅ Parallel testing (old vs. new)
- ✅ Rollback plan if needed

**Integration Testing Strategy:**
```typescript
// Test: Full workflow with new factory
test('full appointment booking workflow', async () => {
  // 1. List appointments
  const appointments = await appointmentsApi.list();
  
  // 2. Get appointment details
  const appointment = await appointmentsApi.get(appointments[0].id);
  
  // 3. Update appointment
  const updated = await appointmentsApi.update(appointment.id, { status: 'confirmed' });
  
  // 4. Verify changes persisted
  const refreshed = await appointmentsApi.get(appointment.id);
  expect(refreshed.status).toBe('confirmed');
});
```

---

## ROLLBACK PLAN

If issues arise during implementation:

1. **Immediate Rollback:** Revert to previous commit
2. **Partial Rollback:** Disable specific factory/decorator
3. **Feature Flags:** Use feature flags to toggle new implementations
4. **Gradual Rollout:** Roll back one service/endpoint at a time

**Rollback Checklist:**
- [ ] Identify issue
- [ ] Create incident ticket
- [ ] Revert changes
- [ ] Verify system stability
- [ ] Root cause analysis
- [ ] Fix and re-test
- [ ] Re-deploy with fixes

---

## MONITORING & OBSERVABILITY

### Metrics to Monitor

**Frontend:**
- API response times (no regression)
- Hook performance (no regression)
- Component render times (no regression)
- Error rates (no increase)
- User session duration (no decrease)

**Backend:**
- Endpoint response times (no regression)
- Database query times (no regression)
- Error rates (no increase)
- Audit log completeness (100%)
- Request throughput (no decrease)

### Monitoring Setup

```python
# Backend monitoring
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log metrics
    logger.info(f"Endpoint: {request.url.path}, Time: {process_time}s")
    
    return response

# Frontend monitoring
export function logMetric(name: string, value: number) {
  console.log(`Metric: ${name} = ${value}`);
  // Send to analytics service
}
```

---

## SUCCESS CRITERIA

✅ All tests passing (frontend + backend)  
✅ No performance regression (< 5% variance)  
✅ No broken imports or references  
✅ Code coverage maintained or improved  
✅ Audit logging 100% complete  
✅ Developer feedback positive  
✅ Documentation updated  
✅ No critical issues in production  

---

## CONTINGENCY PLANS

### If API Service Factory Fails
- Revert to manual services
- Keep factory for future use
- Document lessons learned

### If Hook Factory Fails
- Revert to manual hooks
- Keep factory for future use
- Document lessons learned

### If Base Endpoint Mixin Fails
- Revert to manual endpoints
- Keep mixin for future use
- Document lessons learned

### If Audit Logging Decorator Fails
- Revert to manual logging
- Keep decorator for future use
- Document lessons learned

---

## APPROVAL CHECKLIST

Before proceeding with implementation:

- [ ] Risk assessment reviewed and approved
- [ ] Mitigation strategies agreed upon
- [ ] Testing strategy approved
- [ ] Rollback plan documented
- [ ] Monitoring setup approved
- [ ] Team trained on new patterns
- [ ] Documentation prepared
- [ ] Stakeholder approval obtained

---

**Report Generated:** 2026  
**Status:** Ready for Implementation  
**Risk Level:** Medium (manageable with proper mitigation)  
**Recommended Approval:** Proceed with caution, follow mitigation strategies

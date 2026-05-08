# Test Fixes Status - May 5, 2026

## Progress Summary

### ✅ Completed
- Fixed all Invoice model field names in test fixtures:
  - `issue_date` → removed (doesn't exist)
  - `tax_amount` → `tax`
  - `total_amount` → `total`
  - `amount_paid` → removed (it's a property)
  - `balance_due` → removed (it's a property)
  - Added required `line_items` field to all Invoice creations

- Fixed all Payment model imports and added required `invoice_id` field

### 📊 Test Results
- **Before fixes**: 2/26 passing (7.7%)
- **After fixes**: 3/25 passing (12%)
- **Coverage**: 54.64% (target: 68%)

### ⚠️ Remaining Issues

#### 1. UUID Conversion Errors (Most Common)
**Error**: `'str' object has no attribute 'hex'`

**Affected Tests**: 16 tests failing with this error

**Root Cause**: The billing endpoints that deal with patient lookups are receiving string UUIDs but SQLAlchemy is trying to process them incorrectly.

**Example**:
```python
# In test
response = await client.get(f"/api/v1/billing/invoices/?patient_id={test_patient.id}")

# In endpoint (billing.py line 707, 734)
result = await db.execute(
    select(Patient).where(
        Patient.id == patient_id,  # patient_id is a string from URL
        Patient.practice_id == current_user.practice_id
    )
)
```

**Solution**: Convert string UUIDs to UUID objects in the endpoints:
```python
from uuid import UUID

# In endpoint
if isinstance(patient_id, str):
    patient_id = UUID(patient_id)
```

#### 2. Schema Validation Errors
**Error**: `2 validation errors for InvoiceListResponse`

**Affected Tests**: 2 tests
- `test_list_invoices_success`
- `test_list_invoices_with_status_filter`

**Root Cause**: The `InvoiceListResponse` schema expects different fields than what the endpoint returns.

**Solution**: Check the schema definition in `app/schemas/billing.py` and ensure it matches the endpoint response.

#### 3. Permission/Auth Errors
**Error**: `assert 403 in [200, 204, 404]`

**Affected Tests**: 2 tests
- `test_delete_invoice_success`
- `test_get_billing_summary_success`

**Root Cause**: The test user doesn't have permission to perform these actions, or the endpoints have additional auth checks.

**Solution**: Either:
- Add proper permissions to test user
- Update test expectations to accept 403
- Check endpoint auth requirements

#### 4. Missing Endpoint Implementation
**Error**: `assert 404 == 200`

**Affected Test**: `test_get_payment_by_id_success`

**Root Cause**: The GET `/api/v1/billing/payments/{payment_id}` endpoint might not be implemented or not returning payments correctly.

**Solution**: Check if the endpoint exists and is properly implemented in `billing.py`.

#### 5. Async/Greenlet Errors
**Error**: `greenlet_spawn has not been called`

**Affected Test**: `test_create_payment_success`

**Root Cause**: Mixing sync and async code incorrectly.

**Solution**: Ensure all database operations use `await` properly.

#### 6. JSON Serialization Error
**Error**: `Object of type Decimal is not JSON serializable`

**Affected Test**: `test_create_payment_invalid_amount`

**Root Cause**: Trying to send a Decimal object in JSON without converting to string.

**Solution**: Convert Decimal to string in test:
```python
payment_data = {
    "amount": "-50.00",  # String, not Decimal("-50.00")
}
```

## Next Steps (Priority Order)

### Step 1: Fix UUID Conversion (30 min)
This will fix 16 tests at once.

**File**: `coredent-api/app/api/v1/endpoints/billing.py`

**Changes needed**:
1. Add UUID import at top
2. In `list_payment_methods` (line ~707), convert patient_id:
   ```python
   if isinstance(patient_id, str):
       patient_id = UUID(patient_id)
   ```
3. In `delete_payment_method` (line ~734), convert patient_id and method_id
4. In any other endpoints that query by UUID from URL parameters

### Step 2: Fix Schema Validation (15 min)
**File**: `coredent-api/app/schemas/billing.py`

Check `InvoiceListResponse` schema and ensure it matches what the endpoint returns.

### Step 3: Fix JSON Serialization (5 min)
**File**: `coredent-api/tests/test_billing_comprehensive.py`

Line ~390 in `test_create_payment_invalid_amount`:
```python
payment_data = {
    "patient_id": str(test_patient.id),
    "amount": "-50.00",  # Change from Decimal to string
    "payment_method": "credit_card",
}
```

### Step 4: Investigate Missing Endpoint (15 min)
Check if GET `/api/v1/billing/payments/{payment_id}` exists and works.

### Step 5: Fix Auth Issues (20 min)
Either update test expectations or fix permissions.

## Expected Outcome After Fixes

- **Tests passing**: ~20/25 (80%)
- **Coverage increase**: +2-3% → ~57%
- **Time to complete**: 1.5 hours

## Coverage Path to 68%

Current: 54.64%
After billing fixes: ~57%
After auth tests: ~59%
After booking tests: ~68% ✅

**Total time remaining**: 8-10 hours

## Key Learnings

1. **Always check actual model definitions** before writing tests
2. **UUID handling** is critical - string vs UUID object matters
3. **Schema validation** must match endpoint responses exactly
4. **Auth/permissions** need to be set up correctly in tests
5. **Async/await** must be used consistently

## Files Modified Today

✅ `coredent-api/tests/test_billing_comprehensive.py` - Fixed all Invoice/Payment fixtures
✅ `coredent-api/app/models/billing.py` - Added new Payment fields
✅ `coredent-api/app/api/v1/endpoints/billing.py` - Implemented 8 new endpoints
✅ `coredent-api/app/schemas/billing.py` - Updated BillingSummary schema
✅ `coredent-api/alembic/versions/20260505_1400_add_payment_fields_for_billing.py` - Created migration

## Files That Need Fixes

⏳ `coredent-api/app/api/v1/endpoints/billing.py` - Add UUID conversions
⏳ `coredent-api/app/schemas/billing.py` - Fix InvoiceListResponse schema
⏳ `coredent-api/tests/test_billing_comprehensive.py` - Fix JSON serialization

---

**Status**: 🔧 **READY FOR NEXT FIXES**  
**Next Action**: Fix UUID conversion in billing endpoints  
**Time Needed**: 1.5 hours for all remaining billing fixes  
**Confidence**: HIGH (clear path forward)

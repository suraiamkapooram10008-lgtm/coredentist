# 📝 COMMENT STYLE GUIDE - CoreDent Codebase

**Date:** April 18, 2026  
**Version:** 1.0  
**Status:** ✅ APPROVED

---

## 📋 TABLE OF CONTENTS

1. [Philosophy](#philosophy)
2. [When to Write Comments](#when-to-write-comments)
3. [Comment Patterns to Avoid](#comment-patterns-to-avoid)
4. [TypeScript/JavaScript Standards](#typescriptjavascript-standards)
5. [Python Standards](#python-standards)
6. [Examples](#examples)

---

## 🎯 PHILOSOPHY

### Core Principle: Explain WHY, Not WHAT

**Code shows WHAT it does. Comments explain WHY it does it.**

```typescript
// BAD: Comment explains what code does (obvious)
// Set loading to true
setIsLoading(true);

// GOOD: Comment explains why (not obvious)
// Prevent multiple submissions while request is in flight
setIsLoading(true);
```

### Secondary Principle: Self-Documenting Code

**Write code that's clear enough to not need comments.**

```typescript
// BAD: Unclear code that needs explanation
const x = y > 5 ? z : w;

// GOOD: Clear code that doesn't need explanation
const shouldApplyDiscount = itemCount > 5;
const finalPrice = shouldApplyDiscount ? discountedPrice : regularPrice;
```

---

## ✅ WHEN TO WRITE COMMENTS

### 1. Explain Non-Obvious Business Logic

```typescript
// GOOD: Explains business rule
// HIPAA: Session timeout must be 15 minutes for healthcare systems
const SESSION_TIMEOUT_MINUTES = 15;
```

### 2. Document Complex Algorithms

```typescript
/**
 * Calculate treatment cost using insurance coverage and discounts.
 * 
 * Algorithm:
 * 1. Sum all procedure costs
 * 2. Apply insurance coverage percentage
 * 3. Apply practice discounts
 * 4. Apply patient-specific discounts
 * 5. Round to nearest cent
 */
function calculateTreatmentCost(procedures, insurance, discounts) {
  // ...
}
```

### 3. Explain Workarounds and Hacks

```typescript
// WORKAROUND: SQLite doesn't support UUID type natively
// We store UUIDs as TEXT and cast to UUID for comparisons
const query = `SELECT * FROM users WHERE CAST(id AS TEXT) = ?`;
```

### 4. Document Security/Compliance Decisions

```python
# SECURITY: Use constant-time comparison to prevent timing attacks
if not hmac.compare_digest(signature, expected_signature):
    raise InvalidSignatureError()
```

### 5. Clarify Surprising Behavior

```typescript
// NOTE: This returns a Promise even though it looks synchronous
// The actual file I/O happens in the background
const result = readFileAsync(path);
```

### 6. Mark Important Sections

```python
# ============================================
# CRITICAL: Payment Processing
# ============================================
# This section handles real money transactions.
# Changes here require thorough testing and code review.
```

---

## ❌ COMMENT PATTERNS TO AVOID

### 1. Obvious Comments

```typescript
// BAD: Obvious - remove it
// Get user by ID
const user = await getUser(id);

// GOOD: No comment needed
const user = await getUser(id);
```

### 2. Commented-out Code

```typescript
// BAD: Dead code - remove it
// const oldImplementation = () => {
//   // ... 50 lines of old code
// };

// GOOD: Remove it (it's in git history)
// If you need it later, git log will have it
```

### 3. Redundant Comments

```typescript
// BAD: Redundant - code already shows this
// Loop through all users
for (const user of users) {
  // ...
}

// GOOD: No comment needed
for (const user of users) {
  // ...
}
```

### 4. Outdated Comments

```typescript
// BAD: Outdated - misleads developers
// This function is slow and needs optimization
// TODO: Optimize this function (added 2 years ago, never done)
function slowFunction() {
  // ...
}

// GOOD: Remove or update
// This function is O(n²) due to nested loops
// TODO: Optimize to O(n log n) using sorting (Priority: Medium, Effort: 4 hours)
function slowFunction() {
  // ...
}
```

### 5. Vague Comments

```typescript
// BAD: Vague - doesn't explain anything
// Handle edge case
if (value === null) {
  // ...
}

// GOOD: Specific - explains the edge case
// Handle null values from optional API fields
if (value === null) {
  // ...
}
```

---

## 📘 TYPESCRIPT/JAVASCRIPT STANDARDS

### JSDoc Format

```typescript
/**
 * Brief description of what the function does.
 * 
 * Longer description if needed. Explain the algorithm, edge cases,
 * or important behavior that isn't obvious from the code.
 * 
 * @param paramName - Description of parameter
 * @param anotherParam - Description of another parameter
 * @returns Description of return value
 * @throws ErrorType - Description of when this error is thrown
 * 
 * @example
 * const result = myFunction(value1, value2);
 * console.log(result); // Output: ...
 * 
 * @see {@link relatedFunction} for similar functionality
 */
export function myFunction(paramName: string, anotherParam: number): string {
  // ...
}
```

### Inline Comments

```typescript
// Use for explaining WHY, not WHAT
// Prevent race condition by checking version before update
if (currentVersion === expectedVersion) {
  await updateRecord(record);
}
```

### Block Comments

```typescript
// ============================================
// Section Name
// ============================================
// Use for organizing large sections of code

// Subsection
// Use for organizing within sections
```

---

## 🐍 PYTHON STANDARDS

### Docstring Format (Google Style)

```python
def calculate_treatment_cost(procedures: List[Procedure], 
                            insurance: Insurance,
                            discounts: List[Discount]) -> Decimal:
    """
    Calculate the total cost of a treatment plan including insurance coverage.
    
    This function applies insurance coverage and discounts in the correct order
    to calculate the patient's out-of-pocket cost.
    
    Args:
        procedures: List of procedures in the treatment plan
        insurance: Patient's insurance information
        discounts: Applicable discounts (practice and patient-specific)
        
    Returns:
        Total out-of-pocket cost for the patient, rounded to nearest cent
        
    Raises:
        ValueError: If procedures list is empty
        InvalidInsuranceError: If insurance coverage is invalid
        
    Example:
        >>> procedures = [Procedure(code='D0120', fee=150)]
        >>> insurance = Insurance(coverage=0.8)
        >>> cost = calculate_treatment_cost(procedures, insurance, [])
        >>> cost
        Decimal('30.00')
        
    Note:
        Insurance coverage is applied before discounts to ensure
        discounts are calculated on the patient's responsibility.
    """
    # Implementation
```

### Inline Comments

```python
# Use for explaining WHY, not WHAT
# HIPAA: Audit all access to patient PHI
logger.info(f"User {user_id} accessed patient {patient_id}")
```

---

## 💡 EXAMPLES

### Example 1: Good Comment - Explains Business Logic

```typescript
/**
 * Validate appointment time against practice working hours.
 * 
 * Checks if the requested appointment time falls within the practice's
 * operating hours for the given day, accounting for lunch breaks and
 * special closures.
 * 
 * @param appointmentTime - Requested appointment time
 * @param practiceId - ID of the practice
 * @returns true if time is valid, false otherwise
 */
async function isValidAppointmentTime(
  appointmentTime: Date,
  practiceId: string
): Promise<boolean> {
  // Get practice working hours
  const practice = await getPractice(practiceId);
  
  // Check if day is closed
  if (practice.closedDays.includes(appointmentTime.getDay())) {
    return false;
  }
  
  // Check if time is within working hours
  const hour = appointmentTime.getHours();
  return hour >= practice.openingHour && hour < practice.closingHour;
}
```

### Example 2: Good Comment - Explains Workaround

```python
# WORKAROUND: SQLite doesn't support UUID type natively
# We store UUIDs as TEXT and cast to UUID for comparisons
# This is a limitation of SQLite; PostgreSQL handles this natively
def get_user_by_id(user_id: str) -> Optional[User]:
    # Cast to TEXT for SQLite compatibility
    query = select(User).where(cast(User.id, String) == user_id)
    return db.execute(query).scalar_one_or_none()
```

### Example 3: Good Comment - Explains Security Decision

```typescript
// SECURITY: Use constant-time comparison to prevent timing attacks
// Regular string comparison (===) takes longer for longer matching prefixes,
// which could leak information about valid tokens
if (!crypto.timingSafeEqual(token, expectedToken)) {
  throw new UnauthorizedError();
}
```

### Example 4: Good Comment - Explains Edge Case

```python
def process_payment(payment: Payment) -> PaymentResult:
    """Process a payment transaction."""
    
    # Handle edge case: Some payment gateways return success but don't
    # immediately update their API. Wait briefly before checking status.
    # This prevents false "payment not found" errors.
    time.sleep(0.5)
    
    status = check_payment_status(payment.id)
    return PaymentResult(status=status)
```

### Example 5: Bad Comment - Obvious

```typescript
// BAD: Obvious comment - remove it
// Set user to null
user = null;

// GOOD: No comment needed
user = null;
```

### Example 6: Bad Comment - Outdated

```typescript
// BAD: Outdated TODO - misleads developers
// TODO: Optimize this function (added 3 years ago, never done)
function slowFunction() {
  // ...
}

// GOOD: Clear TODO with priority and effort
// TODO: Optimize from O(n²) to O(n log n) (Priority: Low, Effort: 4 hours)
// Current implementation uses nested loops which is slow for large datasets
function slowFunction() {
  // ...
}
```

---

## 📋 CHECKLIST FOR CODE REVIEW

When reviewing comments, check:

- [ ] Comments explain WHY, not WHAT
- [ ] No obvious comments (code is self-documenting)
- [ ] No commented-out code
- [ ] No outdated comments
- [ ] Public functions have JSDoc/docstrings
- [ ] Complex algorithms are documented
- [ ] Security/compliance decisions are explained
- [ ] Edge cases are clarified
- [ ] TODOs have priority and effort estimates
- [ ] Examples are provided for complex functions

---

## 🚀 IMPLEMENTATION

### For New Code
- Write JSDoc/docstrings for all public functions
- Add inline comments only to explain WHY
- Remove obvious comments before committing

### For Existing Code
- Add JSDoc/docstrings to undocumented public functions
- Remove obvious comments
- Remove commented-out code
- Update outdated comments

### For Code Review
- Enforce this style guide
- Request improvements to comments
- Approve only when comments meet standards

---

## 📞 QUESTIONS?

If you have questions about this style guide:
1. Check the examples above
2. Ask in code review
3. Update this guide if needed

---

**Generated:** April 18, 2026  
**Project:** CoreDent SaaS Platform  
**Status:** ✅ APPROVED


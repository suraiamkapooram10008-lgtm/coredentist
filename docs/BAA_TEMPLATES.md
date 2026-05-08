# Business Associate Agreements (BAA) — CoreDent PMS

## Overview
Under HIPAA, CoreDent is a **Covered Entity** (or Business Associate if reselling). Any vendor that handles PHI on your behalf must sign a BAA.

## Required BAAs

### 1. Railway (Hosting Infrastructure)
**Contact**: support@railway.app or via Dashboard → Settings → Compliance  
**Template**: Use their standard BAA or yours below.

### 2. Stripe / Razorpay (Payment Processing)
- **Stripe**: https://stripe.com/guides/pci-dss-and-hipaa → Request BAA via support
- **Razorpay**: Contact enterprise@razorpay.com for India BAA

### 3. SendGrid / AWS SES (Email)
- **SendGrid**: Available on Pro+ plans — contact support
- **AWS SES**: Covered under AWS BAA (sign once for all AWS services)

### 4. Sentry (Error Tracking)
**Contact**: https://sentry.io/security/ → Business tier required for BAA

### 5. Twilio (SMS — if enabled)
**Contact**: https://www.twilio.com/legal/business-associate-agreement

---

## BAA Template (CoreDent → Vendor)

```
BUSINESS ASSOCIATE AGREEMENT

This Business Associate Agreement ("BAA") is entered into between:
- Covered Entity: [Your Practice Name / CoreDent LLC]
- Business Associate: [Vendor Name]

1. PERMITTED USES AND DISCLOSURES
   Business Associate may only use PHI to provide services to Covered Entity
   as specified in the underlying service agreement.

2. SAFEGUARDS
   Business Associate shall implement Administrative, Physical, and Technical
   safeguards consistent with 45 CFR 164.312 to protect PHI.

3. REPORTING
   Business Associate shall report any Security Incident or Breach to Covered
   Entity within 24 hours of discovery.

4. SUBCONTRACTORS
   Business Associate shall ensure any subcontractors sign equivalent BAAs.

5. TERMINATION
   Upon termination, Business Associate shall return or destroy all PHI within
   30 days and provide written certification.

6. AUDIT RIGHTS
   Covered Entity reserves the right to audit Business Associate's compliance
   with this BAA annually or upon reasonable notice.

Signed: _________________    Date: _______________
[Vendor Representative]

Signed: _________________    Date: _______________
[Covered Entity Representative]
```

---

## Action Items
- [ ] Request BAA from Railway
- [ ] Request BAA from Stripe (or Razorpay)
- [ ] Sign AWS BAA (covers SES, S3)
- [ ] Request BAA from Sentry
- [ ] Request BAA from Twilio (if using SMS)
- [ ] File all signed BAAs in `/docs/compliance/baas/`

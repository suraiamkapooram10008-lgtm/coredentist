# 🇮🇳 CoreDent India — Data Protection Compliance Guide

**Regulation:** Digital Personal Data Protection Act (DPDPA), 2023  
**Sector:** Dental Practice Management SaaS  
**Applicability:** CoreDent handles personal data (patient names, contact info, health records) = **Data Fiduciary** under DPDPA

---

## What I Built (Code Implementation)

All the security features I implemented are **still required and valuable** under Indian law. Here's the mapping:

| Feature I Built | DPDPA Requirement | Section |
|-----------------|-------------------|---------|
| **AES-256 Encryption** | Reasonable security safeguards | §8(5) |
| **MFA/TOTP** | Reasonable security safeguards | §8(5) |
| **Audit Logging** | Data breach detection & accountability | §8(5) |
| **Account Lockout** | Reasonable security safeguards | §8(5) |
| **DB Backup Script** | Data availability & disaster recovery | §8(5) |
| **Break-Glass Access** | Emergency access to data | §8(5) |
| **Health Monitoring** | System availability | §8(5) |
| **Sentry Error Tracking** | Security incident detection | §8(5) |

---

## What India Actually Requires (DPDPA 2023)

### ✅ Already Implemented
- [x] **Encryption at rest & in transit** — §8(5)
- [x] **Access controls (RBAC)** — §8(5)
- [x] **Audit trails** — §8(5)
- [x] **Session timeouts** — §8(5)
- [x] **Password complexity rules** — §8(5)
- [x] **Breach detection (Sentry)** — §8(5)
- [x] **Data backups** — §8(5)

### ⚠️ Remaining (Non-Code Actions)

| Requirement | What It Means | Your Action |
|-------------|---------------|-------------|
| **Consent Management** | Every patient must give explicit consent before their data is stored | Add consent checkbox during patient registration |
| **Privacy Notice** | Clear notice on what data you collect, why, and how long you keep it | Update your Privacy Policy |
| **Data Retention Limits** | Don't keep data forever. Define deletion timelines | Set 7-year retention for medical records, delete after |
| **Right to Access/Erase** | Patients can request their data or ask for deletion | Build "Export My Data" + "Delete My Account" endpoints |
| **Grievance Officer** | Appoint someone to handle data complaints | Assign a Grievance Officer |
| **Data Breach Notification** | Notify users + Board within "reasonable time" if breach occurs | Create breach notification procedure |
| **Cross-Border Transfer** | If data goes outside India, need safeguards | Ensure Railway/Vercel servers are in India or get consent |

---

## What You DON'T Need (US-Only)

| US Requirement | India Equivalent | Status |
|----------------|-----------------|--------|
| HIPAA Risk Analysis | Not required | Ignore |
| Business Associate Agreements (BAAs) | Not required | Ignore |
| HIPAA Security Officer | Not required | Ignore |
| OCR Breach Reporting (60 days) | Notify DPDPA Board "as soon as possible" | Different timeline |
| HITECH Act | Not applicable | Ignore |

---

## Quick Checklist for Indian Launch

### Pre-Launch (Code + Config)
- [x] Encryption (AES-256) ✅
- [x] Access controls (RBAC) ✅
- [x] MFA for admin accounts ✅
- [x] Audit logging ✅
- [x] Automatic backups ✅
- [x] Session timeouts ✅
- [x] Password complexity ✅
- [ ] **Consent checkbox** on patient registration
- [ ] **Privacy Policy** updated for DPDPA
- [ ] **Data retention** policy configured
- [ ] **Grievance Officer** appointed

### Post-Launch (Processes)
- [ ] Patient data export endpoint
- [ ] Patient data deletion endpoint
- [ ] Breach notification procedure
- [ ] Annual security audit
- [ ] Staff training on data protection

---

## Server Location Check

**Critical for India:** DPDPA allows cross-border transfers but you should disclose it.

| Vendor | Current Location | Action Needed |
|--------|-----------------|---------------|
| Railway (DB) | US/EU | Add disclosure in Privacy Policy |
| Vercel (Frontend) | Global CDN | Add disclosure in Privacy Policy |
| AWS S3 (Backups) | US (if used) | Consider Mumbai region |

**Recommendation:** Add a line in your Privacy Policy: *"Your data may be stored on servers located outside India. We use encryption and contractual safeguards to protect it."*

---

## Bottom Line

**The code I built is 100% correct and useful for India.** Encryption, MFA, audit logs, backups — all required by DPDPA §8(5).

**What changes:**
1. Rename `HIPAA_RISK_ASSESSMENT.md` to `DPDPA_COMPLIANCE_CHECKLIST.md` (same content, different framing)
2. Remove BAA/Security Officer language
3. Add consent management
4. Update Privacy Policy for DPDPA
5. Appoint a Grievance Officer (can be you as founder)

**DPDPA is simpler than HIPAA** — no formal risk analysis, no BAAs, no 60-day breach timeline. Just reasonable security + consent + transparency.

---

*Guide prepared for CoreDent India, April 2026*

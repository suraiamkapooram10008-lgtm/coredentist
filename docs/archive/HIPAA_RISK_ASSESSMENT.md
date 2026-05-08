# 🏥 CoreDent SaaS — HIPAA Risk Assessment (2026)

**Assessment Date:** April 24, 2026  
**Assessor:** Senior Security Consultant  
**Scope:** CoreDent Dental Practice Management SaaS — Backend + Frontend  
**Regulation:** 45 CFR Parts 160, 162, 164 (HIPAA Privacy, Security, Breach Notification Rules)  
**Risk Rating:** MEDIUM — *Ready for remediation sprint before PHI handling*

---

## 📊 Executive Summary

| Domain | Status | Risk | Priority |
|--------|--------|------|----------|
| **Administrative Safeguards** | 65% Complete | Medium | High |
| **Physical Safeguards** | 40% Complete | High | Medium |
| **Technical Safeguards** | 75% Complete | Low | High |
| **Organizational Requirements** | 50% Complete | Medium | Medium |
| **Policies & Procedures** | 60% Complete | Medium | High |

**Overall HIPAA Readiness: 58%** — *Substantial progress, requires focused sprint*

---

## 🔒 1. Administrative Safeguards (§ 164.308)

### 1.1 Security Management Process

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Risk Analysis (a)(1)(ii)(A) | ⚠️ PARTIAL | Code audit done, no formal risk register | **Need documented risk analysis report** |
| Risk Management (a)(1)(ii)(B) | ⚠️ PARTIAL | Security fixes implemented | **Need risk management plan with timelines** |
| Sanction Policy (a)(1)(ii)(C) | ❌ MISSING | No employee sanction policy in repo | **Create sanction policy for violations** |
| Information System Activity Review (a)(1)(ii)(D) | ✅ IMPLEMENTED | Audit logging middleware | Review logs quarterly |

### 1.2 Assigned Security Responsibilities

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Security Officer (a)(2) | ⚠️ PARTIAL | No named Security Officer in docs | **Assign Security Officer role** |

### 1.3 Workforce Security

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Authorization & Supervision (a)(3)(ii)(A) | ✅ IMPLEMENTED | RBAC (owner/admin/dentist/hygienist/front_desk) | Document workforce clearance |
| Workforce Clearance (a)(3)(ii)(B) | ⚠️ PARTIAL | No background check policy | **Add background check policy** |
| Termination Procedures (a)(3)(ii)(C) | ❌ MISSING | No termination SOP | **Create account deactivation SOP** |

### 1.4 Information Access Management

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Access Authorization (a)(4)(ii)(A) | ✅ IMPLEMENTED | Role-based access control | Document access request workflow |
| Access Establishment/Modification (a)(4)(ii)(B) | ✅ IMPLEMENTED | User CRUD endpoints | Document change request process |
| Access Termination (a)(4)(ii)(C) | ✅ IMPLEMENTED | `is_active` flag on users | Automate termination triggers |

### 1.5 Security Awareness & Training

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Security Reminders (a)(5)(ii)(A) | ❌ MISSING | No training program | **Implement annual security training** |
| Protection from Malicious Software (a)(5)(ii)(B) | ⚠️ PARTIAL | No endpoint protection docs | **Add antivirus/EDR requirement** |
| Log-in Monitoring (a)(5)(ii)(C) | ✅ IMPLEMENTED | Failed login tracking + lockout | Monitor and alert on anomalies |
| Password Management (a)(5)(ii)(D) | ✅ IMPLEMENTED | Password complexity rules, bcrypt | Enforce 90-day rotation |

### 1.6 Security Incident Procedures

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Response & Reporting (a)(6)(ii) | ⚠️ PARTIAL | Sentry for error tracking, audit logs | **Create incident response playbook** |

### 1.7 Contingency Plan

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Data Backup Plan (a)(7)(ii)(A) | ⚠️ PARTIAL | No automated backup documented | **Implement daily DB backups** |
| Disaster Recovery Plan (a)(7)(ii)(B) | ❌ MISSING | No DR plan in repo | **Create DR runbook** |
| Emergency Mode Operation (a)(7)(ii)(C) | ❌ MISSING | No emergency access procedure | **Define break-glass access** |
| Testing & Revision (a)(7)(ii)(D) | ❌ MISSING | No testing schedule | **Quarterly DR drills** |
| Applications & Data Criticality (a)(7)(ii)(E) | ⚠️ PARTIAL | No formal BIA | **Conduct Business Impact Analysis** |

### 1.8 Evaluation

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Periodic Technical Evaluation (a)(8) | ⚠️ PARTIAL | Manual code reviews | **Annual penetration test** |

### 1.9 Business Associate Contracts

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Written Contracts (a)(1) | ⚠️ PARTIAL | BAA templates exist in `docs/BAA_TEMPLATES.md` | **Execute BAAs with all vendors** |

---

## 🏢 2. Physical Safeguards (§ 164.310)

> **Note:** Physical safeguards primarily apply to the hosting infrastructure (Railway, Vercel). CoreDent is responsible for ensuring its vendors meet these requirements.

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Facility Access Controls (a) | ⚠️ PARTIAL | Railway SOC 2 Type II | **Verify Railway physical security cert** |
| Workstation Use (b) | ❌ N/A | SaaS product — user responsibility | Provide guidance to practices |
| Workstation Security (c) | ❌ N/A | SaaS product — user responsibility | Provide guidance to practices |
| Device & Media Controls (d) | ⚠️ PARTIAL | No media disposal policy | **Add media sanitization policy** |

**Vendor Compliance Checklist:**
- [ ] Railway: SOC 2 Type II, ISO 27001
- [ ] Vercel: SOC 2 Type II
- [ ] Stripe: PCI DSS Level 1, SOC 1/2
- [ ] AWS S3: SOC 2 Type II (if used for documents)

---

## 💻 3. Technical Safeguards (§ 164.312)

### 3.1 Access Control

| Requirement | Status | Implementation | Gap |
|-------------|--------|----------------|-----|
| Unique User Identification (a)(2)(i) | ✅ IMPLEMENTED | UUID-based user IDs + email | — |
| Emergency Access Procedure (a)(2)(ii) | ❌ MISSING | No break-glass admin | **Add emergency access account** |
| Automatic Logoff (a)(2)(iii) | ✅ IMPLEMENTED | 15-min session timeout config | Enforce via middleware |
| Encryption & Decryption (a)(2)(iv) | ✅ IMPLEMENTED | AES-256 field-level encryption | Verify key rotation policy |

### 3.2 Audit Controls

| Requirement | Status | Implementation | Gap |
|-------------|--------|----------------|-----|
| Audit Controls (b) | ✅ IMPLEMENTED | Audit logging middleware + DB logging | Add log integrity verification |

**Audit Log Coverage:**
| Event | Logged | Location |
|-------|--------|----------|
| User login/logout | ✅ | Application logs |
| Patient data access | ✅ | Audit middleware |
| Failed authentication | ✅ | Security middleware |
| Data modification | ✅ | Audit middleware |
| Admin actions | ⚠️ | Partial — needs expansion |
| Report generation | ❌ | **Add logging** |
| Data export | ❌ | **Add logging** |

### 3.3 Integrity

| Requirement | Status | Implementation | Gap |
|-------------|--------|----------------|-----|
| Mechanism to Authenticate ePHI (c)(1) | ⚠️ PARTIAL | DB-level integrity | **Add checksums for critical records** |
| Electronic Signature (c)(2) | ❌ MISSING | No e-signature for records | **Evaluate need for e-signature** |

### 3.4 Person or Entity Authentication

| Requirement | Status | Implementation | Gap |
|-------------|--------|----------------|-----|
| Authentication (d) | ✅ IMPLEMENTED | JWT with refresh tokens, bcrypt | Add MFA support |

### 3.5 Transmission Security

| Requirement | Status | Implementation | Gap |
|-------------|--------|----------------|-----|
| Integrity Controls (e)(1) | ✅ IMPLEMENTED | HTTPS/TLS for all traffic | — |
| Encryption (e)(2)(i) | ✅ IMPLEMENTED | TLS 1.2+ required | Enforce TLS 1.3 |
| Encryption (e)(2)(ii) | ✅ IMPLEMENTED | AES-256 at rest | Document key management |

---

## 📋 4. Organizational Requirements (§ 164.314)

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Business Associate Contracts (a) | ⚠️ PARTIAL | Templates exist, not executed | **Execute BAAs with all vendors** |
| Requirements for Group Health Plans (b) | N/A | Not applicable | — |

---

## 📄 5. Policies & Procedures & Documentation (§ 164.316)

| Requirement | Status | Evidence | Gap |
|-------------|--------|----------|-----|
| Policies & Procedures (a) | ⚠️ PARTIAL | Security audit checklist exists | **Formalize all policies** |
| Documentation (b) | ⚠️ PARTIAL | Code docs, no formal policy docs | **Create policy repository** |
| Time Limit (b)(1) | ❌ MISSING | No retention schedule | **Define 6-year retention** |
| Availability (b)(2) | ❌ MISSING | No policy distribution system | **Distribute to workforce** |
| Updates (b)(3) | ❌ MISSING | No review schedule | **Annual policy review** |

---

## 🔴 Critical Gaps Requiring Immediate Action

### CRITICAL-1: No Business Associate Agreements Executed
**Risk:** If CoreDent handles PHI without BAAs with Railway, Vercel, Stripe, and other vendors, both CoreDent and its customers are in violation of HIPAA.

**Remediation:**
1. Execute BAA with Railway (infrastructure)
2. Execute BAA with Vercel (frontend hosting)
3. Execute BAA with Stripe (payment processing)
4. Execute BAA with AWS (if S3 used for PHI documents)
5. Document all sub-processors in a public sub-processor list

**Effort:** 2-3 days  
**Owner:** Legal/Compliance  
**Timeline:** Before first PHI is stored

---

### CRITICAL-2: No Formal Risk Analysis Document
**Risk:** HIPAA requires a documented risk analysis. Without it, OCR can impose penalties regardless of actual security posture.

**Remediation:**
Create a formal HIPAA Risk Analysis document including:
1. Inventory of all systems handling PHI
2. Threat identification (natural, human, environmental)
3. Vulnerability assessment
4. Risk scoring (likelihood × impact)
5. Risk mitigation plan with timelines
6. Residual risk acceptance

**Effort:** 1-2 days  
**Owner:** Security Officer + Development Team  
**Timeline:** Week 1

---

### CRITICAL-3: No Disaster Recovery / Business Continuity Plan
**Risk:** Extended downtime during a disaster could compromise patient care and result in data loss.

**Remediation:**
1. Daily automated PostgreSQL backups (pg_dump → S3)
2. Point-in-time recovery enabled
3. Documented RTO (Recovery Time Objective): 4 hours
4. Documented RPO (Recovery Point Objective): 1 hour
5. Quarterly DR drill

**Effort:** 1-2 days  
**Owner:** DevOps  
**Timeline:** Week 1-2

---

### CRITICAL-4: No Multi-Factor Authentication (MFA)
**Risk:** Password-only authentication is insufficient for PHI access. Compromised passwords = breached PHI.

**Remediation:**
1. Implement TOTP-based MFA (Google Authenticator, Authy)
2. Require MFA for all admin/owner accounts
3. Encourage MFA for dentist accounts
4. Log all MFA enrollment/reset events

**Effort:** 3-5 days  
**Owner:** Backend Developer  
**Timeline:** Week 2-3

---

## 🟡 Medium Priority Gaps

### MEDIUM-1: Missing Security Officer Assignment
**Remediation:** Assign a named Security Officer (can be CTO or founder initially). Document responsibilities.

### MEDIUM-2: No Workforce Security Training
**Remediation:** Implement annual HIPAA security training for all employees with access to production.

### MEDIUM-3: No Formal Incident Response Playbook
**Remediation:** Create incident response playbook with:
- Detection procedures
- Containment steps
- Notification timelines (60 days for breaches >500 individuals)
- OCR reporting procedures

### MEDIUM-4: No Emergency Access (Break-Glass) Procedure
**Remediation:** Create a break-glass admin account that:
- Requires two-person authorization
- Logs all actions
- Automatically disables after 24 hours
- Alerts Security Officer on activation

---

## 🟢 Low Priority / Already Implemented

| Control | Implementation |
|---------|---------------|
| Unique User IDs | UUID + email |
| Role-Based Access | 5-tier RBAC |
| Automatic Logoff | 15-min timeout |
| Encryption at Rest | AES-256 |
| Encryption in Transit | TLS 1.2+ |
| Audit Logging | Middleware + DB |
| Account Lockout | 5 failed attempts |
| Password Complexity | 12+ chars, mixed case, digits, special |
| PHI Redaction in Logs | Sentry filter + middleware |
| CSRF Protection | Token-based |
| Rate Limiting | Per-endpoint limits |
| Security Headers | HSTS, CSP, X-Frame-Options |

---

## 📋 HIPAA Compliance Checklist

### Pre-Launch (Must Complete)
- [ ] Execute BAAs with all vendors
- [ ] Complete formal Risk Analysis document
- [ ] Assign Security Officer
- [ ] Implement automated daily backups
- [ ] Create Disaster Recovery runbook
- [ ] Implement MFA for admin accounts
- [ ] Create Incident Response playbook

### Month 1 Post-Launch
- [ ] Conduct workforce HIPAA training
- [ ] Implement break-glass emergency access
- [ ] Set up log integrity monitoring
- [ ] Document data retention policy (6 years)
- [ ] Create breach notification procedure

### Month 2-3 Post-Launch
- [ ] Annual penetration test
- [ ] Quarterly access review
- [ ] Quarterly DR drill
- [ ] Policy review and update cycle

---

## 💰 Estimated Penalties for Non-Compliance

| Violation Category | Fine per Violation | Annual Max |
|-------------------|-------------------|------------|
| Tier 1: Unknowing | $137 - $68,928 | $68,928 |
| Tier 2: Reasonable Cause | $1,379 - $68,928 | $68,928 |
| Tier 3: Willful Neglect (Corrected) | $13,785 - $68,928 | $68,928 |
| Tier 4: Willful Neglect (Not Corrected) | $68,928 - $2,067,813 | $2,067,813 |

**CoreDent Current Risk Exposure:** Tier 2-3 (reasonable cause to willful neglect for missing BAAs and risk analysis)

---

## ✅ Verdict

**CoreDent has a strong technical foundation for HIPAA compliance.** The encryption, access controls, and audit logging are well-implemented. However, the **administrative and organizational safeguards are incomplete** — specifically BAAs, risk analysis, and disaster recovery.

**Recommendation:** Complete the 6 pre-launch items above before handling any PHI in production. The technical controls are solid; the compliance documentation needs work.

**Estimated time to full HIPAA compliance: 2-3 weeks of focused effort.**

---

*Assessment completed by Senior Security Consultant, April 24, 2026.*

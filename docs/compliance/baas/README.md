# Business Associate Agreements (BAA) Directory

This directory stores signed Business Associate Agreements required under HIPAA.

## Required BAAs

| Vendor | Service | Status | Requested | Signed | Expires | Notes |
|--------|---------|--------|-----------|--------|---------|-------|
| Railway | Hosting Infrastructure | ❌ Not Started | — | — | — | Contact support@railway.app |
| Stripe | Payment Processing (US) | ❌ Not Started | — | — | — | Request via Stripe Dashboard |
| Razorpay | Payment Processing (India) | ❌ Not Started | — | — | — | Contact enterprise@razorpay.com |
| AWS (SES/S3) | Email + Storage | ❌ Not Started | — | — | — | Sign AWS Enterprise BAA |
| Sentry | Error Tracking | ❌ Not Started | — | — | — | Business tier required |
| Twilio | SMS (if enabled) | ❌ Not Started | — | — | — | Sign via Twilio Console |

## File Naming Convention

```
BAA_<vendor-name>_<signed-date>.pdf
```

Example: `BAA_railway_2026-05-07.pdf`

## Priority Order (HIPAA Risk)

1. **Railway** — Hosting all PHI (highest risk)
2. **AWS** — Encrypted backups contain PHI
3. **Stripe/Razorpay** — Payment data (low PHI risk if PCI compliant)
4. **Sentry** — Error logs may contain PHI
5. **Twilio** — SMS contains appointment data (if used)

## Process

1. Contact vendor and request BAA
2. Review terms with legal/compliance
3. Sign and store PDF here
4. Update tracking status in `DISASTER_RECOVERY.md`
5. Set renewal reminder 30 days before expiry
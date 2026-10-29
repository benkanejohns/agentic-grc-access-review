# Identity and Access Management Policy (excerpt: access review controls)

**Policy ID:** IAM-POL-2.1
**Effective date:** 2026-01-01
**Owner:** CISO
**Review cadence:** Annually or on material change

This excerpt covers the clauses relevant to periodic user access review. It is not the complete policy.

## 4.1 Multi-factor authentication

Multi-factor authentication is mandatory for all production access, without exception. An account without MFA enabled is non-compliant regardless of privilege level or activity.

## 4.2 Inactive account review

User accounts with no recorded authentication activity (password login or access key use) for more than 90 days must be reviewed, and access revoked unless business justification is documented and approved by the account owner's manager.

## 4.3 Privileged account review

Accounts granted full administrative privileges are subject to a shorter inactivity threshold than clause 4.2: they must be reviewed for continued need after 30 days of inactivity, not 90.

## 5.1 Role alignment

Access grants must visibly align with the user's documented department and job function. A grant that does not align with the user's department must be treated as unexplained and escalated for review, regardless of activity recency.

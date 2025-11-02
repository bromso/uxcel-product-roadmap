# Epic to Issue Mapping

This document shows which child issues in Project #17 should be linked to which Epic in Project #18.

The script has already:
- ✅ Added all Epic issues to Project #17 (so they're available for linking)
- ✅ Identified all matching pairs

**Note:** The Parent issue field needs to be set manually in the GitHub UI because GitHub's API doesn't currently support setting PARENT_ISSUE field values programmatically.

## How to Link Manually

1. Go to: https://github.com/users/bromso/projects/17
2. Open each child issue
3. In the "Parent issue" field, select the matching Epic

## Mappings

### EPIC: Core Collaboration Loop
- Define core collaboration JTBD & success criteria
- User interviews: collaboration pain points (n=12)
- Value test: clickable prototype of comment/mention/resolve
- Collaborative doc primitives (create/edit/comment)

### EPIC: Analytics & Telemetry Baseline
- Event taxonomy v1 (activation, retention, performance)
- Integrate analytics SDK + env toggles
- Dashboard: Activation funnel + AHA rate

### EPIC: Real-time Sync & Offline Robustness
- Presence & cursors
- Offline queue & replay

### EPIC: Access & Identity (AuthN/Z)
- Magic link auth + OAuth Google
- Roles & permissions (Owner/Admin/Member/Guest)
- Audit log MVP

### EPIC: Privacy, Security & GDPR
- DSAR: Export & delete user/team data
- DPIA & Records of Processing

### EPIC: Private Beta Program
- Beta recruitment & screening
- In-app feedback widget + triage labels
- Weekly synthesis → roadmap tickets

### EPIC: Public Beta Growth Engine
- Self-serve signup & team creation
- Invite & viral growth loop
- Pricing experiment framework (flags + paywalls)
- Public Beta learnings synthesis

### EPIC: Billing & Entitlements
- Billing & entitlements (Stripe)
- Seat management & metering
- Invoices, taxes, refunds

### EPIC: Reliability & Observability
- SLIs/SLOs + error budget policy

---

**Total:** 25 child issues need to be linked to their parent Epics.

All Epic issues have been added to Project #17 and are ready for linking!


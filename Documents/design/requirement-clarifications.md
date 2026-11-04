# Requirement Clarifications & Spike Resolution

**Module:** DOC.01 (Issue #175)  
**Parent Epic:** [DOC] Documentation & Requirement Clarifications (#174)  

---

## 1. Overview
This specification records all official decisions clarifying previously ambiguous requirements across the Hostel Management System (HMS), ensuring that implementation behavior across all 10 modules is strictly deterministic and documented.

---

## 2. Clarifications & Architectural Decisions

### 2.1 Allocation Priority Rules (FR-04)
- **Question:** How are students prioritized when allocating rooms?
- **Decision:** Allocation prioritizes by student academic year/seniority (Year 4 > Year 3 > Year 2 > Year 1) followed by waitlist registration timestamp (First-Come, First-Served for equal seniority). Special medical or administrative priority flags override standard seniority.

### 2.2 Demerit Points per Severity (FR-06)
- **Question:** What is the point scale for student misconduct complaints?
- **Decision:**
  - **Low Severity:** 1 Demerit Point (Minor noise, room cleanliness warning).
  - **Medium Severity:** 3 Demerit Points (Curfew violation, unauthorized appliance).
  - **High Severity:** 5 Demerit Points (Damage to hostel property, harassment, severe misconduct).
  - Demerit points accumulate automatically on the student record.

### 2.3 Attendance Determination (FR-07)
- **Question:** How is a student's daily attendance status derived?
- **Decision:**
  - A student with an active check-in during hostel hours without an unresolved check-out is marked **Present**.
  - A student on approved Leave for the given date is marked **On Leave**.
  - A student without a check-in or valid leave is marked **Absent** during evening curfew roll call.

### 2.4 Past Leave Dates (FR-09)
- **Question:** Are students permitted to submit leave requests with start dates in the past?
- **Decision:** **No.** Start date must be greater than or equal to current local date (`from_date >= today`). Retrospective leave requests cannot be submitted via self-service; administrative adjustments require Warden/Admin intervention.

### 2.5 Notification Channel (Cross-Cutting / NFR)
- **Question:** What channels are used for system alerts and notifications?
- **Decision:** In-app notification center stored in the SQLite/database layer with real-time UI badges and alert popups. Email and SMS hooks are architected via service interfaces for external gateway integration.

### 2.6 Notice Audience Targeting (FR-10)
- **Question:** Who can notices be targeted to?
- **Decision:** Notices support 4 audience tiers:
  1. `ALL`: All hostel residents, wardens, and staff.
  2. `STUDENTS`: Registered student residents only.
  3. `WARDENS`: Wardens and administrative staff.
  4. Specific Hostel Block/Wing: Residents assigned to designated hostel blocks.

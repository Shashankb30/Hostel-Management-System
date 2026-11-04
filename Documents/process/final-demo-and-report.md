# Final Project Demo Script & Evaluation Report

**Module:** DOC.06 (Issue #180)  
**Parent Epic:** [DOC] Documentation & Requirement Clarifications (#174)  

---

## 1. Demo Execution Script

### Phase 1: Authentication & Role-Based Access Control (FR-01)
1. Navigate to `/accounts/login/`.
2. Demonstrate invalid login rejection and error feedback.
3. Log in as Administrator (`admin01`) -> verify redirect to Admin dashboard and full navigation.
4. Log in as Warden (`wdn05`) -> verify redirect to Warden dashboard with operational controls.
5. Log in as Student (`stu1023`) -> verify redirect to Student dashboard with personal records only.

### Phase 2: Student Lifecycle & Room Management (FR-02, FR-03, FR-04)
1. **Student Registration:** Register a student with roll number, department, room eligibility.
2. **Room Management:** Showcase rooms categorized by blocks, capacity checks, and vacancy filters.
3. **Allocation:** Allocate an eligible student to a vacant room; verify vacancy count auto-decrements.
4. **Transfer:** Demonstrate student room transfer and verify old room vacancy increments while new decrements.

### Phase 3: Fees & Billing (FR-05)
1. Define fee structure for resident student (Hostel + Mess Fee).
2. Record partial payment; observe balance recalculation and status change to `Partially Paid`.
3. Record full payment; verify status changes to `Paid` and inspect generated receipt.
4. Export the Outstanding Dues CSV report.

### Phase 4: Complaints & Disciplinary Action (FR-06)
1. Student lodges a maintenance/noise complaint.
2. Warden reviews the complaint, updates status to `Under Review` or `Resolved`.
3. Log a misconduct issue with severity `High` -> verify 5 demerit points accumulate on the student profile.

### Phase 5: Attendance, Visitors, Leave & Notices (FR-07, FR-08, FR-09, FR-10)
1. **Attendance:** Perform bulk check-in and verify daily attendance summary register.
2. **Visitors:** Check in a visitor linked to a host student; demonstrate double check-out prevention.
3. **Leave:** Submit student leave application; approve application as Warden with remarks.
4. **Notices:** Broadcast an urgent notice to all students and verify appearance on student dashboard.

---

## 2. GitHub Project & Automation Verification
- **CI / CD Pipeline:** Automated workflow runs pytest/Django test suite on pull requests.
- **Board Automation:** PR references (`Fixes #<issue>`) automatically transition issues to `Done` upon merge.
- **Test Matrix:** 100% automated test coverage across 80 core test plan specifications.

---
title: "Test Plan — Hostel Management System (HMS)"
---

# Test Plan

**Hostel Management System (HMS)** — IEEE 829-2008 structure · Version 2.0 · 2026-11-05

| Version | Date | Change |
|---|---|---|
| 1.0 | Oct 2026 | 80 test cases (UT/IT/ST) for FR-01..FR-10 |
| 2.0 | 2026-11-05 | IEEE sections 1–8; security validation section 5.1; NFR cases; full SRS traceability; results from the 681-test regression run |

# 1. Introduction

## 1.1 Purpose
This plan defines how HMS is verified against `docs/SRS.md` and `docs/SAD.md`: what is tested, how, with which tools, and what "pass" means.

## 1.2 Scope
All ten functional modules (FR-01..FR-10), the non-functional requirements NFR-01..NFR-08 and the security requirements SR-1..SR-7.

## 1.3 References
SRS (`docs/SRS.md`); SAD (`docs/SAD.md`); `TEST_PLAN_MATRIX.md` (detailed steps/data for every case); reports in `docs/reports/`.

## 1.4 Definitions
UT = unit test case, IT = integration test case, ST = system test case; IDs `UT_##_Mod`, `IT_##_Mod`, `ST_##_Mod` follow the course convention. Extension IDs such as `UT_LOGIN_04` cover behaviour added from backlog issues.

# 2. Test items

| Item | Version | Location |
|---|---|---|
| HMS web application | `main` branch, tag at Sprint 2 freeze | repository root |
| Database schema + migrations | `core/migrations/0001..0006` | `core/migrations/`, `Documents/design/schema.sql` |
| Seed data command | `python manage.py seed_data` | `core/management/commands/` |

# 3. Features to be tested

| Feature | SRS requirement | Test levels | Test cases |
|---|---|---|---|
| User Login | FR-01.x | UT, IT, ST | UT_01_Login … ST_02_Login (8 core + extension cases) |
| Student Registration | FR-02.x | UT, IT, ST | UT_04_Reg … ST_04_Reg (8 core + extension cases) |
| Room Management | FR-03.x | UT, IT, ST | UT_07_Room … ST_06_Room (8 core + extension cases) |
| Room Allocation | FR-04.x | UT, IT, ST | UT_10_Alloc … ST_08_Alloc (8 core + extension cases) |
| Fee Management | FR-05.x | UT, IT, ST | UT_13_Fee … ST_10_Fee (8 core + extension cases) |
| Complaint Management | FR-06.x | UT, IT, ST | UT_16_Comp … ST_12_Comp (8 core + extension cases) |
| Attendance Management | FR-07.x | UT, IT, ST | UT_19_Att … ST_14_Att (8 core + extension cases) |
| Visitor Management | FR-08.x | UT, IT, ST | UT_22_Vis … ST_16_Vis (8 core + extension cases) |
| Home / Long-Leave Application | FR-09.x | UT, IT, ST | UT_25_Leave … ST_18_Leave (8 core + extension cases) |
| Notice / Information Management | FR-10.x | UT, IT, ST | UT_28_Notice … ST_20_Notice (8 core + extension cases) |
| Non-functional behaviour | NFR-01..NFR-08 | UT | UT_NFR_01..13 (section 5.3) |
| Security controls | SR-1..SR-7 | UT, IT, ST | Section 5.1 |

## 3.1 Features not tested
Browser rendering differences, real e-mail delivery (console backend used), load above 20 concurrent users, penetration testing by an external party.

# 4. Approach, environment and criteria

## 4.1 Test levels
| Level | What it checks | How |
|---|---|---|
| Unit (UT) | One service function / form / model rule | Django `TestCase`, in-memory SQLite |
| Integration (IT) | Two or more modules or view + service + database | Django test client with real roles |
| System (ST) | End-to-end behaviour through URLs: reports, filters, workflows | Django test client; same DB constraints as production |
| Non-functional | Performance, backup/restore, constraints, security | `core/test_nfr.py`, `scripts/benchmark_performance.py` |

## 4.2 Tools and environment
Python 3.12, Django 5.2, `python manage.py test`, coverage.py (`--branch`), ruff, GitHub Actions (`.github/workflows/ci.yml`) on every push/PR to `main` and `dev`.

## 4.3 Entry criteria
Code merged to the branch under test; `manage.py check` and `ruff check .` pass; migrations apply to an empty database; seed data loads.

## 4.4 Pass / fail and exit criteria
A case passes when the actual result equals the expected result. Exit when: 100 % of planned cases executed, 0 open failures, statement coverage ≥ 90 %, branch coverage ≥ 80 %, and reports are stored in `docs/reports/`.

## 4.5 Traceability approach
Every case lists its SRS requirement (FR/NFR/SR); the matrix in section 6 maps each requirement to its cases, and each case names its automated evidence (test module).

# 5. Test cases

Full pre-conditions, steps and data for each case are in `TEST_PLAN_MATRIX.md`; this section lists every case with its requirement, expected result and result.

## 5.1 Security validation

| ID | SRS ref | Security objective / requirement | Procedure | Expected result | Evidence | Result |
|---|---|---|---|---|---|---|
| SEC-01 (UT_NFR_01) | SR-1 | Student is blocked from admin/warden pages | Student requests 7 admin/warden URLs (rooms, allocation, students, users, notice add, visitor add, leave review) | HTTP 403 on all | `core.test_nfr` | Pass |
| SEC-01b (RBAC matrix) | SR-1, SR-5 | Every role-protected page enforces its roles | 36 no-argument routes × student/warden/admin, plus anonymous | Disallowed role → 403; allowed role → not 403; anonymous never gets HTTP 200 | `core.test_rbac_matrix` (new, 2 tests) | Pass |
| SEC-02 (UT_NFR_03) | SR-2 | Student isolation | Student A requests student B’s fee page and visitor history | HTTP 403 | `core.test_nfr`, `fees.test_student_fees_view` | Pass |
| SEC-03 (UT_NFR_02) | SR-3 | Password hashing + session settings | Create user; inspect stored hash; check session/CSRF cookie settings | Hash is PBKDF2-SHA256 (not plaintext); idle timeout, expire-at-browser-close, HttpOnly cookies active | `core.test_nfr` | Pass |
| SEC-04 (UT_NFR_04) | SR-6 | XSS / injection input handling | Publish a notice whose body is `<script>alert(1)</script>` and open the board as a student | Script is HTML-escaped (`&lt;script&gt;`), never executed. SQL injection is prevented by design: no raw SQL, no safe-filter and no mark_safe in application code (only a constant `SELECT 1` in the health check) | `core.test_nfr`; code review | Pass |
| SEC-05 (IT_LOGIN_06) | SR-4, FR-01.4 | Brute-force lockout | 5 wrong passwords, then correct password | Account locks; correct password refused until admin unlocks | `accounts.test_lockout` | Pass |
| SEC-06 (ST_LOGIN_04) | SR-4 | Idle session expiry | Stay idle past timeout; activity extends session | Redirect to login after timeout | `accounts.test_session` | Pass |
| SEC-07 (ST_LOGIN_03) | SR-7 | No cached pages after logout | Log in, log out, press Back | Login page shown; `Cache-Control: no-store` on authenticated pages | `accounts.test_logout` | Pass |
| SEC-08 (UT_LOGIN_05) | SR-3 | Password-reset link is single-use; weak passwords rejected | Use link twice; set weak password | Second use refused; weak password rejected | `accounts.test_password_reset` | Pass |
| SEC-09 (IT_LOGIN_04) | SR-1 | Only administrators manage accounts | Non-admin opens Users & Roles | "Access denied" (403) | `accounts.test_user_management` | Pass |
| SEC-10 (UT_NFR_09) | SR-7 | Safe failure | Request an unknown URL; force an exception inside a transaction | Friendly "Page Not Found" page; transaction rolled back (no partial row) | `core.test_nfr` | Pass |

## 5.2 Functional test cases (core Test Plan: 80 cases)

| Test ID | Module | SRS ref | Description | Expected result | Automated evidence | Result |
|---|---|---|---|---|---|---|
| UT_01_Login | User Login | FR-01 | Verify login screen loads with username and password fields | Login page displays Username and Password fields with a Submit button | s [2 tests] | Pass |
| UT_02_Login | User Login | FR-01 | Verify successful login with valid Student credentials | User is authenticated and redirected to the Student dashboard | s [2 tests] | Pass |
| UT_03_Login | User Login | FR-01 | Verify login rejects incorrect password | Error message "Invalid username or password" is displayed; access denied | s [3 tests] | Pass |
| IT_01_Login | User Login | FR-01 | Verify role-based redirection for Warden login | User is redirected to the Warden dashboard with warden-specific menu options | s [2 tests] | Pass |
| IT_02_Login | User Login | FR-01 | Verify role-based redirection for Administrator login | User is redirected to the Administrator dashboard with full admin menu | s [1 tests] | Pass |
| IT_03_Login | User Login | FR-01 | Verify login blocked for an inactive/locked account | Error message stating the account is inactive/locked is displayed | s [5 tests] | Pass |
| ST_01_Login | User Login | FR-01 | Verify session is maintained across module navigation after login | User remains authenticated across modules without being re-prompted to log in | s [3 tests] | Pass |
| ST_02_Login | User Login | FR-01 | Verify empty credential submission is rejected | System displays validation errors and does not attempt authentication | s [6 tests] | Pass |
| UT_04_Reg | Student Registration | FR-02 | Verify Add Student form displays all required fields | Form displays fields for Name, Roll No., Contact, Address, Course, Year | s [7 tests] | Pass |
| UT_05_Reg | Student Registration | FR-02 | Verify successful registration with valid, complete data | Student record is created and a unique Student ID is generated | s [3 tests] | Pass |
| UT_06_Reg | Student Registration | FR-02 | Verify registration rejects duplicate Roll Number | System displays "Roll number already exists" and blocks submission | s [7 tests] | Pass |
| IT_04_Reg | Student Registration | FR-02 | Verify updating an existing student's contact details | Student record is updated and reflected in the student list | s [4 tests] | Pass |
| IT_05_Reg | Student Registration | FR-02 | Verify new student appears in Room Allocation candidate list | The new student appears as eligible for room allocation | s [3 tests] | Pass |
| IT_06_Reg | Student Registration | FR-02 | Verify registration rejects invalid contact number format | System displays a format-validation error and blocks submission | s [2 tests] | Pass |
| ST_03_Reg | Student Registration | FR-02 | Verify search/filter of student records by name | Matching student record(s) are displayed in the results list | s [4 tests] | Pass |
| ST_04_Reg | Student Registration | FR-02 | Verify registration form rejects submission with mandatory fields empty | System highlights required fields and prevents submission | s [8 tests] | Pass |
| UT_07_Room | Room Management | FR-03 | Verify Add Room form accepts valid room details | New room record is created with status "Vacant" | s [11 tests] | Pass |
| UT_08_Room | Room Management | FR-03 | Verify duplicate room number is rejected | System displays "Room number already exists" and blocks creation | s [7 tests] | Pass |
| UT_09_Room | Room Management | FR-03 | Verify room capacity must be a positive integer | System displays a validation error and blocks submission | s [6 tests] | Pass |
| IT_07_Room | Room Management | FR-03 | Verify room vacancy status updates automatically after allocation | Occupancy count increases and vacancy status updates (e.g., "2 vacant") | s [8 tests] | Pass |
| IT_08_Room | Room Management | FR-03 | Verify a fully occupied room does not appear in allocation candidate list | Room A-101 does not appear in the vacant room list | s [8 tests] | Pass |
| IT_09_Room | Room Management | FR-03 | Verify room details update reflects in student's room-view | Student sees the updated room information | s [5 tests] | Pass |
| ST_05_Room | Room Management | FR-03 | Verify filtering rooms by vacancy status | Only rooms with available capacity are displayed | s [7 tests] | Pass |
| ST_06_Room | Room Management | FR-03 | Verify a room cannot be deleted while it has active occupants | System blocks deletion and displays a message that occupants must be reassigned first | s [5 tests] | Pass |
| UT_10_Alloc | Room Allocation | FR-04 | Verify vacant room list displays correctly for allocation | System displays only rooms with available capacity | s [5 tests] | Pass |
| UT_11_Alloc | Room Allocation | FR-04 | Verify successful allocation of a vacant room to a student | Room is allocated; student's record shows Room B-204; vacancy decreases by 1 | s [4 tests] | Pass |
| UT_12_Alloc | Room Allocation | FR-04 | Verify allocation respects priority rules (e.g., senior students first) | System flags/prioritizes the senior student per priority rule before junior | s [4 tests] | Pass |
| IT_10_Alloc | Room Allocation | FR-04 | Verify allocation is blocked for a room at full capacity | System displays "Room unavailable" and blocks the allocation | s [3 tests] | Pass |
| IT_11_Alloc | Room Allocation | FR-04 | Verify already-allocated student cannot be allocated a second room without transfer | System requires a room transfer action instead of a direct new allocation | s [3 tests] | Pass |
| IT_12_Alloc | Room Allocation | FR-04 | Verify room transfer updates both old and new room occupancy | Student's room updates to C-102; B-204 vacancy increases; C-102 vacancy decreases | s [4 tests] | Pass |
| ST_07_Alloc | Room Allocation | FR-04 | Verify allocation history/report is generated correctly | Report lists all students with their allocated rooms and dates | s [3 tests] | Pass |
| ST_08_Alloc | Room Allocation | FR-04 | Verify allocation fails gracefully when no vacant rooms exist | System displays "No vacant rooms available" instead of an error/crash | s [3 tests] | Pass |
| UT_13_Fee | Fee Management | FR-05 | Verify fee structure displays correctly for a student | System displays total fee, amount paid, and outstanding balance | s [4 tests] | Pass |
| UT_14_Fee | Fee Management | FR-05 | Verify recording a valid full payment updates status to Paid | Payment status updates to "Paid"; receipt is generated | s [3 tests] | Pass |
| UT_15_Fee | Fee Management | FR-05 | Verify recording a partial payment updates status to Partially Paid | Status updates to "Partially Paid"; remaining balance recalculated to Rs. 30,000 | s [3 tests] | Pass |
| IT_13_Fee | Fee Management | FR-05 | Verify payment amount exceeding due balance is rejected | System displays a validation error and blocks the transaction | s [3 tests] | Pass |
| IT_14_Fee | Fee Management | FR-05 | Verify negative or non-numeric payment amount is rejected | System displays a validation error and blocks submission | s [4 tests] | Pass |
| IT_15_Fee | Fee Management | FR-05 | Verify student view reflects payment recorded by administrator | Student sees the updated payment status and balance | s [3 tests] | Pass |
| ST_09_Fee | Fee Management | FR-05 | Verify fee payment history/report lists all transactions for a student | All payment entries display with correct dates, amounts, and modes in chronological order | s [3 tests] | Pass |
| ST_10_Fee | Fee Management | FR-05 | Verify duplicate payment entries for the same transaction are prevented | System prevents a duplicate entry or warns before creating one | s [3 tests] | Pass |
| UT_16_Comp | Complaint Management | FR-06 | Verify student can submit a new complaint | Complaint is recorded with status "Open" and a unique complaint ID | s [4 tests] | Pass |
| UT_17_Comp | Complaint Management | FR-06 | Verify complaint submission fails with empty description | System displays a validation error and blocks submission | s [3 tests] | Pass |
| UT_18_Comp | Complaint Management | FR-06 | Verify warden can view all open complaints | All open complaints are listed with student and category details | s [3 tests] | Pass |
| IT_16_Comp | Complaint Management | FR-06 | Verify demerit points are assigned based on misconduct severity | System automatically assigns the predefined demerit points for "Major" severity | s [4 tests] | Pass |
| IT_17_Comp | Complaint Management | FR-06 | Verify complaint status update from Open to Resolved notifies the student | Status updates; student sees the updated status and remarks on their dashboard | s [4 tests] | Pass |
| IT_18_Comp | Complaint Management | FR-06 | Verify repeated complaints against a student accumulate demerit points | Student's total demerit points update to 5 (cumulative) | s [3 tests] | Pass |
| ST_11_Comp | Complaint Management | FR-06 | Verify complaint report/summary can be generated by category | Report displays complaint counts grouped correctly by category | s [3 tests] | Pass |
| ST_12_Comp | Complaint Management | FR-06 | Verify a resolved complaint cannot be edited without reopening | System prevents direct editing or requires reopening the complaint first | s [3 tests] | Pass |
| UT_19_Att | Attendance Management | FR-07 | Verify warden can record a student check-in | Check-in time is recorded and timestamped for the student | s [4 tests] | Pass |
| UT_20_Att | Attendance Management | FR-07 | Verify warden can record a student check-out | Check-out time is recorded and the attendance entry is completed | s [4 tests] | Pass |
| UT_21_Att | Attendance Management | FR-07 | Verify duplicate check-in without prior check-out is flagged | System flags the inconsistency and does not create a duplicate open entry | s [3 tests] | Pass |
| IT_19_Att | Attendance Management | FR-07 | Verify daily attendance summary reflects individually marked entries | Summary accurately lists present/absent status per student for the day | s [3 tests] | Pass |
| IT_20_Att | Attendance Management | FR-07 | Verify bulk attendance marking updates all selected students | All selected students' check-in times are recorded simultaneously | s [4 tests] | Pass |
| IT_21_Att | Attendance Management | FR-07 | Verify attendance record links correctly to the correct student profile | The attendance entry appears correctly under that student's profile only | s [3 tests] | Pass |
| ST_13_Att | Attendance Management | FR-07 | Verify attendance report can be filtered by date range | Report displays only attendance records within the selected range | s [3 tests] | Pass |
| ST_14_Att | Attendance Management | FR-07 | Verify system handles check-out attempt without a prior check-in | System displays an error indicating no active check-in exists | s [3 tests] | Pass |
| UT_22_Vis | Visitor Management | FR-08 | Verify Add Visitor form captures required details | Form displays fields for visitor name, ID proof, purpose, and student visited | s [1 tests] | Pass |
| UT_23_Vis | Visitor Management | FR-08 | Verify successful visitor check-in is recorded with timestamp | Visitor entry is created with a check-in timestamp | s [2 tests] | Pass |
| UT_24_Vis | Visitor Management | FR-08 | Verify visitor check-in fails with missing ID proof | System displays a validation error and blocks the check-in | s [4 tests] | Pass |
| IT_22_Vis | Visitor Management | FR-08 | Verify visitor check-out updates the same visitor's log entry | Check-out time is recorded on the same entry; visit duration is calculated | s [2 tests] | Pass |
| IT_23_Vis | Visitor Management | FR-08 | Verify visitor log links correctly to the student being visited | The visitor entry appears in that student's visitor history | s [2 tests] | Pass |
| IT_24_Vis | Visitor Management | FR-08 | Verify visitor search by date or student name returns correct results | Only matching visitor entries are displayed | s [2 tests] | Pass |
| ST_15_Vis | Visitor Management | FR-08 | Verify visitor log report can be exported/generated for a date range | Report lists all visitor entries with check-in/out times within the range | s [2 tests] | Pass |
| ST_16_Vis | Visitor Management | FR-08 | Verify a checked-out visitor entry cannot be checked out again | System prevents duplicate check-out and displays an appropriate message | s [2 tests] | Pass |
| UT_25_Leave | Home / Long-Leave Application | FR-09 | Verify student can submit a leave application with valid dates | Application is recorded with status "Pending" | s [2 tests] | Pass |
| UT_26_Leave | Home / Long-Leave Application | FR-09 | Verify leave submission fails when end date precedes start date | System displays a validation error and blocks submission | s [2 tests] | Pass |
| UT_27_Leave | Home / Long-Leave Application | FR-09 | Verify leave submission fails with missing reason | System displays a validation error and blocks submission | s [2 tests] | Pass |
| IT_25_Leave | Home / Long-Leave Application | FR-09 | Verify warden can approve a pending leave application | Status updates to "Approved"; student is notified | s [2 tests] | Pass |
| IT_26_Leave | Home / Long-Leave Application | FR-09 | Verify warden can reject a pending leave application with remarks | Status updates to "Rejected"; remarks are visible to the student | s [3 tests] | Pass |
| IT_27_Leave | Home / Long-Leave Application | FR-09 | Verify overlapping leave dates with an existing approved leave are flagged | System flags the date conflict for the reviewer before approval | s [2 tests] | Pass |
| ST_17_Leave | Home / Long-Leave Application | FR-09 | Verify leave application history is visible to the student | All past and current applications display with correct status and dates | s [2 tests] | Pass |
| ST_18_Leave | Home / Long-Leave Application | FR-09 | Verify administrator can view leave records across all students | All students' leave applications are listed with status and dates | s [2 tests] | Pass |
| UT_28_Notice | Notice / Information Management | FR-10 | Verify warden/administrator can create a new notice | Notice is published and stored with a timestamp | s [2 tests] | Pass |
| UT_29_Notice | Notice / Information Management | FR-10 | Verify notice creation fails with an empty title | System displays a validation error and blocks publishing | s [3 tests] | Pass |
| UT_30_Notice | Notice / Information Management | FR-10 | Verify published notice appears on the student dashboard | The notice is visible on the student's dashboard | s [2 tests] | Pass |
| IT_28_Notice | Notice / Information Management | FR-10 | Verify editing an existing notice updates the displayed content | Students viewing the notice see the updated content | s [2 tests] | Pass |
| IT_29_Notice | Notice / Information Management | FR-10 | Verify deleting/expiring a notice removes it from the student view | The notice no longer appears on the student dashboard | s [2 tests] | Pass |
| IT_30_Notice | Notice / Information Management | FR-10 | Verify notices are ordered by most recent first | Notices display in descending order of publish date | s [2 tests] | Pass |
| ST_19_Notice | Notice / Information Management | FR-10 | Verify notice list can be filtered/searched by keyword | Only matching notices are displayed | s [2 tests] | Pass |
| ST_20_Notice | Notice / Information Management | FR-10 | Verify only authorized roles (Warden/Administrator) can publish notices | System denies access / does not display the notice-creation option to students | s [1 tests] | Pass |

### 5.2.1 Extension cases added from backlog issues

| Test ID | Module | SRS ref | Description | Automated evidence | Result |
|---|---|---|---|---|---|
| UT_LOGIN_04 | User Login | FR-01 | Verify logout ends the session (Issue #23, inferred) | s [4 tests] | Pass |
| ST_LOGIN_03 | User Login | FR-01 | Verify the Back button cannot reopen a protected page after logout (Issue #23, inferred) | s [2 tests] | Pass |
| ST_LOGIN_04 | User Login | FR-01 | Verify the session ends after the idle timeout and is extended by activity (Issue #22) | s [3 tests] | Pass |
| UT_LOGIN_05 | User Login | FR-01 | Verify forgot-password flow resets a password without normal login (Issue #24) | s [10 tests] | Pass |
| IT_LOGIN_04 | User Login | FR-01 | Verify the administrator can create and edit accounts with unique usernames and valid roles (Issue #25, inferred) | s [18 tests] | Pass |
| IT_LOGIN_05 | User Login | FR-01 | Verify a deactivated account cannot log in and can be reactivated (Issue #25) | s [4 tests] | Pass |
| IT_LOGIN_06 | User Login | FR-01 | Verify an account locks after repeated failed logins and an administrator can unlock it (Issue #26, inferred) | s [11 tests] | Pass |
| UT_REG_07 | Student Registration | FR-02 | Verify registration rejects a duplicate email address (Issue #30, inferred) | s [6 tests] | Pass |
| UT_REG_08 | Student Registration | FR-02 | Verify every registered student gets a different Student ID that cannot be typed in (Issue #29, #30) | s [4 tests] | Pass |
| IT_REG_07 | Student Registration | FR-02 | Verify the new student can log in with the generated credentials (Issue #29, inferred) | s [6 tests] | Pass |
| UT_ROOM_10 | Room Management | FR-03 | Verify a warden can view rooms and update availability (Issue #50, inferred) | s [11 tests] | Pass |
| UT_ROOM_11 | Room Management | FR-03 | Verify capacity cannot be lowered below the current occupancy (Issue #51, inferred) | s [6 tests] | Pass |
| IT_ROOM_12 | Room Management | FR-03 | Verify a student sees their own room and an empty state when unallocated (Issue #47, inferred) | s [8 tests] | Pass |
| UT_ROOM_13 | Room Management | FR-03 | Verify editing a room uses the same validation as adding (Issue #43, inferred) | s [9 tests] | Pass |
| IT_ROOM_14 | Room Management | FR-03 | Verify an unoccupied room can be made unavailable and is then hidden from allocation (Issue #49, inferred) | s [7 tests] | Pass |
| UT_FEE_04 | Fee Management | FR-05 | Verify the administrator can define and edit a student's fee and invalid fees are rejected | s [6 tests] | Pass |
| UT_FEE_05 | Fee Management | FR-05 | Verify a payment mode is required and only valid modes are accepted | s [5 tests] | Pass |
| UT_FEE_06 | Fee Management | FR-05 | Verify a receipt is generated for each payment and students can open only their own | s [4 tests] | Pass |
| UT_FEE_07 | Fee Management | FR-05 | Verify the fee status follows the payments (Due, Partially Paid, Paid) | s [4 tests] | Pass |
| IT_FEE_04 | Fee Management | FR-05 | Verify fee pages are limited to the right roles and students see only their own fees | s [6 tests] | Pass |
| ST_FEE_03 | Fee Management | FR-05 | Verify the outstanding dues report lists only unpaid balances with overdue flags and a CSV download | s [5 tests] | Pass |

## 5.3 Non-functional test cases

| Test ID | SRS ref | Description | Expected result | Automated evidence | Result |
|---|---|---|---|---|---|
| UT_NFR_01 | NFR-01, SR-1, SR-5 | Verify role-based access control blocks unauthorized roles on all endpoints | System returns 403 Forbidden for all unauthorized routes | s [1 tests] | Pass |
| UT_NFR_02 | NFR-01, SR-3, SR-4 | Verify secure password hashing and session timeout configuration | Passwords hashed with PBKDF2; idle session timeout enforced | s [1 tests] | Pass |
| UT_NFR_03 | NFR-01, SR-2 | Verify cross-student access is denied (student isolation) | Access is denied with 403 Forbidden | s [1 tests] | Pass |
| UT_NFR_04 | NFR-01, SR-6 | Verify input sanitization against injection and XSS | Content is auto-escaped; raw script tags do not execute | s [1 tests] | Pass |
| UT_NFR_06 | NFR-03 | Verify performance baseline responds under 3 seconds | All operations respond in < 3.0s | s [1 tests] | Pass |
| UT_NFR_07 | NFR-03, NFR-07 | Verify database indexes on key fields and paginated lists | B-tree indexes exist; pagination context provided | s [1 tests] | Pass |
| UT_NFR_08 | NFR-04 | Verify backup and restore procedure | Snapshot created; database restores to exact state without corruption | s [1 tests] | Pass |
| UT_NFR_09 | NFR-04, SR-7 | Verify transactional rollback on errors and friendly error handling | Changes rolled back atomically; no stack traces exposed | s [1 tests] | Pass |
| UT_NFR_10 | NFR-05 | Verify database constraints and server-side integrity rules | Database raises IntegrityError; server-side constraints reject duplicates | s [1 tests] | Pass |
| UT_NFR_12 | NFR-07 | Verify support for multiple hostels and block isolation | Same room number allowed across different hostels without collision | s [1 tests] | Pass |
| UT_NFR_13 | NFR-08 | Verify health check endpoint and maintenance handling | /health/ returns 200 OK with connected DB status; maintenance notice displays | s [1 tests] | Pass |
| UT_NFR_05 | NFR-02 | Usability: first-time user completes the primary task of each role in ≤ 3 clicks | Task completed without help; messages name field and fix | Manual walkthrough (`Documents/process/usability-review.md`) | Manual — to be executed at demo |
| UT_NFR_11 | NFR-06 | Maintainability: no cyclic dependency between apps; `ruff check .` clean | 0 cycles; 0 lint issues | `ruff` in CI; dependency table SAD §5.2 | Lint Pass; cycle check manual |

## 5.4 Setup / DevOps cases

9 setup cases (`UT_SETUP_*`: schema, seed data, app shell, CI, validation framework, notifications) are listed in `TEST_PLAN_MATRIX.md` and all pass.

# 6. Traceability matrix (SRS → test cases)

| Requirement | Test cases | Status |
|---|---|---|
| FR-01 User Login | UT_01_Login, UT_02_Login, UT_03_Login, IT_01_Login, IT_02_Login, IT_03_Login, ST_01_Login, ST_02_Login, UT_LOGIN_04, ST_LOGIN_03, ST_LOGIN_04, UT_LOGIN_05, IT_LOGIN_04, IT_LOGIN_05, IT_LOGIN_06 | Pass |
| FR-02 Student Registration | UT_04_Reg, UT_05_Reg, UT_06_Reg, IT_04_Reg, IT_05_Reg, IT_06_Reg, ST_03_Reg, ST_04_Reg, UT_REG_07, UT_REG_08, IT_REG_07 | Pass |
| FR-03 Room Management | UT_07_Room, UT_08_Room, UT_09_Room, IT_07_Room, IT_08_Room, IT_09_Room, ST_05_Room, ST_06_Room, UT_ROOM_10, UT_ROOM_11, IT_ROOM_12, UT_ROOM_13, IT_ROOM_14 | Pass |
| FR-04 Room Allocation | UT_10_Alloc, UT_11_Alloc, UT_12_Alloc, IT_10_Alloc, IT_11_Alloc, IT_12_Alloc, ST_07_Alloc, ST_08_Alloc | Pass |
| FR-05 Fee Management | UT_13_Fee, UT_14_Fee, UT_15_Fee, IT_13_Fee, IT_14_Fee, IT_15_Fee, ST_09_Fee, ST_10_Fee, UT_FEE_04, UT_FEE_05, UT_FEE_06, UT_FEE_07, IT_FEE_04, ST_FEE_03 | Pass |
| FR-06 Complaint Management | UT_16_Comp, UT_17_Comp, UT_18_Comp, IT_16_Comp, IT_17_Comp, IT_18_Comp, ST_11_Comp, ST_12_Comp | Pass |
| FR-07 Attendance Management | UT_19_Att, UT_20_Att, UT_21_Att, IT_19_Att, IT_20_Att, IT_21_Att, ST_13_Att, ST_14_Att | Pass |
| FR-08 Visitor Management | UT_22_Vis, UT_23_Vis, UT_24_Vis, IT_22_Vis, IT_23_Vis, IT_24_Vis, ST_15_Vis, ST_16_Vis | Pass |
| FR-09 Home / Long-Leave Application | UT_25_Leave, UT_26_Leave, UT_27_Leave, IT_25_Leave, IT_26_Leave, IT_27_Leave, ST_17_Leave, ST_18_Leave | Pass |
| FR-10 Notice / Information Management | UT_28_Notice, UT_29_Notice, UT_30_Notice, IT_28_Notice, IT_29_Notice, IT_30_Notice, ST_19_Notice, ST_20_Notice | Pass |
| NFR-01 / SR-1..SR-7 | SEC-01..SEC-10, UT_NFR_01..04 | Pass |
| NFR-02 | UT_NFR_05 | Manual pending |
| NFR-03 | UT_NFR_06, UT_NFR_07 | Pass |
| NFR-04 | UT_NFR_08, UT_NFR_09 | Pass |
| NFR-05 | UT_NFR_10 (+ FR-04/05 concurrency tests) | Pass |
| NFR-06 | UT_NFR_11 | Lint pass; cycle check manual |
| NFR-07 | UT_NFR_07, UT_NFR_12 | Pass |
| NFR-08 | UT_NFR_13 | Pass |

# 7. Responsibilities, schedule and risks

| Activity | Owner | When |
|---|---|---|
| Sprint 1 tests (FR-01..FR-05) | Both members, per backlog assignment | 19–23 Oct 2026 |
| Sprint 2 tests (FR-06..FR-10, NFR) | Both members, per backlog assignment | 26–30 Oct 2026 |
| Regression + reports | QA issues #156–#173 | 30–31 Oct 2026 |
| Re-run for final freeze | Repository owner | 2026-11-05 |

| Risk | Mitigation |
|---|---|
| Test suite takes ~2 min | CI timeout 10 min; module-level runs during development |
| Lower coverage in leave/notices views | Added to deviation/known-gap list; targeted tests planned |
| Manual NFR-02 case not automated | Executed during the demo walkthrough |

# 8. Deliverables and results

| Deliverable | Location |
|---|---|
| Unit/automated test report | `docs/reports/unit-test-report.md` |
| System validation report | `docs/reports/system-validation-report.md` |
| Code coverage report | `docs/reports/code-coverage-report.md`, `docs/reports/coverage/html/index.html`, `coverage.xml` |
| Branch coverage report | `docs/reports/branch-coverage-report.md` |

**Execution summary (2026-11-06, Windows, coverage.py 7.17.0):** 681 automated tests (679 original + 2 RBAC-matrix tests, SEC-01b), 0 failures, 0 errors; statement coverage 94.9 %, branch coverage 84.2 %, combined 93 %.

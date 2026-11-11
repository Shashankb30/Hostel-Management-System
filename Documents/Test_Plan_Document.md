# Software Test Plan (STP)

## Hostel Management System

**Project:** Hostel Management System (HMS)
**Version:** 2.0
**Authors:** Shashankb30, abhijeetcyalgi
**Date:** 30-10-2026
**Status:** Approved

---

## Revision History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 18-10-2026 | Shashankb30 | Initial test plan with 80 test cases across 10 modules |
| 2.0 | 30-10-2026 | abhijeetcyalgi | Expanded to 127 test cases; added NFR tests, security validation, metrics, and schedule |

## Approvals

| Role | Name | Signature/Date |
|------|------|----------------|
| Team Lead | Shashank B Jain | 30-10-2026 |
| QA / Developer | Abhijeet Cyalgi | 30-10-2026 |

---

## 1. Introduction

**Purpose:** This document defines the test plan for the Hostel Management System v2.0. It outlines test objectives, scope, strategy, resources, schedule, and responsibilities for all levels of testing.

**Scope:** Testing covers all 10 functional modules (FR-01 to FR-10), 8 non-functional requirements (NFR-01 to NFR-08), and DevOps/Setup verification. Hardware, external payment gateways, and university ERP internals are excluded.

**References:**
- HMS Software Requirements Specification (SRS_Document.md)
- HMS Software Architecture Document (Software Architecture Document - Hostel Management System.md)
- HMS Test Plan Matrix (TEST_PLAN_MATRIX.md)
- HMS Backlog and Sprint Plan (BACKLOG_SPRINT_PLAN.md)

**Definitions:**
- **UT:** Unit Test — tests a single function, method, or view in isolation
- **IT:** Integration Test — tests interaction between two or more modules
- **ST:** System Test — tests end-to-end user scenarios across the full system
- **NFR:** Non-Functional Requirement test — verifies security, performance, reliability, etc.

---

## 2. Test Items

The following modules are under test:

| Module | Django App | Description |
|--------|-----------|-------------|
| FR-01: User Login | `accounts` | Authentication, session management, lockout, password reset |
| FR-02: Student Registration | `students` | Student CRUD, duplicate checks, validation |
| FR-03: Room Management | `rooms` | Room CRUD, capacity, vacancy tracking |
| FR-04: Room Allocation | `allocation` | Allocation, transfer, de-allocation, reports |
| FR-05: Fee Management | `fees` | Fee definition, payments, receipts, reports |
| FR-06: Complaint Management | `complaints` | Complaint submission, demerit points, escalation |
| FR-07: Attendance Management | `attendance` | Check-in/out logging, bulk marking, reports |
| FR-08: Visitor Management | `visitors` | Visitor check-in/out, logs, reports |
| FR-09: Leave Application | `leave` | Leave submission, approval workflow |
| FR-10: Notice Management | `notices` | Notice publishing, audience targeting |
| Setup / DevOps | `core` | CI pipeline, templates, seed data, notification service |
| NFR Verification | `core` | Security, performance, integrity, availability |

---

## 3. Features to be Tested

Features mapped to SRS requirement IDs:

### Functional Features
- **FR-01-001 to FR-01-010:** Login, authentication, session, lockout, password reset, account management
- **FR-02-001 to FR-02-007:** Student registration, duplicate checks, auto-generated credentials
- **FR-03-001 to FR-03-008:** Room CRUD, capacity, vacancy, filtering, deletion protection
- **FR-04-001 to FR-04-007:** Room allocation, capacity enforcement, transfers, reports
- **FR-05-001 to FR-05-007:** Fee definition, payment recording, receipts, status, reports
- **FR-06-001 to FR-06-005:** Complaint submission, demerit points, status workflow, reports
- **FR-07-001 to FR-07-005:** Attendance check-in/out, duplicate prevention, bulk marking, reports
- **FR-08-001 to FR-08-005:** Visitor check-in/out, ID proof validation, logs, reports
- **FR-09-001 to FR-09-006:** Leave submission, date validation, approval workflow, overlap detection
- **FR-10-001 to FR-10-008:** Notice CRUD, audience targeting, ordering, role restrictions

### Non-Functional Features
- **NFR-SEC-01 to NFR-SEC-07:** RBAC, password hashing, session security, XSS/SQL injection prevention, data isolation
- **NFR-02:** Usability (documentation-based verification)
- **NFR-03:** Performance (response time under 3 seconds)
- **NFR-04:** Reliability (backup/restore, transactional integrity)
- **NFR-05:** Data integrity (database constraints)
- **NFR-06:** Maintainability (modular structure, coding standards)
- **NFR-07:** Scalability (multi-hostel support)
- **NFR-08:** Availability (health check, maintenance handling)

---

## 4. Features Not to be Tested

- University ERP integration (not in scope)
- External payment gateway processing (no third-party APIs used)
- Mobile native application testing (web-only system)
- Load/stress testing with thousands of concurrent users (scale assumption: hundreds of students)
- Browser-specific rendering differences (Bootstrap handles cross-browser compatibility)

---

## 5. Test Approach / Strategy

### 5.1 Test Levels

| Level | Description | Tool | Count |
|-------|-------------|------|-------|
| **Unit Testing** | Test individual views, forms, services, and model methods in isolation | Django TestCase, pytest | ~500 tests |
| **Integration Testing** | Test module interactions (e.g., allocation updates room occupancy) | Django TestCase with related fixtures | ~120 tests |
| **System Testing** | End-to-end user scenarios across the full system | Django Client with session tracking | ~50 tests |
| **NFR Testing** | Security headers, performance, backup, constraints, health check | Custom test classes in `core/test_nfr.py` | 11 tests |

### 5.2 Test Types

| Type | What It Covers | Strategy |
|------|---------------|----------|
| **Functional Testing** | All FRs per acceptance criteria | Automated via `python manage.py test` |
| **Regression Testing** | All existing tests after each change | CI pipeline runs full suite on every PR |
| **Performance Testing** | Response time for 19 major endpoints | `scripts/benchmark_performance.py` |
| **Security Testing** | RBAC, session handling, XSS, SQL injection | NFR test suite + settings audit |
| **Usability Testing** | Navigation, form clarity, error messages | Documented review in `usability-review.md` |

### 5.3 Entry Criteria

- Stable build delivered (all migrations apply cleanly)
- Test data available via `python manage.py seed_data`
- Test environment ready (Python 3.12, Django 5.2, dependencies installed)
- `python manage.py check` reports no issues

### 5.4 Exit Criteria

- 100% of planned test cases executed
- 0 critical defects open
- All acceptance criteria from the SRS satisfied
- `python manage.py test` passes with 679+ tests
- Performance benchmark shows all endpoints under 3 seconds
- `ruff check .` passes with zero warnings

### 5.5 Security Validation

- RBAC verification: all 10+ app views tested with wrong-role credentials asserting 403
- Password hashing validation: verify `pbkdf2_sha256$` prefix on stored passwords
- Session security: HttpOnly cookies, 30-minute timeout, CSRF protection
- XSS prevention: inject `<script>` tags and verify HTML-escaping in output
- SQL injection prevention: code grep confirms no `.raw()`, `cursor.execute()`, or `RawSQL()`
- Data isolation: cross-student access attempts return 403

---

## 6. Test Environment

### Hardware

- **Development:** Student laptop (Windows/Linux, 8GB+ RAM)
- **CI:** GitHub Actions runner (Ubuntu latest, Python 3.12)

### Software

| Component | Version |
|-----------|---------|
| Python | 3.12 |
| Django | 5.2 |
| SQLite | 3.x (development) |
| Ruff | Latest (linting) |
| GitHub Actions | CI runner |

### Tools

| Tool | Purpose |
|------|---------|
| Django TestCase | Unit, integration, and system test execution |
| Django Test Client | HTTP request simulation |
| `python manage.py test` | Test runner |
| `ruff check .` | Code quality verification |
| `scripts/benchmark_performance.py` | Performance measurement |
| GitHub Actions CI | Automated test execution on PRs |

### Test Data

- Seeded via `python manage.py seed_data`
- Demo accounts: `admin01` (Admin), `wdn05` (Warden), `stu1023` (Student), `stu2024` (Student)
- Demo rooms: A-101 (capacity 3), B-204, C-102
- Demo fee records and hostel data

---

## 7. Test Schedule

| Milestone | Date | Owner |
|-----------|------|-------|
| Test case design (Sprint 1) | 19-Oct-2026 | Both |
| Test execution: FR-01 to FR-05 | 19-23 Oct 2026 | Both |
| Test case design (Sprint 2) | 26-Oct-2026 | Both |
| Test execution: FR-06 to FR-10 | 26-29 Oct 2026 | Both |
| NFR verification | 29-30 Oct 2026 | abhijeetcyalgi |
| Full regression run | 30-Oct-2026 | Both |
| Documentation freeze | 30-Oct-2026 | Both |

---

## 8. Test Deliverables

| Deliverable | Location |
|-------------|----------|
| Test Plan (this document) | `Documents/Test_Plan_Document.md` |
| Test Case Matrix | `TEST_PLAN_MATRIX.md` |
| Automated Test Scripts | `*/tests.py` and `core/test_nfr.py` in each app |
| Performance Benchmark Script | `scripts/benchmark_performance.py` |
| Performance Baseline Report | `Documents/process/performance-baseline.md` |
| Usability Review | `Documents/process/usability-review.md` |
| Test Execution Logs | CI pipeline output on GitHub Actions |
| NFR Verification Report | `Documents/design/nfr-hardening-report.md` |

---

## 9. Roles and Responsibilities

| Role | Name | Responsibilities |
|------|------|-----------------|
| **QA Lead / Developer** | abhijeetcyalgi | NFR test design and execution, performance benchmarks, documentation tests, Sprint 2 module tests |
| **Developer / QA** | Shashankb30 | Sprint 1 module tests, CI pipeline setup, integration tests, regression testing |

---

## 10. Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Test environment instability | Low | High | Docker-like reproducibility with seed data; CI on clean runners |
| Incomplete test data | Medium | Medium | `seed_data` command loads all required test accounts, rooms, and fees |
| Flaky tests due to timing | Low | Medium | Performance tests use generous 3-second threshold |
| Database lock contention on SQLite | Low | Low | Tests use separate test database per run |

---

## 11. Assumptions & Dependencies

- Python 3.12 and all pip dependencies are installed (`pip install -r requirements.txt`)
- `python manage.py migrate` has been run before test execution
- Seed data is loaded via `python manage.py seed_data`
- CI pipeline is configured and active on the GitHub repository
- Test database is destroyed and recreated for each test run (Django default behavior)

---

## 12. Suspension & Resumption Criteria

**Suspend testing if:**
- Build fails to compile or migrate (blocking > 50% of test cases)
- Test environment unavailable for > 2 hours
- Critical security vulnerability discovered requiring immediate fix

**Resume testing when:**
- Blocking defects are resolved and verified
- Environment is stabilized
- Security patches are applied and regression-tested

---

## 13. Test Case Management & Traceability

The RTM ensures mapping of SRS requirements to test cases:

| SRS Requirement | Test Case IDs | Test Level |
|-----------------|---------------|------------|
| FR-01 (Login) | UT_01-03, IT_01-03, ST_01-02, UT_LOGIN_04-05, ST_LOGIN_03-04, IT_LOGIN_04-06 | UT, IT, ST |
| FR-02 (Student Reg.) | UT_04-06, IT_04-06, ST_03-04, UT_REG_07-08, IT_REG_07 | UT, IT, ST |
| FR-03 (Room Mgmt.) | UT_07-09, IT_07-09, ST_05-06, UT_ROOM_10-13, IT_ROOM_12-14 | UT, IT, ST |
| FR-04 (Allocation) | UT_10-12, IT_10-12, ST_07-08 | UT, IT, ST |
| FR-05 (Fees) | UT_13-15, IT_13-15, ST_09-10, UT_FEE_04-07, IT_FEE_04, ST_FEE_03 | UT, IT, ST |
| FR-06 (Complaints) | UT_16-18, IT_16-18, ST_11-12 | UT, IT, ST |
| FR-07 (Attendance) | UT_19-21, IT_19-21, ST_13-14 | UT, IT, ST |
| FR-08 (Visitors) | UT_22-24, IT_22-24, ST_15-16 | UT, IT, ST |
| FR-09 (Leave) | UT_25-27, IT_25-27, ST_17-18 | UT, IT, ST |
| FR-10 (Notices) | UT_28-30, IT_28-30, ST_19-20 | UT, IT, ST |
| NFR-01 (RBAC) | UT_NFR_01 | NFR |
| NFR-02 (Passwords) | UT_NFR_02 | NFR |
| NFR-03 (Isolation) | UT_NFR_03 | NFR |
| NFR-04 (XSS) | UT_NFR_04 | NFR |
| NFR-06 (Performance) | UT_NFR_06 | NFR |
| NFR-07 (Indexes) | UT_NFR_07 | NFR |
| NFR-08 (Backup) | UT_NFR_08 | NFR |
| NFR-09 (Transactions) | UT_NFR_09 | NFR |
| NFR-10 (Constraints) | UT_NFR_10 | NFR |
| NFR-11 (Ruff) | UT_NFR_11 (ruff check) | NFR |
| NFR-12 (Multi-hostel) | UT_NFR_12 | NFR |
| NFR-13 (Health) | UT_NFR_13 | NFR |

Full test case details with steps, data, and results are in [`TEST_PLAN_MATRIX.md`](TEST_PLAN_MATRIX.md).

---

## 14. Test Metrics & Reporting

### Metrics Collected

| Metric | Current Value |
|--------|---------------|
| Total test cases designed | 127 |
| Total automated tests | 679+ |
| Test cases executed | 127 |
| Test cases passed | 117 |
| Test cases pending (manual verification) | 10 |
| Defects found | 0 critical, 0 high |
| Requirement coverage | 100% (all FRs and NFRs have test cases) |
| Code lint warnings | 0 (ruff check passes) |
| Performance endpoints passing | 19/19 (all under 3s) |

### Reports

- **Per-PR:** CI pipeline posts test results on each pull request
- **Performance:** `Documents/process/performance-baseline.md` updated per sprint
- **Final:** Test Summary integrated into this document's metrics section

---

## 15. Approvals

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Team Lead | Shashank B Jain | 30-10-2026 | Approved |
| QA / Developer | Abhijeet Cyalgi | 30-10-2026 | Approved |

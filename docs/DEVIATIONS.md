# Deviations from the submitted SRS, SAD and Test Plan

*FAQ rule: deviations are acceptable if documented and explained at the demo. This list was produced by comparing the code (commit state of the zip, 2026-11-05) with the submitted documents, README and backlog.*

## A. Behaviour differs from the earlier documents

| ID | Earlier statement | What the code does | Why / decision | Document corrected |
|---|---|---|---|---|
| D-01 | SAD v1 §5.2.3: account locks for **15 minutes** after 5 failures | Locks after `HMS_MAX_FAILED_LOGINS` (default 5) and **stays locked until an administrator unlocks it** (UI button or `manage.py unlock_account`) | Admin unlock is stronger against guessing and matches Test Plan IT_LOGIN_06 | SRS FR-01.4, SAD §5 |
| D-02 | README: notices target "all / block / role" | Audiences are **all / students / wardens**, scoped by hostel | SRS FR-10 only requires publishing to the intended audience | SRS FR-10.1 |
| D-03 | README / backlog: "priority assignment" with several rules | One configurable rule: **seniority** (year of study × weight) | Test Plan UT_12 only requires senior-first | SRS FR-04.3 |
| D-04 | SAD v1 §7: "all lists are paginated" | Pagination (25/page) exists on student, leave, notice and visitor lists only | Other lists are short or bounded by a filter | SAD §2, SRS NFR-07 |
| D-05 | SAD v1 §5.2.5 file names (`core/services.py`, `accounts/backends.py`, `accounts/signals.py`, `docs/...`) | Notification service is `core/notifications.py`; authentication is `accounts/services.py`; tests are `test_*.py` files per app | Names changed during implementation | SAD §4.3 |
| D-06 | SRS NFR numbers 01–08 only | Code comments, backlog issues and test names use `NFR.01..NFR.13` / `UT_NFR_01..13` | Backlog numbers are issue numbers, not SRS IDs; mapping is in Test Plan §5.3 | Test Plan |

## B. Planned in README / backlog but not found in the code

These appear in `README.md` or `BACKLOG_SPRINT_PLAN.md` scope text but have no implementation or test. Either implement them or state them as descoped at the demo.

| ID | Item claimed | Module | Evidence searched |
|---|---|---|---|
| D-07 | Audit logging / "system audit logs"; application logging (`LOGGING`) | CROSSCUT | no model, view or settings entry |
| D-08 | Batch import of students | FR-02 | no import code |
| D-09 | Visitor pass generation | FR-08 | no pass number/field |
| D-10 | Curfew violation log; biometric register | FR-07 | not present (attendance is manual check-in/out) |
| D-11 | Parent notification; leave balance records | FR-09 | not present |
| D-12 | Pinned announcements; notice category tags | FR-10 | not present |

## C. Implemented beyond the SRS (extra scope)
Password reset by e-mail (UT_LOGIN_05); user administration with lock/unlock (IT_LOGIN_04..06); allocation waitlist and rules screen; bulk attendance; leave resubmission, cancellation and "more information" status; CSV exports of dues and reports; backup/restore commands; health endpoint.

## D. Documentation inconsistencies fixed or to be fixed
| ID | Issue | Action |
|---|---|---|
| D-13 | `final-demo-and-report.md` says CI runs *pytest* and "100 % automated test coverage" | CI runs `manage.py test`; the 100 % meant "every plan case has an automated test". Real coverage is in `docs/reports/` |
| D-14 | `final-test-summary-report.md` totals 48 UT / 39 IT / 34 ST (121) | `TEST_PLAN_MATRIX.md` has 61 UT / 37 IT / 23 ST (121 rows). Totals match, split does not — use the matrix split |
| D-15 | Test summary says Python 3.14 / Windows | CI uses 3.12; the re-run for this submission used 3.12 |
| D-16 | Issue ranges differ between `BACKLOG_SPRINT_PLAN.md` and the traceability matrix (e.g. FR-02 #28–39 vs #27–38) | Re-export issue numbers from GitHub before the viva |
| D-17 | SAD v1 referred to a "section 9" for deviations that did not exist | Section 8 of the SAD now points to this file |

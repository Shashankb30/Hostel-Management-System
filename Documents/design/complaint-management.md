# Complaint Management (FR-06)

Traceability: FR-06 (R6) · UC-06 · Issues #81 to #93 · Tests `UT_16_Comp` to `UT_18_Comp`, `IT_16_Comp` to `IT_18_Comp`, `ST_11_Comp`, `ST_12_Comp`

Code: `complaints/` (services, views, urls), models in `core/models.py`, migration `core/migrations/0004_complaint_management.py`.

## Who can do what

| Role | Screens |
|---|---|
| Student | `/complaints/` raise a complaint, see own complaints, demerit points and history; edit an open complaint |
| Warden, Administrator | `/complaints/manage/` list and filter, log misconduct, update status, reopen, escalate, demerit rules, summary report |

## Rules (all in `complaints/services.py`)

| Issue | Rule |
|---|---|
| #81 | A student raises a complaint with a category and description. It starts **Open** and gets an ID such as `CMP00012`. |
| #82 | Category and description are required; the description is at most 2000 characters. Every error is shown together. |
| #83 | A warden or administrator logs a misconduct case against a student. |
| #84 | The warden list filters by status, category, type (complaint or misconduct), escalated, and free text. |
| #85 | Demerit points per severity are stored in `DemeritRule` (default Minor 1, Moderate 3, Major 5) and editable. Old records keep the points they were given. |
| #86 | Logging a case adds a `DemeritRecord` with the points of its severity. |
| #87 | A student's total is the sum of their `DemeritRecord` points. |
| #88 | Status moves Open, Under Review, Resolved. Resolving needs remarks. Every change is kept as a `ComplaintUpdate`. |
| #89 | The student gets an in-app `COMPLAINT` notification on every status change, reopening, and misconduct case. |
| #90 | A case is escalated to the administrator when it is Major, when the student has 3 misconduct cases, when their total reaches 10 points, or when they have 3 unresolved complaints in one category. Staff can also escalate by hand. Administrators are notified. |
| #91 | A resolved complaint cannot be edited or moved; it must be reopened first (remarks required). |
| #92 | A student sees only their own complaints, history and demerit points. |
| #93 | The summary report counts complaints per category and status, for an optional date range, and can be downloaded as CSV. |

Staff see the complaints of their own hostel. An account with no hostel sees all.

## Thresholds

`ESCALATE_AFTER_CASES = 3` and `ESCALATE_AT_POINTS = 10` at the top of `complaints/services.py`. These are design choices pending SRS confirmation.

## Migration

Like `0002` and `0003`, `0004` only adds what is missing (new `complaint` columns, the `demerit_rule` and `complaint_update` tables) because `0001` builds tables from the live models. It also seeds the three default rules. It depends on `0003_allocationrule` (FR-04).

# Attendance Management (FR-07)

Traceability: FR-07 (R7) · UC-07 · Issues #95 to #103 · Tests `UT_19_Att` to `UT_21_Att`, `IT_19_Att` to `IT_21_Att`, `ST_13_Att`, `ST_14_Att`

Code: `attendance/` (services, views, urls, template tag). It uses the existing `AttendanceRecord` table, so there is **no migration**.

## Who can do what

| Role | Screens |
|---|---|
| Warden, Administrator | `/attendance/manage/` daily present and absent, check in, check out, bulk marking; `/attendance/manage/report/` report by date range with CSV; `/attendance/manage/student/<id>/` one student's history |
| Student | `/attendance/` My Attendance: the student's own entries |

Staff work with the students of their own hostel (every hostel if their account has none).

## How an entry works

One student has at most one attendance entry per day (`uq_attendance_student_date`). A check-in opens the entry for that day. The matching check-out closes it, even the next morning (check-in 8:00 PM, check-out 9:30 AM next day is one entry). "Present" on a day means the student has an entry with a check-in on that day.

## Rules (all in `attendance/services.py`)

| Issue | Rule |
|---|---|
| #95 | Check-in records the time given (or now) and who recorded it. The time cannot be in the future. |
| #96 | Check-out closes the student's open entry and cannot be before the check-in. |
| #97 | A second check-in while one is still open is refused with "already checked in since ...". Open entries from earlier days are listed as warnings on the daily page. |
| #98 | Check-out with no open entry shows "No active check-in exists", or "Already checked out" if today's entry is finished. |
| #99 | Only active students with an active room allocation can be checked in. |
| #100 | Bulk marking uses one time for every selected student. Each student succeeds or fails on its own and failures are listed. |
| #101 | The daily summary lists Present or Absent for every student with a room, with counts. |
| #102 | A student's history is on My Attendance and the staff history page. Any page, such as the student profile, can show it with `{% load attendance_tags %}{% attendance_history student %}`. |
| #103 | The report filters by date range (default last 7 days) and student, shows days present per student, and downloads as CSV. Cells that look like formulas are escaped. |

A student cannot check in twice on the same day after checking out; the screen says the day is already complete.

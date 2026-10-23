# FR-04 Room Allocation (Epic #52, stories #53-#65)

Warden screens live under `/allocation/` (app `allocation`); all rules are in `allocation/services.py`.
Models stay in `core` (`Allocation`, `AllocationRequest`, new `AllocationRule`, migration `0003`).

| Story | Where |
| :-- | :-- |
| 53 vacant rooms for a student | `services.vacant_rooms`, **Allocate** tab |
| 54 allocate | `services.allocate`, `POST /allocation/allocate/` |
| 55 priority rules stored/editable | `AllocationRule`, **Priority rules** tab |
| 56 apply rules | `priority_score`, `priority_conflicts`, room ordering in `vacant_rooms` |
| 57 waitlist | `add_to_waitlist` / `waitlist` / `remove_from_waitlist`, **Waitlist** tab |
| 58 block full room, refresh list | `_ensure_room_available` -> "Room unavailable"; page reloads with fresh list |
| 59 second allocation needs transfer | `already_allocated` -> redirect to the transfer confirmation page |
| 60 transfer | `services.transfer`, confirm page before saving; old row kept as `transferred` |
| 61 notify student | `core.notifications.notify(student, 'ALLOCATION', ...)` on allocate / transfer / vacate |
| 62 no vacant rooms | "No vacant rooms available" (service error + friendly page, offers waitlist) |
| 63 report | **Report** tab: date range, status, CSV export |
| 64 concurrency | allocate/transfer run in one transaction and lock the room row before counting |
| 65 vacate | `services.vacate`, "Release room" button; allocation becomes `ended` |

## Priority rule (needs team confirmation, story 55 says "documented in SRS after clarification")
Score = sum of `weight x value` over active rules. Only **seniority** (year of study) exists today.
Higher score first; equal scores first come, first served. A student is *flagged* only when a
higher-scoring waiting student would be left without a bed (waiting seniors >= free beds);
the warden can override with "Allocate anyway". New criteria = new `AllocationRule.CRITERION_*`
choice plus one branch in `services.priority_score`.

## Notes
* Candidate rooms are active rooms in the **student's own hostel**.
* Concurrency: `SELECT ... FOR UPDATE` is effective on PostgreSQL; SQLite serialises writers.
  The one-active-allocation-per-student rule is also enforced by a database constraint.

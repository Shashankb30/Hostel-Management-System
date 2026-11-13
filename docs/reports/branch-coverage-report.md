# Branch Coverage Report

Generated: 2026-11-06 | Tool: coverage.py 7.17.0 with `--branch` | Suite: **681 tests, 0 failures**

**TOTAL branches: 810 | covered: 682 | missing: 128 | partial branches: 100 | branch coverage: 84.2%**

Combined statement + branch coverage reported by coverage.py: **93%**

| File | Branches | Covered | Missing | Branch coverage % |
|---|---:|---:|---:|---:|
| `accounts/forms.py` | 6 | 6 | 0 | 100.0 |
| `accounts/lockout.py` | 4 | 4 | 0 | 100.0 |
| `accounts/middleware.py` | 2 | 2 | 0 | 100.0 |
| `accounts/services.py` | 14 | 14 | 0 | 100.0 |
| `accounts/user_forms.py` | 10 | 10 | 0 | 100.0 |
| `accounts/user_service.py` | 4 | 3 | 1 | 75.0 |
| `accounts/user_views.py` | 14 | 11 | 3 | 78.6 |
| `accounts/views.py` | 6 | 4 | 2 | 66.7 |
| `allocation/services.py` | 48 | 45 | 3 | 93.8 |
| `allocation/views.py` | 32 | 29 | 3 | 90.6 |
| `attendance/services.py` | 52 | 52 | 0 | 100.0 |
| `attendance/templatetags/attendance_tags.py` | 2 | 2 | 0 | 100.0 |
| `attendance/views.py` | 18 | 17 | 1 | 94.4 |
| `complaints/services.py` | 92 | 90 | 2 | 97.8 |
| `complaints/views.py` | 32 | 26 | 6 | 81.2 |
| `core/admin.py` | 2 | 2 | 0 | 100.0 |
| `core/context_processors.py` | 2 | 2 | 0 | 100.0 |
| `core/error_messages.py` | 2 | 2 | 0 | 100.0 |
| `core/feedback.py` | 2 | 2 | 0 | 100.0 |
| `core/forms.py` | 6 | 4 | 2 | 66.7 |
| `core/management/commands/backup_database.py` | 6 | 1 | 5 | 16.7 |
| `core/management/commands/restore_database.py` | 10 | 4 | 6 | 40.0 |
| `core/management/commands/seed_data.py` | 4 | 4 | 0 | 100.0 |
| `core/models.py` | 28 | 15 | 13 | 53.6 |
| `core/navigation.py` | 2 | 2 | 0 | 100.0 |
| `core/notifications.py` | 14 | 14 | 0 | 100.0 |
| `core/roles.py` | 6 | 6 | 0 | 100.0 |
| `core/seed.py` | 8 | 8 | 0 | 100.0 |
| `core/validators.py` | 44 | 43 | 1 | 97.7 |
| `core/views.py` | 8 | 6 | 2 | 75.0 |
| `fees/factories.py` | 2 | 1 | 1 | 50.0 |
| `fees/forms.py` | 10 | 9 | 1 | 90.0 |
| `fees/services.py` | 40 | 40 | 0 | 100.0 |
| `fees/views.py` | 22 | 22 | 0 | 100.0 |
| `leave/forms.py` | 6 | 4 | 2 | 66.7 |
| `leave/services.py` | 46 | 27 | 19 | 58.7 |
| `leave/views.py` | 30 | 15 | 15 | 50.0 |
| `notices/forms.py` | 4 | 2 | 2 | 50.0 |
| `notices/services.py` | 44 | 31 | 13 | 70.5 |
| `notices/views.py` | 22 | 12 | 10 | 54.5 |
| `rooms/forms.py` | 8 | 8 | 0 | 100.0 |
| `rooms/selectors.py` | 8 | 8 | 0 | 100.0 |
| `rooms/services.py` | 8 | 8 | 0 | 100.0 |
| `rooms/views.py` | 6 | 6 | 0 | 100.0 |
| `students/services.py` | 4 | 4 | 0 | 100.0 |
| `students/views.py` | 2 | 2 | 0 | 100.0 |
| `visitors/forms.py` | 10 | 6 | 4 | 60.0 |
| `visitors/services.py` | 34 | 29 | 5 | 85.3 |
| `visitors/views.py` | 24 | 18 | 6 | 75.0 |

## Files below 85% branch coverage (viva talking points)

`a->b` = a branch from line a to line b never taken; plain numbers/ranges = lines never executed.

| File | Branch % | Not covered (from `coverage report --show-missing`) |
|---|---:|---|
| `core/management/commands/backup_database.py` | 16.7 | 33-46 |
| `core/management/commands/restore_database.py` | 40.0 | 25, 28, 31-39, 50 |
| `fees/factories.py` | 50.0 | 43->45 |
| `leave/views.py` | 50.0 | 26, 68-69, 85-111, 122-132, 148-149, 172->174, 181->202, 192-196 |
| `notices/forms.py` | 50.0 | 50, 56 |
| `core/models.py` | 53.6 | 32->exit, 48->49, 70->71, 72->73, 73->exit, 118->exit, 131->132, 133->134, 195->197, 195->exit, 212->exit, 237->exit, 266, 272, 311, 357 |
| `notices/views.py` | 54.5 | 44, 46, 106-107, 128, 143-144, 149-154, 165-176, 187->189 |
| `leave/services.py` | 58.7 | 24, 31, 33, 67, 91, 111, 114, 133, 136, 138, 139->144, 142, 144->147, 148, 157-164, 187-188 |
| `visitors/forms.py` | 60.0 | 57, 63, 69, 105 |
| `accounts/views.py` | 66.7 | 34, 67->69 |
| `core/forms.py` | 66.7 | 7->exit, 26->exit |
| `leave/forms.py` | 66.7 | 43, 86-87 |
| `notices/services.py` | 70.5 | 24-28, 42, 62->68, 65, 68->74, 71, 75->78, 79, 82, 86, 141 |
| `accounts/user_service.py` | 75.0 | 35 |
| `core/views.py` | 75.0 | 89-91, 102, 115, 125, 140 |
| `visitors/views.py` | 75.0 | 79-80, 88-91, 108->110, 122, 136->140, 187->191, 193 |
| `accounts/user_views.py` | 78.6 | 32, 36, 68-69, 73 |
| `complaints/views.py` | 81.2 | 70, 91, 100-103, 107, 144->146, 191-192, 204-205 |

**Reading this:** the weakest areas are the leave and notice modules (views/services error paths and filters) and the backup/restore management commands (file-system branches). Core business modules — accounts login/lockout, allocation, fees, attendance — are at 95–100%.


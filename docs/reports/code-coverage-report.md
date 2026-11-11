# Code Coverage Report (statement coverage)

Generated: 2026-11-06 | Tool: coverage.py 7.17.0 (`python -m coverage run --branch manage.py test`) | Windows, local run by the team | Suite: **681 tests, 0 failures** (Ran 681 tests in 178 s — OK)

Reproduce (PowerShell): `$env:DJANGO_SECRET_KEY="local-dev-key"; $env:DJANGO_DEBUG="1"; python -m coverage run --branch manage.py test; python -m coverage report --show-missing; python -m coverage html -d docs/reports/coverage/html`

**TOTAL statements: 3537 | covered: 3357 | missed: 180 | statement coverage: 94.9%** (coverage.py combined statement+branch figure: 93%)

Full line-by-line view: `docs/reports/coverage/html/index.html`; machine-readable: `docs/reports/coverage/coverage.xml`. Omitted: migrations, test files, `scripts/`, `manage.py`, `config/wsgi.py` (see `.coveragerc`).

| File | Statements | Missed | Statement coverage % |
|---|---:|---:|---:|
| `accounts/apps.py` | 5 | 0 | 100.0 |
| `accounts/auth_urls.py` | 4 | 0 | 100.0 |
| `accounts/forms.py` | 36 | 0 | 100.0 |
| `accounts/lockout.py` | 24 | 0 | 100.0 |
| `accounts/management/commands/unlock_account.py` | 15 | 0 | 100.0 |
| `accounts/middleware.py` | 9 | 0 | 100.0 |
| `accounts/services.py` | 47 | 0 | 100.0 |
| `accounts/urls.py` | 4 | 0 | 100.0 |
| `accounts/user_forms.py` | 63 | 0 | 100.0 |
| `accounts/user_service.py` | 36 | 1 | 97.2 |
| `accounts/user_views.py` | 71 | 5 | 93.0 |
| `accounts/views.py` | 47 | 1 | 97.9 |
| `allocation/apps.py` | 5 | 0 | 100.0 |
| `allocation/forms.py` | 10 | 0 | 100.0 |
| `allocation/services.py` | 141 | 2 | 98.6 |
| `allocation/urls.py` | 4 | 0 | 100.0 |
| `allocation/views.py` | 158 | 6 | 96.2 |
| `attendance/apps.py` | 5 | 0 | 100.0 |
| `attendance/services.py` | 142 | 1 | 99.3 |
| `attendance/templatetags/attendance_tags.py` | 9 | 0 | 100.0 |
| `attendance/urls.py` | 4 | 0 | 100.0 |
| `attendance/views.py` | 120 | 0 | 100.0 |
| `complaints/apps.py` | 5 | 0 | 100.0 |
| `complaints/services.py` | 261 | 2 | 99.2 |
| `complaints/urls.py` | 4 | 0 | 100.0 |
| `complaints/views.py` | 163 | 11 | 93.3 |
| `config/settings.py` | 43 | 0 | 100.0 |
| `config/urls.py` | 8 | 0 | 100.0 |
| `core/admin.py` | 4 | 0 | 100.0 |
| `core/apps.py` | 5 | 0 | 100.0 |
| `core/context_processors.py` | 7 | 0 | 100.0 |
| `core/error_messages.py` | 13 | 0 | 100.0 |
| `core/feedback.py` | 4 | 0 | 100.0 |
| `core/forms.py` | 15 | 0 | 100.0 |
| `core/management/commands/backup_database.py` | 36 | 12 | 66.7 |
| `core/management/commands/restore_database.py` | 32 | 10 | 68.8 |
| `core/management/commands/seed_data.py` | 15 | 0 | 100.0 |
| `core/models.py` | 259 | 4 | 98.5 |
| `core/navigation.py` | 15 | 0 | 100.0 |
| `core/notifications.py` | 48 | 0 | 100.0 |
| `core/roles.py` | 27 | 0 | 100.0 |
| `core/seed.py` | 44 | 0 | 100.0 |
| `core/urls.py` | 4 | 0 | 100.0 |
| `core/validators.py` | 106 | 1 | 99.1 |
| `core/views.py` | 67 | 7 | 89.6 |
| `fees/apps.py` | 5 | 0 | 100.0 |
| `fees/factories.py` | 26 | 0 | 100.0 |
| `fees/forms.py` | 49 | 0 | 100.0 |
| `fees/services.py` | 145 | 4 | 97.2 |
| `fees/templatetags/fees_extras.py` | 6 | 0 | 100.0 |
| `fees/urls.py` | 4 | 0 | 100.0 |
| `fees/views.py` | 118 | 0 | 100.0 |
| `leave/apps.py` | 4 | 0 | 100.0 |
| `leave/forms.py` | 42 | 3 | 92.9 |
| `leave/services.py` | 98 | 21 | 78.6 |
| `leave/urls.py` | 4 | 0 | 100.0 |
| `leave/views.py` | 125 | 34 | 72.8 |
| `notices/apps.py` | 4 | 0 | 100.0 |
| `notices/forms.py` | 25 | 2 | 92.0 |
| `notices/services.py` | 82 | 11 | 86.6 |
| `notices/urls.py` | 4 | 0 | 100.0 |
| `notices/views.py` | 105 | 22 | 79.0 |
| `rooms/apps.py` | 5 | 0 | 100.0 |
| `rooms/forms.py` | 43 | 0 | 100.0 |
| `rooms/selectors.py` | 35 | 0 | 100.0 |
| `rooms/services.py` | 25 | 0 | 100.0 |
| `rooms/urls.py` | 4 | 0 | 100.0 |
| `rooms/views.py` | 84 | 2 | 97.6 |
| `students/apps.py` | 5 | 0 | 100.0 |
| `students/forms.py` | 31 | 0 | 100.0 |
| `students/services.py` | 35 | 0 | 100.0 |
| `students/urls.py` | 4 | 0 | 100.0 |
| `students/views.py` | 33 | 0 | 100.0 |
| `visitors/apps.py` | 4 | 0 | 100.0 |
| `visitors/forms.py` | 44 | 4 | 90.9 |
| `visitors/services.py` | 73 | 6 | 91.8 |
| `visitors/urls.py` | 4 | 0 | 100.0 |
| `visitors/views.py` | 118 | 8 | 93.2 |

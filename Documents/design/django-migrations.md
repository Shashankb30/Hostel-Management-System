# SETUP.08 — Django schema and migrations

## Implementation

The repository now has a Django 5.2 project (`config/`) and a schema-owning `core` app. The initial schema covers the multi-hostel root and the main entities used by account, student, room, allocation/waitlist, fee/payment, complaint/demerit, attendance, visitor, leave, and notice workflows. `core/models.py` is the ORM definition, with database constraints for unique student roll numbers, room numbers scoped to a hostel, one active allocation per student, positive room capacity/payment/demerit values, and valid date/time ranges. Occupancy, vacancy, fee balance/status, and demerit totals are derived rather than duplicated as stored columns.

`core/migrations/0001_initial.py` is the initial schema bootstrap migration. It creates tables and constraints using Django's schema editor, after Django's built-in authentication migration. The migration is intentionally a one-time bootstrap for this repository snapshot; for subsequent schema changes, use normal Django-generated `CreateModel`/`AddField`/`AlterField` migrations and do not edit an already-applied migration. Before production use, freeze this bootstrap into generated `CreateModel` operations so migration state is fully represented for `makemigrations --check`.

## Run locally

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py check
python manage.py migrate
python manage.py test core
python manage.py runserver
```

The default database is SQLite. PostgreSQL can be selected through `DB_ENGINE=django.db.backends.postgresql` and the `DB_*` environment variables after installing `psycopg` (`pip install psycopg[binary]`). Never commit a real `.env` or production secret.

## Test traceability

`UT_SETUP_06` in `TEST_PLAN_MATRIX.md` covers clean-database migration and schema integrity. The focused Django tests verify roll-number uniqueness, hostel-scoped room uniqueness, active-allocation uniqueness, and derived occupancy.

## Architecture note

The ADR describes one app per functional module. This first schema commit centralizes model definitions in `core` to keep the database foundation runnable while the module apps are introduced in subsequent setup issues; moving models to their owning apps must be done through explicit migrations and without changing the relational constraints.

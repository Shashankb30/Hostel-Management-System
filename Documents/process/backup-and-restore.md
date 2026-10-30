# 💾 Database Backup & Disaster Recovery Procedure (NFR-04)

**Document ID**: PROC-NFR-04  
**Sprint**: Sprint-2 [26th Oct to 30th Oct]  
**Backlog Issue**: `#150` (`[NFR.08] NFR-04: Backup and restore procedure`)  
**Assignee**: Abhijeet Cyalgi (`@abhijeetcyalgi`)  
**Status**: Verified & Operational  

---

## 1. Overview & Objectives

In accordance with **NFR-04** (System Reliability & Data Integrity), the Hostel Management System includes a standardized, reproducible procedure to create point-in-time snapshots of the database and restore them safely without data corruption.

---

## 2. Backup Architecture

HMS supports two backup strategies:
1. **JSON Fixture Backup (Portable across SQLite & PostgreSQL)**:
   - Serializes all model tables preserving primary and natural foreign keys in exact dependency order:
     `auth.user` -> `core` -> `accounts` -> `students` -> `rooms` -> `allocation` -> `attendance` -> `complaints` -> `fees` -> `visitors` -> `leave` -> `notices`.
2. **Binary Snapshot (SQLite fast filesystem copy)**:
   - Creates a byte-identical copy of `db.sqlite3` with timestamped naming.

---

## 3. Standard Operating Procedures (SOP)

### A. Creating a Database Backup

Run the automated management command:

```bash
# Standard JSON snapshot (default location: backups/hms_backup_<YYYYMMDD_HHMMSS>.json)
python manage.py backup_database

# Custom output destination
python manage.py backup_database --output backups/production_snapshot_v1.json

# Binary snapshot (SQLite development/staging)
python manage.py backup_database --sqlite-raw --output backups/db_snapshot.sqlite3
```

**Expected Output**:
```text
JSON database backup created successfully:
  File: backups\hms_backup_20261030_195740.json
  Size: 7.2 KB
```

---

### B. Restoring from a Backup

To restore data from a previous backup file:

```bash
# Restore from a JSON snapshot (executed inside an atomic transaction)
python manage.py restore_database backups/hms_backup_20261030_195740.json

# Restore from a binary SQLite backup
python manage.py restore_database backups/db_snapshot.sqlite3
```

**Expected Output**:
```text
Restoring database from JSON fixture: backups/hms_backup_20261030_195740.json...
Installed 20 object(s) from 1 fixture(s)
Database records restored successfully from fixture:
  backups/hms_backup_20261030_195740.json
```

---

## 4. Disaster Recovery & Verification Checklist

- [x] **Idempotency**: Successive restores from the same snapshot maintain exact entity states without generating orphaned foreign keys.
- [x] **Transaction Rollback**: If a record fails validation during JSON fixture restoration, the entire operation is rolled back using `transaction.atomic()`, preventing partial or corrupted state.
- [x] **Automated Test Coverage**: Tested in `core.test_nfr.SchemaIntegrityTests.test_UT_NFR_08__backup_and_restore_cycle`.

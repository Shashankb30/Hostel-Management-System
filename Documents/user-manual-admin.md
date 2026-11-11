# ⚙️ Administrator User Manual

**Hostel Management System (HMS)**  
**Version:** 2.0  
**Target Role:** System Administrator  
**Author:** @abhijeetcyalgi  

---

## 1. Introduction
This manual provides instructions for system administrators responsible for institutional setup, user provisioning, student onboarding, financial tracking, system backups, and health monitoring.

---

## 2. User & Access Administration (`/accounts/users/`)

### 2.1 Managing Users & Roles
- Access **Users & Roles** from the admin navigation bar.
- **Add New User:** Create accounts with username, email, full name, and assign one of three roles: `Student`, `Warden`, or `Administrator`.
- **Role Assignment:** Enforces strict role-based access control (RBAC). Non-admin users cannot access administrative endpoints.
- **Account Lockout & Unlock:**
  - View locked accounts (locked automatically after 5 failed login attempts).
  - Click **Unlock** on the user row to immediately restore login access.
- **Deactivation & Reactivation:** Inactive accounts cannot log in; reactivate when students return from leave or suspension.

---

## 3. Student Registration & Onboarding (`/students/`)

### 3.1 Registering New Students
1. Navigate to **Student Management** -> **Add New Student**.
2. Complete the verified fields:
   - **Full Name**, **Roll Number** (strictly unique across the institution).
   - **Email Address** (strictly unique, case-insensitive).
   - **Contact Phone** (numeric validation enforced).
   - **Course**, **Academic Year**, and **Permanent Address**.
3. Upon saving:
   - The system automatically generates a unique institutional **Student ID** (e.g., `STU00012`).
   - A linked user login account is created with auto-generated credentials displayed for the onboarding slip.

---

## 4. Room & Hostel Inventory Management (`/rooms/`)

### 4.1 Room Configuration
- Navigate to **Room Management** -> **Add Room**.
- Specify **Room Number**, **Hostel / Block**, **Floor**, and **Capacity** (must be a positive integer >= 1).
- **Safety Invariant:** Capacity cannot be reduced below the number of current occupants.
- Rooms with active occupants cannot be deleted.

---

## 5. Fee Structure & Payment Ledger (`/fees/`)

### 5.1 Defining Fees
- Define academic hostel fees per student or cohort (academic year, description, total amount).
- Duplicate fees for the same year and description are rejected.

### 5.2 Recording Payments & Issuing Receipts
- Select the student and click **Record Payment**.
- Enter amount paid (must be > 0 and <= outstanding balance) and payment mode:
  - `Cash`, `Online`, `Card`, or `Bank Transfer`.
- Saving generates an official receipt with a unique serial number (`RCT-YYYY-XXXXX`).
- Fee status automatically updates from `Due` -> `Partially Paid` -> `Paid`.

### 5.3 Financial Reports & Dues Export
- Access **Outstanding Dues Report** to view all residents with unpaid balances.
- Filter by overdue status and click **Download CSV** for institutional bursar reporting.

---

## 6. System Operations & Maintenance

### 6.1 Database Backup & Restore
The system provides verified management commands for complete data backup and restoration:
- **Create Backup:**
  ```bash
  python manage.py backup_database
  ```
  Creates a timestamped JSON dump in `backups/hms_backup_YYYYMMDD_HHMMSS.json`.
- **Restore from Backup:**
  ```bash
  python manage.py restore_database backups/hms_backup_YYYYMMDD_HHMMSS.json
  ```
  Restores database state atomically inside a single transaction.

### 6.2 Health Monitoring & Maintenance
- **Health Check Probe:** Query `GET /health/` for JSON monitoring:
  ```json
  {"status": "ok", "database": "connected", "service": "Hostel Management System"}
  ```
- **Maintenance Notice:** `GET /maintenance/` provides a user-friendly notice during scheduled maintenance windows.

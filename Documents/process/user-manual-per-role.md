# Hostel Management System (HMS) - User Manual by Role

**Module:** DOC.05 (Issue #179)  
**Parent Epic:** [DOC] Documentation & Requirement Clarifications (#174)  

---

## 1. Student User Manual

### 1.1 Access & Dashboard
- Navigate to the login page (`/accounts/login/`).
- Sign in using your assigned student username (e.g., `stu1023`) and password.
- Upon successful authentication, the **Student Dashboard** displays:
  - Current room allocation and roommate details.
  - Quick summary of fee dues and upcoming deadlines.
  - Active complaints and demerit points.
  - Latest hostel notices and broadcasts.

### 1.2 Room & Amenities
- Open **My Room** (`/allocation/my-room/`) to inspect room number, hostel block, floor, capacity, and current roommates.

### 1.3 Fees & Invoices
- Go to **Fees & Payments** (`/fees/my-fees/`).
- Review total assessed fees, payments made, and current outstanding balance.
- Click **View Receipt** next to any completed payment to view and download printable payment confirmation receipts.

### 1.4 Complaints & Maintenance
- Click **File Complaint** (`/complaints/submit/`).
- Select category (*Maintenance*, *Discipline*, *Mess*, *Other*), enter a clear description, and submit.
- Track resolution status (*Open*, *Under Review*, *Resolved*) and view any assigned demerit points.

### 1.5 Leave Applications
- Click **Apply Leave** (`/leave/apply/`).
- Select start date, end date, and state your leave reason.
- Monitor application status (*Pending*, *Approved*, *Rejected*).

---

## 2. Warden User Manual

### 2.1 Access & Dashboard
- Sign in with Warden credentials (`/accounts/login/`).
- The **Warden Dashboard** provides real-time occupancy counts, pending complaints, leave requests, and attendance registers.

### 2.2 Room Allocation & Vacancy
- Navigate to **Rooms & Vacancy** (`/rooms/warden/`).
- View room availability by block and floor.
- Mark rooms as unavailable or available for maintenance.
- Allocate vacant rooms or process room transfer requests based on priority rules.

### 2.3 Attendance Tracking
- Navigate to **Attendance Register** (`/attendance/`).
- Record individual or bulk check-in / check-out timestamps.
- Generate daily attendance summaries and export range reports.

### 2.4 Visitor Logs
- Open **Visitor Management** (`/visitors/`).
- Log new visitors: name, contact number, host student roll number, relation, check-in timestamp.
- Record check-out when the visitor departs to maintain strict security.

### 2.5 Leave Review & Complaints
- Review student leave requests under `/leave/` and approve or reject with mandatory remarks.
- Investigate complaints under `/complaints/`, log misconduct cases, and assign demerit points based on policy severity.

---

## 3. Administrator User Manual

### 3.1 Access & Administrative Hub
- Sign in with Administrator credentials (`/accounts/login/`).
- Full access to system configurations, user administration, and master registers.

### 3.2 Student Management
- Navigate to **Students** (`/students/`).
- Register new students, update profiles, or archive inactive records.
- Filter and search student records by name, roll number, or department.

### 3.3 Fee Management & Billing
- Navigate to **Fee Management** (`/fees/`).
- Define fee structures per student or semester.
- Record manual payments (Cash, Bank Transfer, Online, Card).
- Generate and download the **Outstanding Dues Report** with CSV export.

### 3.4 System Hardening & Maintenance
- Perform database JSON backups via `python manage.py backup_database`.
- Restore database states via `python manage.py restore_database`.
- Monitor system health check at `/health/` and manage scheduled maintenance windows.

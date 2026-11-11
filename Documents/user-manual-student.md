# 🎓 Student User Manual

**Hostel Management System (HMS)**  
**Version:** 2.0  
**Target Role:** Student Resident  
**Author:** @abhijeetcyalgi  

---

## 1. Introduction
Welcome to the Hostel Management System (HMS). This manual guides student residents through all available features, workflows, and self-service capabilities.

---

## 2. Getting Started & Logging In

### 2.1 First-Time Access
1. Your account credentials (Roll Number / Student ID and temporary password) are provisioned upon registration by the hostel administrator.
2. Open the application URL in any modern desktop or mobile browser.
3. Enter your assigned username and password, then click **Log In**.
4. Upon successful authentication, you will be redirected to the **Student Dashboard**.

### 2.2 Account Security & Lockout
- **Lockout Policy:** If you enter an incorrect password 5 consecutive times, your account is automatically locked for 15 minutes to prevent unauthorized access.
- **Forgot Password:** Click the **Forgot password?** link on the login page, enter your registered email address, and follow the secure link sent to your inbox.
- **Session Timeout:** Sessions remain active while browsing. If left idle for 30 minutes, you will be securely logged out.

---

## 3. Student Dashboard Overview
The Student Dashboard provides immediate visibility into:
- **Residency Status:** Assigned hostel, block, room number, and roommate count.
- **Financial Summary:** Total fee demanded, amount paid, and current outstanding dues.
- **Disciplinary Record:** Active complaints and accumulated demerit points.
- **Announcements:** Latest broadcast notices and administrative alerts.
- **Quick Actions:** Submit Leave Application, File Complaint, View Receipts.

---

## 4. Key Resident Workflows

### 4.1 Room & Accommodation Details (`/allocation/my-room/`)
- Navigate to **My Room** in the navigation bar.
- If allocated: Displays room number, capacity, occupancy, room type (Single, Double, Triple), and assigned roommates.
- If unallocated: An informative empty state is shown; contact the Warden or check room allocation notices.

### 4.2 Fee Invoices & Payment Receipts (`/fees/my-fees/`)
- Navigate to **Fees & Payments**.
- **Fee Summary:** View total fees, payments made, and remaining balance.
- **Payment History:** Review chronological records of payments with date, amount, and payment mode (Cash, Online, Card, Bank Transfer).
- **Download Receipts:** Click on any completed payment entry to view and print the official receipt (format: `RCT-YYYY-XXXXX`).
- *Note:* Students can only view their own fees; cross-student access is strictly blocked by RBAC.

### 4.3 Filing Complaints & Misconduct Tracking (`/complaints/`)
- Navigate to **Complaints** -> **Submit New Complaint**.
- Select the relevant category: **Maintenance**, **Mess/Food**, **Discipline**, or **General**.
- Enter a concise title and clear description of the issue, then click **Submit**.
- Track status:
  - `Open`: Logged and awaiting warden review.
  - `In Progress`: Under active investigation or maintenance dispatch.
  - `Resolved`: Rectified by the warden with completion remarks.
- **Demerit Points:** Check your profile for any disciplinary points assigned per institutional policy.

### 4.4 Daily Attendance Log (`/attendance/my-attendance/`)
- Navigate to **Attendance**.
- Review your daily check-in and check-out logs timestamped by the warden.
- Verify status flags (Present, Late, Absent).

### 4.5 Applying for Home / Long Leave (`/leave/`)
- Navigate to **Leave Application** -> **Apply for Leave**.
- Fill in:
  - **Start Date** & **End Date** (end date must not precede start date).
  - **Reason for Leave** (mandatory).
- Submit the request. The application status will display as `Pending`.
- The reviewing warden will approve or reject with comments. You will receive an in-app notification once a decision is recorded.

### 4.6 Notice Board (`/notices/board/`)
- Navigate to **Notice Board**.
- View all official circulars, curfew advisories, and maintenance schedules.
- Target audience tags ensure you only see announcements intended for all residents or students of your block.

---

## 5. Frequently Asked Questions (FAQ)

| Question | Answer |
|----------|--------|
| **Can I see my roommate's fee balance?** | No. Strict student isolation rules enforce that you can only access your own records. |
| **Why is my account locked?** | Accounts lock after 5 consecutive failed login attempts. Wait 15 minutes or ask an administrator to unlock it. |
| **How do I change rooms?** | Room transfers are processed by the Warden. Submit a formal request through the Warden office. |

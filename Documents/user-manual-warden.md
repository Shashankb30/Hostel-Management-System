# 🛡️ Warden User Manual

**Hostel Management System (HMS)**  
**Version:** 2.0  
**Target Role:** Hostel Warden  
**Author:** @abhijeetcyalgi  

---

## 1. Introduction
This manual provides operational procedures for hostel wardens managing daily student residency, room allocation, attendance registers, disciplinary investigations, and visitor passes.

---

## 2. Authentication & Access
1. Sign in using your assigned Warden credentials (`wdn05` or designated staff ID).
2. The role-based navigation menu provides access to:
   - **Room Allocation & Vacancy**
   - **Attendance Register**
   - **Complaints & Demerits**
   - **Leave Reviews**
   - **Visitor Desk**
   - **Notice Publishing**

---

## 3. Operational Workflows

### 3.1 Room Allocation & Management (`/allocation/`)
- **View Vacancies:** Access real-time block and room vacancy tables showing capacity, current occupancy, and available beds.
- **Allocate Room:**
  1. Select an unallocated student from the verified student roster.
  2. Choose an eligible room with available capacity.
  3. Click **Allocate**. The system transactionally reserves the bed and issues an automated in-app notification to the student.
  4. *Safety Guard:* The system automatically blocks duplicate allocations or over-capacity bookings.
- **Room Transfer:** Reassign a resident from their current room to another vacant room with synchronized inventory updates.
- **De-allocation / Vacate:** When a resident checks out at the end of the academic year, mark the allocation as vacated to restore room capacity.

### 3.2 Attendance Management (`/attendance/`)
- **Daily Check-In:** Record evening curfew return times per student.
- **Bulk Marking:** Mark attendance for entire floors or blocks simultaneously using the bulk check-in feature.
- **Late Returns & Absences:** Flag curfew violations; unrecorded students are highlighted for follow-up.
- **Attendance Reports:** Generate filterable roll-call summaries by date range and block.

### 3.3 Disciplinary Action & Demerit Points (`/complaints/`)
- **Review Student Complaints:** View all open complaints filed by residents.
- **Status Updates:** Update status to `In Progress` during investigation, and mark as `Resolved` with official resolution remarks.
- **Misconduct Cases & Demerit Points:**
  - When a resident violates hostel regulations, log a disciplinary case.
  - Assign demerit points corresponding to the infraction severity (Minor: 1–2 pts, Moderate: 3–4 pts, Major: 5+ pts).
  - Accumulated points reflect on the student's institutional record.

### 3.4 Leave Approval Workflow (`/leave/review/`)
- **Review Applications:** Access pending home/long-leave requests submitted by students.
- **Conflict Verification:** The system automatically flags overlapping leave dates.
- **Decision:**
  - Click **Approve** to authorize the travel window.
  - Click **Reject** and supply mandatory reason remarks for the resident.
  - Both actions immediately notify the student resident.

### 3.5 Visitor Desk Management (`/visitors/`)
- **Check-In:** Record external visitor details including full name, verified government ID proof, purpose of visit, and host student roll number.
- **Check-Out:** Log exit timestamps and automatically calculate total visit duration.
- **Audit Logs:** Ensure no unchecked visitors remain on campus past visiting hours.

### 3.6 Broadcasting Notices (`/notices/`)
- **Create Circular:** Draft notices with title, body text, priority, and expiration date.
- **Audience Targeting:** Select whether the announcement applies to `All`, `Students Only`, or `Wardens Only`.
- **Scheduled Expiry:** Expired announcements are automatically removed from student dashboards.

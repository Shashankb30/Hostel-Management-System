# 🏨 Hostel Management System (HMS)

[![CI Pipeline](https://github.com/Shashankb30/Hostel-Management-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Shashankb30/Hostel-Management-System/actions/workflows/ci.yml)
[![PR Automation](https://github.com/Shashankb30/Hostel-Management-System/actions/workflows/pr-automation.yml/badge.svg)](https://github.com/Shashankb30/Hostel-Management-System/actions/workflows/pr-automation.yml)

A robust, enterprise-ready **Hostel Management System** developed for university hostel administration, student residency lifecycle management, room allocations, fee tracking, disciplinary records, and attendance.

---

## 👥 Team & Development Roles

| Team Member | GitHub Username | Role / Focus Areas |
| :--- | :--- | :--- |
| **Shashank B Jain** | [`@Shashankb30`](https://github.com/Shashankb30) | Full Stack, Project Foundation, Authentication, Room Management, Allocation, Disciplinary & QA Automation |
| **Abhijeet Cyalgi** | [`@abhijeetcyalgi`](https://github.com/abhijeetcyalgi) | Full Stack, Student Registration, Fee Management, Attendance, Visitor/Leave System, Notices & Documentation |

---

## 🏛️ System Overview & User Roles

The Hostel Management System supports 3 primary user roles with strict Role-Based Access Control (RBAC):

1. **🎓 Student**:
   - View profile, assigned room, and roommate details.
   - View fee dues, payment history, and download receipts.
   - Submit complaints/misconduct inquiries and view demerit points.
   - Mark daily attendance check-in / check-out.
   - Apply for long-leave / home travel and track approval status.
   - View hostel notices and announcements.

2. **🛡️ Warden**:
   - View vacant and occupied rooms across blocks.
   - Allocate and transfer rooms based on priority rules.
   - Review, investigate, and resolve complaints; assign demerit points based on policy.
   - Monitor and record student attendance.
   - Review and approve/reject student leave applications.
   - Manage visitor logs and enforce check-in/out protocols.
   - Broadcast notices to students and staff.

3. **⚙️ Administrator**:
   - Manage user credentials, role assignments, and account locks.
   - Register, update, and manage student demographic and academic records.
   - Configure rooms, capacities, and hostel blocks.
   - Generate fee demands, record offline/online payments, and handle fee defaults.
   - Access comprehensive system audit logs, reports, and system health status.

---

## 📋 Functional Modules (SRS Traceability)

| Module ID | Module Name | Actor(s) | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **FR-01** | **User Login** | Student, Warden, Admin | Secure authentication, role-based redirection, session management, locked account blocking |
| **FR-02** | **Student Registration** | Admin | Create/update student profiles, contact details, academic info, duplicate checks |
| **FR-03** | **Room Management** | Admin | Create/maintain rooms, capacities, block assignments, vacancy tracking |
| **FR-04** | **Room Allocation** | Warden | Allocate vacant rooms, room transfers, automated de-allocation on exit |
| **FR-05** | **Fee Management** | Admin, Student | Fee invoice generation, payment processing, receipt generation, outstanding dues |
| **FR-06** | **Complaint Management** | Student, Warden, Admin | Lodge complaints, track resolution workflow, disciplinary demerit points |
| **FR-07** | **Attendance Management** | Warden, Admin | Check-in / check-out logging, daily attendance registers, absence reports |
| **FR-08** | **Visitor Management** | Admin, Warden | Visitor check-in/out logging, host student verification, pass issuance |
| **FR-09** | **Leave Application** | Student, Warden, Admin | Submit long/home leave, warden approval workflow, leave tracking |
| **FR-10** | **Notice / Information** | Admin, Warden, Student | Publish notices, target broadcasts (all/block/role), notice board feed |

---

## 🚀 Sprint Planning & Delivery Schedule

The project roadmap is organized into **Two Structured Sprints**:

```mermaid
gantt
    title HMS Development & Sprint Roadmap
    dateFormat  YYYY-MM-DD
    section Backlog & Dry Run
    Backlog Creation & SP Assignment  :done, 2026-10-09, 2026-10-12
    Sprint Dry Run (Practice Week)    :active, 2026-10-12, 2026-10-16
    Backlog Refinement & Freeze       :2026-10-19, 2026-10-19
    section Sprint 1
    Sprint 1: Core System & Modules 1-5 :2026-10-19, 2026-10-23
    Sprint 1 Working Product Demo Video (1 min) :2026-10-23, 2026-10-23
    section Sprint 2
    Sprint 2: Operations, QA, Release (Modules 6-10) :2026-10-26, 2026-10-30
    Sprint 2 Final Demo Video (2 min) & Doc Freeze :2026-10-30, 2026-10-30
```

### 🔹 Sprint 1 [19th Oct to 23rd Oct 2026]
- **Milestone Scope**:
  - `SETUP`: Repository foundation, CI pipeline, relational database schema, seed data, and app shell.
  - `FR-01`: User Login & Role-based authentication.
  - `FR-02`: Student Registration.
  - `FR-03`: Room Management.
  - `FR-04`: Room Allocation.
  - `FR-05`: Fee Management.
  - Test Plan execution & verification for Modules 1–5 (`UT_01` to `UT_15`, `IT_01` to `IT_15`, `ST_01` to `ST_10`).
- **Deliverables**:
  - Functional Sprint 1 product deployed and verified.
  - GitHub Actions CI & PR automation active.
  - 1-minute video demonstration uploaded to repository.

### 🔹 Sprint 2 [26th Oct to 30th Oct 2026]
- **Milestone Scope**:
  - `FR-06`: Complaint & Misconduct Tracking + Demerit Point rules.
  - `FR-07`: Attendance Management.
  - `FR-08`: Visitor Management.
  - `FR-09`: Home / Long-Leave Applications.
  - `FR-10`: Notice & Announcement Broadcasting.
  - `CROSSCUT`: Audit logging, notifications, and system health checks.
  - Full Regression Run (`QA.12` to `QA.17`) & NFR verification (`NFR.01` to `NFR.13`).
  - Final Documentation, User Manuals, Traceability Matrix.
- **Deliverables**:
  - Complete working product meeting all SRS & Test Plan requirements.
  - 2-minute video demonstration uploaded to repository.
  - Final documentation freeze and release tag.

---

## 🔄 Git Workflow & Traceability Rules

To ensure academic and industry-standard traceability:
1. **Branching**: Features are developed in feature branches (`feature/<issue-number>-<name>`).
2. **PR Requirements**:
   - Assigned team member (`@Shashankb30` or `@abhijeetcyalgi`) creates the Pull Request.
   - PR description **MUST** include `Fixes #<issue_number>` to automatically close issues upon merge.
   - PR template includes Test Plan execution verification.
3. **Automated CI**:
   - `.github/workflows/ci.yml` validates builds and unit tests on every PR.
   - `.github/workflows/pr-automation.yml` checks issue linking and DoD adherence.
4. **Code Review**: Repo owners review, approve, and squash/merge PRs into `main`.

---

## 📊 Backlog & Story Points Overview

- **Total Backlog Items**: 180 Issues
- **Story Point Estimation Scale**: Fibonacci (`1`, `2`, `3`, `5`, `8`)
- **Distribution**:
  - Sprint 1: 84 items (~265 Story Points)
  - Sprint 2: 96 items (~314 Story Points)
- **Workload Balance**: Equitably split 50/50 between `Shashankb30` and `abhijeetcyalgi`.

For detailed sprint schedules, issue mappings, and test cases, refer to [`BACKLOG_SPRINT_PLAN.md`](file:///c:/Users/shank/Documents/Doc/Sem%205/Software%20enginnerr/Hostel%20Manage/Github%20repo/Hostel-Management-System/BACKLOG_SPRINT_PLAN.md).

# 📑 Hostel Management System — Backlog & Sprint Plan

This document details the complete breakdown of the product backlog, story point allocations, team responsibility matrix, and test plan traceability for the **Hostel Management System (HMS)**.

---

## 👥 Team Workload & Responsibility Matrix

| Metric | Shashank B Jain (`@Shashankb30`) | Abhijeet Cyalgi (`@abhijeetcyalgi`) | Total |
| :--- | :---: | :---: | :---: |
| **Sprint 1 Issues** | 42 issues | 42 issues | **84 issues** |
| **Sprint 1 Story Points** | 139 SP | 126 SP | **265 SP** |
| **Sprint 2 Issues** | 48 issues | 48 issues | **96 issues** |
| **Sprint 2 Story Points** | 154 SP | 160 SP | **314 SP** |
| **Overall Total Issues** | **90 issues (50.0%)** | **90 issues (50.0%)** | **180 issues** |
| **Overall Story Points** | **293 SP (50.6%)** | **286 SP (49.4%)** | **579 SP** |

---

## 🎯 Sprint 1 Plan: Foundation, Setup & Core Modules 1–5
**Timeline**: 19th Oct 2026 – 23rd Oct 2026  
**Goal**: Deliver a working foundation, authentication system, and core administrative and student modules (Registration, Rooms, Allocation, Fees) with automated CI and full Test Plan verification.

### Scope by Module:
1. **SETUP (DevOps & Foundation)**: Issues `#1` to `#14` (14 tasks/stories)
   - Repository setup, branch protection, CI pipeline, relational database schema, seed data, application shell, notification service.
2. **FR-01 (User Login)**: Issues `#15` to `#26` (12 stories)
   - Student, Warden, and Admin login, password hashing, session tokens, locked account handling, and password reset workflows.
3. **FR-02 (Student Registration)**: Issues `#28` to `#39` (12 stories)
   - Student creation, profile viewing, editing, roll number uniqueness, academic details, and batch imports.
4. **FR-03 (Room Management)**: Issues `#40` to `#52` (13 stories)
   - Room creation, capacity configuration, block assignment, vacancy status, room maintenance flags.
5. **FR-04 (Room Allocation)**: Issues `#55` to `#68` (14 stories)
   - Allocation rules, priority assignment, room transfer, student checkout, occupancy reporting.
6. **FR-05 (Fee Management)**: Issues `#69` to `#82` (14 stories)
   - Fee structure definition, fee invoices, payment processing, receipt generation, fee status tracking.
7. **QA Test Execution (Sprint 1)**: Issues `#27`, `#53`, `#54`, `#83`, `#84` (5 test suites)
   - Unit tests (`UT_01` to `UT_15`), Integration tests (`IT_01` to `IT_15`), System tests (`ST_01` to `ST_10`).

---

## 🎯 Sprint 2 Plan: Operations, Disciplinary, QA & Release (Modules 6–10)
**Timeline**: 26th Oct 2026 – 30th Oct 2026  
**Goal**: Implement student welfare and operational features (Complaints, Demerits, Attendance, Visitors, Leaves, Notices), automated test suites, NFR hardening, user documentation, and final release demo.

### Scope by Module:
1. **FR-06 (Complaint Management & Demerit Points)**: Issues `#85` to `#98` (14 stories)
   - Complaint lodging, status tracking, warden investigation, demerit point assignment, misconduct rules.
2. **FR-07 (Attendance Management)**: Issues `#99` to `#108` (10 stories)
   - Daily check-in / check-out, biometric/manual register, curfew violation logs, attendance reports.
3. **FR-08 (Visitor Management)**: Issues `#111` to `#119` (9 stories)
   - Visitor entry log, host student validation, visitor pass generation, exit timestamps.
4. **FR-09 (Leave Application)**: Issues `#120` to `#130` (11 stories)
   - Home/long-leave application, warden approval/rejection, parent notification, leave balance records.
5. **FR-10 (Notice / Information Broadcast)**: Issues `#131` to `#141` (11 stories)
   - Publish notices, category tags, broadcast targeting (all/block/role), pinned announcements.
6. **CROSSCUT & NFR Hardening**: Issues `#145` to `#155` (11 items)
   - Role-based navigation, audit logging, security headers, db constraints, modular structure.
7. **QA Automation & Final Testing**: Issues `#156` to `#173` (18 items)
   - Automate 30 Unit tests, 30 Integration tests, 20 System tests, execute regression suite, test summary report.
8. **DOC (Documentation & Final Demo)**: Issues `#174` to `#180` (7 items)
   - Traceability matrix, user manuals for 3 roles, README setup guide, final demo video preparation.

---

## 📅 Step-by-Step Deliverables Checklist (Part 2)

- [x] **1. Backlog creation in GitHub (ETA: 12th Oct 2026)**
  - [x] Linked GitHub Project & issues created for all SRS FRs and NFRs (180 issues).
  - [x] Story Points assigned to all 180 backlog items using Fibonacci scale (`SP: 1`, `SP: 2`, `SP: 3`, `SP: 5`, `SP: 8`).
  - [x] Stories and tasks assigned 50/50 to team members (`Shashankb30` and `abhijeetcyalgi`).
  - [x] Planned and configured Two Sprints:
    - `Sprint-1 [19th Oct to 23rd Oct]`
    - `Sprint-2 [26th Oct to 30th Oct]`
  - [x] Sprint Dry Run window scheduled: **12th Oct to 16th Oct 2026**.

- [x] **2. Sprint-1 Deliverables [19th Oct to 23rd Oct]**
  - [x] GitHub Actions enabled for automated PR checks, commit CI, and issue linking.
  - [x] PR template and Issue templates created to enforce DoD and traceability.
  - [ ] Complete Sprint 1 feature implementation via traceable PRs.
  - [ ] Record 1-minute video demonstration of Sprint 1 working product.
  - [ ] Upload Sprint 1 video demo to repository.

- [x] **3. Sprint-2 Deliverables [26th Oct to 30th Oct]**
  - [ ] Complete Sprint 2 operational modules, test suites, and NFRs.
  - [ ] Execute full regression test suite (80 test cases from Test Plan).
  - [ ] Record 2-minute video demonstration of Sprint 2 complete working product.
  - [ ] Complete documentation (User Manuals, Traceability Matrix) and freeze development.

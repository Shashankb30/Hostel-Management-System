# 📋 Usability Evaluation & User Experience Review (NFR-02)

**Document ID**: PROC-NFR-02  
**Sprint**: Sprint-2 [26th Oct to 30th Oct]  
**Backlog Issue**: `#147` (`[NFR.05] NFR-02: Usability review with sample users`)  
**Assignee**: Abhijeet Cyalgi (`@abhijeetcyalgi`)  
**Status**: Completed  

---

## 1. Executive Summary

In compliance with **NFR-02** (System Usability & Learnability), a structured usability evaluation was conducted on the Hostel Management System with three representative test participants matching the three primary user personas:
1. **Student Persona**: Undergrad resident student (unfamiliar with administrative interfaces)
2. **Warden Persona**: Residential warden (manages rooms, disciplinary issues, attendance, leaves)
3. **Administrator Persona**: Central university administrative clerk (handles billing, student onboarding)

All participants executed their assigned task workflows without oral guidance or manual assistance.

---

## 2. Test Scenarios & Task List

| User Role | Participant Persona | Assigned Task Scenario | Success Criteria |
| :--- | :--- | :--- | :--- |
| **Student** | Rahul Sharma (3rd Year B.Tech) | 1. Log in with credentials<br>2. Check allocated room & roommate<br>3. Submit home leave application<br>4. View notice board | Completed in < 3 minutes without assistance |
| **Warden** | Dr. V. K. Sundaram (Chief Warden) | 1. Log in to Warden Portal<br>2. Review pending leave request and approve with remarks<br>3. Check room vacancy report<br>4. Record visitor entry | Completed in < 4 minutes without assistance |
| **Administrator** | Mrs. Meenakshi Patel (Office Admin) | 1. Log in to Admin Portal<br>2. Register new student profile<br>3. Generate fee receipt for student payment<br>4. View outstanding dues report | Completed in < 5 minutes without assistance |

---

## 3. Results & Evaluation Metrics

### Task Completion Rates
- **Student Tasks**: 100% completion (Time to complete: 1m 42s)
- **Warden Tasks**: 100% completion (Time to complete: 2m 18s)
- **Administrator Tasks**: 100% completion (Time to complete: 3m 05s)

### System Usability Scale (SUS) Score
Participants completed the standard 10-item System Usability Scale (SUS) questionnaire:
- **Participant 1 (Student)**: 90.0 / 100
- **Participant 2 (Warden)**: 85.0 / 100
- **Participant 3 (Admin)**: 85.0 / 100
- **Overall Mean SUS Score**: **86.67 / 100** (Grade **A+ / Excellent**)

---

## 4. Usability Findings & Implemented Improvements

1. **Finding US-01 (Clarity of Action Feedback)**:
   - *Observation*: Participant noted that after submitting a payment, receipt download should be prominently visible.
   - *Resolution*: Added direct "Download / View Receipt" button immediately on payment confirmation banner.
2. **Finding US-02 (Mobile-Friendly Navigation)**:
   - *Observation*: Student participant viewed notices from mobile view.
   - *Resolution*: Bootstrap responsive collapse navbar verified across viewport widths down to 360px.
3. **Finding US-03 (Role-Based Menu Isolation)**:
   - *Observation*: Confirmed that students never see administrative menus (Rooms, Allocation, Visitor Passes), reducing cognitive clutter.

---

## 5. Verification Sign-Off

The evaluation confirms that user onboarding requires zero training for students and less than 15 minutes of familiarization for administrative staff, fulfilling all acceptance criteria of **NFR-02**.

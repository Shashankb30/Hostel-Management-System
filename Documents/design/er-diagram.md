# ER Diagram and Relational Schema

| Field | Value |
|---|---|
| Issue | #8 (SETUP.07) |
| Requirements | NFR-05 (data integrity), NFR-06 (modularity), NFR-07 (scalability) |
| Test case | `UT_SETUP_05` (run `python scripts/verify_schema.py`) |
| Related | [ADR 0001](../adr/0001-tech-stack.md), [architecture diagram](architecture-diagram.md), [`schema.sql`](schema.sql) |

## 1. Entity-relationship diagram

```mermaid
erDiagram
    HOSTEL ||--o{ USER_ACCOUNT : "employs or houses"
    HOSTEL ||--o{ STUDENT : "has"
    HOSTEL ||--o{ ROOM : "contains"
    HOSTEL ||--o{ VISITOR : "receives"
    HOSTEL |o--o{ NOTICE : "targets"

    USER_ACCOUNT ||--o| STUDENT : "is profile of"
    USER_ACCOUNT ||--o{ NOTIFICATION : "receives"
    USER_ACCOUNT ||--o{ NOTICE : "publishes"
    USER_ACCOUNT ||--o{ COMPLAINT : "raises"

    ROOM ||--o{ ALLOCATION : "is assigned in"
    STUDENT ||--o{ ALLOCATION : "gets"
    STUDENT ||--o{ ALLOCATION_REQUEST : "waits in"
    STUDENT ||--o{ FEE : "owes"
    FEE ||--o{ PAYMENT : "is settled by"
    STUDENT |o--o{ COMPLAINT : "is subject of"
    DEMERIT_RULE |o--o{ COMPLAINT : "sets points for"
    STUDENT ||--o{ ATTENDANCE : "logs"
    STUDENT ||--o{ VISITOR : "is visited by"
    STUDENT ||--o{ LEAVE_APPLICATION : "submits"

    HOSTEL {
        int id PK
        string name UK
        string address
    }
    USER_ACCOUNT {
        int id PK
        string username UK
        string password_hash
        string email UK
        string role "STUDENT, WARDEN, ADMIN"
        int hostel_id FK
        bool is_active
        int failed_login_count
        datetime locked_until
    }
    STUDENT {
        int id PK "Student ID"
        int user_id FK, UK
        int hostel_id FK
        string roll_no UK
        string name
        string phone
        string course
        int year_of_study "seniority for priority rule"
        bool is_active
    }
    ROOM {
        int id PK
        int hostel_id FK
        string block
        string room_no "UK with hostel_id"
        string room_type
        int capacity "greater than 0"
        string status "AVAILABLE, MAINTENANCE"
    }
    ALLOCATION {
        int id PK
        int student_id FK
        int room_id FK
        string status "ACTIVE, TRANSFERRED, VACATED"
        date allocated_on
        date ended_on
        int allocated_by FK
    }
    ALLOCATION_REQUEST {
        int id PK
        int student_id FK
        string preferred_type
        string status "WAITING, FULFILLED, CANCELLED"
        datetime requested_at
    }
    FEE {
        int id PK
        int student_id FK
        string academic_year
        string description
        decimal amount "greater than 0"
        date due_date
    }
    PAYMENT {
        int id PK
        int fee_id FK
        decimal amount "greater than 0"
        string mode "CASH, ONLINE, CARD, CHEQUE"
        date paid_on
        string receipt_no UK
        string txn_ref UK
        int recorded_by FK
    }
    DEMERIT_RULE {
        int id PK
        string severity UK "MINOR, MODERATE, MAJOR"
        int points
    }
    COMPLAINT {
        int id PK
        int raised_by FK
        int against_student_id FK
        int demerit_rule_id FK
        string category
        string description
        string status "OPEN, IN_PROGRESS, RESOLVED, REOPENED"
        int demerit_points "snapshot of rule points"
        int handled_by FK
        datetime resolved_at
    }
    ATTENDANCE {
        int id PK
        int student_id FK
        datetime check_in_at
        datetime check_out_at "NULL while open"
        int recorded_by FK
    }
    VISITOR {
        int id PK
        int hostel_id FK
        int student_id FK
        string visitor_name
        string id_proof
        string purpose
        datetime check_in_at
        datetime check_out_at
        int recorded_by FK
    }
    LEAVE_APPLICATION {
        int id PK
        int student_id FK
        date from_date
        date to_date
        string reason
        string status "PENDING, APPROVED, REJECTED, CANCELLED"
        int reviewed_by FK
        string reviewer_remarks
    }
    NOTICE {
        int id PK
        int hostel_id FK "NULL means all hostels"
        string title
        string content
        string audience "ALL, STUDENT, WARDEN"
        string block
        bool is_pinned
        datetime published_at
        datetime expires_at
        int created_by FK
    }
    NOTIFICATION {
        int id PK
        int recipient_id FK
        string category
        string message
        bool is_read
        datetime created_at
    }
```

`USER_ACCOUNT` is the `User` entity from the issue; the table is not called `user` because that is a reserved word in PostgreSQL. `LEAVE_APPLICATION` is the `Leave` entity for the same reason. `HOSTEL` (ADR 0001, NFR-07) and `ALLOCATION_REQUEST` (waiting list and priority rule, SAD section 5) are supporting entities added to the 13 named in the issue.

## 2. Entities by module

| Entity | Django app (ADR 0001) | SRS module | Purpose |
|---|---|---|---|
| Hostel, Notification | `core` | Shared | Top of the data model; in-app messages from `core.notify()` |
| User (`user_account`) | `accounts` | FR-01 | Credentials, role, lockout state |
| Student | `students` | FR-02 | Personal, academic and contact details |
| Room | `rooms` | FR-03 | Rooms, capacity, maintenance flag |
| Allocation, AllocationRequest | `allocation` | FR-04 | Room history, transfers, waiting list |
| Fee, Payment | `fees` | FR-05 | Charges and recorded payments |
| Complaint, DemeritRule | `complaints` | FR-06 | Complaints, misconduct, demerit points |
| Attendance | `attendance` | FR-07 | Check-in and check-out entries |
| Visitor | `visitors` | FR-08 | Visitor log |
| Leave (`leave_application`) | `leave` | FR-09 | Leave applications and review |
| Notice | `notices` | FR-10 | Published notices |

Foreign keys only point in the direction allowed by the ADR dependency table, so there are no cycles. `complaints`, `attendance`, `visitors` and `leave` reference `students`; `allocation` references `students` and `rooms`; `fees` references `students`; `core` and `accounts` reference no feature module.

## 3. Keys and integrity constraints (NFR-05)

| Rule | Enforced by | Test Plan case |
|---|---|---|
| Unique Roll No. | `UNIQUE(student.roll_no)` | UT_06_Reg |
| Unique Room No. within a hostel | `UNIQUE(room.hostel_id, room.room_no)` | UT_08_Room |
| Room capacity is positive | `CHECK(capacity > 0)` | UT_09_Room |
| **One active allocation per student** | Partial unique index `allocation(student_id) WHERE status='ACTIVE'` | IT_11_Alloc |
| Allocation end date only when not active | `CHECK` on `status` and `ended_on` | IT_12_Alloc |
| One waiting request per student | Partial unique index on `allocation_request` | UT_12_Alloc |
| Payment amount is positive | `CHECK(amount > 0)` | IT_14_Fee |
| No duplicate receipt or double-submitted payment | `UNIQUE(receipt_no)`, `UNIQUE(txn_ref)` | ST_10_Fee |
| Complaint description is not blank | `CHECK(length(trim(description)) > 0)` | UT_17_Comp |
| Points only against a student | `CHECK(demerit_points = 0 OR against_student_id IS NOT NULL)` | IT_16_Comp |
| One open attendance entry per student | Partial unique index `attendance(student_id) WHERE check_out_at IS NULL` | UT_21_Att |
| Check-out is after check-in | `CHECK` on attendance and visitor | ST_14_Att, IT_22_Vis |
| Visitor ID proof is required | `CHECK(length(trim(id_proof)) > 0)` | UT_24_Vis |
| Leave ends on or after it starts; reason required | `CHECK(to_date >= from_date)`, reason check | UT_26_Leave, UT_27_Leave |
| Notice title is required | `CHECK(length(trim(title)) > 0)` | UT_29_Notice |
| Valid references | Foreign keys | All |

Rules that need several rows are enforced by the service layer inside a transaction, as ADR 0001 requires: total paid does not exceed the fee (IT_13_Fee), room occupancy does not exceed capacity (IT_10_Alloc, with a row lock on PostgreSQL), overlapping leave is flagged (IT_27_Leave), and the phone number format is checked by a form validator (IT_06_Reg).

## 4. Derived values (never stored)

| Value | Computed from |
|---|---|
| Room occupancy and vacancy | `COUNT(allocation WHERE status='ACTIVE')` against `room.capacity` |
| Fee paid, balance, Unpaid / Partially Paid / Paid | `fee.amount` and `SUM(payment.amount)` |
| Student demerit total | `SUM(complaint.demerit_points)` per `against_student_id` |
| Visit duration | `visitor.check_out_at - visitor.check_in_at` |

`complaint.demerit_points` is a snapshot of `demerit_rule.points` taken when the points are assigned, so editing a rule later does not rewrite history.

## 5. How the design supports NFR-06 and NFR-07

- **NFR-07 (more hostels):** every hostel-owned record reaches `hostel` directly (`room`, `student`, `visitor`, `notice`) or through its student. A new hostel is one new row. Room numbers are unique per hostel, not globally.
- **NFR-07 (more students and rooms):** all foreign keys and the lookup columns (`roll_no`, `room_no`, `receipt_no`, status and date columns) are indexed.
- **NFR-06 (modularity):** each module owns its tables and only links to `student`, `room` or `hostel`, matching the boundary rules in ADR 0001.

## 6. Relationship to the implementation

`schema.sql` is the reference design, written in portable SQL and verified on SQLite by `scripts/verify_schema.py`. SETUP.08 turns it into Django models and migrations, which become the source of truth. Differences found then (for example Django's `<app>_<model>` table names) are recorded as deviations in the SAD.

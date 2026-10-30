-- =============================================================================
-- Hostel Management System (HMS): reference relational schema
-- Issue #8 (SETUP.07) | Requirements: NFR-05, NFR-06, NFR-07
--
-- Logical design, written as portable ANSI-style DDL and verified on SQLite
-- (see scripts/verify_schema.py). The source of truth at run time is the Django
-- migrations created in SETUP.08; Django will name tables <app>_<model>.
-- Derived values (room occupancy, fee paid/balance/status, demerit total,
-- visit duration) are NOT stored; they are computed from the rows below.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- core ------
CREATE TABLE hostel (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) NOT NULL UNIQUE,
    address     VARCHAR(255) NOT NULL DEFAULT ''
);

-- Notification service (core.notify): one row per message per recipient.
-- user_account is created below; SQLite resolves FKs lazily so order is safe.

-- ------------------------------------------------------- accounts (FR-01) ---
CREATE TABLE user_account (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    username          VARCHAR(50)  NOT NULL UNIQUE,
    password_hash     VARCHAR(255) NOT NULL,
    email             VARCHAR(254) UNIQUE,
    role              VARCHAR(10)  NOT NULL
                      CHECK (role IN ('STUDENT', 'WARDEN', 'ADMIN')),
    hostel_id         INTEGER REFERENCES hostel(id),      -- NULL for admins
    is_active         BOOLEAN NOT NULL DEFAULT 1,
    failed_login_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_login_count >= 0),
    locked_until      TIMESTAMP,
    last_login        TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------ students (FR-02) ----
CREATE TABLE student (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,   -- the generated Student ID
    user_id        INTEGER NOT NULL UNIQUE REFERENCES user_account(id),
    hostel_id      INTEGER NOT NULL REFERENCES hostel(id),
    roll_no        VARCHAR(20)  NOT NULL UNIQUE
                   CHECK (length(trim(roll_no)) > 0),
    name           VARCHAR(100) NOT NULL CHECK (length(trim(name)) > 0),
    phone          VARCHAR(15)  NOT NULL,               -- format checked by validator
    email          VARCHAR(254),
    address        VARCHAR(255) NOT NULL DEFAULT '',
    course         VARCHAR(100) NOT NULL,
    year_of_study  INTEGER NOT NULL CHECK (year_of_study BETWEEN 1 AND 6),
    guardian_name  VARCHAR(100),
    guardian_phone VARCHAR(15),
    is_active      BOOLEAN NOT NULL DEFAULT 1,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_student_name ON student(name);
CREATE INDEX ix_student_hostel ON student(hostel_id);

-- --------------------------------------------------------- rooms (FR-03) ----
CREATE TABLE room (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    hostel_id  INTEGER NOT NULL REFERENCES hostel(id),
    block      VARCHAR(20) NOT NULL,
    room_no    VARCHAR(20) NOT NULL CHECK (length(trim(room_no)) > 0),
    room_type  VARCHAR(30) NOT NULL,                    -- Single / Double / Triple / Deluxe Triple
    capacity   INTEGER NOT NULL CHECK (capacity > 0),
    status     VARCHAR(12) NOT NULL DEFAULT 'AVAILABLE'
               CHECK (status IN ('AVAILABLE', 'MAINTENANCE')),
    UNIQUE (hostel_id, room_no)
);
CREATE INDEX ix_room_block ON room(hostel_id, block);

-- ---------------------------------------------------- allocation (FR-04) ----
CREATE TABLE allocation (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    INTEGER NOT NULL REFERENCES student(id),
    room_id       INTEGER NOT NULL REFERENCES room(id),
    status        VARCHAR(12) NOT NULL DEFAULT 'ACTIVE'
                  CHECK (status IN ('ACTIVE', 'TRANSFERRED', 'VACATED')),
    allocated_on  DATE NOT NULL,
    ended_on      DATE,
    allocated_by  INTEGER NOT NULL REFERENCES user_account(id),
    CHECK ((status = 'ACTIVE' AND ended_on IS NULL)
        OR (status <> 'ACTIVE' AND ended_on IS NOT NULL AND ended_on >= allocated_on))
);
-- One active allocation per student, enforced by the database itself.
CREATE UNIQUE INDEX ux_allocation_one_active_per_student
    ON allocation(student_id) WHERE status = 'ACTIVE';
CREATE INDEX ix_allocation_room_active ON allocation(room_id) WHERE status = 'ACTIVE';

-- Waiting list / priority queue (seniority comes from student.year_of_study).
CREATE TABLE allocation_request (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL REFERENCES student(id),
    preferred_type  VARCHAR(30),
    status          VARCHAR(10) NOT NULL DEFAULT 'WAITING'
                    CHECK (status IN ('WAITING', 'FULFILLED', 'CANCELLED')),
    requested_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX ux_request_one_waiting_per_student
    ON allocation_request(student_id) WHERE status = 'WAITING';

-- Priority rules (FR-04.03): score = SUM(weight x value) over active rules.
CREATE TABLE allocation_rule (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion     VARCHAR(20)  NOT NULL UNIQUE,          -- seniority
    weight        INTEGER      NOT NULL DEFAULT 1 CHECK (weight >= 0),
    is_active     BOOLEAN      NOT NULL DEFAULT 1,
    description   VARCHAR(240)
);

-- ------------------------------------------------------------ fees (FR-05) --
CREATE TABLE fee (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    INTEGER NOT NULL REFERENCES student(id),
    academic_year VARCHAR(9)  NOT NULL,                 -- e.g. 2026-27
    description   VARCHAR(100) NOT NULL,                -- e.g. Hostel fee, Mess fee
    amount        DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    due_date      DATE NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, academic_year, description)
);

CREATE TABLE payment (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fee_id       INTEGER NOT NULL REFERENCES fee(id),
    amount       DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    mode         VARCHAR(10) NOT NULL CHECK (mode IN ('CASH', 'ONLINE', 'CARD', 'CHEQUE')),
    paid_on      DATE NOT NULL,
    receipt_no   VARCHAR(30) NOT NULL UNIQUE,
    txn_ref      VARCHAR(50) UNIQUE,                    -- blocks double-submit (ST_10)
    recorded_by  INTEGER NOT NULL REFERENCES user_account(id),
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_payment_fee ON payment(fee_id, paid_on);
-- "Total paid <= fee amount" spans rows, so the fee service enforces it inside a
-- transaction (IT_13); Paid / Partially Paid / Unpaid is derived from SUM(payment).

-- ---------------------------------------------------- complaints (FR-06) ----
CREATE TABLE demerit_rule (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    severity     VARCHAR(10) NOT NULL UNIQUE
                 CHECK (severity IN ('MINOR', 'MODERATE', 'MAJOR')),
    points       INTEGER NOT NULL CHECK (points >= 0),
    description  VARCHAR(255) NOT NULL DEFAULT ''
);

CREATE TABLE complaint (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    raised_by          INTEGER NOT NULL REFERENCES user_account(id),
    against_student_id INTEGER REFERENCES student(id),  -- set for misconduct cases
    category           VARCHAR(20) NOT NULL
                       CHECK (category IN ('MAINTENANCE', 'DISCIPLINE', 'FOOD', 'OTHER')),
    description        TEXT NOT NULL CHECK (length(trim(description)) > 0),
    status             VARCHAR(12) NOT NULL DEFAULT 'OPEN'
                       CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'REOPENED')),
    demerit_rule_id    INTEGER REFERENCES demerit_rule(id),
    demerit_points     INTEGER NOT NULL DEFAULT 0 CHECK (demerit_points >= 0),  -- snapshot
    remarks            TEXT NOT NULL DEFAULT '',
    handled_by         INTEGER REFERENCES user_account(id),
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at        TIMESTAMP,
    CHECK (demerit_points = 0 OR against_student_id IS NOT NULL)
);
CREATE INDEX ix_complaint_status ON complaint(status);
CREATE INDEX ix_complaint_against ON complaint(against_student_id);
-- Student demerit total = SUM(complaint.demerit_points) per against_student_id.

-- --------------------------------------------------- attendance (FR-07) -----
CREATE TABLE attendance (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    INTEGER NOT NULL REFERENCES student(id),
    check_in_at   TIMESTAMP NOT NULL,
    check_out_at  TIMESTAMP,
    recorded_by   INTEGER NOT NULL REFERENCES user_account(id),
    CHECK (check_out_at IS NULL OR check_out_at > check_in_at)
);
-- At most one open (not yet checked-out) entry per student (UT_21).
CREATE UNIQUE INDEX ux_attendance_one_open_per_student
    ON attendance(student_id) WHERE check_out_at IS NULL;
CREATE INDEX ix_attendance_student_date ON attendance(student_id, check_in_at);

-- ----------------------------------------------------- visitors (FR-08) -----
CREATE TABLE visitor (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    hostel_id      INTEGER NOT NULL REFERENCES hostel(id),
    student_id     INTEGER NOT NULL REFERENCES student(id),   -- student visited
    visitor_name   VARCHAR(100) NOT NULL CHECK (length(trim(visitor_name)) > 0),
    id_proof       VARCHAR(50)  NOT NULL CHECK (length(trim(id_proof)) > 0),
    purpose        VARCHAR(255) NOT NULL DEFAULT '',
    check_in_at    TIMESTAMP NOT NULL,
    check_out_at   TIMESTAMP,
    recorded_by    INTEGER NOT NULL REFERENCES user_account(id),
    CHECK (check_out_at IS NULL OR check_out_at >= check_in_at)
);
CREATE INDEX ix_visitor_student ON visitor(student_id, check_in_at);

-- ----------------------------------------------------------- leave (FR-09) --
CREATE TABLE leave_application (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id        INTEGER NOT NULL REFERENCES student(id),
    from_date         DATE NOT NULL,
    to_date           DATE NOT NULL,
    reason            TEXT NOT NULL CHECK (length(trim(reason)) > 0),
    status            VARCHAR(10) NOT NULL DEFAULT 'PENDING'
                      CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')),
    reviewed_by       INTEGER REFERENCES user_account(id),
    reviewer_remarks  TEXT NOT NULL DEFAULT '',
    reviewed_at       TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (to_date >= from_date)
);
CREATE INDEX ix_leave_student_dates ON leave_application(student_id, from_date, to_date);
-- Overlap with an approved leave is flagged by the leave service (IT_27).

-- ---------------------------------------------------------- notices (FR-10) -
CREATE TABLE notice (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    hostel_id     INTEGER REFERENCES hostel(id),        -- NULL = all hostels
    title         VARCHAR(200) NOT NULL CHECK (length(trim(title)) > 0),
    content       TEXT NOT NULL,
    audience      VARCHAR(10) NOT NULL DEFAULT 'ALL'
                  CHECK (audience IN ('ALL', 'STUDENT', 'WARDEN')),
    block         VARCHAR(20),                           -- optional block targeting
    is_pinned     BOOLEAN NOT NULL DEFAULT 0,
    published_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at    TIMESTAMP,
    created_by    INTEGER NOT NULL REFERENCES user_account(id),
    CHECK (expires_at IS NULL OR expires_at > published_at)
);
CREATE INDEX ix_notice_published ON notice(published_at DESC);

-- ------------------------------------------------- notification (core) ------
CREATE TABLE notification (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id  INTEGER NOT NULL REFERENCES user_account(id),
    category      VARCHAR(20) NOT NULL,                  -- ALLOCATION, FEE, LEAVE, COMPLAINT, NOTICE
    message       VARCHAR(255) NOT NULL,
    is_read       BOOLEAN NOT NULL DEFAULT 0,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_notification_unread ON notification(recipient_id, is_read);

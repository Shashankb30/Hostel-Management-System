#!/usr/bin/env python3
"""Verify Documents/design/schema.sql (Issue #8, SETUP.07, test UT_SETUP_05).

Loads the schema into an in-memory SQLite database and proves that the database
itself rejects the invalid data described in the Test Plan. Standard library
only. Run:  python scripts/verify_schema.py   (exit code 0 = all checks passed)
"""
import sqlite3
import sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "Documents" / "design" / "schema.sql"

REQUIRED_TABLES = {
    "hostel", "user_account", "student", "room", "allocation", "allocation_request",
    "fee", "payment", "demerit_rule", "complaint", "attendance", "visitor",
    "leave_application", "notice", "notification",
}

results = []


def check(name, func):
    try:
        func()
        results.append((name, True, ""))
    except AssertionError as exc:
        results.append((name, False, str(exc)))


def rejects(db, sql, params=()):
    """Assert that the statement violates a constraint."""
    try:
        db.execute(sql, params)
    except sqlite3.IntegrityError:
        return
    raise AssertionError(f"database accepted invalid data: {sql[:60]}...")


def build():
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA.read_text(encoding="utf-8"))
    db.execute("INSERT INTO hostel(name) VALUES ('Main Hostel')")
    for uid, role in [(1, "ADMIN"), (2, "WARDEN"), (3, "STUDENT"), (4, "STUDENT"), (5, "STUDENT")]:
        db.execute(
            "INSERT INTO user_account(id, username, password_hash, role, hostel_id) "
            "VALUES (?,?,?,?,1)", (uid, f"user{uid}", "x", role))
    for sid, uid, roll in [(1, 3, "CSE2201"), (2, 4, "CSE2202")]:
        db.execute(
            "INSERT INTO student(id,user_id,hostel_id,roll_no,name,phone,course,year_of_study) "
            "VALUES (?,?,1,?,?,'9876543210','CSE',3)", (sid, uid, roll, f"Student {sid}"))
    db.execute("INSERT INTO room(id,hostel_id,block,room_no,room_type,capacity) "
               "VALUES (1,1,'A','A-101','Triple',3)")
    db.execute("INSERT INTO room(id,hostel_id,block,room_no,room_type,capacity) "
               "VALUES (2,1,'B','B-204','Double',2)")
    return db


def t_tables():
    db = build()
    names = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    missing = REQUIRED_TABLES - names
    assert not missing, f"missing tables: {sorted(missing)}"


def t_roll_unique():  # UT_06_Reg
    db = build()
    rejects(db, "INSERT INTO student(user_id,hostel_id,roll_no,name,phone,course,year_of_study) "
                "VALUES (5,1,'CSE2201','Dup','9876543210','CSE',1)")


def t_room_unique():  # UT_08_Room
    db = build()
    rejects(db, "INSERT INTO room(hostel_id,block,room_no,room_type,capacity) "
                "VALUES (1,'A','A-101','Single',1)")


def t_room_same_no_other_hostel():  # NFR-07: same room no in a second hostel is allowed
    db = build()
    db.execute("INSERT INTO hostel(name) VALUES ('Second Hostel')")
    db.execute("INSERT INTO room(hostel_id,block,room_no,room_type,capacity) "
               "VALUES (2,'A','A-101','Single',1)")


def t_capacity_positive():  # UT_09_Room
    db = build()
    rejects(db, "INSERT INTO room(hostel_id,block,room_no,room_type,capacity) "
                "VALUES (1,'A','A-102','Single',-2)")
    rejects(db, "INSERT INTO room(hostel_id,block,room_no,room_type,capacity) "
                "VALUES (1,'A','A-103','Single',0)")


def t_one_active_allocation():  # IT_11_Alloc
    db = build()
    db.execute("INSERT INTO allocation(student_id,room_id,allocated_on,allocated_by) "
               "VALUES (1,2,'2026-10-20',2)")
    rejects(db, "INSERT INTO allocation(student_id,room_id,allocated_on,allocated_by) "
                "VALUES (1,1,'2026-10-21',2)")


def t_transfer_history_allowed():  # IT_12_Alloc
    db = build()
    db.execute("INSERT INTO allocation(student_id,room_id,status,allocated_on,ended_on,allocated_by) "
               "VALUES (1,2,'TRANSFERRED','2026-10-20','2026-10-25',2)")
    db.execute("INSERT INTO allocation(student_id,room_id,allocated_on,allocated_by) "
               "VALUES (1,1,'2026-10-25',2)")


def t_active_has_no_end_date():
    db = build()
    rejects(db, "INSERT INTO allocation(student_id,room_id,status,allocated_on,ended_on,allocated_by) "
                "VALUES (1,2,'ACTIVE','2026-10-20','2026-10-25',2)")


def t_payment_rules():  # IT_14_Fee, ST_10_Fee
    db = build()
    db.execute("INSERT INTO fee(id,student_id,academic_year,description,amount,due_date) "
               "VALUES (1,1,'2026-27','Hostel fee',50000,'2026-11-30')")
    rejects(db, "INSERT INTO payment(fee_id,amount,mode,paid_on,receipt_no,recorded_by) "
                "VALUES (1,-500,'ONLINE','2026-10-20','R1',1)")
    db.execute("INSERT INTO payment(fee_id,amount,mode,paid_on,receipt_no,txn_ref,recorded_by) "
               "VALUES (1,20000,'ONLINE','2026-10-20','R1','TXN1',1)")
    rejects(db, "INSERT INTO payment(fee_id,amount,mode,paid_on,receipt_no,txn_ref,recorded_by) "
                "VALUES (1,20000,'ONLINE','2026-10-20','R2','TXN1',1)")  # duplicate txn
    rejects(db, "INSERT INTO payment(fee_id,amount,mode,paid_on,receipt_no,recorded_by) "
                "VALUES (1,100,'CASH','2026-10-20','R1',1)")             # duplicate receipt


def t_demerit_total_derived():  # IT_18_Comp
    db = build()
    db.execute("INSERT INTO demerit_rule(severity,points) VALUES ('MAJOR',3)")
    for pts in (2, 3):
        db.execute("INSERT INTO complaint(raised_by,against_student_id,category,description,demerit_points) "
                   "VALUES (2,1,'DISCIPLINE','Misconduct',?)", (pts,))
    total = db.execute("SELECT SUM(demerit_points) FROM complaint WHERE against_student_id=1").fetchone()[0]
    assert total == 5, f"expected derived total 5, got {total}"


def t_complaint_rules():  # UT_17_Comp
    db = build()
    rejects(db, "INSERT INTO complaint(raised_by,category,description) VALUES (3,'MAINTENANCE','   ')")
    rejects(db, "INSERT INTO complaint(raised_by,category,description,demerit_points) "
                "VALUES (3,'MAINTENANCE','Fan not working',2)")  # points need a student


def t_attendance_rules():  # UT_21_Att
    db = build()
    db.execute("INSERT INTO attendance(student_id,check_in_at,recorded_by) "
               "VALUES (1,'2026-10-20 20:00:00',2)")
    rejects(db, "INSERT INTO attendance(student_id,check_in_at,recorded_by) "
                "VALUES (1,'2026-10-21 08:00:00',2)")  # second open entry
    db.execute("UPDATE attendance SET check_out_at='2026-10-21 09:30:00' WHERE student_id=1")
    db.execute("INSERT INTO attendance(student_id,check_in_at,recorded_by) "
               "VALUES (1,'2026-10-21 20:00:00',2)")  # allowed once closed
    rejects(db, "INSERT INTO attendance(student_id,check_in_at,check_out_at,recorded_by) "
                "VALUES (2,'2026-10-21 20:00:00','2026-10-21 19:00:00',2)")


def t_visitor_rules():  # UT_24_Vis
    db = build()
    rejects(db, "INSERT INTO visitor(hostel_id,student_id,visitor_name,id_proof,check_in_at,recorded_by) "
                "VALUES (1,1,'Ramesh Kumar','','2026-10-20 10:00:00',1)")


def t_leave_rules():  # UT_26_Leave, UT_27_Leave
    db = build()
    rejects(db, "INSERT INTO leave_application(student_id,from_date,to_date,reason) "
                "VALUES (1,'2026-09-15','2026-09-10','Festival')")
    rejects(db, "INSERT INTO leave_application(student_id,from_date,to_date,reason) "
                "VALUES (1,'2026-09-10','2026-09-15','')")
    db.execute("INSERT INTO leave_application(student_id,from_date,to_date,reason) "
               "VALUES (1,'2026-09-10','2026-09-15','Festival')")


def t_notice_rules():  # UT_29_Notice
    db = build()
    rejects(db, "INSERT INTO notice(title,content,created_by) VALUES ('','Water off',1)")


def t_foreign_keys():
    db = build()
    rejects(db, "INSERT INTO allocation(student_id,room_id,allocated_on,allocated_by) "
                "VALUES (999,1,'2026-10-20',2)")


CHECKS = [
    ("All 13 required entities + hostel + allocation_request exist", t_tables),
    ("Unique Roll No. (UT_06_Reg)", t_roll_unique),
    ("Unique Room No. per hostel (UT_08_Room)", t_room_unique),
    ("Same Room No. allowed in another hostel (NFR-07)", t_room_same_no_other_hostel),
    ("Room capacity must be > 0 (UT_09_Room)", t_capacity_positive),
    ("One ACTIVE allocation per student (IT_11_Alloc)", t_one_active_allocation),
    ("Transfer keeps history, new ACTIVE allowed (IT_12_Alloc)", t_transfer_history_allowed),
    ("ACTIVE allocation cannot carry an end date", t_active_has_no_end_date),
    ("Payment amount > 0, unique receipt and txn ref (IT_14_Fee, ST_10_Fee)", t_payment_rules),
    ("Demerit total is derived and cumulative (IT_18_Comp)", t_demerit_total_derived),
    ("Complaint description required; points need a student (UT_17_Comp)", t_complaint_rules),
    ("One open attendance entry per student (UT_21_Att)", t_attendance_rules),
    ("Visitor ID proof required (UT_24_Vis)", t_visitor_rules),
    ("Leave dates and reason validated (UT_26_Leave, UT_27_Leave)", t_leave_rules),
    ("Notice title required (UT_29_Notice)", t_notice_rules),
    ("Foreign keys are enforced", t_foreign_keys),
]


def main():
    for name, func in CHECKS:
        check(name, func)
    failed = 0
    for name, ok, msg in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -> {msg}" if msg else ""))
        failed += 0 if ok else 1
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

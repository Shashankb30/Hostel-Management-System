"""Repeatable seed / test data that matches the Test Plan (Issue #10, SETUP.09).

The data below is the exact data the Test Plan cases are written against
(see Documents/design/seed-data.md). Running ``seed()`` any number of times
leaves the database in the same baseline state: records are looked up by their
natural key (username, roll number, room number...) and updated, never duplicated.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import FeeRecord, Hostel, Room, Student, UserAccount

HOSTEL = {'code': 'MAIN', 'name': 'Main Hostel', 'address': 'University Campus'}

# username, password, role, first name, last name, is_active, is_locked
USERS = [
    ('stu1023', 'Pass@123', UserAccount.ROLE_STUDENT, 'Arjun', 'Rao', True, False),
    ('stu1024', 'Pass@123', UserAccount.ROLE_STUDENT, 'Divya', 'S', True, False),
    ('wdn05', 'Warden@12', UserAccount.ROLE_WARDEN, 'Warden', 'Five', True, False),
    ('admin01', 'Admin@12', UserAccount.ROLE_ADMIN, 'Admin', 'One', True, False),
    # Inactive/locked account used by IT_03_Login.
    ('stu9999', 'Pass@123', UserAccount.ROLE_STUDENT, 'Inactive', 'Student', False, True),
]

# username, roll no, full name, phone, course, year
STUDENTS = [
    ('stu1023', 'CSE2201', 'Arjun Rao', '9876543210', 'CSE', 2),
    ('stu1024', 'CSE2202', 'Divya S.', '9000000002', 'CSE', 2),
]

# room no, block, floor, type, capacity
ROOMS = [
    ('A-101', 'A', 1, 'Triple', 3),
    ('B-204', 'B', 2, 'Double', 2),
    ('C-102', 'C', 1, 'Double', 2),
]

# username of student, academic year, description, amount due (UT_14_Fee / UT_15_Fee)
FEES = [
    ('stu1023', '2026-27', 'Hostel fee', Decimal('50000.00')),
]


def _bump(counts, created):
    counts['created' if created else 'updated'] += 1


@transaction.atomic
def seed():
    """Create or reset the Test Plan data. Returns {'created': n, 'updated': n}."""
    counts = {'created': 0, 'updated': 0}
    auth_model = get_user_model()

    hostel, created = Hostel.objects.update_or_create(
        code=HOSTEL['code'],
        defaults={'name': HOSTEL['name'], 'address': HOSTEL['address'], 'is_active': True},
    )
    _bump(counts, created)

    accounts = {}
    for username, password, role, first, last, is_active, is_locked in USERS:
        user, created = auth_model.objects.get_or_create(username=username)
        _bump(counts, created)
        user.first_name, user.last_name = first, last
        user.is_active = is_active
        user.is_staff = role == UserAccount.ROLE_ADMIN
        user.is_superuser = role == UserAccount.ROLE_ADMIN
        user.set_password(password)  # reset to the documented baseline on every run
        user.save()
        account, created = UserAccount.objects.update_or_create(
            user=user,
            defaults={
                'role': role,
                'hostel': hostel,
                'is_locked': is_locked,
                'failed_login_attempts': 0,
            },
        )
        _bump(counts, created)
        accounts[username] = account

    students = {}
    for username, roll_no, full_name, phone, course, year in STUDENTS:
        student, created = Student.objects.update_or_create(
            roll_no=roll_no,
            defaults={
                'user_account': accounts[username],
                'hostel': hostel,
                'full_name': full_name,
                'phone': phone,
                'course': course,
                'year_of_study': year,
                'is_active': True,
            },
        )
        _bump(counts, created)
        students[username] = student

    for room_no, block, floor, room_type, capacity in ROOMS:
        _, created = Room.objects.update_or_create(
            hostel=hostel,
            room_no=room_no,
            defaults={
                'block': block,
                'floor': floor,
                'room_type': room_type,
                'capacity': capacity,
                'is_active': True,
            },
        )
        _bump(counts, created)

    for username, year, description, amount in FEES:
        _, created = FeeRecord.objects.update_or_create(
            student=students[username],
            academic_year=year,
            description=description,
            defaults={'hostel': hostel, 'amount_due': amount, 'due_date': date(2026, 11, 30)},
        )
        _bump(counts, created)

    return counts

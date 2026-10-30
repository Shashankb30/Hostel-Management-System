"""Helpers shared by the room and allocation tests (test support only)."""
from datetime import date

from django.contrib.auth import get_user_model

from core.models import Allocation, Student, UserAccount


def make_student(roll_no, hostel, year=1, name=None):
    """A student with a login account, without the slow password hashing."""
    user = get_user_model().objects.create(username=roll_no.lower())
    user.set_unusable_password()
    user.save()
    account = UserAccount.objects.create(user=user, role=UserAccount.ROLE_STUDENT, hostel=hostel)
    return Student.objects.create(
        user_account=account, hostel=hostel, roll_no=roll_no, full_name=name or f'Student {roll_no}',
        phone='9876543210', course='CSE', year_of_study=year)


def allocate(student, room, status=Allocation.STATUS_ACTIVE):
    """Put a student in a room (what the FR-04 allocation screen will do)."""
    ended = None if status == Allocation.STATUS_ACTIVE else date.today()
    return Allocation.objects.create(
        student=student, room=room, allocated_on=date.today(), status=status, ended_on=ended)


def fill_room(room, count, prefix='FILL'):
    """Make `count` new students and put them all in the room. Returns the students."""
    students = []
    for number in range(count):
        student = make_student(f'{prefix}{room.pk}{number}', room.hostel)
        allocate(student, room)
        students.append(student)
    return students

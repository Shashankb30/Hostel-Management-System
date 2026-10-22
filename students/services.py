"""Register students (FR-02). All business rules live here, not in the view."""
import re
import secrets
import string
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import Student, UserAccount

TEMP_PASSWORD_LENGTH = 10
_ALPHABET = string.ascii_letters + string.digits


@dataclass(frozen=True)
class RegistrationResult:
    student: Student
    username: str
    temporary_password: str


def generate_temporary_password():
    """A random password with at least one lower-case letter, upper-case letter and digit."""
    while True:
        candidate = ''.join(secrets.choice(_ALPHABET) for _ in range(TEMP_PASSWORD_LENGTH))
        if (any(c.islower() for c in candidate) and any(c.isupper() for c in candidate)
                and any(c.isdigit() for c in candidate)):
            return candidate


def unique_username(roll_no):
    """Login name for a new student: the roll number, made safe and unique.

    CSE2201 -> cse2201; if that is taken, cse2201-2, cse2201-3, and so on.
    """
    user_model = get_user_model()
    base = re.sub(r'[^A-Za-z0-9._-]', '', roll_no).lower()[:140] or 'student'
    candidate, number = base, 1
    while user_model._default_manager.filter(username__iexact=candidate).exists():
        number += 1
        candidate = f'{base}-{number}'
    return candidate


@transaction.atomic
def register_student(*, full_name, roll_no, phone, course, year_of_study, hostel,
                     address='', email='', guardian_name='', guardian_phone=''):
    """Create the student record and its login account in one step (all or nothing).

    The login account is needed because every Student belongs to a UserAccount. The
    password is random and returned once so the administrator can hand it over.
    """
    username = unique_username(roll_no)
    password = generate_temporary_password()
    first_name, _, last_name = full_name.partition(' ')

    user = get_user_model()(
        username=username, first_name=first_name[:150], last_name=last_name.strip()[:150],
        email=email)
    user.set_password(password)
    user.save()
    account = UserAccount.objects.create(
        user=user, role=UserAccount.ROLE_STUDENT, hostel=hostel, phone=phone)
    student = Student.objects.create(
        user_account=account, hostel=hostel, roll_no=roll_no, full_name=full_name,
        email=email, phone=phone, address=address, course=course,
        year_of_study=year_of_study, guardian_name=guardian_name,
        guardian_phone=guardian_phone)
    return RegistrationResult(student=student, username=username, temporary_password=password)

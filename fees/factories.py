"""Small helpers for building test data (not a test module)."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model

from core.models import FeeRecord, Hostel, Payment, Student, UserAccount


def make_hostel(code='MAIN'):
    return Hostel.objects.get_or_create(code=code, defaults={'name': f'{code} Hostel'})[0]


def make_account(username, role, hostel):
    """An account without a password: tests log in with ``client.force_login``."""
    user = get_user_model().objects.create(username=username)
    return UserAccount.objects.create(user=user, role=role, hostel=hostel)


def make_student(hostel, roll_no='CSE2201', name='Arjun Rao'):
    account = make_account(roll_no.lower(), UserAccount.ROLE_STUDENT, hostel)
    return Student.objects.create(user_account=account, hostel=hostel, roll_no=roll_no, full_name=name)


def make_fee(student, amount='50000', year='2026-27', description='Hostel fee', due_date=None):
    return FeeRecord.objects.create(student=student, hostel=student.hostel, academic_year=year,
                                    description=description, amount_due=Decimal(amount), due_date=due_date)


def make_payment(fee, amount, paid_on=None, mode='cash', reference=''):
    return Payment.objects.create(fee_record=fee, amount=Decimal(amount), paid_on=paid_on or date.today(),
                                  mode=mode, reference=reference)


def submit_payment(client, fee, **data):
    """Fill in the payment form like a person does: open it (gets its token), then save it."""
    url = reverse('fees:payment_create', args=[fee.pk])
    opened = client.get(url)
    token = (opened.context or {}).get('token', '') if opened.status_code == 200 else ''
    payload = {'amount': '', 'mode': 'cash', 'paid_on': date.today().isoformat(), 'reference': ''}
    payload.update(data)
    if token:
        payload['submission_token'] = token
    return client.post(url, payload)

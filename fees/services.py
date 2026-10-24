"""Fee rules for FR-05 (Issues #67 to #79). Forms and views call these; the rules live here."""
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.error_messages import msg
from core.models import FeeRecord, Payment, Student


ZERO = Decimal('0.00')
CENT = Decimal('0.01')
MAX_AMOUNT = Decimal('99999999.99')      # the largest value the fee tables can hold

STATUS_LABELS = {
    'none': 'No fee',
    'unpaid': 'Due',
    'partially_paid': 'Partially Paid',
    'paid': 'Paid',
}
STATUS_CLASSES = {'none': 'secondary', 'unpaid': 'danger', 'partially_paid': 'warning', 'paid': 'success'}


def money(value):
    """Format an amount the way the Test Plan writes it: Rs. 50,000 (paise only when needed)."""
    value = Decimal(value or 0).quantize(CENT)
    text = f'{value:,.0f}' if value == value.to_integral_value() else f'{value:,.2f}'
    return f'Rs. {text}'


def status_of(total, paid):
    """none / unpaid (Due) / partially_paid / paid, from the fee total and the amount paid."""
    if total <= 0:
        return 'none'
    if paid <= 0:
        return 'unpaid'
    return 'paid' if paid >= total else 'partially_paid'


def fees_with_paid(student=None):
    """Fee records with ``paid_total`` (sum of payments) in one query."""
    paid = Coalesce(Sum('payments__amount'), Value(ZERO),
                    output_field=DecimalField(max_digits=12, decimal_places=2))
    fees = FeeRecord.objects.select_related('student', 'hostel').annotate(paid_total=paid)
    if student is not None:
        fees = fees.filter(student=student)
    return fees.order_by('-academic_year', 'description', 'pk')


def describe_fee(fee):
    """Add paid, outstanding, status, label and css to a fee from ``fees_with_paid``."""
    fee.paid = fee.paid_total
    fee.outstanding = max(fee.amount_due - fee.paid_total, ZERO)
    fee.status = status_of(fee.amount_due, fee.paid_total)
    fee.status_label = STATUS_LABELS[fee.status]
    fee.status_class = STATUS_CLASSES[fee.status]
    return fee


def _totals(fees):
    total = sum((fee.amount_due for fee in fees), ZERO)
    paid = sum((fee.paid_total for fee in fees), ZERO)
    status = status_of(total, paid)
    return {
        'total': total, 'paid': paid, 'outstanding': max(total - paid, ZERO),
        'status': status, 'label': STATUS_LABELS[status], 'css': STATUS_CLASSES[status],
    }


def student_summary(student):
    """Total fee, amount paid and outstanding balance for one student, plus each fee (UT_13_Fee)."""
    fees = [describe_fee(fee) for fee in fees_with_paid(student)]
    return {**_totals(fees), 'fees': fees}


def students_with_fee_summary(query='', status=''):
    """One row per active student with fee totals; optionally searched and filtered by status."""
    students = Student.objects.select_related('hostel').filter(is_active=True)
    query = (query or '').strip()
    if query:
        students = students.filter(Q(full_name__icontains=query) | Q(roll_no__icontains=query))
    students = list(students.order_by('roll_no'))
    by_student = defaultdict(list)
    for fee in fees_with_paid().filter(student__in=students):
        by_student[fee.student_id].append(fee)
    rows = []
    for student in students:
        row = {'student': student, **_totals(by_student[student.pk]), 'fee_count': len(by_student[student.pk])}
        if status and row['status'] != status:
            continue
        rows.append(row)
    return rows


def _check_fee_amount(amount_due):
    if amount_due <= 0:
        raise ValidationError(msg('positive', field='Amount due'), code='positive')


def _check_fee_is_new(student, academic_year, description, exclude_pk=None):
    clash = FeeRecord.objects.filter(student=student, academic_year=academic_year,
                                     description__iexact=description)
    if exclude_pk is not None:
        clash = clash.exclude(pk=exclude_pk)
    if clash.exists():
        raise ValidationError(msg('fee_duplicate'), code='fee_duplicate')


def define_fee(student, *, academic_year, description, amount_due, due_date=None):
    """Create a fee for a student (FR-05.01). The fee belongs to the student's hostel."""
    _check_fee_amount(amount_due)
    _check_fee_is_new(student, academic_year, description)
    try:
        with transaction.atomic():
            return FeeRecord.objects.create(
                student=student, hostel=student.hostel, academic_year=academic_year,
                description=description, amount_due=amount_due, due_date=due_date)
    except IntegrityError:
        raise ValidationError(msg('fee_duplicate'), code='fee_duplicate') from None


def update_fee(fee, *, academic_year, description, amount_due, due_date=None):
    """Change a fee. The amount may not drop below what has already been paid."""
    _check_fee_amount(amount_due)
    paid = outstanding_paid(fee)
    if amount_due < paid:
        raise ValidationError(msg('fee_below_paid', paid=money(paid)), code='fee_below_paid')
    _check_fee_is_new(fee.student, academic_year, description, exclude_pk=fee.pk)
    fee.academic_year, fee.description = academic_year, description
    fee.amount_due, fee.due_date = amount_due, due_date
    try:
        with transaction.atomic():
            fee.save()
    except IntegrityError:
        raise ValidationError(msg('fee_duplicate'), code='fee_duplicate') from None
    return fee


def outstanding_paid(fee):
    """Total already paid against a fee."""
    return fee.payments.aggregate(total=Sum('amount'))['total'] or ZERO


def outstanding_of(fee):
    """What is still owed on a fee (never negative)."""
    return max(fee.amount_due - outstanding_paid(fee), ZERO)


def record_payment(fee, *, amount, mode, paid_on=None, reference='', received_by=None):
    """Record a payment against a fee (FR-05.03 to FR-05.06, FR-05.12).

    The fee row is locked while the balance is checked, so two payments saved at the same
    moment cannot together pay more than is owed.
    """
    if amount <= 0:
        raise ValidationError(msg('positive', field='Amount'), code='positive')
    if mode not in dict(Payment.MODE_CHOICES):
        raise ValidationError(msg('invalid_choice', field='Payment mode'), code='invalid_choice')
    paid_on = paid_on or timezone.localdate()
    with transaction.atomic():
        locked = FeeRecord.objects.select_for_update().get(pk=fee.pk)
        balance = outstanding_of(locked)
        if balance <= 0:
            raise ValidationError(msg('fee_already_paid'), code='fee_already_paid')
        if amount > balance:
            raise ValidationError(msg('payment_exceeds_balance', balance=money(balance)),
                                  code='payment_exceeds_balance')
        return Payment.objects.create(fee_record=locked, amount=amount, paid_on=paid_on, mode=mode,
                                      reference=reference, received_by=received_by)


def receipt_number(payment):
    """Receipt number for a payment, for example RCP-000123. Derived from the payment id."""
    return f'RCP-{payment.pk:06d}'


def balance_after(payment):
    """What was still owed on the fee right after this payment (receipts and history)."""
    fee = payment.fee_record
    until_now = fee.payments.filter(
        Q(paid_on__lt=payment.paid_on) | Q(paid_on=payment.paid_on, pk__lte=payment.pk)
    ).aggregate(total=Sum('amount'))['total'] or ZERO
    return max(fee.amount_due - until_now, ZERO)


def payment_history(student):
    """Every payment of a student, oldest first, each with its receipt number and balance after."""
    payments = (Payment.objects.filter(fee_record__student=student)
                .select_related('fee_record', 'received_by__user').order_by('paid_on', 'pk'))
    running = defaultdict(lambda: ZERO)
    history = []
    for payment in payments:
        running[payment.fee_record_id] += payment.amount
        payment.receipt_no = receipt_number(payment)
        payment.balance_after = max(payment.fee_record.amount_due - running[payment.fee_record_id], ZERO)
        history.append(payment)
    return history

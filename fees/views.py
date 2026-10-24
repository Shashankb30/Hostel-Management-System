"""Fee screens (FR-05, Issues #67 to #79)."""
import secrets

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from core.error_messages import msg
from core.feedback import flash_errors
from core.models import FeeRecord, Payment, Student, UserAccount
from core.roles import get_account, get_role, role_required

from . import services
from .forms import FeeForm, PaymentForm


ADMIN_ONLY = role_required(UserAccount.ROLE_ADMIN)
STUDENT_ONLY = role_required(UserAccount.ROLE_STUDENT)


def _own_student(request):
    """The logged-in student's Student record, or None if the account has none."""
    try:
        return get_account(request.user).student
    except ObjectDoesNotExist:
        return None


@ADMIN_ONLY
def manage(request):
    """Fee Management: every active student with total, paid and outstanding (FR-05)."""
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if status not in services.STATUS_LABELS:
        status = ''
    rows = services.students_with_fee_summary(query, status)
    totals = {
        'total': sum((row['total'] for row in rows), services.ZERO),
        'paid': sum((row['paid'] for row in rows), services.ZERO),
        'outstanding': sum((row['outstanding'] for row in rows), services.ZERO),
    }
    return render(request, 'fees/manage.html', {
        'rows': rows, 'query': query, 'status': status, 'totals': totals,
        'status_choices': [('', 'Any status')] + list(services.STATUS_LABELS.items()),
    })


@ADMIN_ONLY
def student_fees(request, student_id):
    """One student's fee structure: total, paid and outstanding, and each fee."""
    student = get_object_or_404(Student.objects.select_related('hostel'), pk=student_id)
    return render(request, 'fees/student_fees.html', {
        'student': student, 'summary': services.student_summary(student),
        'history': services.payment_history(student),
    })


@ADMIN_ONLY
def fee_create(request, student_id):
    student = get_object_or_404(Student.objects.select_related('hostel'), pk=student_id)
    form = FeeForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            fee = services.define_fee(
                student, academic_year=data['academic_year'], description=data['description'],
                amount_due=data['amount_due'], due_date=data['due_date'])
        except ValidationError as exc:
            flash_errors(request, exc)
        else:
            messages.success(request, f'Fee "{fee.description}" ({fee.academic_year}) added')
            return redirect('fees:student_fees', student_id=student.pk)
    return render(request, 'fees/fee_form.html',
                  {'form': form, 'student': student, 'title': f'Define fee for {student.full_name}'})


@ADMIN_ONLY
def fee_edit(request, fee_id):
    fee = get_object_or_404(FeeRecord.objects.select_related('student'), pk=fee_id)
    form = FeeForm(request.POST if request.method == 'POST' else None, fee=fee)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            services.update_fee(
                fee, academic_year=data['academic_year'], description=data['description'],
                amount_due=data['amount_due'], due_date=data['due_date'])
        except ValidationError as exc:
            flash_errors(request, exc)
        else:
            messages.success(request, 'Fee updated')
            return redirect('fees:student_fees', student_id=fee.student_id)
    return render(request, 'fees/fee_form.html', {
        'form': form, 'student': fee.student, 'title': f'Edit fee for {fee.student.full_name}'})


TOKEN_KEY = 'fee_payment_tokens'


def _new_token(request):
    """A one-time code for a payment form; only the most recent 20 are kept per session."""
    token = secrets.token_urlsafe(16)
    request.session[TOKEN_KEY] = request.session.get(TOKEN_KEY, [])[-19:] + [token]
    return token


def _token_is_open(request, token):
    return bool(token) and token in request.session.get(TOKEN_KEY, [])


def _close_token(request, token):
    request.session[TOKEN_KEY] = [t for t in request.session.get(TOKEN_KEY, []) if t != token]


@ADMIN_ONLY
def payment_create(request, fee_id):
    fee = get_object_or_404(FeeRecord.objects.select_related('student'), pk=fee_id)
    balance = services.outstanding_of(fee)
    if balance <= 0:
        messages.info(request, msg('fee_already_paid'))
        return redirect('fees:student_fees', student_id=fee.student_id)
    if request.method == 'POST':
        token = request.POST.get('submission_token', '')
        if not _token_is_open(request, token):
            # This form was already submitted (double click, Back button, refresh).
            messages.warning(request, msg('duplicate_payment'))
            return redirect('fees:student_fees', student_id=fee.student_id)
        form = PaymentForm(request.POST, balance=balance)
        if form.is_valid():
            data = form.cleaned_data
            try:
                payment = services.record_payment(
                    fee, amount=data['amount'], mode=data['mode'], paid_on=data['paid_on'],
                    reference=data['reference'], received_by=get_account(request.user))
            except ValidationError as exc:
                flash_errors(request, exc)
            else:
                _close_token(request, token)
                messages.success(request, f'Payment of {services.money(payment.amount)} recorded')
                return redirect('fees:receipt', payment_id=payment.pk)
    else:
        form = PaymentForm(None, balance=balance)
        token = _new_token(request)
    return render(request, 'fees/payment_form.html', {
        'form': form, 'fee': fee, 'student': fee.student, 'balance': balance, 'token': token})


@role_required(UserAccount.ROLE_ADMIN, UserAccount.ROLE_STUDENT)
def receipt(request, payment_id):
    """Receipt for one payment. A student may only open their own."""
    payment = get_object_or_404(
        Payment.objects.select_related('fee_record', 'fee_record__student', 'fee_record__hostel',
                                       'received_by__user'), pk=payment_id)
    fee = payment.fee_record
    if get_role(request.user) == UserAccount.ROLE_STUDENT:
        own = _own_student(request)
        if own is None or own.pk != fee.student_id:
            raise Http404
    return render(request, 'fees/receipt.html', {
        'payment': payment, 'fee': fee, 'student': fee.student,
        'receipt_no': services.receipt_number(payment),
        'balance_after': services.balance_after(payment),
    })


@STUDENT_ONLY
def my_fees(request):
    """The student's own fee status, balance and payment history (FR-05.09, FR-05.10)."""
    student = _own_student(request)
    return render(request, 'fees/my_fees.html', {
        'student': student,
        'summary': services.student_summary(student) if student else None,
        'history': services.payment_history(student) if student else [],
    })

"""Screens for Attendance Management (FR-07): marking, daily summary, history and report."""
import csv
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_POST

from core.error_messages import msg
from core.feedback import flash_errors
from core.models import Student, UserAccount
from core.roles import get_account, role_required

from . import services

STUDENT_ONLY = role_required(UserAccount.ROLE_STUDENT)
STAFF_ONLY = role_required(UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)


def _csv_cell(value):
    """Stop spreadsheets from running a cell that starts like a formula."""
    text = str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@', '\t', '\r') else text


def _day(raw):
    """A date from ?date=, or today when it is missing or invalid."""
    return (parse_date(raw) if raw else None) or timezone.localdate()


def _when(raw):
    """The optional time typed by the warden, or None for 'now'."""
    raw = (raw or '').strip()
    if not raw:
        return None
    value = parse_datetime(raw)
    if value is None:
        raise ValidationError(msg('invalid_format', field='Time'), code='invalid_format')
    return value


def _back(request):
    url = reverse('attendance:manage')
    day = request.POST.get('date', '')
    return redirect(f'{url}?date={day}' if parse_date(day or '') else url)


def _staff_student(account, pk):
    """A student inside the staff member's hostel, or 404."""
    return get_object_or_404(services._scope(account, Student.objects.all()), pk=pk)


# --- warden / administrator: mark and summarise -------------------------------------------

@STAFF_ONLY
def manage(request):
    """Today's attendance: present and absent per student, with check-in and check-out buttons."""
    account = get_account(request.user)
    day = _day(request.GET.get('date'))
    return render(request, 'attendance/manage.html', {
        'summary': services.daily_summary(account, day),
        'flags': services.open_flags(account),
        'is_today': day == timezone.localdate(),
        'now': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
    })


def _single(request, operation, verb):
    account = get_account(request.user)
    student = _staff_student(account, request.POST.get('student') or 0)
    try:
        operation(student, account, _when(request.POST.get('when')))
    except ValidationError as error:
        flash_errors(request, error)
    else:
        messages.success(request, f'{student.full_name} {verb}')
    return _back(request)


@STAFF_ONLY
@require_POST
def check_in(request):
    return _single(request, services.check_in, 'checked in')


@STAFF_ONLY
@require_POST
def check_out(request):
    return _single(request, services.check_out, 'checked out')


@STAFF_ONLY
@require_POST
def bulk(request):
    """Check several selected students in or out at the same time (IT_20_Att)."""
    account = get_account(request.user)
    action = request.POST.get('action', '')
    ids = [int(i) for i in request.POST.getlist('students') if i.isdigit()]
    students = list(services._scope(account, Student.objects.filter(pk__in=ids)).order_by('roll_no'))
    try:
        result = services.bulk_mark(students, action, account, _when(request.POST.get('when')))
    except ValidationError as error:
        flash_errors(request, error)
        return _back(request)
    verb = 'checked in' if action == services.ACTION_CHECK_IN else 'checked out'
    if result.done:
        messages.success(request, f'{len(result.done)} student(s) {verb}')
    for student, problem in result.failed:
        messages.error(request, f'{student.full_name}: {problem}')
    return _back(request)


# --- history and report (FR-07.08, FR-07.09) -----------------------------------------------

@STAFF_ONLY
def student_history(request, pk):
    """One student's attendance history. It only ever shows that student's entries (IT_21_Att)."""
    student = _staff_student(get_account(request.user), pk)
    return render(request, 'attendance/history.html', {
        'student': student, 'records': _with_duration(services.student_history(student)),
        'is_staff_view': True})


@STAFF_ONLY
def report(request):
    """Attendance between two dates, optionally for one student, with CSV download (ST_13_Att)."""
    account = get_account(request.user)
    today = timezone.localdate()
    start = _day_or_none(request.GET.get('start')) if request.GET.get('start') else today - timedelta(days=6)
    end = _day_or_none(request.GET.get('end')) if request.GET.get('end') else today
    student = None
    if request.GET.get('student', '').isdigit():
        student = services._scope(account, Student.objects.filter(pk=request.GET['student'])).first()
    result = {'rows': [], 'per_student': [], 'total': 0}
    if start is None or end is None:
        messages.error(request, msg('invalid_format', field='Date'))
        start, end = start or today - timedelta(days=6), end or today
    else:
        try:
            result = services.attendance_report(account, start, end, student)
        except ValidationError as error:
            flash_errors(request, error)
    if request.GET.get('export') == 'csv' and result['rows']:
        return _csv(result['rows'])
    return render(request, 'attendance/report.html', {
        'result': result, 'start': start.isoformat(), 'end': end.isoformat(), 'chosen': student,
        'students': services.allocated_students(account)})


def _day_or_none(raw):
    return parse_date(raw or '')


def _csv(rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance-report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Roll no', 'Student', 'Check-in', 'Check-out', 'Duration'])
    for r in rows:
        writer.writerow([r.attendance_date.isoformat(), _csv_cell(r.student.roll_no), _csv_cell(r.student.full_name),
                         services.format_time(r.check_in_at), services.format_time(r.check_out_at), r.duration])
    return response


def _with_duration(records):
    records = list(records)
    for record in records:
        record.duration = services.format_duration(record.check_in_at, record.check_out_at)
    return records


# --- student: my attendance (FR-07.08) -----------------------------------------------------

@STUDENT_ONLY
def my_attendance(request):
    """My Attendance: the student's own entries."""
    student = Student.objects.filter(user_account=get_account(request.user)).first()
    records = _with_duration(services.student_history(student)) if student is not None else []
    return render(request, 'attendance/history.html', {
        'student': student, 'records': records, 'is_staff_view': False})

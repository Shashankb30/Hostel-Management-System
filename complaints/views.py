"""Screens for Complaint Management (FR-06): student complaints, staff case handling, rules, report."""
import csv

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from core.error_messages import msg
from core.feedback import flash_errors
from core.models import Complaint, Student, UserAccount
from core.roles import get_account, get_role, role_required
from core.validators import validate_date_range

from . import services

STUDENT_ONLY = role_required(UserAccount.ROLE_STUDENT)
STAFF_ONLY = role_required(UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)
ANY_ROLE = role_required(UserAccount.ROLE_STUDENT, UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)


def _own_student(request):
    return Student.objects.filter(user_account=get_account(request.user)).first()


def _staff_complaint(request, pk):
    """A complaint inside the staff member's hostel, or 404."""
    return get_object_or_404(services._scope(get_account(request.user), Complaint.objects), pk=pk)


# --- student: raise and follow complaints (FR-06.01, .02, .12) ------------------------------

@STUDENT_ONLY
def my_complaints(request):
    """My Complaints: raise a new one, see every complaint and the demerit points (UT_16, UT_17)."""
    student = _own_student(request)
    form = {'category': '', 'title': '', 'description': ''}
    if request.method == 'POST' and student is not None:
        form = {k: request.POST.get(k, '') for k in form}
        try:
            complaint = services.submit_complaint(
                student, form['category'], form['description'], form['title'],
                raised_by=get_account(request.user))
        except ValidationError as error:
            flash_errors(request, error)
        else:
            messages.success(request, f'Complaint {complaint.complaint_id} submitted. Status: Open')
            return redirect('complaints:my_complaints')
    context = {'student': student, 'form': form, 'categories': Complaint.CATEGORY_CHOICES}
    if student is not None:
        context.update({
            'complaints': services.student_complaints(student),
            'demerit_total': services.demerit_total(student),
            'demerits': services.demerit_history(student),
        })
    return render(request, 'complaints/my_complaints.html', context)


@ANY_ROLE
def detail(request, pk):
    """One complaint with its history. Students only see their own."""
    role = get_role(request.user)
    if role == UserAccount.ROLE_STUDENT:
        student = _own_student(request)
        complaint = get_object_or_404(Complaint.objects.select_related('student'), pk=pk, student=student) \
            if student is not None else None
        if complaint is None:
            raise Http404
    else:
        complaint = _staff_complaint(request, pk)
    return render(request, 'complaints/detail.html', {
        'complaint': complaint,
        'updates': complaint.updates.select_related('changed_by__user'),
        'is_staff_view': role != UserAccount.ROLE_STUDENT,
        'can_edit': (role == UserAccount.ROLE_STUDENT and complaint.kind == Complaint.KIND_COMPLAINT
                     and complaint.status != Complaint.STATUS_RESOLVED),
        'status_choices': [c for c in Complaint.STATUS_CHOICES if c[0] != complaint.status],
        'demerit_total': services.demerit_total(complaint.student),
    })


@STUDENT_ONLY
def edit(request, pk):
    """Edit my own complaint. A resolved complaint is locked until a warden reopens it (ST_12)."""
    student = _own_student(request)
    complaint = get_object_or_404(Complaint, pk=pk, student=student, kind=Complaint.KIND_COMPLAINT) \
        if student is not None else None
    if complaint is None:
        raise Http404
    if complaint.status == Complaint.STATUS_RESOLVED:
        messages.error(request, msg('complaint_locked'))
        return redirect('complaints:detail', pk=pk)
    form = {'category': complaint.category, 'description': complaint.description}
    if request.method == 'POST':
        form = {k: request.POST.get(k, '') for k in form}
        try:
            services.edit_complaint(complaint, form['description'], form['category'])
        except ValidationError as error:
            flash_errors(request, error)
            if getattr(error, 'code', None) == 'complaint_locked':
                return redirect('complaints:detail', pk=pk)
        else:
            messages.success(request, f'Complaint {complaint.complaint_id} updated')
            return redirect('complaints:detail', pk=pk)
    return render(request, 'complaints/edit.html', {
        'complaint': complaint, 'form': form, 'categories': Complaint.CATEGORY_CHOICES})


# --- warden / administrator (FR-06.03 to .13) -------------------------------------------------

@STAFF_ONLY
def manage(request):
    """All complaints with filters by status, category and type (UT_18_Comp)."""
    account = get_account(request.user)
    filters = {
        'status': request.GET.get('status', ''), 'category': request.GET.get('category', ''),
        'kind': request.GET.get('kind', ''), 'q': request.GET.get('q', '').strip(),
        'escalated': request.GET.get('escalated') == '1',
    }
    complaints = services.list_complaints(
        account, status=filters['status'], category=filters['category'], kind=filters['kind'],
        escalated=filters['escalated'], search=filters['q'])
    everything = services.list_complaints(account)
    counts = {
        'open': everything.filter(status=Complaint.STATUS_OPEN).count(),
        'under_review': everything.filter(status=Complaint.STATUS_UNDER_REVIEW).count(),
        'resolved': everything.filter(status=Complaint.STATUS_RESOLVED).count(),
        'escalated': everything.filter(is_escalated=True).count(),
    }
    return render(request, 'complaints/manage.html', {
        'complaints': complaints, 'filters': filters, 'counts': counts,
        'statuses': Complaint.STATUS_CHOICES, 'categories': Complaint.CATEGORY_CHOICES,
        'kinds': Complaint.KIND_CHOICES,
    })


@STAFF_ONLY
def log_misconduct(request):
    """Log a misconduct case; the demerit points come from the severity rule (IT_16, IT_18)."""
    account = get_account(request.user)
    students = Student.objects.filter(is_active=True).order_by('roll_no')
    if account.hostel_id is not None:
        students = students.filter(hostel_id=account.hostel_id)
    form = {'student': '', 'severity': '', 'category': 'discipline', 'title': '', 'description': ''}
    if request.method == 'POST':
        form = {k: request.POST.get(k, '') for k in form}
        student = students.filter(pk=form['student']).first() if form['student'].isdigit() else None
        try:
            if student is None:
                raise ValidationError(msg('required', field='Student'), code='required')
            complaint = services.log_misconduct(
                student, form['severity'], form['description'], account,
                category=form['category'], title=form['title'])
        except ValidationError as error:
            flash_errors(request, error)
        else:
            record = complaint.demerit_records.first()
            points = record.points if record else 0
            messages.success(
                request, f'Case {complaint.complaint_id} logged for {student.full_name}: {points} demerit '
                         f'point(s) added. Total: {services.demerit_total(student)}')
            return redirect('complaints:detail', pk=complaint.pk)
    return render(request, 'complaints/misconduct_form.html', {
        'students': students, 'form': form, 'rules': services.list_rules(),
        'categories': Complaint.CATEGORY_CHOICES, 'severities': Complaint.SEVERITY_CHOICES,
    })


@STAFF_ONLY
@require_POST
def update_status(request, pk):
    complaint = _staff_complaint(request, pk)
    try:
        services.change_status(complaint, request.POST.get('status', ''), request.POST.get('remarks', ''),
                               get_account(request.user))
    except ValidationError as error:
        flash_errors(request, error)
    else:
        messages.success(request, f'Complaint {complaint.complaint_id} updated. The student has been notified')
    return redirect('complaints:detail', pk=pk)


@STAFF_ONLY
@require_POST
def reopen(request, pk):
    complaint = _staff_complaint(request, pk)
    try:
        services.reopen(complaint, request.POST.get('remarks', ''), get_account(request.user))
    except ValidationError as error:
        flash_errors(request, error)
    else:
        messages.success(request, f'Complaint {complaint.complaint_id} reopened')
    return redirect('complaints:detail', pk=pk)


@STAFF_ONLY
@require_POST
def escalate(request, pk):
    complaint = _staff_complaint(request, pk)
    try:
        services.escalate(complaint, request.POST.get('reason', ''), get_account(request.user))
    except ValidationError as error:
        flash_errors(request, error)
    else:
        messages.success(request, f'Complaint {complaint.complaint_id} escalated to the administrator')
    return redirect('complaints:detail', pk=pk)


@STAFF_ONLY
def rules(request):
    """Set the demerit points for each severity level (FR-06.05)."""
    if request.method == 'POST':
        posted = {severity: request.POST.get(f'points_{severity}', '') for severity in services.SEVERITIES}
        try:
            services.update_rules(posted)
        except ValidationError as error:
            flash_errors(request, error)
        else:
            messages.success(request, 'Demerit rules saved. Existing records keep the points they were given')
            return redirect('complaints:rules')
    return render(request, 'complaints/rules.html', {'rules': services.list_rules()})


@STAFF_ONLY
def report(request):
    """Complaint summary by category, optionally for a date range, with CSV download (ST_11_Comp)."""
    account = get_account(request.user)
    raw_start, raw_end = request.GET.get('start', ''), request.GET.get('end', '')
    start, end = parse_date(raw_start) if raw_start else None, parse_date(raw_end) if raw_end else None
    if (raw_start and start is None) or (raw_end and end is None):
        messages.error(request, msg('invalid_format', field='Date'))
        start = end = None
    elif start and end:
        try:
            validate_date_range(start, end, 'Start date', 'End date')
        except ValidationError as error:
            flash_errors(request, error)
            start = end = None
    summary = services.category_summary(account, start, end)
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="complaint-summary.csv"'
        writer = csv.writer(response)
        writer.writerow(['Category', 'Total', 'Open', 'Under Review', 'Resolved'])
        for row in summary['rows']:
            writer.writerow([row['label'], row['total'], row['open'], row['under_review'], row['resolved']])
        totals = summary['totals']
        writer.writerow(['All categories', totals['total'], totals['open'], totals['under_review'], totals['resolved']])
        return response
    return render(request, 'complaints/report.html', {
        'summary': summary, 'start': raw_start if start else '', 'end': raw_end if end else ''})

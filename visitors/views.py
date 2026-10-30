"""Views for Visitor Management (FR-08)."""
import csv

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from core.feedback import flash_errors
from core.models import Student, UserAccount, VisitorLog
from core.roles import get_account, get_role, role_required

from . import services
from .forms import VisitorDateFilterForm, VisitorForm, VisitorReportFilterForm

STAFF_ONLY = role_required(UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)
AUTHENTICATED_ONLY = role_required(UserAccount.ROLE_STUDENT, UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)

PAGE_SIZE = 25


def _scope_hostel(account):
    """Return hostel to scope by for wardens, or None for admins with all-hostel access."""
    if account and account.role == UserAccount.ROLE_WARDEN:
        return account.hostel
    return None


@STAFF_ONLY
def visitor_log(request):
    """View and search visitor logs (FR-08.01, FR-08.07)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    form = VisitorDateFilterForm(request.GET)
    q = request.GET.get('q', '').strip()
    raw_date = request.GET.get('date', '').strip()
    day = parse_date(raw_date) if raw_date else None

    logs = services.search_visitors(hostel=hostel, query=q, date=day)
    page = Paginator(logs, PAGE_SIZE).get_page(request.GET.get('page'))

    return render(request, 'visitors/log.html', {
        'page': page,
        'filter_form': form,
        'q': q,
        'selected_date': raw_date,
    })


@STAFF_ONLY
def visitor_add(request):
    """Add a new visitor and check them in (FR-08.01, FR-08.02, FR-08.03)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    if request.method == 'POST':
        form = VisitorForm(request.POST, hostel=hostel)
        if form.is_valid():
            student = form.cleaned_data['student']
            visitor_name = form.cleaned_data['visitor_name']
            id_proof = form.cleaned_data['id_proof']
            purpose = form.cleaned_data.get('purpose', '')
            visitor_phone = form.cleaned_data.get('visitor_phone', '')

            try:
                log = services.check_in(
                    student=student,
                    visitor_name=visitor_name,
                    id_proof=id_proof,
                    purpose=purpose,
                    visitor_phone=visitor_phone,
                    recorded_by=account,
                )
            except ValidationError as exc:
                flash_errors(request, exc)
            else:
                formatted_time = timezone.localtime(log.checked_in_at).strftime('%d %b %Y, %I:%M %p')
                messages.success(request, f'Visitor {log.visitor_name} checked in successfully at {formatted_time}.')
                return redirect('visitors:log')
    else:
        initial = {}
        if request.GET.get('student_id'):
            try:
                initial['student'] = Student.objects.get(pk=request.GET['student_id'])
            except Student.DoesNotExist:
                pass
        form = VisitorForm(initial=initial, hostel=hostel)

    return render(request, 'visitors/form.html', {
        'form': form,
        'title': 'Add Visitor / Check-in',
    })


@STAFF_ONLY
@require_POST
def visitor_checkout(request, pk):
    """Record checkout for an active visitor (FR-08.04, FR-08.05)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    qs = VisitorLog.objects.all()
    if hostel:
        qs = qs.filter(hostel=hostel)
    log = get_object_or_404(qs, pk=pk)

    try:
        services.check_out(log, recorded_by=account)
    except ValidationError as exc:
        flash_errors(request, exc)
    else:
        duration_str = services.format_duration(log.checked_in_at, log.checked_out_at)
        messages.success(request, f'Visitor {log.visitor_name} checked out. Visit duration: {duration_str}.')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'visitors:log'
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect('visitors:log')


@STAFF_ONLY
def visitor_report(request):
    """Visitor report with date range filter and CSV export (FR-08.08)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    form = VisitorReportFilterForm(request.GET)
    from_date = None
    to_date = None

    if form.is_valid():
        from_date = form.cleaned_data.get('from_date')
        to_date = form.cleaned_data.get('to_date')

    logs = services.visitor_report(hostel=hostel, from_date=from_date, to_date=to_date)

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="visitor_report.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Visitor Name', 'ID Proof', 'Phone', 'Student Visited', 'Roll Number',
            'Hostel', 'Purpose', 'Check-In Time', 'Check-Out Time', 'Duration', 'Recorded By',
        ])
        for entry in logs:
            check_in_str = timezone.localtime(entry.checked_in_at).strftime('%Y-%m-%d %H:%M:%S') if entry.checked_in_at else ''
            check_out_str = timezone.localtime(entry.checked_out_at).strftime('%Y-%m-%d %H:%M:%S') if entry.checked_out_at else ''
            duration_str = services.format_duration(entry.checked_in_at, entry.checked_out_at)
            recorded_by_name = entry.recorded_by.user.get_full_name() or entry.recorded_by.user.username if entry.recorded_by else ''

            writer.writerow([
                entry.visitor_name,
                entry.id_proof,
                entry.visitor_phone,
                entry.student.full_name,
                entry.student.roll_no,
                entry.hostel.name,
                entry.purpose,
                check_in_str,
                check_out_str,
                duration_str,
                recorded_by_name,
            ])
        return response

    page = Paginator(logs, PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'visitors/report.html', {
        'page': page,
        'filter_form': form,
        'from_date': from_date,
        'to_date': to_date,
    })


@AUTHENTICATED_ONLY
def student_visitor_history(request, student_id):
    """View visitor logs linked to a specific student (FR-08.06)."""
    account = get_account(request.user)
    role = get_role(request.user)

    if role == UserAccount.ROLE_STUDENT:
        if not hasattr(account, 'student') or account.student.id != student_id:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

    qs = Student.objects.select_related('hostel')
    if role == UserAccount.ROLE_WARDEN and account.hostel:
        qs = qs.filter(hostel=account.hostel)
    student = get_object_or_404(qs, pk=student_id)

    logs = services.get_student_visitor_history(student)
    page = Paginator(logs, PAGE_SIZE).get_page(request.GET.get('page'))

    return render(request, 'visitors/student_history.html', {
        'student': student,
        'page': page,
    })

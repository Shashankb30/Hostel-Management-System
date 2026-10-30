"""Views for Home / Long-Leave Application (FR-09)."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.feedback import flash_errors
from core.models import LeaveApplication, UserAccount
from core.roles import get_account, role_required

from . import services
from .forms import LeaveApplicationForm, LeaveFilterForm, LeaveReviewForm

STUDENT_ONLY = role_required(UserAccount.ROLE_STUDENT)
STAFF_ONLY = role_required(UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)
AUTHENTICATED = role_required(UserAccount.ROLE_STUDENT, UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)

PAGE_SIZE = 25


def _get_student_for_user(request):
    """Retrieve the Student object for the logged-in student user, or raise 403."""
    account = get_account(request.user)
    if not account or not hasattr(account, 'student'):
        raise PermissionDenied
    return account.student


def _scope_hostel(account):
    """Return hostel for wardens, None for admins (access to all hostels)."""
    if account and account.role == UserAccount.ROLE_WARDEN:
        return account.hostel
    return None


# --- Student Screens ---

@STUDENT_ONLY
def my_leaves(request):
    """Student leave application history & status tracking (FR-09.09, ST_17)."""
    student = _get_student_for_user(request)
    applications = services.get_student_leaves(student)
    page = Paginator(applications, PAGE_SIZE).get_page(request.GET.get('page'))

    return render(request, 'leave/my_leaves.html', {
        'student': student,
        'page': page,
    })


@STUDENT_ONLY
def apply_leave(request):
    """Student submits a new leave application (FR-09.01, FR-09.02, FR-09.03, UT_25, UT_26, UT_27)."""
    student = _get_student_for_user(request)

    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST)
        if form.is_valid():
            try:
                app = services.submit_leave_application(
                    student=student,
                    from_date=form.cleaned_data['from_date'],
                    to_date=form.cleaned_data['to_date'],
                    reason=form.cleaned_data['reason'],
                    destination=form.cleaned_data.get('destination', ''),
                )
            except ValidationError as exc:
                flash_errors(request, exc)
            else:
                messages.success(request, f'Leave application {app.application_id} submitted successfully.')
                return redirect('leave:my_leaves')
    else:
        form = LeaveApplicationForm()

    return render(request, 'leave/apply.html', {
        'form': form,
        'title': 'Apply for Leave',
    })


@STUDENT_ONLY
def resubmit_leave(request, pk):
    """Student updates and resubmits application when info was requested (FR-09.08)."""
    student = _get_student_for_user(request)
    app = get_object_or_404(LeaveApplication, pk=pk, student=student)

    if app.status != LeaveApplication.STATUS_INFO_REQUESTED:
        messages.warning(request, 'This application does not require more information.')
        return redirect('leave:my_leaves')

    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST, instance=app)
        if form.is_valid():
            try:
                services.resubmit_application(
                    application=app,
                    from_date=form.cleaned_data['from_date'],
                    to_date=form.cleaned_data['to_date'],
                    reason=form.cleaned_data['reason'],
                    destination=form.cleaned_data.get('destination', ''),
                )
            except ValidationError as exc:
                flash_errors(request, exc)
            else:
                messages.success(request, f'Leave application {app.application_id} resubmitted successfully.')
                return redirect('leave:my_leaves')
    else:
        form = LeaveApplicationForm(instance=app)

    return render(request, 'leave/apply.html', {
        'form': form,
        'title': f'Update Leave Application ({app.application_id})',
        'application': app,
    })


@STUDENT_ONLY
@require_POST
def cancel_leave(request, pk):
    """Student cancels their pending leave application."""
    student = _get_student_for_user(request)
    app = get_object_or_404(LeaveApplication, pk=pk, student=student)

    try:
        services.cancel_application(app, student)
    except ValidationError as exc:
        flash_errors(request, exc)
    else:
        messages.success(request, f'Leave application {app.application_id} was cancelled.')

    return redirect('leave:my_leaves')


# --- Staff Screens (Warden / Admin) ---

@STAFF_ONLY
def review_list(request):
    """Warden reviews pending leave applications (FR-09.04, IT_25)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    form = LeaveFilterForm(request.GET)
    status_filter = request.GET.get('status')
    # Default to pending if not specified in review screen
    if status_filter is None:
        status_filter = LeaveApplication.STATUS_PENDING
    elif status_filter == '':
        status_filter = None

    q = request.GET.get('q', '').strip()

    applications = services.get_all_leaves(hostel=hostel, status=status_filter, query=q)
    page = Paginator(applications, PAGE_SIZE).get_page(request.GET.get('page'))

    return render(request, 'leave/review_list.html', {
        'page': page,
        'filter_form': form,
        'selected_status': status_filter or '',
        'q': q,
        'tab': 'review',
    })


@STAFF_ONLY
def review_detail(request, pk):
    """Review single application: view overlap warnings, approve, reject or request info (FR-09.05, FR-09.06, FR-09.07, FR-09.08)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    qs = LeaveApplication.objects.select_related('student', 'hostel')
    if hostel:
        qs = qs.filter(hostel=hostel)
    app = get_object_or_404(qs, pk=pk)

    # Check for overlapping approved leaves (IT_27)
    overlaps = services.get_overlapping_leaves(app)

    if request.method == 'POST':
        form = LeaveReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            remarks = form.cleaned_data['remarks']

            try:
                if action == LeaveReviewForm.ACTION_APPROVE:
                    services.approve_application(app, reviewer=account, remarks=remarks)
                    messages.success(request, f'Application {app.application_id} approved.')
                elif action == LeaveReviewForm.ACTION_REJECT:
                    services.reject_application(app, reviewer=account, remarks=remarks)
                    messages.success(request, f'Application {app.application_id} rejected.')
                elif action == LeaveReviewForm.ACTION_REQUEST_INFO:
                    services.request_more_information(app, reviewer=account, remarks=remarks)
                    messages.success(request, f'Requested more information for application {app.application_id}.')
            except ValidationError as exc:
                flash_errors(request, exc)
            else:
                return redirect('leave:review')
    else:
        form = LeaveReviewForm()

    return render(request, 'leave/review_detail.html', {
        'application': app,
        'overlaps': overlaps,
        'form': form,
    })


@STAFF_ONLY
def consolidated_records(request):
    """Administrator consolidated leave records across all students (FR-09.10, ST_18)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    form = LeaveFilterForm(request.GET)
    status_filter = request.GET.get('status', '').strip() or None
    q = request.GET.get('q', '').strip()

    applications = services.get_all_leaves(hostel=hostel, status=status_filter, query=q)
    page = Paginator(applications, PAGE_SIZE).get_page(request.GET.get('page'))

    return render(request, 'leave/records.html', {
        'page': page,
        'filter_form': form,
        'selected_status': status_filter or '',
        'q': q,
        'tab': 'records',
    })

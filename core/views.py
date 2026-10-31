from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import UserAccount
from .roles import DASHBOARD_URL_NAMES, get_account, get_role, role_required

# Placeholder tiles. Each module replaces its tile with real data when it is delivered.
TILES = {
    UserAccount.ROLE_STUDENT: [
        ('My Room', 'Your allocated room and roommates will appear here.'),
        ('Fees', 'Your dues and payment history will appear here.'),
        ('Attendance', 'Check in and check out from here.'),
        ('Notices', 'Latest hostel notices will appear here.'),
    ],
    UserAccount.ROLE_WARDEN: [
        ('Room Vacancy', 'Vacant and occupied rooms by block will appear here.'),
        ('Pending Complaints', 'Open complaints needing action will appear here.'),
        ('Leave Requests', 'Applications waiting for approval will appear here.'),
        ('Visitors Today', 'Today\'s visitor log will appear here.'),
    ],
    UserAccount.ROLE_ADMIN: [
        ('Students', 'Registered student records will appear here.'),
        ('Rooms', 'Room configuration and capacity will appear here.'),
        ('Fees', 'Fee demands and collections will appear here.'),
        ('Users & Roles', 'Account and role management will appear here.'),
    ],
}


def _render_dashboard(request, role, title):
    account = get_account(request.user)
    try:
        student = account.student
    except ObjectDoesNotExist:
        student = None

    context = {
        'title': title,
        'account': account,
        'student': student,
        'tiles': TILES[role],
    }

    if role == UserAccount.ROLE_STUDENT:
        from notices.services import get_active_notices
        context['latest_notices'] = get_active_notices(
            role=role, hostel=account.hostel if account else None
        )[:5]

    return render(request, 'core/dashboard.html', context)


@login_required
def home(request):
    """Send each user to the dashboard for their role."""
    role = get_role(request.user)
    if role is None:
        raise PermissionDenied
    return redirect(DASHBOARD_URL_NAMES[role])


@role_required(UserAccount.ROLE_STUDENT)
def dashboard_student(request):
    return _render_dashboard(request, UserAccount.ROLE_STUDENT, 'Student Dashboard')


@role_required(UserAccount.ROLE_WARDEN)
def dashboard_warden(request):
    return _render_dashboard(request, UserAccount.ROLE_WARDEN, 'Warden Dashboard')


@role_required(UserAccount.ROLE_ADMIN)
def dashboard_admin(request):
    return _render_dashboard(request, UserAccount.ROLE_ADMIN, 'Administrator Dashboard')


def health_check(request):
    """NFR-08 / NFR.13: Health check endpoint verifying web and database connectivity."""
    db_ok = True
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception as e:
        db_ok = False
        db_error = str(e)

    status_code = 200 if db_ok else 503
    payload = {
        'status': 'healthy' if db_ok else 'unhealthy',
        'database': 'connected' if db_ok else 'disconnected',
        'service': 'Hostel Management System (HMS)',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
    }
    if db_error:
        payload['error'] = db_error
    return JsonResponse(payload, status=status_code)


def maintenance_view(request):
    """NFR-08: Maintenance notice view during planned maintenance windows."""
    from .models import Notice
    account = get_account(request.user)
    hostel = account.hostel if account else None

    # Fetch any published maintenance notices
    notices_qs = Notice.objects.filter(is_published=True, title__icontains='maintenance')
    if hostel:
        notices_qs = notices_qs.filter(hostel=hostel)
    maintenance_notice = notices_qs.order_by('-published_at').first()

    return render(request, 'core/maintenance.html', {
        'notice': maintenance_notice,
    })


def bad_request_view(request, exception=None):
    """Custom 400 Bad Request handler (NFR-04)."""
    return render(request, '400.html', status=400)


def permission_denied_view(request, exception=None):
    """Custom 403 Forbidden handler (NFR-01)."""
    return render(request, '403.html', status=403)


def page_not_found_view(request, exception=None):
    """Custom 404 Not Found handler."""
    return render(request, '404.html', status=404)


def server_error_view(request):
    """Custom 500 Server Error handler: friendly message, no stack trace (NFR-04)."""
    return render(request, '500.html', status=500)


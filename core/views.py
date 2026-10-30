from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import redirect, render

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

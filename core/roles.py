"""Role helpers shared by every module (Issue #12, SETUP.11)."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from .models import UserAccount

ROLE_LABELS = {
    UserAccount.ROLE_STUDENT: 'Student',
    UserAccount.ROLE_WARDEN: 'Warden',
    UserAccount.ROLE_ADMIN: 'Administrator',
}

# Where each role lands after login.
DASHBOARD_URL_NAMES = {
    UserAccount.ROLE_STUDENT: 'core:dashboard_student',
    UserAccount.ROLE_WARDEN: 'core:dashboard_warden',
    UserAccount.ROLE_ADMIN: 'core:dashboard_admin',
}


def get_account(user):
    """Return the user's UserAccount, or None (anonymous, or no HMS account)."""
    if not getattr(user, 'is_authenticated', False):
        return None
    try:
        return user.hms_account
    except ObjectDoesNotExist:
        return None


def get_role(user):
    """Return 'student' / 'warden' / 'admin', or None if the user has no usable role."""
    account = get_account(user)
    if account is None or account.is_locked:
        return None
    return account.role


def role_required(*roles):
    """Allow only the given roles. Anonymous users go to login; other roles get a 403."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if get_role(request.user) not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return login_required(wrapper)

    return decorator

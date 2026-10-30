"""Lock an account after repeated wrong passwords (Issue #26, FR-01.11).

The threshold is ``HMS_MAX_FAILED_LOGINS`` in settings (environment variable of the
same name, default 5). A locked account stays locked until an administrator unlocks it
on the Users & Roles screen or with ``python manage.py unlock_account <username>``.
"""
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from core.models import UserAccount


def max_attempts():
    """Wrong passwords allowed in a row before the account locks (never less than 1)."""
    return max(int(getattr(settings, 'HMS_MAX_FAILED_LOGINS', 5)), 1)


def register_failure(account):
    """Count one wrong password. Returns True when this attempt locked the account."""
    with transaction.atomic():
        UserAccount.objects.filter(pk=account.pk).update(
            failed_login_attempts=F('failed_login_attempts') + 1, updated_at=timezone.now())
        account.refresh_from_db(fields=['failed_login_attempts', 'is_locked'])
        if account.failed_login_attempts >= max_attempts() and not account.is_locked:
            UserAccount.objects.filter(pk=account.pk).update(
                is_locked=True, updated_at=timezone.now())
            account.is_locked = True
            return True
    return False


def register_success(account):
    """A good login (or password reset) clears the count of wrong passwords."""
    if account.failed_login_attempts:
        UserAccount.objects.filter(pk=account.pk).update(
            failed_login_attempts=0, updated_at=timezone.now())
        account.failed_login_attempts = 0


def unlock(account):
    """Administrator action: unlock the account and clear the count."""
    UserAccount.objects.filter(pk=account.pk).update(
        is_locked=False, failed_login_attempts=0, updated_at=timezone.now())
    account.is_locked = False
    account.failed_login_attempts = 0

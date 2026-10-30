"""Administrator tools for user accounts and roles (Issue #25, FR-01.10)."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from core.error_messages import msg
from core.models import UserAccount

from . import lockout


def _apply_role_flags(user, role):
    """Administrators may use the Django admin site; nobody else may."""
    is_admin = role == UserAccount.ROLE_ADMIN
    user.is_staff = is_admin
    user.is_superuser = is_admin


@transaction.atomic
def create_account(*, username, password, role, hostel=None, first_name='', last_name='',
                   email='', phone=''):
    user = get_user_model()(
        username=username, first_name=first_name, last_name=last_name, email=email)
    user.set_password(password)
    _apply_role_flags(user, role)
    user.save()
    return UserAccount.objects.create(user=user, role=role, hostel=hostel, phone=phone)


@transaction.atomic
def update_account(account, *, acting_user, role, hostel, first_name, last_name, email, phone):
    """Change a person's details and role. Nobody can change their own role, so an
    administrator can never remove their own access by accident."""
    if role != account.role and account.user_id == acting_user.pk:
        raise ValidationError(msg('cannot_change_own_role'), code='cannot_change_own_role')
    user = account.user
    user.first_name, user.last_name, user.email = first_name, last_name, email
    _apply_role_flags(user, role)
    user.save()
    account.role, account.hostel, account.phone = role, hostel, phone
    account.save()
    return account


@transaction.atomic
def set_active(account, active, *, acting_user):
    """Deactivate or reactivate an account. A deactivated account cannot log in."""
    if not active and account.user_id == acting_user.pk:
        raise ValidationError(msg('cannot_deactivate_self'), code='cannot_deactivate_self')
    account.user.is_active = active
    account.user.save(update_fields=['is_active'])


def unlock(account):
    lockout.unlock(account)

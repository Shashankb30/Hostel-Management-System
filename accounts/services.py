"""Login rules for FR-01: who may log in, and what the user is told when they may not.

``authenticate_credentials`` is the single place that decides a login attempt. It never
logs anyone in itself. The login view does that only when ``result.ok`` is True, so a
refused attempt never creates a session.
"""
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from core.error_messages import msg

# Recorded on the user object so django.contrib.auth.login() accepts it.
AUTH_BACKEND = 'django.contrib.auth.backends.ModelBackend'


@dataclass(frozen=True)
class LoginResult:
    user: object = None
    message: str = ''
    code: str = ''

    @property
    def ok(self):
        return self.user is not None


def _refused(key):
    return LoginResult(message=msg(key), code=key)


def hms_account(user):
    """The user's UserAccount, or None when the Django user has no HMS account."""
    try:
        return user.hms_account
    except ObjectDoesNotExist:
        return None


def authenticate_credentials(username, password):
    user_model = get_user_model()
    try:
        user = user_model._default_manager.get_by_natural_key(username)
    except user_model.DoesNotExist:
        user_model().set_password(password)  # same hashing work as a real check
        return _refused('invalid_credentials')

    account = hms_account(user)

    if not user.check_password(password):
        # Same message for "no such user" and "wrong password" (FR-01.03).
        return _refused('invalid_credentials')

    # The password is right. Only now say why the account cannot be used, so that
    # strangers cannot probe which accounts are inactive or locked.
    if not user.is_active:
        return _refused('invalid_credentials')
    if account is None:
        return _refused('no_role')
    user.backend = AUTH_BACKEND
    return LoginResult(user=user)

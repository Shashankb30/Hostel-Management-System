"""In-app notification service (Issue #14, SETUP.13).

Other modules call these functions; they never touch the Notification table directly:

    from core.notifications import notify
    notify(student, 'ALLOCATION', 'You have been allocated room A-101')   # FR-04
    notify(student, 'COMPLAINT', 'Your complaint was marked Resolved')    # FR-06
    notify(student, 'LEAVE', 'Your leave application was approved')       # FR-09

``student`` may be a Student or a UserAccount (for example a warden).
"""
from django.core.exceptions import ValidationError
from django.utils import timezone

from .error_messages import msg
from .models import Notification, Student, UserAccount
from .validators import ErrorCollector, RequiredValidator

CATEGORIES = [value for value, _label in Notification.CATEGORY_CHOICES]
MESSAGE_MAX_LENGTH = Notification._meta.get_field('message').max_length


def _account(target):
    """Return the UserAccount behind a Student or UserAccount."""
    if isinstance(target, Student):
        return target.user_account
    if isinstance(target, UserAccount):
        return target
    raise TypeError('Expected a Student or UserAccount, got %s' % type(target).__name__)


def _validate_category(value):
    if value not in CATEGORIES:
        raise ValidationError(
            msg('invalid_choice', field='Notification type'), code='invalid_choice')


def _validate_message_length(value):
    if len(value) > MESSAGE_MAX_LENGTH:
        raise ValidationError(
            msg('max_length', field='Message', limit=MESSAGE_MAX_LENGTH), code='max_length')


def notify(student, category, message):
    """Save an unread notification for ``student`` and return it.

    ``category`` (the notification type) is one of ALLOCATION, FEE, LEAVE, COMPLAINT, NOTICE.
    Raises ValidationError, using the standard messages, if the type or message is invalid.
    """
    recipient = _account(student)
    category = category.strip().upper() if isinstance(category, str) else category
    message = message.strip() if isinstance(message, str) else message

    errors = ErrorCollector()
    errors.check('category', RequiredValidator('Notification type'), category)
    if category:
        errors.check('category', _validate_category, category)
    errors.check('message', RequiredValidator('Message'), message)
    if message:
        errors.check('message', _validate_message_length, message)
    errors.raise_if_any()

    return Notification.objects.create(recipient=recipient, category=category, message=message)


def get_notifications(target, unread_only=False):
    """Notifications for a user, newest first."""
    notifications = Notification.objects.filter(recipient=_account(target))
    if unread_only:
        notifications = notifications.filter(is_read=False)
    return notifications


def unread_count(target):
    return get_notifications(target, unread_only=True).count()


def _set_read(target, notification_id, value):
    updated = Notification.objects.filter(
        pk=notification_id, recipient=_account(target)
    ).update(is_read=value, updated_at=timezone.now())
    return updated == 1


def mark_read(target, notification_id):
    """Mark one of the user's notifications read. False if it is not theirs / does not exist."""
    return _set_read(target, notification_id, True)


def mark_unread(target, notification_id):
    """Mark one of the user's notifications unread again."""
    return _set_read(target, notification_id, False)


def mark_all_read(target):
    """Mark every unread notification of the user as read; return how many changed."""
    return get_notifications(target, unread_only=True).update(
        is_read=True, updated_at=timezone.now())

"""Business rules for Notice / Information Management (FR-10).

    publish_notice         FR-10.01, .02, .04   Create/publish notice with title, content, audience, and optional expiry (UT_28, UT_29, UT_30)
    update_notice          FR-10.05             Edit existing notice (IT_28)
    delete_notice          FR-10.06             Delete a notice (IT_29)
    expire_notice          FR-10.06             Mark notice expired / unpublished (IT_29)
    get_notices_for_user   FR-10.03, .04, .07   Ordered newest first, filter by audience and expiry (UT_30, IT_30)
    search_notices         FR-10.08             Keyword search in title or body (ST_19)
"""
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from core.error_messages import msg
from core.models import Notice, UserAccount


def _make_aware_end_of_day(date_val):
    """Convert a date or datetime to an aware datetime at end-of-day (23:59:59) in local timezone."""
    if date_val is None:
        return None
    if isinstance(date_val, datetime):
        return timezone.make_aware(date_val) if timezone.is_naive(date_val) else date_val
    # It's a date object
    dt = datetime.combine(date_val, datetime.max.time().replace(microsecond=0))
    return timezone.make_aware(dt)


def publish_notice(title, body, author, audience='all', hostel=None, expires_at=None, is_published=True):
    """Create and optionally publish a notice (FR-10.01, FR-10.02, FR-10.04)."""
    title = (title or '').strip()
    body = (body or '').strip()

    if not title:
        raise ValidationError(msg('required', field='Title'), code='required')
    if not body:
        raise ValidationError(msg('required', field='Content'), code='required')

    if audience not in ('all', 'students', 'wardens'):
        audience = 'all'

    expiry_dt = _make_aware_end_of_day(expires_at)
    now = timezone.now()

    notice = Notice.objects.create(
        title=title,
        body=body,
        published_by=author,
        hostel=hostel,
        audience=audience,
        expires_at=expiry_dt,
        is_published=is_published,
        published_at=now if is_published else None,
    )
    return notice


def update_notice(notice, title=None, body=None, audience=None, hostel=None, expires_at=None, is_published=None):
    """Update an existing notice (FR-10.05, IT_28)."""
    if title is not None:
        title = title.strip()
        if not title:
            raise ValidationError(msg('required', field='Title'), code='required')
        notice.title = title

    if body is not None:
        body = body.strip()
        if not body:
            raise ValidationError(msg('required', field='Content'), code='required')
        notice.body = body

    if audience is not None:
        if audience in ('all', 'students', 'wardens'):
            notice.audience = audience

    if hostel is not None:
        notice.hostel = hostel

    if expires_at is not None:
        notice.expires_at = _make_aware_end_of_day(expires_at)

    if is_published is not None:
        if is_published and not notice.is_published:
            notice.published_at = timezone.now()
        notice.is_published = is_published

    notice.save()
    return notice


def delete_notice(notice):
    """Delete a notice (FR-10.06, IT_29)."""
    pk = notice.pk
    notice.delete()
    return pk


def expire_notice(notice):
    """Mark a notice expired or unpublish it (FR-10.06, IT_29)."""
    notice.is_published = False
    notice.expires_at = timezone.now()
    notice.save(update_fields=['is_published', 'expires_at', 'updated_at'])
    return notice


def get_active_notices(role=None, hostel=None):
    """Return published, unexpired notices visible to the specified role, newest first (FR-10.03, FR-10.04, FR-10.07, IT_30)."""
    now = timezone.now()
    qs = Notice.objects.filter(is_published=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )

    if hostel is not None:
        qs = qs.filter(Q(hostel__isnull=True) | Q(hostel=hostel))

    if role == UserAccount.ROLE_STUDENT:
        qs = qs.filter(audience__in=['all', 'students'])
    elif role == UserAccount.ROLE_WARDEN:
        qs = qs.filter(audience__in=['all', 'wardens'])

    # Ordered newest first (IT_30)
    return qs.select_related('published_by', 'published_by__user', 'hostel').order_by('-published_at', '-created_at')


def search_notices(keyword=None, audience=None, hostel=None, include_unpublished=False):
    """Search notices by keyword, audience, and hostel (FR-10.08, ST_19)."""
    qs = Notice.objects.all()

    if not include_unpublished:
        now = timezone.now()
        qs = qs.filter(is_published=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

    if hostel is not None:
        qs = qs.filter(Q(hostel__isnull=True) | Q(hostel=hostel))

    if audience:
        qs = qs.filter(audience=audience)

    if keyword:
        kw = keyword.strip()
        qs = qs.filter(Q(title__icontains=kw) | Q(body__icontains=kw))

    return qs.select_related('published_by', 'published_by__user', 'hostel').order_by('-created_at')

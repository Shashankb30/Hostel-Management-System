"""Business rules for Visitor Management (FR-08).

    check_in             FR-08.01, .02, .03   Record visitor check-in with timestamp; reject missing details (UT_22, UT_23, UT_24)
    check_out            FR-08.04, .05        Update same log entry with checkout time and duration; prevent double check-out (IT_22, ST_16)
    student_history      FR-08.06             Show visitor history for a student (IT_23)
    search_visitors      FR-08.07             Search visitor entries by student name or date (IT_24)
    visitor_report       FR-08.08             List visitor entries for a date range (ST_15)
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from core.error_messages import msg
from core.models import VisitorLog


def format_duration(start, end):
    """Format duration between start and end into a human-readable string like '1 h 30 min'."""
    if not start or not end:
        return ''
    total_seconds = int((end - start).total_seconds())
    if total_seconds < 0:
        return ''
    minutes = total_seconds // 60
    hours = minutes // 60
    rem_min = minutes % 60
    if hours > 0:
        return f'{hours} h {rem_min:02d} min'
    return f'{rem_min} min'


def _when(value):
    """The timestamp to record: defaults to timezone.now(). Must not be in the future."""
    now = timezone.now()
    if value is None:
        return now
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    if value > now + timedelta(minutes=1):
        raise ValidationError(msg('future_time', field='Time'), code='future_time')
    return value


def check_in(student, visitor_name, id_proof, purpose='', visitor_phone='', recorded_by=None, check_in_at=None):
    """Record a visitor check-in with timestamp (FR-08.01, FR-08.02, FR-08.03)."""
    visitor_name = (visitor_name or '').strip()
    id_proof = (id_proof or '').strip()
    purpose = (purpose or '').strip()
    visitor_phone = (visitor_phone or '').strip()

    if not visitor_name:
        raise ValidationError(msg('required', field='Visitor name'), code='required')
    if not id_proof:
        raise ValidationError(msg('required', field='ID proof'), code='required')
    if not student:
        raise ValidationError(msg('required', field='Student'), code='required')

    timestamp = _when(check_in_at)
    hostel = student.hostel

    log = VisitorLog.objects.create(
        student=student,
        hostel=hostel,
        visitor_name=visitor_name,
        id_proof=id_proof,
        purpose=purpose,
        visitor_phone=visitor_phone,
        checked_in_at=timestamp,
        recorded_by=recorded_by,
    )
    return log


def check_out(visitor_log, recorded_by=None, check_out_at=None):
    """Record a visitor check-out on an active log entry (FR-08.04, FR-08.05)."""
    if visitor_log.checked_out_at is not None:
        raise ValidationError(msg('already_checked_out'), code='already_checked_out')

    timestamp = _when(check_out_at)
    if timestamp < visitor_log.checked_in_at:
        since = timezone.localtime(visitor_log.checked_in_at).strftime('%d %b %Y, %I:%M %p')
        raise ValidationError(msg('checkout_before_checkin', since=since), code='checkout_before_checkin')

    visitor_log.checked_out_at = timestamp
    visitor_log.save(update_fields=['checked_out_at', 'updated_at'])
    return visitor_log


def search_visitors(hostel=None, query=None, date=None):
    """Search visitor logs by student name/roll number or date (FR-08.07)."""
    qs = VisitorLog.objects.select_related('student', 'hostel', 'recorded_by').all()
    if hostel is not None:
        qs = qs.filter(hostel=hostel)

    if query:
        query = query.strip()
        qs = qs.filter(
            Q(student__full_name__icontains=query) |
            Q(student__roll_no__icontains=query) |
            Q(visitor_name__icontains=query)
        )

    if date is not None:
        qs = qs.filter(checked_in_at__date=date)

    return qs.order_by('-checked_in_at')


def visitor_report(hostel=None, from_date=None, to_date=None):
    """Retrieve visitor logs within a date range for reporting (FR-08.08)."""
    qs = VisitorLog.objects.select_related('student', 'hostel', 'recorded_by').all()
    if hostel is not None:
        qs = qs.filter(hostel=hostel)

    if from_date is not None:
        qs = qs.filter(checked_in_at__date__gte=from_date)
    if to_date is not None:
        qs = qs.filter(checked_in_at__date__lte=to_date)

    return qs.order_by('-checked_in_at')


def get_student_visitor_history(student):
    """Return visitor history for a specific student (FR-08.06)."""
    return VisitorLog.objects.filter(student=student).select_related('hostel', 'recorded_by').order_by('-checked_in_at')

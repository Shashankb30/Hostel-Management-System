"""Business rules for Attendance Management (FR-07). Views call these functions only.

    check_in           FR-07.01, .03, .05   record a check-in; refuse a duplicate or a student without a room (UT_19, UT_21)
    check_out          FR-07.02, .04        record a check-out; refuse if there is no open check-in (UT_20, ST_14)
    bulk_mark          FR-07.06             check several students in or out together (IT_20_Att)
    daily_summary      FR-07.07             present / absent for one day (IT_19_Att)
    student_history    FR-07.08             one student's entries (IT_21_Att)
    attendance_report  FR-07.09             entries between two dates (ST_13_Att)

One student has at most one attendance entry per day (the database enforces it). A check-in
leaves the entry open; the matching check-out closes it, even if that is the next morning.
"""
from dataclasses import dataclass, field
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.error_messages import msg
from core.models import Allocation, AttendanceRecord, Student
from core.validators import validate_date_range

ACTION_CHECK_IN = 'check_in'
ACTION_CHECK_OUT = 'check_out'
ACTIONS = [ACTION_CHECK_IN, ACTION_CHECK_OUT]

STATUS_ABSENT = 'absent'
STATUS_INSIDE = 'inside'
STATUS_OUT = 'checked_out'
STATUS_LABELS = {STATUS_ABSENT: 'Absent', STATUS_INSIDE: 'Present, checked in', STATUS_OUT: 'Present, checked out'}


# --- helpers -----------------------------------------------------------------------------

def format_time(value):
    """A date and time for messages and screens, in local time."""
    return timezone.localtime(value).strftime('%d %b %Y, %I:%M %p') if value else ''


def format_duration(start, end):
    """'9 h 30 min' for a finished entry, or '' while it is still open."""
    if not start or not end:
        return ''
    minutes = int((end - start).total_seconds() // 60)
    return f'{minutes // 60} h {minutes % 60:02d} min'


def _when(value):
    """The time to record: now by default. It must not be in the future."""
    now = timezone.now()
    if value is None:
        return now
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    if value > now + timedelta(minutes=1):
        raise ValidationError(msg('future_time', field='Time'), code='future_time')
    return value


def _scope(account, queryset):
    """Staff work with their own hostel's students (every hostel if the account has none)."""
    if account is not None and account.hostel_id is not None:
        return queryset.filter(hostel_id=account.hostel_id)
    return queryset


def has_room(student):
    return Allocation.objects.filter(student=student, status=Allocation.STATUS_ACTIVE).exists()


def open_entry(student):
    """The entry the student is still checked in on, if any (it may be from an earlier day)."""
    return (AttendanceRecord.objects
            .filter(student=student, check_in_at__isnull=False, check_out_at__isnull=True)
            .order_by('-attendance_date', '-id').first())


# --- check-in and check-out (FR-07.01 to FR-07.05) ----------------------------------------

def check_in(student, by, when=None):
    """Record a check-in for a student who has a room and is not already checked in (UT_19_Att)."""
    when = _when(when)
    if not student.is_active:
        raise ValidationError(msg('student_inactive'), code='student_inactive')
    if not has_room(student):
        raise ValidationError(msg('no_room_for_attendance'), code='no_room')
    day = timezone.localtime(when).date()
    try:
        with transaction.atomic():
            existing = open_entry(student)
            if existing is not None:                                            # UT_21_Att
                raise ValidationError(
                    msg('duplicate_checkin', since=format_time(existing.check_in_at)), code='duplicate_checkin')
            if AttendanceRecord.objects.filter(student=student, attendance_date=day).exists():
                raise ValidationError(msg('attendance_day_complete', day=day.strftime('%d %b %Y')),
                                      code='day_complete')
            return AttendanceRecord.objects.create(
                student=student, hostel=student.hostel, attendance_date=day,
                check_in_at=when, recorded_by=by)
    except IntegrityError:
        # Someone else recorded this student a moment ago.
        raise ValidationError(msg('attendance_day_complete', day=day.strftime('%d %b %Y')),
                              code='day_complete') from None


def check_out(student, by, when=None):
    """Close the student's open check-in (UT_20_Att). Without one it is an error (ST_14_Att)."""
    when = _when(when)
    with transaction.atomic():
        entry = (AttendanceRecord.objects.select_for_update()
                 .filter(student=student, check_in_at__isnull=False, check_out_at__isnull=True)
                 .order_by('-attendance_date', '-id').first())
        if entry is None:
            finished_today = AttendanceRecord.objects.filter(
                student=student, attendance_date=timezone.localdate(), check_out_at__isnull=False).exists()
            key = 'already_checked_out' if finished_today else 'no_active_checkin'
            raise ValidationError(msg(key), code=key)
        if when < entry.check_in_at:
            raise ValidationError(
                msg('checkout_before_checkin', since=format_time(entry.check_in_at)), code='checkout_before_checkin')
        entry.check_out_at = when
        entry.save(update_fields=['check_out_at', 'updated_at'])
        return entry


# --- bulk marking (FR-07.06) ---------------------------------------------------------------

@dataclass
class BulkResult:
    done: list = field(default_factory=list)       # AttendanceRecord for each student that worked
    failed: list = field(default_factory=list)     # (Student, message) for each that did not


def bulk_mark(students, action, by, when=None):
    """Check several students in (or out) at the same time. Each one succeeds or fails on its own."""
    students = list(students)
    if action not in ACTIONS:
        raise ValidationError(msg('invalid_choice', field='Action'), code='invalid_choice')
    if not students:
        raise ValidationError(msg('select_students'), code='required')
    when = _when(when)                                      # one time for everyone: "simultaneously"
    operation = check_in if action == ACTION_CHECK_IN else check_out
    result = BulkResult()
    for student in students:
        try:
            with transaction.atomic():
                result.done.append(operation(student, by, when))
        except ValidationError as error:
            result.failed.append((student, ' '.join(error.messages)))
    return result


# --- viewing and reporting (FR-07.07 to FR-07.09) -------------------------------------------

def allocated_students(account):
    """Active students who currently have a room, in the account's hostel."""
    students = Student.objects.filter(
        is_active=True, allocations__status=Allocation.STATUS_ACTIVE).distinct().order_by('roll_no')
    return _scope(account, students)


def open_flags(account, today=None):
    """Entries still open from an earlier day: the student never checked out (FR-07.03)."""
    today = today or timezone.localdate()
    return list(_scope(account, AttendanceRecord.objects.filter(
        check_in_at__isnull=False, check_out_at__isnull=True, attendance_date__lt=today)
        .select_related('student')).order_by('attendance_date', 'student__roll_no'))


def daily_summary(account, day=None):
    """Present or absent for every student with a room on one day (IT_19_Att)."""
    day = day or timezone.localdate()
    students = list(allocated_students(account))
    records = _scope(account, AttendanceRecord.objects.filter(attendance_date=day).select_related('student'))
    by_student = {r.student_id: r for r in records}
    known = {s.pk for s in students}
    for record in records:                       # recorded that day but no longer in a room
        if record.student_id not in known:
            students.append(record.student)
            known.add(record.student_id)
    students.sort(key=lambda s: s.roll_no)
    open_entries = {}
    for entry in (AttendanceRecord.objects.filter(student__in=known, check_in_at__isnull=False,
                                                  check_out_at__isnull=True).order_by('attendance_date', 'id')):
        open_entries[entry.student_id] = entry
    rooms = {a.student_id: a.room.room_no for a in
             Allocation.objects.filter(student__in=known, status=Allocation.STATUS_ACTIVE).select_related('room')}

    rows, present = [], 0
    for student in students:
        record, entry = by_student.get(student.pk), open_entries.get(student.pk)
        if record is None:
            status = STATUS_ABSENT
        elif record.check_out_at is None:
            status = STATUS_INSIDE
        else:
            status = STATUS_OUT
        if status != STATUS_ABSENT:
            present += 1
        rows.append({
            'student': student, 'room': rooms.get(student.pk, ''), 'record': record, 'status': status,
            'status_label': STATUS_LABELS[status], 'open_entry': entry,
            'open_from_earlier': entry is not None and entry.attendance_date != day,
            'duration': format_duration(record.check_in_at, record.check_out_at) if record else '',
            'can_check_in': entry is None and record is None and student.pk in rooms,
            'can_check_out': entry is not None,
        })
    return {'day': day, 'rows': rows, 'present': present, 'absent': len(rows) - present, 'total': len(rows)}


def student_history(student, start=None, end=None):
    """One student's attendance entries, newest first (IT_21_Att)."""
    records = AttendanceRecord.objects.filter(student=student, check_in_at__isnull=False)
    if start is not None:
        records = records.filter(attendance_date__gte=start)
    if end is not None:
        records = records.filter(attendance_date__lte=end)
    return records.order_by('-attendance_date', '-id')


def attendance_report(account, start, end, student=None):
    """Entries between two dates (inclusive) and the days present per student (ST_13_Att)."""
    validate_date_range(start, end, 'Start date', 'End date')
    records = _scope(account, AttendanceRecord.objects.filter(
        attendance_date__gte=start, attendance_date__lte=end, check_in_at__isnull=False)
        .select_related('student')).order_by('-attendance_date', 'student__roll_no')
    if student is not None:
        records = records.filter(student=student)
    rows = list(records)
    for record in rows:
        record.duration = format_duration(record.check_in_at, record.check_out_at)
    days = {}
    for record in rows:
        entry = days.setdefault(record.student_id, {'student': record.student, 'days': 0})
        entry['days'] += 1
    return {'rows': rows, 'per_student': sorted(days.values(), key=lambda e: e['student'].roll_no),
            'total': len(rows)}

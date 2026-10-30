"""Room allocation business rules (FR-04, Issues #53-#65).

Views call these functions and never change Allocation rows themselves, so every rule
(capacity, one room per student, priority, notifications) lives in one place.

    vacant_rooms(student)                 FR-04.01  rooms with a free bed, best first
    allocate(student, room, by=...)       FR-04.02  allocate, honouring capacity + priority
    transfer(student, new_room, by=...)   FR-04.08  move a student between rooms
    vacate(allocation, by=...)            FR-04.13  release a room when a student leaves
    add_to_waitlist / waitlist            FR-04.05  queue of unallocated students
    allocation_report(...)                FR-04.11  history of allocations

Capacity safety (FR-04.12): allocate() and transfer() run in one transaction and lock the
room row (SELECT ... FOR UPDATE on PostgreSQL) before counting occupants, so two wardens
can never both take the last bed. SQLite serialises writers, so it is safe there too.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, F, Q
from django.utils import timezone

from core.error_messages import msg
from core.models import Allocation, AllocationRequest, AllocationRule, Room, Student
from core.notifications import notify


# --- priority rules (FR-04.03 / FR-04.04) ---------------------------------------------

def ensure_default_rules():
    """Make sure the built-in rules exist (safe to call any number of times)."""
    AllocationRule.objects.get_or_create(
        criterion=AllocationRule.CRITERION_SENIORITY,
        defaults={'weight': 1, 'is_active': True,
                  'description': 'Senior students (higher year of study) are served first'})


def get_rules():
    ensure_default_rules()
    return list(AllocationRule.objects.order_by('criterion'))


def priority_score(student):
    """Sum of weight x value over every active rule. Higher means served first."""
    score = 0
    for rule in get_rules():
        if rule.is_active and rule.criterion == AllocationRule.CRITERION_SENIORITY:
            score += rule.weight * (student.year_of_study or 0)
    return score


def recalculate_waitlist_priorities():
    """Re-score every waiting request after the rules changed. Returns how many."""
    requests = list(AllocationRequest.objects.filter(
        status=AllocationRequest.STATUS_WAITING).select_related('student'))
    for request in requests:
        request.priority = priority_score(request.student)
    AllocationRequest.objects.bulk_update(requests, ['priority'])
    return len(requests)


# --- queries ---------------------------------------------------------------------------

def current_allocation(student):
    """The student's active allocation, or None."""
    return (Allocation.objects.filter(student=student, status=Allocation.STATUS_ACTIVE)
            .select_related('room', 'room__hostel').first())


def roommates(student):
    """Other students currently in the same room as ``student``."""
    allocation = current_allocation(student)
    if allocation is None:
        return []
    return list(Student.objects.filter(
        allocations__room=allocation.room, allocations__status=Allocation.STATUS_ACTIVE,
    ).exclude(pk=student.pk).order_by('full_name'))


def vacant_rooms(student=None, *, hostel=None, exclude_room=None):
    """Active rooms with at least one free bed, in the student's hostel.

    Ordered by the allocation rules: a room of the type the student asked for comes first,
    then rooms that are already partly filled (so beds are used up before new rooms are
    opened), then block / room number. Each room gets ``occupied_beds`` and ``free_beds``.
    """
    hostel = hostel or (student.hostel if student is not None else None)
    rooms = (Room.objects.filter(is_active=True)
             .annotate(occupied_beds=Count(
                 'allocations', filter=Q(allocations__status=Allocation.STATUS_ACTIVE)))
             .filter(occupied_beds__lt=F('capacity')).select_related('hostel'))
    if hostel is not None:
        rooms = rooms.filter(hostel=hostel)
    if exclude_room is not None:
        rooms = rooms.exclude(pk=exclude_room.pk)
    rooms = list(rooms)
    wanted = ''
    if student is not None:
        request = (AllocationRequest.objects.filter(
            student=student, status=AllocationRequest.STATUS_WAITING).first())
        wanted = (request.requested_room_type if request else '').strip().lower()
    for room in rooms:
        room.free_beds = room.capacity - room.occupied_beds
    rooms.sort(key=lambda r: (
        0 if wanted and r.room_type.strip().lower() == wanted else 1,
        r.free_beds == r.capacity,   # partly filled rooms first
        r.block, r.room_no))
    return rooms


def total_vacancies(hostel):
    return sum(room.free_beds for room in vacant_rooms(hostel=hostel))


def waitlist(hostel=None):
    """Waiting requests, highest priority first, then first come first served."""
    requests = (AllocationRequest.objects.filter(status=AllocationRequest.STATUS_WAITING)
                .select_related('student', 'student__hostel')
                .order_by('-priority', 'requested_at', 'pk'))
    if hostel is not None:
        requests = requests.filter(student__hostel=hostel)
    return requests


def priority_conflicts(student):
    """Waiting students who outrank ``student`` and would be left without a bed.

    Empty when there are enough free beds for everyone with a higher score, so a junior
    student is only flagged when taking a bed would push a senior student out.
    """
    higher = list(waitlist(student.hostel).exclude(student=student)
                  .filter(priority__gt=priority_score(student)))
    if higher and len(higher) >= total_vacancies(student.hostel):
        return higher
    return []


# --- changes ---------------------------------------------------------------------------

def _require_active(student):
    if not student.is_active:
        raise ValidationError(msg('student_inactive'), code='student_inactive')


def _ensure_room_available(room, student):
    """Raise unless ``room`` is open, in the student's hostel and has a free bed.

    Call with the room row already locked. Says 'No vacant rooms available' when the
    whole hostel is full, otherwise 'Room unavailable' (UC-04 exception 5a).
    """
    occupied = Allocation.objects.filter(room=room, status=Allocation.STATUS_ACTIVE).count()
    if room.is_active and room.hostel_id == student.hostel_id and occupied < room.capacity:
        return
    if not vacant_rooms(student):
        raise ValidationError(msg('no_vacant_rooms'), code='no_vacant_rooms')
    raise ValidationError(msg('room_unavailable'), code='room_unavailable')


def _close_waiting_requests(student, by):
    AllocationRequest.objects.filter(
        student=student, status=AllocationRequest.STATUS_WAITING
    ).update(status=AllocationRequest.STATUS_APPROVED, processed_by=by,
             updated_at=timezone.now())


@transaction.atomic
def allocate(student, room, *, by, override_priority=False, today=None):
    """Allocate ``room`` to an unallocated student (UT_11, IT_10, IT_11, UT_12).

    Raises ValidationError with one of the codes: student_inactive, already_allocated
    (use transfer), room_unavailable, no_vacant_rooms, priority_conflict (a higher-priority
    student is waiting; pass override_priority=True to allocate anyway).
    """
    today = today or timezone.localdate()
    student = Student.objects.select_for_update().get(pk=student.pk)
    room = Room.objects.select_for_update().select_related('hostel').get(pk=room.pk)
    _require_active(student)
    if current_allocation(student) is not None:
        raise ValidationError(msg('already_allocated'), code='already_allocated')
    _ensure_room_available(room, student)
    if not override_priority and priority_conflicts(student):
        raise ValidationError(msg('priority_conflict'), code='priority_conflict')
    allocation = Allocation.objects.create(
        student=student, room=room, allocated_by=by, allocated_on=today)
    _close_waiting_requests(student, by)
    notify(student, 'ALLOCATION',
           f'You have been allocated room {room.room_no} ({room.hostel.name})')
    return allocation


@transaction.atomic
def transfer(student, new_room, *, by, today=None):
    """Move an allocated student to another room (IT_12). The old allocation is kept as
    history with status 'transferred'."""
    today = today or timezone.localdate()
    student = Student.objects.select_for_update().get(pk=student.pk)
    current = (Allocation.objects.select_for_update()
               .filter(student=student, status=Allocation.STATUS_ACTIVE)
               .select_related('room').first())
    if current is None:
        raise ValidationError(msg('not_allocated'), code='not_allocated')
    if current.room_id == new_room.pk:
        raise ValidationError(msg('same_room'), code='same_room')
    # Lock both rooms in a fixed order so two simultaneous transfers cannot deadlock.
    locked = {r.pk: r for r in Room.objects.select_for_update().select_related('hostel')
              .filter(pk__in=[current.room_id, new_room.pk]).order_by('pk')}
    new_room, old_room = locked[new_room.pk], locked[current.room_id]
    _ensure_room_available(new_room, student)
    current.status = Allocation.STATUS_TRANSFERRED
    current.ended_on = max(today, current.allocated_on)
    current.save(update_fields=['status', 'ended_on', 'updated_at'])
    allocation = Allocation.objects.create(
        student=student, room=new_room, allocated_by=by, allocated_on=today)
    notify(student, 'ALLOCATION',
           f'Your room has been changed from {old_room.room_no} to {new_room.room_no} '
           f'({new_room.hostel.name})')
    return allocation


@transaction.atomic
def vacate(allocation, *, by, today=None):
    """End an active allocation when a student leaves, freeing the bed."""
    today = today or timezone.localdate()
    allocation = (Allocation.objects.select_for_update().select_related('room', 'student')
                  .get(pk=allocation.pk))
    if allocation.status != Allocation.STATUS_ACTIVE:
        raise ValidationError(msg('not_allocated'), code='not_allocated')
    allocation.status = Allocation.STATUS_ENDED
    allocation.ended_on = max(today, allocation.allocated_on)
    allocation.save(update_fields=['status', 'ended_on', 'updated_at'])
    notify(allocation.student, 'ALLOCATION',
           f'Your allocation of room {allocation.room.room_no} has ended')
    return allocation


# --- waitlist (FR-04.05) --------------------------------------------------------------

@transaction.atomic
def add_to_waitlist(student, *, by, room_type=''):
    """Queue an unallocated student for a room."""
    student = Student.objects.select_for_update().get(pk=student.pk)
    _require_active(student)
    if current_allocation(student) is not None:
        raise ValidationError(msg('already_allocated'), code='already_allocated')
    if AllocationRequest.objects.filter(
            student=student, status=AllocationRequest.STATUS_WAITING).exists():
        raise ValidationError(msg('already_waiting'), code='already_waiting')
    return AllocationRequest.objects.create(
        student=student, preferred_hostel=student.hostel,
        requested_room_type=(room_type or '').strip(), priority=priority_score(student))


def remove_from_waitlist(request, *, by):
    """Cancel a waiting request. Returns False if it was no longer waiting."""
    updated = AllocationRequest.objects.filter(
        pk=request.pk, status=AllocationRequest.STATUS_WAITING
    ).update(status=AllocationRequest.STATUS_CANCELLED, processed_by=by,
             updated_at=timezone.now())
    return updated == 1


def unallocated_students(hostel=None):
    """Active students with no active allocation."""
    students = (Student.objects.filter(is_active=True)
                .exclude(allocations__status=Allocation.STATUS_ACTIVE).order_by('roll_no'))
    if hostel is not None:
        students = students.filter(hostel=hostel)
    return students


# --- report (FR-04.11) ----------------------------------------------------------------

def allocation_report(*, start=None, end=None, status=None):
    """Allocations that were in effect at any time between ``start`` and ``end``."""
    rows = (Allocation.objects
            .select_related('student', 'room', 'room__hostel', 'allocated_by__user')
            .order_by('-allocated_on', '-pk'))
    if end is not None:
        rows = rows.filter(allocated_on__lte=end)
    if start is not None:
        rows = rows.filter(Q(ended_on__isnull=True) | Q(ended_on__gte=start))
    if status:
        rows = rows.filter(status=status)
    return rows

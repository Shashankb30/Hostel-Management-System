"""Warden screens for Room Allocation (FR-04) and the student's My Room page."""
import csv

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from core.error_messages import msg
from core.feedback import flash_errors
from core.models import Allocation, AllocationRequest, Room, Student, UserAccount
from core.roles import get_account, role_required
from core.validators import validate_date_range

from . import services
from .forms import RuleFormSet

WARDEN_ONLY = role_required(UserAccount.ROLE_WARDEN)
STUDENT_ONLY = role_required(UserAccount.ROLE_STUDENT)


def _manage_url(student=None):
    url = reverse('allocation:manage')
    return f'{url}?student={student.pk}' if student is not None else url


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# --- allocate (FR-04.01, .02, .04, .06, .07, .10) -----------------------------------------

@WARDEN_ONLY
def manage(request):
    """Pick a student, see suggested vacant rooms, allocate (UT_10, UT_11)."""
    students = list(Student.objects.filter(is_active=True).order_by('roll_no'))
    rooms_by_student = {
        a.student_id: a.room for a in
        Allocation.objects.filter(status=Allocation.STATUS_ACTIVE).select_related('room')}
    for student in students:
        student.current_room = rooms_by_student.get(student.pk)

    selected = None
    pk = _int_or_none(request.GET.get('student'))
    if pk is not None:
        selected = next((s for s in students if s.pk == pk), None)

    context = {'students': students, 'selected': selected}
    if selected is not None:
        allocation = services.current_allocation(selected)
        context['allocation'] = allocation
        if allocation is not None:
            context['roommates'] = services.roommates(selected)
        else:
            context['vacant_rooms'] = services.vacant_rooms(selected)
            context['conflicts'] = services.priority_conflicts(selected)
            context['priority'] = services.priority_score(selected)
            context['waiting'] = AllocationRequest.objects.filter(
                student=selected, status=AllocationRequest.STATUS_WAITING).exists()
    return render(request, 'allocation/manage.html', context)


@WARDEN_ONLY
@require_POST
def allocate(request):
    student = get_object_or_404(Student, pk=_int_or_none(request.POST.get('student')) or 0)
    room = get_object_or_404(
        Room, pk=_int_or_none(request.POST.get('room')) or 0)
    try:
        services.allocate(
            student, room, by=get_account(request.user),
            override_priority=request.POST.get('override') == '1')
    except ValidationError as exc:
        if exc.code == 'already_allocated':
            # FR-04.07: a student who already has a room must be transferred instead.
            messages.warning(request, exc.messages[0])
            return redirect(f"{reverse('allocation:transfer', args=[student.pk])}?room={room.pk}")
        flash_errors(request, exc)  # for a full room this refreshes the list (UC-04 5a)
    else:
        messages.success(request, f'Room {room.room_no} allocated to {student.full_name}')
    return redirect(_manage_url(student))


# --- transfer (FR-04.08) -------------------------------------------------------------------

@WARDEN_ONLY
def transfer(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    allocation = services.current_allocation(student)
    if allocation is None:
        messages.error(request, msg('not_allocated'))
        return redirect(_manage_url(student))

    target = None
    room_pk = _int_or_none(request.POST.get('room') or request.GET.get('room'))
    if room_pk is not None:
        target = next((r for r in services.vacant_rooms(
            student, exclude_room=allocation.room) if r.pk == room_pk), None)
        if target is None:
            messages.error(request, msg('room_unavailable'))

    if request.method == 'POST' and target is not None:
        try:
            services.transfer(student, target, by=get_account(request.user))
        except ValidationError as exc:
            flash_errors(request, exc)
            return redirect(reverse('allocation:transfer', args=[student.pk]))
        messages.success(
            request, f'{student.full_name} moved from {allocation.room.room_no} '
                     f'to {target.room_no}')
        return redirect(_manage_url(student))

    return render(request, 'allocation/transfer.html', {
        'student': student, 'allocation': allocation, 'target': target,
        'vacant_rooms': services.vacant_rooms(student, exclude_room=allocation.room),
    })


@WARDEN_ONLY
@require_POST
def vacate(request, allocation_pk):
    allocation = get_object_or_404(Allocation.objects.select_related('student', 'room'),
                                   pk=allocation_pk)
    try:
        services.vacate(allocation, by=get_account(request.user))
    except ValidationError as exc:
        flash_errors(request, exc)
    else:
        messages.success(request, f'Room {allocation.room.room_no} released by '
                                  f'{allocation.student.full_name}')
    return redirect(_manage_url(allocation.student))


# --- waitlist (FR-04.05) -------------------------------------------------------------------

@WARDEN_ONLY
def waitlist(request):
    waiting_ids = AllocationRequest.objects.filter(
        status=AllocationRequest.STATUS_WAITING).values_list('student_id', flat=True)
    return render(request, 'allocation/waitlist.html', {
        'requests': services.waitlist(),
        'candidates': services.unallocated_students().exclude(pk__in=list(waiting_ids)),
    })


@WARDEN_ONLY
@require_POST
def waitlist_add(request):
    student = get_object_or_404(Student, pk=_int_or_none(request.POST.get('student')) or 0)
    try:
        services.add_to_waitlist(student, by=get_account(request.user),
                                 room_type=request.POST.get('room_type', ''))
    except ValidationError as exc:
        flash_errors(request, exc)
    else:
        messages.success(request, f'{student.full_name} added to the waitlist')
    return redirect('allocation:waitlist')


@WARDEN_ONLY
@require_POST
def waitlist_remove(request, pk):
    item = get_object_or_404(AllocationRequest.objects.select_related('student'), pk=pk)
    if services.remove_from_waitlist(item, by=get_account(request.user)):
        messages.success(request, f'{item.student.full_name} removed from the waitlist')
    else:
        messages.error(request, 'This request is no longer waiting')
    return redirect('allocation:waitlist')


# --- priority rules (FR-04.03) -------------------------------------------------------------

@WARDEN_ONLY
def rules(request):
    services.ensure_default_rules()
    formset = RuleFormSet(request.POST or None)
    if request.method == 'POST' and formset.is_valid():
        formset.save()
        count = services.recalculate_waitlist_priorities()
        messages.success(request, f'Priority rules saved; {count} waiting request(s) re-ordered')
        return redirect('allocation:rules')
    return render(request, 'allocation/rules.html', {'formset': formset})


# --- report (FR-04.11) ---------------------------------------------------------------------

def _csv_safe(value):
    """Stop spreadsheet programs from running a cell that starts like a formula."""
    text = '' if value is None else str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@') else text


@WARDEN_ONLY
def report(request):
    start = parse_date(request.GET.get('start', '') or '')
    end = parse_date(request.GET.get('end', '') or '')
    status = request.GET.get('status', '')
    if status not in {value for value, _label in Allocation.STATUS_CHOICES}:
        status = ''
    rows = None
    try:
        validate_date_range(start, end, 'Start date', 'End date')
    except ValidationError as exc:
        flash_errors(request, exc)
    else:
        rows = services.allocation_report(start=start, end=end, status=status)

    if rows is not None and request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="allocation-report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Roll no', 'Student', 'Hostel', 'Room', 'Allocated on', 'Ended on',
                         'Status', 'Allocated by'])
        for row in rows:
            writer.writerow([_csv_safe(v) for v in (
                row.student.roll_no, row.student.full_name, row.room.hostel.name,
                row.room.room_no, row.allocated_on, row.ended_on or '',
                row.get_status_display(),
                row.allocated_by.user.get_username() if row.allocated_by else '')])
        return response

    return render(request, 'allocation/report.html', {
        'rows': rows, 'start': start, 'end': end, 'status': status,
        'statuses': Allocation.STATUS_CHOICES,
    })


# --- student: My Room (FR-03.08) ---------------------------------------------------------

@STUDENT_ONLY
def my_room(request):
    """My Room: the student's own room, read live from the room record."""
    student = Student.objects.filter(user_account=get_account(request.user)).first()
    allocation, roommates = None, 0
    if student is not None:
        allocation = (Allocation.objects.select_related('room__hostel')
                      .filter(student=student, status=Allocation.STATUS_ACTIVE).first())
    if allocation is not None:
        roommates = (Allocation.objects
                     .filter(room=allocation.room, status=Allocation.STATUS_ACTIVE)
                     .exclude(pk=allocation.pk).count())
    return render(request, 'allocation/my_room.html', {
        'student': student, 'allocation': allocation,
        'room': allocation.room if allocation else None, 'roommates': roommates,
    })

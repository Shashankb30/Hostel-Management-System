"""Room Management screens (FR-03)."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.error_messages import msg
from core.feedback import flash_errors
from core.models import Room, UserAccount
from core.roles import get_account, get_role, role_required

from . import services
from . import selectors
from .forms import ROOM_TYPE_SUGGESTIONS, RoomForm

ADMIN_ONLY = role_required(UserAccount.ROLE_ADMIN)
STAFF = role_required(UserAccount.ROLE_ADMIN, UserAccount.ROLE_WARDEN)


def _visible_rooms(request):
    """Rooms this user may see: administrators see all, a warden sees their own hostel."""
    rooms = Room.objects.select_related('hostel')
    account = get_account(request.user)
    if account and account.role == UserAccount.ROLE_WARDEN and account.hostel_id:
        rooms = rooms.filter(hostel_id=account.hostel_id)
    return rooms.order_by('hostel__name', 'room_no')


def _room_list(request, *, manage):
    rooms = _visible_rooms(request)
    annotated = selectors.with_occupancy(rooms)
    vacancy = request.GET.get('vacancy', selectors.VACANCY_ALL)
    annotated = selectors.filter_by_vacancy(annotated, vacancy)
    context = {'rows': selectors.build_rows(annotated)}
    context.update(vacancy=vacancy, vacancy_choices=selectors.VACANCY_CHOICES)
    context.update(manage=manage)
    return render(request, 'rooms/room_list.html', context)


@ADMIN_ONLY
def room_manage(request):
    """Room Management: every room, with the Add Room button."""
    return _room_list(request, manage=True)


@STAFF
def room_vacancy(request):
    """Rooms & Vacancy: the warden's view of rooms and availability."""
    return _room_list(request, manage=False)


@ADMIN_ONLY
def room_add(request):
    """Add Room."""
    account = get_account(request.user)
    form = RoomForm(request.POST or None, initial={'hostel': account.hostel_id if account else None})
    if request.method == 'POST' and form.is_valid():
        try:
            room = services.create_room(**form.cleaned_data)
        except IntegrityError:
            # Another administrator added the same room number a moment ago.
            form.add_error('room_no', msg('unique', field='Room number'))
        else:
            messages.success(
                request, f'Room {room.room_no} added. Status: Vacant, capacity {room.capacity}')
            return redirect('rooms:manage')
    return _room_form(request, form, 'Add Room')


@ADMIN_ONLY
def room_edit(request, pk):
    """Edit Room: number, capacity, type, block and floor."""
    room = get_object_or_404(Room.objects.select_related('hostel'), pk=pk)
    form = RoomForm(request.POST or None, room=room)
    if request.method == 'POST' and form.is_valid():
        data = {key: value for key, value in form.cleaned_data.items() if key != 'hostel'}
        try:
            services.update_room(room, **data)
        except IntegrityError:
            form.add_error('room_no', msg('unique', field='Room number'))
        else:
            messages.success(request, f'Room {room.room_no} updated')
            return redirect('rooms:manage')
    return _room_form(request, form, f'Edit room {room.room_no}')


def _room_form(request, form, title):
    return render(request, 'rooms/room_form.html', {
        'form': form, 'title': title, 'type_suggestions': ROOM_TYPE_SUGGESTIONS})


def _home(request):
    """Where to go after an action: the warden's page for wardens, otherwise Room Management."""
    return 'rooms:vacancy' if get_role(request.user) == UserAccount.ROLE_WARDEN else 'rooms:manage'


def _room_action(request, pk, action, done):
    room = get_object_or_404(_visible_rooms(request), pk=pk)
    try:
        action(room)
    except ValidationError as error:
        flash_errors(request, error)
    else:
        messages.success(request, f'Room {room.room_no} {done}')
    return redirect(_home(request))


@ADMIN_ONLY
@require_POST
def room_delete(request, pk):
    return _room_action(request, pk, services.delete_room, 'deleted')


@STAFF
@require_POST
def room_deactivate(request, pk):
    return _room_action(
        request, pk, lambda room: services.set_available(room, False), 'is now unavailable')


@STAFF
@require_POST
def room_reactivate(request, pk):
    return _room_action(
        request, pk, lambda room: services.set_available(room, True), 'is available again')

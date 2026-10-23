"""Room rules (FR-03). Business rules live here, not in the views."""
from django.core.exceptions import ValidationError

from core.error_messages import msg
from core.models import Room


def create_room(*, hostel, room_no, room_type, capacity, block='', floor=None):
    """Add a room. A new room has nobody in it, so it starts out Vacant."""
    return Room.objects.create(
        hostel=hostel, room_no=room_no, room_type=room_type, capacity=capacity,
        block=block, floor=floor or 0)


def update_room(room, *, room_no, room_type, capacity, block='', floor=None):
    """Change a room's number, type, capacity, block or floor."""
    room.room_no, room.room_type, room.capacity = room_no, room_type, capacity
    room.block, room.floor = block, floor or 0
    room.save()
    return room


def delete_room(room):
    """Delete a room nobody has ever lived in.

    A room with people in it must have them reassigned first. A room that only has
    history (past allocations) is kept for the records and can be deactivated instead.
    """
    if room.occupancy:
        raise ValidationError(msg('room_has_occupants'), code='room_has_occupants')
    if room.allocations.exists():
        raise ValidationError(msg('room_has_history'), code='room_has_history')
    room.delete()


def set_available(room, available):
    """Make a room available (active) or unavailable. Occupied rooms cannot be switched off."""
    if not available and room.occupancy:
        raise ValidationError(
            msg('room_has_occupants_unavailable'), code='room_has_occupants_unavailable')
    room.is_active = available
    room.save(update_fields=['is_active', 'updated_at'])


def check_capacity(room, capacity):
    """Capacity may not drop below the number of students currently in the room."""
    occupied = room.occupancy
    if capacity < occupied:
        raise ValidationError(
            msg('capacity_below_occupancy', occupied=occupied), code='capacity_below_occupancy')

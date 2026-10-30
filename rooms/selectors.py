"""Read-only room queries: occupancy, vacancy status and allocation candidates (FR-03)."""
from dataclasses import dataclass

from django.db.models import Count, F, Q

from core.models import Allocation, Room

STATUS_VACANT, STATUS_PARTIAL, STATUS_FULL = 'vacant', 'partial', 'full'
STATUS_LABELS = {
    STATUS_VACANT: 'Vacant',
    STATUS_PARTIAL: 'Partially occupied',
    STATUS_FULL: 'Full',
}


def with_occupancy(queryset):
    """Add ``occupied`` (students living in the room now) to every room in one query.

    Only active allocations count, so transferring or vacating frees the bed at once.
    """
    return queryset.annotate(
        occupied=Count('allocations', filter=Q(allocations__status=Allocation.STATUS_ACTIVE)))


@dataclass(frozen=True)
class RoomRow:
    """One line of the room list: the room plus the numbers derived from its allocations."""

    room: Room
    occupied: int

    @property
    def free(self):
        return max(self.room.capacity - self.occupied, 0)

    @property
    def status(self):
        if self.occupied <= 0:
            return STATUS_VACANT
        return STATUS_FULL if self.occupied >= self.room.capacity else STATUS_PARTIAL

    @property
    def status_label(self):
        return STATUS_LABELS[self.status]


def build_rows(queryset):
    return [RoomRow(room=room, occupied=room.occupied) for room in queryset]


def open_for_allocation(hostel=None):
    """Rooms a student can be allocated to: active, with at least one free bed.

    Fully occupied and deactivated rooms are left out, so they cannot be picked (FR-03.06).
    The allocation screens (FR-04) build their vacant-room lists from this.
    """
    rooms = Room.objects.filter(is_active=True).select_related('hostel')
    if hostel is not None:
        rooms = rooms.filter(hostel=hostel)
    return (with_occupancy(rooms).filter(occupied__lt=F('capacity'))
            .order_by('hostel__name', 'room_no'))

VACANCY_ALL, VACANCY_AVAILABLE, VACANCY_FULL = 'all', 'available', 'full'
VACANCY_CHOICES = [
    (VACANCY_ALL, 'All rooms'),
    (VACANCY_AVAILABLE, 'Vacant only (free beds)'),
    (VACANCY_FULL, 'Full rooms'),
]


def filter_by_vacancy(annotated_rooms, value):
    """Narrow rooms already passed through with_occupancy(). Unknown values show everything."""
    if value == VACANCY_AVAILABLE:
        return annotated_rooms.filter(is_active=True, occupied__lt=F('capacity'))
    if value == VACANCY_FULL:
        return annotated_rooms.filter(occupied__gte=F('capacity'))
    return annotated_rooms

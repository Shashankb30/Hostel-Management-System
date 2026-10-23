"""Issue #45 (FR-03.06): full rooms are left out of allocation lists."""
from django.test import TestCase

from core.models import Allocation, Hostel, Room
from core.seed import seed
from rooms import selectors
from rooms.testing import allocate, fill_room, make_student


class OpenForAllocationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def numbers(self, **kwargs):
        return [room.room_no for room in selectors.open_for_allocation(**kwargs)]

    def test_IT_08_Room__a_room_at_full_capacity_is_not_offered(self):
        fill_room(Room.objects.get(room_no='A-101'), 3)
        self.assertNotIn('A-101', self.numbers())

    def test_IT_08_Room__rooms_with_free_beds_are_offered(self):
        fill_room(Room.objects.get(room_no='A-101'), 3)
        fill_room(Room.objects.get(room_no='B-204'), 1)
        self.assertEqual(self.numbers(), ['B-204', 'C-102'])

    def test_IT_08_Room__every_room_is_offered_when_nobody_is_allocated(self):
        self.assertEqual(self.numbers(), ['A-101', 'B-204', 'C-102'])

    def test_IT_08_Room__a_room_that_has_just_filled_up_disappears(self):
        room = Room.objects.get(room_no='B-204')  # capacity 2
        fill_room(room, 1)
        self.assertIn('B-204', self.numbers())
        allocate(make_student('LAST01', self.hostel), room)
        self.assertNotIn('B-204', self.numbers())

    def test_IT_08_Room__a_bed_freed_by_a_transfer_or_vacating_makes_the_room_offered_again(self):
        room = Room.objects.get(room_no='B-204')
        first, second = fill_room(room, 2)
        self.assertNotIn('B-204', self.numbers())
        Allocation.objects.filter(student=first).update(
            status=Allocation.STATUS_ENDED, ended_on=first.allocations.first().allocated_on)
        self.assertIn('B-204', self.numbers())
        self.assertEqual(second.allocations.filter(status='active').count(), 1)

    def test_IT_08_Room__deactivated_rooms_are_not_offered(self):
        Room.objects.filter(room_no='C-102').update(is_active=False)
        self.assertNotIn('C-102', self.numbers())

    def test_IT_08_Room__can_be_limited_to_one_hostel(self):
        other = Hostel.objects.create(name='Annexe', code='ANX')
        Room.objects.create(hostel=other, room_no='X-1', room_type='Single', capacity=1)
        self.assertEqual(self.numbers(hostel=other), ['X-1'])
        self.assertNotIn('X-1', self.numbers(hostel=self.hostel))

    def test_IT_08_Room__each_result_carries_its_occupancy(self):
        fill_room(Room.objects.get(room_no='A-101'), 2)
        rooms = {room.room_no: room.occupied for room in selectors.open_for_allocation()}
        self.assertEqual(rooms['A-101'], 2)
        self.assertEqual(rooms['B-204'], 0)

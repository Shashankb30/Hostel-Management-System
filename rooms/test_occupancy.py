"""Issue #44 (FR-03.05): occupancy and vacancy status follow the allocations."""
from datetime import date

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.models import Allocation, Hostel, Room
from core.seed import seed
from rooms.testing import allocate, fill_room, make_student


class OccupancyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        self.room = Room.objects.get(room_no='A-101')  # capacity 3

    def row(self, room_no='A-101'):
        response = self.client.get(reverse('rooms:manage'))
        return {r.room.room_no: r for r in response.context['rows']}[room_no], response

    def test_IT_07_Room__empty_room_is_vacant(self):
        row, response = self.row()
        self.assertEqual((row.occupied, row.free, row.status), (0, 3, 'vacant'))
        self.assertContains(response, '0 / 3')

    def test_IT_07_Room__one_of_three_beds_taken_shows_two_vacant(self):
        fill_room(self.room, 1)
        row, response = self.row()
        self.assertEqual((row.occupied, row.free, row.status_label), (1, 2, 'Partially occupied'))
        self.assertContains(response, '1 / 3')
        self.assertContains(response, '2 vacant')

    def test_IT_07_Room__allocating_one_more_student_updates_the_numbers(self):
        fill_room(self.room, 1)
        before, _ = self.row()
        allocate(make_student('NEW001', self.hostel), self.room)
        after, _ = self.row()
        self.assertEqual((before.occupied, before.free), (1, 2))
        self.assertEqual((after.occupied, after.free), (2, 1))

    def test_IT_07_Room__a_full_room_shows_zero_vacant_and_full(self):
        fill_room(self.room, 3)
        row, response = self.row()
        self.assertEqual((row.occupied, row.free, row.status), (3, 0, 'full'))
        self.assertContains(response, '3 / 3')
        self.assertContains(response, '0 vacant')

    def test_IT_07_Room__a_transfer_frees_the_bed_in_the_old_room(self):
        students = fill_room(self.room, 2)
        Allocation.objects.filter(student=students[0]).update(
            status=Allocation.STATUS_TRANSFERRED, ended_on=date.today())
        allocate(students[0], Room.objects.get(room_no='B-204'))
        old, _ = self.row('A-101')
        new, _ = self.row('B-204')
        self.assertEqual(old.occupied, 1)
        self.assertEqual(new.occupied, 1)

    def test_IT_07_Room__vacating_frees_the_bed(self):
        students = fill_room(self.room, 2)
        Allocation.objects.filter(student=students[1]).update(
            status=Allocation.STATUS_ENDED, ended_on=date.today())
        row, _ = self.row()
        self.assertEqual((row.occupied, row.free), (1, 2))

    def test_IT_07_Room__status_is_derived_not_stored(self):
        self.assertFalse(hasattr(Room, 'status'))
        self.assertNotIn('status', {field.name for field in Room._meta.get_fields()})

    def test_IT_07_Room__list_needs_the_same_number_of_queries_however_many_rooms_there_are(self):
        def count_queries():
            with CaptureQueriesContext(connection) as queries:
                self.client.get(reverse('rooms:manage'))
            return len(queries)

        few = count_queries()
        for number in range(5):
            room = Room.objects.create(
                hostel=self.hostel, room_no=f'Z-{number}', room_type='Double', capacity=2)
            fill_room(room, 1, prefix=f'Q{number}')
        self.assertEqual(count_queries(), few)

"""Issue #48 (FR-03.09): filter rooms by vacancy status."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Room
from core.seed import seed
from rooms.testing import fill_room


class VacancyFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')
        fill_room(Room.objects.get(room_no='A-101'), 3)   # full
        fill_room(Room.objects.get(room_no='B-204'), 1)   # partly occupied, 1 free
        # C-102 stays empty
        cls.unavailable = Room.objects.create(
            hostel=cls.hostel, room_no='U-1', room_type='Single', capacity=1, is_active=False)

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))

    def shown(self, **params):
        response = self.client.get(reverse('rooms:manage'), params)
        self.assertEqual(response.status_code, 200)
        return sorted(row.room.room_no for row in response.context['rows'])

    def test_ST_05_Room__all_rooms_are_shown_by_default(self):
        self.assertEqual(self.shown(), ['A-101', 'B-204', 'C-102', 'U-1'])
        self.assertEqual(self.shown(vacancy='all'), ['A-101', 'B-204', 'C-102', 'U-1'])

    def test_ST_05_Room__vacant_only_shows_rooms_with_free_beds(self):
        self.assertEqual(self.shown(vacancy='available'), ['B-204', 'C-102'])

    def test_ST_05_Room__vacant_only_leaves_out_full_and_unavailable_rooms(self):
        rooms = self.shown(vacancy='available')
        self.assertNotIn('A-101', rooms)
        self.assertNotIn('U-1', rooms)

    def test_ST_05_Room__full_rooms_filter(self):
        self.assertEqual(self.shown(vacancy='full'), ['A-101'])

    def test_ST_05_Room__an_unknown_filter_value_shows_everything(self):
        self.assertEqual(self.shown(vacancy='nonsense'), ['A-101', 'B-204', 'C-102', 'U-1'])

    def test_ST_05_Room__the_filter_form_shows_the_current_choice(self):
        response = self.client.get(reverse('rooms:manage'), {'vacancy': 'available'})
        self.assertContains(response, 'Vacant only')
        self.assertContains(response, 'value="available" selected')

    def test_ST_05_Room__filtered_rows_keep_correct_occupancy(self):
        response = self.client.get(reverse('rooms:manage'), {'vacancy': 'available'})
        rows = {row.room.room_no: row for row in response.context['rows']}
        self.assertEqual((rows['B-204'].occupied, rows['B-204'].free), (1, 1))
        self.assertEqual((rows['C-102'].occupied, rows['C-102'].free), (0, 2))

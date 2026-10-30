"""Issue #49 (FR-03.10): no deleting occupied rooms; deactivate unoccupied rooms."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Allocation, Hostel, Room
from core.seed import seed
from rooms import selectors
from rooms.testing import allocate, fill_room, make_student


class DeleteRoomTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        self.occupied = Room.objects.get(room_no='A-101')
        self.empty = Room.objects.create(hostel=self.hostel, room_no='N-1', room_type='Single', capacity=1)

    def post(self, action, room):
        return self.client.post(reverse(f'rooms:{action}', args=[room.pk]), follow=True)

    # --- delete ------------------------------------------------------------------
    def test_ST_06_Room__a_room_with_occupants_cannot_be_deleted(self):
        fill_room(self.occupied, 2)
        response = self.post('delete', self.occupied)
        self.assertContains(response, 'Room has occupants; reassign them before deleting the room')
        self.assertTrue(Room.objects.filter(pk=self.occupied.pk).exists())

    def test_ST_06_Room__a_room_nobody_has_lived_in_can_be_deleted(self):
        response = self.post('delete', self.empty)
        self.assertContains(response, 'Room N-1 deleted')
        self.assertFalse(Room.objects.filter(pk=self.empty.pk).exists())

    def test_ST_06_Room__a_room_with_only_past_residents_is_kept_for_the_records(self):
        student = make_student('OLD001', self.hostel)
        allocate(student, self.empty, status=Allocation.STATUS_ENDED)
        response = self.post('delete', self.empty)
        self.assertContains(response, 'Room has allocation history')
        self.assertTrue(Room.objects.filter(pk=self.empty.pk).exists())

    def test_ST_06_Room__delete_needs_post(self):
        self.assertEqual(
            self.client.get(reverse('rooms:delete', args=[self.empty.pk])).status_code, 405)
        self.assertTrue(Room.objects.filter(pk=self.empty.pk).exists())

    def test_ST_06_Room__unknown_room_is_a_404(self):
        self.assertEqual(self.client.post(reverse('rooms:delete', args=[99999])).status_code, 404)

    # --- make unavailable / available -------------------------------------------
    def test_IT_ROOM_14__an_unoccupied_room_can_be_made_unavailable(self):
        response = self.post('deactivate', self.empty)
        self.assertContains(response, 'Room N-1 is now unavailable')
        self.empty.refresh_from_db()
        self.assertFalse(self.empty.is_active)

    def test_IT_ROOM_14__an_unavailable_room_is_not_offered_for_allocation(self):
        self.assertIn('N-1', [r.room_no for r in selectors.open_for_allocation()])
        self.post('deactivate', self.empty)
        self.assertNotIn('N-1', [r.room_no for r in selectors.open_for_allocation()])

    def test_IT_ROOM_14__an_occupied_room_cannot_be_made_unavailable(self):
        fill_room(self.occupied, 1)
        response = self.post('deactivate', self.occupied)
        self.assertContains(response, 'Room has occupants; reassign them before making the room unavailable')
        self.occupied.refresh_from_db()
        self.assertTrue(self.occupied.is_active)

    def test_IT_ROOM_14__a_room_can_be_made_available_again(self):
        self.post('deactivate', self.empty)
        response = self.post('reactivate', self.empty)
        self.assertContains(response, 'Room N-1 is available again')
        self.empty.refresh_from_db()
        self.assertTrue(self.empty.is_active)

    def test_IT_ROOM_14__the_list_shows_availability_and_the_action_buttons(self):
        response = self.client.get(reverse('rooms:manage'))
        self.assertContains(response, 'Make unavailable')
        self.assertContains(response, 'Delete')
        self.post('deactivate', self.empty)
        listing = self.client.get(reverse('rooms:manage'))
        self.assertContains(listing, 'Unavailable')
        self.assertContains(listing, 'Make available')

    def test_IT_ROOM_14__state_changes_need_post(self):
        for action in ('deactivate', 'reactivate'):
            with self.subTest(action=action):
                self.assertEqual(
                    self.client.get(reverse(f'rooms:{action}', args=[self.empty.pk])).status_code, 405)

    def test_IT_ROOM_14__students_cannot_change_rooms(self):
        self.client.force_login(get_user_model().objects.get(username='stu1023'))
        for action in ('delete', 'deactivate', 'reactivate'):
            with self.subTest(action=action):
                response = self.client.post(reverse(f'rooms:{action}', args=[self.empty.pk]))
                self.assertEqual(response.status_code, 403)
        self.assertTrue(Room.objects.get(pk=self.empty.pk).is_active)

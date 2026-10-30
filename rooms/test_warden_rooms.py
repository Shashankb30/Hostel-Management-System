"""Issue #50 (FR-03.11): a warden views rooms and updates their availability."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Room
from core.seed import seed
from rooms.testing import fill_room


class WardenRoomTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')
        cls.annexe = Hostel.objects.create(name='Annexe', code='ANX')
        cls.far_room = Room.objects.create(hostel=cls.annexe, room_no='X-1', room_type='Single', capacity=1)

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='wdn05'))
        self.room = Room.objects.get(room_no='C-102')

    def test_UT_ROOM_10__warden_menu_has_a_working_rooms_and_vacancy_link(self):
        response = self.client.get(reverse('core:dashboard_warden'))
        links = {item['label']: item['url'] for item in response.context['nav_items']}
        self.assertEqual(links['Rooms & Vacancy'], reverse('rooms:vacancy'))

    def test_UT_ROOM_10__warden_sees_rooms_with_occupancy_and_vacancy(self):
        fill_room(Room.objects.get(room_no='A-101'), 1)
        response = self.client.get(reverse('rooms:vacancy'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rooms &amp; Vacancy')
        rows = {row.room.room_no: row for row in response.context['rows']}
        self.assertEqual((rows['A-101'].occupied, rows['A-101'].free), (1, 2))

    def test_UT_ROOM_10__warden_can_filter_by_vacancy(self):
        fill_room(Room.objects.get(room_no='B-204'), 2)  # full
        response = self.client.get(reverse('rooms:vacancy'), {'vacancy': 'available'})
        shown = sorted(row.room.room_no for row in response.context['rows'])
        self.assertEqual(shown, ['A-101', 'C-102'])

    def test_UT_ROOM_10__warden_only_sees_rooms_of_their_own_hostel(self):
        response = self.client.get(reverse('rooms:vacancy'))
        shown = {row.room.room_no for row in response.context['rows']}
        self.assertNotIn('X-1', shown)
        self.assertEqual(shown, {'A-101', 'B-204', 'C-102'})

    def test_UT_ROOM_10__administrator_sees_every_hostel_on_the_same_page(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        response = self.client.get(reverse('rooms:vacancy'))
        self.assertIn('X-1', {row.room.room_no for row in response.context['rows']})

    def test_UT_ROOM_10__warden_can_make_a_room_unavailable_and_available_again(self):
        response = self.client.post(reverse('rooms:deactivate', args=[self.room.pk]), follow=True)
        self.assertRedirects(response, reverse('rooms:vacancy'))
        self.assertContains(response, 'Room C-102 is now unavailable')
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_active)
        self.client.post(reverse('rooms:reactivate', args=[self.room.pk]))
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_active)

    def test_UT_ROOM_10__same_rule_as_administrator_occupied_rooms_cannot_be_switched_off(self):
        fill_room(self.room, 1)
        response = self.client.post(reverse('rooms:deactivate', args=[self.room.pk]), follow=True)
        self.assertContains(response, 'reassign them before making the room unavailable')
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_active)

    def test_UT_ROOM_10__warden_cannot_change_a_room_of_another_hostel(self):
        response = self.client.post(reverse('rooms:deactivate', args=[self.far_room.pk]))
        self.assertEqual(response.status_code, 404)
        self.far_room.refresh_from_db()
        self.assertTrue(self.far_room.is_active)

    def test_UT_ROOM_10__warden_page_has_availability_buttons_but_no_add_or_delete(self):
        response = self.client.get(reverse('rooms:vacancy'))
        self.assertContains(response, 'Make unavailable')
        self.assertNotContains(response, reverse('rooms:add'))
        self.assertNotContains(response, 'Delete')
        self.assertNotContains(response, '/edit/')

    def test_UT_ROOM_10__warden_cannot_add_edit_or_delete_rooms(self):
        self.assertEqual(self.client.get(reverse('rooms:manage')).status_code, 403)
        self.assertEqual(self.client.get(reverse('rooms:add')).status_code, 403)
        self.assertEqual(self.client.get(reverse('rooms:edit', args=[self.room.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('rooms:delete', args=[self.room.pk])).status_code, 403)
        self.assertTrue(Room.objects.filter(pk=self.room.pk).exists())

    def test_UT_ROOM_10__students_cannot_open_the_vacancy_page(self):
        self.client.force_login(get_user_model().objects.get(username='stu1023'))
        self.assertEqual(self.client.get(reverse('rooms:vacancy')).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('rooms:vacancy')).status_code, 302)

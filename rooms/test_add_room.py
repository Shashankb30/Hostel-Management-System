"""Issue #40 (FR-03.01): add a room with number, capacity and type."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Room
from core.seed import seed


class AddRoomTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))

    def data(self, **overrides):
        data = {'hostel': self.hostel.pk, 'room_no': 'D-301', 'block': 'D', 'floor': '3',
                'room_type': 'Triple', 'capacity': '3'}
        data.update(overrides)
        return data

    def add(self, **overrides):
        return self.client.post(reverse('rooms:add'), self.data(**overrides))

    def test_UT_07_Room__room_management_lists_rooms_and_has_an_add_room_button(self):
        response = self.client.get(reverse('rooms:manage'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room Management')
        self.assertContains(response, 'Add Room')
        self.assertContains(response, reverse('rooms:add'))
        self.assertContains(response, 'A-101')

    def test_UT_07_Room__add_form_asks_for_room_number_capacity_and_type(self):
        response = self.client.get(reverse('rooms:add'))
        self.assertEqual(response.status_code, 200)
        for label in ('Room No.', 'Capacity', 'Type'):
            with self.subTest(label=label):
                self.assertContains(response, f'>{label}')
        for field in ('room_no', 'capacity', 'room_type', 'hostel', 'block', 'floor'):
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')

    def test_UT_07_Room__valid_room_is_saved(self):
        response = self.add()
        self.assertRedirects(response, reverse('rooms:manage'))
        room = Room.objects.get(room_no='D-301')
        self.assertEqual((room.capacity, room.room_type, room.block, room.floor), (3, 'Triple', 'D', 3))
        self.assertEqual(room.hostel, self.hostel)
        self.assertTrue(room.is_active)

    def test_UT_07_Room__new_room_is_vacant(self):
        response = self.add(room_no='A-102', block='A', floor='1')
        self.assertRedirects(response, reverse('rooms:manage'))
        listing = self.client.get(reverse('rooms:manage'))
        self.assertContains(listing, 'A-102')
        self.assertContains(listing, 'Vacant')

    def test_UT_07_Room__success_message_names_the_room_and_its_status(self):
        response = self.client.post(reverse('rooms:add'), self.data(), follow=True)
        self.assertContains(response, 'Room D-301 added')
        self.assertContains(response, 'Vacant')

    def test_UT_07_Room__block_and_floor_are_optional(self):
        self.add(room_no='E-1', block='', floor='')
        room = Room.objects.get(room_no='E-1')
        self.assertEqual((room.block, room.floor), ('', 0))

    def test_UT_07_Room__administrators_hostel_is_preselected(self):
        response = self.client.get(reverse('rooms:add'))
        self.assertEqual(response.context['form'].initial['hostel'], self.hostel.pk)

    def test_UT_07_Room__required_fields_are_reported_together(self):
        response = self.add(room_no='', room_type='', capacity='', hostel='')
        self.assertEqual(response.status_code, 200)
        for message in ('Room number is required', 'Room type is required',
                        'Capacity is required', 'Hostel is required'):
            with self.subTest(message=message):
                self.assertContains(response, message)
        self.assertFalse(Room.objects.filter(room_no='').exists())

    def test_UT_07_Room__room_number_must_not_contain_spaces(self):
        response = self.add(room_no='D 301')
        self.assertContains(response, 'Room number format is invalid')
        self.assertFalse(Room.objects.filter(block='D').exists())

    def test_UT_07_Room__floor_must_be_a_whole_number_in_range(self):
        for value, message in (('abc', 'Floor must be a whole number'), ('101', 'Floor must be at most 100')):
            with self.subTest(value=value):
                self.assertContains(self.add(floor=value), message)

    def test_UT_07_Room__rooms_menu_item_is_a_working_link(self):
        response = self.client.get(reverse('core:dashboard_admin'))
        links = {item['label']: item['url'] for item in response.context['nav_items']}
        self.assertEqual(links['Rooms'], reverse('rooms:manage'))

    def test_UT_07_Room__only_administrators_can_add_rooms(self):
        for username in ('wdn05', 'stu1023'):
            self.client.force_login(get_user_model().objects.get(username=username))
            for name in ('rooms:manage', 'rooms:add'):
                with self.subTest(username=username, url=name):
                    self.assertEqual(self.client.get(reverse(name)).status_code, 403)
            self.assertEqual(self.add().status_code, 403)
        self.assertFalse(Room.objects.filter(room_no='D-301').exists())

"""Issue #43 (FR-03.04): edit room details."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Room
from core.seed import seed


class EditRoomTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        self.room = Room.objects.get(room_no='A-101')
        self.url = reverse('rooms:edit', args=[self.room.pk])

    def data(self, **overrides):
        data = {'hostel': self.hostel.pk, 'room_no': 'A-101', 'block': 'A', 'floor': '1',
                'room_type': 'Triple', 'capacity': '3'}
        data.update(overrides)
        return data

    def edit(self, **overrides):
        return self.client.post(self.url, self.data(**overrides))

    def test_UT_ROOM_13__edit_form_is_filled_with_the_current_details(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="A-101"')
        self.assertContains(response, 'value="Triple"')
        self.assertContains(response, 'value="3"')

    def test_UT_ROOM_13__number_capacity_and_type_can_be_changed(self):
        response = self.edit(room_no='A-110', capacity='4', room_type='Deluxe Triple')
        self.assertRedirects(response, reverse('rooms:manage'))
        self.room.refresh_from_db()
        self.assertEqual((self.room.room_no, self.room.capacity, self.room.room_type),
                         ('A-110', 4, 'Deluxe Triple'))

    def test_UT_ROOM_13__changes_appear_in_the_room_list(self):
        self.edit(room_no='A-110', room_type='Deluxe Triple')
        listing = self.client.get(reverse('rooms:manage'))
        self.assertContains(listing, 'A-110')
        self.assertContains(listing, 'Deluxe Triple')
        self.assertNotContains(listing, 'A-101')

    def test_UT_ROOM_13__block_and_floor_can_be_changed(self):
        self.edit(block='B', floor='2')
        self.room.refresh_from_db()
        self.assertEqual((self.room.block, self.room.floor), ('B', 2))

    def test_UT_ROOM_13__same_validation_as_adding(self):
        for overrides, message in ((dict(room_no='B-204'), 'Room number already exists'),
                                   (dict(capacity='-2'), 'Capacity must be greater than zero'),
                                   (dict(capacity='abc'), 'Capacity must be a whole number'),
                                   (dict(room_no=''), 'Room number is required'),
                                   (dict(room_type=''), 'Room type is required')):
            with self.subTest(message=message):
                self.assertContains(self.edit(**overrides), message)
        self.room.refresh_from_db()
        self.assertEqual((self.room.room_no, self.room.capacity), ('A-101', 3))

    def test_UT_ROOM_13__keeping_the_same_number_is_not_a_duplicate(self):
        self.assertRedirects(self.edit(room_type='Single', capacity='1'), reverse('rooms:manage'))

    def test_UT_ROOM_13__a_room_cannot_move_to_another_hostel(self):
        other = Hostel.objects.create(name='Annexe', code='ANX')
        self.edit(hostel=other.pk)
        self.room.refresh_from_db()
        self.assertEqual(self.room.hostel, self.hostel)

    def test_UT_ROOM_13__unknown_room_is_a_404(self):
        self.assertEqual(self.client.get(reverse('rooms:edit', args=[99999])).status_code, 404)

    def test_UT_ROOM_13__only_administrators_can_edit(self):
        for username in ('wdn05', 'stu1023'):
            self.client.force_login(get_user_model().objects.get(username=username))
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.edit(room_type='Single').status_code, 403)
        self.room.refresh_from_db()
        self.assertEqual(self.room.room_type, 'Triple')

"""Issue #41 (FR-03.02): reject a duplicate room number."""
import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Room
from core.seed import seed


class DuplicateRoomTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        self.rooms_before = Room.objects.count()

    def add(self, **overrides):
        data = {'hostel': self.hostel.pk, 'room_no': 'A-101', 'block': 'A', 'floor': '1',
                'room_type': 'Triple', 'capacity': '3'}
        data.update(overrides)
        return self.client.post(reverse('rooms:add'), data)

    def test_UT_08_Room__duplicate_room_number_is_rejected_with_the_test_plan_message(self):
        response = self.add()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room number already exists')
        self.assertEqual(Room.objects.count(), self.rooms_before)

    def test_UT_08_Room__the_room_number_field_is_highlighted(self):
        response = self.add()
        tag = re.search(r'<input[^>]*name="room_no"[^>]*>', response.content.decode())
        self.assertIn('is-invalid', tag.group(0))

    def test_UT_08_Room__the_form_keeps_what_was_typed(self):
        response = self.add(room_type='Deluxe Triple')
        self.assertContains(response, 'value="Deluxe Triple"')

    def test_UT_08_Room__check_ignores_case_and_spaces(self):
        for value in ('a-101', '  A-101  '):
            with self.subTest(value=value):
                self.assertContains(self.add(room_no=value), 'Room number already exists')
        self.assertEqual(Room.objects.count(), self.rooms_before)

    def test_UT_08_Room__a_new_number_is_accepted(self):
        self.assertRedirects(self.add(room_no='A-199'), reverse('rooms:manage'))

    def test_UT_08_Room__the_same_number_may_exist_in_another_hostel(self):
        other = Hostel.objects.create(name='Annexe', code='ANX')
        response = self.add(hostel=other.pk)
        self.assertRedirects(response, reverse('rooms:manage'))
        self.assertEqual(Room.objects.filter(room_no='A-101').count(), 2)

    def test_UT_08_Room__two_administrators_saving_at_once_get_the_same_message(self):
        with patch('rooms.services.create_room', side_effect=IntegrityError):
            response = self.add(room_no='A-199')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room number already exists')
        self.assertEqual(Room.objects.count(), self.rooms_before)

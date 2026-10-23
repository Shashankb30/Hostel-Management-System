"""Issue #51 (FR-03.12): capacity cannot drop below the current occupancy."""
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.models import Room
from core.seed import seed
from rooms import services
from rooms.testing import fill_room


class CapacityVersusOccupancyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        self.room = Room.objects.get(room_no='A-101')  # capacity 3
        fill_room(self.room, 2)

    def edit(self, capacity):
        return self.client.post(reverse('rooms:edit', args=[self.room.pk]), {
            'hostel': self.room.hostel_id, 'room_no': 'A-101', 'block': 'A', 'floor': '1',
            'room_type': 'Triple', 'capacity': capacity})

    def test_UT_ROOM_11__lowering_capacity_below_the_occupants_is_rejected(self):
        response = self.edit('1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Capacity cannot be lower than the 2 student(s) currently in the room')
        self.room.refresh_from_db()
        self.assertEqual(self.room.capacity, 3)

    def test_UT_ROOM_11__the_capacity_field_is_highlighted(self):
        response = self.edit('1')
        tag = re.search(r'<input[^>]*name="capacity"[^>]*>', response.content.decode())
        self.assertIn('is-invalid', tag.group(0))

    def test_UT_ROOM_11__capacity_equal_to_the_occupants_is_allowed(self):
        self.assertRedirects(self.edit('2'), reverse('rooms:manage'))
        self.room.refresh_from_db()
        self.assertEqual(self.room.capacity, 2)

    def test_UT_ROOM_11__raising_capacity_is_allowed(self):
        self.assertRedirects(self.edit('6'), reverse('rooms:manage'))

    def test_UT_ROOM_11__only_students_currently_in_the_room_count(self):
        empty = Room.objects.get(room_no='C-102')
        self.assertRedirects(
            self.client.post(reverse('rooms:edit', args=[empty.pk]), {
                'hostel': empty.hostel_id, 'room_no': 'C-102', 'block': 'C', 'floor': '1',
                'room_type': 'Single', 'capacity': '1'}),
            reverse('rooms:manage'))

    def test_UT_ROOM_11__the_service_enforces_the_rule_too(self):
        with self.assertRaises(ValidationError):
            services.check_capacity(self.room, 1)
        services.check_capacity(self.room, 2)  # exactly the occupants: fine

"""Issue #42 (FR-03.03): capacity must be a positive whole number."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Room
from core.seed import seed


class CapacityValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        self.rooms_before = Room.objects.count()

    def add(self, capacity):
        return self.client.post(reverse('rooms:add'), {
            'hostel': self.hostel.pk, 'room_no': 'F-101', 'room_type': 'Single', 'capacity': capacity})

    def test_UT_09_Room__negative_capacity_is_rejected(self):
        response = self.add('-2')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Capacity must be greater than zero')
        self.assertEqual(Room.objects.count(), self.rooms_before)

    def test_UT_09_Room__zero_capacity_is_rejected(self):
        self.assertContains(self.add('0'), 'Capacity must be greater than zero')
        self.assertEqual(Room.objects.count(), self.rooms_before)

    def test_UT_09_Room__non_numeric_capacity_is_rejected(self):
        for value in ('abc', '2.5', '3 beds'):
            with self.subTest(value=value):
                self.assertContains(self.add(value), 'Capacity must be a whole number')
        self.assertEqual(Room.objects.count(), self.rooms_before)

    def test_UT_09_Room__capacity_has_an_upper_limit(self):
        self.assertContains(self.add('101'), 'Capacity must be at most 100')
        self.assertEqual(Room.objects.count(), self.rooms_before)

    def test_UT_09_Room__smallest_and_largest_valid_capacities_are_accepted(self):
        self.assertRedirects(self.add('1'), reverse('rooms:manage'))
        self.client.post(reverse('rooms:add'), {
            'hostel': self.hostel.pk, 'room_no': 'F-102', 'room_type': 'Hall', 'capacity': '100'})
        self.assertEqual(Room.objects.count(), self.rooms_before + 2)

    def test_UT_09_Room__the_capacity_field_is_highlighted(self):
        response = self.add('-2')
        self.assertRegex(response.content.decode(), r'<input[^>]*name="capacity"[^>]*is-invalid')

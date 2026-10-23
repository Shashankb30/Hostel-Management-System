"""Issue #46 (FR-03.07): room detail changes reflect in the student's room view."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Room, Student
from core.seed import seed
from rooms.testing import allocate


class RoomChangesReachTheStudentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.room = Room.objects.get(room_no='A-101')
        allocate(Student.objects.get(roll_no='CSE2201'), cls.room)

    def setUp(self):
        self.admin = Client()
        self.admin.force_login(get_user_model().objects.get(username='admin01'))
        self.student = Client()
        self.student.force_login(get_user_model().objects.get(username='stu1023'))

    def edit(self, **overrides):
        data = {'hostel': self.room.hostel_id, 'room_no': self.room.room_no, 'block': self.room.block,
                'floor': self.room.floor, 'room_type': self.room.room_type, 'capacity': self.room.capacity}
        data.update(overrides)
        return self.admin.post(reverse('rooms:edit', args=[self.room.pk]), data)

    def my_room(self):
        return self.student.get(reverse('allocation:my_room'))

    def test_IT_09_Room__a_changed_room_type_is_shown_to_the_allocated_student(self):
        self.assertNotContains(self.my_room(), 'Deluxe Triple')
        self.assertEqual(self.edit(room_type='Deluxe Triple').status_code, 302)
        self.assertContains(self.my_room(), 'Deluxe Triple')

    def test_IT_09_Room__a_changed_room_number_is_shown(self):
        self.edit(room_no='A-150')
        response = self.my_room()
        self.assertContains(response, 'Room A-150')
        self.assertNotContains(response, 'Room A-101')

    def test_IT_09_Room__changed_block_floor_and_capacity_are_shown(self):
        self.edit(block='Z', floor=4, capacity=5)
        response = self.my_room()
        self.assertEqual(response.context['room'].block, 'Z')
        self.assertContains(response, '>5<')

    def test_IT_09_Room__a_rejected_edit_changes_nothing_for_the_student(self):
        self.edit(room_type='Deluxe Triple', capacity='-1')
        self.assertNotContains(self.my_room(), 'Deluxe Triple')

    def test_IT_09_Room__the_page_is_never_cached_so_a_reload_shows_the_change(self):
        self.assertIn('no-store', self.my_room()['Cache-Control'])

"""Issue #47 (FR-03.08): a student sees their own allocated room."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Room, Student, UserAccount
from core.seed import seed
from rooms.testing import allocate, make_student


class MyRoomTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.room = Room.objects.get(room_no='B-204')
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')

    def log_in(self, username):
        self.client.force_login(get_user_model().objects.get(username=username))

    def test_IT_ROOM_12__allocated_student_sees_room_number_type_and_roommate_count(self):
        allocate(self.arjun, self.room)
        allocate(self.divya, self.room)
        self.log_in('stu1023')
        response = self.client.get(reverse('allocation:my_room'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room B-204')
        self.assertContains(response, self.room.room_type)
        self.assertEqual(response.context['roommates'], 1)

    def test_IT_ROOM_12__details_include_hostel_block_floor_and_capacity(self):
        allocate(self.arjun, self.room)
        self.log_in('stu1023')
        response = self.client.get(reverse('allocation:my_room'))
        for expected in (self.room.hostel.name, 'Block', 'Floor', 'Capacity', 'Allocated on'):
            with self.subTest(expected=expected):
                self.assertContains(response, expected)

    def test_IT_ROOM_12__roommates_count_leaves_out_the_student_and_past_roommates(self):
        allocate(self.arjun, self.room)
        other = make_student('GONE01', self.room.hostel)
        allocate(other, self.room, status='ended')
        self.log_in('stu1023')
        response = self.client.get(reverse('allocation:my_room'))
        self.assertEqual(response.context['roommates'], 0)

    def test_IT_ROOM_12__a_student_without_a_room_sees_an_empty_state(self):
        self.log_in('stu1023')
        response = self.client.get(reverse('allocation:my_room'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You have not been allocated a room yet')
        self.assertIsNone(response.context['room'])

    def test_IT_ROOM_12__a_student_only_sees_their_own_room(self):
        other_room = Room.objects.get(room_no='C-102')
        allocate(self.arjun, self.room)
        allocate(self.divya, other_room)
        self.log_in('stu1023')
        response = self.client.get(reverse('allocation:my_room'))
        self.assertContains(response, 'Room B-204')
        self.assertNotContains(response, 'C-102')

    def test_IT_ROOM_12__a_student_login_without_a_student_record_is_told_so(self):
        user = get_user_model().objects.create_user(username='norecord', password='Pass@123')
        UserAccount.objects.create(user=user, role=UserAccount.ROLE_STUDENT, hostel=self.room.hostel)
        self.client.force_login(user)
        response = self.client.get(reverse('allocation:my_room'))
        self.assertContains(response, 'student record has not been created yet')

    def test_IT_ROOM_12__my_room_menu_item_is_a_working_link(self):
        self.log_in('stu1023')
        response = self.client.get(reverse('core:dashboard_student'))
        links = {item['label']: item['url'] for item in response.context['nav_items']}
        self.assertEqual(links['My Room'], reverse('allocation:my_room'))

    def test_IT_ROOM_12__only_students_can_open_my_room(self):
        for username in ('wdn05', 'admin01'):
            self.log_in(username)
            self.assertEqual(self.client.get(reverse('allocation:my_room')).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('allocation:my_room')).status_code, 302)

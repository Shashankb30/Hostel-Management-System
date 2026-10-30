from django.test import TestCase
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from datetime import date
from .models import Hostel, UserAccount, Student, Room, Allocation

class SchemaIntegrityTests(TestCase):
    def setUp(self):
        self.hostel = Hostel.objects.create(name='North Hostel', code='NH')
        auth_user = get_user_model().objects.create_user(username='student1', password='not-a-real-secret')
        self.account = UserAccount.objects.create(user=auth_user, hostel=self.hostel)
        self.student = Student.objects.create(user_account=self.account, hostel=self.hostel, roll_no='CSE001', full_name='Test Student')
        self.room = Room.objects.create(hostel=self.hostel, room_no='A-101', capacity=2)

    def test_roll_number_is_unique(self):
        auth_user = get_user_model().objects.create_user(username='student2')
        account = UserAccount.objects.create(user=auth_user, hostel=self.hostel)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Student.objects.create(user_account=account, hostel=self.hostel, roll_no='CSE001', full_name='Duplicate')

    def test_room_number_unique_per_hostel(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Room.objects.create(hostel=self.hostel, room_no='A-101', capacity=1)

    def test_room_number_can_repeat_in_another_hostel(self):
        other = Hostel.objects.create(name='South Hostel', code='SH')
        Room.objects.create(hostel=other, room_no='A-101', capacity=1)

    def test_active_allocation_is_unique_per_student(self):
        Allocation.objects.create(student=self.student, room=self.room, allocated_on=date.today())
        other_room = Room.objects.create(hostel=self.hostel, room_no='A-102', capacity=2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Allocation.objects.create(student=self.student, room=other_room, allocated_on=date.today())

    def test_ended_allocation_does_not_block_new_active_allocation(self):
        Allocation.objects.create(student=self.student, room=self.room, allocated_on=date.today(), status='ended')
        other_room = Room.objects.create(hostel=self.hostel, room_no='A-102', capacity=2)
        Allocation.objects.create(student=self.student, room=other_room, allocated_on=date.today())

    def test_room_occupancy_is_derived(self):
        self.assertEqual(self.room.occupancy, 0)
        Allocation.objects.create(student=self.student, room=self.room, allocated_on=date.today())
        self.assertEqual(self.room.occupancy, 1)
        self.assertEqual(self.room.vacancies, 1)

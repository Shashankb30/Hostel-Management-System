from io import StringIO

from django.contrib.auth import authenticate, get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from .models import FeeRecord, Hostel, Room, Student, UserAccount
from .seed import seed


class SeedDataTests(TestCase):
    def setUp(self):
        seed()

    def test_users_have_test_plan_credentials_and_roles(self):
        expected = {
            'stu1023': ('Pass@123', UserAccount.ROLE_STUDENT),
            'wdn05': ('Warden@12', UserAccount.ROLE_WARDEN),
            'admin01': ('Admin@12', UserAccount.ROLE_ADMIN),
        }
        for username, (password, role) in expected.items():
            user = authenticate(username=username, password=password)
            self.assertIsNotNone(user, username)
            self.assertEqual(user.hms_account.role, role)

    def test_stu9999_is_inactive_and_locked(self):
        user = get_user_model().objects.get(username='stu9999')
        self.assertFalse(user.is_active)
        self.assertTrue(user.hms_account.is_locked)
        self.assertIsNone(authenticate(username='stu9999', password='Pass@123'))

    def test_students_exist(self):
        arjun = Student.objects.get(roll_no='CSE2201')
        self.assertEqual(arjun.full_name, 'Arjun Rao')
        self.assertEqual(arjun.phone, '9876543210')
        self.assertEqual(arjun.user_account.user.username, 'stu1023')
        self.assertTrue(Student.objects.filter(full_name__startswith='Divya').exists())

    def test_rooms_exist_with_expected_capacity(self):
        self.assertEqual(Room.objects.get(room_no='A-101').capacity, 3)
        self.assertEqual(Room.objects.filter(room_no__in=['B-204', 'C-102']).count(), 2)

    def test_seeded_rooms_start_vacant(self):
        for room in Room.objects.all():
            self.assertEqual(room.occupancy, 0)
            self.assertEqual(room.vacancies, room.capacity)

    def test_outstanding_fee_is_fifty_thousand(self):
        fee = FeeRecord.objects.get(student__roll_no='CSE2201')
        self.assertEqual(fee.balance, 50000)
        self.assertEqual(fee.fee_status, 'unpaid')

    def test_seed_is_idempotent(self):
        tracked = (Hostel, get_user_model(), UserAccount, Student, Room, FeeRecord)
        before = [model.objects.count() for model in tracked]
        result = seed()
        seed()
        self.assertEqual(result['created'], 0)
        self.assertEqual([model.objects.count() for model in tracked], before)

    def test_seed_restores_baseline_state(self):
        user = get_user_model().objects.get(username='stu1023')
        user.set_password('changed-by-a-test')
        user.save()
        account = user.hms_account
        account.is_locked = True
        account.failed_login_attempts = 5
        account.save()
        Room.objects.filter(room_no='A-101').update(capacity=9)

        seed()

        self.assertIsNotNone(authenticate(username='stu1023', password='Pass@123'))
        account.refresh_from_db()
        self.assertFalse(account.is_locked)
        self.assertEqual(account.failed_login_attempts, 0)
        self.assertEqual(Room.objects.get(room_no='A-101').capacity, 3)


class SeedCommandTests(TestCase):
    @override_settings(DEBUG=True)
    def test_command_runs_twice_without_error(self):
        out = StringIO()
        call_command('seed_data', stdout=out)
        call_command('seed_data', stdout=out)
        self.assertIn('stu1023', out.getvalue())
        self.assertEqual(Student.objects.filter(roll_no='CSE2201').count(), 1)

    @override_settings(DEBUG=False)
    def test_command_refuses_when_debug_is_off(self):
        with self.assertRaises(CommandError):
            call_command('seed_data', stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username='admin01').exists())

    @override_settings(DEBUG=False)
    def test_force_flag_allows_seeding(self):
        call_command('seed_data', '--force', stdout=StringIO())
        self.assertTrue(get_user_model().objects.filter(username='admin01').exists())

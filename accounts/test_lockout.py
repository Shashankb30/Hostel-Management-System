"""Issue #26 (FR-01.11): lock an account after repeated failed logins."""
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts import lockout
from core.models import UserAccount
from core.seed import seed


@override_settings(HMS_MAX_FAILED_LOGINS=3)
class LockoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def log_in(self, username, password):
        return self.client.post(reverse('login'), {'username': username, 'password': password})

    def account(self, username='stu1023'):
        return UserAccount.objects.get(user__username=username)

    def test_IT_LOGIN_06__wrong_password_is_counted(self):
        self.log_in('stu1023', 'wrong@1')
        self.assertEqual(self.account().failed_login_attempts, 1)
        self.assertFalse(self.account().is_locked)

    def test_IT_LOGIN_06__account_locks_at_the_threshold_and_says_so(self):
        self.log_in('stu1023', 'wrong@1')
        self.log_in('stu1023', 'wrong@2')
        response = self.log_in('stu1023', 'wrong@3')
        self.assertContains(response, 'too many failed login attempts')
        self.assertTrue(self.account().is_locked)

    def test_IT_LOGIN_06__locked_account_refuses_even_the_correct_password(self):
        for attempt in range(3):
            self.log_in('stu1023', f'wrong@{attempt}')
        response = self.log_in('stu1023', 'Pass@123')
        self.assertContains(response, 'too many failed login attempts')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_IT_LOGIN_06__count_stops_growing_once_locked(self):
        for attempt in range(6):
            self.log_in('stu1023', f'wrong@{attempt}')
        self.assertEqual(self.account().failed_login_attempts, 3)

    def test_IT_LOGIN_06__good_login_clears_the_count(self):
        self.log_in('stu1023', 'wrong@1')
        self.log_in('stu1023', 'wrong@2')
        self.log_in('stu1023', 'Pass@123')
        self.assertEqual(self.account().failed_login_attempts, 0)

    def test_IT_LOGIN_06__threshold_is_configurable(self):
        with override_settings(HMS_MAX_FAILED_LOGINS=2):
            self.log_in('stu1024', 'wrong@1')
            self.log_in('stu1024', 'wrong@2')
        self.assertTrue(self.account('stu1024').is_locked)
        self.assertEqual(lockout.max_attempts(), 3)

    def test_IT_LOGIN_06__inactive_account_failures_are_not_counted(self):
        self.log_in('stu9999', 'wrong@1')
        self.assertEqual(self.account('stu9999').failed_login_attempts, 0)

    def test_IT_LOGIN_06__unknown_username_changes_nothing(self):
        self.log_in('nobody99', 'wrong@1')
        self.assertEqual(UserAccount.objects.filter(failed_login_attempts__gt=0).count(), 0)

    def test_IT_LOGIN_06__unlock_command_unlocks_and_allows_login(self):
        for attempt in range(3):
            self.log_in('stu1023', f'wrong@{attempt}')
        call_command('unlock_account', 'stu1023', stdout=StringIO())
        account = self.account()
        self.assertFalse(account.is_locked)
        self.assertEqual(account.failed_login_attempts, 0)
        self.assertEqual(self.log_in('stu1023', 'Pass@123').status_code, 302)

    def test_IT_LOGIN_06__unlock_command_rejects_unknown_username(self):
        with self.assertRaises(CommandError):
            call_command('unlock_account', 'nobody99', stdout=StringIO())

"""Issue #20 (FR-01.05): inactive or locked accounts cannot log in."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import UserAccount
from core.seed import seed


class BlockedAccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def log_in(self, username, password):
        return self.client.post(reverse('login'), {'username': username, 'password': password})

    def test_IT_03_Login__seeded_inactive_locked_account_is_refused(self):
        response = self.log_in('stu9999', 'Pass@123')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inactive or locked')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_IT_03_Login__inactive_account_message_gives_the_reason(self):
        get_user_model().objects.filter(username='stu1024').update(is_active=False)
        response = self.log_in('stu1024', 'Pass@123')
        self.assertContains(response, 'Account is inactive or locked')
        self.assertContains(response, 'deactivated')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_IT_03_Login__locked_account_message_gives_the_reason(self):
        UserAccount.objects.filter(user__username='stu1024').update(is_locked=True)
        response = self.log_in('stu1024', 'Pass@123')
        self.assertContains(response, 'Account is inactive or locked')
        self.assertContains(response, 'locked by an administrator')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_IT_03_Login__no_session_is_created_for_a_blocked_account(self):
        self.log_in('stu9999', 'Pass@123')
        self.assertEqual(self.client.get('/').status_code, 302)  # still sent to login
        self.assertTrue(self.client.get('/').url.startswith('/login/'))

    def test_IT_03_Login__wrong_password_does_not_reveal_that_the_account_is_blocked(self):
        response = self.log_in('stu9999', 'wrong@1')
        self.assertContains(response, 'Invalid username or password')
        self.assertNotContains(response, 'inactive or locked')

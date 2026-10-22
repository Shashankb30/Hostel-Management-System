"""Issue #21 (FR-01.06): blank credentials are rejected before authenticating."""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.models import UserAccount
from core.seed import seed


class BlankCredentialsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def post_login(self, username, password):
        with patch('accounts.forms.authenticate_credentials') as authenticate:
            response = self.client.post(
                reverse('login'), {'username': username, 'password': password})
        return response, authenticate

    def test_ST_02_Login__blank_username_and_password_show_validation_errors(self):
        response, authenticate = self.post_login('', '')
        self.assertContains(response, 'Username is required')
        self.assertContains(response, 'Password is required')
        authenticate.assert_not_called()
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_ST_02_Login__blank_password_only(self):
        response, authenticate = self.post_login('stu1023', '')
        self.assertContains(response, 'Password is required')
        self.assertNotContains(response, 'Username is required')
        authenticate.assert_not_called()

    def test_ST_02_Login__blank_username_only(self):
        response, authenticate = self.post_login('', 'Pass@123')
        self.assertContains(response, 'Username is required')
        authenticate.assert_not_called()

    def test_ST_02_Login__spaces_only_count_as_blank(self):
        response, authenticate = self.post_login('   ', '   ')
        self.assertContains(response, 'Username is required')
        self.assertContains(response, 'Password is required')
        authenticate.assert_not_called()

    def test_ST_02_Login__username_that_is_too_long_is_rejected_before_authenticating(self):
        response, authenticate = self.post_login('x' * 151, 'Pass@123')
        self.assertContains(response, 'Username must be at most 150 characters')
        authenticate.assert_not_called()

    def test_ST_02_Login__blank_submit_does_not_count_as_a_failed_login(self):
        self.client.post(reverse('login'), {'username': 'stu1023', 'password': ''})
        account = UserAccount.objects.get(user__username='stu1023')
        self.assertEqual(account.failed_login_attempts, 0)

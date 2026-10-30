"""Issue #23 (FR-01.08): logout."""
from django.test import TestCase
from django.urls import reverse

from core.seed import seed


class LogoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def setUp(self):
        self.client.post(reverse('login'), {'username': 'stu1023', 'password': 'Pass@123'})

    def test_UT_LOGIN_04__logout_ends_the_session_and_returns_to_login(self):
        self.assertIn('_auth_user_id', self.client.session)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_UT_LOGIN_04__login_page_confirms_the_logout(self):
        response = self.client.post(reverse('logout'), follow=True)
        self.assertContains(response, 'You have been logged out')

    def test_UT_LOGIN_04__logout_needs_post(self):
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_UT_LOGIN_04__logout_when_not_logged_in_just_shows_login(self):
        self.client.post(reverse('logout'), follow=True)  # shows (and clears) the first message
        response = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(response.redirect_chain[-1][0], reverse('login'))
        self.assertNotContains(response, 'You have been logged out')

    def test_ST_LOGIN_03__protected_page_is_not_reachable_after_logout(self):
        self.client.post(reverse('logout'))
        response = self.client.get(reverse('core:dashboard_student'))
        self.assertRedirects(response, '/login/?next=/dashboard/student/')

    def test_ST_LOGIN_03__pages_for_logged_in_users_are_not_cached_by_the_browser(self):
        response = self.client.get(reverse('core:dashboard_student'))
        cache_control = response['Cache-Control']
        self.assertIn('no-store', cache_control)
        self.assertIn('private', cache_control)

    def test_logout_button_is_shown_in_the_top_bar(self):
        response = self.client.get(reverse('core:dashboard_student'))
        self.assertContains(response, 'action="%s"' % reverse('logout'))
        self.assertContains(response, 'Log out')

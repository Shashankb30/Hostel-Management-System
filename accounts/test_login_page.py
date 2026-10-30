"""Issue #16 (FR-01.01): the login page."""
from django.test import TestCase
from django.urls import reverse

from core.seed import seed


class LoginPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def test_UT_01_Login__page_shows_username_password_and_submit(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'type="submit"')

    def test_UT_01_Login__password_input_is_masked(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'type="password"')

    def test_login_page_is_served_at_login_url(self):
        self.assertEqual(reverse('login'), '/login/')

    def test_logged_in_user_opening_login_page_goes_to_dashboard(self):
        self.client.login(username='stu1023', password='Pass@123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('core:dashboard_student'))

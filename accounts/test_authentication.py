"""Issues #17, #18, #19 (FR-01.02 to FR-01.04): valid login, invalid login, role redirect."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.seed import seed


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def log_in(self, username, password, **extra):
        return self.client.post(
            reverse('login'), {'username': username, 'password': password}, **extra)

    def form_errors(self, response):
        return list(response.context['form'].non_field_errors())

    # --- #17 valid Student credentials -------------------------------------------
    def test_UT_02_Login__valid_student_reaches_student_dashboard(self):
        response = self.log_in('stu1023', 'Pass@123')
        self.assertRedirects(response, reverse('core:dashboard_student'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_UT_02_Login__session_belongs_to_the_logged_in_student(self):
        self.log_in('stu1023', 'Pass@123')
        user = get_user_model().objects.get(username='stu1023')
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    # --- #18 invalid credentials -------------------------------------------------
    def test_UT_03_Login__wrong_password_shows_error_and_denies_access(self):
        response = self.log_in('stu1023', 'wrong@1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_UT_03_Login__user_can_retry_after_an_error(self):
        self.log_in('stu1023', 'wrong@1')
        response = self.log_in('stu1023', 'Pass@123')
        self.assertRedirects(response, reverse('core:dashboard_student'))

    def test_UT_03_Login__message_does_not_reveal_which_field_was_wrong(self):
        wrong_password = self.form_errors(self.log_in('stu1023', 'wrong@1'))
        unknown_user = self.form_errors(self.log_in('nobody99', 'Pass@123'))
        self.assertEqual(wrong_password, ['Invalid username or password'])
        self.assertEqual(wrong_password, unknown_user)

    # --- #19 role-based redirection ----------------------------------------------
    def test_IT_01_Login__warden_lands_on_warden_dashboard_with_warden_menu(self):
        response = self.log_in('wdn05', 'Warden@12')
        self.assertRedirects(response, reverse('core:dashboard_warden'))
        labels = [item['label'] for item in self.client.get(
            reverse('core:dashboard_warden')).context['nav_items']]
        self.assertIn('Room Allocation', labels)
        self.assertNotIn('Users & Roles', labels)

    def test_IT_02_Login__administrator_lands_on_admin_dashboard_with_full_menu(self):
        response = self.log_in('admin01', 'Admin@12')
        self.assertRedirects(response, reverse('core:dashboard_admin'))
        labels = [item['label'] for item in self.client.get(
            reverse('core:dashboard_admin')).context['nav_items']]
        for expected in ('Users & Roles', 'Students', 'Rooms', 'Fees', 'Reports'):
            self.assertIn(expected, labels)

    def test_IT_01_Login__user_without_an_hms_role_is_refused(self):
        get_user_model().objects.create_user(username='norole', password='Pass@123')
        response = self.log_in('norole', 'Pass@123')
        self.assertContains(response, 'Account has no role assigned')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_follows_a_safe_next_address(self):
        response = self.client.post(
            reverse('login') + '?next=/dashboard/student/',
            {'username': 'stu1023', 'password': 'Pass@123'})
        self.assertRedirects(response, '/dashboard/student/')

    def test_login_ignores_an_external_next_address(self):
        response = self.client.post(
            reverse('login') + '?next=https://evil.example/',
            {'username': 'stu1023', 'password': 'Pass@123'})
        self.assertRedirects(response, reverse('core:dashboard_student'))

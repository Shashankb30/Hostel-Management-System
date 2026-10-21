"""Issue #25 (FR-01.10): the administrator manages user accounts and roles."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Hostel, UserAccount
from core.seed import seed

PASSWORD = 'Brand-New#Pass7'


class UserManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.admin = get_user_model().objects.get(username='admin01')
        self.client.force_login(self.admin)

    def account(self, username):
        return UserAccount.objects.select_related('user').get(user__username=username)

    def data(self, **overrides):
        data = {
            'username': 'stu2001', 'first_name': 'New', 'last_name': 'Student',
            'email': 'stu2001@hms.example', 'phone': '9876500001', 'role': 'student',
            'hostel': self.hostel.pk, 'password1': PASSWORD, 'password2': PASSWORD,
        }
        data.update(overrides)
        return data

    def create(self, **overrides):
        return self.client.post(reverse('accounts:user_create'), self.data(**overrides))

    def log_in_as(self, username, password):
        other = Client()
        return other, other.post(reverse('login'), {'username': username, 'password': password})

    # --- access ------------------------------------------------------------------
    def test_IT_LOGIN_04__only_administrators_can_open_user_management(self):
        urls = [reverse('accounts:users'), reverse('accounts:user_create')]
        for username in ('stu1023', 'wdn05'):
            self.client.force_login(get_user_model().objects.get(username=username))
            for url in urls:
                with self.subTest(username=username, url=url):
                    self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(urls[0]).status_code, 302)

    def test_IT_LOGIN_04__users_menu_item_is_now_a_working_link(self):
        response = self.client.get(reverse('core:dashboard_admin'))
        links = {item['label']: item['url'] for item in response.context['nav_items']}
        self.assertEqual(links['Users & Roles'], reverse('accounts:users'))

    # --- list and filters --------------------------------------------------------
    def test_IT_LOGIN_04__list_shows_accounts_with_role_and_status(self):
        response = self.client.get(reverse('accounts:users'))
        for username in ('stu1023', 'wdn05', 'admin01', 'stu9999'):
            self.assertContains(response, username)
        self.assertContains(response, 'Inactive')
        self.assertContains(response, 'Locked')

    def test_IT_LOGIN_04__list_can_be_filtered(self):
        by_role = self.client.get(reverse('accounts:users'), {'role': 'warden'})
        self.assertContains(by_role, 'wdn05')
        self.assertNotContains(by_role, 'stu1023')
        by_status = self.client.get(reverse('accounts:users'), {'status': 'inactive'})
        self.assertContains(by_status, 'stu9999')
        self.assertNotContains(by_status, 'wdn05')
        by_text = self.client.get(reverse('accounts:users'), {'q': 'Divya'})
        self.assertContains(by_text, 'stu1024')
        self.assertNotContains(by_text, 'stu1023')

    # --- create ------------------------------------------------------------------
    def test_IT_LOGIN_04__admin_creates_a_student_account_that_can_log_in(self):
        response = self.create()
        self.assertRedirects(response, reverse('accounts:users'))
        account = self.account('stu2001')
        self.assertEqual(account.role, UserAccount.ROLE_STUDENT)
        self.assertEqual(account.hostel, self.hostel)
        self.assertFalse(account.user.is_staff)
        other, login = self.log_in_as('stu2001', PASSWORD)
        self.assertRedirects(login, reverse('core:dashboard_student'))

    def test_IT_LOGIN_04__admin_role_can_use_the_admin_site(self):
        self.create(username='adm2002', email='adm2002@hms.example', role='admin', hostel='')
        user = self.account('adm2002').user
        self.assertTrue(user.is_staff and user.is_superuser)

    def test_IT_LOGIN_04__username_must_be_unique(self):
        before = get_user_model().objects.count()
        response = self.create(username='stu1023', email='other@hms.example')
        self.assertContains(response, 'Username already exists')
        self.assertEqual(get_user_model().objects.count(), before)

    def test_IT_LOGIN_04__username_uniqueness_ignores_case(self):
        response = self.create(username='STU1023', email='other@hms.example')
        self.assertContains(response, 'Username already exists')

    def test_IT_LOGIN_04__role_must_be_one_of_the_three(self):
        response = self.create(role='superhero')
        self.assertContains(response, 'Role is not a valid choice')
        self.assertFalse(get_user_model().objects.filter(username='stu2001').exists())

    def test_IT_LOGIN_04__student_and_warden_need_a_hostel(self):
        response = self.create(hostel='')
        self.assertContains(response, 'Hostel is required')

    def test_IT_LOGIN_04__password_rules_are_enforced(self):
        mismatch = self.create(password2='Different#Pass8')
        self.assertContains(mismatch, 'Passwords do not match')
        weak = self.create(password1='123', password2='123')
        self.assertTrue(weak.context['form'].errors['password1'])
        self.assertFalse(get_user_model().objects.filter(username='stu2001').exists())

    def test_IT_LOGIN_04__required_fields_are_reported(self):
        response = self.create(username='', password1='', password2='')
        self.assertContains(response, 'Username is required')
        self.assertContains(response, 'Password is required')

    def test_IT_LOGIN_04__email_must_be_unique_so_password_reset_is_unambiguous(self):
        response = self.create(email='STU1023@hms.example')
        self.assertContains(response, 'Email address already exists')

    def test_IT_LOGIN_04__phone_format_is_checked(self):
        response = self.create(phone='abcde12')
        self.assertContains(response, 'Phone number must be exactly 10 digits')

    # --- edit --------------------------------------------------------------------
    def test_IT_LOGIN_04__admin_changes_another_users_name_and_role(self):
        target = self.account('stu1024')
        response = self.client.post(reverse('accounts:user_edit', args=[target.pk]), {
            'first_name': 'Divya', 'last_name': 'Sharma', 'email': 'stu1024@hms.example',
            'phone': '9000000002', 'role': 'warden', 'hostel': self.hostel.pk})
        self.assertRedirects(response, reverse('accounts:users'))
        target = self.account('stu1024')
        self.assertEqual(target.role, UserAccount.ROLE_WARDEN)
        self.assertEqual(target.user.last_name, 'Sharma')
        other, login = self.log_in_as('stu1024', 'Pass@123')
        self.assertRedirects(login, reverse('core:dashboard_warden'))

    def test_IT_LOGIN_04__admin_cannot_change_their_own_role(self):
        own = self.account('admin01')
        response = self.client.post(reverse('accounts:user_edit', args=[own.pk]), {
            'first_name': 'Admin', 'last_name': 'One', 'email': 'admin01@hms.example',
            'phone': '', 'role': 'student', 'hostel': self.hostel.pk})
        self.assertRedirects(response, reverse('accounts:users'))
        self.assertEqual(self.account('admin01').role, UserAccount.ROLE_ADMIN)

    def test_IT_LOGIN_04__edit_does_not_clash_with_the_users_own_email(self):
        target = self.account('stu1023')
        response = self.client.post(reverse('accounts:user_edit', args=[target.pk]), {
            'first_name': 'Arjun', 'last_name': 'Rao', 'email': 'stu1023@hms.example',
            'phone': '9876543210', 'role': 'student', 'hostel': self.hostel.pk})
        self.assertRedirects(response, reverse('accounts:users'))

    def test_IT_LOGIN_04__edit_page_for_unknown_account_is_404(self):
        self.assertEqual(self.client.get(reverse('accounts:user_edit', args=[99999])).status_code, 404)

    # --- deactivate / reactivate -------------------------------------------------
    def test_IT_LOGIN_05__deactivated_account_cannot_log_in_and_can_be_reactivated(self):
        target = self.account('stu1023')
        self.client.post(reverse('accounts:user_deactivate', args=[target.pk]))
        self.assertFalse(self.account('stu1023').user.is_active)
        other, response = self.log_in_as('stu1023', 'Pass@123')
        self.assertContains(response, 'inactive or locked')
        self.assertNotIn('_auth_user_id', other.session)

        self.client.post(reverse('accounts:user_reactivate', args=[target.pk]))
        self.assertTrue(self.account('stu1023').user.is_active)
        other, response = self.log_in_as('stu1023', 'Pass@123')
        self.assertRedirects(response, reverse('core:dashboard_student'))

    def test_IT_LOGIN_05__admin_cannot_deactivate_their_own_account(self):
        own = self.account('admin01')
        response = self.client.post(reverse('accounts:user_deactivate', args=[own.pk]), follow=True)
        self.assertContains(response, 'You cannot deactivate your own account')
        self.assertTrue(self.account('admin01').user.is_active)

    def test_IT_LOGIN_05__state_changes_need_post(self):
        target = self.account('stu1023')
        for name in ('user_deactivate', 'user_reactivate', 'user_unlock'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f'accounts:{name}', args=[target.pk])).status_code, 405)

    def test_IT_LOGIN_05__other_roles_cannot_change_accounts(self):
        target = self.account('stu1024')
        self.client.force_login(get_user_model().objects.get(username='wdn05'))
        response = self.client.post(reverse('accounts:user_deactivate', args=[target.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.account('stu1024').user.is_active)

    # --- unlock ------------------------------------------------------------------
    def test_IT_LOGIN_06__admin_unlocks_a_locked_account(self):
        UserAccount.objects.filter(user__username='stu1023').update(
            is_locked=True, failed_login_attempts=5)
        target = self.account('stu1023')
        response = self.client.post(reverse('accounts:user_unlock', args=[target.pk]), follow=True)
        self.assertContains(response, 'unlocked')
        target = self.account('stu1023')
        self.assertFalse(target.is_locked)
        self.assertEqual(target.failed_login_attempts, 0)
        other, login = self.log_in_as('stu1023', 'Pass@123')
        self.assertRedirects(login, reverse('core:dashboard_student'))

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import UserAccount
from .navigation import MENUS, NavItem, build_menu
from .seed import seed


class ShellTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def login_as(self, username):
        self.client.force_login(get_user_model().objects.get(username=username))

    def labels(self, response):
        return [item['label'] for item in response.context['nav_items']]

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/login/?next=/')

    def test_login_page_renders(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')

    def test_home_redirects_each_role_to_its_dashboard(self):
        expected = {
            'stu1023': 'core:dashboard_student',
            'wdn05': 'core:dashboard_warden',
            'admin01': 'core:dashboard_admin',
        }
        for username, url_name in expected.items():
            with self.subTest(username=username):
                self.login_as(username)
                self.assertRedirects(self.client.get('/'), reverse(url_name))

    def test_each_dashboard_uses_the_common_layout(self):
        for username, url_name in [('stu1023', 'core:dashboard_student'),
                                   ('wdn05', 'core:dashboard_warden'),
                                   ('admin01', 'core:dashboard_admin')]:
            with self.subTest(username=username):
                self.login_as(username)
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'base.html')
                self.assertTemplateUsed(response, 'core/dashboard.html')

    def test_menus_differ_by_role(self):
        menus = {}
        for username, url_name in [('stu1023', 'core:dashboard_student'),
                                   ('wdn05', 'core:dashboard_warden'),
                                   ('admin01', 'core:dashboard_admin')]:
            self.login_as(username)
            menus[username] = self.labels(self.client.get(reverse(url_name)))
        self.assertEqual(len({tuple(m) for m in menus.values()}), 3)
        self.assertIn('My Room', menus['stu1023'])
        self.assertNotIn('Users & Roles', menus['stu1023'])
        self.assertIn('Room Allocation', menus['wdn05'])
        self.assertNotIn('My Room', menus['wdn05'])
        self.assertIn('Users & Roles', menus['admin01'])
        self.assertNotIn('Room Allocation', menus['admin01'])

    def test_role_name_is_shown_in_header(self):
        self.login_as('wdn05')
        self.assertContains(self.client.get(reverse('core:dashboard_warden')), 'Warden')

    def test_user_cannot_open_another_roles_dashboard(self):
        self.login_as('stu1023')
        self.assertEqual(self.client.get(reverse('core:dashboard_warden')).status_code, 403)
        self.assertEqual(self.client.get(reverse('core:dashboard_admin')).status_code, 403)
        self.login_as('wdn05')
        self.assertEqual(self.client.get(reverse('core:dashboard_student')).status_code, 403)

    def test_user_without_hms_account_gets_403(self):
        orphan = get_user_model().objects.create_user(username='orphan', password='x')
        self.client.force_login(orphan)
        self.assertEqual(self.client.get('/').status_code, 403)

    def test_locked_account_gets_403(self):
        UserAccount.objects.filter(user__username='stu1023').update(is_locked=True)
        self.login_as('stu1023')
        self.assertEqual(self.client.get('/').status_code, 403)

    def test_logout_returns_to_login(self):
        self.login_as('stu1023')
        response = self.client.post('/logout/')
        self.assertRedirects(response, '/login/')

    def test_unbuilt_module_items_are_disabled_not_broken(self):
        fake = {'student': [NavItem('Dashboard', 'core:dashboard_student'),
                            NavItem('Not Built Yet', 'nomodule:nothing')]}
        with patch.dict(MENUS, fake):
            by_label = {item['label']: item for item in build_menu('student')}
        self.assertIsNone(by_label['Not Built Yet']['url'])
        self.assertEqual(by_label['Dashboard']['url'], reverse('core:dashboard_student'))

    def test_admin_site_link_works_for_admin_role(self):
        by_label = {i['label']: i for i in build_menu(UserAccount.ROLE_ADMIN)}
        self.assertEqual(by_label['Admin Site']['url'], reverse('admin:index'))

    def test_every_role_has_a_menu_starting_with_dashboard(self):
        for role, items in MENUS.items():
            self.assertEqual(items[0].label, 'Dashboard', role)

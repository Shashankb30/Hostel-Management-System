"""Issue #22 (FR-01.07): the session lasts across module navigation and ends on timeout."""
from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.navigation import build_menu
from core.seed import seed


class SessionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def log_in(self, username='stu1023', password='Pass@123'):
        return self.client.post(reverse('login'), {'username': username, 'password': password})

    def assertStillLoggedIn(self, response):
        self.assertNotIn('/login/', response.get('Location', ''))
        self.assertIn('_auth_user_id', self.client.session)

    def test_ST_01_Login__student_stays_logged_in_while_navigating(self):
        self.log_in()
        for path in ('/dashboard/student/', '/', '/dashboard/student/',
                     '/dashboard/warden/',            # a 403 page is not a logout
                     '/no-such-module/',              # neither is a 404
                     '/dashboard/student/'):
            with self.subTest(path=path):
                self.assertStillLoggedIn(self.client.get(path))

    def test_ST_01_Login__every_menu_page_that_exists_keeps_the_session(self):
        # Covers Fees, Notices and the other modules automatically as they are delivered.
        self.log_in()
        urls = [item['url'] for item in build_menu('student') if item['url']]
        self.assertTrue(urls)
        for url in urls:
            with self.subTest(url=url):
                self.assertStillLoggedIn(self.client.get(url))

    def test_ST_01_Login__each_role_keeps_its_session_across_pages(self):
        for username, password, home in [('wdn05', 'Warden@12', 'core:dashboard_warden'),
                                         ('admin01', 'Admin@12', 'core:dashboard_admin')]:
            with self.subTest(username=username):
                self.client.logout()
                self.log_in(username, password)
                self.assertStillLoggedIn(self.client.get(reverse(home)))
                self.assertStillLoggedIn(self.client.get('/'))
                self.assertStillLoggedIn(self.client.get(reverse(home)))

    def test_ST_LOGIN_04__expired_session_sends_the_user_back_to_login(self):
        self.log_in()
        Session.objects.update(expire_date=timezone.now() - timedelta(minutes=1))
        response = self.client.get('/dashboard/student/')
        self.assertRedirects(response, '/login/?next=/dashboard/student/')

    def test_ST_LOGIN_04__activity_restarts_the_idle_timer(self):
        self.log_in()
        Session.objects.update(expire_date=timezone.now() + timedelta(minutes=1))
        self.client.get('/dashboard/student/')
        expiry = Session.objects.order_by('-expire_date').first().expire_date
        self.assertGreater(expiry, timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE // 2))

    def test_ST_LOGIN_04__timeout_settings(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, settings.HMS_SESSION_TIMEOUT_MINUTES * 60)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

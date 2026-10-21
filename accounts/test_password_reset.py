"""Issue #24 (FR-01.09): forgot password / password reset."""
import re

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from core.models import UserAccount
from core.seed import seed

NEW_PASSWORD = 'Brand-New#Pass7'


class PasswordResetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def request_reset(self, email):
        return self.client.post(reverse('password_reset'), {'email': email})

    def reset_link(self):
        match = re.search(r'https?://[^/\s]+(/reset/\S+)', mail.outbox[0].body)
        self.assertIsNotNone(match, 'the email should contain a reset link')
        return match.group(1)

    def open_reset_link(self):
        """Follow the emailed link; Django hides the token and redirects to the form."""
        response = self.client.get(self.reset_link())
        self.assertEqual(response.status_code, 302)
        return response.url

    def test_UT_LOGIN_05__login_page_has_a_forgot_password_link(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, reverse('password_reset'))
        self.assertContains(response, 'Forgot password?')

    def test_UT_LOGIN_05__reset_request_sends_an_email_with_a_link(self):
        response = self.request_reset('stu1023@hms.example')
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['stu1023@hms.example'])
        self.assertIn('/reset/', mail.outbox[0].body)

    def test_UT_LOGIN_05__password_is_reset_without_logging_in_first(self):
        self.request_reset('stu1023@hms.example')
        form_url = self.open_reset_link()
        self.assertEqual(self.client.get(form_url).status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)  # no normal login was needed
        response = self.client.post(
            form_url, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD})
        self.assertRedirects(response, reverse('password_reset_complete'))

    def test_UT_LOGIN_05__new_password_works_and_old_one_does_not(self):
        self.request_reset('stu1023@hms.example')
        form_url = self.open_reset_link()
        self.client.post(form_url, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD})
        old = self.client.post(reverse('login'), {'username': 'stu1023', 'password': 'Pass@123'})
        self.assertContains(old, 'Invalid username or password')
        new = self.client.post(reverse('login'), {'username': 'stu1023', 'password': NEW_PASSWORD})
        self.assertRedirects(new, reverse('core:dashboard_student'))

    def test_UT_LOGIN_05__link_cannot_be_used_twice(self):
        self.request_reset('stu1023@hms.example')
        link = self.reset_link()
        form_url = self.client.get(link).url
        self.client.post(form_url, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD})
        again = self.client.get(link)
        self.assertContains(again, 'not valid')

    def test_UT_LOGIN_05__weak_or_mismatched_password_is_rejected(self):
        self.request_reset('stu1023@hms.example')
        form_url = self.open_reset_link()
        weak = self.client.post(form_url, {'new_password1': '123', 'new_password2': '123'})
        self.assertEqual(weak.status_code, 200)
        self.assertTrue(weak.context['form'].errors)
        mismatch = self.client.post(
            form_url, {'new_password1': NEW_PASSWORD, 'new_password2': 'Different#Pass8'})
        self.assertEqual(mismatch.status_code, 200)
        self.assertTrue(mismatch.context['form'].errors)
        login = self.client.post(reverse('login'), {'username': 'stu1023', 'password': 'Pass@123'})
        self.assertEqual(login.status_code, 302)  # the old password still works

    def test_UT_LOGIN_05__unknown_email_gets_the_same_answer_and_no_email(self):
        response = self.request_reset('nobody@hms.example')
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_UT_LOGIN_05__inactive_account_gets_no_reset_email(self):
        response = self.request_reset('stu9999@hms.example')
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_UT_LOGIN_05__invalid_link_shows_a_clear_page(self):
        response = self.client.get(reverse('password_reset_confirm', args=['MQ', 'bad-token']))
        self.assertContains(response, 'not valid')

    def test_UT_LOGIN_05__reset_clears_failed_login_count_but_not_a_lock(self):
        UserAccount.objects.filter(user__username='stu1023').update(failed_login_attempts=2)
        self.request_reset('stu1023@hms.example')
        form_url = self.open_reset_link()
        self.client.post(form_url, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD})
        self.assertEqual(UserAccount.objects.get(user__username='stu1023').failed_login_attempts, 0)

        UserAccount.objects.filter(user__username='stu1024').update(is_locked=True)
        mail.outbox.clear()
        self.request_reset('stu1024@hms.example')
        form_url = self.open_reset_link()
        self.client.post(form_url, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD})
        self.assertTrue(UserAccount.objects.get(user__username='stu1024').is_locked)

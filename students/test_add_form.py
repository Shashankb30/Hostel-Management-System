"""Issue #28 (FR-02.01): Student Management and the Add New Student form."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.seed import seed


class AddStudentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))

    def test_UT_04_Reg__student_management_has_an_add_new_student_button(self):
        response = self.client.get(reverse('students:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Management')
        self.assertContains(response, 'Add New Student')
        self.assertContains(response, reverse('students:add'))

    def test_UT_04_Reg__form_shows_name_roll_no_contact_address_course_and_year(self):
        response = self.client.get(reverse('students:add'))
        self.assertEqual(response.status_code, 200)
        for label in ('Name', 'Roll No.', 'Contact', 'Address', 'Course', 'Year'):
            with self.subTest(label=label):
                self.assertContains(response, f'>{label}')
        for field in ('full_name', 'roll_no', 'phone', 'address', 'course', 'year_of_study'):
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')
        self.assertContains(response, 'type="submit"')

    def test_UT_04_Reg__students_menu_item_is_a_working_link(self):
        response = self.client.get(reverse('core:dashboard_admin'))
        links = {item['label']: item['url'] for item in response.context['nav_items']}
        self.assertEqual(links['Students'], reverse('students:list'))

    def test_UT_04_Reg__administrators_hostel_is_preselected(self):
        response = self.client.get(reverse('students:add'))
        self.assertEqual(response.context['form'].initial['hostel'],
                         get_user_model().objects.get(username='admin01').hms_account.hostel_id)

    def test_UT_04_Reg__list_shows_registered_students(self):
        response = self.client.get(reverse('students:list'))
        self.assertContains(response, 'CSE2201')
        self.assertContains(response, 'Arjun Rao')
        self.assertContains(response, 'CSE2202')

    def test_UT_04_Reg__list_is_paginated(self):
        with patch('students.views.PAGE_SIZE', 1):
            first = self.client.get(reverse('students:list'))
            second = self.client.get(reverse('students:list'), {'page': 2})
        self.assertContains(first, 'CSE2201')
        self.assertNotContains(first, 'CSE2202')
        self.assertContains(first, 'Page 1 of 2')
        self.assertContains(second, 'CSE2202')

    def test_UT_04_Reg__only_administrators_can_open_student_management(self):
        for username in ('stu1023', 'wdn05'):
            self.client.force_login(get_user_model().objects.get(username=username))
            for name in ('students:list', 'students:add'):
                with self.subTest(username=username, url=name):
                    self.assertEqual(self.client.get(reverse(name)).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('students:list')).status_code, 302)

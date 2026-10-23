"""Issue #30 (FR-02.03): reject duplicate Roll Number and email."""
import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Student
from core.seed import seed


class DuplicateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))
        self.students_before = Student.objects.count()
        self.users_before = get_user_model().objects.count()

    def register(self, **overrides):
        data = {
            'full_name': 'Meera Nair', 'roll_no': 'CSE2301', 'phone': '9876543210',
            'address': '', 'course': 'CSE', 'year_of_study': '1', 'hostel': self.hostel.pk,
            'email': '', 'guardian_name': '', 'guardian_phone': '',
        }
        data.update(overrides)
        return self.client.post(reverse('students:add'), data)

    def assertNothingSaved(self):
        self.assertEqual(Student.objects.count(), self.students_before)
        self.assertEqual(get_user_model().objects.count(), self.users_before)

    def assertHighlighted(self, response, field):
        tag = re.search(rf'<(?:input|select|textarea)[^>]*name="{field}"[^>]*>', response.content.decode())
        self.assertIsNotNone(tag, f'no input named {field}')
        self.assertIn('is-invalid', tag.group(0))

    # --- UT_06_Reg ---------------------------------------------------------------
    def test_UT_06_Reg__duplicate_roll_number_is_rejected_with_the_test_plan_message(self):
        response = self.register(roll_no='CSE2201')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Roll number already exists')
        self.assertNothingSaved()

    def test_UT_06_Reg__the_roll_number_field_is_highlighted(self):
        response = self.register(roll_no='CSE2201')
        self.assertHighlighted(response, 'roll_no')

    def test_UT_06_Reg__the_form_keeps_what_the_administrator_typed(self):
        response = self.register(roll_no='CSE2201', full_name='Meera Nair')
        self.assertContains(response, 'value="Meera Nair"')

    def test_UT_06_Reg__roll_number_check_ignores_case(self):
        response = self.register(roll_no='cse2201')
        self.assertContains(response, 'Roll number already exists')
        self.assertNothingSaved()

    def test_UT_06_Reg__roll_number_check_ignores_surrounding_spaces(self):
        response = self.register(roll_no='  CSE2201  ')
        self.assertContains(response, 'Roll number already exists')
        self.assertNothingSaved()

    def test_UT_06_Reg__a_new_roll_number_is_accepted(self):
        response = self.register(roll_no='CSE2399')
        self.assertRedirects(response, reverse('students:list'))

    def test_UT_06_Reg__race_between_two_administrators_is_reported_not_a_crash(self):
        with patch('students.services.register_student', side_effect=IntegrityError):
            response = self.register(roll_no='CSE2399')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Roll number already exists')
        self.assertHighlighted(response, 'roll_no')
        self.assertNothingSaved()

    # --- duplicate email ---------------------------------------------------------
    def test_UT_REG_07__email_used_by_an_existing_login_account_is_rejected(self):
        response = self.register(email='stu1023@hms.example')
        self.assertContains(response, 'Email address already exists')
        self.assertHighlighted(response, 'email')
        self.assertNothingSaved()

    def test_UT_REG_07__email_used_by_another_student_is_rejected(self):
        first = self.register(email='meera@hms.example')
        self.assertEqual(first.status_code, 302)
        second = self.register(roll_no='CSE2302', email='meera@hms.example')
        self.assertContains(second, 'Email address already exists')
        self.assertEqual(Student.objects.filter(email='meera@hms.example').count(), 1)

    def test_UT_REG_07__email_check_ignores_case(self):
        response = self.register(email='STU1023@HMS.EXAMPLE')
        self.assertContains(response, 'Email address already exists')

    def test_UT_REG_07__students_without_an_email_do_not_clash_with_each_other(self):
        self.assertEqual(self.register(roll_no='CSE2301').status_code, 302)
        self.assertEqual(self.register(roll_no='CSE2302').status_code, 302)

    def test_UT_REG_07__a_badly_formed_email_is_rejected(self):
        response = self.register(email='not-an-email')
        self.assertContains(response, 'Email address format is invalid')

    # --- Student ID --------------------------------------------------------------
    def test_UT_REG_07__student_id_cannot_be_entered_so_it_cannot_be_duplicated(self):
        response = self.client.get(reverse('students:add'))
        self.assertNotContains(response, 'name="student_id"')
        existing = Student.objects.get(roll_no='CSE2201')
        self.register(student_id=existing.student_id)
        new = Student.objects.get(roll_no='CSE2301')
        self.assertNotEqual(new.student_id, existing.student_id)

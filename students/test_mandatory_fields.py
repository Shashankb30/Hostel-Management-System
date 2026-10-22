"""Issue #31 (FR-02.04): mandatory fields are enforced on registration."""
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Student
from core.seed import seed


class MandatoryFieldTests(TestCase):
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

    def test_ST_04_Reg__blank_name_and_roll_number_are_highlighted_and_not_saved(self):
        response = self.register(full_name='', roll_no='')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Name is required')
        self.assertContains(response, 'Roll No. is required')
        self.assertHighlighted(response, 'full_name')
        self.assertHighlighted(response, 'roll_no')
        self.assertNothingSaved()

    def test_ST_04_Reg__only_the_blank_field_is_flagged(self):
        response = self.register(full_name='')
        self.assertContains(response, 'Name is required')
        self.assertNotContains(response, 'Roll No. is required')
        self.assertHighlighted(response, 'full_name')
        self.assertNothingSaved()

    def test_ST_04_Reg__spaces_only_count_as_blank(self):
        response = self.register(full_name='   ', roll_no='   ')
        self.assertContains(response, 'Name is required')
        self.assertContains(response, 'Roll No. is required')
        self.assertNothingSaved()

    def test_ST_04_Reg__every_required_field_is_checked(self):
        response = self.register(full_name='', roll_no='', phone='', course='',
                                 year_of_study='', hostel='')
        for message in ('Name is required', 'Roll No. is required', 'Contact is required',
                        'Course is required', 'Year is required', 'Hostel is required'):
            with self.subTest(message=message):
                self.assertContains(response, message)
        self.assertNothingSaved()

    def test_ST_04_Reg__optional_fields_may_be_left_blank(self):
        response = self.register(address='', email='', guardian_name='', guardian_phone='')
        self.assertRedirects(response, reverse('students:list'))
        self.assertTrue(Student.objects.filter(roll_no='CSE2301').exists())

    def test_ST_04_Reg__year_must_be_a_whole_number_between_1_and_8(self):
        for value, message in (('abc', 'Year must be a whole number'),
                               ('0', 'Year must be at least 1'),
                               ('9', 'Year must be at most 8')):
            with self.subTest(value=value):
                response = self.register(year_of_study=value)
                self.assertContains(response, message)
        self.assertNothingSaved()

    def test_ST_04_Reg__hostel_must_be_a_real_choice(self):
        response = self.register(hostel='99999')
        self.assertContains(response, 'Hostel is not a valid choice')
        self.assertNothingSaved()

    def test_ST_04_Reg__required_fields_are_marked_on_the_form(self):
        response = self.client.get(reverse('students:add'))
        self.assertContains(response, 'novalidate')
        self.assertContains(response, 'text-danger')  # the asterisk beside required fields
        self.assertContains(response, 'required')

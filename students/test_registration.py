"""Issue #29 (FR-02.02): register a student with valid data and generate a Student ID."""
import re

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Hostel, Student, UserAccount
from core.seed import seed
from students import services


class RegistrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username='admin01'))

    def data(self, **overrides):
        data = {
            'full_name': 'Meera Nair', 'roll_no': 'CSE2301', 'phone': '9876543210',
            'address': '12 Lake Road', 'course': 'CSE', 'year_of_study': '1',
            'hostel': self.hostel.pk, 'email': '', 'guardian_name': '', 'guardian_phone': '',
        }
        data.update(overrides)
        return data

    def register(self, follow=False, **overrides):
        return self.client.post(reverse('students:add'), self.data(**overrides), follow=follow)

    # --- UT_05_Reg ---------------------------------------------------------------
    def test_UT_05_Reg__valid_registration_creates_the_student_record(self):
        response = self.register()
        self.assertRedirects(response, reverse('students:list'))
        student = Student.objects.get(roll_no='CSE2301')
        self.assertEqual(student.full_name, 'Meera Nair')
        self.assertEqual(student.phone, '9876543210')
        self.assertEqual(student.address, '12 Lake Road')
        self.assertEqual(student.course, 'CSE')
        self.assertEqual(student.year_of_study, 1)
        self.assertEqual(student.hostel, self.hostel)
        self.assertTrue(student.is_active)

    def test_UT_05_Reg__a_unique_student_id_is_generated_and_shown(self):
        response = self.register(follow=True)
        student = Student.objects.get(roll_no='CSE2301')
        self.assertRegex(student.student_id, r'^STU\d{5}$')
        self.assertContains(response, f'Student ID: {student.student_id}')
        self.assertContains(response, 'Meera Nair registered')

    def test_UT_05_Reg__new_student_appears_in_the_student_list_with_the_id(self):
        self.register()
        student = Student.objects.get(roll_no='CSE2301')
        response = self.client.get(reverse('students:list'))
        self.assertContains(response, student.student_id)
        self.assertContains(response, 'Meera Nair')

    def test_UT_REG_08__every_student_gets_a_different_id(self):
        self.register(roll_no='CSE2301')
        self.register(roll_no='CSE2302', full_name='Ravi Kumar')
        ids = [student.student_id for student in Student.objects.all()]
        self.assertEqual(len(ids), 4)  # two seeded + two new
        self.assertEqual(len(set(ids)), 4)

    def test_UT_REG_08__the_id_does_not_change_when_the_record_is_edited(self):
        self.register()
        student = Student.objects.get(roll_no='CSE2301')
        before = student.student_id
        student.phone = '9123456789'
        student.save()
        self.assertEqual(Student.objects.get(pk=student.pk).student_id, before)

    def test_UT_REG_08__unsaved_student_has_no_id_yet(self):
        self.assertEqual(Student().student_id, '')

    def test_UT_REG_08__a_posted_student_id_is_ignored(self):
        self.register(student_id='STU00001')
        student = Student.objects.get(roll_no='CSE2301')
        self.assertEqual(student.student_id, f'STU{student.pk:05d}')

    # --- login account for the new student --------------------------------------
    def test_IT_REG_07__registration_creates_a_student_login_account(self):
        self.register()
        student = Student.objects.get(roll_no='CSE2301')
        account = student.user_account
        self.assertEqual(account.role, UserAccount.ROLE_STUDENT)
        self.assertEqual(account.hostel, self.hostel)
        self.assertEqual(account.phone, '9876543210')
        self.assertTrue(account.user.is_active)
        self.assertEqual(account.user.username, 'cse2301')
        self.assertEqual((account.user.first_name, account.user.last_name), ('Meera', 'Nair'))

    def test_IT_REG_07__the_temporary_password_lets_the_student_log_in(self):
        response = self.register(follow=True)
        match = re.search(r'username (\S+), temporary password (\S+)\.', response.content.decode())
        self.assertIsNotNone(match, 'the login details should be shown to the administrator')
        username, password = match.groups()
        student_client = Client()
        login = student_client.post(reverse('login'), {'username': username, 'password': password})
        self.assertRedirects(login, reverse('core:dashboard_student'))

    def test_IT_REG_07__temporary_passwords_are_random_and_strong_enough(self):
        passwords = {services.generate_temporary_password() for _ in range(20)}
        self.assertGreater(len(passwords), 15)
        for password in passwords:
            self.assertEqual(len(password), services.TEMP_PASSWORD_LENGTH)
            self.assertTrue(any(c.islower() for c in password))
            self.assertTrue(any(c.isupper() for c in password))
            self.assertTrue(any(c.isdigit() for c in password))

    def test_IT_REG_07__username_is_made_unique_when_the_roll_number_name_is_taken(self):
        get_user_model().objects.create_user(username='cse2301', password='Pass@123')
        self.register()
        student = Student.objects.get(roll_no='CSE2301')
        self.assertEqual(student.user_account.user.username, 'cse2301-2')

    def test_IT_REG_07__username_drops_characters_a_login_name_cannot_hold(self):
        self.assertEqual(services.unique_username('21/CS 007'), '21cs007')

    def test_IT_REG_07__registration_is_all_or_nothing(self):
        self.register()
        users_before = get_user_model().objects.count()
        accounts_before = UserAccount.objects.count()
        with self.assertRaises(IntegrityError):
            services.register_student(
                full_name='Someone Else', roll_no='CSE2301', phone='9876543210', course='CSE',
                year_of_study=1, hostel=self.hostel)
        self.assertEqual(get_user_model().objects.count(), users_before)
        self.assertEqual(UserAccount.objects.count(), accounts_before)

    # --- contact number format (IT_06_Reg) --------------------------------------
    def test_IT_06_Reg__alphabetic_phone_is_rejected(self):
        response = self.register(phone='abcde12')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phone number must be exactly 10 digits')
        self.assertFalse(Student.objects.filter(roll_no='CSE2301').exists())

    def test_IT_06_Reg__guardian_contact_uses_the_same_format_rule(self):
        response = self.register(guardian_phone='12345')
        self.assertContains(response, 'Phone number must be exactly 10 digits')

    def test_roll_number_with_spaces_is_rejected(self):
        response = self.register(roll_no='CSE 2301')
        self.assertContains(response, 'Roll No. format is invalid')
        self.assertFalse(Student.objects.filter(full_name='Meera Nair').exists())

    def test_optional_details_are_saved_when_given(self):
        self.register(email='meera@hms.example', guardian_name='Suresh Nair',
                      guardian_phone='9000000009')
        student = Student.objects.get(roll_no='CSE2301')
        self.assertEqual(student.email, 'meera@hms.example')
        self.assertEqual(student.user_account.user.email, 'meera@hms.example')
        self.assertEqual(student.guardian_name, 'Suresh Nair')
        self.assertEqual(student.guardian_phone, '9000000009')

    def test_only_administrators_can_register_students(self):
        self.client.force_login(get_user_model().objects.get(username='wdn05'))
        response = self.register()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Student.objects.filter(roll_no='CSE2301').exists())

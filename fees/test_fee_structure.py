"""Issues #67, #68 (FR-05.01, FR-05.02): define a student's fee; see total, paid and outstanding."""
from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.models import FeeRecord, UserAccount

from . import services
from .factories import make_account, make_fee, make_hostel, make_payment, make_student


class FeeStructureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = make_hostel()
        cls.admin = make_account('admin_t', UserAccount.ROLE_ADMIN, cls.hostel)
        cls.student = make_student(cls.hostel, 'CSE2201', 'Arjun Rao')

    def setUp(self):
        self.client.force_login(self.admin.user)

    def student_page(self, student=None):
        return self.client.get(reverse('fees:student_fees', args=[(student or self.student).pk]))

    def define(self, **overrides):
        data = {'academic_year': '2026-27', 'description': 'Hostel fee', 'amount_due': '50000', 'due_date': ''}
        data.update(overrides)
        return self.client.post(reverse('fees:fee_create', args=[self.student.pk]), data)

    # ---- viewing (#68) --------------------------------------------------------------------
    def test_UT_13_Fee__student_page_shows_total_paid_and_outstanding(self):
        fee = make_fee(self.student, '50000')
        make_payment(fee, '20000')
        response = self.student_page()
        self.assertContains(response, 'Arjun Rao')
        self.assertContains(response, 'CSE2201')
        summary = response.context['summary']
        self.assertEqual((summary['total'], summary['paid'], summary['outstanding']), (50000, 20000, 30000))
        for text in ('Rs. 50,000', 'Rs. 20,000', 'Rs. 30,000'):
            self.assertContains(response, text)

    def test_UT_13_Fee__unpaid_fee_shows_the_full_balance(self):
        make_fee(self.student, '50000')
        response = self.student_page()
        self.assertContains(response, 'Rs. 50,000')
        self.assertContains(response, 'Due')
        self.assertEqual(response.context['summary']['paid'], 0)

    def test_UT_13_Fee__totals_add_up_across_several_fees(self):
        first = make_fee(self.student, '40000', year='2026-27')
        make_fee(self.student, '10000', year='2026-27', description='Mess advance')
        make_payment(first, '15000')
        summary = services.student_summary(self.student)
        self.assertEqual((summary['total'], summary['paid'], summary['outstanding']), (50000, 15000, 35000))
        self.assertEqual(len(summary['fees']), 2)

    def test_UT_13_Fee__student_without_a_fee_is_told_so(self):
        response = self.student_page()
        self.assertContains(response, 'No fee has been defined for this student yet')
        self.assertEqual(response.context['summary']['label'], 'No fee')

    def test_UT_13_Fee__list_shows_every_student_with_totals(self):
        fee = make_fee(self.student, '50000')
        make_payment(fee, '50000')
        other = make_student(self.hostel, 'CSE2202', 'Divya S.')
        make_fee(other, '30000')
        response = self.client.get(reverse('fees:manage'))
        by_roll = {row['student'].roll_no: row for row in response.context['rows']}
        self.assertEqual(by_roll['CSE2201']['label'], 'Paid')
        self.assertEqual(by_roll['CSE2202']['label'], 'Due')
        self.assertEqual(response.context['totals']['outstanding'], 30000)
        self.assertContains(response, 'Rs. 80,000')

    def test_UT_13_Fee__list_can_be_searched_and_filtered(self):
        make_fee(self.student, '50000')
        other = make_student(self.hostel, 'CSE2202', 'Divya S.')
        make_fee(other, '30000')
        make_payment(other.fee_records.get(), '30000')
        def rolls(**params):
            response = self.client.get(reverse('fees:manage'), params)
            return [row['student'].roll_no for row in response.context['rows']]

        self.assertEqual(rolls(q='arjun'), ['CSE2201'])
        self.assertEqual(rolls(q='2202'), ['CSE2202'])
        self.assertEqual(rolls(status='paid'), ['CSE2202'])
        self.assertEqual(rolls(status='unpaid'), ['CSE2201'])
        self.assertEqual(sorted(rolls(status='nonsense')), ['CSE2201', 'CSE2202'])

    def test_UT_13_Fee__inactive_students_are_not_listed(self):
        self.student.is_active = False
        self.student.save()
        self.assertEqual(self.client.get(reverse('fees:manage')).context['rows'], [])

    # ---- defining (#67) -------------------------------------------------------------------
    def test_UT_FEE_04__valid_fee_is_created_for_the_student(self):
        response = self.define(due_date='2026-11-30')
        self.assertRedirects(response, reverse('fees:student_fees', args=[self.student.pk]))
        fee = FeeRecord.objects.get()
        self.assertEqual((fee.student, fee.hostel, fee.academic_year, fee.description, fee.amount_due),
                         (self.student, self.hostel, '2026-27', 'Hostel fee', 50000))
        self.assertEqual(fee.due_date, date(2026, 11, 30))
        self.assertContains(self.student_page(), 'Rs. 50,000')

    def test_UT_FEE_04__due_date_is_optional(self):
        self.define()
        self.assertIsNone(FeeRecord.objects.get().due_date)

    def test_UT_FEE_04__amount_must_be_a_positive_number(self):
        for value, text in (('0', 'Amount due must be greater than zero'),
                            ('-100', 'Amount due must be greater than zero'),
                            ('abc', 'Amount due must be a number'),
                            ('', 'Amount due is required'),
                            ('100.555', 'Amount due can have at most 2 decimal places'),
                            ('1000000000', 'Amount due must be at most')):
            with self.subTest(amount=value):
                self.assertContains(self.define(amount_due=value), text)
                self.assertEqual(FeeRecord.objects.count(), 0)

    def test_UT_FEE_04__academic_year_and_description_are_required_and_checked(self):
        self.assertContains(self.define(academic_year=''), 'Academic year is required')
        self.assertContains(self.define(academic_year='2026'), 'Academic year format is invalid')
        self.assertContains(self.define(description=''), 'Description is required')
        self.assertEqual(FeeRecord.objects.count(), 0)

    def test_UT_FEE_04__the_same_fee_cannot_be_defined_twice(self):
        make_fee(self.student)
        response = self.define(description='hostel FEE')
        self.assertContains(response, 'A fee with this academic year and description already exists')
        self.assertEqual(FeeRecord.objects.count(), 1)

    def test_UT_FEE_04__a_different_year_or_description_is_allowed(self):
        make_fee(self.student)
        self.define(academic_year='2027-28')
        self.define(description='Mess advance')
        self.assertEqual(FeeRecord.objects.count(), 3)

    def test_UT_FEE_04__fee_can_be_edited(self):
        fee = make_fee(self.student, '50000')
        response = self.client.post(reverse('fees:fee_edit', args=[fee.pk]), {
            'academic_year': '2026-27', 'description': 'Hostel fee', 'amount_due': '55000.50',
            'due_date': '2026-12-15'})
        self.assertRedirects(response, reverse('fees:student_fees', args=[self.student.pk]))
        fee.refresh_from_db()
        self.assertEqual(str(fee.amount_due), '55000.50')
        self.assertEqual(fee.due_date, date(2026, 12, 15))
        self.assertContains(self.student_page(), 'Rs. 55,000.50')

    def test_UT_FEE_04__edit_form_is_filled_with_the_current_values(self):
        fee = make_fee(self.student, '50000')
        response = self.client.get(reverse('fees:fee_edit', args=[fee.pk]))
        self.assertContains(response, 'value="2026-27"')
        self.assertContains(response, 'value="Hostel fee"')

    def test_UT_FEE_04__amount_cannot_drop_below_what_is_already_paid(self):
        fee = make_fee(self.student, '50000')
        make_payment(fee, '20000')
        response = self.client.post(reverse('fees:fee_edit', args=[fee.pk]), {
            'academic_year': '2026-27', 'description': 'Hostel fee', 'amount_due': '15000', 'due_date': ''})
        self.assertContains(response, 'Fee amount cannot be lower than the amount already paid (Rs. 20,000)')
        fee.refresh_from_db()
        self.assertEqual(fee.amount_due, 50000)

    def test_UT_FEE_04__editing_cannot_create_a_duplicate(self):
        make_fee(self.student, '50000')
        other = make_fee(self.student, '1000', description='Mess advance')
        response = self.client.post(reverse('fees:fee_edit', args=[other.pk]), {
            'academic_year': '2026-27', 'description': 'Hostel fee', 'amount_due': '1000', 'due_date': ''})
        self.assertContains(response, 'already exists for the student')

    def test_UT_FEE_04__service_rejects_a_non_positive_amount(self):
        with self.assertRaises(ValidationError):
            services.define_fee(self.student, academic_year='2026-27', description='X', amount_due=0)

    def test_UT_FEE_04__unknown_student_or_fee_is_a_404(self):
        self.assertEqual(self.client.get(reverse('fees:student_fees', args=[99999])).status_code, 404)
        self.assertEqual(self.client.get(reverse('fees:fee_edit', args=[99999])).status_code, 404)

    def test_IT_FEE_04__only_the_administrator_may_manage_fees(self):
        fee = make_fee(self.student)
        warden = make_account('warden_t', UserAccount.ROLE_WARDEN, self.hostel)
        for account in (warden, self.student.user_account):
            self.client.force_login(account.user)
            for name, args in (('manage', []), ('student_fees', [self.student.pk]),
                               ('fee_create', [self.student.pk]), ('fee_edit', [fee.pk])):
                with self.subTest(user=account.user.username, page=name):
                    self.assertEqual(self.client.get(reverse(f'fees:{name}', args=args)).status_code, 403)
        self.assertEqual(self.define().status_code, 403)
        self.assertEqual(FeeRecord.objects.count(), 1)

    def test_IT_FEE_04__anonymous_users_are_sent_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('fees:manage'))
        self.assertRedirects(response, '/login/?next=/fees/')

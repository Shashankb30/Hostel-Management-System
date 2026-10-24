"""Issue #79 (FR-05.13): outstanding dues report."""
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from core.models import UserAccount

from . import services
from .factories import make_account, make_fee, make_hostel, make_payment, make_student


class DuesReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = make_hostel()
        cls.admin = make_account('admin_t', UserAccount.ROLE_ADMIN, cls.hostel)
        today = date.today()
        cls.a = make_student(cls.hostel, 'CSE0001', 'Asha')          # partly paid, overdue
        cls.b = make_student(cls.hostel, 'CSE0002', 'Bala')          # nothing paid, not yet due
        cls.c = make_student(cls.hostel, 'CSE0003', 'Chitra')        # fully paid
        cls.d = make_student(cls.hostel, 'CSE0004', 'Deepak')        # no longer a resident
        cls.e = make_student(cls.hostel, 'CSE0005', 'Esha')          # no fee at all
        cls.fee_a = make_fee(cls.a, '50000', due_date=today - timedelta(days=10))
        make_payment(cls.fee_a, '20000')
        cls.fee_b = make_fee(cls.b, '40000', due_date=today + timedelta(days=30))
        cls.fee_c = make_fee(cls.c, '25000', due_date=today - timedelta(days=5))
        make_payment(cls.fee_c, '25000')
        cls.fee_d = make_fee(cls.d, '99000')
        cls.d.is_active = False
        cls.d.save()

    def setUp(self):
        self.client.force_login(self.admin.user)

    def report(self, **params):
        response = self.client.get(reverse('fees:dues_report'), params)
        self.assertEqual(response.status_code, 200)
        return response

    def rolls(self, **params):
        return [fee.student.roll_no for fee in self.report(**params).context['rows']]

    def test_ST_FEE_03__lists_only_fees_that_still_have_a_balance(self):
        self.assertEqual(self.rolls(), ['CSE0002', 'CSE0001'])

    def test_ST_FEE_03__largest_balance_comes_first(self):
        rows = self.report().context['rows']
        self.assertEqual([fee.outstanding for fee in rows], [40000, 30000])

    def test_ST_FEE_03__shows_amounts_paid_and_outstanding(self):
        response = self.report()
        for text in ('Asha', 'CSE0001', 'Rs. 50,000', 'Rs. 20,000', 'Rs. 30,000', 'Partially Paid', 'Due'):
            self.assertContains(response, text)

    def test_ST_FEE_03__total_outstanding_is_the_sum_of_the_rows(self):
        response = self.report()
        self.assertEqual(response.context['total'], 70000)
        self.assertContains(response, 'Rs. 70,000')

    def test_ST_FEE_03__paid_fees_residents_who_left_and_students_without_fees_are_left_out(self):
        rolls = self.rolls()
        for roll in ('CSE0003', 'CSE0004', 'CSE0005'):
            self.assertNotIn(roll, rolls)

    def test_ST_FEE_03__overdue_fees_are_flagged(self):
        by_roll = {fee.student.roll_no: fee.overdue for fee in self.report().context['rows']}
        self.assertEqual(by_roll, {'CSE0001': True, 'CSE0002': False})
        self.assertContains(self.report(), 'text-bg-danger">Overdue</span>')

    def test_ST_FEE_03__a_fee_without_a_due_date_is_never_overdue(self):
        make_fee(self.e, '1000')
        by_roll = {fee.student.roll_no: fee.overdue for fee in self.report().context['rows']}
        self.assertFalse(by_roll['CSE0005'])

    def test_ST_FEE_03__overdue_only_filter(self):
        self.assertEqual(self.rolls(overdue='1'), ['CSE0001'])
        self.assertTrue(self.report(overdue='1').context['overdue_only'])
        self.assertEqual(self.report(overdue='1').context['total'], 30000)

    def test_ST_FEE_03__a_fee_drops_off_the_report_once_it_is_paid(self):
        make_payment(self.fee_b, '40000')
        self.assertEqual(self.rolls(), ['CSE0001'])

    def test_ST_FEE_03__each_unpaid_fee_of_a_student_is_its_own_row(self):
        make_fee(self.a, '1000', description='Mess advance')
        rows = self.report().context['rows']
        self.assertEqual([fee.student.roll_no for fee in rows].count('CSE0001'), 2)

    def test_ST_FEE_03__empty_report_says_so(self):
        make_payment(self.fee_a, '30000')
        make_payment(self.fee_b, '40000')
        response = self.report()
        self.assertContains(response, 'No outstanding dues')
        self.assertEqual(response.context['total'], 0)

    def test_ST_FEE_03__csv_download_has_one_line_per_fee(self):
        response = self.client.get(reverse('fees:dues_report'), {'format': 'csv'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        lines = response.content.decode().strip().splitlines()
        self.assertEqual(lines[0].split(',')[0:3], ['Roll no', 'Student', 'Hostel'])
        self.assertEqual(len(lines), 3)
        self.assertIn('CSE0002,Bala', lines[1])
        self.assertTrue(lines[2].startswith('CSE0001,Asha'))
        self.assertTrue(lines[2].endswith('30000.00,yes'))

    def test_ST_FEE_03__csv_respects_the_overdue_filter(self):
        response = self.client.get(reverse('fees:dues_report'), {'format': 'csv', 'overdue': '1'})
        self.assertEqual(len(response.content.decode().strip().splitlines()), 2)

    def test_ST_FEE_03__report_is_reachable_from_fee_management(self):
        response = self.client.get(reverse('fees:manage'))
        self.assertContains(response, reverse('fees:dues_report'))

    def test_ST_FEE_03__service_returns_rows_and_total(self):
        rows, total = services.dues_report()
        self.assertEqual((len(rows), total), (2, 70000))

    def test_ST_FEE_03__only_the_administrator_can_open_the_report(self):
        warden = make_account('warden_t', UserAccount.ROLE_WARDEN, self.hostel)
        for account in (warden, self.a.user_account):
            self.client.force_login(account.user)
            self.assertEqual(self.client.get(reverse('fees:dues_report')).status_code, 403)
            self.assertEqual(self.client.get(reverse('fees:dues_report'), {'format': 'csv'}).status_code, 403)
        self.client.logout()
        response = self.client.get(reverse('fees:dues_report'))
        self.assertRedirects(response, '/login/?next=/fees/dues/')

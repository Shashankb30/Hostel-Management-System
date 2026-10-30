"""Issues #75, #76 (FR-05.09, FR-05.10): students see their own fees; history in date order."""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from core.models import UserAccount
from core.navigation import build_menu

from . import services
from .factories import make_account, make_fee, make_hostel, make_payment, make_student, submit_payment


class StudentFeesViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = make_hostel()
        cls.admin = make_account('admin_t', UserAccount.ROLE_ADMIN, cls.hostel)
        cls.warden = make_account('warden_t', UserAccount.ROLE_WARDEN, cls.hostel)
        cls.student = make_student(cls.hostel, 'CSE2201', 'Arjun Rao')
        cls.other = make_student(cls.hostel, 'CSE2202', 'Divya S.')

    def setUp(self):
        self.fee = make_fee(self.student, '50000')

    def my_fees(self, student=None):
        self.client.force_login((student or self.student).user_account.user)
        return self.client.get(reverse('fees:my_fees'))

    def test_IT_15_Fee__student_sees_the_payment_recorded_by_the_administrator(self):
        self.client.force_login(self.admin.user)
        before = self.my_fees()
        self.assertContains(before, 'text-bg-danger">Due</span>')
        self.assertContains(before, 'Rs. 50,000')

        self.client.force_login(self.admin.user)
        submit_payment(self.client, self.fee, amount='20000', mode='online', reference='UPI 77')
        after = self.my_fees()
        self.assertContains(after, 'text-bg-warning">Partially Paid</span>')
        self.assertContains(after, 'Rs. 30,000')
        self.assertContains(after, 'Rs. 20,000')
        self.assertContains(after, 'Online')
        self.assertContains(after, 'UPI 77')

    def test_IT_15_Fee__student_sees_paid_once_the_fee_is_cleared(self):
        make_payment(self.fee, '50000')
        response = self.my_fees()
        self.assertContains(response, 'text-bg-success">Paid</span>')
        self.assertEqual(response.context['summary']['outstanding'], 0)

    def test_IT_15_Fee__summary_matches_what_the_administrator_sees(self):
        make_payment(self.fee, '12345.50')
        mine = self.my_fees().context['summary']
        self.client.force_login(self.admin.user)
        theirs = self.client.get(reverse('fees:student_fees', args=[self.student.pk])).context['summary']
        for key in ('total', 'paid', 'outstanding', 'label'):
            self.assertEqual(mine[key], theirs[key])

    def test_ST_09_Fee__history_lists_every_payment_oldest_first(self):
        make_payment(self.fee, '10000', paid_on=date(2026, 10, 25), mode='card')
        make_payment(self.fee, '20000', paid_on=date(2026, 10, 10), mode='cash')
        make_payment(self.fee, '5000', paid_on=date(2026, 10, 18), mode='online')
        history = self.my_fees().context['history']
        self.assertEqual([(p.paid_on.day, p.amount, p.mode) for p in history],
                         [(10, 20000, 'cash'), (18, 5000, 'online'), (25, 10000, 'card')])

    def test_ST_09_Fee__page_shows_dates_amounts_and_modes_in_that_order(self):
        make_payment(self.fee, '10000', paid_on=date(2026, 10, 25), mode='card')
        make_payment(self.fee, '20000', paid_on=date(2026, 10, 10), mode='cash')
        html = self.my_fees().content.decode()
        self.assertLess(html.index('10 Oct 2026'), html.index('25 Oct 2026'))
        for text in ('Rs. 20,000', 'Rs. 10,000', 'Cash', 'Card'):
            self.assertIn(text, html)

    def test_ST_09_Fee__each_row_shows_the_balance_after_that_payment(self):
        make_payment(self.fee, '10000', paid_on=date(2026, 10, 25))
        make_payment(self.fee, '20000', paid_on=date(2026, 10, 10))
        history = self.my_fees().context['history']
        self.assertEqual([p.balance_after for p in history], [30000, 20000])

    def test_ST_09_Fee__same_day_payments_keep_the_order_they_were_entered(self):
        first = make_payment(self.fee, '1000', paid_on=date(2026, 10, 10))
        second = make_payment(self.fee, '2000', paid_on=date(2026, 10, 10))
        history = services.payment_history(self.student)
        self.assertEqual([p.pk for p in history], [first.pk, second.pk])

    def test_ST_09_Fee__history_rows_link_to_their_receipts(self):
        payment = make_payment(self.fee, '1000')
        response = self.my_fees()
        self.assertContains(response, reverse('fees:receipt', args=[payment.pk]))
        self.assertContains(response, f'RCP-{payment.pk:06d}')

    def test_ST_09_Fee__administrator_sees_the_same_history_for_the_student(self):
        make_payment(self.fee, '10000', paid_on=date(2026, 10, 25))
        make_payment(self.fee, '20000', paid_on=date(2026, 10, 10))
        self.client.force_login(self.admin.user)
        response = self.client.get(reverse('fees:student_fees', args=[self.student.pk]))
        self.assertEqual([p.amount for p in response.context['history']], [20000, 10000])

    def test_ST_09_Fee__student_without_payments_sees_an_empty_history(self):
        self.assertContains(self.my_fees(), 'No payments recorded yet')

    def test_IT_FEE_04__a_student_sees_only_their_own_fees_and_payments(self):
        make_payment(self.fee, '1000')
        other_fee = make_fee(self.other, '99000', description='Other fee')
        make_payment(other_fee, '7777')
        response = self.my_fees()
        self.assertContains(response, 'Hostel fee')
        self.assertNotContains(response, 'Other fee')
        self.assertNotContains(response, 'Rs. 7,777')
        self.assertNotContains(response, 'Divya')

    def test_IT_FEE_04__student_with_no_fee_is_told_so(self):
        self.assertContains(self.my_fees(self.other), 'No fee has been defined for you yet')

    def test_IT_FEE_04__account_without_a_student_record_gets_a_message(self):
        lonely = make_account('lonely', UserAccount.ROLE_STUDENT, self.hostel)
        self.client.force_login(lonely.user)
        self.assertContains(self.client.get(reverse('fees:my_fees')), 'student record is not set up')

    def test_IT_FEE_04__wardens_and_administrators_have_no_my_fees_page(self):
        for account in (self.warden, self.admin):
            self.client.force_login(account.user)
            self.assertEqual(self.client.get(reverse('fees:my_fees')).status_code, 403)

    def test_IT_FEE_04__anonymous_users_are_sent_to_login(self):
        response = self.client.get(reverse('fees:my_fees'))
        self.assertRedirects(response, '/login/?next=/fees/my/')

    def test_IT_FEE_04__receipt_links_back_to_the_right_page_for_each_role(self):
        payment = make_payment(self.fee, '1000')
        self.client.force_login(self.student.user_account.user)
        self.assertContains(self.client.get(reverse('fees:receipt', args=[payment.pk])), 'Back to my fees')
        self.client.force_login(self.admin.user)
        self.assertContains(self.client.get(reverse('fees:receipt', args=[payment.pk])), 'Back to student fees')

    def test_IT_FEE_04__menu_links_lead_to_the_fee_pages(self):
        links = {role: {item['label']: item['url'] for item in build_menu(role)}
                 for role in ('student', 'admin')}
        self.assertEqual(links['student']['Fees & Payments'], reverse('fees:my_fees'))
        self.assertEqual(links['admin']['Fees'], reverse('fees:manage'))

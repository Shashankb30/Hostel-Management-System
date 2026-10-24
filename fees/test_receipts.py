"""Issue #74 (FR-05.08): a receipt is generated for every payment."""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from core.models import Payment, UserAccount

from . import services
from .factories import make_account, make_fee, make_hostel, make_payment, make_student, submit_payment


class ReceiptTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = make_hostel()
        cls.admin = make_account('admin_t', UserAccount.ROLE_ADMIN, cls.hostel)
        cls.warden = make_account('warden_t', UserAccount.ROLE_WARDEN, cls.hostel)
        cls.student = make_student(cls.hostel, 'CSE2201', 'Arjun Rao')
        cls.other = make_student(cls.hostel, 'CSE2202', 'Divya S.')

    def setUp(self):
        self.client.force_login(self.admin.user)
        self.fee = make_fee(self.student, '50000')

    def receipt_url(self, payment):
        return reverse('fees:receipt', args=[payment.pk])

    def test_UT_FEE_06__saving_a_payment_opens_its_receipt(self):
        response = submit_payment(self.client, self.fee, amount='50000', mode='online')
        payment = Payment.objects.get()
        self.assertRedirects(response, self.receipt_url(payment))

    def test_UT_FEE_06__receipt_shows_the_payment_details(self):
        payment = make_payment(self.fee, '20000', paid_on=date(2026, 10, 20), mode='online',
                               reference='UPI 4411')
        payment.received_by = self.admin
        payment.save()
        response = self.client.get(self.receipt_url(payment))
        self.assertEqual(response.status_code, 200)
        for text in (f'RCP-{payment.pk:06d}', 'Arjun Rao', 'CSE2201', 'Hostel fee, 2026-27',
                     '20 Oct 2026', 'Online', 'UPI 4411', 'Rs. 20,000', 'Rs. 50,000',
                     'Rs. 30,000', self.hostel.name, 'admin_t'):
            self.assertContains(response, text)

    def test_UT_FEE_06__receipt_numbers_are_unique_and_follow_the_payment(self):
        first = make_payment(self.fee, '1000')
        second = make_payment(self.fee, '2000')
        self.assertNotEqual(services.receipt_number(first), services.receipt_number(second))
        self.assertEqual(services.receipt_number(first), f'RCP-{first.pk:06d}')

    def test_UT_FEE_06__balance_after_each_payment_follows_the_payment_dates(self):
        later = make_payment(self.fee, '10000', paid_on=date(2026, 10, 25))
        earlier = make_payment(self.fee, '20000', paid_on=date(2026, 10, 20))
        self.assertEqual(services.balance_after(earlier), 30000)
        self.assertEqual(services.balance_after(later), 20000)

    def test_UT_FEE_06__same_day_payments_are_ordered_by_entry(self):
        first = make_payment(self.fee, '10000', paid_on=date(2026, 10, 20))
        second = make_payment(self.fee, '5000', paid_on=date(2026, 10, 20))
        self.assertEqual(services.balance_after(first), 40000)
        self.assertEqual(services.balance_after(second), 35000)

    def test_UT_FEE_06__receipt_of_a_fully_paid_fee_shows_zero_balance(self):
        payment = make_payment(self.fee, '50000')
        self.assertContains(self.client.get(self.receipt_url(payment)), 'Rs. 0')

    def test_UT_FEE_06__receipt_without_a_reference_hides_the_reference_line(self):
        payment = make_payment(self.fee, '1000')
        self.assertNotContains(self.client.get(self.receipt_url(payment)), 'Reference')

    def test_UT_FEE_06__unknown_receipt_is_a_404(self):
        self.assertEqual(self.client.get(reverse('fees:receipt', args=[99999])).status_code, 404)

    def test_IT_FEE_04__a_student_can_open_their_own_receipt(self):
        payment = make_payment(self.fee, '1000')
        self.client.force_login(self.student.user_account.user)
        response = self.client.get(self.receipt_url(payment))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'RCP-')

    def test_IT_FEE_04__a_student_cannot_open_someone_elses_receipt(self):
        payment = make_payment(make_fee(self.other, '30000'), '1000')
        self.client.force_login(self.student.user_account.user)
        self.assertEqual(self.client.get(self.receipt_url(payment)).status_code, 404)

    def test_IT_FEE_04__wardens_and_visitors_cannot_open_receipts(self):
        payment = make_payment(self.fee, '1000')
        self.client.force_login(self.warden.user)
        self.assertEqual(self.client.get(self.receipt_url(payment)).status_code, 403)
        self.client.logout()
        response = self.client.get(self.receipt_url(payment))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

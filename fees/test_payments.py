"""Issues #69 to #73, #78 (FR-05.03 to FR-05.07, FR-05.12): record payments and compute status."""
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import FeeRecord, Payment, UserAccount

from . import services
from .factories import make_account, make_fee, make_hostel, make_payment, make_student, submit_payment


class RecordPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = make_hostel()
        cls.admin = make_account('admin_t', UserAccount.ROLE_ADMIN, cls.hostel)
        cls.student = make_student(cls.hostel, 'CSE2201', 'Arjun Rao')

    def setUp(self):
        self.client.force_login(self.admin.user)
        self.fee = make_fee(self.student, '50000')

    def pay(self, amount, **data):
        return submit_payment(self.client, self.fee, amount=amount, **data)

    def summary(self):
        return services.student_summary(self.student)

    # ---- full and partial payments (#69, #70, #73) ----------------------------------------
    def test_UT_14_Fee__full_payment_marks_the_fee_paid(self):
        response = self.pay('50000', mode='online')
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get()
        self.assertEqual((payment.amount, payment.mode, payment.fee_record), (50000, 'online', self.fee))
        summary = self.summary()
        self.assertEqual((summary['label'], summary['outstanding']), ('Paid', 0))

    def test_UT_14_Fee__paid_status_is_shown_on_the_student_page(self):
        self.pay('50000', mode='online')
        response = self.client.get(reverse('fees:student_fees', args=[self.student.pk]))
        self.assertContains(response, 'text-bg-success">Paid</span>')
        self.assertNotContains(response, 'Record payment')

    def test_UT_14_Fee__the_payment_is_recorded_by_the_logged_in_administrator(self):
        self.pay('50000', mode='online')
        self.assertEqual(Payment.objects.get().received_by, self.admin)

    def test_UT_15_Fee__partial_payment_marks_the_fee_partially_paid(self):
        self.pay('20000', mode='cash')
        summary = self.summary()
        self.assertEqual((summary['label'], summary['paid'], summary['outstanding']),
                         ('Partially Paid', 20000, 30000))
        self.assertContains(self.client.get(reverse('fees:student_fees', args=[self.student.pk])),
                            'Rs. 30,000')

    def test_UT_15_Fee__several_payments_add_up_until_the_fee_is_paid(self):
        for amount, label, outstanding in (('10000', 'Partially Paid', 40000),
                                           ('15000', 'Partially Paid', 25000),
                                           ('25000', 'Paid', 0)):
            with self.subTest(amount=amount):
                self.pay(amount)
                summary = self.summary()
                self.assertEqual((summary['label'], summary['outstanding']), (label, outstanding))
        self.assertEqual(Payment.objects.count(), 3)

    def test_UT_15_Fee__paise_are_kept(self):
        self.pay('1234.50')
        self.assertEqual(Payment.objects.get().amount, Decimal('1234.50'))
        self.assertEqual(self.summary()['outstanding'], Decimal('48765.50'))

    def test_UT_15_Fee__reference_and_date_are_saved(self):
        self.pay('1000', paid_on='2026-10-20', reference='UPI 4411')
        payment = Payment.objects.get()
        self.assertEqual((payment.paid_on, payment.reference), (date(2026, 10, 20), 'UPI 4411'))

    def test_UT_15_Fee__payment_form_shows_the_outstanding_balance(self):
        make_payment(self.fee, '20000')
        response = self.client.get(reverse('fees:payment_create', args=[self.fee.pk]))
        self.assertContains(response, 'Outstanding balance: Rs. 30,000')

    # ---- rejecting bad amounts (#71, #72) -------------------------------------------------
    def test_IT_13_Fee__payment_above_the_balance_is_rejected(self):
        make_payment(self.fee, '40000')                       # balance is now Rs. 10,000
        response = self.pay('15000')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Payment amount cannot exceed the outstanding balance of Rs. 10,000')
        self.assertEqual(Payment.objects.count(), 1)

    def test_IT_13_Fee__paying_exactly_the_balance_is_allowed(self):
        make_payment(self.fee, '40000')
        self.assertEqual(self.pay('10000').status_code, 302)
        self.assertEqual(self.summary()['label'], 'Paid')

    def test_IT_13_Fee__one_paisa_over_is_rejected(self):
        self.assertContains(self.pay('50000.01'), 'cannot exceed the outstanding balance')
        self.assertEqual(Payment.objects.count(), 0)

    def test_IT_13_Fee__a_fully_paid_fee_takes_no_more_payments(self):
        make_payment(self.fee, '50000')
        response = self.client.get(reverse('fees:payment_create', args=[self.fee.pk]), follow=True)
        self.assertContains(response, 'This fee is already fully paid')
        with self.assertRaises(ValidationError) as ctx:
            services.record_payment(self.fee, amount=Decimal('1'), mode='cash')
        self.assertEqual(ctx.exception.messages, ['This fee is already fully paid'])

    def test_IT_13_Fee__service_blocks_an_overpayment_too(self):
        with self.assertRaises(ValidationError) as ctx:
            services.record_payment(self.fee, amount=Decimal('50001'), mode='cash')
        self.assertEqual(ctx.exception.messages,
                         ['Payment amount cannot exceed the outstanding balance of Rs. 50,000'])
        self.assertEqual(Payment.objects.count(), 0)

    def test_IT_14_Fee__negative_zero_and_text_amounts_are_rejected(self):
        for value, text in (('-500', 'Amount must be greater than zero'),
                            ('0', 'Amount must be greater than zero'),
                            ('abc', 'Amount must be a number'),
                            ('12abc', 'Amount must be a number'),
                            ('', 'Amount is required'),
                            ('   ', 'Amount is required'),
                            ('10.255', 'Amount can have at most 2 decimal places'),
                            ('1000000000', 'Amount must be at most')):
            with self.subTest(amount=value):
                response = self.pay(value)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, text)
                self.assertEqual(Payment.objects.count(), 0)

    def test_IT_14_Fee__service_rejects_a_non_positive_amount(self):
        for amount in (Decimal('-5'), Decimal('0')):
            with self.assertRaises(ValidationError):
                services.record_payment(self.fee, amount=amount, mode='cash')
        self.assertEqual(Payment.objects.count(), 0)

    def test_IT_14_Fee__payment_date_cannot_be_in_the_future(self):
        later = (timezone.localdate() + timedelta(days=2)).isoformat()
        self.assertContains(self.pay('1000', paid_on=later), 'Payment date cannot be in the future')
        self.assertEqual(Payment.objects.count(), 0)

    def test_IT_14_Fee__payment_date_is_required_and_must_be_a_date(self):
        self.assertContains(self.pay('1000', paid_on=''), 'Payment date is required')
        self.assertContains(self.pay('1000', paid_on='not-a-date'), 'Payment date format is invalid')

    # ---- payment mode (#78) ---------------------------------------------------------------
    def test_UT_FEE_05__every_payment_mode_is_accepted_and_saved(self):
        for index, (mode, label) in enumerate(Payment.MODE_CHOICES, start=1):
            with self.subTest(mode=mode):
                self.pay(str(index * 100), mode=mode)
                self.assertEqual(Payment.objects.get(amount=index * 100).mode, mode)
                self.assertEqual(Payment.objects.get(amount=index * 100).get_mode_display(), label)

    def test_UT_FEE_05__mode_is_required(self):
        self.assertContains(self.pay('1000', mode=''), 'Payment mode is required')
        self.assertEqual(Payment.objects.count(), 0)

    def test_UT_FEE_05__unknown_mode_is_rejected(self):
        self.assertContains(self.pay('1000', mode='barter'), 'Payment mode is not a valid choice')
        self.assertEqual(Payment.objects.count(), 0)

    def test_UT_FEE_05__service_rejects_an_unknown_mode(self):
        with self.assertRaises(ValidationError):
            services.record_payment(self.fee, amount=Decimal('10'), mode='barter')

    # ---- status calculation (#73) ---------------------------------------------------------
    def test_UT_FEE_07__status_follows_the_amount_paid(self):
        self.assertEqual(services.status_of(Decimal('100'), Decimal('0')), 'unpaid')
        self.assertEqual(services.status_of(Decimal('100'), Decimal('0.01')), 'partially_paid')
        self.assertEqual(services.status_of(Decimal('100'), Decimal('99.99')), 'partially_paid')
        self.assertEqual(services.status_of(Decimal('100'), Decimal('100')), 'paid')
        self.assertEqual(services.status_of(Decimal('0'), Decimal('0')), 'none')
        self.assertEqual([services.STATUS_LABELS[s] for s in ('unpaid', 'partially_paid', 'paid')],
                         ['Due', 'Partially Paid', 'Paid'])

    def test_UT_FEE_07__status_agrees_with_the_model_property(self):
        def both():
            fee = FeeRecord.objects.get(pk=self.fee.pk)
            described = services.describe_fee(services.fees_with_paid().get(pk=fee.pk))
            return described.status, fee.fee_status

        self.assertEqual(both(), ('unpaid', 'unpaid'))
        make_payment(self.fee, '100')
        self.assertEqual(both(), ('partially_paid', 'partially_paid'))
        make_payment(self.fee, '49900')
        self.assertEqual(both(), ('paid', 'paid'))

    def test_UT_FEE_07__each_fee_has_its_own_status(self):
        other = make_fee(self.student, '1000', description='Mess advance')
        make_payment(other, '1000')
        by_description = {fee.description: fee.status_label for fee in self.summary()['fees']}
        self.assertEqual(by_description, {'Hostel fee': 'Due', 'Mess advance': 'Paid'})

    # ---- who may record payments ---------------------------------------------------------
    def test_IT_FEE_04__only_the_administrator_records_payments(self):
        warden = make_account('warden_t', UserAccount.ROLE_WARDEN, self.hostel)
        url = reverse('fees:payment_create', args=[self.fee.pk])
        for account in (warden, self.student.user_account):
            self.client.force_login(account.user)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {'amount': '100', 'mode': 'cash'}).status_code, 403)
        self.assertEqual(Payment.objects.count(), 0)

    def test_IT_FEE_04__unknown_fee_is_a_404(self):
        self.assertEqual(self.client.get(reverse('fees:payment_create', args=[99999])).status_code, 404)

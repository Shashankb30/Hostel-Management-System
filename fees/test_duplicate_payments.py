"""Issue #77 (FR-05.11): the same payment cannot be saved twice by accident."""
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Payment, UserAccount

from . import services
from .factories import make_account, make_fee, make_hostel, make_student, submit_payment


class DuplicatePaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = make_hostel()
        cls.admin = make_account('admin_t', UserAccount.ROLE_ADMIN, cls.hostel)
        cls.student = make_student(cls.hostel, 'CSE2201', 'Arjun Rao')

    def setUp(self):
        self.client.force_login(self.admin.user)
        self.fee = make_fee(self.student, '50000')
        self.url = reverse('fees:payment_create', args=[self.fee.pk])

    def open_form(self):
        return self.client.get(self.url).context['token']

    def save(self, token, **data):
        payload = {'amount': '1000', 'mode': 'cash', 'paid_on': date.today().isoformat(),
                   'reference': '', 'submission_token': token}
        payload.update(data)
        return self.client.post(self.url, payload)

    def test_ST_10_Fee__saving_the_same_form_twice_records_one_payment(self):
        token = self.open_form()
        first = self.save(token)
        self.assertEqual(first.status_code, 302)
        second = self.save(token)
        self.assertRedirects(second, reverse('fees:student_fees', args=[self.student.pk]))
        self.assertEqual(Payment.objects.count(), 1)

    def test_ST_10_Fee__the_second_attempt_shows_a_warning(self):
        token = self.open_form()
        self.save(token)
        response = self.client.post(self.url, {
            'amount': '1000', 'mode': 'cash', 'paid_on': date.today().isoformat(),
            'submission_token': token}, follow=True)
        self.assertContains(response, 'This payment was already submitted')
        self.assertEqual(Payment.objects.count(), 1)

    def test_ST_10_Fee__a_double_click_cannot_pay_twice(self):
        token = self.open_form()
        for _ in range(3):
            self.save(token)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(services.outstanding_of(self.fee), 49000)

    def test_ST_10_Fee__a_post_without_a_token_is_refused(self):
        response = self.client.post(self.url, {
            'amount': '1000', 'mode': 'cash', 'paid_on': date.today().isoformat()}, follow=True)
        self.assertContains(response, 'This payment was already submitted')
        self.assertEqual(Payment.objects.count(), 0)

    def test_ST_10_Fee__an_unknown_token_is_refused(self):
        self.open_form()
        self.assertEqual(self.save('made-up-token').status_code, 302)
        self.assertEqual(Payment.objects.count(), 0)

    def test_ST_10_Fee__every_opening_of_the_form_gets_its_own_token(self):
        self.assertNotEqual(self.open_form(), self.open_form())

    def test_ST_10_Fee__a_mistake_does_not_use_up_the_token(self):
        token = self.open_form()
        self.assertEqual(self.save(token, amount='abc').status_code, 200)
        self.assertEqual(self.save(token, amount='999999').status_code, 200)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(self.save(token, amount='1500').status_code, 302)
        self.assertEqual(Payment.objects.get().amount, 1500)

    def test_ST_10_Fee__two_forms_opened_one_after_the_other_both_work_once(self):
        first, second = self.open_form(), self.open_form()
        self.save(second, amount='2000')
        self.save(first, amount='3000')
        self.assertEqual(sorted(p.amount for p in Payment.objects.all()), [2000, 3000])

    def test_ST_10_Fee__only_the_most_recent_forms_stay_open(self):
        tokens = [self.open_form() for _ in range(25)]
        self.assertEqual(self.save(tokens[0]).status_code, 302)       # refused: redirected away
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(self.save(tokens[-1]).status_code, 302)
        self.assertEqual(Payment.objects.count(), 1)

    def test_ST_10_Fee__an_identical_payment_moments_later_is_blocked_even_with_a_new_form(self):
        self.assertEqual(submit_payment(self.client, self.fee, amount='1000').status_code, 302)
        response = submit_payment(self.client, self.fee, amount='1000')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This payment was already submitted')
        self.assertEqual(Payment.objects.count(), 1)

    def test_ST_10_Fee__a_different_amount_mode_or_date_is_allowed_straight_away(self):
        submit_payment(self.client, self.fee, amount='1000')
        submit_payment(self.client, self.fee, amount='1001')
        submit_payment(self.client, self.fee, amount='1000', mode='online')
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        submit_payment(self.client, self.fee, amount='1000', paid_on=yesterday)
        self.assertEqual(Payment.objects.count(), 4)

    def test_ST_10_Fee__the_same_payment_is_allowed_again_after_the_waiting_period(self):
        submit_payment(self.client, self.fee, amount='1000')
        Payment.objects.update(created_at=timezone.now() - services.DUPLICATE_WINDOW - timedelta(seconds=1))
        self.assertEqual(submit_payment(self.client, self.fee, amount='1000').status_code, 302)
        self.assertEqual(Payment.objects.count(), 2)

    def test_ST_10_Fee__the_service_itself_blocks_an_immediate_repeat(self):
        services.record_payment(self.fee, amount=Decimal('1000'), mode='cash')
        with self.assertRaises(ValidationError) as ctx:
            services.record_payment(self.fee, amount=Decimal('1000'), mode='cash')
        self.assertIn('already submitted', ctx.exception.messages[0])
        self.assertEqual(Payment.objects.count(), 1)

    def test_ST_10_Fee__a_blocked_repeat_does_not_hide_the_overpayment_check(self):
        submit_payment(self.client, self.fee, amount='49000')
        response = submit_payment(self.client, self.fee, amount='5000')
        self.assertContains(response, 'cannot exceed the outstanding balance of Rs. 1,000')

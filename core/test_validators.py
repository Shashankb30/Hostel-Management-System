from datetime import date, datetime
from decimal import Decimal

from django import forms
from django.contrib.messages import constants, get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages.utils import get_level_tags
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase

from .error_messages import MESSAGES, msg
from .feedback import flash_errors
from .models import Hostel, Room, Student, UserAccount
from .validators import (
    ErrorCollector,
    NumericValidator,
    PhoneValidator,
    RegexFormatValidator,
    RequiredValidator,
    validate_date_range,
    validate_unique,
)


def message_of(rule, *args, **kwargs):
    """Return the single error message a rule raises, or None if it passes."""
    try:
        rule(*args, **kwargs)
    except ValidationError as exc:
        return exc.messages[0]
    return None


def code_of(rule, *args, **kwargs):
    try:
        rule(*args, **kwargs)
    except ValidationError as exc:
        return exc.error_list[0].code
    return None


class MessageCatalogueTests(SimpleTestCase):
    def test_standard_wording_matches_test_plan(self):
        self.assertEqual(msg('unique', field='Room number'), 'Room number already exists')
        self.assertEqual(msg('unique', field='Roll number'), 'Roll number already exists')
        self.assertEqual(msg('invalid_credentials'), 'Invalid username or password')
        self.assertEqual(msg('room_unavailable'), 'Room unavailable')
        self.assertEqual(msg('no_vacant_rooms'), 'No vacant rooms available')

    def test_first_letter_is_capitalised(self):
        self.assertEqual(msg('unique', field='roll number'), 'Roll number already exists')

    def test_field_defaults_when_missing(self):
        self.assertEqual(msg('required'), 'This field is required')

    def test_unknown_key_and_missing_param_fail_loudly(self):
        with self.assertRaises(KeyError):
            msg('no_such_message')
        with self.assertRaises(ValueError):
            msg('date_range', start='From date')

    def test_messages_have_no_trailing_full_stop(self):
        for key, text in MESSAGES.items():
            self.assertFalse(text.endswith('.'), key)


class RequiredValidatorTests(SimpleTestCase):
    def test_blank_values_fail(self):
        for value in (None, '', '   ', [], {}):
            with self.subTest(value=value):
                self.assertEqual(message_of(RequiredValidator('Name'), value), 'Name is required')

    def test_present_values_pass(self):
        for value in ('x', 0, False, '0', ['a']):
            with self.subTest(value=value):
                self.assertIsNone(message_of(RequiredValidator('Name'), value))

    def test_code(self):
        self.assertEqual(code_of(RequiredValidator('Name'), ''), 'required')


class NumericValidatorTests(SimpleTestCase):
    def test_numbers_pass(self):
        check = NumericValidator('Amount')
        for value in (5, '5', ' 5 ', 5.5, '5.50', Decimal('5.5'), 0, -3):
            with self.subTest(value=value):
                self.assertIsNone(message_of(check, value))

    def test_non_numbers_fail(self):
        check = NumericValidator('Amount')
        for value in ('abc', '5x', True, 'NaN', 'Infinity', float('inf')):
            with self.subTest(value=value):
                self.assertEqual(message_of(check, value), 'Amount must be a number')

    def test_blank_is_skipped(self):
        self.assertIsNone(message_of(NumericValidator('Amount'), ''))
        self.assertIsNone(message_of(NumericValidator('Amount'), None))

    def test_integer_only(self):
        check = NumericValidator('Capacity', integer=True)
        self.assertIsNone(message_of(check, '3'))
        self.assertIsNone(message_of(check, '3.0'))
        self.assertEqual(message_of(check, '3.5'), 'Capacity must be a whole number')

    def test_positive(self):
        check = NumericValidator('Capacity', positive=True)
        self.assertEqual(message_of(check, 0), 'Capacity must be greater than zero')
        self.assertEqual(message_of(check, -2), 'Capacity must be greater than zero')
        self.assertIsNone(message_of(check, 1))

    def test_limits(self):
        check = NumericValidator('Year', min_value=1, max_value=6)
        self.assertEqual(message_of(check, 0), 'Year must be at least 1')
        self.assertEqual(message_of(check, 7), 'Year must be at most 6')
        self.assertIsNone(message_of(check, 1))
        self.assertIsNone(message_of(check, 6))

    def test_is_deconstructible_for_model_fields(self):
        path, args, kwargs = NumericValidator('Year', min_value=1).deconstruct()
        self.assertEqual(path, 'core.validators.NumericValidator')
        self.assertEqual(kwargs['min_value'], 1)


class FormatValidatorTests(SimpleTestCase):
    def test_phone(self):
        check = PhoneValidator()
        self.assertIsNone(message_of(check, '9876543210'))
        for value in ('98765', '98765432101', 'abcdefghij', '98765 43210'):
            with self.subTest(value=value):
                self.assertEqual(message_of(check, value), 'Phone number must be exactly 10 digits')

    def test_phone_blank_is_skipped(self):
        self.assertIsNone(message_of(PhoneValidator(), ''))

    def test_custom_pattern(self):
        check = RegexFormatValidator(r'[A-Z]{3}\d{4}', 'Roll number')
        self.assertIsNone(message_of(check, 'CSE2201'))
        self.assertEqual(message_of(check, 'cse2201'), 'Roll number format is invalid')


class DateRangeTests(SimpleTestCase):
    def test_valid_range(self):
        self.assertIsNone(message_of(validate_date_range, date(2026, 11, 1), date(2026, 11, 5)))

    def test_same_day_allowed_by_default(self):
        self.assertIsNone(message_of(validate_date_range, date(2026, 11, 1), date(2026, 11, 1)))

    def test_end_before_start_fails_with_labels(self):
        self.assertEqual(
            message_of(validate_date_range, date(2026, 11, 5), date(2026, 11, 1),
                       'From date', 'To date'),
            'To date cannot be before From date')

    def test_strict_mode_rejects_equal(self):
        self.assertEqual(
            message_of(validate_date_range, date(2026, 11, 1), date(2026, 11, 1),
                       'Publish time', 'Expiry time', allow_equal=False),
            'Expiry time must be after Publish time')

    def test_blank_dates_are_skipped(self):
        self.assertIsNone(message_of(validate_date_range, None, date(2026, 11, 1)))
        self.assertIsNone(message_of(validate_date_range, date(2026, 11, 1), None))

    def test_datetimes_work(self):
        self.assertEqual(
            code_of(validate_date_range, datetime(2026, 11, 1, 10), datetime(2026, 11, 1, 9)),
            'date_range')

    def test_error_can_be_attached_to_a_field(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_date_range(date(2026, 11, 5), date(2026, 11, 1), field='to_date')
        self.assertIn('to_date', ctx.exception.error_dict)


class UniqueValidatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = Hostel.objects.create(name='Main Hostel', code='MAIN')
        cls.other = Hostel.objects.create(name='Other Hostel', code='OTH')
        cls.room = Room.objects.create(hostel=cls.hostel, room_no='A-101', capacity=3)

    def test_duplicate_room_number_in_same_hostel_fails(self):
        self.assertEqual(
            message_of(validate_unique, Room.objects, 'room_no', 'A-101',
                       'Room number', hostel=self.hostel),
            'Room number already exists')

    def test_same_room_number_in_another_hostel_is_allowed(self):
        self.assertIsNone(message_of(validate_unique, Room.objects, 'room_no', 'A-101',
                                     'Room number', hostel=self.other))

    def test_new_value_passes(self):
        self.assertIsNone(message_of(validate_unique, Room.objects, 'room_no', 'Z-999',
                                     'Room number', hostel=self.hostel))

    def test_editing_a_record_does_not_clash_with_itself(self):
        self.assertIsNone(message_of(validate_unique, Room.objects, 'room_no', 'A-101',
                                     'Room number', exclude_pk=self.room.pk, hostel=self.hostel))

    def test_case_insensitive_option(self):
        self.assertIsNone(message_of(validate_unique, Room.objects, 'room_no', 'a-101',
                                     'Room number', hostel=self.hostel))
        self.assertEqual(
            message_of(validate_unique, Room.objects, 'room_no', 'a-101', 'Room number',
                       case_insensitive=True, hostel=self.hostel),
            'Room number already exists')

    def test_blank_value_is_skipped(self):
        self.assertIsNone(message_of(validate_unique, Room.objects, 'room_no', '',
                                     'Room number', hostel=self.hostel))

    def test_duplicate_roll_number_message(self):
        account = UserAccount.objects.create(
            user=self._make_user('stu_unique'), role=UserAccount.ROLE_STUDENT, hostel=self.hostel)
        Student.objects.create(
            user_account=account, hostel=self.hostel, roll_no='CSE2201', full_name='Arjun Rao',
            phone='9876543210', course='CSE', year_of_study=2)
        self.assertEqual(
            message_of(validate_unique, Student.objects, 'roll_no', 'CSE2201', 'Roll number'),
            'Roll number already exists')

    @staticmethod
    def _make_user(username):
        from django.contrib.auth import get_user_model
        return get_user_model().objects.create_user(username=username, password='x')


class ErrorCollectorTests(SimpleTestCase):
    def test_collects_all_errors_by_field(self):
        errors = ErrorCollector()
        errors.check('name', RequiredValidator('Name'), '')
        errors.check('capacity', NumericValidator('Capacity', positive=True), 0)
        errors.check('phone', PhoneValidator(), '123')
        errors.check('ok_field', RequiredValidator('Fine'), 'value')
        self.assertTrue(errors.has_errors)
        with self.assertRaises(ValidationError) as ctx:
            errors.raise_if_any()
        self.assertEqual(set(ctx.exception.error_dict), {'name', 'capacity', 'phone'})
        self.assertIn('Name is required', ctx.exception.messages)
        self.assertEqual(len(ctx.exception.messages), 3)

    def test_nothing_raised_when_all_checks_pass(self):
        errors = ErrorCollector()
        errors.check('name', RequiredValidator('Name'), 'Arjun')
        self.assertFalse(errors.has_errors)
        errors.raise_if_any()

    def test_add_accepts_plain_messages_and_dict_errors(self):
        errors = ErrorCollector()
        errors.add('room', msg('room_unavailable'))
        errors.add('dates', ValidationError({'to_date': 'bad'}))
        with self.assertRaises(ValidationError) as ctx:
            errors.raise_if_any()
        self.assertEqual(set(ctx.exception.error_dict), {'room', 'to_date'})


class ShowingErrorsTests(SimpleTestCase):
    def test_flash_errors_adds_one_alert_per_message(self):
        request = RequestFactory().get('/')
        request.session = {}
        request._messages = FallbackStorage(request)
        errors = ErrorCollector()
        errors.check('name', RequiredValidator('Name'), '')
        errors.check('phone', PhoneValidator(), '1')
        with self.assertRaises(ValidationError) as ctx:
            errors.raise_if_any()
        flash_errors(request, ctx.exception)
        shown = [m.message for m in get_messages(request)]
        self.assertEqual(sorted(shown),
                         ['Name is required', 'Phone number must be exactly 10 digits'])

    def test_error_level_uses_bootstrap_danger_class(self):
        self.assertEqual(get_level_tags()[constants.ERROR], 'danger')

    def test_form_errors_partial_lists_the_standard_messages(self):
        class DemoForm(forms.Form):
            name = forms.CharField(required=False)

        form = DemoForm(data={'name': ''})
        form.full_clean()
        form.add_error('name', msg('required', field='Name'))
        form.add_error(None, msg('room_unavailable'))
        html = render_to_string('includes/form_errors.html', {'form': form})
        self.assertIn('Name is required', html)
        self.assertIn('Room unavailable', html)
        self.assertIn('alert-danger', html)

    def test_form_errors_partial_is_empty_without_errors(self):
        class DemoForm(forms.Form):
            name = forms.CharField(required=False)

        form = DemoForm(data={'name': 'x'})
        form.full_clean()
        self.assertEqual(render_to_string('includes/form_errors.html', {'form': form}).strip().count('alert'), 0)

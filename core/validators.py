"""Reusable validators: required, numeric, date range, unique, format (Issue #13).

Two kinds:
* Field validators (classes) work in Django model fields and form fields:
      validators=[RequiredValidator('Room number'), NumericValidator('Capacity', integer=True, min_value=1)]
* Rule functions (validate_*) for checks that look at several values or the database:
      validate_date_range(from_date, to_date, 'From date', 'To date')
      validate_unique(Room.objects, 'room_no', value, 'Room number', hostel=hostel)

Every failure is a django ValidationError whose message comes from core.error_messages.
Use ErrorCollector to gather all problems of a form or service call and raise them together.
"""
import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .error_messages import msg

EMPTY_VALUES = (None, '', [], (), {})


def _is_blank(value):
    return value in EMPTY_VALUES or (isinstance(value, str) and not value.strip())


@deconstructible
class RequiredValidator:
    """Value must be present (not None, empty or only spaces)."""

    def __init__(self, field='This field'):
        self.field = field

    def __call__(self, value):
        if _is_blank(value):
            raise ValidationError(msg('required', field=self.field), code='required')


def _to_number(value):
    """Convert to int/Decimal, or raise ValueError if it is not a finite number."""
    if isinstance(value, bool):
        raise ValueError(value)
    if isinstance(value, int):
        return value
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except InvalidOperation:
        raise ValueError(value) from None
    if not number.is_finite():
        raise ValueError(value)
    return number


@deconstructible
class NumericValidator:
    """Value must be a number, optionally whole, positive, and within limits.

    Blank values are skipped (combine with RequiredValidator to forbid blanks).
    """

    def __init__(self, field='This field', integer=False, positive=False,
                 min_value=None, max_value=None):
        self.field = field
        self.integer = integer
        self.positive = positive
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, value):
        if _is_blank(value):
            return
        try:
            number = _to_number(value)
        except ValueError:
            raise ValidationError(msg('numeric', field=self.field), code='numeric') from None
        if self.integer and number != int(number):
            raise ValidationError(msg('integer', field=self.field), code='integer')
        if self.positive and number <= 0:
            raise ValidationError(msg('positive', field=self.field), code='positive')
        if self.min_value is not None and number < self.min_value:
            raise ValidationError(
                msg('min_value', field=self.field, limit=self.min_value), code='min_value')
        if self.max_value is not None and number > self.max_value:
            raise ValidationError(
                msg('max_value', field=self.field, limit=self.max_value), code='max_value')


@deconstructible
class RegexFormatValidator:
    """Value must match a pattern, for example a roll number or phone number."""

    def __init__(self, pattern, field='This field', message_key='invalid_format'):
        self.pattern = pattern
        self.field = field
        self.message_key = message_key

    def __call__(self, value):
        if _is_blank(value):
            return
        if not re.fullmatch(self.pattern, str(value)):
            raise ValidationError(
                msg(self.message_key, field=self.field), code=self.message_key)


def PhoneValidator():
    """10-digit phone number (matches the registration test cases)."""
    return RegexFormatValidator(r'\d{10}', 'Phone number', message_key='invalid_phone')


def validate_date_range(start, end, start_label='Start date', end_label='End date',
                        allow_equal=True, field=None):
    """``end`` must not be before ``start`` (or must be strictly after, if allow_equal=False).

    Blank dates are skipped. Pass ``field`` to attach the error to that form field.
    """
    if start is None or end is None:
        return
    if allow_equal:
        if end >= start:
            return
        key = 'date_range'
    else:
        if end > start:
            return
        key = 'date_after'
    message = msg(key, start=start_label, end=end_label)
    error = ValidationError({field: message}, code=key) if field else ValidationError(message, code=key)
    raise error


def validate_unique(queryset, field_name, value, label, exclude_pk=None,
                    case_insensitive=False, **scope):
    """Raise '<label> already exists' if another row has this value.

    ``scope`` narrows the check, for example room numbers are unique per hostel:
        validate_unique(Room.objects, 'room_no', 'A-101', 'Room number', hostel=hostel)
    Pass ``exclude_pk`` when editing an existing record so it does not clash with itself.
    """
    if _is_blank(value):
        return
    lookup = f'{field_name}__iexact' if case_insensitive else field_name
    matches = queryset.filter(**{lookup: value}, **scope)
    if exclude_pk is not None:
        matches = matches.exclude(pk=exclude_pk)
    if matches.exists():
        raise ValidationError(msg('unique', field=label), code='unique')


class ErrorCollector:
    """Collect errors from many checks, then raise them together as one ValidationError."""

    def __init__(self):
        self._errors = {}

    def check(self, field, rule, *args, **kwargs):
        """Run ``rule(*args, **kwargs)``; keep its error (if any) under ``field``."""
        try:
            rule(*args, **kwargs)
        except ValidationError as exc:
            self.add(field, exc)

    def add(self, field, error):
        """Add a ValidationError, or a message-key/message string, under ``field``."""
        if isinstance(error, ValidationError):
            if hasattr(error, 'error_dict'):
                for key, errors in error.error_dict.items():
                    self._errors.setdefault(key, []).extend(errors)
            else:
                self._errors.setdefault(field, []).extend(error.error_list)
        else:
            self._errors.setdefault(field, []).append(ValidationError(str(error)))

    @property
    def has_errors(self):
        return bool(self._errors)

    def raise_if_any(self):
        if self._errors:
            raise ValidationError(self._errors)

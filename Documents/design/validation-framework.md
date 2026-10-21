# Shared Validation and Error-Message Framework (SETUP.12 · Issue #13)

Traceability: NFR-06, NFR-07 · Test case: `UT_SETUP_10`

Every module validates input and reports problems with the same tools, so the same mistake
always produces the same message.

| Piece | File | What it gives you |
|---|---|---|
| Message catalogue | `core/error_messages.py` | `msg('unique', field='Room number')` returns `Room number already exists` |
| Validators | `core/validators.py` | required, numeric, format (phone), date range, unique |
| Error collector | `core/validators.py` | Gather all errors, raise them together |
| Show errors | `core/feedback.py`, `templates/includes/form_errors.html` | One way to display errors on a page |
| Alert colour | `MESSAGE_TAGS` in `config/settings.py` | Error messages appear as red Bootstrap alerts |

## Validators

| Need | Use | Example message |
|---|---|---|
| Required | `RequiredValidator('Room number')` | Room number is required |
| Numeric | `NumericValidator('Amount')` | Amount must be a number |
| Whole number | `NumericValidator('Capacity', integer=True)` | Capacity must be a whole number |
| Positive / limits | `NumericValidator('Capacity', positive=True)`, `min_value=1`, `max_value=6` | Capacity must be greater than zero |
| Phone | `PhoneValidator()` | Phone number must be exactly 10 digits |
| Other formats | `RegexFormatValidator(r'[A-Z]{3}\d{4}', 'Roll number')` | Roll number format is invalid |
| Date range | `validate_date_range(start, end, 'From date', 'To date')` | To date cannot be before From date |
| Unique | `validate_unique(Room.objects, 'room_no', value, 'Room number', hostel=hostel)` | Room number already exists |

Blank values are skipped by every validator except `RequiredValidator`, so combine the two
when a field is mandatory (this is Django's own convention).

## Using it

**In a model or form field**
```python
from core.validators import NumericValidator, PhoneValidator, RequiredValidator

capacity = models.PositiveSmallIntegerField(
    validators=[RequiredValidator('Capacity'), NumericValidator('Capacity', integer=True, min_value=1)])
phone = models.CharField(max_length=10, validators=[PhoneValidator()])
```

**In a form's `clean()` or a service function**
```python
from core.validators import ErrorCollector, validate_date_range, validate_unique

errors = ErrorCollector()
errors.check('room_no', validate_unique, Room.objects, 'room_no', room_no, 'Room number', hostel=hostel)
errors.check('to_date', validate_date_range, from_date, to_date, 'From date', 'To date')
errors.raise_if_any()          # one ValidationError holding every problem
```

**In a view**
```python
from django.core.exceptions import ValidationError
from core.feedback import flash_errors

try:
    create_room(...)
except ValidationError as exc:
    flash_errors(request, exc)     # one red alert per message
```
In a template with a form: `{% include 'includes/form_errors.html' with form=form %}`.

## Adding a new message
1. Add one line to `MESSAGES` in `core/error_messages.py` (no trailing full stop; start with the field name).
2. Use `msg('your_key', ...)` everywhere. Never type error text in views or services.

## Rules
- Messages name the field, so they stay clear when shown in a list.
- Wording that appears in the Test Plan (`Room number already exists`, `Roll number already exists`, `Invalid username or password`, `Room unavailable`, `No vacant rooms available`) is fixed. Change it only together with the Test Plan.
- The database constraints from #9 stay as the last line of defence. These validators give the friendly message before the database refuses the row.

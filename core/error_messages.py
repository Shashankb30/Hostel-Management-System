"""One catalogue of user-facing error messages (Issue #13, SETUP.12).

Every module gets its wording from here, so the same mistake always produces the
same message. Messages name the field and have no trailing full stop, matching
the Test Plan (for example "Room number already exists").

    msg('unique', field='Room number')   ->  'Room number already exists'
"""

MESSAGES = {
    # Generic field rules
    'required': '{field} is required',
    'numeric': '{field} must be a number',
    'integer': '{field} must be a whole number',
    'positive': '{field} must be greater than zero',
    'min_value': '{field} must be at least {limit}',
    'max_value': '{field} must be at most {limit}',
    'date_range': '{end} cannot be before {start}',
    'date_after': '{end} must be after {start}',
    'unique': '{field} already exists',
    'invalid_format': '{field} format is invalid',
    'invalid_phone': 'Phone number must be exactly 10 digits',
    'max_length': '{field} must be at most {limit} characters',
    'invalid_choice': '{field} is not a valid choice',
    # Business messages taken from the Test Plan
    'invalid_credentials': 'Invalid username or password',
    'account_locked': 'Account is inactive or locked',
    'no_role': 'Account has no role assigned. Contact the administrator',
    'room_unavailable': 'Room unavailable',
    'no_vacant_rooms': 'No vacant rooms available',
    'room_has_occupants': 'Room has occupants; reassign them before deleting the room',
    'no_active_checkin': 'No active check-in exists',
    'already_checked_out': 'Already checked out',
}


def msg(key, **params):
    """Return the standard message for ``key`` with ``params`` filled in."""
    try:
        template = MESSAGES[key]
    except KeyError:
        raise KeyError(f'Unknown error message key: {key!r}') from None
    if '{field}' in template:
        params.setdefault('field', 'This field')
    try:
        text = template.format(**params)
    except KeyError as exc:
        raise ValueError(f'Message {key!r} needs the parameter {exc.args[0]!r}') from None
    return text[0].upper() + text[1:]

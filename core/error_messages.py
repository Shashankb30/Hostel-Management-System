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
    'duplicate_payment': 'This payment was already submitted; check the payment history before saving it again',
    'payment_exceeds_balance': 'Payment amount cannot exceed the outstanding balance of {balance}',
    'fee_already_paid': 'This fee is already fully paid',
    'payment_date_future': 'Payment date cannot be in the future',
    'fee_duplicate': 'A fee with this academic year and description already exists for the student',
    'fee_below_paid': 'Fee amount cannot be lower than the amount already paid ({paid})',
    'max_decimals': '{field} can have at most 2 decimal places',
    'max_length': '{field} must be at most {limit} characters',
    'invalid_choice': '{field} is not a valid choice',
    # Business messages taken from the Test Plan
    'invalid_credentials': 'Invalid username or password',
    'account_locked': 'Account is inactive or locked',
    'no_role': 'Account has no role assigned. Contact the administrator',
    'account_inactive': 'Account is inactive or locked: this account has been deactivated. Contact the administrator',
    'account_locked_admin': 'Account is inactive or locked: it has been locked by an administrator. Contact the administrator',
    'account_locked_attempts': 'Account is inactive or locked: too many failed login attempts. Contact the administrator to unlock it',
    'password_mismatch': 'Passwords do not match',
    'cannot_deactivate_self': 'You cannot deactivate your own account',
    'cannot_change_own_role': 'You cannot change your own role',
    'room_unavailable': 'Room unavailable',
    'no_vacant_rooms': 'No vacant rooms available',
    'room_has_occupants': 'Room has occupants; reassign them before deleting the room',
    'room_has_occupants_unavailable': 'Room has occupants; reassign them before making the room unavailable',
    'room_has_history': 'Room has allocation history; make it unavailable instead of deleting it',
    'capacity_below_occupancy': 'Capacity cannot be lower than the {occupied} student(s) currently in the room',
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

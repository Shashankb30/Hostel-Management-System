"""Forms for the administrator's user-management screens (Issue #25)."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.error_messages import msg
from core.models import Hostel, UserAccount
from core.validators import PhoneValidator, RegexFormatValidator, validate_unique


def _required(label):
    return {'required': msg('required', field=label)}


class _StyledForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)


class AccountFormBase(_StyledForm):
    """Fields shared by the create and edit screens."""

    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(
        required=False, label='Email address',
        error_messages={'invalid': msg('invalid_format', field='Email address')},
        help_text='Needed for the "Forgot password" email.')
    phone = forms.CharField(max_length=20, required=False, validators=[PhoneValidator()])
    role = forms.ChoiceField(
        choices=UserAccount.ROLE_CHOICES,
        error_messages={**_required('Role'), 'invalid_choice': msg('invalid_choice', field='Role')})
    hostel = forms.ModelChoiceField(
        queryset=Hostel.objects.filter(is_active=True), required=False, empty_label='No hostel',
        error_messages={'invalid_choice': msg('invalid_choice', field='Hostel')})

    #: pk of the Django user being edited, so its own email does not count as a duplicate
    user_pk = None

    def clean_email(self):
        value = self.cleaned_data.get('email', '')
        validate_unique(get_user_model()._default_manager, 'email', value, 'Email address',
                        exclude_pk=self.user_pk, case_insensitive=True)
        return value

    def clean(self):
        cleaned = super().clean()
        role, hostel = cleaned.get('role'), cleaned.get('hostel')
        needs_hostel = role in (UserAccount.ROLE_STUDENT, UserAccount.ROLE_WARDEN)
        if needs_hostel and hostel is None and 'hostel' not in self.errors:
            self.add_error('hostel', msg('required', field='Hostel'))
        return cleaned


class UserCreateForm(AccountFormBase):
    username = forms.CharField(
        max_length=150, error_messages=_required('Username'),
        validators=[RegexFormatValidator(r'[\w.@+-]+', 'Username')],
        help_text='Letters, digits and @ . + - _ only.')
    password1 = forms.CharField(
        label='Password', strip=False, error_messages=_required('Password'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(
        label='Confirm password', strip=False, error_messages=_required('Confirm password'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    field_order = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'hostel',
                   'password1', 'password2']

    def clean_username(self):
        value = self.cleaned_data['username']
        validate_unique(get_user_model()._default_manager, 'username', value, 'Username',
                        case_insensitive=True)
        return value

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get('password1'), cleaned.get('password2')
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', msg('password_mismatch'))
            else:
                try:
                    validate_password(password1)
                except ValidationError as exc:
                    self.add_error('password1', exc)
        return cleaned


class UserEditForm(AccountFormBase):
    def __init__(self, *args, account, acting_user, **kwargs):
        kwargs.setdefault('initial', {
            'first_name': account.user.first_name,
            'last_name': account.user.last_name,
            'email': account.user.email,
            'phone': account.phone,
            'role': account.role,
            'hostel': account.hostel_id,
        })
        super().__init__(*args, **kwargs)
        self.account = account
        self.user_pk = account.user_id
        if account.user_id == acting_user.pk:
            # Nobody changes their own role; a disabled field ignores whatever is posted.
            self.fields['role'].disabled = True
            self.fields['role'].help_text = 'You cannot change your own role.'

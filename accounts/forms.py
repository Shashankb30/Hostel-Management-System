"""Forms for login and password reset (FR-01)."""
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator

from core.error_messages import msg
from core.validators import RequiredValidator

from .services import authenticate_credentials


class LoginForm(forms.Form):
    """Username + password. Blank fields are reported here and never reach authentication."""

    username = forms.CharField(
        validators=[MaxLengthValidator(150, message=msg('max_length', field='Username', limit=150))],
        error_messages={'required': msg('required', field='Username')},
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'autofocus': True, 'autocomplete': 'username',
            'maxlength': '150'}),
    )
    password = forms.CharField(
        strip=False,
        validators=[RequiredValidator('Password')],
        error_messages={'required': msg('required', field='Password')},
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'autocomplete': 'current-password'}),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user_cache = None

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned  # blank or invalid input: do not attempt authentication
        result = authenticate_credentials(cleaned['username'], cleaned['password'])
        if not result.ok:
            raise ValidationError(result.message, code=result.code)
        self.user_cache = result.user
        return cleaned

    def get_user(self):
        return self.user_cache

"""The Add New Student form (FR-02)."""
from django import forms
from django.contrib.auth import get_user_model

from core.error_messages import msg
from core.forms import BootstrapFormMixin
from core.models import Hostel
from core.models import Student
from core.validators import PhoneValidator, RegexFormatValidator
from core.validators import validate_unique


def _required(label):
    return {'required': msg('required', field=label)}


class StudentRegistrationForm(BootstrapFormMixin, forms.Form):
    """Personal, academic and contact details of a new student."""

    full_name = forms.CharField(
        label='Name', max_length=160,
    )
    roll_no = forms.CharField(
        label='Roll No.', max_length=32,
        validators=[RegexFormatValidator(r'[A-Za-z0-9][A-Za-z0-9/._-]*', 'Roll No.')],
        help_text='Letters, digits and / . _ - only, for example CSE2201.',
    )
    phone = forms.CharField(
        label='Contact', max_length=20, validators=[PhoneValidator()],
        help_text='10-digit mobile number.',
    )
    address = forms.CharField(
        label='Address', required=False, widget=forms.Textarea(attrs={'rows': 2}))
    course = forms.CharField(
        label='Course', max_length=100,
    )
    year_of_study = forms.IntegerField(
        label='Year',
    )
    hostel = forms.ModelChoiceField(
        label='Hostel', queryset=Hostel.objects.filter(is_active=True), empty_label='Select a hostel',
    )
    email = forms.EmailField(
        label='Email address', required=False,
        error_messages={'invalid': msg('invalid_format', field='Email address')},
        help_text='Optional. Lets the student use "Forgot password".')
    guardian_name = forms.CharField(label='Guardian name', max_length=160, required=False)
    guardian_phone = forms.CharField(
        label='Guardian contact', max_length=20, required=False, validators=[PhoneValidator()])

    def clean_roll_no(self):
        value = self.cleaned_data['roll_no']
        validate_unique(Student.objects, 'roll_no', value, 'Roll number', case_insensitive=True)
        return value

    def clean_email(self):
        value = self.cleaned_data.get('email', '')
        # The email becomes the login account's email as well, so check both places.
        validate_unique(get_user_model()._default_manager, 'email', value, 'Email address',
                        case_insensitive=True)
        validate_unique(Student.objects, 'email', value, 'Email address', case_insensitive=True)
        return value

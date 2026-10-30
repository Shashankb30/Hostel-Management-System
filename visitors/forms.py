"""Forms for Visitor Management (FR-08)."""
from django import forms

from core.error_messages import msg
from core.models import Student, VisitorLog


class VisitorForm(forms.ModelForm):
    """Form for adding and checking in a new visitor (FR-08.01, FR-08.02, FR-08.03)."""

    id_proof = forms.CharField(
        max_length=50,
        required=True,
        error_messages={'required': msg('required', field='ID proof')},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Govt ID / Aadhaar / College ID'}),
        label='ID Proof',
    )
    visitor_name = forms.CharField(
        max_length=160,
        required=True,
        error_messages={'required': msg('required', field='Visitor name')},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Visitor full name'}),
        label='Visitor Name',
    )
    visitor_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact phone number (optional)'}),
        label='Phone Number',
    )
    purpose = forms.CharField(
        max_length=240,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Purpose of visit'}),
        label='Purpose',
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True).select_related('hostel', 'user_account').order_by('full_name'),
        required=True,
        error_messages={'required': msg('required', field='Student')},
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Student Visited',
    )

    class Meta:
        model = VisitorLog
        fields = ['visitor_name', 'id_proof', 'purpose', 'student', 'visitor_phone']

    def __init__(self, *args, hostel=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hostel is not None:
            self.fields['student'].queryset = self.fields['student'].queryset.filter(hostel=hostel)

    def clean_visitor_name(self):
        val = (self.cleaned_data.get('visitor_name') or '').strip()
        if not val:
            raise forms.ValidationError(msg('required', field='Visitor name'))
        return val

    def clean_id_proof(self):
        val = (self.cleaned_data.get('id_proof') or '').strip()
        if not val:
            raise forms.ValidationError(msg('required', field='ID proof'))
        return val

    def clean_student(self):
        val = self.cleaned_data.get('student')
        if not val:
            raise forms.ValidationError(msg('required', field='Student'))
        return val


class VisitorDateFilterForm(forms.Form):
    """Filter visitor logs by search query and/or date."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search student or visitor'}),
        label='Search',
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date',
    )


class VisitorReportFilterForm(forms.Form):
    """Filter visitor logs for report generation within a date range."""
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='From Date',
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='To Date',
    )

    def clean(self):
        cleaned = super().clean()
        from_date = cleaned.get('from_date')
        to_date = cleaned.get('to_date')
        if from_date and to_date and to_date < from_date:
            raise forms.ValidationError(msg('date_range', start='From date', end='To date'))
        return cleaned

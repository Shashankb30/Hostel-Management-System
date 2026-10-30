"""Forms for Home / Long-Leave Application (FR-09)."""
from django import forms

from core.error_messages import msg
from core.models import LeaveApplication


class LeaveApplicationForm(forms.ModelForm):
    """Student leave application form (FR-09.01, FR-09.02, FR-09.03)."""

    from_date = forms.DateField(
        required=True,
        error_messages={'required': msg('required', field='From date')},
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='From Date',
    )
    to_date = forms.DateField(
        required=True,
        error_messages={'required': msg('required', field='To date')},
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='To Date',
    )
    destination = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Home town, City, Address'}),
        label='Destination / Place of Visit',
    )
    reason = forms.CharField(
        required=True,
        error_messages={'required': msg('required', field='Reason')},
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'State the reason for leave'}),
        label='Reason for Leave',
    )

    class Meta:
        model = LeaveApplication
        fields = ['from_date', 'to_date', 'destination', 'reason']

    def clean_reason(self):
        val = (self.cleaned_data.get('reason') or '').strip()
        if not val:
            raise forms.ValidationError(msg('required', field='Reason'))
        return val

    def clean(self):
        cleaned = super().clean()
        from_date = cleaned.get('from_date')
        to_date = cleaned.get('to_date')

        if from_date and to_date and to_date < from_date:
            raise forms.ValidationError(msg('date_range', start='From date', end='To date'))

        return cleaned


class LeaveReviewForm(forms.Form):
    """Staff review action form for approval, rejection, or requesting more information (FR-09.05, FR-09.06, FR-09.08)."""

    ACTION_APPROVE = 'approve'
    ACTION_REJECT = 'reject'
    ACTION_REQUEST_INFO = 'request_info'

    ACTION_CHOICES = [
        (ACTION_APPROVE, 'Approve'),
        (ACTION_REJECT, 'Reject'),
        (ACTION_REQUEST_INFO, 'Request Info'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.HiddenInput(),
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks (required for Rejection / Info Request)'}),
        label='Reviewer Remarks',
    )

    def clean(self):
        cleaned = super().clean()
        action = cleaned.get('action')
        remarks = (cleaned.get('remarks') or '').strip()

        if action in (self.ACTION_REJECT, self.ACTION_REQUEST_INFO) and not remarks:
            field_name = 'Rejection remarks' if action == self.ACTION_REJECT else 'Remarks'
            self.add_error('remarks', msg('required', field=field_name))

        cleaned['remarks'] = remarks
        return cleaned


class LeaveFilterForm(forms.Form):
    """Filter form for staff review and admin records lists."""

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + LeaveApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search student name or roll number'}),
    )

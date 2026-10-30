"""Forms for Notice / Information Management (FR-10)."""
from django import forms

from core.error_messages import msg
from core.models import Notice


class NoticeForm(forms.ModelForm):
    """Notice authoring and edit form (FR-10.01, FR-10.02, FR-10.04, FR-10.05)."""

    title = forms.CharField(
        max_length=160,
        required=True,
        error_messages={'required': msg('required', field='Title')},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notice title / headline'}),
        label='Title',
    )
    body = forms.CharField(
        required=True,
        error_messages={'required': msg('required', field='Content')},
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Notice content / announcement details'}),
        label='Content',
    )
    audience = forms.ChoiceField(
        choices=Notice.AUDIENCE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Target Audience',
    )
    expires_at = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Expiry Date (Optional)',
        help_text='Leave blank if the notice does not expire.',
    )
    is_published = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Publish immediately',
    )

    class Meta:
        model = Notice
        fields = ['title', 'body', 'audience', 'expires_at', 'is_published']

    def clean_title(self):
        val = (self.cleaned_data.get('title') or '').strip()
        if not val:
            raise forms.ValidationError(msg('required', field='Title'))
        return val

    def clean_body(self):
        val = (self.cleaned_data.get('body') or '').strip()
        if not val:
            raise forms.ValidationError(msg('required', field='Content'))
        return val


class NoticeFilterForm(forms.Form):
    """Filter form for search and audience filtering."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search notices by keyword'}),
        label='Keyword',
    )
    audience = forms.ChoiceField(
        required=False,
        choices=[('', 'All Audiences')] + Notice.AUDIENCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Audience',
    )

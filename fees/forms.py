"""Fee and payment forms (FR-05)."""
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.error_messages import msg
from core.models import Payment
from core.validators import NumericValidator, RegexFormatValidator
from .services import CENT, MAX_AMOUNT, money


def _required(label):
    return {'required': msg('required', field=label)}


def _style(form):
    for field in form.fields.values():
        css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
        field.widget.attrs.setdefault('class', css)


def _to_money(value, label):
    """Text that already passed NumericValidator -> Decimal with at most two decimal places."""
    amount = Decimal(value.strip())
    if amount != amount.quantize(CENT):
        raise ValidationError(msg('max_decimals', field=label), code='max_decimals')
    return amount.quantize(CENT)


class FeeForm(forms.Form):
    """Define or edit a fee for a student (FR-05.01)."""

    academic_year = forms.CharField(
        label='Academic year', max_length=9, error_messages=_required('Academic year'),
        validators=[RegexFormatValidator(r'\d{4}-\d{2}(\d{2})?', 'Academic year')],
        help_text='For example 2026-27.')
    description = forms.CharField(
        label='Description', max_length=160, initial='Hostel fee', error_messages=_required('Description'))
    amount_due = forms.CharField(
        label='Amount due (Rs.)', error_messages=_required('Amount due'),
        validators=[NumericValidator('Amount due', positive=True, max_value=MAX_AMOUNT)])
    due_date = forms.DateField(
        label='Due date', required=False, widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'invalid': msg('invalid_format', field='Due date')})

    def __init__(self, *args, fee=None, **kwargs):
        if fee is not None:
            kwargs.setdefault('initial', {
                'academic_year': fee.academic_year, 'description': fee.description,
                'amount_due': fee.amount_due, 'due_date': fee.due_date})
        super().__init__(*args, **kwargs)
        _style(self)

    def clean_amount_due(self):
        return _to_money(self.cleaned_data['amount_due'], 'Amount due')


class PaymentForm(forms.Form):
    """Record a payment (FR-05.03 to FR-05.06, FR-05.12)."""

    amount = forms.CharField(
        label='Amount (Rs.)', error_messages=_required('Amount'),
        validators=[NumericValidator('Amount', positive=True, max_value=MAX_AMOUNT)])
    mode = forms.ChoiceField(
        label='Payment mode', choices=[('', 'Select mode')] + Payment.MODE_CHOICES,
        error_messages={**_required('Payment mode'), 'invalid_choice': msg('invalid_choice', field='Payment mode')})
    paid_on = forms.DateField(
        label='Payment date', widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={**_required('Payment date'), 'invalid': msg('invalid_format', field='Payment date')})
    reference = forms.CharField(
        label='Reference (optional)', max_length=100, required=False,
        help_text='Transaction id, cheque or receipt book number.')

    def __init__(self, *args, balance=None, **kwargs):
        kwargs.setdefault('initial', {'paid_on': timezone.localdate()})
        super().__init__(*args, **kwargs)
        if balance is not None:
            self.fields['amount'].help_text = f'Outstanding balance: {money(balance)}'
        _style(self)

    def clean_amount(self):
        return _to_money(self.cleaned_data['amount'], 'Amount')

    def clean_paid_on(self):
        value = self.cleaned_data['paid_on']
        if value > timezone.localdate():
            raise ValidationError(msg('payment_date_future'), code='payment_date_future')
        return value

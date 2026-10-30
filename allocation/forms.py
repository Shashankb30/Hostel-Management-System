from django import forms
from django.forms import modelformset_factory

from core.models import AllocationRule


class RuleForm(forms.ModelForm):
    weight = forms.IntegerField(min_value=0, max_value=100, label='Weight')

    class Meta:
        model = AllocationRule
        fields = ['weight', 'is_active', 'description']
        labels = {'is_active': 'Active', 'description': 'Description'}


RuleFormSet = modelformset_factory(AllocationRule, form=RuleForm, extra=0)

"""Form helpers shared by every module."""
from django import forms


def _add_class(widget, css):
    classes = widget.attrs.get('class', '')
    if css not in classes.split():
        widget.attrs['class'] = f'{classes} {css}'.strip()


class BootstrapFormMixin:
    """Bootstrap 5 styling for every field.

    Put it before ``forms.Form`` in the bases. Fields that fail validation also get the
    red ``is-invalid`` outline, so people can see exactly which inputs to fix.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            is_select = isinstance(field.widget, forms.Select)
            _add_class(field.widget, 'form-select' if is_select else 'form-control')

    def add_error(self, field, error):
        super().add_error(field, error)
        if field in self.fields:  # errors without a field are shown above the form
            _add_class(self.fields[field].widget, 'is-invalid')
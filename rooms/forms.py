"""Add Room and Edit Room form (FR-03)."""
from django import forms
from django.core.exceptions import ValidationError

from core.error_messages import msg
from core.forms import BootstrapFormMixin
from core.models import Hostel
from core.models import Room
from core.validators import NumericValidator, RegexFormatValidator
from core.validators import validate_unique
from . import services

ROOM_TYPE_SUGGESTIONS = ['Single', 'Double', 'Triple', 'Deluxe Triple']
MAX_CAPACITY = 100


def _required(label):
    return {'required': msg('required', field=label)}


class RoomForm(BootstrapFormMixin, forms.Form):
    """Room number, capacity and type (plus hostel, block and floor)."""

    hostel = forms.ModelChoiceField(
        label='Hostel', queryset=Hostel.objects.filter(is_active=True), empty_label='Select a hostel',
        error_messages={**_required('Hostel'), 'invalid_choice': msg('invalid_choice', field='Hostel')})
    room_no = forms.CharField(
        label='Room No.', max_length=20,
        validators=[RegexFormatValidator(r'[A-Za-z0-9][A-Za-z0-9/._-]*', 'Room number')],
        help_text='Letters, digits and / . _ - only, for example A-101.',
        error_messages=_required('Room number'))
    block = forms.CharField(label='Block', max_length=40, required=False)
    floor = forms.IntegerField(
        label='Floor', required=False, initial=0,
        validators=[NumericValidator('Floor', integer=True, min_value=-5, max_value=100)],
        error_messages={'invalid': msg('integer', field='Floor')})
    room_type = forms.CharField(
        label='Type', max_length=40, error_messages=_required('Room type'),
        widget=forms.TextInput(attrs={'list': 'room-type-options', 'autocomplete': 'off'}),
        help_text='Pick a suggestion or type your own, for example Triple.')
    capacity = forms.IntegerField(
        label='Capacity',
        validators=[NumericValidator('Capacity', integer=True, positive=True, max_value=MAX_CAPACITY)],
        error_messages={**_required('Capacity'), 'invalid': msg('integer', field='Capacity')},
    )

    room = None  # the Room being edited; None when adding

    def __init__(self, *args, room=None, **kwargs):
        self.room = room
        if room is not None:
            kwargs.setdefault('initial', {
                'hostel': room.hostel_id, 'room_no': room.room_no, 'block': room.block,
                'floor': room.floor, 'room_type': room.room_type, 'capacity': room.capacity,
            })
        super().__init__(*args, **kwargs)
        if room is not None:
            # A room never moves to another hostel; a disabled field keeps its initial value.
            self.fields['hostel'].disabled = True
            self.fields['hostel'].help_text = 'A room cannot move to another hostel.'

    def clean(self):
        cleaned = super().clean()
        hostel, room_no = cleaned.get('hostel'), cleaned.get('room_no')
        if hostel is not None and room_no:
            try:
                validate_unique(
                    Room.objects, 'room_no', room_no, 'Room number', case_insensitive=True,
                    exclude_pk=self.room.pk if self.room else None, hostel=hostel)
            except ValidationError as error:
                self.add_error('room_no', error)
        return cleaned

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if self.room is not None:
            services.check_capacity(self.room, capacity)  # raises ValidationError
        return capacity

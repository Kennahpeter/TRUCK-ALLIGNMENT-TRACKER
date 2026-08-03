import datetime

from django import forms

from .models import Alignment, Truck


class AlignmentForm(forms.ModelForm):
    class Meta:
        model = Alignment
        fields = [
            'truck_id',
            'trailer_id',
            'alignment_date',
            'alignment_time',
            'mileage',
            'tech_name',
        ]
        widgets = {
            'truck_id': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_truck_id',
            }),
            'trailer_id': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Auto-filled from truck', 'id': 'id_trailer_id',
            }),
            'alignment_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'alignment_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'placeholder': 'Odometer reading'
            }),
            'tech_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Technician full name'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Truck dropdown is sourced from the active fleet register.
        truck_choices = [('', '— Select truck —')] + [
            (t.truck_id, t.truck_id) for t in Truck.objects.filter(active=True).order_by('truck_id')
        ]
        self.fields['truck_id'].widget.choices = truck_choices
        self.fields['truck_id'].choices = truck_choices

        # Default the date/time fields to "now" for brand-new records only.
        if not self.instance.pk:
            now = datetime.datetime.now()
            self.fields['alignment_date'].initial = now.date()
            self.fields['alignment_time'].initial = now.time().replace(microsecond=0)

    def clean_mileage(self):
        mileage = self.cleaned_data.get('mileage')
        if mileage is None or mileage <= 0:
            raise forms.ValidationError("Mileage must be a positive number.")
        return mileage


class ReportFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    tech_name = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    truck_id = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        tech_choices = kwargs.pop('tech_choices', [])
        truck_choices = kwargs.pop('truck_choices', [])
        super().__init__(*args, **kwargs)
        self.fields['tech_name'].choices = [('', 'All Technicians')] + tech_choices
        self.fields['truck_id'].choices = [('', 'All Trucks')] + truck_choices

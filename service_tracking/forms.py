from django import forms
from django.utils import timezone

from alignments.models import Truck

from .models import Customer, MileageUpdate, ServiceRecord, Vehicle


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['company_name', 'contact_person', 'phone', 'email', 'address', 'notes']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'truck', 'customer', 'fleet_number', 'vehicle_type',
            'make', 'model', 'driver_name', 'active', 'notes',
        ]
        widgets = {
            'truck': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'fleet_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer trucks that don't already have a service profile
        # (except the one currently attached to this vehicle, when editing).
        used_truck_ids = Vehicle.objects.exclude(pk=self.instance.pk).values_list('truck_id', flat=True)
        self.fields['truck'].queryset = Truck.objects.exclude(pk__in=used_truck_ids).order_by('truck_id')


class MileageUpdateForm(forms.ModelForm):
    class Meta:
        model = MileageUpdate
        fields = ['odometer_reading', 'recorded_date']
        widgets = {
            'odometer_reading': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'recorded_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['recorded_date'].initial = timezone.localdate()


class ServiceRecordForm(forms.ModelForm):
    class Meta:
        model = ServiceRecord
        fields = [
            'service_date', 'odometer_reading', 'service_type', 'description',
            'technician', 'parts_used', 'labour_cost', 'parts_cost', 'remarks',
        ]
        widgets = {
            'service_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'odometer_reading': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'technician': forms.TextInput(attrs={'class': 'form-control'}),
            'parts_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'labour_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'parts_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['service_date'].initial = timezone.localdate()

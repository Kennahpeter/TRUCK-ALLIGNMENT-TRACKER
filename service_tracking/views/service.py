from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import ServiceRecordForm
from ..models import Vehicle
from ..utils.audit import log_action


@login_required
def service_record_add(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        form = ServiceRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.vehicle = vehicle
            record.created_by = request.user
            record.save()

            # A completed service also updates the truck's baseline service KM/date,
            # and counts as a fresh, non-suspicious mileage data point.
            vehicle.truck.last_service_km = record.odometer_reading
            vehicle.truck.last_service_date = record.service_date
            if not vehicle.truck.current_odometer or record.odometer_reading > vehicle.truck.current_odometer:
                vehicle.truck.current_odometer = record.odometer_reading
            vehicle.truck.save(update_fields=['last_service_km', 'last_service_date', 'current_odometer'])

            vehicle.mileage_updates.create(
                odometer_reading=record.odometer_reading,
                recorded_date=record.service_date,
                source='manual',
                recorded_by=request.user,
            )

            log_action(request.user, 'create', vehicle, details=f"Service recorded at {record.odometer_reading:,} KM")
            messages.success(request, f"Service record added for {vehicle.registration}.")
            return redirect('service_tracking:vehicle_detail', pk=vehicle.pk)
    else:
        form = ServiceRecordForm()

    return render(request, 'service_tracking/service_form.html', {'form': form, 'vehicle': vehicle})

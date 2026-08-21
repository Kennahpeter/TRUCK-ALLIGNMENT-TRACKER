from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import MileageUpdateForm
from ..logic.mileage_validation import check_mileage
from ..models import Vehicle
from ..utils.audit import log_action


@login_required
def mileage_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        form = MileageUpdateForm(request.POST)
        confirm = request.POST.get('confirm_suspicious') == '1'

        if form.is_valid():
            new_reading = form.cleaned_data['odometer_reading']
            recorded_date = form.cleaned_data['recorded_date']
            is_suspicious, reason = check_mileage(vehicle, new_reading, recorded_date)

            if is_suspicious and not confirm:
                # Don't save yet — ask the user to confirm.
                return render(request, 'service_tracking/mileage_form.html', {
                    'form': form,
                    'vehicle': vehicle,
                    'suspicious_reason': reason,
                    'pending_reading': new_reading,
                    'pending_date': recorded_date,
                })

            update = form.save(commit=False)
            update.vehicle = vehicle
            update.recorded_by = request.user
            update.flagged_suspicious = is_suspicious
            update.flag_reason = reason
            update.save()

            # Keep the Truck's current_odometer in sync for the alignments app too.
            vehicle.truck.current_odometer = new_reading
            vehicle.truck.save(update_fields=['current_odometer'])

            log_action(request.user, 'update', vehicle, details=f"Mileage updated to {new_reading:,} KM")
            messages.success(request, f"Mileage for {vehicle.registration} updated to {new_reading:,} KM.")
            return redirect('service_tracking:vehicle_detail', pk=vehicle.pk)
    else:
        form = MileageUpdateForm()

    return render(request, 'service_tracking/mileage_form.html', {'form': form, 'vehicle': vehicle})

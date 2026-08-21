from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import CustomerForm, VehicleForm
from ..logic.calculations import is_mileage_stale, status_color, status_label
from ..models import Customer, Vehicle
from ..utils.audit import log_action


# ---------------------------------------------------------------------------
# Vehicle table
# ---------------------------------------------------------------------------
@login_required
def vehicle_list(request):
    queryset = Vehicle.objects.select_related('truck', 'customer').all()

    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(truck__truck_id__icontains=q) | queryset.filter(
            fleet_number__icontains=q
        ) | queryset.filter(driver_name__icontains=q)

    customer_id = request.GET.get('customer')
    if customer_id:
        queryset = queryset.filter(customer_id=customer_id)

    active_only = request.GET.get('active') == '1'
    if active_only:
        queryset = queryset.filter(active=True)

    status_filter = request.GET.get('status')

    rows = []
    for vehicle in queryset:
        status = vehicle.service_status
        if status_filter and status != status_filter:
            continue
        rows.append({
            'vehicle': vehicle,
            'status': status,
            'status_label': status_label(status),
            'status_color': status_color(status),
            'stale': is_mileage_stale(vehicle),
        })

    context = {
        'rows': rows,
        'customers': Customer.objects.all(),
        'q': q,
        'selected_customer': customer_id or '',
        'selected_status': status_filter or '',
        'active_only': active_only,
        'status_choices': ['CURRENT', 'APPROACHING', 'DUE_SOON', 'OVERDUE', 'RECENTLY_SERVICED', 'UNKNOWN'],
    }
    return render(request, 'service_tracking/vehicle_list.html', context)


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle.objects.select_related('truck', 'customer'), pk=pk)
    status = vehicle.service_status
    context = {
        'vehicle': vehicle,
        'status': status,
        'status_label': status_label(status),
        'status_color': status_color(status),
        'stale': is_mileage_stale(vehicle),
        'service_records': vehicle.service_records.all()[:25],
        'mileage_updates': vehicle.mileage_updates.all()[:25],
        'follow_ups': vehicle.follow_ups.all()[:10],
    }
    return render(request, 'service_tracking/vehicle_detail.html', context)


@login_required
def vehicle_add(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            log_action(request.user, 'create', vehicle)
            messages.success(request, f"Vehicle {vehicle.registration} was added.")
            return redirect('service_tracking:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm()
    return render(request, 'service_tracking/vehicle_form.html', {'form': form})


@login_required
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            log_action(request.user, 'update', vehicle)
            messages.success(request, f"Vehicle {vehicle.registration} was updated.")
            return redirect('service_tracking:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'service_tracking/vehicle_form.html', {'form': form, 'is_edit': True, 'vehicle': vehicle})


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'service_tracking/customer_list.html', {'customers': customers})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    vehicles = customer.vehicles.select_related('truck').all()
    rows = [{
        'vehicle': v,
        'status': v.service_status,
        'status_label': status_label(v.service_status),
        'status_color': status_color(v.service_status),
    } for v in vehicles]
    return render(request, 'service_tracking/customer_detail.html', {'customer': customer, 'rows': rows})


@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            log_action(request.user, 'create', customer)
            messages.success(request, f"Customer '{customer.company_name}' was added.")
            return redirect('service_tracking:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, 'service_tracking/customer_form.html', {'form': form})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            log_action(request.user, 'update', customer)
            messages.success(request, f"Customer '{customer.company_name}' was updated.")
            return redirect('service_tracking:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'service_tracking/customer_form.html', {'form': form, 'is_edit': True, 'customer': customer})

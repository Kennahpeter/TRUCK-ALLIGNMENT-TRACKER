"""
Core service-status calculation logic.

Nothing here is stored on the Vehicle model — status, KM remaining, and
KM overdue are always derived live from the ServiceRecord / MileageUpdate
history plus the configurable ServiceThreshold row. This keeps the numbers
honest: there's nothing to fall out of sync, and the vehicle's full history
can always be reconstructed from the permanent records.
"""
from datetime import timedelta

from django.utils import timezone

STATUS_LABELS = {
    'RECENTLY_SERVICED': 'Recently Serviced',
    'CURRENT': 'Current',
    'APPROACHING': 'Approaching Service',
    'DUE_SOON': 'Due Soon',
    'OVERDUE': 'Overdue',
    'UNKNOWN': 'No Mileage Data',
}

STATUS_COLORS = {
    'RECENTLY_SERVICED': 'info',
    'CURRENT': 'success',
    'APPROACHING': 'warning',
    'DUE_SOON': 'orange',
    'OVERDUE': 'danger',
    'UNKNOWN': 'secondary',
}


def get_service_status(vehicle):
    """Return one of RECENTLY_SERVICED / CURRENT / APPROACHING / DUE_SOON / OVERDUE / UNKNOWN."""
    from ..models import ServiceThreshold

    remaining = vehicle.km_remaining
    if remaining is None:
        return 'UNKNOWN'

    latest_service = vehicle.latest_service
    if latest_service and latest_service.service_date >= timezone.localdate() - timedelta(days=7):
        return 'RECENTLY_SERVICED'

    thresholds = ServiceThreshold.get_solo()

    if remaining <= 0:
        return 'OVERDUE'
    if remaining <= thresholds.due_soon_km_remaining:
        return 'DUE_SOON'
    if remaining <= thresholds.approaching_km_remaining:
        return 'APPROACHING'
    return 'CURRENT'


def status_label(status_code):
    return STATUS_LABELS.get(status_code, status_code)


def status_color(status_code):
    return STATUS_COLORS.get(status_code, 'secondary')


def is_mileage_stale(vehicle):
    """True if the vehicle's mileage hasn't been updated within the configured window."""
    from ..models import ServiceThreshold

    latest = vehicle.latest_mileage_update
    thresholds = ServiceThreshold.get_solo()
    if not latest:
        return True
    return (timezone.localdate() - latest.recorded_date).days > thresholds.stale_mileage_days

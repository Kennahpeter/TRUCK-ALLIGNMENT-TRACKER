from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from alignments.models import Truck

User = settings.AUTH_USER_MODEL


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
class Customer(models.Model):
    company_name = models.CharField(max_length=150, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name

    def get_absolute_url(self):
        return reverse('service_tracking:customer_detail', args=[self.pk])

    @property
    def vehicle_count(self):
        return self.vehicles.count()


# ---------------------------------------------------------------------------
# Vehicle
# ---------------------------------------------------------------------------
class Vehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('truck', 'Truck'),
        ('trailer', 'Trailer'),
        ('truck_trailer', 'Truck & Trailer'),
        ('van', 'Van'),
        ('pickup', 'Pickup'),
        ('other', 'Other'),
    ]

    truck = models.OneToOneField(
        Truck, on_delete=models.PROTECT, related_name='service_vehicle',
        help_text="Links this service profile to the fleet register entry used by Alignment Tracker.",
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles',
    )
    fleet_number = models.CharField(max_length=30, blank=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='truck')
    make = models.CharField(max_length=60, blank=True)
    model = models.CharField(max_length=60, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['truck__truck_id']

    def __str__(self):
        return f"{self.truck.truck_id}"

    def get_absolute_url(self):
        return reverse('service_tracking:vehicle_detail', args=[self.pk])

    @property
    def registration(self):
        return self.truck.truck_id

    # --- dynamic service calculations -------------------------------------
    @property
    def latest_mileage_update(self):
        return self.mileage_updates.order_by('-recorded_date', '-id').first()

    @property
    def current_km(self):
        latest = self.latest_mileage_update
        if latest:
            return latest.odometer_reading
        return self.truck.current_odometer

    @property
    def latest_service(self):
        return self.service_records.order_by('-service_date', '-id').first()

    @property
    def last_service_km(self):
        latest = self.latest_service
        if latest:
            return latest.odometer_reading
        return self.truck.last_service_km

    @property
    def last_service_date(self):
        latest = self.latest_service
        if latest:
            return latest.service_date
        return self.truck.last_service_date

    @property
    def next_service_km(self):
        base = self.last_service_km
        interval = self.truck.service_interval_km or 15000
        if base is not None:
            return base + interval
        return interval

    @property
    def km_remaining(self):
        current = self.current_km
        if current is None:
            return None
        return self.next_service_km - current

    @property
    def km_overdue(self):
        remaining = self.km_remaining
        if remaining is None:
            return 0
        return abs(remaining) if remaining < 0 else 0

    @property
    def service_status(self):
        from .logic.calculations import get_service_status
        return get_service_status(self)


# ---------------------------------------------------------------------------
# Service history (permanent, never overwritten)
# ---------------------------------------------------------------------------
class ServiceRecord(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('preventive', 'Preventive Service'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('other', 'Other'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_records')
    service_date = models.DateField()
    odometer_reading = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, default='preventive')
    description = models.TextField(blank=True)
    technician = models.CharField(max_length=100, blank=True)
    parts_used = models.TextField(blank=True)
    labour_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    next_service_km = models.PositiveIntegerField(
        help_text="Snapshot of the next-due KM at the time this service was recorded.",
        blank=True,
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-service_date', '-id']

    def __str__(self):
        return f"{self.vehicle} — {self.service_date} @ {self.odometer_reading:,} KM"

    @property
    def total_cost(self):
        return (self.labour_cost or 0) + (self.parts_cost or 0)

    def save(self, *args, **kwargs):
        if not self.next_service_km:
            interval = self.vehicle.truck.service_interval_km or 15000
            self.next_service_km = self.odometer_reading + interval
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Mileage history
# ---------------------------------------------------------------------------
class MileageUpdate(models.Model):
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('wialon', 'Wialon'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='mileage_updates')
    odometer_reading = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    recorded_date = models.DateField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    flagged_suspicious = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_date', '-id']

    def __str__(self):
        return f"{self.vehicle} — {self.odometer_reading:,} KM on {self.recorded_date}"


# ---------------------------------------------------------------------------
# Service follow-up / call tracking
# ---------------------------------------------------------------------------
class ServiceFollowUp(models.Model):
    STATUS_CHOICES = [
        ('not_contacted', 'Not Contacted'),
        ('called', 'Called'),
        ('confirmed', 'Customer Confirmed'),
        ('scheduled', 'Appointment Scheduled'),
        ('arrived', 'Vehicle Arrived'),
        ('in_progress', 'Service In Progress'),
        ('completed', 'Service Completed'),
        ('declined', 'Customer Declined'),
        ('rescheduled', 'Rescheduled'),
    ]
    CONTACT_METHOD_CHOICES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('in_person', 'In Person'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='follow_ups')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_contacted')
    contact_date = models.DateField(null=True, blank=True)
    contact_method = models.CharField(max_length=10, choices=CONTACT_METHOD_CHOICES, blank=True)
    person_contacted = models.CharField(max_length=100, blank=True)
    staff_responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    next_follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.vehicle} — {self.get_status_display()}"


# ---------------------------------------------------------------------------
# Configurable thresholds (Settings screen)
# ---------------------------------------------------------------------------
class ServiceThreshold(models.Model):
    approaching_km_remaining = models.PositiveIntegerField(default=3000)
    due_soon_km_remaining = models.PositiveIntegerField(default=1000)
    stale_mileage_days = models.PositiveIntegerField(default=14)

    class Meta:
        verbose_name = "Service Threshold Settings"
        verbose_name_plural = "Service Threshold Settings"

    def __str__(self):
        return "Service Threshold Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=20, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} {self.model_name} #{self.object_id} by {self.user}"


# ---------------------------------------------------------------------------
# Notification architecture (skeleton only — no live sending yet)
# ---------------------------------------------------------------------------
class NotificationRule(models.Model):
    TRIGGER_CHOICES = [
        ('approaching', 'Vehicle Approaching Service'),
        ('due_soon', 'Vehicle Due Soon'),
        ('overdue', 'Vehicle Overdue'),
        ('stale_mileage', 'Mileage Not Updated'),
    ]
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('in_system', 'In-System'),
    ]

    trigger_type = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_trigger_type_display()} → {self.get_channel_display()}"


class NotificationLog(models.Model):
    rule = models.ForeignKey(NotificationRule, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='notification_logs')
    channel = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    payload = models.TextField(blank=True)

    def __str__(self):
        return f"{self.vehicle} — {self.channel} ({self.status})"

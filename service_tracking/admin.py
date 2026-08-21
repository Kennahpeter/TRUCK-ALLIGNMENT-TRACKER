from django.contrib import admin

from .models import (
    AuditLog, Customer, MileageUpdate, NotificationLog, NotificationRule,
    ServiceFollowUp, ServiceRecord, ServiceThreshold, Vehicle,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'phone', 'email', 'vehicle_count')
    search_fields = ('company_name', 'contact_person', 'phone', 'email')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration', 'customer', 'vehicle_type', 'driver_name', 'active')
    list_filter = ('vehicle_type', 'active', 'customer')
    search_fields = ('truck__truck_id', 'fleet_number', 'driver_name')


@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_date', 'odometer_reading', 'service_type', 'total_cost')
    list_filter = ('service_type', 'service_date')
    date_hierarchy = 'service_date'
    search_fields = ('vehicle__truck__truck_id', 'technician')


@admin.register(MileageUpdate)
class MileageUpdateAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'odometer_reading', 'recorded_date', 'source', 'flagged_suspicious')
    list_filter = ('source', 'flagged_suspicious')
    date_hierarchy = 'recorded_date'


@admin.register(ServiceFollowUp)
class ServiceFollowUpAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'status', 'contact_date', 'staff_responsible', 'next_follow_up_date')
    list_filter = ('status',)


@admin.register(ServiceThreshold)
class ServiceThresholdAdmin(admin.ModelAdmin):
    list_display = ('approaching_km_remaining', 'due_soon_km_remaining', 'stale_mileage_days')

    def has_add_permission(self, request):
        # Singleton — only one row should ever exist.
        return not ServiceThreshold.objects.exists()


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_repr')
    list_filter = ('action', 'model_name')
    date_hierarchy = 'timestamp'
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('trigger_type', 'channel', 'active')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'channel', 'status', 'sent_at')

from django.contrib import admin

from .models import Alignment, Truck


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('truck_id', 'trailer_id', 'active')
    list_filter = ('active',)
    search_fields = ('truck_id', 'trailer_id')
    ordering = ('truck_id',)


@admin.register(Alignment)
class AlignmentAdmin(admin.ModelAdmin):
    list_display = (
        'truck_id',
        'trailer_id',
        'alignment_date',
        'alignment_time',
        'mileage',
        'tech_name',
        'created_at',
    )
    search_fields = ('truck_id', 'tech_name')
    list_filter = ('alignment_date', 'tech_name')
    date_hierarchy = 'alignment_date'
    ordering = ('-alignment_date', '-alignment_time')

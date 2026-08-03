from django.core.validators import MinValueValidator
from django.db import models


class Truck(models.Model):
    """
    A single truck/trailer pairing from the D&A Hauliers fleet register.
    Used to populate the Truck ID / Trailer ID dropdowns so technicians
    can only log alignments against real fleet units.
    """

    truck_id = models.CharField(max_length=20, unique=True)
    trailer_id = models.CharField(max_length=20, blank=True, null=True)
    active = models.BooleanField(default=True, help_text="Uncheck to retire a unit from the dropdowns.")

    class Meta:
        ordering = ['truck_id']
        verbose_name = "Fleet Truck"
        verbose_name_plural = "Fleet Trucks"

    def __str__(self):
        return f"{self.truck_id} ({self.trailer_id or 'no trailer'})"


class Alignment(models.Model):
    """
    Represents a single wheel-alignment service event for a truck
    (and, optionally, its attached trailer).
    """

    truck_id = models.CharField(
        max_length=20,
        blank=False,
        help_text="Unique identifier / unit number for the truck.",
    )
    trailer_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Trailer identifier, if applicable.",
    )
    alignment_date = models.DateField(
        help_text="Date the alignment service was performed.",
    )
    alignment_time = models.TimeField(
        help_text="Time the alignment service was performed.",
    )
    mileage = models.IntegerField(
        validators=[MinValueValidator(1, message="Mileage must be a positive number.")],
        help_text="Odometer reading (miles) at time of service.",
    )
    tech_name = models.CharField(
        max_length=100,
        help_text="Name of the technician who performed the alignment.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-alignment_date', '-alignment_time']
        verbose_name = "Alignment"
        verbose_name_plural = "Alignments"

    def __str__(self):
        return f"{self.truck_id} - {self.alignment_date} ({self.tech_name})"

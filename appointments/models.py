from django.db import models
from django.conf import settings

from hospital.models import Doctor, Service


class AppointmentSlot(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointment_slots'
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='appointment_slots'
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'doctor',
                    'service',
                    'date',
                    'start_time',
                ],
                name='unique_doctor_service_slot'
            )
        ]
        ordering = ['date', 'start_time']

    def __str__(self):
        return (
            f"{self.start_time.strftime('%H.%M')} - "
            f"{self.end_time.strftime('%H.%M')}"
        )


class Appointment(models.Model):

    class Status(models.TextChoices):
        BOOKED = 'BOOKED', 'Booked'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    # Authenticated patient who made the booking
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    username = models.CharField(
        max_length=200
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=15
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    date = models.DateField()

    slot = models.OneToOneField(
        AppointmentSlot,
        on_delete=models.CASCADE,
        related_name='appointment'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BOOKED
    )

    booked_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.doctor} - "
            f"{self.date} - "
            f"{self.slot}"
        )
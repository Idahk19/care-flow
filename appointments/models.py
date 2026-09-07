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

    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}"


class Appointment(models.Model):

    class Status(models.TextChoices):
        BOOKED = 'BOOKED', 'Booked'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

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

    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.email} - {self.slot}"
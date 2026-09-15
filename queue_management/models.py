from django.db import models

from appointments.models import Appointment


class QueueEntry(models.Model):

    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting'
        CALLED = 'CALLED', 'Called'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        SKIPPED = 'SKIPPED', 'Skipped'
        CANCELLED = 'CANCELLED', 'Cancelled'

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='queue_entry'
    )

    queue_number = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )

    checked_in_at = models.DateTimeField(
        auto_now_add=True
    )

    called_at = models.DateTimeField(
        null=True,
        blank=True
    )

    consultation_started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    consultation_completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['queue_number']

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'appointment',
                    'queue_number',
                ],
                name='unique_queue_entry_number'
            )
        ]

    def __str__(self):
        return (
            f"Queue #{self.queue_number} - "
            f"{self.appointment.patient.username}"
        )
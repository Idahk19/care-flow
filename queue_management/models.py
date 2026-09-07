from django.db import models
from django.conf import settings
from appointments.models import Appointment


class QueueEntry(models.Model):

    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting'
        CALLED = 'CALLED', 'Called'
        IN_SERVICE = 'IN_SERVICE', 'In Service'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='queue_entry'
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )

    queue_number = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )

    checked_in_at = models.DateTimeField(auto_now_add=True)

    estimated_wait_time = models.PositiveIntegerField(
        default=0,
        help_text="Estimated waiting time in minutes"
    )

    def __str__(self):
        return f"Queue #{self.queue_number} - {self.patient.email}"
    

class Notification(models.Model):

    class NotificationType(models.TextChoices):
        APPOINTMENT = 'APPOINTMENT', 'Appointment'
        CHECK_IN = 'CHECK_IN', 'Check In'
        QUEUE = 'QUEUE', 'Queue'
        CANCELLATION = 'CANCELLATION', 'Cancellation'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )

    message = models.TextField()

    is_sent = models.BooleanField(default=False)

    sent_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.email} - {self.notification_type}"
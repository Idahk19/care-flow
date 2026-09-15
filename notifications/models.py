from django.conf import settings
from django.db import models


class Notification(models.Model):

    class Type(models.TextChoices):
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        ALMOST_TURN = 'ALMOST_TURN', 'Almost Your Turn'
        YOUR_TURN = 'YOUR_TURN', 'Your Turn'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    queue_entry = models.ForeignKey(
        'queue_management.QueueEntry',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )

    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'queue_entry',
                    'notification_type',
                ],
                name='unique_queue_notification_type'
            )
        ]

    def __str__(self):
        return (
            f"{self.patient.username} - "
            f"{self.notification_type}"
        )
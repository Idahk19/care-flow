from .models import Notification


def create_notification(
    patient,
    queue_entry,
    notification_type,
    message,
):
    notification, created = Notification.objects.get_or_create(
        patient=patient,
        queue_entry=queue_entry,
        notification_type=notification_type,
        defaults={
            'message': message,
        }
    )

    return notification
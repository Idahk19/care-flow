from django.utils import timezone

from notifications.services import (
    create_notification,
    send_notification_sms,
)
from notifications.models import Notification

from .models import QueueEntry


AVERAGE_CONSULTATION_MINUTES = 30


def calculate_people_ahead(queue_entry):

    active_statuses = [
        QueueEntry.Status.WAITING,
        QueueEntry.Status.CALLED,
        QueueEntry.Status.IN_PROGRESS,
    ]

    return (
        QueueEntry.objects
        .filter(
            appointment__doctor=queue_entry.appointment.doctor,
            appointment__date=queue_entry.appointment.date,
            queue_number__lt=queue_entry.queue_number,
            status__in=active_statuses,
        )
        .count()
    )


def calculate_estimated_wait(queue_entry):

    people_ahead = calculate_people_ahead(queue_entry)

    current_patient = (
        QueueEntry.objects
        .filter(
            appointment__doctor=queue_entry.appointment.doctor,
            appointment__date=queue_entry.appointment.date,
            status=QueueEntry.Status.IN_PROGRESS,
        )
        .exclude(
            id=queue_entry.id
        )
        .first()
    )

    if not current_patient:
        return people_ahead * AVERAGE_CONSULTATION_MINUTES

    if current_patient.consultation_started_at:

        elapsed = (
            timezone.now()
            - current_patient.consultation_started_at
        ).total_seconds() / 60

        remaining_time = max(
            0,
            AVERAGE_CONSULTATION_MINUTES - elapsed
        )

    else:
        remaining_time = AVERAGE_CONSULTATION_MINUTES

    other_people_ahead = max(
        0,
        people_ahead - 1
    )

    return round(
        remaining_time
        + (
            other_people_ahead
            * AVERAGE_CONSULTATION_MINUTES
        )
    )


def notify_next_patient(doctor, date):

    next_patient = (
        QueueEntry.objects
        .select_related(
            'appointment__patient',
        )
        .filter(
            appointment__doctor=doctor,
            appointment__date=date,
            status=QueueEntry.Status.WAITING,
        )
        .order_by('queue_number')
        .first()
    )

    if not next_patient:
        return None

    message = (
        "You're almost up. "
        "Please be ready."
    )

    create_notification(
        patient=next_patient.appointment.patient,
        queue_entry=next_patient,
        notification_type=Notification.Type.ALMOST_TURN,
        message=message,
    )

    send_notification_sms(
        patient=next_patient.appointment.patient,
        message=message,
    )

    return next_patient
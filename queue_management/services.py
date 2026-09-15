from django.utils import timezone

from .models import QueueEntry


AVERAGE_CONSULTATION_MINUTES = 30


def calculate_people_ahead(queue_entry):
    """
    Calculate how many active patients are ahead
    of the given queue entry.
    """

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
    """
    Calculate the approximate waiting time in minutes.

    Uses a default average consultation time of
    20 minutes per patient.
    """

    people_ahead = calculate_people_ahead(queue_entry)

    # Find the patient currently being seen
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

    # If nobody is currently being seen
    if not current_patient:
        return people_ahead * AVERAGE_CONSULTATION_MINUTES

    # Calculate how long the current consultation
    # has already been running
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

    # The current patient is included in people_ahead,
    # so remove them before multiplying the remaining
    # patients by the full consultation duration.
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
from datetime import timedelta

from django.utils import timezone

from .models import Notification
from .sms import send_sms
from appointments.models import Appointment


def create_notification(
    patient,
    notification_type,
    message,
    appointment=None,
    queue_entry=None,
):
    if appointment is not None:
        notification, created = Notification.objects.get_or_create(
            patient=patient,
            appointment=appointment,
            notification_type=notification_type,
            defaults={
                'message': message,
            }
        )
    else:
        notification, created = Notification.objects.get_or_create(
            patient=patient,
            queue_entry=queue_entry,
            notification_type=notification_type,
            defaults={
                'message': message,
            }
        )

    return notification, created


def send_notification_sms(patient, message):
    phone_number = getattr(patient, 'phone', None)

    if not phone_number:
        return None

    try:
        return send_sms(
            phone_number,
            message
        )
    except Exception:
        return None


def send_appointment_reminders():
    now = timezone.localtime()

    reminder_start = now + timedelta(minutes=25)
    reminder_end = now + timedelta(minutes=35)

    appointments = Appointment.objects.select_related(
        'patient',
        'doctor',
        'service',
        'slot',
    ).filter(
        status=Appointment.Status.BOOKED,
        date=reminder_start.date(),
        slot__start_time__gte=reminder_start.time(),
        slot__start_time__lte=reminder_end.time(),
    )

    for appointment in appointments:

        doctor_name = (
            f"Dr. {appointment.doctor.first_name} "
            f"{appointment.doctor.last_name}"
        )

        appointment_time = appointment.slot.start_time.strftime(
            '%I:%M %p'
        )

        message = (
            f"Reminder: You have an appointment with "
            f"{doctor_name} for {appointment.service.name} "
            f"today at {appointment_time}. "
            f"Your appointment is in about 30 minutes."
        )

        notification, created = create_notification(
            patient=appointment.patient,
            appointment=appointment,
            notification_type=Notification.Type.APPOINTMENT_REMINDER,
            message=message,
        )

        if created:
            send_notification_sms(
                patient=appointment.patient,
                message=message,
            )
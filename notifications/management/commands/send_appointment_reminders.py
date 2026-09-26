from django.core.management.base import BaseCommand

from notifications.services import send_appointment_reminders


class Command(BaseCommand):
    help = 'Send appointment reminders for appointments starting soon'

    def handle(self, *args, **options):
        send_appointment_reminders()

        self.stdout.write(
            self.style.SUCCESS(
                'Appointment reminders checked successfully.'
            )
        )
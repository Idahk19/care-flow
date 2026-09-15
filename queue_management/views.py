from django.db import transaction
from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from appointments.models import Appointment
from hospital.models import Doctor
from .models import QueueEntry
from .serializers import (
    CheckInSerializer,
    DoctorQueueSerializer,
    QueueEntrySerializer,
)


class CheckInView(generics.CreateAPIView):

    serializer_class = CheckInSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    @transaction.atomic
    def perform_create(self, serializer):

        appointment_id = serializer.validated_data['appointment'].id

        appointment = (
            Appointment.objects
            .select_for_update()
            .select_related(
                'patient',
                'doctor'
            )
            .get(id=appointment_id)
        )

        today = timezone.localdate()

        # Appointment must be for today
        if appointment.date != today:
            raise ValidationError({
                'appointment': (
                    'Only appointments scheduled for today '
                    'can be checked in.'
                )
            })

        # Appointment cannot be cancelled
        if appointment.status == Appointment.Status.CANCELLED:
            raise ValidationError({
                'appointment': (
                    'This appointment has been cancelled '
                    'and cannot be checked in.'
                )
            })

        # Appointment cannot already be completed
        if appointment.status == Appointment.Status.COMPLETED:
            raise ValidationError({
                'appointment': (
                    'This appointment has already been completed.'
                )
            })

        # Check whether the patient is already in the queue
        if hasattr(appointment, 'queue_entry'):
            raise ValidationError({
                'appointment': (
                    'This patient has already been checked in '
                    'for this appointment.'
                )
            })

        # Lock the doctor so two receptionists cannot
        # generate the same queue number at the same time
        doctor = (
            Doctor.objects
            .select_for_update()
            .get(id=appointment.doctor_id)
        )

        # Find the highest queue number for this doctor today
        last_queue_entry = (
            QueueEntry.objects
            .filter(
                appointment__doctor=doctor,
                appointment__date=today
            )
            .order_by('-queue_number')
            .first()
        )

        if last_queue_entry:
            next_queue_number = (
                last_queue_entry.queue_number + 1
            )
        else:
            next_queue_number = 1

        # Create queue entry
        queue_entry = QueueEntry.objects.create(
            appointment=appointment,
            queue_number=next_queue_number,
            status=QueueEntry.Status.WAITING
        )

        # Update appointment status
        appointment.status = Appointment.Status.CHECKED_IN

        appointment.save(
            update_fields=['status']
        )

        serializer.instance = queue_entry

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        self.perform_create(serializer)

        queue_entry = serializer.instance

        response_serializer = QueueEntrySerializer(
            queue_entry,
            context={
                'request': request
            }
        )

        from rest_framework.response import Response
        from rest_framework import status

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

class DoctorQueueView(generics.GenericAPIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        today = timezone.localdate()

        doctor = request.user.doctor_profile

        queue = (
            QueueEntry.objects
            .filter(
                appointment__doctor=doctor,
                appointment__date=today,
                status__in=[
                    QueueEntry.Status.WAITING,
                    QueueEntry.Status.CALLED,
                    QueueEntry.Status.IN_PROGRESS,
                ]
            )
            .select_related(
                'appointment__patient'
            )
            .order_by('queue_number')
        )

        serializer = DoctorQueueSerializer(
            queue,
            many=True
        )

        return Response({
            'doctor': str(doctor),
            'queue_date': today,
            'total_people': queue.count(),
            'patients': serializer.data
        })
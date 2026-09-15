from django.db import transaction
from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from appointments.models import Appointment
from hospital.models import Doctor
from queue_management.services import notify_next_patient
from .models import QueueEntry
from .serializers import (
    CallNextPatientSerializer,
    CheckInSerializer,
    CompleteConsultationSerializer,
    DoctorQueueSerializer,
    MyQueueSerializer,
    QueueEntrySerializer,
    SkipPatientSerializer,
    StartConsultationSerializer,
)
from notifications.services import create_notification
from notifications.models import Notification


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

        create_notification(
              patient=appointment.patient,
              queue_entry=queue_entry,
              notification_type=Notification.Type.CHECKED_IN,
              message=(
                  f"You're checked in. "
                  f"Your queue number is #{queue_entry.queue_number}."
                ),
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
                    QueueEntry.Status.SKIPPED,
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

class CallNextPatientView(generics.GenericAPIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    @transaction.atomic
    def post(self, request):

        doctor = request.user.doctor_profile
        today = timezone.localdate()

        queue_entry = (
            QueueEntry.objects
            .select_for_update()
            .select_related(
                'appointment__patient',
                'appointment__doctor',
            )
            .filter(
                appointment__doctor=doctor,
                appointment__date=today,
                status=QueueEntry.Status.WAITING,
            )
            .order_by('queue_number')
            .first()
        )

        if not queue_entry:

            queue_entry = (
                QueueEntry.objects
                .select_for_update()
                .select_related(
                    'appointment__patient',
                    'appointment__doctor',
                )
                .filter(
                    appointment__doctor=doctor,
                    appointment__date=today,
                    status=QueueEntry.Status.SKIPPED,
                )
                .order_by('queue_number')
                .first()
            )

        if not queue_entry:
            raise ValidationError({
                'detail': (
                    'There are no patients waiting '
                    'in your queue.'
                )
            })

        queue_entry.status = QueueEntry.Status.CALLED
        queue_entry.called_at = timezone.now()

        queue_entry.save(
            update_fields=[
                'status',
                'called_at',
            ]
        )

        create_notification(
            patient=queue_entry.appointment.patient,
            queue_entry=queue_entry,
            notification_type=Notification.Type.YOUR_TURN,
            message=(
                'Your turn. '
                'Please proceed to the doctor\'s room.'
            ),
        )

        serializer = CallNextPatientSerializer(
            queue_entry
        )

        return Response(
            serializer.data,
            status=200
        )
class MyQueueView(generics.GenericAPIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        today = timezone.localdate()

        active_statuses = [
            QueueEntry.Status.WAITING,
            QueueEntry.Status.CALLED,
            QueueEntry.Status.IN_PROGRESS,
        ]

        queue_entry = (
            QueueEntry.objects
            .select_related(
                'appointment__patient',
                'appointment__doctor',
                'appointment__service',
            )
            .filter(
                appointment__patient=request.user,
                appointment__date=today,
                status__in=active_statuses,
            )
            .first()
        )

        if not queue_entry:
            return Response(
                {
                    'detail': (
                        'You are not currently in a queue.'
                    )
                },
                status=404
            )

        serializer = MyQueueSerializer(
            queue_entry
        )

        return Response(
            serializer.data,
            status=200
        )

class StartConsultationView(generics.GenericAPIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    @transaction.atomic
    def post(self, request):

        doctor = request.user.doctor_profile

        today = timezone.localdate()

        queue_entry = (
            QueueEntry.objects
            .select_for_update()
            .select_related(
                'appointment__patient',
                'appointment__doctor',
            )
            .filter(
                appointment__doctor=doctor,
                appointment__date=today,
                status=QueueEntry.Status.CALLED,
            )
            .order_by('called_at')
            .first()
        )

        if not queue_entry:
            raise ValidationError({
                'detail': (
                    'There is no called patient '
                    'to start.'
                )
            })

        queue_entry.status = QueueEntry.Status.IN_PROGRESS

        queue_entry.consultation_started_at = timezone.now()

        queue_entry.save(
            update_fields=[
                'status',
                'consultation_started_at',
            ]
        )

        serializer = StartConsultationSerializer(
            queue_entry
        )

        return Response(
            serializer.data,
            status=200
        )

class CompleteConsultationView(generics.GenericAPIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    @transaction.atomic
    def post(self, request):

        doctor = request.user.doctor_profile

        today = timezone.localdate()

        queue_entry = (
            QueueEntry.objects
            .select_for_update()
            .select_related(
                'appointment__patient',
                'appointment__doctor',
            )
            .filter(
                appointment__doctor=doctor,
                appointment__date=today,
                status=QueueEntry.Status.IN_PROGRESS,
            )
            .order_by('consultation_started_at')
            .first()
        )

        if not queue_entry:
            raise ValidationError({
                'detail': (
                    'There is no consultation '
                    'currently in progress.'
                )
            })

        queue_entry.status = QueueEntry.Status.COMPLETED

        queue_entry.consultation_completed_at = timezone.now()

        queue_entry.save(
            update_fields=[
                'status',
                'consultation_completed_at',
            ]
        )

        appointment = queue_entry.appointment

        appointment.status = Appointment.Status.COMPLETED

        appointment.save(
            update_fields=['status']
        )

        serializer = CompleteConsultationSerializer(
            queue_entry
        )

        return Response(
            serializer.data,
            status=200
        )
class SkipPatientView(generics.GenericAPIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    @transaction.atomic
    def post(self, request):

        doctor = request.user.doctor_profile

        today = timezone.localdate()

        queue_entry = (
            QueueEntry.objects
            .select_for_update()
            .select_related(
                'appointment__patient',
                'appointment__doctor',
            )
            .filter(
                appointment__doctor=doctor,
                appointment__date=today,
                status=QueueEntry.Status.CALLED,
            )
            .order_by('called_at')
            .first()
        )

        if not queue_entry:
            raise ValidationError({
                'detail': (
                    'There is no called patient '
                    'to skip.'
                )
            })

        queue_entry.status = QueueEntry.Status.SKIPPED

        queue_entry.save(
            update_fields=[
                'status',
            ]
        )

        next_patient = notify_next_patient(
            doctor=doctor,
            date=today,
        )

        serializer = SkipPatientSerializer(
            queue_entry
        )

        return Response(
            {
                'skipped_patient': serializer.data,
                'next_patient_notified': (
                    next_patient is not None
                ),
            },
            status=200
        )
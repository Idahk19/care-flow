from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import User

from notifications.models import Notification
from notifications.services import (
    create_notification,
    send_notification_sms,
)

from .models import Appointment, AppointmentSlot
from .serializers import (
    AdminAppointmentSerializer,
    AppointmentBookingSerializer,
    AvailableSlotSerializer,
    AppointmentUpdateSerializer,
    DoctorAppointmentSerializer,
)


class AppointmentCreateView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):

        slot_id = serializer.validated_data['slot'].id

        slot = (
            AppointmentSlot.objects
            .select_for_update()
            .get(id=slot_id)
        )

        if not slot.is_available:
            raise ValidationError({
                'slot': (
                    'This time slot has already been booked. '
                    'Please select another slot.'
                )
            })

        if hasattr(slot, 'appointment'):
            raise ValidationError({
                'slot': (
                    'This time slot has already been booked. '
                    'Please select another slot.'
                )
            })

        appointment = serializer.save(
            patient=self.request.user,
            slot=slot
        )

        slot.is_available = False
        slot.save(update_fields=['is_available'])

        doctor_name = (
            f"Dr. {appointment.doctor.first_name} "
            f"{appointment.doctor.last_name}"
        )

        service_name = appointment.service.name

        appointment_time = appointment.slot.start_time.strftime(
            '%I:%M %p'
        )

        message = (
            f"Your appointment has been booked successfully "
            f"with {doctor_name} for {service_name} on "
            f"{appointment.date} at {appointment_time}."
        )

        create_notification(
            patient=appointment.patient,
            appointment=appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            message=message,
        )

        send_notification_sms(
            patient=appointment.patient,
            message=message,
        )


class AppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user
        ).order_by('-booked_at')


class AppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser or user.role == User.Role.ADMIN:
            return Appointment.objects.all().order_by('-booked_at')

        if hasattr(user, 'doctor_profile'):
            return Appointment.objects.filter(
                doctor=user.doctor_profile
            ).order_by('-booked_at')

        return Appointment.objects.filter(
            patient=user
        ).order_by('-booked_at')


class AppointmentUpdateView(generics.UpdateAPIView):
    serializer_class = AppointmentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user
        )

    @transaction.atomic
    def perform_update(self, serializer):

        appointment = self.get_object()

        old_slot = appointment.slot

        new_status = serializer.validated_data.get('status')
        new_slot = serializer.validated_data.get('slot')

        if new_status == Appointment.Status.CANCELLED:

            serializer.save(
                status=Appointment.Status.CANCELLED
            )

            old_slot.is_available = True
            old_slot.save(
                update_fields=['is_available']
            )

            return

        if new_slot is None:
            serializer.save()
            return

        if new_slot.id == old_slot.id:
            serializer.save()
            return

        if not new_slot.is_available:
            raise ValidationError({
                'slot': (
                    'This time slot has already been booked. '
                    'Please select another slot.'
                )
            })

        old_slot.is_available = True
        old_slot.save(
            update_fields=['is_available']
        )

        new_slot.is_available = False
        new_slot.save(
            update_fields=['is_available']
        )

        serializer.save(
            slot=new_slot
        )


class AppointmentDeleteView(generics.DestroyAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user
        )

    @transaction.atomic
    def perform_destroy(self, instance):

        slot = (
            AppointmentSlot.objects
            .select_for_update()
            .get(id=instance.slot_id)
        )

        slot.is_available = True
        slot.save(update_fields=['is_available'])

        instance.delete()


class AvailableSlotListView(generics.ListAPIView):
    serializer_class = AvailableSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        doctor_id = self.request.query_params.get('doctor')
        service_id = self.request.query_params.get('service')
        date_string = self.request.query_params.get('date')

        if not doctor_id or not service_id or not date_string:
            raise ValidationError({
                'error': 'doctor, service and date are required.'
            })

        try:
            requested_date = datetime.strptime(
                date_string,
                '%Y-%m-%d'
            ).date()
        except ValueError:
            raise ValidationError({
                'date': 'Use the format YYYY-MM-DD.'
            })

        if requested_date < timezone.localdate():
            raise ValidationError({
                'date': 'You cannot view slots for a previous day.'
            })

        slots = AppointmentSlot.objects.filter(
            doctor_id=doctor_id,
            service_id=service_id,
            date=requested_date
        )

        if not slots.exists():

            start_time = time(8, 0)
            closing_time = time(18, 0)

            current_time = datetime.combine(
                requested_date,
                start_time
            )

            end_time = datetime.combine(
                requested_date,
                closing_time
            )

            new_slots = []

            while current_time < end_time:

                slot_end = current_time + timedelta(minutes=30)

                if slot_end > end_time:
                    break

                new_slots.append(
                    AppointmentSlot(
                        doctor_id=doctor_id,
                        service_id=service_id,
                        date=requested_date,
                        start_time=current_time.time(),
                        end_time=slot_end.time(),
                        is_available=True
                    )
                )

                current_time = slot_end

            AppointmentSlot.objects.bulk_create(
                new_slots,
                ignore_conflicts=True
            )

            slots = AppointmentSlot.objects.filter(
                doctor_id=doctor_id,
                service_id=service_id,
                date=requested_date
            )

        return slots.filter(
            is_available=True
        ).order_by('start_time')


class DoctorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {'error': 'Doctor access required.'},
                status=403
            )

        doctor = request.user.doctor_profile
        today = timezone.localdate()

        appointments = Appointment.objects.filter(
            doctor=doctor,
            date=today
        )

        return Response({
            'today': appointments.count(),

            'in_progress': appointments.filter(
                status=Appointment.Status.CHECKED_IN
            ).count(),

            'completed': appointments.filter(
                status=Appointment.Status.COMPLETED
            ).count(),

            'skipped': appointments.filter(
                status=Appointment.Status.CANCELLED
            ).count(),
        })


class DoctorTodayAppointmentsView(generics.ListAPIView):
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        doctor = self.request.user.doctor_profile

        return Appointment.objects.filter(
            doctor=doctor
        ).select_related(
            'patient',
            'service',
            'slot'
        ).order_by(
            '-date',
            '-slot__start_time'
        )


class AdminAppointmentListView(generics.ListAPIView):
    serializer_class = AdminAppointmentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Appointment.objects.all().select_related(
            'patient',
            'doctor',
            'service',
            'slot',
        ).order_by('-booked_at')
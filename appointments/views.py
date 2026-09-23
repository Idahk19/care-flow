from datetime import datetime, time, timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from accounts.models import User
from .models import Appointment, AppointmentSlot
from .serializers import (
    AdminAppointmentSerializer,
    AppointmentBookingSerializer,
    AvailableSlotSerializer,
    AppointmentUpdateSerializer,
    DoctorAppointmentSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Appointment
# Create/book an appointment
class AppointmentCreateView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic # Run everything inside this function as one database transaction
    def perform_create(self, serializer):

        slot_id = serializer.validated_data['slot'].id

        # Lock the slot while booking it
        slot = (
            AppointmentSlot.objects
            .select_for_update()
            .get(id=slot_id)
        )

        # Check availability again inside the transaction
        if not slot.is_available:
            raise ValidationError({
                'slot': 'This time slot has already been booked. Please select another slot.'
            })

        if hasattr(slot, 'appointment'):
            raise ValidationError({
                'slot': 'This time slot has already been booked. Please select another slot.'
            })

        appointment = serializer.save(
            patient=self.request.user,
            slot=slot
        )

        slot.is_available = False
        slot.save(update_fields=['is_available'])


# View patient's appointments
class AppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user
        ).order_by('-booked_at')


# View one appointment
class AppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin sees all appointments
        if user.is_superuser or user.role == User.Role.ADMIN:
            return Appointment.objects.all().order_by('-booked_at')

        # Doctor sees only appointments assigned to them
        if hasattr(user, 'doctor_profile'):
            return Appointment.objects.filter(
                doctor=user.doctor_profile
            ).order_by('-booked_at')

        # Patient sees only appointments they booked
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

        # Cancel appointment
        if new_status == Appointment.Status.CANCELLED:

            serializer.save(
                status=Appointment.Status.CANCELLED
            )

            old_slot.is_available = True
            old_slot.save(
                update_fields=['is_available']
            )

            return

        # No new slot selected
        if new_slot is None:
            serializer.save()
            return

        # Same slot
        if new_slot.id == old_slot.id:
            serializer.save()
            return

        # New slot is already booked
        if not new_slot.is_available:
            raise ValidationError({
                'slot': (
                    'This time slot has already been booked. '
                    'Please select another slot.'
                )
            })

        # Release old slot
        old_slot.is_available = True
        old_slot.save(
            update_fields=['is_available']
        )

        # Book new slot
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
        # Make the slot available again
        slot = (
            AppointmentSlot.objects
            .select_for_update()
            .get(id=instance.slot_id)
        )

        slot.is_available = True
        slot.save(update_fields=['is_available'])

        # Delete the appointment
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

        # Do not allow past dates
        if requested_date < timezone.localdate():
            raise ValidationError({
                'date': 'You cannot view slots for a previous day.'
            })

        # Check if slots already exist
        slots = AppointmentSlot.objects.filter(
            doctor_id=doctor_id,
            service_id=service_id,
            date=requested_date
        )

        # If no slots exist, generate slots for the selected date
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

            # Get the newly-created slots
            slots = AppointmentSlot.objects.filter(
                doctor_id=doctor_id,
                service_id=service_id,
                date=requested_date
            )

        # Return ONLY slots that are still available
        return slots.filter(
            is_available=True
        ).order_by('start_time')

class DoctorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Make sure the logged-in user is a doctor
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {'error': 'Doctor access required.'},
                status=403
            )

        doctor = request.user.doctor_profile
        today = timezone.localdate()

        # Today's appointments for this doctor
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
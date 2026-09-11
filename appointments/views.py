from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from accounts.models import User
from .models import Appointment, AppointmentSlot
from .serializers import (
    AppointmentBookingSerializer,
)

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
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user
        )

    def perform_update(self, serializer):
        old_slot = self.get_object().slot
        new_slot = serializer.validated_data.get('slot')

        if new_slot is None or new_slot == old_slot:
            serializer.save()
            return

        if not new_slot.is_available:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({
                'slot': 'This slot has already been booked. Please select another slot.'
            })

        old_slot.is_available = True
        old_slot.save(update_fields=['is_available'])

        new_slot.is_available = False
        new_slot.save(update_fields=['is_available'])

        serializer.save(slot=new_slot)


class AppointmentCancelView(generics.UpdateAPIView):
    serializer_class = AppointmentBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user
        )

    def perform_update(self, serializer):
        appointment = serializer.save(
            status=Appointment.Status.CANCELLED
        )

        appointment.slot.is_available = True
        appointment.slot.save(update_fields=['is_available'])

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

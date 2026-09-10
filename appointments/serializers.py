from rest_framework import serializers

from .models import Appointment, AppointmentSlot
from hospital.models import Doctor, Service


class AppointmentBookingSerializer(serializers.ModelSerializer):
    # Patient information comes from the logged-in user
    username = serializers.CharField(
        source='patient.username',
        read_only=True
    )

    email = serializers.EmailField(
        source='patient.email',
        read_only=True
    )

    phone = serializers.CharField(
        source='patient.phone',
        read_only=True
    )

    # Booking selections
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        write_only=True
    )

    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.filter(is_active=True),
        write_only=True
    )

    date = serializers.DateField(
        write_only=True
    )

    slot = serializers.PrimaryKeyRelatedField(
        queryset=AppointmentSlot.objects.filter(is_available=True)
    )

    # Nice readable output
    service_name = serializers.CharField(
        source='slot.service.name',
        read_only=True
    )

    doctor_name = serializers.SerializerMethodField(
        read_only=True
    )

    appointment_date = serializers.DateField(
        source='slot.date',
        read_only=True
    )

    start_time = serializers.TimeField(
        source='slot.start_time',
        read_only=True
    )

    end_time = serializers.TimeField(
        source='slot.end_time',
        read_only=True
    )

    class Meta:
        model = Appointment

        fields = [
            'id',
            'username',
            'email',
            'phone',

            'service',
            'doctor',
            'date',
            'slot',

            'service_name',
            'doctor_name',
            'appointment_date',
            'start_time',
            'end_time',

            'status',
            'booked_at',
        ]

        read_only_fields = [
            'id',
            'username',
            'email',
            'phone',
            'service_name',
            'doctor_name',
            'appointment_date',
            'start_time',
            'end_time',
            'status',
            'booked_at',
        ]

    def get_doctor_name(self, obj):
        doctor = obj.slot.doctor
        return f"Dr. {doctor.first_name} {doctor.last_name}"

    def validate(self, attrs):
        service = attrs.get('service')
        doctor = attrs.get('doctor')
        date = attrs.get('date')
        slot = attrs.get('slot')

        # Make sure the selected slot matches the selected service
        if slot.service_id != service.id:
            raise serializers.ValidationError({
                'slot': 'The selected time slot does not belong to the selected service.'
            })

        # Make sure the selected slot matches the selected doctor
        if slot.doctor_id != doctor.id:
            raise serializers.ValidationError({
                'slot': 'The selected time slot does not belong to the selected doctor.'
            })

        # Make sure the selected slot matches the selected date
        if slot.date != date:
            raise serializers.ValidationError({
                'slot': 'The selected time slot does not belong to the selected date.'
            })

        # Check availability
        if not slot.is_available:
            raise serializers.ValidationError({
                'slot': 'This time slot has already been booked. Please select another slot.'
            })

        # Because Appointment.slot is OneToOneField
        if hasattr(slot, 'appointment'):
            raise serializers.ValidationError({
                'slot': 'This time slot has already been booked. Please select another slot.'
            })

        return attrs
    
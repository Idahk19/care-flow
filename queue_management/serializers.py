from rest_framework import serializers

from appointments.models import Appointment
from .models import QueueEntry

from .services import (
    calculate_people_ahead,
    calculate_estimated_wait,
)


class CheckInSerializer(serializers.Serializer):

    appointment = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.all()
    )

class QueueEntrySerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(
        source='appointment.patient.get_full_name',
        read_only=True
    )

    doctor_name = serializers.SerializerMethodField()

    appointment_date = serializers.DateField(
        source='appointment.date',
        read_only=True
    )

    class Meta:
        model = QueueEntry

        fields = [
            'id',
            'appointment',
            'patient_name',
            'doctor_name',
            'appointment_date',
            'queue_number',
            'status',
            'checked_in_at',
            'called_at',
            'consultation_started_at',
            'consultation_completed_at',
        ]

        read_only_fields = [
            'id',
            'patient_name',
            'doctor_name',
            'appointment_date',
            'queue_number',
            'status',
            'checked_in_at',
            'called_at',
            'consultation_started_at',
            'consultation_completed_at',
        ]

    def get_doctor_name(self, obj):
        doctor = obj.appointment.doctor

        return (
            f"Dr. {doctor.first_name} "
            f"{doctor.last_name}"
        )

class DoctorQueueSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(
        source='appointment.patient.get_full_name',
        read_only=True
    )

    people_ahead = serializers.SerializerMethodField()

    estimated_wait_minutes = serializers.SerializerMethodField()

    class Meta:
        model = QueueEntry

        fields = [
            'id',
            'queue_number',
            'patient_name',
            'status',
            'checked_in_at',
            'called_at',
            'people_ahead',
            'estimated_wait_minutes',
        ]

    def get_people_ahead(self, obj):
        return calculate_people_ahead(obj)

    def get_estimated_wait_minutes(self, obj):
        return calculate_estimated_wait(obj)
    
class MyQueueSerializer(serializers.ModelSerializer):

    doctor_name = serializers.SerializerMethodField()

    service_name = serializers.CharField(
        source='appointment.service.name',
        read_only=True
    )

    people_ahead = serializers.SerializerMethodField()

    estimated_wait_minutes = serializers.SerializerMethodField()

    message = serializers.SerializerMethodField()

    class Meta:
        model = QueueEntry

        fields = [
            'queue_number',
            'status',
            'doctor_name',
            'service_name',
            'people_ahead',
            'estimated_wait_minutes',
            'message',
        ]

    def get_doctor_name(self, obj):
        doctor = obj.appointment.doctor

        return (
            f"Dr. {doctor.first_name} "
            f"{doctor.last_name}"
        )

    def get_people_ahead(self, obj):
        return calculate_people_ahead(obj)

    def get_estimated_wait_minutes(self, obj):

        if obj.status in [
            QueueEntry.Status.CALLED,
            QueueEntry.Status.IN_PROGRESS,
        ]:
            return 0

        return calculate_estimated_wait(obj)

    def get_message(self, obj):

        if obj.status == QueueEntry.Status.CALLED:
            return (
                "It's your turn. "
                "Please proceed to the doctor's room."
            )

        if obj.status == QueueEntry.Status.IN_PROGRESS:
            return "Your consultation is in progress."

        people_ahead = calculate_people_ahead(obj)

        if people_ahead == 0:
            return "You are next. Please be ready."

        if people_ahead == 1:
            return "There is 1 patient ahead of you."

        return (
            f"There are {people_ahead} patients "
            f"ahead of you."
        )

class CallNextPatientSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(
        source='appointment.patient.get_full_name',
        read_only=True
    )

    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = QueueEntry

        fields = [
            'id',
            'queue_number',
            'patient_name',
            'doctor_name',
            'status',
            'called_at',
        ]

        read_only_fields = [
            'id',
            'queue_number',
            'patient_name',
            'doctor_name',
            'status',
            'called_at',
        ]

    def get_doctor_name(self, obj):

        doctor = obj.appointment.doctor

        return (
            f"Dr. {doctor.first_name} "
            f"{doctor.last_name}"
        )

class StartConsultationSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(
        source='appointment.patient.get_full_name',
        read_only=True
    )

    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = QueueEntry

        fields = [
            'id',
            'queue_number',
            'patient_name',
            'doctor_name',
            'status',
            'consultation_started_at',
        ]

        read_only_fields = [
            'id',
            'queue_number',
            'patient_name',
            'doctor_name',
            'status',
            'consultation_started_at',
        ]

    def get_doctor_name(self, obj):
        doctor = obj.appointment.doctor

        return (
            f"Dr. {doctor.first_name} "
            f"{doctor.last_name}"
        )
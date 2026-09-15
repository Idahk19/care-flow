from rest_framework import serializers

from appointments.models import Appointment
from .models import QueueEntry


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
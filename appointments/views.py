from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            appointment = serializer.save()

            return Response(
                AppointmentSerializer(appointment).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()

        appointment.status = 'CANCELLED'
        appointment.save()

        return Response({
            'message': 'Appointment cancelled successfully.',
            'appointment': AppointmentSerializer(appointment).data
        })

    @action(detail=True, methods=['get'])
    def appointment_status(self, request, pk=None):
        appointment = self.get_object()

        return Response({
            'appointment_id': appointment.id,
            'status': appointment.status
        })
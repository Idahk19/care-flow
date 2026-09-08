from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import QueueEntry
from .serializers import QueueEntrySerializer


class QueueEntryViewSet(viewsets.ModelViewSet):
    queryset = QueueEntry.objects.all()
    serializer_class = QueueEntrySerializer

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        queue_entry = self.get_object()

        queue_entry.status = 'WAITING'
        queue_entry.save()

        return Response({
            'message': 'Patient checked in successfully.',
            'queue_entry': QueueEntrySerializer(queue_entry).data
        })

    @action(detail=True, methods=['get'])
    def position(self, request, pk=None):
        queue_entry = self.get_object()

        patients_ahead = QueueEntry.objects.filter(
            status='WAITING',
            created_at__lt=queue_entry.created_at
        ).count()

        return Response({
            'queue_position': patients_ahead + 1,
            'patients_ahead': patients_ahead
        })

    @action(detail=True, methods=['get'])
    def estimated_wait(self, request, pk=None):
        queue_entry = self.get_object()

        patients_ahead = QueueEntry.objects.filter(
            status='WAITING',
            created_at__lt=queue_entry.created_at
        ).count()

        # Temporary estimate: 15 minutes per patient
        estimated_minutes = patients_ahead * 15

        return Response({
            'patients_ahead': patients_ahead,
            'estimated_wait_minutes': estimated_minutes
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        queue_entry = self.get_object()

        queue_entry.status = 'COMPLETED'
        queue_entry.save()

        return Response({
            'message': 'Queue entry completed.',
            'queue_entry': QueueEntrySerializer(queue_entry).data
        })

    @action(detail=False, methods=['get'])
    def waiting(self, request):
        queue = QueueEntry.objects.filter(
            status='WAITING'
        ).order_by('created_at')

        return Response(
            QueueEntrySerializer(queue, many=True).data
        )

    @action(detail=False, methods=['post'])
    def call_next(self, request):
        queue_entry = QueueEntry.objects.filter(
            status='WAITING'
        ).order_by('created_at').first()

        if not queue_entry:
            return Response(
                {'message': 'No patients are currently waiting.'},
                status=status.HTTP_404_NOT_FOUND
            )

        queue_entry.status = 'IN_PROGRESS'
        queue_entry.save()

        return Response({
            'message': 'Next patient called.',
            'queue_entry': QueueEntrySerializer(queue_entry).data
        })
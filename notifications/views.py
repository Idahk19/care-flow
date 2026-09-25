from rest_framework import generics, permissions

from .models import Notification
from .serializers import NotificationSerializer


class MyNotificationsView(generics.ListAPIView):

    serializer_class = NotificationSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        return (
            Notification.objects
            .filter(
                patient=self.request.user
            )
            .order_by('-created_at')
        )



class MarkNotificationReadView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        return Notification.objects.filter(
            patient=self.request.user
        )

    def update(self, request, *args, **kwargs):
        notification = self.get_object()

        notification.is_read = True
        notification.save(
            update_fields=['is_read']
        )

        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )
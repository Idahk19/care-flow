from django.urls import path

from .views import CheckInView, DoctorQueueView


urlpatterns = [
    path(
        'check-in/',
        CheckInView.as_view(),
        name='queue-check-in'
    ),
    path(
        'doctor/',
        DoctorQueueView.as_view(),
        name='doctor-queue'
    ),
]
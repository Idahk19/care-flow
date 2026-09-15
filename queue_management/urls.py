from django.urls import path

from .views import CallNextPatientView, CheckInView, DoctorQueueView, MyQueueView, MyQueueView, StartConsultationView, StartConsultationView


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
    path(
        'doctor/call-next/',
        CallNextPatientView.as_view(),
        name='doctor-call-next'
    ),
    path(
        'my-queue/',
        MyQueueView.as_view(),
        name='my-queue'
    ),
    path(
        'doctor/start/',
        StartConsultationView.as_view(),
        name='doctor-start-consultation'
    ),
]
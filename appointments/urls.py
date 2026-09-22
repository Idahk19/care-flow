from django.urls import path

from .views import (
    AdminAppointmentListView,
    AppointmentListView,
    AppointmentCreateView,
    AppointmentDetailView,
    AppointmentUpdateView,
    AppointmentDeleteView,
    AvailableSlotListView,
    DoctorDashboardView,
    DoctorTodayAppointmentsView,
)

urlpatterns = [
    path('', AppointmentListView.as_view(), name='appointment-list'),

    path(
        'book/',
        AppointmentCreateView.as_view(),
        name='appointment-book'
    ),

    path(
        'slots/',
        AvailableSlotListView.as_view(),
        name='available-slots'
    ),

    path(
        '<int:pk>/',
        AppointmentDetailView.as_view(),
        name='appointment-detail'
    ),

    path(
        '<int:pk>/update/',
        AppointmentUpdateView.as_view(),
        name='appointment-update'
    ),

    path(
        '<int:pk>/delete/',
        AppointmentDeleteView.as_view(),
        name='appointment-delete'
    ),
    path(
        'doctor/dashboard/',
        DoctorDashboardView.as_view(),
        name='doctor-dashboard'
    ),
    path(
    'doctor/today/',
    DoctorTodayAppointmentsView.as_view(),
    name='doctor-today-appointments'
),
path(
    'admin/',
    AdminAppointmentListView.as_view(),
    name='admin-appointment-list'
),
]
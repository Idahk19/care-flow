from django.urls import path

from .views import (
    AppointmentCreateView,
    AppointmentListView,
    AppointmentDetailView,
    AppointmentUpdateView,
    AppointmentCancelView,
)

urlpatterns = [
    path(
        '',
        AppointmentListView.as_view(),
        name='appointment-list'
    ),

    path(
        'book/',
        AppointmentCreateView.as_view(),
        name='appointment-book'
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
        '<int:pk>/cancel/',
        AppointmentCancelView.as_view(),
        name='appointment-cancel'
    ),
]
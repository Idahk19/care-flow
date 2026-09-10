from django.urls import path

from .views import (
    DepartmentViewSet,
    DoctorViewSet,
    ServiceViewSet,
)


urlpatterns = [
    # Departments
    path(
        'departments/',
        DepartmentViewSet.as_view({
            'get': 'list',
            'post': 'create',
        }),
        name='department-list',
    ),

    path(
        'departments/<int:pk>/',
        DepartmentViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='department-detail',
    ),

    # Doctors
    path(
        'doctors/',
        DoctorViewSet.as_view({
            'get': 'list',
            'post': 'create',
        }),
        name='doctor-list',
    ),

    path(
        'doctors/<int:pk>/',
        DoctorViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='doctor-detail',
    ),

    # Services
    path(
        'services/',
        ServiceViewSet.as_view({
            'get': 'list',
            'post': 'create',
        }),
        name='service-list',
    ),

    path(
        'services/<int:pk>/',
        ServiceViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='service-detail',
    ),
]
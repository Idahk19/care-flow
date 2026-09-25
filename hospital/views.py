from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAdminUser
from rest_framework import generics
from rest_framework.views import APIView, Response
from accounts.models import User
from appointments.models import Appointment
from .models import Department, Doctor, Service
from .serializers import (
    AdminPatientSerializer,
    DepartmentSerializer,
    DoctorCreateSerializer,
    DoctorSerializer,
    ServiceSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminUser]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]

        return [permission() for permission in permission_classes]

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]

        return [permission() for permission in permission_classes]

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    

    def get(self, request):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Admin access required.'},
                status=403
            )

        return Response({
            'total_patients': User.objects.filter(role='PATIENT').count(),
            'total_doctors': Doctor.objects.count(),
            'total_services': Service.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'total_users': User.objects.count(),
            'total_departments': Department.objects.count(),
        })

class AdminPatientListView(generics.ListAPIView):
    serializer_class = AdminPatientSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        if self.request.user.role != 'ADMIN':
            return User.objects.none()

        return User.objects.filter(
            role='PATIENT'
        ).order_by('id')


class AdminPatientDeleteView(generics.DestroyAPIView):
    serializer_class = AdminPatientSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        if self.request.user.role != 'ADMIN':
            return User.objects.none()

        return User.objects.filter(
            role='PATIENT'
        )
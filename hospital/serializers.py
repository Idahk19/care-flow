from rest_framework import serializers
from .models import Department, Doctor, Service


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            'id',
            'name',
            'description',
            'is_active',
        ]
        read_only_fields = ['id']


class DoctorSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source='department.name',
        read_only=True
    )

    class Meta:
        model = Doctor
        fields = [
            'id',
            'department',
            'department_name',
            'first_name',
            'last_name',
            'specialization',
            'phone_number',
            'email',
            'is_active',
        ]
        read_only_fields = ['id', 'department_name']


class ServiceSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source='department.name',
        read_only=True
    )

    class Meta:
        model = Service
        fields = [
            'id',
            'department',
            'department_name',
            'name',
            'description',
            'is_active',
        ]
        read_only_fields = ['id', 'department_name']
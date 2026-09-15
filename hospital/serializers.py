from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Department, Doctor, Service


User = get_user_model()


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


class DoctorCreateSerializer(serializers.ModelSerializer):

    username = serializers.CharField(read_only=True)
    temporary_password = serializers.CharField(read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id',
            'username',
            'temporary_password',
            'department',
            'first_name',
            'last_name',
            'specialization',
            'phone_number',
            'email',
            'is_active',
        ]

        read_only_fields = [
            'id',
            'username',
            'temporary_password',
        ]

    def create(self, validated_data):

        first_name = validated_data['first_name'].strip().lower()
        last_name = validated_data['last_name'].strip().lower()

        # Remove spaces from the name
        first_name = first_name.replace(' ', '')
        last_name = last_name.replace(' ', '')

        base_username = f"{first_name}{last_name}"
        username = base_username

        # Make sure the username is unique
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Generate temporary password
        temporary_password = f"{username}@careflow"

        # Create the User account
        user = User.objects.create_user(
            username=username,
            password=temporary_password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data.get('email') or '',
            role=User.Role.STAFF,
        )

        # Make sure this doctor is not a Django admin
        user.is_staff = False
        user.is_superuser = False
        user.save()

        # Create the Doctor
        doctor = Doctor.objects.create(
            user=user,
            **validated_data
        )

        # Store the generated credentials temporarily
        doctor._generated_username = username
        doctor._generated_password = temporary_password

        return doctor

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['username'] = getattr(
            instance,
            '_generated_username',
            instance.user.username if instance.user else None
        )

        data['temporary_password'] = getattr(
            instance,
            '_generated_password',
            None
        )

        return data
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer
)


class RegisterView(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'message': 'Account created successfully.',
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is not None:
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'message': 'Login successful.',
                    'token': token.key,
                    'user': UserSerializer(user).data
                })

            return Response({
                'error': 'Invalid email or password.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()

        return Response({
            'message': 'Logout successful.'
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                'message': 'Profile updated successfully.',
                'user': serializer.data
            })

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class UserListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('id')
        serializer = UserSerializer(users, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {
                    'error': 'Current password and new password are required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the user's current password
        user = authenticate(
            username=request.user.username,
            password=current_password
        )

        if user is None:
            return Response(
                {
                    'error': 'Current password is incorrect.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {
                    'error': 'New password must be at least 8 characters.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if current_password == new_password:
            return Response(
                {
                    'error': 'New password must be different from the current password.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Hash and store the new password
        user.set_password(new_password)
        user.save()

        return Response(
            {
                'message': 'Password changed successfully.'
            },
            status=status.HTTP_200_OK
        )
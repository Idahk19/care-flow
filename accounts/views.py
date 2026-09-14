from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer
)


class RegisterView(APIView):

    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response({
                'message': 'Account created successfully.',
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
                refresh = RefreshToken.for_user(user)

                return Response({
                    'message': 'Login successful.',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })

            return Response({
                'error': 'Invalid username or password.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Logout successful.'},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


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
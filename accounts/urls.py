from django.urls import path

from .views import (
    ChangePasswordView,
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    UserListView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/', UserListView.as_view(), name='user-detail'),
    path(
        'change-password/',
        ChangePasswordView.as_view(),
        name='change-password'
    ),
]
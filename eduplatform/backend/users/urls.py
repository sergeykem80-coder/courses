from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    RefreshTokenAPIView,
    LogoutAPIView,
    MeAPIView,
    ProfileAPIView,
)

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('refresh/', RefreshTokenAPIView.as_view(), name='token-refresh'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    
    # User profile endpoints
    path('me/', MeAPIView.as_view(), name='me'),
    path('me/profile/', ProfileAPIView.as_view(), name='profile'),
]

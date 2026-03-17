from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer,
    UserDetailSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    POST /api/auth/register/
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'Пользователь успешно зарегистрирован',
            'user_id': user.id,
            'email': user.email,
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(TokenObtainPairView):
    """
    API endpoint for user login.
    POST /api/auth/login/
    Returns JWT access and refresh tokens.
    """
    pass


class RefreshTokenAPIView(TokenRefreshView):
    """
    API endpoint for refreshing access token.
    POST /api/auth/refresh/
    """
    pass


class LogoutAPIView(APIView):
    """
    API endpoint for user logout.
    POST /api/auth/logout/
    Note: For full logout with token blacklisting, add SIMPLE_JWT blacklist app.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # In production with token blacklisting, add token to blacklist here
        return Response({
            'message': 'Выход выполнен успешно'
        }, status=status.HTTP_200_OK)


class MeAPIView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for current user data.
    GET /api/auth/me/ - get current user data
    PUT /api/auth/me/ - update current user data
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileSerializer
        return UserDetailSerializer


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for user profile.
    GET /api/me/profile/ - get profile
    PUT /api/me/profile/ - update profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = User.objects.get().profile.get_or_create(user=self.request.user)
        return profile

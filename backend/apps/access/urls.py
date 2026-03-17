"""
URL маршруты для приложения access
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StudentAccessViewSet, LessonProgressViewSet, AdminAccessViewSet
)


# Создаем роутер для API
router = DefaultRouter()

# Студенческие endpoints
router.register(
    r'me',
    StudentAccessViewSet,
    basename='student-access'
)

# Прогресс уроков
router.register(
    r'progress',
    LessonProgressViewSet,
    basename='lesson-progress'
)

# Админские endpoints
router.register(
    r'admin',
    AdminAccessViewSet,
    basename='admin-access'
)


urlpatterns = [
    # API endpoints через router
    path('', include(router.urls)),
]

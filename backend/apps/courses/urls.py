"""
URL маршруты для приложения courses
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, CourseViewSet, PublicCourseViewSet,
    ModuleViewSet, LessonViewSet
)


# Создаем роутер для API
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'public/courses', PublicCourseViewSet, basename='public-course')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'lessons', LessonViewSet, basename='lesson')


urlpatterns = [
    # API endpoints через router
    path('', include(router.urls)),
]

# Для удобства можно добавить дополнительные пути вручную
# Например: path('courses/<slug:slug>/enroll/', ...)

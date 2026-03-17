"""
Courses app URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    ModuleViewSet,
    LessonViewSet,
    PublicCourseListView,
    PublicCourseDetailView,
)

router = DefaultRouter()
router.register(r'', CourseViewSet, basename='course')

app_name = 'courses'

urlpatterns = [
    # Public endpoints (no authentication required for browsing)
    path('public/', PublicCourseListView.as_view(), name='course-list-public'),
    path('public/<slug:slug>/', PublicCourseDetailView.as_view(), name='course-detail-public'),
    
    # Admin/Authenticated endpoints
    path('', include(router.urls)),
]

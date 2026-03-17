"""
Views for the courses app.

Provides API endpoints for course management and public browsing.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.shortcuts import get_object_or_404
from .models import Course, Module, Lesson, Category
from .serializers import (
    CourseSerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    ModuleSerializer,
    LessonSerializer,
    CategorySerializer,
)


class IsAdminOrCurator(permissions.BasePermission):
    """Permission check for admin and curator roles."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role in ['admin', 'curator']
        )


class PublicCourseListView(ListAPIView):
    """Public endpoint to list all published courses."""
    queryset = Course.objects.filter(status='published').select_related('category', 'author')
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search by title or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) | 
                models.Q(description__icontains=search)
            )
        
        # Filter by max price
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset


class PublicCourseDetailView(RetrieveAPIView):
    """Public endpoint to get course details by slug."""
    queryset = Course.objects.filter(status='published').select_related('category', 'author')
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class CourseViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for courses.
    Access: Admin/Curator only.
    """
    queryset = Course.objects.all().select_related('category', 'author')
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCurator]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ModuleViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for modules.
    Access: Admin/Curator only.
    """
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCurator]
    
    def get_queryset(self):
        course_id = self.request.query_params.get('course_id')
        if course_id:
            return Module.objects.filter(course_id=course_id).order_by('order_index')
        return Module.objects.all().order_by('order_index')
    
    def perform_create(self, serializer):
        course_id = self.request.data.get('course')
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            # Auto-set order_index if not provided
            if not serializer.validated_data.get('order_index'):
                last_module = Module.objects.filter(course=course).order_by('-order_index').first()
                next_index = (last_module.order_index + 1) if last_module else 0
                serializer.save(course=course, order_index=next_index)
            else:
                serializer.save(course=course)


class LessonViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for lessons.
    Access: Admin/Curator only.
    """
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCurator]
    
    def get_queryset(self):
        module_id = self.request.query_params.get('module_id')
        if module_id:
            return Lesson.objects.filter(module_id=module_id).order_by('order_index')
        return Lesson.objects.all().order_by('order_index')
    
    def perform_create(self, serializer):
        module_id = self.request.data.get('module')
        if module_id:
            module = get_object_or_404(Module, id=module_id)
            # Auto-set order_index if not provided
            if not serializer.validated_data.get('order_index'):
                last_lesson = Lesson.objects.filter(module=module).order_by('-order_index').first()
                next_index = (last_lesson.order_index + 1) if last_lesson else 0
                serializer.save(module=module, order_index=next_index)
            else:
                serializer.save(module=module)

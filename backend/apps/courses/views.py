"""
Views для курсов, модулей и уроков.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Category, Course, Module, Lesson
from .serializers import (
    CategorySerializer, CategoryListSerializer,
    CourseListSerializer, CourseDetailSerializer, 
    CourseCreateUpdateSerializer, CoursePublicSerializer,
    ModuleSerializer, ModuleCreateUpdateSerializer,
    LessonListSerializer, LessonDetailSerializer,
    LessonCreateUpdateSerializer
)


class IsAdminOrCurator(permissions.BasePermission):
    """Разрешение только для администраторов и кураторов"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role in ['admin', 'curator']
        )


class IsAuthenticatedOrFreePreview(permissions.BasePermission):
    """Доступ к уроку: авторизованный пользователь или бесплатный предпросмотр"""
    
    def has_object_permission(self, request, view, obj):
        # Бесплатный предпросмотр доступен всем
        if obj.is_free_preview:
            return True
        
        # Для авторизованных пользователей проверяем доступ к курсу
        if request.user and request.user.is_authenticated:
            # Проверяем наличие доступа к курсу через UserCourseAccess
            from apps.access.models import UserCourseAccess
            return UserCourseAccess.objects.filter(
                user=request.user,
                course=obj.module.course,
                is_active=True
            ).exists()
        
        return False


# ==================== Категории ====================

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для категорий курсов (только чтение)
    
    list: Список всех категорий
    retrieve: Детальная информация о категории
    courses: Список курсов в категории
    """
    queryset = Category.objects.all()
    filter_backends = [OrderingFilter]
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Получить все опубликованные курсы в категории"""
        category = self.get_object()
        courses = category.courses.filter(status='published')
        serializer = CoursePublicSerializer(courses, many=True)
        return Response(serializer.data)


# ==================== Курсы ====================

class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления курсами
    
    list: Список курсов (публичный или админский в зависимости от прав)
    retrieve: Детальная информация о курсе
    create: Создать курс (admin/curator)
    update: Обновить курс (admin/curator)
    destroy: Удалить курс (admin/curator)
    modules: Получить модули курса
    """
    queryset = Course.objects.select_related('category', 'author').prefetch_related('modules')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title', 'description', 'short_description']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']
    
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Фильтрация курсов в зависимости от прав пользователя"""
        queryset = super().get_queryset()
        
        # Если не админ/куратор, показываем только опубликованные
        if not (self.request.user and 
                self.request.user.role in ['admin', 'curator']):
            queryset = queryset.filter(status='published')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        elif self.action == 'list' and (
            self.request.user and 
            self.request.user.role in ['admin', 'curator']
        ):
            return CourseListSerializer
        return CoursePublicSerializer
    
    def get_permissions(self):
        """Разные права для разных действий"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrCurator]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Установка автора при создании курса"""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['get'])
    def modules(self, request, slug=None):
        """Получить все модули курса с уроками"""
        course = self.get_object()
        modules = course.modules.prefetch_related('lessons').order_by('order_index')
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)


# ==================== Публичные курсы (витрина) ====================

class PublicCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Публичный ViewSet для витрины курсов
    Доступен всем без аутентификации
    """
    queryset = Course.objects.filter(status='published').select_related('category')
    serializer_class = CoursePublicSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'description', 'short_description']
    ordering_fields = ['created_at', 'price']
    ordering = ['-created_at']
    
    lookup_field = 'slug'
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Список категорий с количеством курсов"""
        categories = Category.objects.annotate(
            courses_count=Count('courses', filter=Q(courses__status='published'))
        ).filter(courses_count__gt=0)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


# ==================== Модули (Admin only) ====================

class ModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления модулями (только admin/curator)
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAdminOrCurator]
    
    def get_queryset(self):
        return Module.objects.all().prefetch_related('lessons')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ModuleCreateUpdateSerializer
        return ModuleSerializer
    
    def perform_create(self, serializer):
        """Сохранение модуля с курсом из query params"""
        course_id = self.request.query_params.get('course_id')
        if course_id:
            course = Course.objects.get(id=course_id)
            serializer.save(course=course)
        else:
            raise serializers.ValidationError("Необходимо указать course_id")


# ==================== Уроки ====================

class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления уроками
    
    Для студентов: только чтение с проверкой доступа
    Для администраторов: полный CRUD
    """
    filter_backends = [OrderingFilter]
    ordering_fields = ['order_index']
    ordering = ['order_index']
    
    def get_queryset(self):
        return Lesson.objects.select_related('module__course')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return LessonCreateUpdateSerializer
        return LessonDetailSerializer
    
    def get_permissions(self):
        """Разные права для разных действий"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrCurator]
        else:
            permission_classes = [IsAuthenticatedOrFreePreview]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def embed(self, request, pk=None):
        """Получить embed URL для урока"""
        lesson = self.get_object()
        embed_url = lesson.get_embed_url(request)
        
        if not embed_url:
            return Response(
                {'error': 'Видео не найдено'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({'embed_url': embed_url})

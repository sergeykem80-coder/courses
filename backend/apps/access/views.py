"""
Views для управления доступом к курсам и прогрессом обучения.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from .models import UserCourseAccess, LessonProgress
from .serializers import (
    UserCourseAccessSerializer, GrantCourseAccessSerializer,
    LessonProgressSerializer, UpdateLessonProgressSerializer,
    CourseProgressSerializer
)
from apps.courses.models import Course, Lesson


class IsAdminOrCurator(permissions.BasePermission):
    """Разрешение только для администраторов и кураторов"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role in ['admin', 'curator']
        )


class StudentAccessViewSet(viewsets.ViewSet):
    """
    ViewSet для студентов: просмотр своих курсов и доступа
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """
        Получить список курсов пользователя с доступом
        """
        accesses = UserCourseAccess.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('course__category')
        
        # Фильтруем истекшие доступа
        active_accesses = [
            acc for acc in accesses 
            if not acc.is_expired()
        ]
        
        serializer = UserCourseAccessSerializer(active_accesses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='courses/(?P<course_id>[^/.]+)/progress')
    def course_progress(self, request, course_id=None):
        """
        Получить прогресс по конкретному курсу
        """
        # Проверяем доступ к курсу
        access = get_object_or_404(
            UserCourseAccess,
            user=request.user,
            course_id=course_id,
            is_active=True
        )
        
        if access.is_expired():
            return Response(
                {'error': 'Доступ к курсу истек'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        course = access.course
        
        # Получаем все уроки курса
        total_lessons = Lesson.objects.filter(
            module__course=course
        ).count()
        
        # Получаем завершенные уроки
        completed_lessons = LessonProgress.objects.filter(
            user=request.user,
            lesson__module__course=course,
            is_completed=True
        ).count()
        
        # Вычисляем процент
        progress_percent = 0.0
        if total_lessons > 0:
            progress_percent = round((completed_lessons / total_lessons) * 100, 2)
        
        # Находим следующий урок для продолжения
        completed_lesson_ids = LessonProgress.objects.filter(
            user=request.user,
            is_completed=True
        ).values_list('lesson_id', flat=True)
        
        next_lesson = Lesson.objects.filter(
            module__course=course
        ).exclude(id__in=completed_lesson_ids).order_by(
            'module__order_index',
            'order_index'
        ).first()
        
        from apps.courses.serializers import LessonDetailSerializer
        
        data = {
            'course_id': course.id,
            'course_title': course.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percent': progress_percent,
            'next_lesson': LessonDetailSerializer(
                next_lesson,
                context={'request': request}
            ).data if next_lesson else None
        }
        
        return Response(data)


class LessonProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления прогрессом уроков
    """
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LessonProgress.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='lessons/(?P<lesson_id>[^/.]+)/update')
    def update_lesson_progress(self, request, lesson_id=None):
        """
        Обновить прогресс урока
        POST /api/access/progress/lessons/{lesson_id}/update/
        Body: {"is_completed": true, "last_watched_second": 120}
        """
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Проверяем доступ к курсу
        has_access = UserCourseAccess.objects.filter(
            user=request.user,
            course=lesson.module.course,
            is_active=True
        ).exists()
        
        # Или это бесплатный предпросмотр
        if not has_access and not lesson.is_free_preview:
            return Response(
                {'error': 'Нет доступа к этому уроку'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UpdateLessonProgressSerializer(
            data=request.data,
            context={'lesson': lesson}
        )
        serializer.is_valid(raise_exception=True)
        
        # Получаем или создаем прогресс
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        # Обновляем поля
        if 'last_watched_second' in serializer.validated_data:
            progress.update_progress(
                serializer.validated_data['last_watched_second']
            )
        
        if serializer.validated_data.get('is_completed'):
            progress.mark_completed()
        
        return Response(LessonProgressSerializer(progress).data)


class AdminAccessViewSet(viewsets.ViewSet):
    """
    ViewSet для администраторов: управление доступом пользователей
    """
    permission_classes = [IsAdminOrCurator]
    
    @action(detail=False, methods=['post'], url_path='users/(?P<user_id>[^/.]+)/grant-course')
    def grant_course_access(self, request, user_id=None):
        """
        Выдать доступ пользователю к курсу
        POST /api/access/admin/users/{user_id}/grant-course/
        Body: {"course_id": 123, "expires_at": "2026-12-31T23:59:59"}
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = get_object_or_404(User, id=user_id)
        
        serializer = GrantCourseAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course = Course.objects.get(id=serializer.validated_data['course_id'])
        
        # Создаем или обновляем доступ
        access, created = UserCourseAccess.objects.update_or_create(
            user=user,
            course=course,
            defaults={
                'granted_by': request.user,
                'expires_at': serializer.validated_data.get('expires_at'),
                'is_active': True
            }
        )
        
        return Response({
            'message': 'Доступ успешно выдан',
            'access': UserCourseAccessSerializer(access).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['delete'], url_path='users/(?P<user_id>[^/.]+)/revoke-course/(?P<course_id>[^/.]+)')
    def revoke_course_access(self, request, user_id=None, course_id=None):
        """
        Отозвать доступ пользователя к курсу
        DELETE /api/access/admin/users/{user_id}/revoke-course/{course_id}/
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = get_object_or_404(User, id=user_id)
        course = get_object_or_404(Course, id=course_id)
        
        try:
            access = UserCourseAccess.objects.get(user=user, course=course)
            access.is_active = False
            access.save()
            
            return Response({'message': 'Доступ отозван'})
        except UserCourseAccess.DoesNotExist:
            return Response(
                {'error': 'Доступ не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def user_accesses(self, request):
        """
        Получить все доступы пользователя (админ просмотр)
        GET /api/access/admin/user_accesses/?user_id=123
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'Необходимо указать user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)
        
        accesses = UserCourseAccess.objects.filter(
            user=user
        ).select_related('course__category')
        
        serializer = UserCourseAccessSerializer(accesses, many=True)
        return Response(serializer.data)

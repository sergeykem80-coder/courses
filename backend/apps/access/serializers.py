"""
Serializers для управления доступом и прогрессом.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import UserCourseAccess, LessonProgress
from apps.courses.models import Course
from apps.courses.serializers import CourseListSerializer, LessonDetailSerializer


class UserCourseAccessSerializer(serializers.ModelSerializer):
    """Сериализатор доступа пользователя к курсу"""
    course = CourseListSerializer(read_only=True)
    granted_by_name = serializers.CharField(
        source='granted_by.get_full_name',
        read_only=True
    )
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = UserCourseAccess
        fields = [
            'id', 'user', 'course', 'granted_at', 'granted_by',
            'granted_by_name', 'expires_at', 'is_active', 'is_expired'
        ]
        read_only_fields = ['granted_at', 'granted_by']
    
    def get_is_expired(self, obj) -> bool:
        return obj.is_expired()


class GrantCourseAccessSerializer(serializers.Serializer):
    """Сериализатор для выдачи доступа к курсу"""
    course_id = serializers.IntegerField()
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate_course_id(self, value):
        """Проверка существования курса"""
        try:
            course = Course.objects.get(id=value)
            if course.status != 'published':
                raise serializers.ValidationError(
                    "Курс не опубликован"
                )
        except Course.DoesNotExist:
            raise serializers.ValidationError("Курс не найден")
        return value
    
    def validate_expires_at(self, value):
        """Проверка даты истечения"""
        if value and value < timezone.now():
            raise serializers.ValidationError(
                "Дата истечения должна быть в будущем"
            )
        return value


class LessonProgressSerializer(serializers.ModelSerializer):
    """Сериализатор прогресса урока"""
    lesson = LessonDetailSerializer(read_only=True)
    progress_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'user', 'lesson', 'is_completed',
            'last_watched_second', 'completed_at',
            'updated_at', 'progress_percent'
        ]
        read_only_fields = ['user', 'completed_at', 'updated_at']
    
    def get_progress_percent(self, obj) -> float:
        """Процент просмотра видео"""
        if not obj.lesson.duration_seconds:
            return 0.0
        
        percent = (obj.last_watched_second / obj.lesson.duration_seconds) * 100
        return min(round(percent, 2), 100.0)


class UpdateLessonProgressSerializer(serializers.Serializer):
    """Сериализатор для обновления прогресса"""
    is_completed = serializers.BooleanField(required=False)
    last_watched_second = serializers.IntegerField(
        required=False,
        min_value=0
    )
    
    def validate_last_watched_second(self, value):
        """Проверка что время не больше длительности урока"""
        lesson = self.context.get('lesson')
        if lesson and lesson.duration_seconds:
            if value > lesson.duration_seconds:
                # Не блокируем, но можно добавить предупреждение
                pass
        return value


class CourseProgressSerializer(serializers.Serializer):
    """Сериализатор общего прогресса по курсу"""
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    total_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    next_lesson = LessonDetailSerializer(read_only=True)

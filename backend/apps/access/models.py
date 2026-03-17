"""
Модели для управления доступом к курсам и прогрессом обучения.
"""
from django.db import models
from django.conf import settings


class UserCourseAccess(models.Model):
    """
    Связь пользователь-курс: кто имеет доступ к каким курсам
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_accesses',
        verbose_name='Пользователь'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        verbose_name='Курс'
    )
    granted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата предоставления доступа'
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_accesses',
        verbose_name='Кто выдал доступ'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата истечения доступа',
        help_text="Для курсов с подпиской или временным доступом"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    
    class Meta:
        db_table = 'user_course_access'
        verbose_name = 'Доступ к курсу'
        verbose_name_plural = 'Доступы к курсам'
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['course', 'is_active']),
        ]
    
    def __str__(self):
        status = "активен" if self.is_active else "неактивен"
        return f"{self.user.email} -> {self.course.title} ({status})"
    
    def is_expired(self):
        """Проверка истечения срока доступа"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at


class LessonProgress(models.Model):
    """
    Прогресс прохождения уроков
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.CASCADE,
        verbose_name='Урок'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Завершен'
    )
    last_watched_second = models.PositiveIntegerField(
        default=0,
        verbose_name='Последняя просмотренная секунда',
        help_text="Для видео-уроков"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        db_table = 'lesson_progress'
        verbose_name = 'Прогресс урока'
        verbose_name_plural = 'Прогресс уроков'
        unique_together = ['user', 'lesson']
        indexes = [
            models.Index(fields=['user', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]
    
    def __str__(self):
        status = "завершен" if self.is_completed else "в процессе"
        return f"{self.user.email} - {self.lesson.title} ({status})"
    
    def mark_completed(self):
        """Отметить урок как завершенный"""
        from django.utils import timezone
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    
    def update_progress(self, seconds: int):
        """Обновить прогресс просмотра"""
        self.last_watched_second = seconds
        self.save()

"""
Models for the payments app.

Includes access tracking models for user-course relationships.
"""
from django.db import models
from django.conf import settings
from courses.models import Course, Lesson
from orders.models import Order


class PaymentNotification(models.Model):
    """
    Stores raw webhook notifications from payment systems.
    Useful for debugging and audit trails.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payment_notifications',
        verbose_name="Заказ"
    )
    raw_data = models.JSONField(
        default=dict,
        verbose_name="Исходные данные"
    )
    processed = models.BooleanField(
        default=False,
        verbose_name="Обработано"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата получения"
    )
    
    class Meta:
        db_table = 'payment_notifications'
        verbose_name = "Платёжное уведомление"
        verbose_name_plural = "Платёжные уведомления"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for Order {self.order.id} - {'Processed' if self.processed else 'Pending'}"


class UserCourseAccess(models.Model):
    """Tracks which users have access to which courses."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_accesses',
        verbose_name="Пользователь"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='user_accesses',
        verbose_name="Курс"
    )
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата выдачи")
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_accesses',
        verbose_name="Выдал доступ"
    )
    expires_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Действует до",
        help_text="Для курсов с подпиской"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        db_table = 'user_course_access'
        verbose_name = "Доступ к курсу"
        verbose_name_plural = "Доступы к курсам"
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} -> {self.course.title}"


class LessonProgress(models.Model):
    """Tracks user progress through lessons."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name="Пользователь"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name="Урок"
    )
    is_completed = models.BooleanField(default=False, verbose_name="Завершено")
    last_watched_second = models.PositiveIntegerField(
        default=0, 
        verbose_name="Последняя просмотренная секунда"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата завершения"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        db_table = 'lesson_progress'
        verbose_name = "Прогресс урока"
        verbose_name_plural = "Прогрессы уроков"
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        return f"{self.user.email} - {self.lesson.title} ({self.last_watched_second}s)"

"""
Django Admin конфигурация для приложения Access.
Управление доступом пользователей к курсам и отслеживание прогресса.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import datetime
from .models import UserCourseAccess, LessonProgress


@admin.register(UserCourseAccess)
class UserCourseAccessAdmin(admin.ModelAdmin):
    """Админка для управления доступом пользователей к курсам"""
    
    list_display = (
        'user', 
        'course', 
        'granted_at', 
        'expires_at', 
        'is_active',
        'status_badge',
        'granted_by'
    )
    list_filter = ('is_active', 'granted_at', 'expires_at', 'course')
    search_fields = ('user__email', 'user__username', 'course__title', 'course__slug')
    ordering = ('-granted_at',)
    date_hierarchy = 'granted_at'
    
    fieldsets = (
        ('Доступ', {
            'fields': (
                'user',
                'course',
                'is_active',
            ),
        }),
        ('Даты', {
            'fields': (
                'granted_at',
                'expires_at',
            ),
        }),
        ('Информация о выдаче', {
            'fields': ('granted_by',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('granted_at', 'granted_by')
    
    def status_badge(self, obj):
        """Цветной индикатор статуса доступа"""
        if not obj.is_active:
            color = '#dc3545'
            label = 'Неактивен'
        elif obj.expires_at and obj.expires_at < timezone.now():
            color = '#ffc107'
            label = 'Истёк'
        else:
            color = '#28a745'
            label = 'Активен'
        
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:12px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Статус'
    
    def save_model(self, request, obj, form, change):
        """Автоматическая установка granted_by при создании"""
        if not change and not obj.granted_by:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_access', 'deactivate_access', 'extend_access_30_days']
    
    def activate_access(self, request, queryset):
        """Массовое действие: Активировать доступ"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} записей активировано.')
    activate_access.short_description = 'Активировать выбранные'
    
    def deactivate_access(self, request, queryset):
        """Массовое действие: Деактивировать доступ"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} записей деактивировано.')
    deactivate_access.short_description = 'Деактивировать выбранные'
    
    def extend_access_30_days(self, request, queryset):
        """Массовое действие: Продлить доступ на 30 дней"""
        from datetime import timedelta
        count = 0
        for access in queryset:
            if access.expires_at:
                access.expires_at += timedelta(days=30)
            else:
                access.expires_at = timezone.now() + timedelta(days=30)
            access.save()
            count += 1
        self.message_user(request, f'Доступ продлён для {count} пользователей.')
    extend_access_30_days.short_description = 'Продлить доступ на 30 дней'


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """Админка для отслеживания прогресса студентов"""
    
    list_display = (
        'user', 
        'lesson', 
        'course_name',
        'is_completed', 
        'last_watched_second',
        'duration_display',
        'completed_at',
        'updated_at'
    )
    list_filter = ('is_completed', 'completed_at', 'lesson__module__course')
    search_fields = (
        'user__email', 
        'user__username', 
        'lesson__title',
        'lesson__module__course__title'
    )
    ordering = ('-updated_at',)
    date_hierarchy = 'completed_at'
    
    def course_name(self, obj):
        """Название курса"""
        return obj.lesson.module.course.title if obj.lesson and obj.lesson.module else '-'
    course_name.short_description = 'Курс'
    
    def duration_display(self, obj):
        """Форматирование просмотренного времени"""
        if not obj.last_watched_second:
            return '0:00'
        minutes = obj.last_watched_second // 60
        seconds = obj.last_watched_second % 60
        return f"{minutes}:{seconds:02d}"
    duration_display.short_description = 'Просмотрено'
    
    actions = ['mark_as_completed', 'reset_progress']
    
    def mark_as_completed(self, request, queryset):
        """Массовое действие: Отметить как завершённые"""
        from datetime import timezone
        updated = queryset.update(
            is_completed=True,
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} уроков отмечено как завершённые.')
    mark_as_completed.short_description = 'Отметить как завершённые'
    
    def reset_progress(self, request, queryset):
        """Массовое действие: Сбросить прогресс"""
        updated = queryset.update(
            is_completed=False,
            last_watched_second=0,
            completed_at=None
        )
        self.message_user(request, f'Прогресс сброшен для {updated} уроков.')
    reset_progress.short_description = 'Сбросить прогресс'

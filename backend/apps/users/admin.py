"""
Django Admin конфигурация для приложения Users.
Расширенное управление пользователями и их профилями.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline для профиля пользователя"""
    
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ('bio', 'city', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Расширенная админка для пользователей с ролями"""
    
    list_display = (
        'username', 
        'email', 
        'role', 
        'is_active',
        'is_email_verified',
        'has_profile',
        'date_joined',
        'last_login'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'is_email_verified')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__city')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'email')
        }),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar', 'avatar_preview')
        }),
        ('Права доступа', {
            'fields': (
                'role',
                'is_active', 
                'is_staff', 
                'is_superuser',
                'is_email_verified',
                'groups', 
                'user_permissions',
            ),
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 
                'email', 
                'password1', 
                'password2', 
                'role',
                'is_active'
            ),
        }),
    )
    
    inlines = [UserProfileInline]
    
    readonly_fields = ('last_login', 'date_joined', 'avatar_preview')
    
    def avatar_preview(self, obj):
        """Предпросмотр аватара пользователя"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-width:150px; max-height:150px; border-radius:50%; border:2px solid #ccc;" />',
                obj.avatar.url
            )
        return "Нет аватара"
    avatar_preview.short_description = 'Аватар'
    
    def has_profile(self, obj):
        """Индикатор наличия заполненного профиля"""
        if hasattr(obj, 'profile'):
            return format_html('<span style="color:green;">✓ Профиль заполнен</span>')
        return format_html('<span style="color:#999;">— Профиль не создан</span>')
    has_profile.short_description = 'Профиль'
    
    actions = [
        'activate_users', 
        'deactivate_users', 
        'verify_emails',
        'make_student',
        'make_curator',
        'make_admin'
    ]
    
    def activate_users(self, request, queryset):
        """Массовое действие: Активировать пользователей"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} пользователей активировано.')
    activate_users.short_description = 'Активировать выбранных'
    
    def deactivate_users(self, request, queryset):
        """Массовое действие: Деактивировать пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} пользователей деактивировано.')
    deactivate_users.short_description = 'Деактивировать выбранных'
    
    def verify_emails(self, request, queryset):
        """Массовое действие: Подтвердить email адреса"""
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'Email подтверждён для {updated} пользователей.')
    verify_emails.short_description = 'Подтвердить email'
    
    def make_student(self, request, queryset):
        """Массовое действие: Установить роль Студент"""
        updated = queryset.update(role='student')
        self.message_user(request, f'Роль "Студент" установлена для {updated} пользователей.')
    make_student.short_description = 'Установить роль: Студент'
    
    def make_curator(self, request, queryset):
        """Массовое действие: Установить роль Куратор"""
        updated = queryset.update(role='curator')
        self.message_user(request, f'Роль "Куратор" установлена для {updated} пользователей.')
    make_curator.short_description = 'Установить роль: Куратор'
    
    def make_admin(self, request, queryset):
        """Массовое действие: Установить роль Администратор"""
        updated = queryset.update(role='admin')
        self.message_user(request, f'Роль "Администратор" установлена для {updated} пользователей.')
    make_admin.short_description = 'Установить роль: Администратор'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Админка для профилей пользователей"""
    
    list_display = ('user', 'city', 'bio_preview', 'created_at')
    list_filter = ('city', 'created_at')
    search_fields = ('user__email', 'user__username', 'bio', 'city')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def bio_preview(self, obj):
        """Краткое описание биографии"""
        if obj.bio:
            return obj.bio[:100] + ('...' if len(obj.bio) > 100 else '')
        return '-'
    bio_preview.short_description = 'О себе'

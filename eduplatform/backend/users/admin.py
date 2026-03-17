from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    list_display = ('email', 'username', 'role', 'is_email_verified', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_email_verified', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar')
        }),
        ('Права доступа', {
            'fields': ('role', 'is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""
    list_display = ('user', 'city', 'created_at')
    list_filter = ('city', 'created_at')
    search_fields = ('user__email', 'bio', 'city')
    readonly_fields = ('created_at',)

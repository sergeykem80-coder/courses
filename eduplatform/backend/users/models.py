from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access control.
    Roles: student, curator, admin
    """
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('curator', 'Куратор'),
        ('admin', 'Администратор'),
    ]
    
    email = models.EmailField(unique=True, verbose_name='Email')
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='student',
        verbose_name='Роль'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True, 
        verbose_name='Аватар'
    )
    is_email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_curator(self):
        return self.role in ['curator', 'admin']
    
    @property
    def is_admin_user(self):
        return self.role == 'admin'


class UserProfile(models.Model):
    """
    Extended user profile with additional information.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='Пользователь'
    )
    bio = models.TextField(blank=True, verbose_name='О себе')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f"Profile: {self.user.email}"

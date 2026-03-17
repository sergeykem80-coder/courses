"""
Models for the courses app.

Defines Course, Module, Lesson, and Category models.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    """Course category for organizing courses."""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, verbose_name="Слаг")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    class Meta:
        db_table = 'categories'
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Main course model with all course information."""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'Архив'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название курса")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Слаг")
    description = models.TextField(verbose_name="Полное описание")
    short_description = models.CharField(max_length=300, blank=True, verbose_name="Краткое описание")
    cover_image = models.ImageField(upload_to='courses/covers/', verbose_name="Обложка")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='courses',
        verbose_name="Категория"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Статус"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={'role__in': ['admin', 'curator']},
        related_name='created_courses',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        db_table = 'courses'
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_total_lessons(self):
        """Get total number of lessons in the course."""
        return Lesson.objects.filter(module__course=self).count()
    
    def get_total_modules(self):
        """Get total number of modules in the course."""
        return self.modules.count()


class Module(models.Model):
    """Module/Section within a course."""
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='modules',
        verbose_name="Курс"
    )
    title = models.CharField(max_length=200, verbose_name="Название модуля")
    order_index = models.PositiveIntegerField(default=0, verbose_name="Порядковый номер")
    
    class Meta:
        db_table = 'modules'
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"
        ordering = ['order_index']
        unique_together = ['course', 'order_index']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """Individual lesson within a module."""
    CONTENT_TYPES = [
        ('video', 'Видео'),
        ('text', 'Текст'),
        ('quiz', 'Тест'),
        ('attachment', 'Файл'),
    ]
    
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='lessons',
        verbose_name="Модуль"
    )
    title = models.CharField(max_length=200, verbose_name="Название урока")
    content_type = models.CharField(
        max_length=20, 
        choices=CONTENT_TYPES, 
        default='video',
        verbose_name="Тип контента"
    )
    kinescope_video_id = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="ID видео Kinescope",
        help_text="ID видео из Kinescope.io"
    )
    kinescope_embed_code = models.TextField(
        blank=True, 
        verbose_name="Embed код Kinescope",
        help_text="Готовый iframe-код для вставки"
    )
    text_content = models.TextField(blank=True, verbose_name="Текстовое содержимое")
    order_index = models.PositiveIntegerField(default=0, verbose_name="Порядковый номер")
    is_free_preview = models.BooleanField(
        default=False, 
        verbose_name="Бесплатный предпросмотр",
        help_text="Доступно без покупки курса"
    )
    duration_seconds = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Длительность (секунды)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        db_table = 'lessons'
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['order_index']
        unique_together = ['module', 'order_index']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def get_next_lesson(self):
        """Get the next lesson in the same module."""
        return Lesson.objects.filter(
            module=self.module, 
            order_index__gt=self.order_index
        ).order_by('order_index').first()
    
    def get_previous_lesson(self):
        """Get the previous lesson in the same module."""
        return Lesson.objects.filter(
            module=self.module, 
            order_index__lt=self.order_index
        ).order_by('-order_index').first()

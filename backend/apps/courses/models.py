"""
Модели для курсов, модулей и уроков.
"""
from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    """Категории курсов"""
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Слаг')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Курс обучения"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'Архив'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название курса')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')
    description = models.TextField(verbose_name='Полное описание')
    short_description = models.CharField(
        max_length=300, 
        blank=True, 
        verbose_name='Краткое описание'
    )
    cover_image = models.ImageField(
        upload_to='courses/covers/', 
        verbose_name='Обложка курса'
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена'
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='courses',
        verbose_name='Категория'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='Статус'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={'role__in': ['admin', 'curator']},
        related_name='authored_courses',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'courses'
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_lessons_count(self):
        """Количество уроков в курсе"""
        return Lesson.objects.filter(module__course=self).count()
    
    def get_duration(self):
        """Общая длительность курса в секундах"""
        from django.db.models import Sum
        result = Lesson.objects.filter(
            module__course=self
        ).aggregate(total=Sum('duration_seconds'))
        return result['total'] or 0


class Module(models.Model):
    """Модуль курса (группа уроков)"""
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='modules',
        verbose_name='Курс'
    )
    title = models.CharField(max_length=200, verbose_name='Название модуля')
    order_index = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    description = models.TextField(blank=True, verbose_name='Описание модуля')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'modules'
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'
        ordering = ['order_index']
        unique_together = ['course', 'order_index']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_lessons_count(self):
        """Количество уроков в модуле"""
        return self.lessons.count()


class Lesson(models.Model):
    """Урок курса"""
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
        verbose_name='Модуль'
    )
    title = models.CharField(max_length=200, verbose_name='Название урока')
    content_type = models.CharField(
        max_length=20, 
        choices=CONTENT_TYPES, 
        default='video',
        verbose_name='Тип контента'
    )
    kinescope_video_id = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='ID видео Kinescope',
        help_text="ID видео из Kinescope.io"
    )
    kinescope_embed_code = models.TextField(
        blank=True, 
        verbose_name='Embed код Kinescope',
        help_text="Готовый iframe-код для вставки видео"
    )
    text_content = models.TextField(
        blank=True, 
        verbose_name='Текстовое содержание'
    )
    order_index = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_free_preview = models.BooleanField(
        default=False, 
        verbose_name='Бесплатный предпросмотр',
        help_text="Доступен без покупки курса"
    )
    duration_seconds = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name='Длительность (сек)'
    )
    attachment = models.FileField(
        upload_to='courses/attachments/',
        blank=True,
        null=True,
        verbose_name='Прикрепленный файл'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lessons'
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order_index']
        unique_together = ['module', 'order_index']
        indexes = [
            models.Index(fields=['module', 'order_index']),
            models.Index(fields=['content_type']),
        ]
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def get_embed_url(self, request=None):
        """
        Генерация URL для embed Kinescope с параметрами безопасности
        """
        if not self.kinescope_video_id:
            return None
        
        base_url = f"https://kinescope.io/embed/{self.kinescope_video_id}"
        params = {
            'autoplay': '0',
            'controls': '1',
        }
        
        # Добавляем domain restriction если есть request
        if request:
            params['domain'] = request.get_host()
        
        query_string = '&'.join(f'{key}={value}' for key, value in params.items())
        return f"{base_url}?{query_string}"
    
    def get_next_lesson(self):
        """Следующий урок в модуле"""
        return Lesson.objects.filter(
            module=self.module,
            order_index__gt=self.order_index
        ).order_by('order_index').first()
    
    def get_previous_lesson(self):
        """Предыдущий урок в модуле"""
        return Lesson.objects.filter(
            module=self.module,
            order_index__lt=self.order_index
        ).order_by('-order_index').first()

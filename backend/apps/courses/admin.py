"""
Django Admin конфигурация для приложения Courses.
Предоставляет удобные интерфейсы для управления курсами, модулями и уроками.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Course, Module, Lesson


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий курсов"""
    
    list_display = ('name', 'slug', 'description_preview')
    list_editable = ('slug',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    
    def description_preview(self, obj):
        """Краткое описание категории"""
        if obj.description:
            return obj.description[:100] + ('...' if len(obj.description) > 100 else '')
        return '-'
    description_preview.short_description = 'Описание'


class ModuleInline(admin.TabularInline):
    """Inline для модулей внутри курса"""
    
    model = Module
    extra = 0
    ordering = ('order_index',)
    fields = ('title', 'order_index', 'lessons_count')
    readonly_fields = ('lessons_count',)
    
    def lessons_count(self, obj):
        """Количество уроков в модуле"""
        return obj.lessons.count()
    lessons_count.short_description = 'Уроков'


class LessonInline(admin.StackedInline):
    """Inline для уроков внутри модуля (используется в ModuleAdmin)"""
    
    model = Lesson
    extra = 0
    ordering = ('order_index',)
    fields = (
        'title', 
        'content_type', 
        'kinescope_video_id', 
        'is_free_preview',
        'order_index',
        'duration_seconds',
        'preview_embed'
    )
    readonly_fields = ('preview_embed',)
    
    def preview_embed(self, obj):
        """Предпросмотр видео в админке"""
        if obj.content_type == 'video' and obj.kinescope_video_id:
            embed_url = f"https://kinescope.io/embed/{obj.kinescope_video_id}"
            return format_html(
                '<iframe src="{}" frameborder="0" allowfullscreen '
                'style="width:100%; height:200px; border:1px solid #ccc;"></iframe>',
                embed_url
            )
        return "Нет видео для предпросмотра"
    preview_embed.short_description = 'Предпросмотр видео'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Админка для курсов с расширенным функционалом"""
    
    list_display = (
        'title', 
        'author', 
        'category', 
        'price', 
        'status', 
        'modules_count',
        'lessons_count',
        'created_at',
        'status_badge'
    )
    list_filter = ('status', 'category', 'author', 'created_at')
    search_fields = ('title', 'description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [ModuleInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'title', 
                'slug', 
                'short_description',
                'description',
                'cover_image',
                'cover_image_preview'
            ),
        }),
        ('Параметры курса', {
            'fields': (
                'price', 
                'category', 
                'author', 
                'status'
            ),
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'cover_image_preview', 'modules_count', 'lessons_count')
    
    def cover_image_preview(self, obj):
        """Предпросмотр обложки курса"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width:300px; max-height:200px; border:1px solid #ccc;" />',
                obj.cover_image.url
            )
        return "Нет обложки"
    cover_image_preview.short_description = 'Обложка'
    
    def modules_count(self, obj):
        """Количество модулей в курсе"""
        return obj.modules.count()
    modules_count.short_description = 'Модулей'
    
    def lessons_count(self, obj):
        """Общее количество уроков в курсе"""
        total = sum(module.lessons.count() for module in obj.modules.all())
        return total
    lessons_count.short_description = 'Уроков'
    
    def status_badge(self, obj):
        """Цветной бейдж статуса курса"""
        colors = {
            'draft': '#6c757d',
            'published': '#28a745',
            'archived': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        status_labels = {
            'draft': 'Черновик',
            'published': 'Опубликован',
            'archived': 'Архив',
        }
        label = status_labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:12px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Статус'
    
    actions = ['make_published', 'make_draft', 'make_archived']
    
    def make_published(self, request, queryset):
        """Массовое действие: Опубликовать выбранные курсы"""
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} курс(а/ов) опубликовано.')
    make_published.short_description = 'Опубликовать выбранные'
    
    def make_draft(self, request, queryset):
        """Массовое действие: Вернуть в черновики"""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} курс(а/ов) возвращено в черновики.')
    make_draft.short_description = 'Вернуть в черновики'
    
    def make_archived(self, request, queryset):
        """Массовое действие: Архивировать курсы"""
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} курс(а/ов) архивировано.')
    make_archived.short_description = 'Архивировать выбранные'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """Админка для модулей"""
    
    list_display = ('title', 'course', 'order_index', 'lessons_count')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order_index')
    inlines = [LessonInline]
    
    def lessons_count(self, obj):
        """Количество уроков в модуле"""
        return obj.lessons.count()
    lessons_count.short_description = 'Уроков'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Админка для уроков с поддержкой Kinescope"""
    
    list_display = (
        'title', 
        'module', 
        'course_name',
        'content_type', 
        'order_index',
        'is_free_preview',
        'duration_display',
        'has_video'
    )
    list_filter = ('content_type', 'is_free_preview', 'module__course')
    search_fields = ('title', 'text_content', 'module__course__title')
    ordering = ('module', 'order_index')
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'title',
                'module',
                'order_index',
                'is_free_preview',
            ),
        }),
        ('Тип контента', {
            'fields': ('content_type',),
            'description': 'Выберите тип содержимого урока',
        }),
        ('Видео (Kinescope)', {
            'fields': ('kinescope_video_id', 'kinescope_embed_code', 'video_preview'),
            'classes': ('collapse',),
            'description': 'Вставьте ID видео из Kinescope или готовый iframe код',
        }),
        ('Текстовое содержание', {
            'fields': ('text_content',),
            'classes': ('collapse',),
        }),
        ('Дополнительно', {
            'fields': ('duration_seconds',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('video_preview', 'course_name')
    
    def course_name(self, obj):
        """Название курса (для удобства навигации)"""
        return obj.module.course.title if obj.module else '-'
    course_name.short_description = 'Курс'
    
    def video_preview(self, obj):
        """Предпросмотр видео из Kinescope"""
        if obj.content_type == 'video' and obj.kinescope_video_id:
            embed_url = f"https://kinescope.io/embed/{obj.kinescope_video_id}"
            return format_html(
                '<div style="margin:10px 0;">'
                '<iframe src="{}" frameborder="0" allowfullscreen '
                'style="width:100%; height:400px; border:1px solid #ccc; border-radius:4px;"></iframe>'
                '</div>'
                '<p style="color:#666; font-size:12px;">ID видео: {}</p>',
                embed_url,
                obj.kinescope_video_id
            )
        elif obj.kinescope_embed_code:
            return mark_safe(f'<div style="margin:10px 0;">{obj.kinescope_embed_code}</div>')
        return "Видео не настроено. Укажите kinescope_video_id или embed код."
    video_preview.short_description = 'Предпросмотр видео'
    
    def duration_display(self, obj):
        """Форматирование длительности урока"""
        if not obj.duration_seconds:
            return '-'
        minutes = obj.duration_seconds // 60
        seconds = obj.duration_seconds % 60
        return f"{minutes}:{seconds:02d}"
    duration_display.short_description = 'Длительность'
    
    def has_video(self, obj):
        """Индикатор наличия видео"""
        if obj.content_type == 'video' and obj.kinescope_video_id:
            return format_html('<span style="color:green;">✓ Видео</span>')
        return format_html('<span style="color:#999;">—</span>')
    has_video.short_description = 'Видео'
    
    # Автоматическая подстановка курса при создании через URL
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'module' in form.base_fields:
            # Фильтрация модулей по выбранному курсу (если есть GET параметр)
            course_id = request.GET.get('course_id')
            if course_id:
                from ..models import Course
                try:
                    course = Course.objects.get(pk=course_id)
                    form.base_fields['module'].queryset = course.modules.all()
                except Course.DoesNotExist:
                    pass
        return form

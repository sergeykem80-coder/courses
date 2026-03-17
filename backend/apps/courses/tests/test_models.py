"""
Тесты для моделей курсов, модулей и уроков
"""
import pytest
from django.utils.text import slugify
from apps.courses.models import Category, Course, Module, Lesson


@pytest.mark.django_db
class TestCategoryModel:
    """Тесты модели Category"""
    
    def test_category_creation(self):
        """Создание категории"""
        category = Category.objects.create(
            name="Python Разработка",
            description="Курсы по Python"
        )
        
        assert category.name == "Python Разработка"
        assert category.slug == "python-razrabotka"
        assert str(category) == "Python Разработка"
    
    def test_category_slug_auto_generation(self):
        """Автоматическая генерация слага"""
        category = Category(name="Веб Разработка на Django")
        category.save()
        
        assert category.slug == "veb-razrabotka-na-django"
    
    def test_category_unique_slug(self):
        """Уникальность слага"""
        Category.objects.create(name="Python")
        
        with pytest.raises(Exception):
            Category.objects.create(name="Python")


@pytest.mark.django_db
class TestCourseModel:
    """Тесты модели Course"""
    
    def test_course_creation(self, admin_user):
        """Создание курса"""
        category = Category.objects.create(name="Backend")
        course = Course.objects.create(
            title="Python для начинающих",
            description="Полный курс по Python",
            short_description="Основы Python",
            price=9900.00,
            category=category,
            author=admin_user
        )
        
        assert course.title == "Python для начинающих"
        assert course.slug == "python-dlya-nachinayushchikh"
        assert course.price == 9900.00
        assert course.status == 'draft'
        assert str(course) == "Python для начинающих"
    
    def test_course_slug_auto_generation(self, admin_user):
        """Автоматическая генерация слага курса"""
        category = Category.objects.create(name="Backend")
        course = Course.objects.create(
            title="React + TypeScript Продвинутый",
            description="Описание",
            price=15000,
            category=category,
            author=admin_user
        )
        
        assert course.slug == "react-typescript-prodvinutyy"
    
    def test_course_lessons_count(self, admin_user, course_with_lessons):
        """Подсчет количества уроков в курсе"""
        course = course_with_lessons
        
        assert course.get_lessons_count() == 3
    
    def test_course_duration(self, admin_user, course_with_lessons):
        """Подсчет общей длительности курса"""
        course = course_with_lessons
        
        # Длительность уроков: 300 + 600 + 450 = 1350 секунд
        assert course.get_duration() == 1350


@pytest.mark.django_db
class TestModuleModel:
    """Тесты модели Module"""
    
    def test_module_creation(self, published_course):
        """Создание модуля"""
        module = Module.objects.create(
            course=published_course,
            title="Введение в Python",
            order_index=1,
            description="Первые шаги"
        )
        
        assert module.title == "Введение в Python"
        assert module.order_index == 1
        assert str(module) == f"{published_course.title} - Введение в Python"
    
    def test_module_lessons_count(self, course_with_lessons):
        """Подсчет уроков в модуле"""
        module = course_with_lessons.modules.first()
        
        assert module.get_lessons_count() == 2


@pytest.mark.django_db
class TestLessonModel:
    """Тесты модели Lesson"""
    
    def test_lesson_creation(self, module):
        """Создание урока"""
        lesson = Lesson.objects.create(
            module=module,
            title="Установка Python",
            content_type='video',
            kinescope_video_id='abc123xyz',
            order_index=1,
            duration_seconds=300
        )
        
        assert lesson.title == "Установка Python"
        assert lesson.content_type == 'video'
        assert lesson.kinescope_video_id == 'abc123xyz'
        assert lesson.duration_seconds == 300
        assert lesson.is_free_preview is False
    
    def test_lesson_embed_url_generation(self, module, rf):
        """Генерация embed URL для Kinescope"""
        lesson = Lesson.objects.create(
            module=module,
            title="Видео урок",
            content_type='video',
            kinescope_video_id='testvideo123',
            order_index=1
        )
        
        # Создаем фейковый request
        request = rf.get('/')
        request.META['HTTP_HOST'] = 'example.com'
        
        embed_url = lesson.get_embed_url(request)
        
        assert embed_url is not None
        assert 'kinescope.io/embed/testvideo123' in embed_url
        assert 'domain=example.com' in embed_url
        assert 'autoplay=0' in embed_url
        assert 'controls=1' in embed_url
    
    def test_lesson_embed_url_without_video(self, module):
        """Embed URL без видео"""
        lesson = Lesson.objects.create(
            module=module,
            title="Текстовый урок",
            content_type='text',
            text_content="Какой-то текст",
            order_index=1
        )
        
        embed_url = lesson.get_embed_url()
        assert embed_url is None
    
    def test_lesson_next_previous(self, course_with_lessons):
        """Навигация между уроками"""
        module = course_with_lessons.modules.first()
        lessons = list(module.lessons.all().order_by('order_index'))
        
        # Первый урок
        first_lesson = lessons[0]
        assert first_lesson.get_previous_lesson() is None
        assert first_lesson.get_next_lesson() == lessons[1]
        
        # Второй урок
        second_lesson = lessons[1]
        assert second_lesson.get_previous_lesson() == lessons[0]
        assert second_lesson.get_next_lesson() == lessons[2]
        
        # Третий урок (последний)
        third_lesson = lessons[2]
        assert third_lesson.get_previous_lesson() == lessons[1]
        assert third_lesson.get_next_lesson() is None


@pytest.mark.django_db
class TestKinescopeService:
    """Тесты сервиса Kinescope"""
    
    def test_extract_video_id_from_url(self):
        """Извлечение ID видео из различных URL"""
        from apps.courses.services.kinescope import KinescopeService
        
        test_cases = [
            ("https://kinescope.io/abc123", "abc123"),
            ("https://kinescope.io/embed/xyz789", "xyz789"),
            ("https://kinescope.io/player?v=video456", "video456"),
            ("invalid-url", None),
            ("", None),
            (None, None),
        ]
        
        for url, expected in test_cases:
            result = KinescopeService.extract_video_id_from_url(url)
            assert result == expected, f"Failed for URL: {url}"

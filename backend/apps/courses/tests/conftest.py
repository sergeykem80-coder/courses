"""
Фикстуры для тестов приложения courses
"""
import pytest
from apps.courses.models import Category, Course, Module, Lesson


@pytest.fixture
def category():
    """Создание категории"""
    return Category.objects.create(
        name="Backend Разработка",
        slug="backend-razrabotka",
        description="Курсы по backend разработке"
    )


@pytest.fixture
def published_course(admin_user, category):
    """Опубликованный курс"""
    return Course.objects.create(
        title="Python Профессионал",
        slug="python-professional",
        description="Полный курс по Python для профессионалов",
        short_description="Стань Python разработчиком",
        price=15900.00,
        category=category,
        author=admin_user,
        status='published'
    )


@pytest.fixture
def draft_course(admin_user, category):
    """Курс в статусе черновика"""
    return Course.objects.create(
        title="Новый курс по Django",
        description="Курс в разработке",
        price=9900.00,
        category=category,
        author=admin_user,
        status='draft'
    )


@pytest.fixture
def module(published_course):
    """Модуль курса"""
    return Module.objects.create(
        course=published_course,
        title="Основы Python",
        order_index=1,
        description="Изучаем основы языка Python"
    )


@pytest.fixture
def course_with_lessons(admin_user, category):
    """Курс с модулями и уроками"""
    course = Course.objects.create(
        title="Fullstack Веб-разработка",
        description="Полный курс по веб-разработке",
        price=25000.00,
        category=category,
        author=admin_user,
        status='published'
    )
    
    # Создаем модуль
    module = Module.objects.create(
        course=course,
        title="Введение в веб-разработку",
        order_index=1
    )
    
    # Создаем уроки
    Lesson.objects.create(
        module=module,
        title="Как работает интернет",
        content_type='video',
        kinescope_video_id='intro001',
        order_index=1,
        duration_seconds=300,
        is_free_preview=True
    )
    
    Lesson.objects.create(
        module=module,
        title="HTML и CSS основы",
        content_type='video',
        kinescope_video_id='html_css_001',
        order_index=2,
        duration_seconds=600
    )
    
    # Второй модуль
    module2 = Module.objects.create(
        course=course,
        title="JavaScript основы",
        order_index=2
    )
    
    Lesson.objects.create(
        module=module2,
        title="Переменные и типы данных",
        content_type='video',
        kinescope_video_id='js_vars_001',
        order_index=1,
        duration_seconds=450
    )
    
    return course

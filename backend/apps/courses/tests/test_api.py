"""
Тесты для API endpoints курсов
"""
import pytest
from rest_framework import status
from apps.courses.models import Category, Course, Module, Lesson


@pytest.mark.django_db
class TestCategoryAPI:
    """Тесты API категорий"""
    
    def test_list_categories(self, client, category):
        """Получение списка категорий"""
        url = '/api/courses/categories/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['name'] == 'Backend Разработка'
    
    def test_retrieve_category(self, client, category):
        """Получение детальной информации о категории"""
        url = f'/api/courses/categories/{category.id}/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Backend Разработка'
        assert 'courses_count' in response.data
    
    def test_category_courses(self, client, published_course, category):
        """Получение курсов в категории"""
        url = f'/api/courses/categories/{category.id}/courses/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['slug'] == 'python-professional'


@pytest.mark.django_db
class TestPublicCourseAPI:
    """Тесты публичного API курсов (витрина)"""
    
    def test_list_published_courses(self, client, published_course, draft_course):
        """Получение списка опубликованных курсов"""
        url = '/api/courses/public/courses/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Должен вернуть только опубликованные курсы
        assert len(response.data) == 1
        assert response.data[0]['slug'] == 'python-professional'
    
    def test_course_search(self, client, published_course):
        """Поиск курсов"""
        url = '/api/courses/public/courses/?search=Python'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_course_filter_by_category(self, client, published_course, category):
        """Фильтрация курсов по категории"""
        url = f'/api/courses/public/courses/?category={category.id}'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_retrieve_course_detail(self, client, published_course):
        """Детальная информация о курсе"""
        url = f'/api/courses/public/courses/{published_course.slug}/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == published_course.title
        assert 'modules' in response.data or 'category' in response.data
    
    def test_draft_course_not_visible(self, client, draft_course):
        """Черновики не видны в публичном API"""
        url = f'/api/courses/public/courses/{draft_course.slug}/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCourseAPI:
    """Тесты API курсов (с аутентификацией)"""
    
    def test_list_courses_unauthenticated(self, client, published_course):
        """Неаутентифицированный пользователь видит только опубликованные"""
        url = '/api/courses/courses/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_create_course_admin(self, client, admin_user, category):
        """Админ может создавать курсы"""
        client.force_authenticate(user=admin_user)
        
        url = '/api/courses/courses/'
        data = {
            'title': 'Новый курс',
            'description': 'Описание курса',
            'price': '9900.00',
            'category': category.id,
            'status': 'draft'
        }
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Course.objects.filter(slug='novyy-kurs').exists()
    
    def test_create_course_student_forbidden(self, client, student_user, category):
        """Студент не может создавать курсы"""
        client.force_authenticate(user=student_user)
        
        url = '/api/courses/courses/'
        data = {
            'title': 'Курс от студента',
            'description': 'Описание',
            'price': '5000.00',
            'category': category.id
        }
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_course_curator(self, client, curator_user, published_course):
        """Куратор может обновлять курсы"""
        client.force_authenticate(user=curator_user)
        
        url = f'/api/courses/courses/{published_course.slug}/'
        data = {'price': '19900.00'}
        response = client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        published_course.refresh_from_db()
        assert str(published_course.price) == '19900.00'
    
    def test_get_course_modules(self, client, course_with_lessons):
        """Получение модулей курса с уроками"""
        url = f'/api/courses/courses/{course_with_lessons.slug}/modules/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Два модуля
        
        # Проверяем что уроки включены
        first_module = response.data[0]
        assert 'lessons' in first_module
        assert len(first_module['lessons']) >= 1


@pytest.mark.django_db
class TestLessonAPI:
    """Тесты API уроков"""
    
    def test_lesson_free_preview_accessible(self, client, course_with_lessons):
        """Бесплатный предпросмотр доступен без покупки"""
        free_lesson = Lesson.objects.filter(
            module__course=course_with_lessons,
            is_free_preview=True
        ).first()
        
        url = f'/api/courses/lessons/{free_lesson.id}/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'embed_url' in response.data
    
    def test_lesson_requires_access(self, client, course_with_lessons, student_user):
        """Платный урок требует доступа к курсу"""
        paid_lesson = Lesson.objects.filter(
            module__course=course_with_lessons,
            is_free_preview=False
        ).first()
        
        client.force_authenticate(user=student_user)
        url = f'/api/courses/lessons/{paid_lesson.id}/'
        response = client.get(url)
        
        # Доступ запрещен т.к. у студента нет доступа к курсу
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_lesson_with_access(self, client, course_with_lessons, student_user):
        """Доступ к уроку при наличии доступа к курсу"""
        from apps.access.models import UserCourseAccess
        
        # Выдаем доступ к курсу
        UserCourseAccess.objects.create(
            user=student_user,
            course=course_with_lessons,
            is_active=True
        )
        
        paid_lesson = Lesson.objects.filter(
            module__course=course_with_lessons,
            is_free_preview=False
        ).first()
        
        client.force_authenticate(user=student_user)
        url = f'/api/courses/lessons/{paid_lesson.id}/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_lesson_embed_endpoint(self, client, module, rf):
        """Получение embed URL для урока"""
        lesson = Lesson.objects.create(
            module=module,
            title="Видео",
            content_type='video',
            kinescope_video_id='test123',
            order_index=1
        )
        
        url = f'/api/courses/lessons/{lesson.id}/embed/'
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'embed_url' in response.data
        assert 'kinescope.io/embed/test123' in response.data['embed_url']
    
    def test_create_lesson_admin(self, client, admin_user, module):
        """Админ может создавать уроки"""
        client.force_authenticate(user=admin_user)
        
        url = '/api/courses/lessons/'
        data = {
            'module': module.id,
            'title': 'Новый урок',
            'content_type': 'video',
            'kinescope_video_id': 'newvideo456',
            'order_index': 10
        }
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Lesson.objects.filter(title='Новый урок').exists()

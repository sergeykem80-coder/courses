# 📚 API Документация: Курсы и Доступ

## Обзор

Этот документ описывает API endpoints для управления курсами, модулями, уроками и доступом студентов.

---

## 🔐 Базовая аутентификация

Все endpoints, кроме публичных, требуют JWT-токен в заголовке:
```
Authorization: Bearer <your_jwt_token>
```

---

## 📖 Курсы (Public & Admin)

### Публичная витрина курсов

#### GET `/api/courses/public/courses/`
Получить список опубликованных курсов (доступно всем)

**Query Parameters:**
- `category` (int): Фильтр по категории
- `search` (string): Поиск по названию и описанию
- `ordering` (string): Сортировка (`-created_at`, `price`, `-price`)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Python Профессионал",
    "slug": "python-professional",
    "short_description": "Стань Python разработчиком",
    "description": "Полный курс...",
    "cover_image": "https://media.example.com/courses/python.jpg",
    "price": "15900.00",
    "category": {
      "id": 1,
      "name": "Backend Разработка",
      "slug": "backend-razrabotka"
    },
    "lessons_count": 24,
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

#### GET `/api/courses/public/courses/{slug}/`
Детальная информация о курсе

**Response:**
```json
{
  "id": 1,
  "title": "Python Профессионал",
  "slug": "python-professional",
  "description": "Полное описание курса...",
  "short_description": "Стань Python разработчиком",
  "cover_image": "https://...",
  "price": "15900.00",
  "category": {...},
  "author": 1,
  "author_name": "Иван Петров",
  "author_avatar": "https://...",
  "status": "published",
  "status_display": "Опубликован",
  "modules": [
    {
      "id": 1,
      "title": "Введение",
      "description": "...",
      "order_index": 1,
      "lessons_count": 3,
      "lessons": [
        {
          "id": 1,
          "title": "Установка Python",
          "content_type": "video",
          "order_index": 1,
          "is_free_preview": true,
          "duration_seconds": 300
        }
      ],
      "created_at": "..."
    }
  ],
  "lessons_count": 24,
  "duration_seconds": 7200,
  "created_at": "...",
  "updated_at": "..."
}
```

#### GET `/api/courses/public/courses/categories/`
Список категорий с количеством курсов

---

### Управление курсами (Admin/Curator)

#### GET `/api/courses/courses/`
Список всех курсов (админ видит все, студенты только published)

#### POST `/api/courses/courses/`
Создать новый курс (только admin/curator)

**Request:**
```json
{
  "title": "Новый курс по Django",
  "description": "Полное описание...",
  "short_description": "Кратко о курсе",
  "cover_image": "file upload",
  "price": "9900.00",
  "category": 1,
  "status": "draft"
}
```

#### PUT/PATCH `/api/courses/courses/{slug}/`
Обновить курс

#### DELETE `/api/courses/courses/{slug}/`
Удалить курс

#### GET `/api/courses/courses/{slug}/modules/`
Получить модули курса с уроками

---

## 🎥 Уроки (Lessons)

### GET `/api/courses/lessons/{id}/`
Получить информацию об уроке

**Permissions:**
- Если `is_free_preview=true` — доступно всем
- Иначе требуется активный доступ к курсу через `UserCourseAccess`

**Response:**
```json
{
  "id": 1,
  "title": "Установка Python",
  "content_type": "video",
  "content_type_display": "Видео",
  "kinescope_video_id": "abc123xyz",
  "kinescope_embed_code": "<iframe>...</iframe>",
  "text_content": "",
  "order_index": 1,
  "is_free_preview": true,
  "duration_seconds": 300,
  "attachment": null,
  "embed_url": "https://kinescope.io/embed/abc123xyz?autoplay=0&controls=1&domain=example.com",
  "has_next": true,
  "has_previous": false,
  "created_at": "...",
  "updated_at": "..."
}
```

### GET `/api/courses/lessons/{id}/embed/`
Получить embed URL для видео урока

**Response:**
```json
{
  "embed_url": "https://kinescope.io/embed/abc123xyz?autoplay=0&controls=1"
}
```

### POST `/api/courses/lessons/`
Создать урок (только admin/curator)

**Request:**
```json
{
  "module": 1,
  "title": "Новый урок",
  "content_type": "video",
  "kinescope_video_id": "newvideo456",
  "text_content": "Дополнительные материалы...",
  "order_index": 1,
  "is_free_preview": false,
  "duration_seconds": 600
}
```

---

## 🎓 Доступ к курсам (Student)

### GET `/api/access/me/my_courses/`
Получить список моих курсов (требуется авторизация)

**Response:**
```json
[
  {
    "id": 1,
    "user": 5,
    "course": {
      "id": 1,
      "title": "Python Профессионал",
      "slug": "python-professional",
      "cover_image": "...",
      "price": "15900.00",
      "category": 1,
      "category_name": "Backend"
    },
    "granted_at": "2026-01-20T12:00:00Z",
    "granted_by": null,
    "granted_by_name": null,
    "expires_at": null,
    "is_active": true,
    "is_expired": false
  }
]
```

### GET `/api/access/me/courses/{course_id}/progress/`
Получить прогресс по курсу

**Response:**
```json
{
  "course_id": 1,
  "course_title": "Python Профессионал",
  "total_lessons": 24,
  "completed_lessons": 5,
  "progress_percent": 20.83,
  "next_lesson": {
    "id": 6,
    "title": "Функции и модули",
    "content_type": "video",
    "duration_seconds": 450,
    ...
  }
}
```

---

## 📊 Прогресс уроков

### POST `/api/access/progress/lessons/{lesson_id}/update/`
Обновить прогресс урока

**Request:**
```json
{
  "is_completed": true,
  "last_watched_second": 300
}
```

**Response:**
```json
{
  "id": 1,
  "user": 5,
  "lesson": {...},
  "is_completed": true,
  "last_watched_second": 300,
  "completed_at": "2026-01-20T14:30:00Z",
  "updated_at": "2026-01-20T14:30:00Z",
  "progress_percent": 100.0
}
```

---

## 👨‍💼 Администрирование доступа

### POST `/api/access/admin/users/{user_id}/grant-course/`
Выдать доступ пользователю к курсу (admin/curator)

**Request:**
```json
{
  "course_id": 1,
  "expires_at": "2026-12-31T23:59:59"
}
```

**Response:**
```json
{
  "message": "Доступ успешно выдан",
  "access": {
    "id": 1,
    "user": 5,
    "course": {...},
    "granted_at": "...",
    "granted_by": 1,
    "granted_by_name": "Администратор",
    "expires_at": "2026-12-31T23:59:59",
    "is_active": true,
    "is_expired": false
  }
}
```

### DELETE `/api/access/admin/users/{user_id}/revoke-course/{course_id}/`
Отозвать доступ пользователя к курсу

**Response:**
```json
{
  "message": "Доступ отозван"
}
```

### GET `/api/access/admin/user_accesses/?user_id=123`
Получить все доступы пользователя (admin просмотр)

---

## 🔗 Категории

### GET `/api/courses/categories/`
Список всех категорий

### GET `/api/courses/categories/{id}/`
Детальная информация о категории

### GET `/api/courses/categories/{id}/courses/`
Курсы в категории

---

## 📝 Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Неверные данные запроса |
| 401 | Требуется авторизация |
| 403 | Нет прав доступа |
| 404 | Ресурс не найден |
| 409 | Конфликт (например, доступ уже существует) |

---

## 💡 Пример использования (JavaScript/React)

```typescript
// Получение списка курсов
const response = await fetch('/api/courses/public/courses/');
const courses = await response.json();

// Покупка курса (после оплаты сервер выдаст доступ)
// ...

// Получение моих курсов
const myCourses = await fetch('/api/access/me/my_courses/', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Обновление прогресса
await fetch(`/api/access/progress/lessons/${lessonId}/update/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    last_watched_second: 120,
    is_completed: false
  })
});
```

---

## 🔒 Безопасность

1. **Kinescope Domain Restriction**: Все embed URLs генерируются с параметром `domain=` для защиты от хотлинка
2. **Проверка доступа**: Каждый запрос к уроку проверяет наличие `UserCourseAccess`
3. **Бесплатный предпросмотр**: Уроки с `is_free_preview=true` доступны без покупки

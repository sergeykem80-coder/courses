# 🎓 EduPlatform - Платформа онлайн-обучения

Аналог GetCourse с интеграцией Kinescope.io и Robokassa.

## 📋 Содержание

- [Технологический стек](#технологический-стек)
- [Быстрый старт](#быстрый-старт)
- [API Документация](#api-документация)
- [Структура проекта](#структура-проекта)

## 🛠️ Технологический стек

**Backend:**
- Django 4.2+
- Django REST Framework 3.14
- JWT аутентификация (djangorestframework-simplejwt)
- PostgreSQL / SQLite
- Django Guardian (object-level permissions)

**Интеграции:**
- Kinescope.io - видеохостинг для курсов
- Robokassa - приём платежей

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env`:
```bash
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ROBOKASSA_LOGIN=test_login
ROBOKASSA_PASSWORD1=test_password1
ROBOKASSA_PASSWORD2=test_password2
```

### 3. Миграции и создание суперпользователя

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Запуск сервера

```bash
python manage.py runserver
```

Сервер доступен по адресу: http://localhost:8000

## 🔐 API Документация

### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/auth/register/` | Регистрация нового пользователя |
| POST | `/api/auth/login/` | Вход, получение JWT токенов |
| POST | `/api/auth/refresh/` | Обновление access токена |
| POST | `/api/auth/logout/` | Выход |
| GET | `/api/auth/me/` | Данные текущего пользователя |
| PUT | `/api/me/profile/` | Обновление профиля |

### Пример запроса на регистрацию

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "securepass123",
    "password_confirm": "securepass123"
  }'
```

### Пример входа

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "username", "password": "securepass123"}'
```

Ответ:
```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci..."
}
```

## 📁 Структура проекта

```
backend/
├── config/              # Настройки Django
│   ├── settings.py      # Основные настройки
│   ├── urls.py          # Корневой URLconf
│   └── wsgi.py
├── users/               # Приложение пользователей
│   ├── models.py        # User, UserProfile
│   ├── serializers.py   # DRF serializers
│   ├── views.py         # Auth views
│   ├── urls.py          # User URLs
│   └── admin.py         # Admin конфигурация
├── courses/             # Курсы (в разработке)
├── orders/              # Заказы (в разработке)
├── payments/            # Платежи (в разработке)
├── docs/                # Документация
├── manage.py
├── requirements.txt
└── .env
```

## 👥 Роли пользователей

- **student** - Студент (доступ к купленным курсам)
- **curator** - Куратор (управление курсами)
- **admin** - Администратор (полный доступ)

## 🧪 Тестирование API

Тестовые учётные данные администратора:
- Email: `admin@eduplatform.ru`
- Password: `admin123`

## 📝 Лицензия

MIT

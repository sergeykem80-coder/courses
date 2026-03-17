# Настройка главного urls.py и интеграция приложений

## 📋 Обзор изменений

В данном этапе была выполнена настройка главного `urls.py` и создание URL-конфигураций для всех приложений проекта EduPlatform.

---

## ✅ Выполненные задачи

### 1. Главный URL-конфигуратор (`config/urls.py`)

**Файл**: `/workspace/eduplatform/backend/config/urls.py`

Подключены все приложения через пространства имен:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth endpoints
    path('api/auth/', include('users.urls')),
    
    # Courses endpoints
    path('api/courses/', include('courses.urls', namespace='courses')),
    
    # Orders endpoints
    path('api/orders/', include('orders.urls', namespace='orders')),
    
    # Payments endpoints (Robokassa)
    path('api/payments/', include('payments.urls', namespace='payments')),
]
```

---

### 2. Приложение "Курсы" (`courses/`)

#### Модели (`models.py`)
- **Category** - категории курсов (авто-слаг)
- **Course** - курсы с полями: title, slug, description, price, cover_image, status
- **Module** - модули курса с order_index
- **Lesson** - уроки с поддержкой:
  - `kinescope_video_id` - ID видео из Kinescope
  - `kinescope_embed_code` - готовый iframe код
  - `is_free_preview` - бесплатный предпросмотр
  - Методы: `get_next_lesson()`, `get_previous_lesson()`

#### Представления (`views.py`)
- **PublicCourseListView** - публичный список курсов (фильтрация, поиск, сортировка)
- **PublicCourseDetailView** - детальная информация о курсе
- **CourseViewSet** - CRUD для курсов (admin/curator)
- **ModuleViewSet** - CRUD для модулей (admin/curator)
- **LessonViewSet** - CRUD для уроков (admin/curator)

#### Сериализаторы (`serializers.py`)
- `CategorySerializer`
- `CourseListSerializer` - легкий список
- `CourseDetailSerializer` - полный с модулями и уроками
- `CourseSerializer` - для создания/редактирования
- `ModuleSerializer`
- `LessonSerializer`

#### URL-адреса (`urls.py`)
```
/api/courses/public/                    # GET - список опубликованных
/api/courses/public/<slug:slug>/        # GET - детали курса
/api/courses/                           # CRUD (admin/curator)
```

#### Сервис Kinescope (`services/kinescope.py`)
- `KinescopeService.generate_embed_url()` - генерация URL embed
- `KinescopeService.generate_embed_html()` - готовый iframe HTML
- `KinescopeService.extract_video_id()` - извлечение ID из URL
- `KinescopeService.get_video_info()` - получение метаданных через API

---

### 3. Приложение "Заказы" (`orders/`)

#### Модели (`models.py`)
- **Order** - заказы на покупку курсов:
  - Статусы: pending, paid, cancelled, refunded
  - Robokassa поля: `robokassa_inv_id`, `robokassa_out_sum`, `robokassa_signature`
  - Связи: user, course

#### Представления (`views.py`)
- **OrderViewSet** - управление заказами:
  - Студенты видят только свои заказы
  - Admin/Curator видят все заказы
  - Action `mark_as_paid` - ручная отметка оплаты

#### Сериализаторы (`serializers.py`)
- `OrderSerializer` - просмотр заказов
- `OrderCreateSerializer` - создание заказа

#### URL-адреса (`urls.py`)
```
/api/orders/                # List/Create (auth)
/api/orders/{id}/           # Retrieve/Update/Delete
/api/orders/{id}/mark_as_paid/  # POST (admin only)
```

---

### 4. Приложение "Платежи" (`payments/`)

#### Модели (`models.py`)
- **UserCourseAccess** - доступ пользователя к курсам:
  - Поля: user, course, granted_at, expires_at, is_active
  - Unique together: (user, course)
  
- **LessonProgress** - прогресс прохождения уроков:
  - Поля: user, lesson, is_completed, last_watched_second
  - Unique together: (user, lesson)

#### Представления (`views.py`)
- **PaymentViewSet**:
  - `create()` - создание заказа + генерация ссылки Robokassa
  - `list()` - список заказов пользователя
  
- **RobokassaWebhookView** - обработка вебхуков от Robokassa:
  - Проверка подписи
  - Обновление статуса заказа
  - Автоматическая выдача доступа к курсу
  
- **PaymentSuccessView** - страница успешной оплаты
- **PaymentFailView** - страница ошибки оплаты

#### Сервис Robokassa (`views.py` - RobokassaService)
- `_generate_signature()` - генерация MD5 подписи
- `create_payment_url()` - создание ссылки на оплату
- `verify_webhook_signature()` - проверка вебхука

#### Сериализаторы (`serializers.py`)
- `PaymentSerializer` - просмотр платежей
- `OrderCreateSerializer` - создание платежа (course_slug)

#### URL-адреса (`urls.py`)
```
/api/payments/                      # POST - создать платеж, GET - список
/api/payments/robokassa-webhook/    # POST - вебхук от Robokassa
/payments/success/                  # GET - страница успеха
/payments/fail/                     # GET - страница ошибки
```

---

## 🔧 Технические детали

### Миграции
Все миграции успешно созданы и применены:
```bash
python manage.py makemigrations users courses orders payments
python manage.py migrate
```

Созданные миграции:
- `courses/migrations/0001_initial.py` - Category, Course, Module, Lesson
- `orders/migrations/0001_initial.py` - Order
- `payments/migrations/0001_initial.py` - UserCourseAccess, LessonProgress

### Проверка
```bash
python manage.py check
# System check identified no issues (0 silenced).
```

---

## 📊 API Endpoints Summary

### Authentication (users app)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход (JWT) |
| POST | `/api/auth/refresh/` | Обновление токена |
| POST | `/api/auth/logout/` | Выход |
| GET | `/api/auth/me/` | Данные пользователя |

### Courses
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/courses/public/` | Any | Список курсов |
| GET | `/api/courses/public/{slug}/` | Any | Детали курса |
| GET | `/api/courses/` | Admin/Curator | Список всех |
| POST | `/api/courses/` | Admin/Curator | Создать курс |
| PUT | `/api/courses/{id}/` | Admin/Curator | Редактировать |
| DELETE | `/api/courses/{id}/` | Admin/Curator | Удалить |

### Orders
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/orders/` | Auth | Свои заказы |
| POST | `/api/orders/` | Auth | Создать заказ |
| GET | `/api/orders/{id}/` | Auth | Детали заказа |
| POST | `/api/orders/{id}/mark_as_paid/` | Admin | Отметить оплаченным |

### Payments
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/payments/` | Auth | Создать платеж |
| GET | `/api/payments/` | Auth | История платежей |
| POST | `/api/payments/robokassa-webhook/` | None | Вебхук Robokassa |
| GET | `/payments/success/` | Auth | Успех оплаты |
| GET | `/payments/fail/` | Auth | Ошибка оплаты |

---

## 🎯 Пример использования API

### 1. Создание платежа за курс

```http
POST /api/payments/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "course_slug": "python-basics"
}
```

**Ответ**:
```json
{
  "order_id": 123,
  "payment_url": "https://auth.robokassa.ru/Merchant/Index.aspx?MerchantLogin=...&OutSum=1000.00&InvId=123&...",
  "amount": "1000.00",
  "course_title": "Python для начинающих"
}
```

### 2. Вебхук от Robokassa (автоматически)

Robokassa отправляет POST на `/api/payments/robokassa-webhook/`:
```
OutSum=1000.00
InvId=123
SignatureValue=ABC123...
```

Сервер:
1. Проверяет подпись
2. Обновляет заказ: `status = 'paid'`
3. Создает `UserCourseAccess` для пользователя
4. Возвращает `OK|123`

### 3. Получение своих курсов

```http
GET /api/me/courses/
Authorization: Bearer {access_token}
```

---

## 🔐 Безопасность

### Robokassa Integration
- Используется два пароля (password1 для запросов, password2 для вебхуков)
- MD5 подпись всех параметров
- CSRF exempt только для webhook endpoint
- Проверка дублирования оплаты

### Доступ к курсам
- Модель `UserCourseAccess` проверяется перед показом урока
- Бесплатные уроки (`is_free_preview=True`) доступны без покупки
- Администраторы могут выдавать доступ вручную

### Kinescope Video Protection
- Domain restriction в настройках Kinescope
- DRM защита (опционально)
- Watermark с email пользователя (рекомендуется)

---

## 📁 Структура файлов

```
eduplatform/backend/
├── config/
│   ├── settings.py          # Настройки (Robokassa, Kinescope, JWT)
│   └── urls.py              # Главный URL конфиг
├── users/                   # Аутентификация
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── courses/                 # Курсы и контент
│   ├── models.py            # Course, Module, Lesson, Category
│   ├── views.py             # Public + Admin viewsets
│   ├── serializers.py       # 6 serializers
│   ├── urls.py              # Public + Admin routes
│   └── services/
│       └── kinescope.py     # Kinescope integration
├── orders/                  # Заказы
│   ├── models.py            # Order
│   ├── views.py             # OrderViewSet
│   ├── serializers.py       # Order serializers
│   └── urls.py
└── payments/                # Платежи и доступ
    ├── models.py            # UserCourseAccess, LessonProgress
    ├── views.py             # Payment + Robokassa webhook
    ├── serializers.py       # Payment serializers
    └── urls.py
```

---

## 🚀 Следующие шаги

1. **Настройка Django Admin** - интерфейсы для управления курсами
2. **Frontend (React)** - личный кабинет, витрина, плеер
3. **Email уведомления** - отправка писем об оплате
4. **Тестирование** - unit тесты для платежей и доступа
5. **Деплой** - Docker, Nginx, SSL

---

## 📝 Переменные окружения (.env)

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite для разработки)
DATABASE_URL=sqlite:///db.sqlite3

# Robokassa
ROBOKASSA_LOGIN=your_login
ROBOKASSA_PASSWORD1=your_password1
ROBOKASSA_PASSWORD2=your_password2
ROBOKASSA_IS_TEST=True

# Kinescope
KINESCOPE_API_TOKEN=your_token

# Email (для уведомлений)
EMAIL_HOST=smtp.sendpulse.com
EMAIL_HOST_USER=your_user
EMAIL_HOST_PASSWORD=your_pass
DEFAULT_FROM_EMAIL=noreply@eduplatform.ru
```

---

**Дата завершения**: 2026  
**Статус**: ✅ Готово к тестированию и дальнейшей разработке

# 📦 Настройка проекта для Amvera.ru - Краткое руководство

## Быстрый старт

### 1. Подготовка секретов на Amvera

```bash
# Авторизация в CLI
amvera auth login

# Перейдите в директорию проекта
cd backend

# Создайте секреты (замените значения на свои)
amvera secrets set SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
amvera secrets set POSTGRES_DB=eduplatform
amvera secrets set POSTGRES_USER=eduser
amvera secrets set POSTGRES_PASSWORD=<надежный_пароль>
amvera secrets set POSTGRES_HOST=<host_базы_amvera>
amvera secrets set POSTGRES_PORT=5432
amvera secrets set ROBOKASSA_LOGIN=<login>
amvera secrets set ROBOKASSA_PASSWORD1=<password1>
amvera secrets set ROBOKASSA_PASSWORD2=<password2>
amvera secrets set ROBOKASSA_IS_TEST=true
amvera secrets set KINESCOPE_API_TOKEN=<token>
amvera secrets set EMAIL_HOST_USER=<email>
amvera secrets set EMAIL_HOST_PASSWORD=<password>
amvera secrets set ALLOWED_HOSTS=ваш-app.amvera.io,localhost,127.0.0.1
```

### 2. Создание базы данных PostgreSQL

В панели Amvera:
1. Projects → Ваш проект → Databases → Create Database
2. Выберите PostgreSQL
3. Скопируйте хост для `POSTGRES_HOST`

### 3. Деплой приложения

```bash
# Из директории backend
amvera deploy
```

### 4. Применение миграций

```bash
amvera exec python manage.py migrate
amvera exec python manage.py collectstatic --noinput
amvera exec python manage.py createsuperuser
```

### 5. Проверка работы

```bash
# Health check
curl https://ваш-app.amvera.io/api/payments/health/

# Просмотр логов
amvera logs --follow
```

---

## Структура файлов для Amvera

```
backend/
├── Dockerfile              # Образ приложения
├── amvera.toml            # Конфигурация Amvera
├── requirements.txt       # Зависимости Python
├── .env.example          # Шаблон переменных окружения
├── .gitignore            # Игнорируемые файлы
├── DEPLOY_AMVERA.md      # Полная документация
├── manage.py             # Django management
├── config/
│   ├── settings.py       # Настройки Django (адаптированы для Amvera)
│   ├── urls.py           # URL маршруты
│   └── wsgi.py           # WSGI entry point
├── apps/
│   ├── users/            # Аутентификация и пользователи
│   ├── courses/          # Курсы, модули, уроки
│   ├── access/           # Доступ к курсам и прогресс
│   ├── orders/           # Заказы
│   └── payments/         # Платежи (Robokassa, health check)
├── media/                # Медиафайлы пользователей (volume)
└── staticfiles/          # Статика Django (volume)
```

---

## Ключевые изменения для Amvera

### settings.py

- ✅ `DEBUG=False` по умолчанию
- ✅ `SECRET_KEY` без значения по умолчанию (требуется в Secrets)
- ✅ `DATABASES` без fallback на SQLite
- ✅ `ALLOWED_HOSTS` из Secrets
- ✅ Логирование в console (stdout/stderr)
- ✅ Security настройки для reverse proxy
- ✅ Health check endpoint

### payments/views.py

- ✅ Добавлен `HealthCheckView` для мониторинга
- ✅ Улучшено логирование вебхуков Robokassa
- ✅ Модель `PaymentNotification` для аудита

### amvera.toml

- ✅Volumes для media и staticfiles
- ✅Health check конфигурация
- ✅Ресурсы (CPU, Memory)
- ✅Порты и сеть

---

## Интеграции

### Robokassa Webhook URL

```
https://ваш-домен.ru/api/payments/robokassa-webhook/
```

### Kinescope Domain Whitelist

Добавьте в настройках Kinescope:
- `ваш-app.amvera.io`
- `ваш-домен.ru`
- `www.ваш-домен.ru`

---

## Полезные команды

```bash
# Логи в реальном времени
amvera logs --follow

# Перезапуск
amvera restart

# Миграции
amvera exec python manage.py migrate

# Создать суперпользователя
amvera exec python manage.py createsuperuser

# Масштабирование
amvera scale --cpu 2 --memory 2048

# Информация о проекте
amvera app info
```

---

## Решение проблем

| Проблема | Решение |
|----------|---------|
| Ошибка БД | Проверьте `POSTGRES_*` в Secrets |
| Bad signature (Robokassa) | Проверьте `ROBOKASSA_PASSWORD2` |
| Видео не работает | Добавьте домен в whitelist Kinescope |
| Health check failed | Проверьте логи: `amvera logs` |

---

## Документация

- 📖 [Полное руководство](DEPLOY_AMVERA.md)
- 🔗 [Amvera Docs](https://docs.amvera.ru/)
- 💬 [Amvera Telegram](https://t.me/amvera_chat)

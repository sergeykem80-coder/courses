# 🚀 Руководство по развертыванию на Amvera.ru

## Обзор

Платформа онлайн-обучения **EduPlatform** полностью настроена для развертывания на российской облачной платформе [Amvera](https://amvera.ru/).

---

## 📋 Предварительные требования

1. Аккаунт на [Amvera](https://amvera.ru/)
2. Установленный CLI Amvera:
   ```bash
   curl -fsSL https://amvera.io/install.sh | bash
   ```
3. Авторизация в CLI:
   ```bash
   amvera auth login
   ```

---

## 🔐 Настройка секретов (Secrets)

Все чувствительные данные хранятся в Secrets Amvera, а не в коде.

### 1. Создайте секреты через CLI:

```bash
# Перейдите в директорию проекта
cd /workspace/eduplatform/backend

# Основной ключ Django (сгенерируйте надежный ключ)
amvera secrets set SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# PostgreSQL (создайте базу данных в панели Amvera)
amvera secrets set POSTGRES_DB=eduplatform
amvera secrets set POSTGRES_USER=eduser
amvera secrets set POSTGRES_PASSWORD=<ваш_надежный_пароль>
amvera secrets set POSTGRES_HOST=<host_базы_данных_amvera>
amvera secrets set POSTGRES_PORT=5432

# Robokassa
amvera secrets set ROBOKASSA_LOGIN=<ваш_login>
amvera secrets set ROBOKASSA_PASSWORD1=<password1>
amvera secrets set ROBOKASSA_PASSWORD2=<password2>
amvera secrets set ROBOKASSA_IS_TEST=false

# Kinescope
amvera secrets set KINESCOPE_API_TOKEN=<ваш_token>

# Email (SendPulse или другой SMTP)
amvera secrets set EMAIL_HOST_USER=<ваш_email>
amvera secrets set EMAIL_HOST_PASSWORD=<пароль_приложения>
amvera secrets set DEFAULT_FROM_EMAIL=noreply@ваш-домен.ru

# Домены
amvera secrets set ALLOWED_HOSTS=ваш-домен.ru,www.ваш-домен.ru,ваш-app.amvera.io
```

### 2. Или через панель управления Amvera:

1. Откройте проект в панели Amvera
2. Перейдите в раздел **Secrets**
3. Добавьте все переменные из списка выше

---

## 🗄️ База данных PostgreSQL

### Вариант 1: Использовать управляемую БД Amvera

1. В панели Amvera создайте сервис **PostgreSQL**
2. Скопируйте параметры подключения (host, port, database, user, password)
3. Добавьте их в Secrets (см. выше)

### Вариант 2: Внешняя база данных

Используйте любой внешний PostgreSQL (Timeweb Cloud, Selectel, Yandex Cloud и т.д.)

---

## 📦 Развертывание приложения

### 1. Инициализация проекта Amvera

```bash
cd /workspace/eduplatform/backend

# Инициализируйте проект (если еще не инициализирован)
amvera init

# Или используйте готовый amvera.toml
```

### 2. Деплой приложения

```bash
# Запуск деплоя
amvera deploy

# Деплой с указанием пути к контексту (если запускаете из корня проекта)
amvera deploy --path backend
```

### 3. Мониторинг деплоя

```bash
# Просмотр логов в реальном времени
amvera logs --follow

# Проверка статуса приложения
amvera ps

# Информация о контейнере
amvera app info
```

---

## 🌐 Настройка домена

### 1. Добавьте свой домен в панели Amvera:

1. Откройте проект → **Domains**
2. Нажмите **Add Domain**
3. Введите ваш домен (например, `edu.yoursite.ru`)

### 2. Настройте DNS записи:

Создайте CNAME запись у вашего регистратора домена:
```
CNAME edu.yoursite.ru → ваш-app.amvera.io
```

### 3. Обновите ALLOWED_HOSTS:

```bash
amvera secrets set ALLOWED_HOSTS=edu.yoursite.ru,www.edu.yoursite.ru,ваш-app.amvera.io
```

### 4. SSL сертификат

Amvera автоматически предоставляет HTTPS через Let's Encrypt.

---

## 📁 Медиафайлы и статика

### Тома (Volumes)

В `amvera.toml` настроены два тома:

- `/app/media` (1 GiB) — для загружаемых пользователями файлов (аватарки, обложки курсов)
- `/app/staticfiles` (512 MiB) — для собранной статики Django

### Доступ к медиафайлам

Для раздачи медиафайлов через Nginx добавьте в `amvera.toml`:

```toml
[network]
ports = [{ containerPort = 8000, protocol = "http" }]

# Статические файлы будут доступны по /media/
```

В production Django автоматически раздает статику через `WHITE_NOISE` или настройте отдельный CDN.

---

## 🔍 Health Check

Эндпоинт для проверки здоровья приложения:

```
GET https://ваш-домен.ru/api/payments/health/
```

Ответ при успехе:
```json
{
  "status": "healthy",
  "database": "connected",
  "debug": false
}
```

Amvera автоматически проверяет этот эндпоинт каждые 30 секунд.

---

## 📊 Логирование

Логи выводятся в stdout/stderr и автоматически собираются Amvera.

### Просмотр логов:

```bash
# Последние логи
amvera logs

# Логи в реальном времени
amvera logs --follow

# Логи за последние 2 часа
amvera logs --since 2h
```

### Уровни логирования:

- `INFO` — основные события (создание заказов, оплата, выдача доступа)
- `DEBUG` — детальная информация (вебхуки Robokassa)
- `WARNING` — предупреждения (неверная подпись вебхука)
- `ERROR` — ошибки

---

## 💰 Настройка Robokassa Webhook

### 1. В панели Robokassa укажите URL:

- **Result URL**: `https://ваш-домен.ru/api/payments/robokassa-webhook/`
- **Success URL**: `https://ваш-домен.ru/api/payments/success/`
- **Fail URL**: `https://ваш-домен.ru/api/payments/fail/`

### 2. Метод отправки: **POST**

### 3. Параметры:

- Используйте тестовый режим (`ROBOKASSA_IS_TEST=true`) для разработки
- Переключите на боевой режим (`false`) после проверки

---

## 🎥 Настройка Kinescope

### 1. В личном кабинете Kinescope:

1. Перейдите в **Настройки проекта** → **Безопасность**
2. Включите **Domain Restriction**
3. Добавьте ваши домены:
   - `ваш-домен.ru`
   - `www.ваш-домен.ru`
   - `ваш-app.amvera.io`

### 2. Получите API токен:

1. Перейдите в **Настройки** → **API**
2. Создайте новый токен
3. Добавьте его в Secrets:
   ```bash
   amvera secrets set KINESCOPE_API_TOKEN=<ваш_token>
   ```

---

## 🔄 CI/CD (опционально)

### Автоматический деплой через GitHub Actions:

Создайте `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Amvera

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Amvera CLI
        run: curl -fsSL https://amvera.io/install.sh | bash
      
      - name: Login to Amvera
        run: amvera auth login --token ${{ secrets.AMVERA_TOKEN }}
      
      - name: Deploy
        run: |
          cd backend
          amvera deploy --yes
```

В GitHub Secrets добавьте `AMVERA_TOKEN` (получите в панели Amvera).

---

## 🛠️ Управление приложением

### Миграции базы данных:

```bash
# Запуск миграций через exec
amvera exec python manage.py migrate

# Создание суперпользователя
amvera exec python manage.py createsuperuser
```

### Сбор статики:

```bash
amvera exec python manage.py collectstatic --noinput
```

### Перезапуск контейнера:

```bash
amvera restart
```

### Масштабирование:

```bash
# Изменение ресурсов (CPU, Memory)
amvera scale --cpu 2 --memory 2048
```

---

## 🧪 Тестирование перед продакшеном

### Чек-лист:

- [ ] Все секреты установлены
- [ ] База данных подключена
- [ ] Миграции применены
- [ ] Health check возвращает 200 OK
- [ ] Робота вебхуков Robokасса проверена в тестовом режиме
- [ ] Видео Kinescope воспроизводятся только с вашего домена
- [ ] Письма отправляются через SMTP
- [ ] Домен настроен и работает HTTPS
- [ ] Логи пишутся корректно

### Тестовый сценарий:

1. Зарегистрируйте нового пользователя
2. Создайте тестовый курс в админке
3. Оформите заказ на курс
4. Оплатите через тестовый режим Robokassa
5. Проверьте, что доступ выдан автоматически
6. Проверьте воспроизведение видео Kinescope

---

## 📈 Мониторинг и алерты

### В панели Amvera:

1. **Metrics** — использование CPU, памяти, диска
2. **Logs** — поиск по логам
3. **Alerts** — настройте уведомления при ошибках

### Рекомендуемые метрики для отслеживания:

- Количество успешных оплат
- Ошибки вебхуков Robokassa
- Время ответа API (< 500мс)
- Количество активных пользователей

---

## 🔒 Безопасность

### Реализованные меры:

✅ HTTPS (автоматически через Amvera)  
✅ Secure cookies  
✅ CSRF защита  
✅ HSTS (1 год)  
✅ X-Forwarded-Proto для reverse proxy  
✅ Секреты вне кода  
✅ Логирование всех платежей  

### Дополнительные рекомендации:

1. Регулярно обновляйте зависимости
2. Используйте сложные пароли для Secrets
3. Включите 2FA в панели Amvera
4. Настройте резервное копирование БД
5. Ограничьте доступ к админке по IP

---

## 🆘 Решение проблем

### Ошибка "Bad signature" от Robokassa:

Проверьте правильность `ROBOKASSA_PASSWORD2` в Secrets.

### Видео Kinescope не воспроизводится:

Убедитесь, что домен добавлен в whitelist в настройках Kinescope.

### Ошибки подключения к БД:

Проверьте параметры `POSTGRES_*` в Secrets и доступность БД.

### Приложение не запускается:

```bash
# Проверьте логи
amvera logs --follow

# Проверьте статус
amvera ps

# Попробуйте пересобрать
amvera deploy --rebuild
```

---

## 📞 Поддержка

- Документация Amvera: https://docs.amvera.ru/
- Техподдержка Amvera: support@amvera.ru
- Telegram чат Amvera: https://t.me/amvera_chat

---

## 📝 Полезные команды

```bash
# Показать информацию о проекте
amvera app info

# Список всех секретов
amvera secrets list

# Удалить секрет
amvera secrets delete SECRET_NAME

# Перезапустить приложение
amvera restart

# Остановить приложение
amvera stop

# Запустить интерактивную оболочку Django
amvera exec python manage.py shell
```

---

**Готово!** Ваша платформа онлайн-обучения развернута на Amvera и готова к работе 🎉

# Инструкции по деплою на сервер

## 🔔 Настройка системы уведомлений

### 1. Загрузка Firebase credentials

```bash
# На сервере, в директории проекта backend
cd /path/to/backend

# Скачайте firebase-credentials.json с вашего локального компьютера
# или создайте его на сервере с содержимым из Firebase Console
```

**Важно:** Файл `firebase-credentials.json` должен быть в корне директории `backend/`

### 2. Обновление .env файла

Убедитесь, что в `.env` файле есть:

```env
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
```

### 3. Обновление кода на сервере

```bash
# На сервере
cd /path/to/backend
git pull origin main

# Или если используете docker-compose
cd /path/to/project
git pull origin main
cd backend
git pull origin main
```

### 4. Применение миграций базы данных

```bash
# Внутри Docker контейнера backend
docker-compose exec backend alembic upgrade head

# Или если запускаете напрямую
alembic upgrade head
```

### 5. Обновление Docker контейнеров

```bash
# Остановите текущие контейнеры
docker-compose down

# Пересоберите образы
docker-compose build

# Запустите с новыми изменениями
docker-compose up -d
```

### 6. Проверка сервисов

Убедитесь, что все сервисы запущены:

```bash
docker-compose ps
```

Должны быть запущены:
- ✅ `backend` - основной API сервер
- ✅ `postgres` - база данных
- ✅ `redis` - кэш и очередь задач
- ✅ `celery_worker` - воркер для фоновых задач
- ✅ `celery_beat` - планировщик периодических задач (НОВЫЙ!)

### 7. Проверка Celery Beat

Проверьте, что Celery Beat запущен и работает:

```bash
# Проверка логов
docker-compose logs celery_beat

# Должны увидеть что-то вроде:
# celery beat v5.x.x is starting.
# LocalTime -> 2026-01-19 02:00:00
# Database: Redis://redis:6379/0
```

### 8. Проверка расписания задач

Проверьте, что задачи запланированы:

```bash
docker-compose exec celery_beat celery -A app.tasks.celery_app inspect scheduled
```

Должны увидеть:
- `send-daily-task-summary` - ежедневно в 8:00
- `check-overdue-tasks` - каждые 4 часа
- `check-task-reminders` - каждый час

### 9. Проверка Firebase инициализации

Проверьте логи backend, чтобы убедиться, что Firebase инициализирован:

```bash
docker-compose logs backend | grep -i firebase
```

Должны увидеть:
```
✅ Firebase Admin SDK initialized
```

Если видите:
```
⚠️ FIREBASE_CREDENTIALS_PATH not set, push notifications disabled
```

Тогда проверьте:
1. Существует ли файл `firebase-credentials.json` в директории `backend/`
2. Правильно ли указан путь в `.env` файле
3. Перезапустите контейнер: `docker-compose restart backend`

### 10. Тестирование уведомлений

После деплоя можно протестировать отправку уведомлений:

```bash
# Войдите в контейнер backend
docker-compose exec backend python3

# В Python консоли
from app.services.notification_service import NotificationService
import asyncio

async def test():
    # Замените на реальный FCM token пользователя
    fcm_token = "USER_FCM_TOKEN_HERE"
    result = await NotificationService.test_notification(fcm_token)
    print("✅ Отправлено!" if result else "❌ Ошибка")

asyncio.run(test())
```

## 📋 Чеклист деплоя

- [ ] `firebase-credentials.json` загружен на сервер
- [ ] `.env` файл обновлен с `FIREBASE_CREDENTIALS_PATH`
- [ ] Код обновлен через `git pull`
- [ ] Миграции применены (`alembic upgrade head`)
- [ ] Docker контейнеры пересобраны и перезапущены
- [ ] Все сервисы запущены (включая `celery_beat`)
- [ ] Celery Beat работает и показывает расписание
- [ ] Firebase инициализирован (проверка логов)
- [ ] Тестовое уведомление отправлено успешно

## 🔍 Отладка проблем

### Уведомления не приходят

1. **Проверьте логи Celery Worker:**
   ```bash
   docker-compose logs celery_worker | grep -i "notification\|reminder\|error"
   ```

2. **Проверьте логи Celery Beat:**
   ```bash
   docker-compose logs celery_beat | tail -50
   ```

3. **Проверьте Firebase инициализацию:**
   ```bash
   docker-compose logs backend | grep -i firebase
   ```

4. **Проверьте FCM token пользователя:**
   ```bash
   docker-compose exec postgres psql -U memoir_user -d memoir -c "SELECT email, fcm_token IS NOT NULL as has_token FROM users WHERE email = 'user@example.com';"
   ```

### Celery Beat не запускается

1. Проверьте, что Redis доступен:
   ```bash
   docker-compose exec celery_beat ping -c 1 redis
   ```

2. Проверьте переменные окружения:
   ```bash
   docker-compose exec celery_beat env | grep -i redis
   ```

### Дублирующиеся уведомления

Проверьте логику в `app/tasks/notification_tasks.py`:
- Убедитесь, что проверка `Task.updated_at` работает корректно
- Проверьте, что `min_update_time` рассчитывается правильно

## 📞 Поддержка

Если возникли проблемы, проверьте:
1. Логи всех сервисов: `docker-compose logs`
2. Статус контейнеров: `docker-compose ps`
3. Расписание Celery: `docker-compose exec celery_beat celery -A app.tasks.celery_app inspect scheduled`

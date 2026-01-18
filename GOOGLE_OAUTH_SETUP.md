# Google OAuth Setup - Quick Start

## Что было сделано:

### Frontend (Flutter)
1. ✅ Добавлен пакет `google_sign_in` в `pubspec.yaml`
2. ✅ Создан `GoogleAuthService` для работы с Google Sign In
3. ✅ Добавлена кнопка "Continue with Google" на страницу `EmailAuthPage`
4. ✅ Настроен `GoogleService-Info.plist` с CLIENT_ID для iOS
5. ✅ Добавлен URL scheme в `Info.plist` для iOS

### Backend (Python/FastAPI)
1. ✅ Добавлено поле `google_id` в модель `User`
2. ✅ Сделано поле `phone_number` необязательным
3. ✅ Создан `GoogleAuthService` для верификации Google токенов
4. ✅ Добавлен endpoint `POST /api/v1/auth/google`
5. ✅ Добавлен пакет `google-auth` в `requirements.txt`
6. ✅ Создана миграция БД

## Что нужно сделать на бэкенде:

### 1. Установить зависимости
```bash
cd backend
pip install -r requirements.txt
```

### 2. Применить миграцию
```bash
cd backend
alembic upgrade head
```

### 3. Перезапустить бэкенд
```bash
docker-compose down
docker-compose up -d
```

## Как это работает:

1. Пользователь нажимает "Continue with Google" в приложении
2. Flutter открывает Google Sign In диалог
3. После успешной авторизации, приложение получает `id_token` от Google
4. Приложение отправляет `id_token` на бэкенд (`POST /api/v1/auth/google`)
5. Бэкенд верифицирует токен через Google API
6. Если пользователь новый - создается аккаунт, если существующий - выполняется вход
7. Бэкенд возвращает JWT токены (access + refresh) и информацию о пользователе
8. Приложение сохраняет токены и перенаправляет пользователя

## Endpoints

### POST /api/v1/auth/google
Аутентификация через Google

**Request:**
```json
{
  "id_token": "eyJhbGc...",
  "access_token": "ya29.a0A..." // optional
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "is_new_user": false,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user",
    "first_name": "John",
    "last_name": "Doe",
    "avatar_url": "https://..."
  }
}
```

## Настройка Google Cloud Console

В Google Cloud Console уже настроено для:
- **Project ID**: memoir-c7600
- **iOS Client ID**: 660553470030-as8ms2ovb1cb3tk2ii50s1a4iaq1ea0d.apps.googleusercontent.com
- **Bundle ID**: net.memoir-ai.app

## Тестирование

Чтобы протестировать:
1. Запустите бэкенд
2. Запустите iOS симулятор или реальное устройство
3. Откройте приложение и нажмите "Continue with Google"
4. Войдите в Google аккаунт
5. Проверьте, что создался/вошел пользователь

## Troubleshooting

Если Google Sign In не работает:
- Проверьте, что `GoogleService-Info.plist` содержит `CLIENT_ID` и `REVERSED_CLIENT_ID`
- Проверьте, что в `Info.plist` добавлен правильный URL scheme
- Убедитесь, что Bundle ID совпадает: `net.memoir-ai.app`
- Проверьте логи бэкенда на ошибки верификации токена

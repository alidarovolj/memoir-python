# 📧 Настройка отправки Email для авторизации

## 🔑 Настройка SMTP (на примере Gmail)

### Вариант 1: Gmail с App Password (Рекомендуется)

1. **Включите двухфакторную аутентификацию**
   - Перейдите на https://myaccount.google.com/security
   - Включите "2-Step Verification"

2. **Создайте App Password**
   - Перейдите на https://myaccount.google.com/apppasswords
   - Выберите "Mail" и "Other (Custom name)"
   - Введите "Memoir Backend"
   - Скопируйте сгенерированный пароль (16 символов без пробелов)

3. **Используйте эти настройки:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_TLS=True
   SMTP_USER=ваш-email@gmail.com
   SMTP_PASSWORD=сгенерированный-app-password
   EMAIL_FROM=ваш-email@gmail.com
   EMAIL_FROM_NAME=Memoir
   EMAIL_TEST_MODE=False
   ```

### Вариант 2: Другие SMTP провайдеры

#### Яндекс.Почта
```env
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=ваш-email@yandex.ru
SMTP_PASSWORD=ваш-пароль
```

#### Mail.ru
```env
SMTP_HOST=smtp.mail.ru
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=ваш-email@mail.ru
SMTP_PASSWORD=ваш-пароль
```

#### SendGrid (Профессиональный сервис)
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
EMAIL_FROM=noreply@yourdomain.com
```

#### Mailgun
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=postmaster@mg.yourdomain.com
SMTP_PASSWORD=your-mailgun-smtp-password
EMAIL_FROM=noreply@yourdomain.com
```

## ⚙️ Настройка в проекте

### На сервере

1. **Откройте `.env` файл:**
```bash
cd /home/ubuntu/memoir/backend
nano .env
```

2. **Добавьте настройки email:**
```env
# Email Provider (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=Memoir
EMAIL_TEST_MODE=False
```

3. **Перезапустите backend:**
```bash
sudo docker compose restart backend
```

## 🧪 Тестирование

### Отправка тестового email

```bash
curl -X POST http://194.32.140.80:8000/api/v1/email-auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Ответ при успехе:
```json
{
  "success": true,
  "message": "Verification code sent to email",
  "expires_in": 300
}
```

### Проверка кода

```bash
curl -X POST http://194.32.140.80:8000/api/v1/email-auth/verify-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "code": "123456"}'
```

## 📊 Мониторинг

### Логи отправки email

```bash
sudo docker compose logs -f backend | grep EMAIL
```

Вы увидите:
- `📧 [EMAIL] Sending verification code to...` - начало отправки
- `✅ [EMAIL] Email sent successfully` - успешная отправка
- `❌ [EMAIL] Authentication failed` - ошибка авторизации SMTP
- `❌ [EMAIL] SMTP error` - другие ошибки SMTP

### Логи проверки кодов

```bash
sudo docker compose logs -f backend | grep EMAIL_VERIFY
```

## 🚨 Возможные проблемы

### Проблема: "SMTP authentication failed"

**Решение:**
1. Проверьте правильность email и пароля
2. Для Gmail - используйте App Password, не обычный пароль
3. Убедитесь что двухфакторная аутентификация включена (для Gmail)

### Проблема: "Connection refused" или "Timeout"

**Решение:**
1. Проверьте SMTP_HOST и SMTP_PORT
2. Для Gmail используйте port 587 с TLS=True
3. Проверьте файрвол сервера: `sudo ufw allow 587/tcp`

### Проблема: Email попадают в спам

**Решение:**
1. Используйте профессиональный SMTP сервис (SendGrid, Mailgun)
2. Настройте SPF, DKIM, DMARC записи для вашего домена
3. Используйте свой домен вместо Gmail

### Проблема: "Sender address rejected"

**Решение:**
1. Убедитесь что EMAIL_FROM совпадает с SMTP_USER (для Gmail)
2. Или используйте профессиональный SMTP сервис

## 🔄 Режимы работы

### Тестовый режим (разработка)

```env
EMAIL_TEST_MODE=True
```

Коды будут только логироваться, письма не отправляются:
```bash
sudo docker compose logs backend | grep "📝 \[EMAIL\]"
```

### Продакшн режим (реальные письма)

```env
EMAIL_TEST_MODE=False
SMTP_USER=ваш-реальный-email
SMTP_PASSWORD=ваш-реальный-пароль
```

## 📞 API Endpoints

### Отправка кода на email
```
POST /api/v1/email-auth/send-code
Body: {"email": "user@example.com"}
```

### Проверка кода
```
POST /api/v1/email-auth/verify-code
Body: {"email": "user@example.com", "code": "123456"}
```

### Повторная отправка
```
POST /api/v1/email-auth/resend-code
Body: {"email": "user@example.com"}
```

## 💡 Рекомендации

### Для разработки
- Используйте `EMAIL_TEST_MODE=True`
- Или Gmail с App Password

### Для продакшн
- Используйте профессиональный SMTP сервис (SendGrid, Mailgun, AWS SES)
- Настройте свой домен
- Настройте SPF, DKIM, DMARC
- Мониторьте доставляемость писем

## 📈 Лимиты

### Gmail
- ~500 писем в день (бесплатно)
- ~2000 писем в день (Google Workspace)

### SendGrid
- 100 писем в день (бесплатно)
- От $14.95/мес за 40,000 писем

### Mailgun
- 5,000 писем в месяц (бесплатно)
- От $35/мес за 50,000 писем

## 🔐 Безопасность

1. **Никогда не коммитьте** пароли в git
2. **Используйте App Passwords** для Gmail
3. **Ограничьте доступ** к `.env` файлу:
   ```bash
   chmod 600 .env
   ```
4. **Мониторьте логи** на подозрительную активность

## 📚 Документация

- Gmail App Passwords: https://support.google.com/accounts/answer/185833
- SendGrid: https://sendgrid.com/docs/
- Mailgun: https://documentation.mailgun.com/

# 🚀 Инструкция по деплою Backend на сервер

## 📋 Информация о сервере

- **IP-адрес**: 194.32.140.80
- **IPv6-адрес**: 2a00:5da0:1:201::7a4
- **Пользователь**: ubuntu
- **Пароль**: 3YFA/03TCtm4ObMVwImwtfA=
- **ОС**: Ubuntu 22.04 LTS
- **Ресурсы**: 2 CPU, 2 GB RAM, 40 GB Disk

## 🔧 Автоматический деплой (Рекомендуется)

### Шаг 1: Подключение к серверу

```bash
ssh ubuntu@194.32.140.80
# Пароль: 3YFA/03TCtm4ObMVwImwtfA=
```

### Шаг 2: Загрузка скрипта деплоя

```bash
# Клонируем репозиторий
git clone https://github.com/alidarovolj/memoir.git
cd memoir/backend

# Делаем скрипт исполняемым
chmod +x deploy.sh
```

### Шаг 3: Создание .env файла

```bash
# Копируем шаблон
cp env.template .env

# Редактируем .env файл
nano .env
```

**Обязательно замените следующие значения:**
- `SECRET_KEY` - сгенерируйте случайную строку (можно использовать: `openssl rand -hex 32`)
- `OPENAI_API_KEY` - ваш API ключ OpenAI
- `FIREBASE_CREDENTIALS_PATH` - путь к файлу Firebase credentials

### Шаг 4: Загрузка Firebase credentials

```bash
# На вашем локальном компьютере
scp /path/to/firebase-credentials.json ubuntu@194.32.140.80:/home/ubuntu/memoir/backend/

# На сервере переименуем
mv firebase-credentials.json firebase-credentials.json
```

### Шаг 5: Запуск деплоя

```bash
./deploy.sh
```

Скрипт автоматически:
- Обновит систему
- Установит Docker и Docker Compose
- Запустит контейнеры
- Выполнит миграции базы данных

---

## 🛠 Ручной деплой

Если автоматический скрипт не работает, следуйте этим шагам:

### 1. Подключение к серверу

```bash
ssh ubuntu@194.32.140.80
```

### 2. Обновление системы

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 3. Установка Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 4. Установка Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5. Клонирование репозитория

```bash
cd /home/ubuntu
git clone https://github.com/alidarovolj/memoir.git
cd memoir/backend
```

### 6. Настройка окружения

```bash
# Создаем .env файл
cp env.template .env
nano .env

# Загружаем Firebase credentials (с локального компьютера)
# scp /path/to/firebase-credentials.json ubuntu@194.32.140.80:/home/ubuntu/memoir/backend/
```

### 7. Запуск контейнеров

```bash
# Для production используем специальный docker-compose файл
sudo docker-compose -f docker-compose.prod.yml up -d --build
```

### 8. Запуск миграций

```bash
sudo docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 9. Проверка статуса

```bash
sudo docker-compose -f docker-compose.prod.yml ps
```

---

## 🌐 Доступ к сервисам

После успешного деплоя сервисы будут доступны по следующим адресам:

- **Backend API**: http://194.32.140.80:8000
- **API Documentation**: http://194.32.140.80:8000/docs
- **Flower (Celery Monitor)**: http://194.32.140.80:5555

---

## 📊 Полезные команды

### Просмотр логов

```bash
# Все логи
sudo docker-compose logs -f

# Только backend
sudo docker-compose logs -f backend

# Только celery worker
sudo docker-compose logs -f celery_worker
```

### Перезапуск сервисов

```bash
# Перезапуск всех сервисов
sudo docker-compose restart

# Перезапуск конкретного сервиса
sudo docker-compose restart backend
```

### Остановка сервисов

```bash
sudo docker-compose down
```

### Обновление кода

```bash
cd /home/ubuntu/memoir
git pull
cd backend
sudo docker-compose down
sudo docker-compose up -d --build
sudo docker-compose exec backend alembic upgrade head
```

### Резервное копирование базы данных

```bash
# Создание бэкапа
sudo docker-compose exec postgres pg_dump -U memoir_user memoir > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
sudo docker-compose exec -T postgres psql -U memoir_user memoir < backup_file.sql
```

---

## 🔐 Безопасность

### Рекомендации по безопасности:

1. **Смените пароль root и ubuntu**
   ```bash
   sudo passwd ubuntu
   sudo passwd root
   ```

2. **Настройте файрвол**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 8000/tcp
   sudo ufw allow 5555/tcp
   sudo ufw enable
   ```

3. **Настройте SSH ключи вместо паролей**
   ```bash
   # На локальном компьютере
   ssh-copy-id ubuntu@194.32.140.80
   
   # На сервере отключите вход по паролю
   sudo nano /etc/ssh/sshd_config
   # Установите: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

4. **Используйте HTTPS с Let's Encrypt** (необходим домен)
   ```bash
   sudo apt-get install certbot
   # Следуйте инструкциям certbot
   ```

---

## 🐛 Решение проблем

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
sudo docker-compose logs

# Проверьте, не заняты ли порты
sudo netstat -tulpn | grep -E '8000|5432|6379|5555'

# Пересоздайте контейнеры
sudo docker-compose down -v
sudo docker-compose up -d --build
```

### Проблема: Ошибки миграций

```bash
# Откатите миграции и примените заново
sudo docker-compose exec backend alembic downgrade -1
sudo docker-compose exec backend alembic upgrade head
```

### Проблема: Недостаточно памяти

```bash
# Проверьте использование памяти
free -h
docker stats

# Уменьшите количество воркеров в docker-compose.prod.yml
# backend: --workers 1
# celery: --concurrency=1
```

---

## 📞 Поддержка

Если возникли проблемы, проверьте:
1. Логи контейнеров: `sudo docker-compose logs -f`
2. Статус сервисов: `sudo docker-compose ps`
3. Свободное место на диске: `df -h`
4. Использование памяти: `free -h`

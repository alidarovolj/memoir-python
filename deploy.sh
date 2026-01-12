#!/bin/bash

# Memoir Backend Deployment Script
# Для Ubuntu 22.04 LTS

set -e

echo "🚀 Starting Memoir Backend Deployment..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Обновление системы
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Установка необходимых пакетов
echo -e "${YELLOW}📦 Installing required packages...${NC}"
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    python3 \
    python3-pip

# Установка Docker
echo -e "${YELLOW}🐳 Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Установка Docker Compose
echo -e "${YELLOW}🐳 Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Создание директории для проекта
echo -e "${YELLOW}📁 Setting up project directory...${NC}"
PROJECT_DIR="/home/ubuntu/memoir"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    echo -e "${GREEN}✅ Project directory created${NC}"
else
    echo -e "${GREEN}✅ Project directory exists${NC}"
fi

# Клонирование репозитория
cd /home/ubuntu
echo -e "${YELLOW}📥 Cloning repository...${NC}"
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "Enter your GitHub repository URL:"
    read REPO_URL
    git clone $REPO_URL memoir
else
    echo -e "${YELLOW}Repository exists, pulling latest changes...${NC}"
    cd memoir
    git pull
fi

cd "$PROJECT_DIR/backend"

# Создание .env файла если не существует
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file based on .env.example${NC}"
    echo -e "${YELLOW}Use: nano .env${NC}"
    exit 1
fi

# Запуск миграций и Docker контейнеров
echo -e "${YELLOW}🔧 Building and starting Docker containers...${NC}"
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d

# Ожидание запуска контейнеров
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Запуск миграций
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
sudo docker-compose exec -T backend alembic upgrade head

# Проверка статуса
echo -e "${YELLOW}📊 Checking services status...${NC}"
sudo docker-compose ps

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo "🌐 Backend API: http://194.32.140.80:8000"
echo "📚 API Docs: http://194.32.140.80:8000/docs"
echo "🌺 Flower (Celery): http://194.32.140.80:5555"
echo ""
echo "📝 View logs: sudo docker-compose logs -f"
echo "🔄 Restart services: sudo docker-compose restart"
echo "🛑 Stop services: sudo docker-compose down"

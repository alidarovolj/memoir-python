# Memoir Backend API

**AI-powered Personal Memory Management System** - Backend API built with FastAPI, PostgreSQL, and OpenAI.

## 🚀 Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 16 + pgvector extension
- **Cache**: Redis
- **Background Tasks**: Celery
- **AI**: OpenAI API (GPT-4o-mini, text-embedding-3-small)
- **Container**: Docker + Docker Compose

## 📋 Features

- ✅ JWT Authentication (30-day tokens)
- ✅ Memory CRUD with AI classification
- ✅ Smart Content Search (TMDB, Google Books, etc.)
- ✅ Stories (Instagram-like, 7-day expiration)
- ✅ Tasks & Planning with AI suggestions
- ✅ Semantic search with embeddings
- ✅ Background AI processing with Celery

## 🛠️ Local Development

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (optional, for local dev)

### Quick Start

1. **Clone the repository**
```bash
git clone git@github.com:alidarovolj/memoir-python.git
cd memoir-python
```

2. **Set up environment variables**
```bash
cp .env.example .env
nano .env  # Add your API keys
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec backend alembic upgrade head
```

5. **API is ready!**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📁 Project Structure

```
.
├── app/
│   ├── api/              # API endpoints
│   │   └── v1/          # API v1 routes
│   ├── core/            # Core config & security
│   ├── db/              # Database setup
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── tasks/           # Celery tasks
├── alembic/             # Database migrations
├── tests/               # Tests
├── docker-compose.yml   # Docker services
├── Dockerfile          # Backend container
└── requirements.txt    # Python dependencies
```

## 🔐 Environment Variables

Required variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://memoir_user:memoir_pass@postgres:5432/memoir

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# OpenAI
OPENAI_API_KEY=sk-...

# External APIs
TMDB_API_KEY=your-tmdb-key
GOOGLE_BOOKS_KEY=your-google-books-key
# ... other API keys
```

## 🧪 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Memories
- `GET /api/v1/memories` - List memories
- `POST /api/v1/memories` - Create memory (AI classification in background)
- `GET /api/v1/memories/{id}` - Get memory details
- `PUT /api/v1/memories/{id}` - Update memory
- `DELETE /api/v1/memories/{id}` - Delete memory

### Stories
- `GET /api/v1/stories` - List public stories
- `POST /api/v1/stories` - Create story
- `DELETE /api/v1/stories/{id}` - Delete story

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `POST /api/v1/tasks/analyze` - AI analyze task

### Smart Search
- `POST /api/v1/smart-search` - Universal smart search

## 🐳 Docker Services

```yaml
services:
  postgres:    # PostgreSQL 16 + pgvector
  redis:       # Redis 7
  backend:     # FastAPI app
  celery:      # Background worker
  flower:      # Celery monitoring (optional)
```

## 🚀 Production Deployment

### VPS Setup (Ubuntu 22.04 LTS)

1. **Install Docker**
```bash
curl -fsSL https://get.docker.com | sh
sudo apt install docker-compose-plugin -y
```

2. **Clone and configure**
```bash
git clone git@github.com:alidarovolj/memoir-python.git
cd memoir-python
cp .env.example .env
nano .env  # Add production values
```

3. **Start services**
```bash
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

4. **Setup Nginx (optional)**
```nginx
server {
    listen 80;
    server_name api.memoir-ai.net;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Database Schema

### Key Tables
- `users` - User accounts
- `memories` - User memories with AI metadata
- `categories` - Predefined categories
- `embeddings` - Vector embeddings for semantic search
- `stories` - Instagram-like stories (7-day expiration)
- `tasks` - User tasks with AI suggestions

## 🤖 AI Features

### Memory Classification
- Automatic category detection
- Tag generation
- Entity extraction
- Confidence scoring

### Task Analysis
- Smart time scope detection (daily/weekly/monthly/long-term)
- Priority suggestion
- Category assignment

### Smart Search
- Intent detection (movie, book, place, recipe)
- External API integration (TMDB, Google Books, etc.)
- Rich metadata fetching

## 🧪 Testing

```bash
# Run tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app
```

## 📝 Database Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## 🔍 Monitoring

- **Flower**: http://localhost:5555 (Celery monitoring)
- **Logs**: `docker-compose logs -f backend`

## 📦 Dependencies

See `requirements.txt` for full list. Key packages:
- fastapi==0.109.0
- sqlalchemy==2.0.25
- asyncpg==0.29.0
- openai==1.10.0
- celery==5.3.6
- redis==5.0.1

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Related

- **Flutter App**: [memoir-flutter](https://github.com/alidarovolj/memoir)
- **API Docs**: http://localhost:8000/docs

## 👤 Author

**Alidarov Olzhas**
- GitHub: [@alidarovolj](https://github.com/alidarovolj)

## ⭐ Support

Give a ⭐️ if this project helped you!

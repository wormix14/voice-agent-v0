# Voice Agent V0

An AI-powered voice and text assistant built with FastAPI, PostgreSQL.

---

## 🛠 Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn
- **Package & Environment Management:** [uv](https://docs.astral.sh/uv/)
- **Database:** PostgreSQL 16, SQLAlchemy, `psycopg2-binary`
- **Containerization:** Docker

---

## ⚙️ Environment Configuration

1. Create a `.env` file in the project root:

```env
# Database Credentials
DATABASE_URL=postgresql+psycopg2://app_user:app_password@db:5432/app_db

# Third-Party API Keys
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
CARTESIA_API_KEY=your_cartesia_api_key_here
```
## Running with Docker Compose
```
docker compose up --build
```
## Endpoints
Web UI: http://localhost:8000
PostgreSQL: localhost:5433 / db:5432 (internal Docker network)
## Stop Services
```
docker compose down
```

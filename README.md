# Holistic Novel Engine

A production-grade multi-agent system for AI-powered novel writing.

## Architecture

- **Backend**: Python FastAPI with async support
- **Frontend**: Next.js with Tailwind CSS
- **Database**: PostgreSQL (structured) + Pinecone (vector)
- **Queue**: Celery + Redis
- **Orchestration**: LangGraph

## Quick Start

```bash
# Start all services
docker-compose up -d

# Backend only
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm install && npm run dev
```

## Agent System

| Agent | Role |
|-------|------|
| **Architect** | Creates outlines, character sheets, world-building |
| **Lorekeeper** | RAG-based consistency manager |
| **Beater** | Breaks chapters into story beats |
| **Ghostwriter** | Generates prose from beats |
| **Editor** | Reviews and critiques output |

## License

MIT

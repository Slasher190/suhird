# Suhird (सुहृद्)

**A WhatsApp-based matchmaking platform** — Sanskrit for "good-hearted friend".

Open source, AI-powered, designed for 1-2K user scale. Integrates with [OpenClaw](https://github.com/openclaw/openclaw) as the WhatsApp gateway.

## Architecture

```
WhatsApp Users
      |
OpenClaw Gateway (:18789)
      |
      ├── Known numbers → Normal assistant (unchanged)
      └── Unknown numbers → Suhird Bot (:8000)
                               |
                               ├── PostgreSQL (:5433) — profiles, matches
                               ├── Qdrant (:6335) — vector embeddings
                               ├── Redis (:6380) — session management
                               ├── MemPalace (:8001) — preference learning
                               └── Local storage — photos
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenClaw gateway running with WhatsApp connected
- Ollama with `nomic-embed-text` model pulled

### 1. Clone and configure

```bash
cd suhird
cp .env.example .env
# Edit .env with your actual secrets and tokens
```

### 2. Pull the Ollama embedding model

```bash
ollama pull nomic-embed-text
```

### 3. Start all services

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port 5433
- Qdrant on port 6335
- Redis on port 6380
- MemPalace service on port 8001
- Suhird bot on port 8000

### 4. Configure OpenClaw

```bash
bash scripts/apply_openclaw_config.sh
```

This backs up your OpenClaw config, then:
- Changes `dmPolicy` to `"open"` (accepts messages from unknown numbers)
- Adds Suhird as a model provider (`suhird-bot/matchmaker`)
- Adds a matchmaker agent for unknown numbers

Restart the OpenClaw gateway after applying:
```bash
launchctl stop ai.openclaw.gateway && launchctl start ai.openclaw.gateway
```

### 5. Verify

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "suhird"}

curl http://localhost:8001/health
# {"status": "ok", "service": "mempalace"}
```

## How It Works

### User Flow

1. Unknown number texts "Hi" on WhatsApp
2. OpenClaw routes message to Suhird
3. Suhird starts onboarding (25+ questions)
4. Profile completed with photos
5. User requests matches → gets top 5 recommendations
6. User likes/passes on profiles
7. Mutual like → both users get each other's contact

### Matching Algorithm

```
Final Score = 30% Structured + 30% Semantic + 40% MemPalace
```

- **Structured (30%)**: Age, location, gender preferences, lifestyle compatibility
- **Semantic (30%)**: Qdrant vector similarity on bio prompts and interests
- **MemPalace (40%)**: Learned from like/skip behavior over time

### Onboarding Questions (34 total)

| Section      | Count | Topics                                    |
|-------------|-------|-------------------------------------------|
| Basic Info   | 4     | Name, age, gender, location              |
| Bio Prompts  | 8     | Hinge-style conversation starters        |
| Preferences  | 4     | Looking for gender, age range, distance  |
| Lifestyle    | 11    | Work, smoking, diet, exercise, pets...   |
| Values       | 5     | Religion, politics, ambition, finance    |
| Interests    | 1     | Multi-select from 20 categories          |
| Photos       | -     | Up to 6 photos                           |

## API Reference

### OpenResponses Endpoint (OpenClaw integration)

```
POST /v1/responses
Authorization: Bearer <SUHIRD_API_TOKEN>
```

### REST API

All REST endpoints require JWT authentication via `Authorization: Bearer <token>`.

| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| POST   | /api/users                    | Create user              |
| POST   | /api/users/auth               | Get JWT token            |
| GET    | /api/users/{id}               | Get profile              |
| PUT    | /api/users/{id}               | Update profile           |
| POST   | /api/users/{id}/photos        | Upload photo             |
| GET    | /api/users/{id}/photos/{n}    | Get photo                |
| GET    | /api/users/{id}/matches       | Get recommendations      |
| POST   | /api/matches/{id}/like        | Like a profile           |
| POST   | /api/matches/{id}/pass        | Pass a profile           |
| GET    | /api/matches/mutual           | Get mutual matches       |
| POST   | /api/blocks                   | Block a user             |

### WhatsApp Bot Commands

| Command        | Description                    |
|---------------|--------------------------------|
| show matches   | Browse match recommendations  |
| my profile     | View your profile             |
| help           | Show available commands       |
| like 1         | Like profile #1               |
| pass 2         | Pass on profile #2            |
| like all       | Like all shown profiles       |
| more           | Show next batch               |
| stop           | Stop browsing                 |

## Project Structure

```
suhird/
├── docker-compose.yml
├── Dockerfile
├── .env / .env.example
├── requirements.txt
├── README.md
├── migrations/
│   └── 001_initial.sql
├── src/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings from .env
│   ├── database.py              # Async PostgreSQL connection
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── api/
│   │   ├── webhook.py           # OpenResponses + WhatsApp webhook
│   │   ├── users.py             # User CRUD endpoints
│   │   └── matches.py           # Match endpoints
│   ├── bot/
│   │   ├── handler.py           # Message dispatcher
│   │   ├── onboarding.py        # 34-question flow
│   │   ├── states.py            # Conversation state machine
│   │   └── messages.py          # WhatsApp message templates
│   ├── services/
│   │   ├── user_service.py      # User CRUD
│   │   ├── matching_service.py  # 3-component matching engine
│   │   ├── photo_service.py     # Photo upload/resize/serve
│   │   ├── qdrant_service.py    # Vector operations
│   │   └── mempalace_service.py # Preference learning client
│   └── utils/
│       ├── embeddings.py        # Ollama embedding generation
│       ├── validators.py        # Input validation
│       └── security.py          # JWT + phone encryption
├── mempalace_service/
│   ├── main.py                  # FastAPI wrapper for MemPalace
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/
│   └── apply_openclaw_config.sh # OpenClaw config helper
├── photos/                      # Local photo storage
└── logs/
```

## Environment Variables

See [`.env.example`](.env.example) for all configuration options.

## Tech Stack

| Component   | Technology            | Port  |
|------------|----------------------|-------|
| Backend    | Python 3.11 + FastAPI | 8000  |
| Database   | PostgreSQL 16         | 5433  |
| Vector DB  | Qdrant                | 6335  |
| Sessions   | Redis 7               | 6380  |
| Memory     | MemPalace + ChromaDB  | 8001  |
| Embeddings | Ollama + nomic-embed  | 11434 |
| Gateway    | OpenClaw              | 18789 |

## License

Open source. MIT License.

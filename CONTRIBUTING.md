# Contributing to Suhird

Thank you for your interest in contributing to Suhird! Whether it's a bug fix, a new feature, documentation improvement, or a translation — every contribution matters.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Guidelines](#coding-guidelines)
- [Project Structure](#project-structure)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Community](#community)

---

## Code of Conduct

By participating in this project, you agree to maintain a welcoming and respectful environment. Be kind, be constructive, and remember the name — Suhird means "good-hearted friend."

- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/suhird.git
   cd suhird
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/Slasher190/suhird.git
   ```
4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Ollama with `nomic-embed-text` model
- OpenClaw gateway (optional, for WhatsApp integration testing)

### Install dependencies

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Start infrastructure services

```bash
# Start PostgreSQL, Qdrant, Redis, MemPalace
docker compose up -d postgres qdrant redis mempalace
```

### Configure environment

```bash
cp .env.example .env
# Edit .env with your local settings
```

### Run the app locally

```bash
uvicorn src.main:app --reload --port 8000
```

### Run the MemPalace service locally

```bash
cd mempalace_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

---

## How to Contribute

### Areas where help is welcome

| Area | Description |
|------|-------------|
| **Bug fixes** | Found something broken? Fix it! |
| **Matching algorithm** | Improve scoring, add new signals |
| **Onboarding UX** | Better question flow, multilingual support |
| **Testing** | Unit tests, integration tests, load tests |
| **Documentation** | Improve README, add API docs, write guides |
| **Translations** | Translate bot messages to other languages |
| **Security** | Audit encryption, auth, data handling |
| **Performance** | Optimize queries, caching, connection pooling |
| **Frontend** | Admin dashboard, analytics panel |
| **DevOps** | CI/CD pipeline, Kubernetes manifests |

### Good first issues

Look for issues labeled `good first issue` or `help wanted` in the [Issues tab](https://github.com/Slasher190/suhird/issues). These are specifically curated for new contributors.

---

## Pull Request Process

1. **Sync your fork** before starting work:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Make your changes** in a dedicated branch:
   ```bash
   git checkout -b fix/describe-the-fix
   ```

3. **Keep commits focused** — one logical change per commit. Write clear commit messages:
   ```
   Fix age validation accepting values below 18

   The validator was using > instead of >= for the lower bound check,
   allowing 17-year-olds to register.
   ```

4. **Test your changes** — make sure existing functionality isn't broken.

5. **Push and open a PR**:
   ```bash
   git push origin fix/describe-the-fix
   ```
   Then open a Pull Request on GitHub against `main`.

6. **PR description** should include:
   - What changed and why
   - How to test it
   - Screenshots (if UI-related)
   - Related issue number (e.g., `Closes #12`)

7. **Review** — maintainers will review your PR. Be open to feedback and requested changes.

### Branch naming convention

| Prefix | Use for |
|--------|---------|
| `feature/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes |
| `refactor/` | Code restructuring |
| `test/` | Adding or updating tests |
| `chore/` | Build, CI, dependency updates |

---

## Coding Guidelines

### Python

- **Python 3.11+** — use modern syntax (type hints, `match`, `|` unions)
- **Formatting** — follow PEP 8. Use `black` for auto-formatting if available
- **Type hints** — add them to all function signatures
- **Docstrings** — add to public functions and classes. Keep them concise
- **No unnecessary comments** — code should be self-explanatory. Comment only non-obvious logic

### FastAPI conventions

- Use `async def` for all route handlers
- Use dependency injection (`Depends()`) for DB sessions and auth
- Return Pydantic models from endpoints, not raw dicts
- Use proper HTTP status codes (201 for creation, 409 for conflicts, etc.)

### Database

- Never write raw SQL in Python code — use SQLAlchemy ORM
- Add migrations for any schema changes in `migrations/`
- Use UUIDs for primary keys
- Add indexes for columns used in WHERE clauses

### Git

- Don't commit `.env`, secrets, or large binary files
- Don't commit `__pycache__/` or IDE config files
- Rebase on `main` before opening a PR (no merge commits)

---

## Project Structure

```
suhird/
├── src/
│   ├── main.py              # App entry point
│   ├── config.py            # Settings
│   ├── database.py          # DB connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/                 # REST + webhook endpoints
│   ├── bot/                 # Conversation engine
│   ├── services/            # Business logic
│   └── utils/               # Helpers (security, embeddings)
├── mempalace_service/       # Standalone preference learning service
├── migrations/              # SQL migrations
├── assets/                  # Logo, images
└── scripts/                 # Setup helpers
```

When adding new files:
- **New endpoint** → `src/api/`
- **New service/business logic** → `src/services/`
- **New bot feature** → `src/bot/`
- **New utility** → `src/utils/`
- **Schema change** → `migrations/` + `src/models.py` + `src/schemas.py`

---

## Reporting Bugs

Open an issue with the `bug` label and include:

1. **Description** — what happened vs what you expected
2. **Steps to reproduce** — minimal steps to trigger the bug
3. **Environment** — OS, Python version, Docker version
4. **Logs** — relevant error messages or stack traces
5. **Screenshots** — if applicable

---

## Suggesting Features

Open an issue with the `enhancement` label and include:

1. **Problem** — what user need does this address?
2. **Proposed solution** — how should it work?
3. **Alternatives considered** — what else did you think of?
4. **Scope** — is this a small tweak or a large feature?

---

## Community

- **Issues** — [github.com/Slasher190/suhird/issues](https://github.com/Slasher190/suhird/issues)
- **Discussions** — open a GitHub Discussion for questions or ideas
- **Maintainer** — [@Slasher190](https://github.com/Slasher190)

---

Thank you for helping make Suhird better. Every contribution, no matter how small, helps people find meaningful connections.

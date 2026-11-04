# DevTeam AI

**An AI-powered multi-agent software development platform** that acts as your virtual engineering team.

> Describe your software in plain language → Six specialized AI agents design, build, test and review it for you.

---

## Overview

DevTeam AI orchestrates a team of six specialized AI agents using **CrewAI** and **Meta Muse Spark**:

| Agent | Responsibility |
|---|---|
| 🗂️ Product Manager | Requirement analysis and user story generation |
| 🏗️ Software Architect | System design and technology stack selection |
| 🗄️ Database Designer | Schema design, ER diagrams and data modeling |
| 💻 Developer | Code generation across frontend and backend |
| 🧪 Testing Engineer | Unit tests, integration tests and test reports |
| 🔍 Code Reviewer | Code quality checks and best-practice review |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | Python 3.10 + FastAPI |
| Multi-agent Framework | CrewAI + CrewAI Flows |
| AI Model | Meta Muse Spark (Phase 2) |
| Database | SQLite (initial) |
| Code Execution | Docker (Phase 3) |

---

## Project Structure

```
DevTeam AI/
├── frontend/              ← React + Vite application
│   ├── src/
│   │   ├── components/    ← Reusable UI components
│   │   ├── pages/         ← Page-level components
│   │   ├── layouts/       ← Layout wrappers
│   │   └── services/      ← API service layer
│   ├── public/
│   └── vite.config.js
│
├── backend/               ← FastAPI application
│   ├── api/               ← Route handlers
│   │   └── endpoints/     ← Individual endpoint modules
│   ├── agents/            ← CrewAI agent definitions (Phase 2)
│   ├── workflows/         ← CrewAI flows (Phase 2)
│   ├── services/          ← Business logic
│   ├── database/          ← SQLite models
│   ├── main.py            ← FastAPI entry point
│   ├── requirements.txt
│   └── venv/              ← Python virtual environment (existing)
│
├── generated_projects/    ← AI-generated project outputs (Phase 2)
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js 18+ and npm 9+
- Python 3.10 (venv already set up in `backend/venv/`)

---

### Backend Setup

```bash
# From the project root
cd backend

# Activate the existing virtual environment (Windows)
venv\Scripts\activate

# (macOS / Linux)
source venv/bin/activate

# Copy environment template and configure values
cp .env.example .env

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**  
Interactive docs at **http://localhost:8000/docs**

---

### Frontend Setup

```bash
# From the project root
cd frontend

# Install dependencies
npm install

# Copy environment template (already pre-configured for local dev)
cp .env.example .env

# Start the development server
npm run dev
```

The app will be available at **http://localhost:5173**

---

### Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "DevTeam AI API",
  "version": "1.0.0",
  "timestamp": "...",
  "uptime": "operational"
}
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Backend health check |
| `GET` | `/api/projects` | List all projects |
| `GET` | `/docs` | Swagger interactive docs |

---

## Development Phases

| Phase | Status | Description |
|---|---|---|
| **Phase 1** | ✅ Complete | Frontend + Backend foundation, health check |
| **Phase 2** | 🔜 Planned | CrewAI agents + Meta Muse Spark integration |
| **Phase 3** | 🔜 Planned | Docker code execution and project export |

---

## Environment Variables

**Backend** (`backend/.env`):
```env
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:5173
META_API_KEY=your_meta_api_key_here
DATABASE_URL=sqlite:///./devteam_ai.db
APP_ENV=development
SECRET_KEY=your_secret_key_here
```

**Frontend** (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
```

> ⚠️ **Never commit `.env` files with real API keys.**

---

## Security

- API keys are **never hardcoded** in frontend or backend code.
- All secrets are loaded from `.env` files via `python-dotenv`.
- `.env` is in `.gitignore`.
- The frontend communicates with the backend API only — never directly with third-party AI APIs.

---

## License

MIT © DevTeam AI


# 📊 InstaVest

> **Institutional-grade stock research, rebuilt for the AI era.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)

---

## What is InstaVest?

InstaVest is an AI-native investment research terminal designed for serious retail investors, finance students, and independent analysts who don't have access to Bloomberg or Capital IQ.

**Core question it answers:** *"What changed about a company, why does it matter, and does it affect my investment thesis?"*

### Key Features

- 🧠 **Company Brain** — Aggregated intelligence object per company
- 📈 **Reverse DCF** — Deterministic valuation with market expectations analysis
- ⚡ **Signal Engine** — Rule-based signals with prioritization ranking
- 📋 **Thesis Boards** — Track investment theses with monitored assumptions
- 💼 **Portfolio Intelligence** — Risk analytics and concentration analysis
- 📊 **Peer Comparison** — Relative valuation across peer groups
- 🤖 **AI Synthesis** — Claude-powered research summaries (never invents numbers)
- 📝 **Investment Memos** — Auto-generated institutional-grade reports

---

## Quick Start

### Prerequisites

- [Docker](https://docker.com/get-started) & Docker Compose
- [Node.js 20+](https://nodejs.org) (for local frontend dev)

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/InstaVest.git
cd InstaVest
cp .env.example .env
```

Edit `.env` with your API keys (optional — mock data works without them).

### 2. Start Everything

```bash
make up
```

This boots:
- **PostgreSQL** on `localhost:5432`
- **FastAPI API** on `localhost:8000` ([API docs](http://localhost:8000/docs))
- **Next.js frontend** on `localhost:3000`

### 3. Run Migrations

```bash
make migrate
```

### 4. Seed Mock Data (optional)

```bash
make seed
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         Next.js 15 + TailwindCSS + shadcn        │
│    Dashboard │ Research │ Thesis │ Portfolio      │
└────────────────────┬────────────────────────────┘
                     │ REST API
┌────────────────────┴────────────────────────────┐
│                FastAPI Backend                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │Ingestion │ │Valuation │ │  Signal Engine    │ │
│  │ Service  │ │ Service  │ │  + Prioritizer    │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Thesis   │ │Portfolio │ │  AI Reasoning    │ │
│  │ Service  │ │ Service  │ │  (Claude API)    │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────────────────────────────────────────┐│
│  │      Company Brain + Event Bus               ││
│  └──────────────────────────────────────────────┘│
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────┐
│              PostgreSQL 16                        │
│  25+ tables: companies, brains, signals,          │
│  thesis, portfolios, models, events, etc.         │
└─────────────────────────────────────────────────┘
```

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Tail logs |
| `make migrate` | Run database migrations |
| `make seed` | Seed mock data |
| `make test` | Run all tests |
| `make clean` | Remove containers and volumes |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Auto | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | No | Claude API for AI synthesis |
| `FMP_API_KEY` | No | Financial Modeling Prep for data |
| `NEXT_PUBLIC_API_URL` | Auto | Backend API URL |

---

## License

MIT

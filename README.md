# Trading Risk Dashboard

Internal decision-support tooling for a commodities trading business, starting
with **trading risk (TMT)**. This repository contains the first end-to-end
slice: a read-only dashboard that surfaces positions, exposure, P/L,
utilisation and supplied VaR, and raises deterministic, explainable alerts.

> **Demonstration prototype.** Not a trade-execution, pricing or booking
> system. Position data is **synthetic sample data**; the Live Market page uses
> **real prices from a free, unofficial source (Yahoo Finance)** — clearly
> labelled, not the firm's authoritative feed, and stored as application-owned
> history. Upstream access is read-only.

## Architecture

A modular monolith:

```
React + TypeScript (Vite, MUI, Plotly, TanStack Query)        frontend/
        │  typed API over /api/v1
FastAPI + Pydantic + pandas + SQLAlchemy 2.x                   backend/
        │  read-only adapters → domain calc / ingestion → typed API
data/sample/positions.csv     (deterministic synthetic source)
Yahoo Finance (yfinance)  →   PostgreSQL market history (e.g. Neon)
```

Flow: **source adapter → domain valuation → portfolio summary + alert
evaluation → typed API → dashboard**. Financial definitions live only in the
backend domain/alert layers; the frontend owns presentation, formatting,
filters and states. The frontend never duplicates business logic.

## What this slice includes

- **Backend** (`backend/app`)
  - `domain/` — position valuation and portfolio aggregation, pure functions
    using `Decimal`. Explicit sign convention; missing values kept distinct
    from zero; no cross-currency aggregation without an FX rate.
  - `alerts/` — deterministic rules (exposure utilisation, P/L loss, VaR,
    missing data, staleness) with thresholds in backend config only.
  - `adapters/` — read-only CSV source, precision-preserving.
  - `api/` (`/api/v1`) — `health`, `filters`, `positions` (paginated/filterable),
    `summary`, `alerts`. Errors map to stable machine-readable codes.
- **Live market (real data + persisted history)**
  - `adapters/yahoo_market_source.py` — read-only yfinance adapter; source time,
    currency and unit preserved with **no conversion** (grains in `USc`/bu,
    copper in USD/lb). `POWER` omitted — no reliable free source.
  - `db_models.py` + `repositories/` — idempotent persistence
    (`UNIQUE(symbol, source_ts)`) into `market_observation`, plus an
    `ingestion_run` audit table for control/management.
  - `services/ingestion.py` + `app/ingest.py` — one ingestion cycle or a single
    `--loop` process; `POST /market/ingest` triggers it on demand.
  - `api/` — `/market` (latest + recent series), `/market/history`,
    `/ingestion-runs`.
- **Frontend** (`frontend/src`)
  - KPI cards, positions table (MUI X Data Grid), exposure-concentration chart
    (Plotly), alerts panel, and desk/trader/commodity filters synced to the URL.
  - Live Market page: real-data labelling, source/ingest timestamps, **text**
    stale status, DB-backed history chart, and a "Refresh now" ingestion trigger.
  - Loading, empty, stale-refresh and error states. Polling for near-real-time
    refresh, preserving the last good response during background refresh.
  - Severity shown as **text and** colour (never colour alone).

## Deferred (intentionally not built yet)

The project rules say not to build infrastructure for hypothetical needs.

- **PostgreSQL + SQLAlchemy 2.x + Alembic** — **now added** for the live-market
  history slice, using a managed database (e.g. Neon); no local Docker Compose.
  Not substituted with SQLite. Other application-owned state (e.g. alert
  acknowledgements) will reuse it as features require.
- **Authentication (OIDC/SSO)** — added when access control is required.

## Toolchain note

The prescribed stack was adapted to the local environment (Node 16, no Docker):
the frontend pins **Vite 4 + Vitest 0.34** (Node-16-compatible) instead of
Vite 5. The backend matches the spec (Python 3.11+, FastAPI, Pydantic v2,
pandas, SQLAlchemy 2.x, Alembic, psycopg 3). Persistence uses a **managed
PostgreSQL** (e.g. Neon) rather than local Docker Compose, since Docker is not
available in this environment.

## Running locally

Prerequisites: Python 3.11+ and Node.js (16+). No database is required.

```bash
# 1) Install
cd backend  && python -m pip install -r requirements-dev.txt
cd ../frontend && npm install

# 2) Run the backend (terminal 1)
cd backend && python -m uvicorn app.main:app --reload --port 8000

# 3) Run the frontend (terminal 2) — proxies /api to the backend
cd frontend && npm run dev
# open http://localhost:5173
```

With GNU Make available, the same steps are `make setup`, `make dev-backend`,
`make dev-frontend`.

### Live market data (optional)

The positions dashboard needs no database. For the Live Market page's **real**
data and history, point the backend at a PostgreSQL database and ingest:

```bash
# 1) Create a free Postgres (e.g. Neon) and set the URL in backend/.env
#    (git-ignored). Note the +psycopg driver and sslmode=require:
# DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/neondb?sslmode=require

# 2) Apply migrations
cd backend && python -m alembic upgrade head        # or: make migrate

# 3) Fetch + store data
cd backend && python -m app.ingest                  # one cycle  (make ingest)
cd backend && python -m app.ingest --loop --interval 60   # continuous (make ingest-loop)
# …or click "Refresh now" on the page.
```

Without a `DATABASE_URL`, set `MARKET_SOURCE=synthetic` to run the page on the
offline illustrative generator (no DB, no network).

## Tests and checks

```bash
# Backend
cd backend && python -m pytest -q && ruff check . && ruff format --check . && mypy

# Frontend
cd frontend && npm test && npm run typecheck && npm run build
```

Current status: backend **50 pytest** passing + **3 Postgres integration tests**
that skip without `DATABASE_URL` (ruff + mypy clean); frontend **15 Vitest**
passing (tsc + build clean). Alert rules are tested immediately below, at and
above each threshold, plus missing, stale and duplicate inputs; ingestion is
tested for idempotency (the `ON CONFLICT` path).

## Key data rules honoured

- Sign convention explicit: `quantity` signed (long +, short −);
  `market_value = quantity × market_price`,
  `unrealised_pl = quantity × (market_price − avg_price)`.
- Missing inputs (`market_price`, `var_1d`) are preserved as null, excluded
  from totals, and flagged — never treated as zero. Row P014 demonstrates this.
- Money computed in `Decimal`; rounded only for display.
- VaR is a **supplied** value; the portfolio VaR card is a labelled
  illustrative simple sum (ignores diversification), not an authoritative VaR.
- Timestamps stored in UTC, displayed in `Europe/London`.
- No currency aggregation without an approved FX rate (the API refuses it).
- Alert thresholds live in `backend/app/alerts/config.py`, never the frontend.

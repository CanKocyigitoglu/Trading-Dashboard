# Trading Risk Dashboard

Internal decision-support tooling for a commodities trading business, starting
with **trading risk (TMT)**. This repository contains the first end-to-end
slice: a read-only dashboard that surfaces positions, exposure, P/L,
utilisation and supplied VaR, and raises deterministic, explainable alerts.

> **Demonstration prototype.** Not a trade-execution, pricing or booking
> system. All sample data is **synthetic**. Upstream access is read-only.

## Architecture

A modular monolith:

```
React + TypeScript (Vite, MUI, Plotly, TanStack Query)        frontend/
        │  typed API over /api/v1
FastAPI + Pydantic + pandas                                    backend/
        │  read-only source adapter → domain calc → alerts → typed API
data/sample/positions.csv  (deterministic synthetic source)
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
- **Frontend** (`frontend/src`)
  - KPI cards, positions table (MUI X Data Grid), exposure-concentration chart
    (Plotly), alerts panel, and desk/trader/commodity filters synced to the URL.
  - Loading, empty, stale-refresh and error states. Polling for near-real-time
    refresh, preserving the last good response during background refresh.
  - Severity shown as **text and** colour (never colour alone).

## Deferred (intentionally not built yet)

The project rules say not to build infrastructure for hypothetical needs. The
first dashboard is read-only and needs no application-owned state, so these are
deferred until a feature requires them:

- **PostgreSQL + SQLAlchemy + Alembic + Docker Compose** — added with the first
  write workflow (e.g. alert acknowledgements, audit). Not substituted with
  SQLite.
- **Authentication (OIDC/SSO)** — added when access control is required.

## Toolchain note

The prescribed stack was adapted to the local environment (Node 16, no Docker):
the frontend pins **Vite 4 + Vitest 0.34** (Node-16-compatible) instead of
Vite 5. The backend matches the spec (Python 3.11+, FastAPI, Pydantic v2,
pandas). When Node 18+ and Docker are available, the frontend versions can be
bumped and the persistence slice added.

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

## Tests and checks

```bash
# Backend
cd backend && python -m pytest -q && ruff check . && ruff format --check . && mypy

# Frontend
cd frontend && npm test && npm run typecheck && npm run build
```

Current status: backend **36 pytest** passing (ruff + mypy clean); frontend
**10 Vitest** passing (tsc + build clean). Alert rules are tested immediately
below, at and above each threshold, plus missing, stale and duplicate inputs.

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

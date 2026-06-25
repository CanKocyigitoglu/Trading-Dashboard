.PHONY: setup dev dev-backend dev-frontend test test-backend test-frontend check clean \
        db-up db-down migrate seed ingest ingest-loop

# --- Setup -----------------------------------------------------------------

setup:
	cd backend && python -m pip install -r requirements-dev.txt
	cd frontend && npm install

# --- Develop ---------------------------------------------------------------
# Run the two dev servers in separate terminals.

dev:
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals."

dev-backend:
	cd backend && python -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# --- Test ------------------------------------------------------------------

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest -q

test-frontend:
	cd frontend && npm test

# --- Lint / typecheck ------------------------------------------------------

check:
	cd backend && ruff check . && ruff format --check . && mypy
	cd frontend && npm run typecheck

# --- Clean -----------------------------------------------------------------

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache frontend/dist
	find backend -type d -name __pycache__ -prune -exec rm -rf {} +

# --- Database --------------------------------------------------------------
# PostgreSQL is provided by a managed service (e.g. Neon); there is no local
# docker-compose. Set DATABASE_URL in backend/.env, then apply migrations.

db-up db-down:
	@echo "Using managed PostgreSQL (e.g. Neon). No local container to start/stop."

migrate:
	cd backend && python -m alembic upgrade head

# --- Market data ingestion -------------------------------------------------
# `seed` runs one cycle to populate initial history; `ingest-loop` keeps it
# refreshing as a single dedicated process.

ingest seed:
	cd backend && python -m app.ingest

ingest-loop:
	cd backend && python -m app.ingest --loop --interval 60

.PHONY: setup dev dev-backend dev-frontend test test-backend test-frontend check clean \
        db-up db-down migrate seed

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

# --- Database (deferred) ---------------------------------------------------
# The current slice is read-only and has no persistence, so these targets are
# placeholders. They will be implemented (docker-compose + Alembic) when a
# write workflow first requires application-owned state.

db-up db-down migrate seed:
	@echo "No database in the current read-only slice. See README (Deferred)."

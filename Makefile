.PHONY: run db-up db-down migrate migration test lint typecheck

# Start local development server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Docker services (PostgreSQL)
db-up:
	docker-compose up -d

db-down:
	docker-compose down

# Run Alembic migrations
migrate:
	alembic upgrade head

# Create a new migration
migration:
	alembic revision --autogenerate -m "$(msg)"

# Run tests
test:
	pytest tests/ -v

# Lint and format
lint:
	ruff check app/ tests/
	ruff format app/ tests/

# Type check
typecheck:
	mypy app/

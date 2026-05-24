.PHONY: up down logs migrate seed test clean

# ─── Development ────────────────────────────────────
up:
	docker compose up --build -d
	@echo "✅ InstaVest running — Frontend: http://localhost:3000 | API: http://localhost:8000/docs"

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

# ─── Database ───────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

migrate-generate:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec api python -m app.seed

# ─── Testing ────────────────────────────────────────
test:
	docker compose exec api pytest tests/ -v

test-backend:
	docker compose exec api pytest tests/ -v

test-frontend:
	docker compose exec web npm test

# ─── Cleanup ────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans
	@echo "🧹 Cleaned up containers and volumes"

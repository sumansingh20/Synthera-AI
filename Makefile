.PHONY: install dev setup run-api run-frontend run test lint format clean docker-up docker-down

# ─── Installation ────────────────────────────────────────
install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"

setup: install
	cp -n .env.example .env 2>/dev/null || true
	@echo "Setup complete. Edit .env with your API keys."

# ─── Run Services ────────────────────────────────────────
run-api:
	uvicorn synthera.api.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	streamlit run frontend/app.py --server.port 8501

run: ## Run both backend and frontend
	@echo "Starting backend..."
	uvicorn synthera.api.main:app --host 0.0.0.0 --port 8000 --reload &
	@echo "Starting frontend..."
	streamlit run frontend/app.py --server.port 8501

# ─── Testing ─────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=synthera --cov-report=html --cov-report=term-missing

# ─── Code Quality ────────────────────────────────────────
lint:
	ruff check synthera/ tests/ frontend/
	mypy synthera/

format:
	ruff format synthera/ tests/ frontend/
	ruff check --fix synthera/ tests/ frontend/

# ─── Docker ──────────────────────────────────────────────
docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down -v

# ─── Cleanup ─────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf chroma_db/ htmlcov/ .coverage dist/ build/ *.egg-info
	@echo "Cleaned up."

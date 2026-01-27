.PHONY: help run test test-cov lint format clean migrations agent docker-build docker-run

help:
	@echo "AFFILI-AI Backend - Available Commands"
	@echo "======================================"
	@echo "make run              - Start development server"
	@echo "make test             - Run all tests"
	@echo "make test-cov         - Run tests with coverage"
	@echo "make lint             - Lint code with flake8"
	@echo "make format           - Format code with black"
	@echo "make clean            - Remove cache and build files"
	@echo "make migrations       - Show database migration status"
	@echo "make agent            - Run local agent"
	@echo "make docker-build     - Build Docker backend image"
	@echo "make docker-run       - Run Docker backend container"
	@echo "make help             - Show this help message"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app tests --max-line-length=100

format:
	black app tests --line-length=100

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info

migrations:
	@echo "Database migration file: migrations/001_create_tables.sql"
	@echo "Apply to Supabase: Copy SQL to SQL Editor and execute"
	@echo "Apply to local PostgreSQL: psql -U postgres -d affili_ai_db -f migrations/001_create_tables.sql"

agent:
	cd agent && python main.py

docker-build:
	docker build -t affili-ai-backend .

docker-run:
	docker run -p 8000:8000 \
	-e DATABASE_URL=postgresql://user:password@localhost:5432/affili_ai \
	-e SECRET_KEY=your-secret-key \
	-e ENCRYPTION_KEY=your-32-byte-key \
	affili-ai-backend

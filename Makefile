.PHONY: help dev prod test clean install lint format docker-build docker-up docker-down migrate test-backend test-frontend

# Default target
.DEFAULT_GOAL := help

# Colors for output
YELLOW := \033[1;33m
GREEN := \033[1;32m
RESET := \033[0m

help: ## Show this help message
	@echo "$(YELLOW)AURORA_LIFE - Development Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# ============================================================================
# Development
# ============================================================================

install: ## Install all dependencies
	@echo "$(YELLOW)Installing backend dependencies...$(RESET)"
	cd backend && pip install -r requirements.txt -r requirements-dev.txt
	@echo "$(YELLOW)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install
	@echo "$(GREEN)✓ All dependencies installed$(RESET)"

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up

dev-build: ## Build and start development environment
	docker-compose -f docker-compose.dev.yml up --build

dev-down: ## Stop development environment
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Show development logs
	docker-compose -f docker-compose.dev.yml logs -f

# ============================================================================
# Testing
# ============================================================================

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	@echo "$(YELLOW)Running backend tests...$(RESET)"
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

test-backend-unit: ## Run backend unit tests only
	cd backend && pytest tests/unit/ -v

test-backend-integration: ## Run backend integration tests only
	cd backend && pytest tests/integration/ -v

test-frontend: ## Run frontend tests
	@echo "$(YELLOW)Running frontend tests...$(RESET)"
	cd frontend && npm test -- --passWithNoTests

test-e2e: ## Run E2E tests
	@echo "$(YELLOW)Running E2E tests...$(RESET)"
	cd backend && pytest tests/e2e/ -v

test-coverage: ## Generate test coverage report
	cd backend && pytest tests/ --cov=app --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in backend/htmlcov/$(RESET)"

# ============================================================================
# Code Quality
# ============================================================================

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code
	@echo "$(YELLOW)Linting backend...$(RESET)"
	cd backend && black --check app tests
	cd backend && isort --check app tests
	cd backend && flake8 app tests
	cd backend && mypy app
	cd backend && bandit -r app

lint-frontend: ## Lint frontend code
	@echo "$(YELLOW)Linting frontend...$(RESET)"
	cd frontend && npm run lint
	cd frontend && npm run type-check

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code
	@echo "$(YELLOW)Formatting backend...$(RESET)"
	cd backend && black app tests
	cd backend && isort app tests
	@echo "$(GREEN)✓ Backend formatted$(RESET)"

format-frontend: ## Format frontend code
	@echo "$(YELLOW)Formatting frontend...$(RESET)"
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}"
	@echo "$(GREEN)✓ Frontend formatted$(RESET)"

# ============================================================================
# Database
# ============================================================================

migrate: ## Run database migrations
	@echo "$(YELLOW)Running database migrations...$(RESET)"
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration
	@echo "$(YELLOW)Creating new migration...$(RESET)"
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "$(YELLOW)Resetting database...$(RESET)"
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.dev.yml up -d postgres redis
	@sleep 5
	$(MAKE) migrate
	@echo "$(GREEN)✓ Database reset complete$(RESET)"

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build all Docker images
	docker-compose -f docker-compose.dev.yml build

docker-build-prod: ## Build production Docker images
	docker build -t aurora-life-backend:prod ./backend
	docker build -t aurora-life-frontend:prod --build-arg NEXT_PUBLIC_API_URL=https://api.auroralife.app ./frontend

docker-up: ## Start all services
	docker-compose -f docker-compose.dev.yml up -d

docker-down: ## Stop all services
	docker-compose -f docker-compose.dev.yml down

docker-logs: ## Show Docker logs
	docker-compose -f docker-compose.dev.yml logs -f

docker-ps: ## Show running containers
	docker-compose -f docker-compose.dev.yml ps

docker-clean: ## Remove all containers, volumes, and images
	docker-compose -f docker-compose.dev.yml down -v --rmi all

# ============================================================================
# Production
# ============================================================================

prod: ## Start production environment (requires .env file)
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

# ============================================================================
# Utilities
# ============================================================================

clean: ## Clean all generated files
	@echo "$(YELLOW)Cleaning...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf frontend/.next frontend/node_modules/.cache 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(RESET)"

shell-backend: ## Open backend shell
	docker-compose -f docker-compose.dev.yml exec backend bash

shell-db: ## Open database shell
	docker-compose -f docker-compose.dev.yml exec postgres psql -U aurora -d aurora_life

pre-commit-install: ## Install pre-commit hooks
	@echo "$(YELLOW)Installing pre-commit hooks...$(RESET)"
	cd backend && pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(RESET)"

pre-commit-run: ## Run pre-commit on all files
	cd backend && pre-commit run --all-files

health-check: ## Check health of all services
	@echo "$(YELLOW)Checking service health...$(RESET)"
	@curl -f http://localhost:8000/health && echo "$(GREEN)✓ Backend healthy$(RESET)" || echo "✗ Backend unhealthy"
	@curl -f http://localhost:3000 && echo "$(GREEN)✓ Frontend healthy$(RESET)" || echo "✗ Frontend unhealthy"

ci-local: ## Run CI checks locally
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) docker-build
	@echo "$(GREEN)✓ All CI checks passed$(RESET)"

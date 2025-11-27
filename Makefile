# AURORA LIFE - Makefile
# Quick commands for development and deployment

.PHONY: help install up down restart logs shell test migrate seed clean build

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	@cp -n .env.example .env || true
	@cd backend && pip install -r requirements.txt
	@echo "✅ Done!"

up: ## Start all services
	@echo "🚀 Starting AURORA LIFE..."
	docker-compose up -d
	@echo "✅ Services started!"

down: ## Stop all services
	docker-compose down

restart: ## Restart services
	docker-compose restart

logs: ## Show all logs
	docker-compose logs -f

migrate: ## Run migrations
	docker-compose exec backend alembic upgrade head

seed: ## Seed database
	docker-compose exec backend python -m app.db.seed_gamification

test: ## Run tests
	docker-compose exec backend pytest tests/ -v

shell: ## Backend shell
	docker-compose exec backend /bin/bash

clean: ## Cleanup
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

quickstart: ## Quick start
	@cp -n .env.example .env || true
	@make build
	@make up
	@sleep 10
	@make migrate
	@make seed
	@echo "✨ Ready! Visit http://localhost:8000/docs"

build: ## Build images
	docker-compose build

status: ## Service status
	docker-compose ps

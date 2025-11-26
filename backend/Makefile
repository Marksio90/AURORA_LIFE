.PHONY: help install test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run all linters"
	@echo "  make format     - Format code with black and isort"
	@echo "  make clean      - Remove cache and temp files"
	@echo "  make hooks      - Install pre-commit hooks"
	@echo "  make run        - Run the application"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-hooks:
	pre-commit install
	@echo "Pre-commit hooks installed!"

test:
	pytest --cov=app --cov-report=html --cov-report=term

test-fast:
	pytest -x --ff

lint:
	black --check app tests
	isort --check app tests
	flake8 app tests
	mypy app
	bandit -r app

format:
	black app tests
	isort app tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov .coverage

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

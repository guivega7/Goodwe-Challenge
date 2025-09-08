# SolarMind - Makefile for common development tasks

.PHONY: help install install-dev run test lint format clean db-init db-upgrade security docs

help:  ## Show this help message
	@echo "SolarMind - Solar Energy Management System"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

run:  ## Run the development server
	python app.py

run-prod:  ## Run with gunicorn (production)
	gunicorn -w 4 -b 0.0.0.0:8000 app:app

test:  ## Run tests
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-quick:  ## Run tests without coverage
	pytest tests/ -v

lint:  ## Run linting checks
	flake8 . --max-line-length=100 --extend-ignore=E203,W503
	mypy . --ignore-missing-imports
	bandit -r . -ll -x tests/

format:  ## Format code with black and isort
	black .
	isort . --profile black

format-check:  ## Check code formatting
	black --check .
	isort --check-only --profile black .

clean:  ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build

db-init:  ## Initialize database
	python init_db.py

db-upgrade:  ## Upgrade database schema
	flask db upgrade

security:  ## Run security checks
	bandit -r . -ll
	safety check
	pip-audit

docs:  ## Build documentation
	cd docs && make html

docs-serve:  ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8080

docker-build:  ## Build Docker image
	docker build -t solarmind .

docker-run:  ## Run Docker container
	docker run -p 5000:5000 --env-file .env solarmind

pre-commit:  ## Run pre-commit hooks
	pre-commit run --all-files

setup:  ## Set up complete development environment
	python -m venv venv
	. venv/bin/activate && make install-dev
	cp .env.example .env
	make db-init
	@echo "Setup complete! Don't forget to edit .env with your configuration"

check:  ## Run all checks (lint, test, security)
	make lint
	make test
	make security

deploy-check:  ## Pre-deployment checks
	make format-check
	make check
	@echo "Ready for deployment!"

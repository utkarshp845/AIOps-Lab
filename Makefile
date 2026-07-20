COMPOSE ?= docker compose
PYTHON ?= python

.PHONY: up down logs build test lint generate-traffic analyze-logs evaluate-assistant validate format

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f demo-service ai-sre-assistant

build:
	$(COMPOSE) build demo-service ai-sre-assistant

test: build
	$(COMPOSE) run --rm --no-deps demo-service pytest -q
	$(COMPOSE) run --rm --no-deps ai-sre-assistant pytest -q

lint: build
	$(COMPOSE) run --rm --no-deps demo-service ruff check app tests
	$(COMPOSE) run --rm --no-deps ai-sre-assistant ruff check app cli tests

generate-traffic:
	$(PYTHON) scripts/generate-demo-traffic.py --base-url http://localhost:8000

analyze-logs:
	$(COMPOSE) run --rm --no-deps ai-sre-assistant python cli/sre.py analyze --max-lines 120

evaluate-assistant: build
	$(COMPOSE) run --rm --no-deps ai-sre-assistant python -m evals.run_evals

validate: test lint evaluate-assistant
	@echo "Production-readiness validation passed."

format:
	$(COMPOSE) run --rm --no-deps demo-service ruff format app tests
	$(COMPOSE) run --rm --no-deps ai-sre-assistant ruff format app cli tests


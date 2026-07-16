COMPOSE ?= docker compose
PYTHON ?= python

.PHONY: up down logs test lint generate-traffic analyze-logs evaluate-assistant format

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f demo-service ai-sre-assistant

test:
	$(COMPOSE) build demo-service ai-sre-assistant
	$(COMPOSE) run --rm --no-deps demo-service pytest -q
	$(COMPOSE) run --rm --no-deps ai-sre-assistant pytest -q

lint:
	$(COMPOSE) run --rm --no-deps demo-service ruff check app tests
	$(COMPOSE) run --rm --no-deps ai-sre-assistant ruff check app cli tests

generate-traffic:
	$(PYTHON) scripts/generate-demo-traffic.py --base-url http://localhost:8000

analyze-logs:
	$(COMPOSE) run --rm --no-deps ai-sre-assistant python cli/sre.py analyze --max-lines 120

evaluate-assistant:
	$(COMPOSE) build ai-sre-assistant
	$(COMPOSE) run --rm --no-deps ai-sre-assistant python -m evals.run_evals

format:
	$(COMPOSE) run --rm --no-deps demo-service ruff format app tests
	$(COMPOSE) run --rm --no-deps ai-sre-assistant ruff format app cli tests


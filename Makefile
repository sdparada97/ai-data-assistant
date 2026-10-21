SHELL := /bin/bash

# uv avisa si VIRTUAL_ENV apunta a otro entorno (p. ej. pyenv); se ignora aquí.
unexport VIRTUAL_ENV

UV_RUN := uv run --all-packages --frozen
DEFAULT_FILTER := not llm
LLM_FILTER := llm

.PHONY: help test test-llm eval up

help: ## Lista los objetivos disponibles
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "%-10s %s\n", $$1, $$2}'

test: ## Pruebas sin LLM, red ni credenciales
	$(UV_RUN) pytest -m "$(DEFAULT_FILTER)"

test-llm: ## Solo pruebas marcadas @pytest.mark.llm (requieren red y credenciales)
	@$(UV_RUN) pytest -m "$(LLM_FILTER)"; rc=$$?; \
	if [ $$rc -eq 5 ]; then echo "No hay pruebas llm"; exit 0; fi; exit $$rc

eval: ## Evaluación con el golden set (pendiente)
	@echo "Evaluación no disponible: pendiente del change add-evaluation-suite" >&2; exit 1

up: ## Levanta backend y frontend con Docker Compose
	docker compose up --build

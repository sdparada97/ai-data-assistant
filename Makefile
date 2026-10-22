SHELL := /bin/bash

# uv avisa si VIRTUAL_ENV apunta a otro entorno (p. ej. pyenv); se ignora aquí.
unexport VIRTUAL_ENV

UV_RUN := uv run --all-packages --frozen

# Rutas por defecto de la ingesta (sobrescribibles desde el entorno). No viven en el código.
SALES_CSV_PATH ?= data/raw/02_Ventas_2026.csv
DUCKDB_PATH ?= data/processed/analytics.duckdb
SEMANTIC_LAYER_PATH ?= backend/config/semantic_layer.yaml
DATA_QUALITY_PATH ?= backend/config/data_quality.yaml
DEFAULT_FILTER := not llm
LLM_FILTER := llm

.PHONY: help test test-llm eval up ingest

help: ## Lista los objetivos disponibles
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "%-10s %s\n", $$1, $$2}'

test: ## Pruebas sin LLM, red ni credenciales
	$(UV_RUN) pytest -m "$(DEFAULT_FILTER)"

test-llm: ## Solo pruebas marcadas @pytest.mark.llm (requieren red y credenciales)
	@$(UV_RUN) pytest -m "$(LLM_FILTER)"; rc=$$?; \
	if [ $$rc -eq 5 ]; then echo "No hay pruebas llm"; exit 0; fi; exit $$rc

eval: ## Evaluación con el golden set (pendiente)
	@echo "Evaluación no disponible: pendiente del change add-evaluation-suite" >&2; exit 1

ingest: ## Carga el CSV de ventas en DuckDB aplicando las reglas de calidad
	@SALES_CSV_PATH="$(SALES_CSV_PATH)" DUCKDB_PATH="$(DUCKDB_PATH)" \
	SEMANTIC_LAYER_PATH="$(SEMANTIC_LAYER_PATH)" DATA_QUALITY_PATH="$(DATA_QUALITY_PATH)" \
	$(UV_RUN) python -m analyst_backend.ingestion

up: ## Levanta backend y frontend con Docker Compose
	docker compose up --build

SHELL := /bin/bash

# uv avisa si VIRTUAL_ENV apunta a otro entorno (p. ej. pyenv); se ignora aquí.
unexport VIRTUAL_ENV

UV_RUN := uv run --all-packages --frozen

# Rutas por defecto de la ingesta (sobrescribibles desde el entorno). No viven en el código.
SALES_CSV_PATH ?= data/raw/02_Ventas_2026.csv
DUCKDB_PATH ?= data/processed/analytics.duckdb
SEMANTIC_LAYER_PATH ?= backend/config/semantic_layer.yaml
DATA_QUALITY_PATH ?= backend/config/data_quality.yaml
# Documentos y modelo de embeddings.
DOCUMENTS_DIR ?= data/raw
DOCUMENTS_DB_PATH ?= data/processed/documents.duckdb
DOCUMENTS_CONFIG_PATH ?= backend/config/documents.yaml
MODELS_CACHE_DIR ?= .cache/models
# Agente de consulta.
AGENT_CONFIG_PATH ?= backend/config/agent.yaml
# Variables del LLM (make ask, make test-llm): se cargan de ENV_FILE solo si existe, sin mostrarlas.
ENV_FILE ?= .env
ENV_LOAD = $(if $(wildcard $(ENV_FILE)),--env-file $(ENV_FILE))
# Rutas de las pruebas llm (por defecto, las de pyproject.toml).
LLM_TESTS ?=
# Datos del host que make up monta en el backend (solo lectura). Las bases deben llamarse
# analytics.duckdb y documents.duckdb, los nombres por defecto de make ingest y make ingest-docs.
DOCKER_DATA_DIR ?= data/processed
DOCKER_MODELS_DIR ?= $(MODELS_CACHE_DIR)
DEFAULT_FILTER := not llm and not embeddings
LLM_FILTER := llm
EMBEDDINGS_FILTER := embeddings

.PHONY: help test test-llm test-embeddings eval up up-check ingest ingest-docs models ask

help: ## Lista los objetivos disponibles
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "%-16s %s\n", $$1, $$2}'

test: ## Pruebas sin LLM, modelo de embeddings, red ni credenciales
	$(UV_RUN) pytest -m "$(DEFAULT_FILTER)"

test-llm: ## Solo pruebas marcadas @pytest.mark.llm (requieren red y credenciales en ENV_FILE)
	@$(UV_RUN) $(ENV_LOAD) pytest -m "$(LLM_FILTER)" $(LLM_TESTS); rc=$$?; \
	if [ $$rc -eq 5 ]; then echo "No hay pruebas llm"; exit 0; fi; exit $$rc

models: ## Descarga el modelo de embeddings en MODELS_CACHE_DIR y comprueba su huella
	@MODELS_CACHE_DIR="$(MODELS_CACHE_DIR)" DOCUMENTS_CONFIG_PATH="$(DOCUMENTS_CONFIG_PATH)" \
	$(UV_RUN) python -m analyst_backend.documents.models_cli

test-embeddings: ## Solo pruebas marcadas @pytest.mark.embeddings, con el modelo real y sin red (requiere make models)
	@MODELS_CACHE_DIR="$(MODELS_CACHE_DIR)" DOCUMENTS_CONFIG_PATH="$(DOCUMENTS_CONFIG_PATH)" \
	$(UV_RUN) python -m analyst_backend.documents.models_cli --check
	MODELS_CACHE_DIR="$(MODELS_CACHE_DIR)" $(UV_RUN) pytest -m "$(EMBEDDINGS_FILTER)"

eval: ## Evaluación con el golden set (pendiente)
	@echo "Evaluación no disponible: pendiente del change add-evaluation-suite" >&2; exit 1

ingest: ## Carga el CSV de ventas en DuckDB aplicando las reglas de calidad
	@SALES_CSV_PATH="$(SALES_CSV_PATH)" DUCKDB_PATH="$(DUCKDB_PATH)" \
	SEMANTIC_LAYER_PATH="$(SEMANTIC_LAYER_PATH)" DATA_QUALITY_PATH="$(DATA_QUALITY_PATH)" \
	$(UV_RUN) python -m analyst_backend.ingestion

ingest-docs: ## Convierte y fragmenta los documentos y publica su base con embeddings (requiere make models)
	@DOCUMENTS_DIR="$(DOCUMENTS_DIR)" DOCUMENTS_DB_PATH="$(DOCUMENTS_DB_PATH)" \
	DOCUMENTS_CONFIG_PATH="$(DOCUMENTS_CONFIG_PATH)" MODELS_CACHE_DIR="$(MODELS_CACHE_DIR)" \
	$(UV_RUN) python -m analyst_backend.documents

ask: ## Responde una pregunta: make ask Q="<pregunta>" (requiere make ingest, make ingest-docs y Gemini en ENV_FILE)
	@AGENT_CONFIG_PATH="$(AGENT_CONFIG_PATH)" DUCKDB_PATH="$(DUCKDB_PATH)" SEMANTIC_LAYER_PATH="$(SEMANTIC_LAYER_PATH)" \
	DOCUMENTS_DB_PATH="$(DOCUMENTS_DB_PATH)" DOCUMENTS_CONFIG_PATH="$(DOCUMENTS_CONFIG_PATH)" \
	MODELS_CACHE_DIR="$(MODELS_CACHE_DIR)" $(UV_RUN) $(ENV_LOAD) python -m analyst_backend.agent

up-check: ## Comprueba las bases y el modelo que necesita make up
	@test -f "$(DOCKER_DATA_DIR)/analytics.duckdb" || \
		{ echo "Falta la base de ventas en $(DOCKER_DATA_DIR)/analytics.duckdb: ejecuta make ingest." >&2; exit 1; }
	@test -f "$(DOCKER_DATA_DIR)/documents.duckdb" || \
		{ echo "Falta la base de documentos en $(DOCKER_DATA_DIR)/documents.duckdb: ejecuta make ingest-docs." >&2; exit 1; }
	@MODELS_CACHE_DIR="$(DOCKER_MODELS_DIR)" DOCUMENTS_CONFIG_PATH="$(DOCUMENTS_CONFIG_PATH)" \
	$(UV_RUN) python -m analyst_backend.documents.models_cli --check

up: up-check ## Levanta backend (:8000) y frontend (:8501) en 127.0.0.1 con los datos del host
	DOCKER_DATA_DIR="$(abspath $(DOCKER_DATA_DIR))" DOCKER_MODELS_DIR="$(abspath $(DOCKER_MODELS_DIR))" \
	docker compose up --build

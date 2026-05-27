# ABOUTME: Per-session make targets for the MLOps workshop monorepo.
# ABOUTME: All Python targets run inside the project venv; nothing touches Agentic_DevOps/.
.DEFAULT_GOAL := help

VENV       ?= .venv
PY         ?= $(VENV)/bin/python
PIP        ?= uv pip install --python $(PY)
S2         := MLOps_Deployment_Workshop/Session_2_Shadow_Deployment
MODELS     := $(S2)/models

.PHONY: help install validate validate-session-2 test test-session-2 clean \
        train-models-session-2 package-models-session-2

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

install: ## Create the venv (Python 3.12) and install dev dependencies
	uv venv --python 3.12 $(VENV)
	$(PIP) --group dev

validate: ## Run the full local validation chain (delegates per session)
	bash scripts/validate-local.sh

validate-session-2: ## Run Session 2 validation only
	bash $(S2)/scripts/validate-session-2.sh

test: ## Run all session tests with coverage
	$(PY) -m pytest --cov=MLOps_Deployment_Workshop

test-session-2: ## Run Session 2 tests with coverage
	$(PY) -m pytest $(S2)/tests --cov=$(S2)

train-models-session-2: ## Train champion and challenger models
	$(PY) $(MODELS)/train_champion.py
	$(PY) $(MODELS)/train_challenger.py

package-models-session-2: ## Package both models into SageMaker tar.gz artifacts
	$(PY) $(MODELS)/package_model.py --input $(MODELS)/model-v1.0.0.joblib --output $(MODELS)/model-v1.0.0.tar.gz
	$(PY) $(MODELS)/package_model.py --input $(MODELS)/model-v1.0.1.joblib --output $(MODELS)/model-v1.0.1.tar.gz

clean: ## Remove caches and generated artifacts
	find . -path ./.venv -prune -o -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov
	rm -f $(MODELS)/*.joblib $(MODELS)/*.tar.gz

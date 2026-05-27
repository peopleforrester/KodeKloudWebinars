# ABOUTME: Entry points for the NFCU Session 4 KServe collateral — validation and the
# ABOUTME: local/EKS cluster, predictor build, and rehearsal lifecycle targets.

SHELL := /bin/bash
ROOT  := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help
.PHONY: help validate bootstrap-local teardown-local eks-up eks-down \
        build-predictor run-rehearsal clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

## ----------------------------------------------------------------------------
## Validation — the local test harness. Skips tools that are not installed
## rather than failing, so it runs anywhere; CI installs the full set.
## ----------------------------------------------------------------------------
validate: ## Run all static checks (yaml, markdown, terraform, manifests, scripts, python)
	@bash scripts/validate.sh

## ----------------------------------------------------------------------------
## Local kind cluster
## ----------------------------------------------------------------------------
bootstrap-local: ## Create the kind cluster and install all add-ons
	@bash cluster/local/up.sh

teardown-local: ## Destroy the kind cluster and its Docker artifacts
	@bash cluster/local/down.sh

## ----------------------------------------------------------------------------
## EKS demo cluster (speaker's own AWS account)
## ----------------------------------------------------------------------------
eks-up: ## terraform apply the EKS cluster, then bootstrap add-ons
	@bash cluster/eks/up.sh

eks-down: ## terraform destroy the EKS cluster (safety-gated)
	@bash cluster/eks/down.sh

## ----------------------------------------------------------------------------
## Predictor image
## ----------------------------------------------------------------------------
build-predictor: ## Build the multi-arch TinyLlama predictor image
	@bash predictors/tinyllama/build.sh

## ----------------------------------------------------------------------------
## Rehearsal
## ----------------------------------------------------------------------------
run-rehearsal: ## Full end-to-end rehearsal on the local kind cluster
	@bash rehearsal/run-full-session-local.sh

## ----------------------------------------------------------------------------
## Housekeeping
## ----------------------------------------------------------------------------
clean: ## Remove generated model artifacts and local result dumps
	@rm -rf manifests/model-artifacts/model-v*/ manifests/model-artifacts/*.bst
	@find . -name '*.k6-summary.json' -delete
	@echo "Cleaned generated artifacts."

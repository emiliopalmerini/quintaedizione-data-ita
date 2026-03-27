SHELL := /bin/sh

RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: help test quality format vet clean parse-srd pdf-convert

.DEFAULT_GOAL := help

test: format vet
	@echo -e "$(BLUE)Running tests...$(NC)"
	go test -race -v ./...
	@echo -e "$(GREEN)Tests passed!$(NC)"

quality:
	@echo -e "$(BLUE)Running data quality checks...$(NC)"
	go test -tags=quality -race -v -run TestDataQuality ./store/
	@echo -e "$(GREEN)Quality checks completed!$(NC)"

format:
	@echo -e "$(BLUE)Formatting Go code...$(NC)"
	go fmt ./...
	@echo -e "$(GREEN)Code formatted!$(NC)"

vet:
	@echo -e "$(BLUE)Running vet...$(NC)"
	go vet ./...
	@echo -e "$(GREEN)Vet passed!$(NC)"

clean:
	@echo -e "$(BLUE)Cleaning build artifacts...$(NC)"
	go clean
	@echo -e "$(GREEN)Cleanup completed!$(NC)"

parse-srd:
	@if [ -z "$(PDF)" ]; then \
		echo -e "$(RED)Error: PDF argument required. Usage: make parse-srd PDF=path/to/file.pdf$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Building parser image...$(NC)"
	docker build -f Dockerfile.Parser -t srd-parser .
	@echo -e "$(BLUE)Running SRD parser...$(NC)"
	docker run --rm \
		-v $(CURDIR)/data/srd:/app/output \
		-v $(abspath $(PDF)):/app/input.pdf:ro \
		srd-parser /app/input.pdf --output-dir /app/output
	@echo -e "$(GREEN)SRD parsing completed!$(NC)"

pdf-convert:
	@if [ -z "$(PDF)" ]; then \
		echo -e "$(RED)Error: PDF argument required. Usage: make pdf-convert PDF=path/to/file.pdf$(NC)"; \
		exit 1; \
	fi
	@command -v uv >/dev/null 2>&1 || (echo -e "$(RED)Error: uv is not installed. Visit https://docs.astral.sh/uv/$(NC)" && exit 1)
	@echo -e "$(BLUE)Running PDF conversion...$(NC)"
	uv run scripts/pdf-to-markdown.py $(PDF)
	@echo -e "$(GREEN)PDF conversion completed!$(NC)"

help:
	@echo -e "$(BLUE) quintaedizione-data-ita - Available Commands:$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Go Development:$(NC)"
	@echo "  make test       # Format, vet, and run tests with race detector"
	@echo "  make format     # Format Go code"
	@echo "  make vet        # Run go vet"
	@echo "  make quality    # Run data quality checks (double spaces, orphan markdown, etc.)"
	@echo "  make clean      # Clean build artifacts"
	@echo ""
	@echo -e "$(YELLOW)Data Pipeline:$(NC)"
	@echo "  make parse-srd PDF=<path>   # Parse SRD PDF into JSON (via Docker)"
	@echo "  make pdf-convert PDF=<path> # Convert PDF to per-collection markdown files"

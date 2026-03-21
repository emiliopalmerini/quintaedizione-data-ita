SHELL := /bin/sh

RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: help test format vet clean

.DEFAULT_GOAL := help

test: format vet
	@echo -e "$(BLUE)Running tests...$(NC)"
	go test -race -v ./...
	@echo -e "$(GREEN)Tests passed!$(NC)"

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

help:
	@echo -e "$(BLUE) quintaedizione-data-ita - Available Commands:$(NC)"
	@echo ""
	@echo "  make test       # Format, vet, and run tests with race detector"
	@echo "  make format     # Format Go code"
	@echo "  make vet        # Run go vet"
	@echo "  make clean      # Clean build artifacts"

# GRC Fix Monitor Makefile

.PHONY: help install install-dev test test-unit test-bdd test-coverage lint format clean run

# Default target
help:
	@echo "Available commands:"
	@echo "  install        Install the package"
	@echo "  install-dev    Install package with development dependencies"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-bdd       Run BDD tests only"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  lint           Run code linting"
	@echo "  format         Format code with black"
	@echo "  clean          Clean up build artifacts"
	@echo "  run            Run the tool with default settings"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e .[dev]

# Testing
test:
	pytest -v

test-unit:
	pytest -v -m unit

test-coverage:
	pytest --cov=grc_fix_monitor --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 grc_fix_monitor.py test_*.py
	mypy grc_fix_monitor.py

format:
	black grc_fix_monitor.py test_*.py

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete

# Run the tool
run:
	python grc_fixes_monitor/grc_fixes.py -d -o grc_fixes.tsv
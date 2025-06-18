# GRC Fix Monitor Makefile

.PHONY: help test lint format clean run

# Default target
help:
	@echo "Available commands:"
	@echo "  test           Run all tests"
	@echo "  lint           Run code linting"
	@echo "  format         Format code with black"
	@echo "  clean          Clean up build artifacts"
	@echo "  run            Run the tool with default settings"

# Testing
test:
	pytest -v

# Code quality
lint:
	flake8 grc_fixes_monitor/grc_fixes.py tests/test_*.py
	mypy grc_fixes_monitor/grc_fixes.py

format:
	black grc_fixes_monitor/grc_fixes.py tests/test_*.py

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
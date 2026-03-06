# GRC Fix Monitor Makefile

.PHONY: help test lint format clean run download_issues_mapping_data

# Default target
help:
	@echo "Available commands:"
	@echo "  test                          Run all tests"
	@echo "  lint                          Run code linting"
	@echo "  format                        Format code with black"
	@echo "  clean                         Clean up build artifacts"
	@echo "  run                           Run the tool with default settings"
	@echo "  download_issues_mapping_data  Download issue mapping data"
# Testing
test:
	uv run pytest -v

# Code quality
lint:
	uv run flake8 grc_fixes_monitor/grc_fixes.py tests/test_*.py
	uv run mypy grc_fixes_monitor/grc_fixes.py

format:
	uv run black grc_fixes_monitor/grc_fixes.py tests/test_*.py

download_issues_mapping_data:
	@echo "Downloading issue mapping data..."
	@DATE=$$(date +%F); DIR=data/$$DATE; \
	rm -rf "$$DIR" && mkdir -p "$$DIR" && \
	wget -qc -O "$$DIR/patch_type" https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_assembly_structure/PATCHES/alt_scaffolds/patch_type && \
	wget -qc -O "$$DIR/alt_scaffold_placement.txt" https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_assembly_structure/PATCHES/alt_scaffolds/alt_scaffold_placement.txt && \
	for chr in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 X Y NA Un; do \
		wget -qc -O "$$DIR/chr$${chr}_issues.xml" "https://ftp.ncbi.nlm.nih.gov/pub/grc/human/GRC/Issue_Mapping/chr$${chr}_issues.xml" || exit 1; \
	done && \
	echo "Download complete in $$DIR."

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
	uv run python -m grc_fixes_monitor.parse_grc_fixes -d data/2026-03-06 -o output/grc_fixes.tsv
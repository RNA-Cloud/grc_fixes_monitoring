# Tests Overview

This document describes the test suite for the `grc_fixes_monitor` package, including the test structure, coverage, fixtures, and how to run the tests.

---

## Running the Tests

```bash
# Run all tests (via Makefile)
make test

# Run all tests directly with uv
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_parse_grc_fixes.py -v

# Run a specific test by name
uv run pytest tests/test_patch_type_parser.py::TestPatchTypeParser::test_get_fix_patches_filters_only_fix -v
```

The test runner is configured in `pytest.ini` at the project root.

---

## Configuration

**`pytest.ini`** settings:

| Setting | Value | Description |
|---------|-------|-------------|
| `testpaths` | `tests` | Directory searched for test files |
| `python_files` | `test_*.py` | File name pattern for test discovery |
| Output | Verbose with short tracebacks | Default output format |
| Warnings | Filtered to errors | Unhandled warnings are treated as test failures |

**Markers** (used to categorise tests):

| Marker | Purpose |
|--------|---------|
| `unit` | Tests a single function or class in isolation |
| `integration` | Tests interactions between multiple components |
| `slow` | Tests that take a long time to complete |
| `network` | Tests that require network access |

---

## Directory Structure

```
tests/
├── conftest.py                         # Shared pytest fixtures
├── test_parse_grc_fixes.py             # Tests for the main orchestrator
├── test_grc_issues_parser.py           # Tests for the GRC issues XML parser
├── test_patch_type_parser.py           # Tests for the patch type parser
├── test_scaffold_placement_parser.py   # Tests for the scaffold placement parser
└── data/                               # Static fixture data
    ├── patch_type                      # Sample patch type records
    ├── alt_scaffold_placement.txt      # Sample scaffold placements
    ├── chr1_issues.xml                 # Sample issues for chromosome 1
    └── chr2_issues.xml                 # Sample issues for chromosome 2
```

---

## Fixtures (`conftest.py`)

Fixtures are defined in `tests/conftest.py` and are available to all test files.

| Fixture | Scope | Description |
|---------|-------|-------------|
| `project_root_path` | `session` | Absolute `Path` to the repository root |
| `tests_data_dir` | `session` | Absolute `Path` to `tests/data/` |
| `data_file` | `session` | Callable `(file_name: str) -> Path`; resolves a file in `tests/data/` and raises `FileNotFoundError` if it does not exist |
| `patch_type_file` | function | `Path` to `tests/data/patch_type` |
| `alt_scaffold_placement_file` | function | `Path` to `tests/data/alt_scaffold_placement.txt` |
| `chr1_issues_file` | function | `Path` to `tests/data/chr1_issues.xml` |
| `chr2_issues_file` | function | `Path` to `tests/data/chr2_issues.xml` |
| `copied_test_data_dir` | function | `Path` to a temporary copy of `tests/data/`; used for integration tests that require a mutable data directory |

---

## Test Files

### `test_parse_grc_fixes.py`

Tests the top-level orchestration functions in `grc_fixes_monitor/parse_grc_fixes.py`.

| Test | Description |
|------|-------------|
| `test_check_data_files_accepts_valid_input` | Confirms `check_data_files()` succeeds when all required files are present |
| `test_check_data_files_logs_when_chr_xml_missing` | Confirms an error is logged when no `chr*.xml` files are found |
| `test_check_data_files_raises_when_alt_scaffold_placement_missing` | Confirms `FileNotFoundError` is raised when `alt_scaffold_placement.txt` is absent |
| `test_check_data_files_raises_when_patch_type_missing` | Confirms `FileNotFoundError` is raised when `patch_type` is absent |
| `test_write_output_writes_tab_delimited_rows` | Confirms `write_output()` produces a valid tab-delimited file with the correct header and data |
| `test_main_generates_expected_output_file` | Integration test; runs `main()` end-to-end against the fixture data and asserts 15 output rows, all with `scaffold_type == "FIX"`, including a specific known row |
| `test_main_exits_when_issue_is_missing` | Confirms `main()` raises `ValueError` when a scaffold's issue ID cannot be found in the XML data |

---

### `test_grc_issues_parser.py`

Tests `grc_fixes_monitor/parsers/grc_issues.py`.

#### `TestGRCIssuesParser` class

| Test | Description |
|------|-------------|
| `test_from_file_parses_issues_and_locations` | Parses `chr1_issues.xml` and verifies the issue count, a known issue's metadata, and its `Position` and `Quality` data |
| `test_get_returns_none_for_unknown_key` | Confirms `get()` returns `None` for a key that does not exist |
| `test_from_file_raises_for_missing_file` | Confirms `FileNotFoundError` is raised for a non-existent file |
| `test_from_file_raises_for_invalid_xml` | Confirms `ValueError` is raised for malformed XML |
| `test_from_directory_parses_and_merges_files` | Parses both `chr1_issues.xml` and `chr2_issues.xml` from the fixture directory and verifies the merged issue count |
| `test_from_directory_raises_for_non_directory` | Confirms `NotADirectoryError` is raised when the path is a file |
| `test_from_directory_raises_for_duplicate_keys` | Confirms `ValueError` is raised when the same XML file is provided twice, producing duplicate issue keys |

#### Module-level tests

| Test | Description |
|------|-------------|
| `test_build_index_raises_for_duplicate_key` | Confirms `_build_index()` raises `ValueError` when the same issue is supplied twice |
| `test_build_index_raises_for_missing_key` | Confirms `_build_index()` raises `ValueError` when an issue has no `<key>` element |
| `test_parse_position_handles_missing_map_sequence_and_quality` | Confirms `_parse_position()` sets optional fields to `None` when `<mapSequence>` and `<quality>` are absent |
| `test_parse_quality_parses_versions_and_methods` | Confirms `_parse_quality()` correctly parses `<version_mapped>` elements and method accessions |

---

### `test_patch_type_parser.py`

Tests `grc_fixes_monitor/parsers/patch_type.py`.

#### `TestPatchTypeParser` class

| Test | Description |
|------|-------------|
| `test_from_file_parses_expected_rows` | Parses the fixture `patch_type` file and verifies the row count and the first record's fields |
| `test_init_stores_patch_types` | Confirms `PatchTypeParser.__init__()` stores the provided list unchanged |
| `test_get_fix_patches_filters_only_fix` | Confirms only records with `patch_type == "FIX"` are returned |
| `test_get_fix_patches_empty_for_empty_input` | Confirms an empty list is returned when no patch records are provided |
| `test_from_file_raises_for_missing_file` | Confirms `FileNotFoundError` is raised for a non-existent file |
| `test_from_file_raises_for_missing_expected_column` | Confirms `ValueError` is raised when a required column is absent from the header |

---

### `test_scaffold_placement_parser.py`

Tests `grc_fixes_monitor/parsers/scaffoled_placement.py`.

#### `TestScaffoldPlacementParser` class

| Test | Description |
|------|-------------|
| `test_from_file_parses_expected_rows` | Parses the fixture `alt_scaffold_placement.txt` and verifies the row count and first record's numeric and string fields |
| `test_scaffold_placements_property_returns_stored_value` | Confirms the `scaffold_placements` property returns the list supplied to `__init__()` |
| `test_from_file_raises_for_missing_file` | Confirms `FileNotFoundError` is raised for a non-existent file |
| `test_from_file_raises_for_missing_expected_column` | Confirms `ValueError` is raised when a required column is absent from the header |

#### Module-level tests

| Test | Description |
|------|-------------|
| `test_extract_keys_returns_hg_issue_ids` | Confirms `_extract_keys()` returns `["HG-2231", "HG-2496"]` for `"HG2231_HG2496_PATCH"` and an empty list for a name with no `HG` numbers |
| `test_to_per_issue_scaffold_placements_expands_multi_issue_name` | Confirms a two-issue scaffold name produces two dictionary entries both pointing to the same `ScaffoldPlacement` object |
| `test_to_per_issue_scaffold_placements_overwrites_duplicate_keys` | Confirms that when two scaffolds share an issue ID, the later scaffold's placement overwrites the earlier one |

---

## Test Data

Static fixture files in `tests/data/` are kept small and representative:

| File | Contents |
|------|----------|
| `patch_type` | 21 rows covering both `FIX` and `NOVEL` patch types, including multi-issue patch names |
| `alt_scaffold_placement.txt` | 39 rows with a mix of single-issue and multi-issue scaffold names |
| `chr1_issues.xml` | 241 issues assigned to chromosome 1, including `HG-1001` with full location and quality metadata |
| `chr2_issues.xml` | 158 issues assigned to chromosome 2 |

Combined, the two XML fixture files contain 399 unique issues, which is sufficient to exercise the directory-level merging logic in `GRCIssuesParser.from_directory()`.

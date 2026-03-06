# Workflow Technical Documentation

This document describes the technical design and implementation of the `grc_fixes_monitor` package, which processes NCBI/GRC genome assembly patch data into a consolidated TSV output file.

---

## Package Structure

```
grc_fixes_monitor/
├── __init__.py
├── parse_grc_fixes.py          # Main orchestration script and CLI entry point
└── parsers/
    ├── __init__.py
    ├── grc_issues.py           # XML parser for GRC issue metadata
    ├── patch_type.py           # Tab-delimited parser for patch type classification
    └── scaffoled_placement.py  # Tab-delimited parser for scaffold placement coordinates
```

---

## Data Flow

The pipeline joins three input sources to produce a single flat TSV:

```
patch_type  ──────────────────► Filter FIX patches
                                        │
alt_scaffold_placement.txt  ──► Filter placements for FIX scaffolds
                                        │
                                Extract per-issue placements (via HG regex)
                                        │
chr*_issues.xml (×26)  ──────► Parse and index all GRC issues
                                        │
                                Join placements ↔ issues
                                        │
                                        ▼
                               grc_fixes.tsv (22 columns)
```

---

## Module Reference

### `parse_grc_fixes.py` — Main Orchestrator

This is the top-level script that coordinates all parsers, performs the join, and writes the output file.

#### `OutputRecord` dataclass

An immutable dataclass representing a single row in the output TSV. All 22 fields are described in the [Output Schema](#output-schema) section below.

#### `check_data_files(data_folder: Path)`

Validates that all required input files are present in `data_folder`:
- Logs an error if no `chr*.xml` files are found.
- Raises `FileNotFoundError` if `alt_scaffold_placement.txt` is missing.
- Raises `FileNotFoundError` if `patch_type` is missing.

#### `write_output(records: list[OutputRecord], output_file: Path)`

Writes the list of `OutputRecord` instances to a tab-delimited file with a header row derived from the dataclass field names.

#### `main()`

CLI entry point. Accepts the following arguments:

| Flag | Description | Required | Default |
|------|-------------|----------|---------|
| `-d` / `--data-folder` | Path to the snapshot data directory | Yes | — |
| `-o` / `--output-file` | Path to the output TSV file | No | `grc_fixes.csv` |
| `-v` / `--verbose` | Enable `DEBUG`-level logging | No | `INFO` level |

**Example usage:**

```bash
uv run python -m grc_fixes_monitor.parse_grc_fixes \
  -d data/2026-03-06 \
  -o output/grc_fixes.tsv \
  --verbose
```

Or via the Makefile:

```bash
make run SNAPSHOT_DATE=2026-03-06
```

---

### `parsers/patch_type.py` — Patch Type Parser

Reads and filters the `patch_type` tab-delimited file.

#### `PatchType` dataclass

| Field | Type | Description |
|-------|------|-------------|
| `alt_scaf_name` | `str` | Name of the alternate scaffold patch |
| `alt_scaf_acc` | `str` | GenBank accession for the scaffold |
| `patch_type` | `str` | Classification: `FIX` or `NOVEL` |

#### `PatchTypeParser` class

| Method | Description |
|--------|-------------|
| `from_file(patch_type_file: Path)` | Class method; reads and parses the file, returns a `PatchTypeParser` instance |
| `patch_types` | Property returning all parsed `PatchType` records |
| `get_fix_patches()` | Returns only the records where `patch_type == "FIX"` |

**Error handling:**
- Raises `FileNotFoundError` if the file does not exist.
- Raises `ValueError` if an expected column is missing from the header.

---

### `parsers/scaffoled_placement.py` — Scaffold Placement Parser

Reads the `alt_scaffold_placement.txt` tab-delimited file and expands multi-issue scaffold names into per-issue mappings.

#### `ScaffoldPlacement` dataclass

| Field | Type | Description |
|-------|------|-------------|
| `alt_asm_name` | `str` | Assembly name for the alternate scaffold set |
| `prim_asm_name` | `str` | Assembly name for the primary sequence |
| `alt_scaf_name` | `str` | Name of the alternate scaffold patch |
| `alt_scaf_acc` | `str` | GenBank accession for the alternate scaffold |
| `parent_type` | `str` | Type of parent sequence (e.g. `CHROMOSOME`) |
| `parent_name` | `str` | Parent chromosome or sequence name (e.g. `1`, `X`) |
| `parent_acc` | `str` | GenBank accession for the parent sequence |
| `region_name` | `str` | Genomic region name |
| `ori` | `str` | Strand orientation (`+` or `-`) |
| `alt_scaf_start` | `int` | Start coordinate on the alternate scaffold |
| `alt_scaf_stop` | `int` | Stop coordinate on the alternate scaffold |
| `parent_start` | `int` | Start coordinate on the parent sequence |
| `parent_stop` | `int` | Stop coordinate on the parent sequence |
| `alt_start_tail` | `int` | Unaligned bases at the scaffold start |
| `alt_stop_tail` | `int` | Unaligned bases at the scaffold end |

#### `ScaffoldPlacementParser` class

| Method | Description |
|--------|-------------|
| `from_file(placement_file: Path)` | Class method; reads and parses the file, returns a `ScaffoldPlacementParser` instance |
| `scaffold_placements` | Property returning all parsed `ScaffoldPlacement` records |

**Error handling:**
- Raises `FileNotFoundError` if the file does not exist.
- Raises `ValueError` if an expected column is missing from the header.

#### `to_per_issue_scaffold_placements(placements: list[ScaffoldPlacement]) -> dict[str, ScaffoldPlacement]`

A module-level function that expands a list of `ScaffoldPlacement` records into a dictionary keyed by GRC issue ID.

Some patch names encode multiple issues — for example, `HG1342_HG2282_PATCH` addresses both `HG-1342` and `HG-2282`. This function uses the regular expression `HG(\d+)` to extract all issue numbers from each scaffold name and creates a separate entry for each, all pointing to the same `ScaffoldPlacement`.

If the same issue ID appears in more than one scaffold, the later entry overwrites the earlier one and a debug log message is emitted.

**Example:**

```python
# "HG2231_HG2496_PATCH" expands to two entries:
{
    "HG-2231": ScaffoldPlacement(alt_scaf_name="HG2231_HG2496_PATCH", ...),
    "HG-2496": ScaffoldPlacement(alt_scaf_name="HG2231_HG2496_PATCH", ...),
}
```

---

### `parsers/grc_issues.py` — GRC Issues XML Parser

Parses GRC issue XML files and provides a lookup interface by issue ID.

#### `Issue` dataclass

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Issue classification (e.g. `Missing sequence`, `Path Problem`) |
| `key` | `str` | Unique issue ID in the format `HG-NNNN` |
| `assigned_chr` | `str` | Chromosome to which the issue is assigned |
| `accession1` | `str` | Primary GenBank accession |
| `accession2` | `str` | Secondary GenBank accession |
| `report_type` | `str` | Reporting category |
| `summary` | `str` | Short description |
| `status` | `str` | Current status (e.g. `Resolved`) |
| `status_text` | `str` | Descriptive status text |
| `description` | `str` | Detailed problem description |
| `experiment_type` | `str` | Experimental method |
| `external_info_type` | `str` | External information classification |
| `update` | `str` | ISO 8601 timestamp of the last update |
| `resolution` | `str` | Resolution code |
| `resolution_text` | `str` | Detailed resolution description |
| `affect_version` | `str` | First affected assembly version |
| `fix_version` | `str` | Assembly version(s) where the fix was applied |
| `locations` | `tuple[Position, ...]` | Genomic positions for the issue |

#### `Position` dataclass

Represents a genomic mapping of an issue to a specific assembly and sequence.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Assembly name (e.g. `GRCh38.p14`) |
| `gb_asm_acc` | `str` | GenBank assembly accession |
| `ref_asm_acc` | `str` | RefSeq assembly accession |
| `asm_status` | `str` | Assembly status (e.g. `latest`) |
| `map_status` | `str` | Mapping status (e.g. `MAPPED`) |
| `map_sequence` | `str` | Sequence identifier for the mapping |
| `map_seq_gb_acc` | `str` | GenBank accession for the mapping sequence |
| `map_seq_ref_acc` | `str` | RefSeq accession for the mapping sequence |
| `map_seq_type` | `str` | Sequence type (e.g. `CHROMOSOME`) |
| `start` | `str` | Start coordinate |
| `stop` | `str` | Stop coordinate |
| `quality` | `Quality \| None` | Quality metadata, if present |

#### `Quality` dataclass

Holds mapping quality metadata.

| Field | Type | Description |
|-------|------|-------------|
| `versions_mapped` | `tuple[VersionMapped, ...]` | Assembly versions to which this position has been mapped |
| `method_acc1` | `str` | Primary mapping method accession |
| `method_acc2` | `str` | Secondary mapping method accession |

#### `GRCIssuesParser` class

| Method | Description |
|--------|-------------|
| `from_file(xml_file: Path)` | Class method; parses a single `chr*_issues.xml` file |
| `from_directory(data_dir: Path)` | Class method; parses all `*.xml` files in a directory and merges them into one parser |
| `get(key: str)` | Returns the `Issue` for the given key, or `None` if not found |
| `__len__()` | Returns the number of issues in the index |
| `__contains__(key: str)` | Returns `True` if the key exists in the index |

**Error handling:**
- Raises `FileNotFoundError` if an XML file does not exist.
- Raises `ValueError` for malformed XML.
- Raises `NotADirectoryError` if the path passed to `from_directory` is not a directory.
- Raises `ValueError` if duplicate issue keys are detected across files or within a single file.
- Raises `ValueError` if an issue element has no `<key>` element.

---

## Processing Pipeline

The following steps are performed by `main()` in order:

1. **Validate inputs** — `check_data_files()` confirms that all three required file types are present.

2. **Parse patch types** — `PatchTypeParser.from_file()` reads `patch_type` and `get_fix_patches()` filters to only `FIX` patches.

3. **Parse scaffold placements** — `ScaffoldPlacementParser.from_file()` reads all rows from `alt_scaffold_placement.txt`.

4. **Filter placements** — Only placements whose `alt_scaf_name` matches a known FIX patch name are retained.

5. **Expand to per-issue placements** — `to_per_issue_scaffold_placements()` extracts issue IDs from scaffold names using the `HG(\d+)` pattern, producing one mapping entry per issue ID.

6. **Parse GRC issues** — `GRCIssuesParser.from_directory()` reads all 26 `chr*_issues.xml` files and merges them into a single index.

7. **Join** — For each issue ID in the per-issue placement dictionary, the corresponding `Issue` is looked up. If any issue ID is missing from the XML index, a `ValueError` is raised immediately.

8. **Write output** — `write_output()` serialises all `OutputRecord` instances to a tab-delimited TSV file.

---

## Output Schema

The output file is a tab-delimited TSV with the following 22 columns:

| Column | Source | Description |
|--------|--------|-------------|
| `issue_id` | `Issue.key` | GRC issue ID (e.g. `HG-1342`) |
| `type` | `Issue.type` | Issue classification |
| `status` | `Issue.status` | Current issue status |
| `last_updated` | `Issue.update` | Timestamp of the last update |
| `affects_version` | `Issue.affect_version` | Assembly version first affected |
| `fix_version` | `Issue.fix_version` | Assembly version(s) where the fix was applied |
| `summary` | `Issue.summary` | Short issue description |
| `description` | `Issue.description` | Detailed issue description |
| `experiment_type` | `Issue.experiment_type` | Experimental method |
| `report_type` | `Issue.report_type` | Reporting category |
| `resolution` | `Issue.resolution` | Resolution code |
| `resolution_text` | `Issue.resolution_text` | Detailed resolution text |
| `scaffold_type` | Hardcoded `"FIX"` | Patch type (always `FIX` in this output) |
| `alt_scaf_name` | `ScaffoldPlacement.alt_scaf_name` | Alternate scaffold name |
| `parent_type` | `ScaffoldPlacement.parent_type` | Parent sequence type |
| `parent_name` | `ScaffoldPlacement.parent_name` | Parent chromosome or sequence name |
| `parent_acc` | `ScaffoldPlacement.parent_acc` | Parent sequence GenBank accession |
| `parent_start` | `ScaffoldPlacement.parent_start` | Start coordinate on parent |
| `parent_stop` | `ScaffoldPlacement.parent_stop` | Stop coordinate on parent |
| `ori` | `ScaffoldPlacement.ori` | Strand orientation |
| `alt_scaf_acc` | `ScaffoldPlacement.alt_scaf_acc` | Alternate scaffold GenBank accession |
| `alt_scaf_start` | `ScaffoldPlacement.alt_scaf_start` | Start coordinate on alternate scaffold |
| `alt_scaf_stop` | `ScaffoldPlacement.alt_scaf_stop` | Stop coordinate on alternate scaffold |

---

## Logging

The tool uses Python's standard `logging` module throughout. All loggers are named after their respective module (e.g. `grc_fixes_monitor.parse_grc_fixes`).

| Level | When used |
|-------|-----------|
| `INFO` | Major steps: file discovery, record counts, file writes |
| `DEBUG` | Detailed per-record events: key extraction, skipped entries, index merging |
| `ERROR` | Missing files, invalid XML, duplicate issue keys, missing issue lookups |

Logging is configured in `main()`. Pass `-v` / `--verbose` to enable `DEBUG`-level output; the default level is `INFO`.

---

## Error Handling Summary

| Condition | Behaviour |
|-----------|-----------|
| Missing `alt_scaffold_placement.txt` | `FileNotFoundError` raised from `check_data_files()` |
| Missing `patch_type` | `FileNotFoundError` raised from `check_data_files()` |
| No `chr*.xml` files found | Error logged; processing continues |
| XML file not found | `FileNotFoundError` raised from `GRCIssuesParser.from_file()` |
| Malformed XML | `ValueError` raised from `GRCIssuesParser.from_file()` |
| Duplicate issue keys across XML files | `ValueError` raised from `GRCIssuesParser.from_directory()` |
| Issue ID from scaffold not found in XML | `ValueError` raised from `main()` |
| Missing column in `patch_type` | `ValueError` raised from `PatchTypeParser.from_file()` |
| Missing column in `alt_scaffold_placement.txt` | `ValueError` raised from `ScaffoldPlacementParser.from_file()` |

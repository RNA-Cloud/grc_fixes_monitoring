# Data Sources

This document describes the data files downloaded to the `data/` directory, including their origins, formats, and key fields.

## Overview

Data is downloaded from two NCBI FTP endpoints and organised into date-stamped snapshot directories under `data/YYYY-MM-DD/`. Each snapshot contains three types of files:

| File | Source | Format |
|------|--------|--------|
| `patch_type` | NCBI Assembly FTP | Tab-delimited |
| `alt_scaffold_placement.txt` | NCBI Assembly FTP | Tab-delimited |
| `chr*_issues.xml` | NCBI GRC Issue Mapping FTP | XML |

---

## Downloading Data

Use the Makefile target to download a fresh snapshot for a given date:

```bash
make download_issues_mapping_data SNAPSHOT_DATE=YYYY-MM-DD
```

This removes any existing snapshot directory for that date, recreates it, and downloads all required files. The snapshot date is written to `.issues_mapping_date` and used as the default for subsequent `make run` invocations.

---

## File Descriptions

### `patch_type`

**Download URL:**
```
https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_assembly_structure/PATCHES/alt_scaffolds/patch_type
```

**Format:** Tab-delimited text file with a header row.

**Purpose:** Lists all alternate scaffold patches in the GRCh38.p14 assembly, each annotated with its patch type. The workflow uses this file to identify which scaffolds are genuine fix patches (`FIX`) versus novel alternate loci (`NOVEL`).

**Columns:**

| Column | Description |
|--------|-------------|
| `#alt_scaf_name` | Name of the alternate scaffold patch (e.g. `HG1342_HG2282_PATCH`) |
| `alt_scaf_acc` | GenBank accession for the alternate scaffold (e.g. `KQ031383.1`) |
| `patch_type` | Patch classification: `FIX` (corrects an error in the primary assembly) or `NOVEL` (adds sequence not represented in the primary assembly) |

**Example rows:**
```
#alt_scaf_name	alt_scaf_acc	patch_type
HG1342_HG2282_PATCH	KQ031383.1	FIX
HSCHR1_5_CTG3	KN196472.1	NOVEL
```

---

### `alt_scaffold_placement.txt`

**Download URL:**
```
https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_assembly_structure/PATCHES/alt_scaffolds/alt_scaffold_placement.txt
```

**Format:** Tab-delimited text file with a header row.

**Purpose:** Provides genomic coordinates for each alternate scaffold, describing where the scaffold is placed relative to its parent chromosome or unlocalized sequence. The workflow joins these coordinates with issue metadata to produce the final output.

**Columns:**

| Column | Description |
|--------|-------------|
| `#alt_asm_name` | Assembly name for the alternate scaffold set (e.g. `PATCHES`) |
| `prim_asm_name` | Assembly name for the primary sequence (e.g. `Primary Assembly`) |
| `alt_scaf_name` | Name of the alternate scaffold patch |
| `alt_scaf_acc` | GenBank accession for the alternate scaffold |
| `parent_type` | Type of the parent sequence (e.g. `CHROMOSOME`, `UNLOCALIZED`) |
| `parent_name` | Name of the parent chromosome or sequence (e.g. `1`, `X`) |
| `parent_acc` | GenBank accession for the parent sequence (e.g. `CM000663.2`) |
| `region_name` | Name of the genomic region |
| `ori` | Orientation of the scaffold on the parent: `+` (plus strand) or `-` (minus strand) |
| `alt_scaf_start` | Start coordinate on the alternate scaffold (1-based) |
| `alt_scaf_stop` | Stop coordinate on the alternate scaffold (1-based) |
| `parent_start` | Start coordinate on the parent sequence (1-based) |
| `parent_stop` | Stop coordinate on the parent sequence (1-based) |
| `alt_start_tail` | Unaligned sequence length at the start of the scaffold |
| `alt_stop_tail` | Unaligned sequence length at the end of the scaffold |

**Example row:**
```
#alt_asm_name	prim_asm_name	alt_scaf_name	alt_scaf_acc	parent_type	parent_name	parent_acc	region_name	ori	alt_scaf_start	alt_scaf_stop	parent_start	parent_stop	alt_start_tail	alt_stop_tail
PATCHES	Primary Assembly	HG1342_HG2282_PATCH	KQ031383.1	CHROMOSOME	1	CM000663.2	REGION_1	+	1	494316	12818488	13312803	0	0
```

---

### `chr*_issues.xml`

**Download URL pattern:**
```
https://ftp.ncbi.nlm.nih.gov/pub/grc/human/GRC/Issue_Mapping/chr{CHR}_issues.xml
```

where `{CHR}` is one of: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `22`, `X`, `Y`, `NA`, `Un`.

This results in 26 XML files downloaded per snapshot.

**Format:** XML with a `<GenomeIssues>` root element containing `<issue>` child elements.

**Purpose:** Provides detailed metadata for each GRC issue, including type, status, resolution, summary, and version information. The workflow parses all 26 files and merges them into a single index keyed by issue ID (e.g. `HG-1342`).

**Key XML elements per `<issue>`:**

| Element | Description |
|---------|-------------|
| `<type>` | Issue classification (e.g. `Missing sequence`, `Path Problem`, `Gap`) |
| `<key>` | Unique issue identifier in the format `HG-NNNN` (e.g. `HG-1342`) |
| `<assignedChr>` | Chromosome to which the issue is assigned |
| `<accession1>` / `<accession2>` | GenBank accessions associated with the issue |
| `<reportType>` | Reporting category (e.g. `RefSeq Report`) |
| `<summary>` | Short description of the issue |
| `<status>` | Current status (e.g. `Resolved`) |
| `<description>` | Detailed description of the problem |
| `<experiment_type>` | Experimental method used (e.g. `Clone Sequencing`) |
| `<update>` | Date and time of the last update |
| `<resolution>` | Resolution code (e.g. `GRC Resolved by Electronic Means`) |
| `<resolution_text>` | Detailed resolution description |
| `<affectVersion>` | Assembly version first affected (e.g. `GRCh37`) |
| `<fixVersion>` | Assembly version(s) in which the fix was applied (e.g. `GRCh37.p11,GRCh38`) |
| `<location><position>` | Genomic positions mapping the issue to specific assembly coordinates |

**Example XML fragment:**
```xml
<GenomeIssues>
  <issue>
    <type>Missing sequence</type>
    <key>HG-1001</key>
    <assignedChr>1</assignedChr>
    <summary>Gap in chromosome 1</summary>
    <status>Resolved</status>
    <affectVersion>GRCh37</affectVersion>
    <fixVersion>GRCh37.p11,GRCh38</fixVersion>
    <resolution>GRC Resolved by Electronic Means</resolution>
    <location>
      <position name="GRCh38.p14" gb_asm_acc="GCA_000001405.29" ref_asm_acc="GCF_000001405.40" asm_status="latest">
        <mapStatus>MAPPED</mapStatus>
        <start>1000</start>
        <stop>2000</stop>
      </position>
    </location>
  </issue>
</GenomeIssues>
```

---

## Directory Structure

After downloading a snapshot, the `data/` directory has the following structure:

```
data/
└── YYYY-MM-DD/
    ├── patch_type
    ├── alt_scaffold_placement.txt
    ├── chr1_issues.xml
    ├── chr2_issues.xml
    ├── ...
    ├── chr22_issues.xml
    ├── chrX_issues.xml
    ├── chrY_issues.xml
    ├── chrNA_issues.xml
    └── chrUn_issues.xml
```

Multiple snapshots can coexist under `data/`. The active snapshot is determined by the `.issues_mapping_date` file at the project root, or by passing `SNAPSHOT_DATE=YYYY-MM-DD` to `make`.

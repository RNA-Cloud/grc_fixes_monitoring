from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path

import pytest

from grc_fixes_monitor.parse_grc_fixes import (
    OutputRecord,
    check_data_files,
    main,
    write_output,
)


def _make_output_record() -> OutputRecord:
    return OutputRecord(
        issue_id="HG-1",
        type="Missing sequence",
        status="Resolved",
        last_updated="2020-01-01T00:00:00.000-0000",
        affects_version="GRCh37",
        fix_version="GRCh38",
        summary="Example summary",
        description="Example description",
        experiment_type="Clone Sequencing",
        report_type="RefSeq Report",
        resolution="GRC Resolved by Electronic Means",
        resolution_text="Example resolution",
        scaffold_type="FIX",
        alt_scaf_name="HG1_PATCH",
        parent_type="CHROMOSOME",
        parent_name="1",
        parent_acc="CM000663.2",
        parent_start=100,
        parent_stop=200,
        ori="+",
        alt_scaf_acc="ACC1",
        alt_scaf_start=1,
        alt_scaf_stop=1000,
    )


def test_check_data_files_accepts_valid_input(copied_test_data_dir: Path) -> None:
    check_data_files(copied_test_data_dir)


def test_check_data_files_logs_when_chr_xml_missing(
    tmp_path: Path,
    patch_type_file: Path,
    alt_scaffold_placement_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "patch_type").write_text(patch_type_file.read_text(encoding="utf-8"), encoding="utf-8")
    (data_dir / "alt_scaffold_placement.txt").write_text(
        alt_scaffold_placement_file.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with caplog.at_level(logging.ERROR):
        check_data_files(data_dir)

    assert "No chr*.xml files found" in caplog.text


def test_check_data_files_raises_when_alt_scaffold_placement_missing(
    tmp_path: Path,
    patch_type_file: Path,
    chr1_issues_file: Path,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "patch_type").write_text(patch_type_file.read_text(encoding="utf-8"), encoding="utf-8")
    (data_dir / "chr1_issues.xml").write_text(chr1_issues_file.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="alt_scaffold_placement.txt not found"):
        check_data_files(data_dir)


def test_check_data_files_raises_when_patch_type_missing(
    tmp_path: Path,
    alt_scaffold_placement_file: Path,
    chr1_issues_file: Path,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "alt_scaffold_placement.txt").write_text(
        alt_scaffold_placement_file.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (data_dir / "chr1_issues.xml").write_text(chr1_issues_file.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="patch_type not found"):
        check_data_files(data_dir)


def test_write_output_writes_tab_delimited_rows(tmp_path: Path) -> None:
    output_file = tmp_path / "grc_fixes.tsv"
    records = [_make_output_record()]

    write_output(records, output_file)

    with output_file.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    assert len(rows) == 1
    assert rows[0]["issue_id"] == "HG-1"
    assert rows[0]["scaffold_type"] == "FIX"
    assert rows[0]["alt_scaf_name"] == "HG1_PATCH"
    assert rows[0]["parent_start"] == "100"


def test_main_generates_expected_output_file(
    copied_test_data_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_file = tmp_path / "output.tsv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "parse_grc_fixes.py",
            "--data-folder",
            str(copied_test_data_dir),
            "--output-file",
            str(output_file),
            "--verbose",
        ],
    )

    main()

    with output_file.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    assert len(rows) == 16
    assert all(row["scaffold_type"] == "FIX" for row in rows)
    assert any(
        row["issue_id"] == "HG-1342" and row["alt_scaf_name"] == "HG1342_HG2282_PATCH"
        for row in rows
    )


def test_main_exits_when_issue_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "patch_type").write_text(
        "#alt_scaf_name\talt_scaf_acc\tpatch_type\nHG999_PATCH\tACC999\tFIX\n",
        encoding="utf-8",
    )
    (data_dir / "alt_scaffold_placement.txt").write_text(
        (
            "#alt_asm_name\tprim_asm_name\talt_scaf_name\talt_scaf_acc\tparent_type\t"
            "parent_name\tparent_acc\tregion_name\tori\talt_scaf_start\talt_scaf_stop\t"
            "parent_start\tparent_stop\talt_start_tail\talt_stop_tail\n"
            "PATCHES\tPrimary Assembly\tHG999_PATCH\tACC999\tCHROMOSOME\t1\tCM000663.2\t"
            "REGION\t+\t1\t100\t1000\t1100\t0\t0\n"
        ),
        encoding="utf-8",
    )
    (data_dir / "chr1_issues.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<GenomeIssues>
  <issue>
    <key>HG-1</key>
  </issue>
</GenomeIssues>
""",
        encoding="utf-8",
    )

    output_file = tmp_path / "output.tsv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "parse_grc_fixes.py",
            "--data-folder",
            str(data_dir),
            "--output-file",
            str(output_file),
        ],
    )

    with pytest.raises(ValueError):
        main()

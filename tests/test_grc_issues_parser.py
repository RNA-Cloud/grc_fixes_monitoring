from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from grc_fixes_monitor.parsers.grc_issues import GRCIssuesParser


class TestGRCIssuesParser:
    def test_from_file_parses_issues_and_locations(self, chr1_issues_file: Path) -> None:
        parser = GRCIssuesParser.from_file(chr1_issues_file)

        assert len(parser) == 241
        assert "HG-1001" in parser
        issue = parser.get("HG-1001")
        assert issue is not None
        assert issue.key == "HG-1001"
        assert issue.type == "Missing sequence"
        assert issue.affect_version == "GRCh37"
        assert issue.fix_version == "GRCh37.p11,GRCh38"
        assert len(issue.locations) == 3
        assert issue.locations[0].map_seq_type == "CHROMOSOME"
        assert issue.locations[0].quality.method_acc1 == "component"
        assert issue.locations[0].quality.versions_mapped[0].acc == "BX511041"

    def test_removal_of_newlines(self, chr10_issues_file: Path) -> None:
        parser = GRCIssuesParser.from_file(chr10_issues_file)

        issue = parser.get("HG-2334")
        assert issue is not None
        assert issue.description.count("\n") == 0

    def test_HG_2334(self, chr10_issues_file: Path) -> None:
        parser = GRCIssuesParser.from_file(chr10_issues_file)

        issue = parser.get("HG-2334")
        assert issue is not None
        assert issue.description == "There is an insertion of a 'T' in the reference genome between position 471-472 of NM_001304717.1 (corresponding to position 87,864,104 of NC_000010.11). All 89 transcripts at this position are lacking the 'T' (MAF for T=0.00 for rs71022512). There is also a mismatch in the genome at position 511 of NM_001304717.1 (corresponding to position 87,864,144 of NC_000010.11). The reference genome has a 'G' at this position, but all 89 transcripts have a 'C' (MAF for G=0.0000 for rs2943772)."

    def test_get_returns_none_for_unknown_key(self, chr1_issues_file: Path) -> None:
        parser = GRCIssuesParser.from_file(chr1_issues_file)

        assert parser.get("HG-999999") is None

    def test_from_file_raises_for_missing_file(self, tmp_path: Path) -> None:
        missing_file = tmp_path / "missing.xml"

        with pytest.raises(FileNotFoundError, match="XML file not found"):
            GRCIssuesParser.from_file(missing_file)

    def test_from_file_raises_for_invalid_xml(self, tmp_path: Path) -> None:
        malformed_xml = tmp_path / "invalid.xml"
        malformed_xml.write_text("<GenomeIssues><issue></GenomeIssues>", encoding="utf-8")

        with pytest.raises(ValueError, match="Failed to parse XML file"):
            GRCIssuesParser.from_file(malformed_xml)

    def test_from_directory_parses_and_merges_files(self, copied_test_data_dir: Path) -> None:
        parser = GRCIssuesParser.from_directory(copied_test_data_dir)

        assert len(parser) == 492
        assert "HG-1001" in parser
        assert "HG-1007" in parser

    def test_from_directory_raises_for_non_directory(self, tmp_path: Path) -> None:
        not_a_directory = tmp_path / "not_a_directory.xml"
        not_a_directory.write_text("<x/>", encoding="utf-8")

        with pytest.raises(NotADirectoryError, match="Not a directory"):
            GRCIssuesParser.from_directory(not_a_directory)

    def test_from_directory_raises_for_duplicate_keys(
        self,
        tmp_path: Path,
        chr1_issues_file: Path,
    ) -> None:
        duplicate_data_dir = tmp_path / "dupes"
        duplicate_data_dir.mkdir()
        (duplicate_data_dir / "chr1_a.xml").write_text(
            chr1_issues_file.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (duplicate_data_dir / "chr1_b.xml").write_text(
            chr1_issues_file.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Duplicate keys found"):
            GRCIssuesParser.from_directory(duplicate_data_dir)


def test_build_index_raises_for_duplicate_key(chr1_issues_file: Path) -> None:
    parser = GRCIssuesParser.from_file(chr1_issues_file)
    issue = parser.get("HG-1001")
    assert issue is not None

    with pytest.raises(ValueError, match="Duplicate key found: HG-1001"):
        GRCIssuesParser._build_index([issue, issue])


def test_build_index_raises_for_missing_key(chr1_issues_file: Path) -> None:
    parser = GRCIssuesParser.from_file(chr1_issues_file)
    issue = parser.get("HG-1001")
    assert issue is not None
    missing_key_issue = replace(issue, key=None)

    with pytest.raises(ValueError, match="Issue with no key encountered"):
        GRCIssuesParser._build_index([missing_key_issue])


def test_parse_position_handles_missing_map_sequence_and_quality() -> None:
    position_el = ET.fromstring(
        """
        <position name="GRCh38.p14" gb_asm_acc="GCA" ref_asm_acc="GCF" asm_status="latest">
          <mapStatus>MAPPED</mapStatus>
          <start>10</start>
          <stop>20</stop>
        </position>
        """
    )

    position = GRCIssuesParser._parse_position(position_el)

    assert position.map_sequence is None
    assert position.map_seq_gb_acc is None
    assert position.map_seq_ref_acc is None
    assert position.map_seq_type is None
    assert position.quality is None


def test_parse_quality_parses_versions_and_methods() -> None:
    quality_el = ET.fromstring(
        """
        <quality>
          <version_mapped acc="A1">1</version_mapped>
          <version_mapped acc="B2">2</version_mapped>
          <method_acc1>component</method_acc1>
          <method_acc2>alignment</method_acc2>
        </quality>
        """
    )

    quality = GRCIssuesParser._parse_quality(quality_el)

    assert quality.versions_mapped[0].acc == "A1"
    assert quality.versions_mapped[0].version == "1"
    assert quality.versions_mapped[1].acc == "B2"
    assert quality.versions_mapped[1].version == "2"
    assert quality.method_acc1 == "component"
    assert quality.method_acc2 == "alignment"

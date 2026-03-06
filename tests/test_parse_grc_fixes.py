import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from dataclasses import asdict

from grc_fixes_monitor.parsers.patch_type import PatchType, PatchTypeParser
from grc_fixes_monitor.parsers.scaffoled_placement import ScaffoldPlacementParser

class TestPatchTypeParser:

    def test_parse_reads_expected_first_row(self, patch_type_file: Path):
        parser = PatchTypeParser.from_file(patch_type_file)

        first = parser.patch_types[0]
        assert first.alt_scaf_name == "HG1342_HG2282_PATCH"
        assert first.alt_scaf_acc == "KQ031383.1"
        assert first.patch_type == "FIX"

    def test_number_of_patch_types(self, patch_type_file: Path):
        parser = PatchTypeParser.from_file(patch_type_file)

        assert len(parser.patch_types) == 21

    def test_init_accepts_patch_types_directly(self):
        patch_types = [
            PatchType("HG1342_HG2282_PATCH", "KQ031383.1", "FIX"),
            PatchType("HG1343_PATCH", "KQ031384.1", "NOVEL"),
        ]
        parser = PatchTypeParser(patch_types)

        assert parser.patch_types == patch_types

    def test_get_fix_patches_empty_when_no_fix_types(self):
        patch_types = [
            PatchType("HG1342_PATCH", "KQ031383.1", "NOVEL"),
        ]
        parser = PatchTypeParser(patch_types)

        assert parser.get_fix_patches() == []

    def test_get_fix_patches_empty_when_no_patch_types(self):
        parser = PatchTypeParser([])

        assert parser.get_fix_patches() == []

    def test_from_file_raises_on_missing_file(self, tmp_path: Path):
        missing_file = tmp_path / "nonexistent.tsv"

        with pytest.raises(FileNotFoundError, match="nonexistent.tsv"):
            PatchTypeParser.from_file(missing_file)

    def test_from_file_raises_on_missing_column(self, tmp_path: Path):
        malformed_tsv = tmp_path / "malformed.tsv"
        malformed_tsv.write_text("wrong_col\talt_scaf_acc\tpatch_type\nval1\tval2\tval3\n")

        with pytest.raises(ValueError, match="Missing expected column"):
            PatchTypeParser.from_file(malformed_tsv)

class TestScaffoldPlacementParser:

    def test_parse_reads_expected_first_row(self, alt_scaffold_placement_file: Path):
        parser = ScaffoldPlacementParser.from_file(alt_scaffold_placement_file)

        first = parser.scaffold_placements[0]
        assert first.alt_scaf_name == "HG1342_HG2282_PATCH"
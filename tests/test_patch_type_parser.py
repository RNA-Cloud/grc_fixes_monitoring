from __future__ import annotations

from pathlib import Path

import pytest

from grc_fixes_monitor.parsers.patch_type import PatchType, PatchTypeParser


class TestPatchTypeParser:
    def test_from_file_parses_expected_rows(self, patch_type_file: Path) -> None:
        parser = PatchTypeParser.from_file(patch_type_file)

        assert len(parser.patch_types) == 21
        assert parser.patch_types[0] == PatchType(
            alt_scaf_name="HG1342_HG2282_PATCH",
            alt_scaf_acc="KQ031383.1",
            patch_type="FIX",
        )

    def test_init_stores_patch_types(self) -> None:
        patch_types = [
            PatchType("HG1_PATCH", "ACC1", "FIX"),
            PatchType("HG2_PATCH", "ACC2", "NOVEL"),
        ]

        parser = PatchTypeParser(patch_types)

        assert parser.patch_types == patch_types

    def test_get_fix_patches_filters_only_fix(self) -> None:
        patch_types = [
            PatchType("HG1_PATCH", "ACC1", "NOVEL"),
            PatchType("HG2_PATCH", "ACC2", "FIX"),
            PatchType("HG3_PATCH", "ACC3", "FIX"),
        ]
        parser = PatchTypeParser(patch_types)

        fix_patches = parser.get_fix_patches()

        assert fix_patches == [
            PatchType("HG2_PATCH", "ACC2", "FIX"),
            PatchType("HG3_PATCH", "ACC3", "FIX"),
        ]

    def test_get_fix_patches_empty_for_empty_input(self) -> None:
        parser = PatchTypeParser([])

        assert parser.get_fix_patches() == []

    def test_from_file_raises_for_missing_file(self, tmp_path: Path) -> None:
        missing_file = tmp_path / "missing_patch_type.tsv"

        with pytest.raises(FileNotFoundError, match="Patch type file not found"):
            PatchTypeParser.from_file(missing_file)

    def test_from_file_raises_for_missing_expected_column(self, tmp_path: Path) -> None:
        malformed = tmp_path / "patch_type"
        malformed.write_text(
            "wrong_header\talt_scaf_acc\tpatch_type\nHG1_PATCH\tACC1\tFIX\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Missing expected column"):
            PatchTypeParser.from_file(malformed)

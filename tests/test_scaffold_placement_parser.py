from __future__ import annotations

from pathlib import Path

import pytest

from grc_fixes_monitor.parsers.scaffoled_placement import (
    ScaffoldPlacement,
    ScaffoldPlacementParser,
    _extract_keys,
    to_per_issue_scaffold_placements,
)


class TestScaffoldPlacementParser:
    def test_from_file_parses_expected_rows(self, alt_scaffold_placement_file: Path) -> None:
        parser = ScaffoldPlacementParser.from_file(alt_scaffold_placement_file)

        assert len(parser.scaffold_placements) == 39
        first = parser.scaffold_placements[0]
        assert first.alt_scaf_name == "HG1342_HG2282_PATCH"
        assert first.alt_scaf_acc == "KQ031383.1"
        assert first.parent_acc == "CM000663.2"
        assert first.parent_start == 12818488
        assert first.parent_stop == 13312803
        assert isinstance(first.alt_scaf_start, int)
        assert isinstance(first.alt_scaf_stop, int)

    def test_scaffold_placements_property_returns_stored_value(self) -> None:
        placements = [
            ScaffoldPlacement(
                alt_asm_name="PATCHES",
                prim_asm_name="Primary Assembly",
                alt_scaf_name="HG1_PATCH",
                alt_scaf_acc="ACC1",
                parent_type="CHROMOSOME",
                parent_name="1",
                parent_acc="CM000663.2",
                region_name="REGION",
                ori="+",
                alt_scaf_start=1,
                alt_scaf_stop=2,
                parent_start=3,
                parent_stop=4,
                alt_start_tail=0,
                alt_stop_tail=0,
            )
        ]

        parser = ScaffoldPlacementParser(placements)

        assert parser.scaffold_placements == placements

    def test_from_file_raises_for_missing_file(self, tmp_path: Path) -> None:
        missing_file = tmp_path / "missing_alt_scaffold_placement.txt"

        with pytest.raises(FileNotFoundError, match="Scaffold placement file not found"):
            ScaffoldPlacementParser.from_file(missing_file)

    def test_from_file_raises_for_missing_expected_column(self, tmp_path: Path) -> None:
        malformed = tmp_path / "alt_scaffold_placement.txt"
        malformed.write_text(
            "wrong_col\tprim_asm_name\nvalue\tPrimary Assembly\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Missing expected column"):
            ScaffoldPlacementParser.from_file(malformed)


def test_extract_keys_returns_hg_issue_ids() -> None:
    assert _extract_keys("HG2231_HG2496_PATCH") == ["HG-2231", "HG-2496"]
    assert _extract_keys("HSCHR1_5_CTG3") == []


def test_to_per_issue_scaffold_placements_expands_multi_issue_name(
    alt_scaffold_placement_file: Path,
) -> None:
    parser = ScaffoldPlacementParser.from_file(alt_scaffold_placement_file)
    multi_issue_placement = next(
        placement
        for placement in parser.scaffold_placements
        if placement.alt_scaf_name == "HG2231_HG2496_PATCH"
    )

    per_issue = to_per_issue_scaffold_placements([multi_issue_placement])

    assert per_issue["HG-2231"] is multi_issue_placement
    assert per_issue["HG-2496"] is multi_issue_placement
    assert len(per_issue) == 2


def test_to_per_issue_scaffold_placements_overwrites_duplicate_keys() -> None:
    first = ScaffoldPlacement(
        alt_asm_name="PATCHES",
        prim_asm_name="Primary Assembly",
        alt_scaf_name="HG100_PATCH",
        alt_scaf_acc="ACC1",
        parent_type="CHROMOSOME",
        parent_name="1",
        parent_acc="CM000663.2",
        region_name="REGION1",
        ori="+",
        alt_scaf_start=1,
        alt_scaf_stop=10,
        parent_start=100,
        parent_stop=200,
        alt_start_tail=0,
        alt_stop_tail=0,
    )
    second = ScaffoldPlacement(
        alt_asm_name="PATCHES",
        prim_asm_name="Primary Assembly",
        alt_scaf_name="HG100_HG200_PATCH",
        alt_scaf_acc="ACC2",
        parent_type="CHROMOSOME",
        parent_name="2",
        parent_acc="CM000664.2",
        region_name="REGION2",
        ori="-",
        alt_scaf_start=11,
        alt_scaf_stop=20,
        parent_start=300,
        parent_stop=400,
        alt_start_tail=0,
        alt_stop_tail=0,
    )

    per_issue = to_per_issue_scaffold_placements([first, second])

    assert per_issue["HG-100"] is second
    assert per_issue["HG-200"] is second

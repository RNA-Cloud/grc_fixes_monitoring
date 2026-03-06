from __future__ import annotations
import csv
import logging
from pathlib import Path
from dataclasses import dataclass
import re
from unittest import result

logger = logging.getLogger(__name__)

_HG_PATTERN = re.compile(r"HG(\d+)")

@dataclass
class ScaffoldPlacement:
    """Data class for scaffold placement information"""

    alt_asm_name: str
    prim_asm_name: str
    alt_scaf_name: str
    alt_scaf_acc: str
    parent_type: str
    parent_name: str
    parent_acc: str
    region_name: str
    ori: str
    alt_scaf_start: int
    alt_scaf_stop: int
    parent_start: int
    parent_stop: int
    alt_start_tail: int
    alt_stop_tail: int

class ScaffoldPlacementParser:
    """Parser for scaffold placement information"""

    _ALT_ASM_NAME_COL = "#alt_asm_name"
    _PRIM_ASM_NAME_COL = "prim_asm_name"
    _ALT_SCAF_NAME_COL = "alt_scaf_name"
    _ALT_SCAF_ACC_COL = "alt_scaf_acc"
    _PARENT_TYPE_COL = "parent_type"
    _PARENT_NAME_COL = "parent_name"
    _PARENT_ACC_COL = "parent_acc"
    _REGION_NAME_COL = "region_name"
    _ORI_COL = "ori"
    _ALT_SCAF_START_COL = "alt_scaf_start"
    _ALT_SCAF_STOP_COL = "alt_scaf_stop"
    _PARENT_START_COL = "parent_start"
    _PARENT_STOP_COL = "parent_stop"
    _ALT_START_TAIL_COL = "alt_start_tail"
    _ALT_STOP_TAIL_COL = "alt_stop_tail"

    def __init__(self, placements: list[ScaffoldPlacement]):
        self._placements = placements

    @classmethod
    def from_file(cls, placement_file: Path) -> ScaffoldPlacementParser:
        return cls(cls._parse(placement_file))
    
    @staticmethod
    def _parse(placement_file: Path) -> list[ScaffoldPlacement]:
        try:
            with placement_file.open() as f:
                reader = csv.DictReader(f, delimiter='\t')
                return [
                    ScaffoldPlacement(
                        alt_asm_name=row[ScaffoldPlacementParser._ALT_ASM_NAME_COL],
                        prim_asm_name=row[ScaffoldPlacementParser._PRIM_ASM_NAME_COL],
                        alt_scaf_name=row[ScaffoldPlacementParser._ALT_SCAF_NAME_COL],
                        alt_scaf_acc=row[ScaffoldPlacementParser._ALT_SCAF_ACC_COL],
                        parent_type=row[ScaffoldPlacementParser._PARENT_TYPE_COL],
                        parent_name=row[ScaffoldPlacementParser._PARENT_NAME_COL],
                        parent_acc=row[ScaffoldPlacementParser._PARENT_ACC_COL],
                        region_name=row[ScaffoldPlacementParser._REGION_NAME_COL],
                        ori=row[ScaffoldPlacementParser._ORI_COL],
                        alt_scaf_start=int(row[ScaffoldPlacementParser._ALT_SCAF_START_COL]),
                        alt_scaf_stop=int(row[ScaffoldPlacementParser._ALT_SCAF_STOP_COL]),
                        parent_start=int(row[ScaffoldPlacementParser._PARENT_START_COL]),
                        parent_stop=int(row[ScaffoldPlacementParser._PARENT_STOP_COL]),
                        alt_start_tail=int(row[ScaffoldPlacementParser._ALT_START_TAIL_COL]),
                        alt_stop_tail=int(row[ScaffoldPlacementParser._ALT_STOP_TAIL_COL]),
                    )
                    for row in reader
                ]
        except KeyError as e:
            raise ValueError(f"Missing expected column in scaffold placement file: {e}") from e
        except FileNotFoundError:
            raise FileNotFoundError(f"Scaffold placement file not found: {placement_file}")
        
    @property
    def scaffold_placements(self) -> list[ScaffoldPlacement]:
        return self._placements
    
def _extract_keys(alt_scaf_name: str) -> list[str]:
    return [f"HG-{m}" for m in _HG_PATTERN.findall(alt_scaf_name)]


def to_per_issue_scaffold_placements(placements: list[ScaffoldPlacement]) -> dict[str, ScaffoldPlacement]:
    """
    Expand a list of ScaffoldPlacements into GRCIssueScaffoldPlacements,
    one entry per HG key extracted from alt_scaf_name.

    e.g. HG2231_HG2496_PATCH produces two entries with keys HG-2231 and HG-2496,
    both referencing the same ScaffoldPlacement.
    """
    result = {}

    for placement in placements:
        keys = _extract_keys(placement.alt_scaf_name)
        for key in keys:
            result[key] = placement

    return result
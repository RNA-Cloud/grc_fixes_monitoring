from __future__ import annotations
import csv
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PatchType:
    """Data class for patch type information"""

    alt_scaf_name: str
    alt_scaf_acc: str
    patch_type: str

class PatchTypeParser:
    """Parser for patch type information"""

    _PATCH_TYPE_FIX = "FIX"
    _ALT_SCAF_NAME_COL = "#alt_scaf_name"
    _ALT_SCAF_ACC_COL = "alt_scaf_acc"
    _PATCH_TYPE_COL = "patch_type"

    def __init__(self, patch_types: list[PatchType]):
        self._patch_types = patch_types

    @classmethod
    def from_file(cls, patch_type_file: Path) -> PatchTypeParser:
        return cls(cls._parse(patch_type_file))

    @staticmethod
    def _parse(patch_type_file: Path) -> list[PatchType]:
        try:
            with patch_type_file.open() as f:
                reader = csv.DictReader(f, delimiter='\t')
                return [
                    PatchType(
                        alt_scaf_name=row[PatchTypeParser._ALT_SCAF_NAME_COL],
                        alt_scaf_acc=row[PatchTypeParser._ALT_SCAF_ACC_COL],
                        patch_type=row[PatchTypeParser._PATCH_TYPE_COL]
                    )
                    for row in reader
                ]
        except KeyError as e:
            raise ValueError(f"Missing expected column in patch type file: {e}") from e
        except FileNotFoundError:
            raise FileNotFoundError(f"Patch type file not found: {patch_type_file}")

    @property
    def patch_types(self) -> list[PatchType]:
        return self._patch_types
    
    def get_fix_patches(self) -> list[PatchType]:
        fix_patches = []
        for patch in self._patch_types: 
            if patch.patch_type == self._PATCH_TYPE_FIX:
                fix_patches.append(patch)
        return fix_patches
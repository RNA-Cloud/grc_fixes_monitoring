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
        logger.debug("Initialised PatchTypeParser with %d patch records", len(patch_types))

    @classmethod
    def from_file(cls, patch_type_file: Path) -> PatchTypeParser:
        logger.info("Parsing patch type file: %s", patch_type_file)
        patch_types = cls._parse(patch_type_file)
        logger.info("Parsed %d patch type records from %s", len(patch_types), patch_type_file)
        return cls(patch_types)

    @staticmethod
    def _parse(patch_type_file: Path) -> list[PatchType]:
        try:
            with patch_type_file.open(encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = [
                    PatchType(
                        alt_scaf_name=row[PatchTypeParser._ALT_SCAF_NAME_COL],
                        alt_scaf_acc=row[PatchTypeParser._ALT_SCAF_ACC_COL],
                        patch_type=row[PatchTypeParser._PATCH_TYPE_COL]
                    )
                    for row in reader
                ]
                logger.debug("Read %d rows from patch type file %s", len(rows), patch_type_file)
                return rows
        except KeyError as e:
            logger.error("Patch type file %s is missing expected column %s", patch_type_file, e)
            raise ValueError(f"Missing expected column in patch type file: {e}") from e
        except FileNotFoundError:
            logger.error("Patch type file not found: %s", patch_type_file)
            raise FileNotFoundError(f"Patch type file not found: {patch_type_file}")

    @property
    def patch_types(self) -> list[PatchType]:
        return self._patch_types
    
    def get_fix_patches(self) -> list[PatchType]:
        logger.info("Filtering patch records for patch_type=%s", self._PATCH_TYPE_FIX)
        fix_patches = []
        for patch in self._patch_types:
            if patch.patch_type == self._PATCH_TYPE_FIX:
                fix_patches.append(patch)
            else:
                logger.debug(
                    "Skipping non-FIX patch %s with type %s",
                    patch.alt_scaf_name,
                    patch.patch_type,
                )
        logger.info("Found %d FIX patches out of %d patch records", len(fix_patches), len(self._patch_types))
        return fix_patches

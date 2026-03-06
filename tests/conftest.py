from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Callable

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
TESTS_DATA_DIR = TESTS_DIR / "data"

# Ensure imports resolve from the project package.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def tests_data_dir() -> Path:
    return TESTS_DATA_DIR


@pytest.fixture(scope="session")
def data_file(tests_data_dir: Path) -> Callable[[str], Path]:
    def _resolve(file_name: str) -> Path:
        path = tests_data_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Fixture data file not found: {path}")
        return path

    return _resolve


@pytest.fixture
def patch_type_file(data_file: Callable[[str], Path]) -> Path:
    return data_file("patch_type")


@pytest.fixture
def alt_scaffold_placement_file(data_file: Callable[[str], Path]) -> Path:
    return data_file("alt_scaffold_placement.txt")


@pytest.fixture
def chr1_issues_file(data_file: Callable[[str], Path]) -> Path:
    return data_file("chr1_issues.xml")


@pytest.fixture
def chr2_issues_file(data_file: Callable[[str], Path]) -> Path:
    return data_file("chr2_issues.xml")


@pytest.fixture
def copied_test_data_dir(tmp_path: Path, tests_data_dir: Path) -> Path:
    copied_data_dir = tmp_path / "data"
    shutil.copytree(tests_data_dir, copied_data_dir)
    return copied_data_dir

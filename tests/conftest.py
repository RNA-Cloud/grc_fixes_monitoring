#!/usr/bin/env python3
"""
Pytest configuration file
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Fixture to provide project root path"""
    return Path(__file__).parent


@pytest.fixture
def temp_output_dir(tmp_path):
    """Fixture to provide temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add unit marker to all tests by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to tests that make network calls
        if 'fetch' in item.name or 'network' in item.name:
            item.add_marker(pytest.mark.slow)
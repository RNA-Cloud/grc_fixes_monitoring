#!/usr/bin/env python3
"""
Test suite for GRC Fix Monitoring Tool

This test suite provides comprehensive testing for the GRC Fix Monitoring Tool,
including mocked HTTP responses and file-based fixtures for testing.
"""

import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from dataclasses import asdict

import requests

# Import the modules to test
from grc_fixes_monitor.grc_fixes import (
    GRCFixMonitor, 
    PatchPlacement, 
    PatchType, 
    IssueInfo, 
    FinalRecord
)


class TestGRCFixMonitor:
    """Test class for GRCFixMonitor functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create a GRCFixMonitor instance for testing"""
        return GRCFixMonitor(debug=True)
    
    @pytest.fixture
    def mock_alt_scaffold_placement_data(self):
        """Mock data for alt scaffold placement"""
        with open("tests/fixtures/alt_scaffold_placement.txt", "r") as f:
            return f.read()
    
    @pytest.fixture
    def mock_patch_type_data(self):
        """Mock data for patch types"""
        with open("tests/fixtures/patch_type.txt", "r") as f:
            return f.read()
    
    @pytest.fixture
    def mock_issue_html(self):
        """Mock HTML content for issue pages"""
        def get_html(issue_id):
            try:
                with open(f"tests/fixtures/{issue_id}.html", "r") as f:
                    return f.read()
            except FileNotFoundError:
                with open(f"tests/fixtures/issue_not_found.html", "r") as f:
                    return f.read()
      
        return get_html

    @patch('requests.get')
    def test_fetch_alt_scaffold_placement(self, mock_get, monitor, mock_alt_scaffold_placement_data):
        """Test fetching and parsing alt scaffold placement data"""
        mock_response = Mock()
        mock_response.text = mock_alt_scaffold_placement_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        placements = monitor.fetch_alt_scaffold_placement()
        
        assert len(placements) == 3
        assert placements[0].alt_scaf_name == "HG1342_HG2282_PATCH"
        assert placements[0].alt_scaf_acc == "KQ031383.1"
        assert placements[0].parent_name == "1"
        assert placements[0].parent_start == 12818488
        assert placements[0].parent_stop == 13312803
                
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_fetch_patch_types(self, mock_get, monitor, mock_patch_type_data):
        """Test fetching and parsing patch type data"""
        mock_response = Mock()
        mock_response.text = mock_patch_type_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        patch_types = monitor.fetch_patch_types()
        
        assert len(patch_types) == 3
        assert patch_types[0].alt_scaf_name == "HG1342_HG2282_PATCH"
        assert patch_types[0].alt_scaf_acc == "KQ031383.1"
        assert patch_types[0].patch_type == "FIX"
        assert patch_types[1].patch_type == "NOVEL"
        assert patch_types[2].patch_type == "FIX"
        
        mock_get.assert_called_once()
    
    def test_filter_fix_patches(self, monitor):
        """Test filtering patch types for FIX patches only"""
        patch_types = [
            PatchType("HG1342_HG2282_PATCH", "KN196472.1", "FIX"),
            PatchType("HG2095_PATCH", "KN196473.1", "FIX"),
            PatchType("HG2104_PATCH", "KN196474.1", "NOVEL"),
            PatchType("HG2105_PATCH", "KN196475.1", "FIX")
        ]
        
        fix_patches = monitor.filter_fix_patches(patch_types)
        
        assert len(fix_patches) == 3
        assert "HG1342_HG2282_PATCH" in fix_patches
        assert "HG2095_PATCH" in fix_patches
        assert "HG2105_PATCH" in fix_patches
        assert "HG2104_PATCH" not in fix_patches
    
    def test_extract_issue_ids(self, monitor):
        """Test extracting issue IDs from alt scaffold names"""
        # Test single issue ID
        issue_ids = monitor.extract_issue_ids("HG2095_PATCH")
        assert issue_ids == ["HG-2095"]
        
        # Test multiple issue IDs
        issue_ids = monitor.extract_issue_ids("HG1342_HG2282_PATCH")
        assert issue_ids == ["HG-1342", "HG-2282"]
        
        # Test no issue IDs
        issue_ids = monitor.extract_issue_ids("SOME_OTHER_PATCH")
        assert issue_ids == []
    
    @patch('requests.get')
    def test_fetch_issue_info(self, mock_get, monitor, mock_issue_html):
        """Test fetching and parsing issue information from GRC website"""
        def mock_response_func(url, timeout=None):
            # Extract issue ID from URL
            issue_id = url.split('/')[-1]
            mock_response = Mock()
            mock_response.content = mock_issue_html(issue_id)
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_response_func
        
        # Test HG-2104
        issue_info = monitor.fetch_issue_info("HG-2104")
        assert issue_info.issue_id == "HG-2104"
    
    @patch('requests.get')
    def test_process_fixes_integration(self, mock_get, monitor, mock_alt_scaffold_placement_data, mock_patch_type_data, mock_issue_html):
        """Test the complete process_fixes workflow"""
        def mock_response_func(url, timeout=None):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if "alt_scaffold_placement.txt" in url:
                mock_response.text = mock_alt_scaffold_placement_data
            elif "patch_type" in url:
                mock_response.text = mock_patch_type_data
            elif "/grc/human/issues/" in url:
                issue_id = url.split('/')[-1]
                mock_response.content = mock_issue_html(issue_id)
            
            return mock_response
        
        mock_get.side_effect = mock_response_func
        
        records = monitor.process_fixes(sample=False)
        
        assert len(records) == 5

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.tsv', delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Write records to temporary TSV file using the monitor's method
            monitor.save_to_tsv(records, temp_path)
            
            # Read expected records from fixture file
            expected_path = Path("tests/fixtures/expected_final_records.tsv")

            # Compare the two files line by line
            with open(temp_path, 'r', encoding='utf-8') as temp_f, \
                 open(expected_path, 'r', encoding='utf-8') as expected_f:
                
                temp_lines = [line.strip() for line in temp_f.readlines()]
                expected_lines = [line.strip() for line in expected_f.readlines()]
                
                assert len(temp_lines) == len(expected_lines), f"Line count mismatch: {len(temp_lines)} vs {len(expected_lines)}"
                
                # Compare header
                assert temp_lines[0] == expected_lines[0], "Header mismatch"
                
                # Compare each data line
                for i in range(1, len(temp_lines)):
                    temp_fields = temp_lines[i].split('\t')
                    expected_fields = expected_lines[i].split('\t')
                    
                    assert len(temp_fields) == len(expected_fields), f"Column count mismatch in line, Expected {len(expected_fields)} but got {len(temp_fields)} in line {i+1}"
                    
                    for field in range(len(expected_fields)):
                        assert temp_fields[field] == expected_fields[field], f"Field mismatch in line {i+1}, Expected {expected_fields[field]} but got {temp_fields[field]}"
                    
        finally:
            # Clean up temporary file
            temp_path.unlink(missing_ok=True)
    
    def test_error_handling_network_failure(self, monitor):
        """Test error handling for network failures"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            
            with pytest.raises(requests.RequestException):
                monitor.fetch_alt_scaffold_placement()
    
    def test_error_handling_malformed_data(self, monitor):
        """Test error handling for malformed data"""
        malformed_data = "invalid\tdata\twith\ttoo\tfew\tcolumns"
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = malformed_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Should handle malformed data gracefully
            placements = monitor.fetch_alt_scaffold_placement()
            assert len(placements) == 0  # No valid placements parsed
    

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
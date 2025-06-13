import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import csv
import io

from grc_fixes_monitor.grc_fixes import (
    GRCFixMonitor, 
    PatchPlacement, 
    PatchType, 
    IssueInfo, 
    FinalRecord
)


@pytest.fixture
def sample_placement_data():
    """Fixture for sample placement data"""
    return """#alt_asm_name prim_asm_name alt_scaf_name alt_scaf_acc parent_type parent_name parent_acc region_name ori alt_scaf_start alt_scaf_stop parent_start parent_stop alt_start_tail alt_stop_tail
PATCHES	Primary Assembly	HG1342_HG2282_PATCH	KQ031383.1	CHROMOSOME	1	CM000663.2	PRAME_REGION_1	+	1	467143	12818488	13312803	0	0
PATCHES	Primary Assembly	HG2095_PATCH	KN538361.1	CHROMOSOME	1	CM000663.2	REGION200	+	1	305542	17157487	17460319	0	0"""


@pytest.fixture
def sample_patch_type_data():
    """Fixture for sample patch type data"""
    return """#alt_scaf_name alt_scaf_acc patch_type
HG1342_HG2282_PATCH	KQ031383.1	FIX
HSCHR1_5_CTG3	KQ983255.1	NOVEL
HG2095_PATCH	KN538361.1	FIX"""


@pytest.fixture
def sample_html_response():
    """Fixture for sample HTML response from GRC issues page"""
    return """
    <html>
        <div id="issue-summary">
            <dl id="issue_info">
                <dt>Summary:</dt>
                <dd>Correction to chromosome 1 sequence</dd>
                <dt>Description:</dt>
                <dd>This patch corrects an error in the reference sequence</dd>
                <dt>Status:</dt>
                <dd>Fixed</dd>
                <dt>Type:</dt>
                <dd>Sequence Error</dd>
                <dt>Last Updated:</dt>
                <dd>2023-01-15</dd>
                <dt>Affects Version:</dt>
                <dd>GRCh38.p13</dd>
                <dt>Fix Version:</dt>
                <dd>GRCh38.p14</dd>
                <dt>Resolution:</dt>
                <dd>Fixed</dd>
                <dt>Scaffold Type:</dt>
                <dd>Chromosome</dd>
                <dt>Comment:</dt>
                <dd>Sequence corrected based on new evidence</dd>
            </dl>
        </div>
    </html>
    """

class TestGRCFixMonitor:
    """Test cases for GRCFixMonitor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = GRCFixMonitor(debug=False)
    
    def test_init_default(self):
        """Test default initialization"""
        monitor = GRCFixMonitor()
        assert monitor.debug is False
    
    def test_init_debug(self):
        """Test debug initialization"""
        monitor = GRCFixMonitor(debug=True)
        assert monitor.debug is True
    
    @patch('requests.get')
    def test_fetch_alt_scaffold_placement_success(self, mock_get):
        """Test successful fetching of alt scaffold placement data"""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """#alt_asm_name prim_asm_name alt_scaf_name alt_scaf_acc parent_type parent_name parent_acc region_name ori alt_scaf_start alt_scaf_stop parent_start parent_stop alt_start_tail alt_stop_tail
PATCHES	Primary Assembly	HG1342_HG2282_PATCH	KQ031383.1	CHROMOSOME	1	CM000663.2	PRAME_REGION_1	+	1	467143	12818488	13312803	0	0
PATCHES	Primary Assembly	HG2095_PATCH	KN538361.1	CHROMOSOME	1	CM000663.2	REGION200	+	1	305542	17157487	17460319	0	0"""
        mock_get.return_value = mock_response
        
        placements = self.monitor.fetch_alt_scaffold_placement()
        
        assert len(placements) == 2
        assert placements[0].alt_scaf_name == "HG1342_HG2282_PATCH"
        assert placements[0].alt_scaf_acc == "KQ031383.1"
        assert placements[1].alt_scaf_name == "HG2095_PATCH"
        assert placements[1].alt_scaf_acc == "KN538361.1"
    
    @patch('requests.get')
    def test_fetch_alt_scaffold_placement_request_error(self, mock_get):
        """Test request error handling in fetch_alt_scaffold_placement"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            self.monitor.fetch_alt_scaffold_placement()
    
    @patch('requests.get')
    def test_fetch_patch_types_success(self, mock_get):
        """Test successful fetching of patch types"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """#alt_scaf_name alt_scaf_acc patch_type
HG1342_HG2282_PATCH	KQ031383.1	FIX
HSCHR1_5_CTG3	KQ983255.1	NOVEL
HG2095_PATCH	KN538361.1	FIX"""
        mock_get.return_value = mock_response
        
        patch_types = self.monitor.fetch_patch_types()
        
        assert len(patch_types) == 3
        assert patch_types[0].alt_scaf_name == "HG1342_HG2282_PATCH"
        assert patch_types[0].patch_type == "FIX"
        assert patch_types[1].patch_type == "NOVEL"
        assert patch_types[2].patch_type == "FIX"
    
    def test_filter_fix_patches(self):
        """Test filtering of FIX patches"""
        patch_types = [
            PatchType("HG1342_PATCH", "KQ031383.1", "FIX"),
            PatchType("HSCHR1_CTG3", "KQ983255.1", "NOVEL"),
            PatchType("HG2095_PATCH", "KN538361.1", "FIX"),
        ]
        
        fix_patches = self.monitor.filter_fix_patches(patch_types)
        
        assert len(fix_patches) == 2
        assert "HG1342_PATCH" in fix_patches
        assert "HG2095_PATCH" in fix_patches
        assert "HSCHR1_CTG3" not in fix_patches
    
    def test_extract_issue_ids_single(self):
        """Test extraction of single issue ID"""
        issue_ids = self.monitor.extract_issue_ids("HG2095_PATCH")
        assert issue_ids == ["HG-2095"]
    
    def test_extract_issue_ids_multiple(self):
        """Test extraction of multiple issue IDs"""
        issue_ids = self.monitor.extract_issue_ids("HG1342_HG2282_PATCH")
        assert issue_ids == ["HG-1342", "HG-2282"]
    
    def test_extract_issue_ids_none(self):
        """Test extraction with no issue IDs"""
        issue_ids = self.monitor.extract_issue_ids("HSCHR1_CTG3")
        assert issue_ids == []
    
    @patch('requests.get')
    def test_fetch_issue_info_success(self, mock_get):
        """Test successful fetching of issue information"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html>
            <div id="issue-summary">
                <dl id="issue_info">
                    <dt>Summary:</dt>
                    <dd>Test summary</dd>
                    <dt>Status:</dt>
                    <dd>Fixed</dd>
                    <dt>Type:</dt>
                    <dd>Bug</dd>
                </dl>
            </div>
        </html>
        """
        mock_get.return_value = mock_response
        
        issue_info = self.monitor.fetch_issue_info("HG-2095")
        
        assert issue_info.issue_id == "HG-2095"
        assert issue_info.summary == "Test summary"
        assert issue_info.status == "Fixed"
        assert issue_info.type == "Bug"
    
    @patch('requests.get')
    def test_fetch_issue_info_request_error(self, mock_get):
        """Test request error handling in fetch_issue_info"""
        mock_get.side_effect = Exception("Network error")
        
        # Should not raise exception, but return empty IssueInfo
        issue_info = self.monitor.fetch_issue_info("HG-2095")
        assert issue_info.issue_id == "HG-2095"
        assert issue_info.summary == ""
    
    def test_save_to_csv(self):
        """Test saving records to CSV"""
        records = [
            FinalRecord(
                alt_scaf_name="HG2095_PATCH",
                patch_type="FIX",
                parent_type="CHROMOSOME",
                parent_name="1",
                parent_acc="CM000663.2",
                parent_start=17157487,
                parent_stop=17460319,
                ori="+",
                alt_scaf_acc="KN538361.1",
                alt_scaf_start=1,
                alt_scaf_stop=305542,
                issue_id="HG-2095",
                summary="Test summary"
            )
        ]
        
        with patch('builtins.open', mock_open()) as mock_file:
            self.monitor.save_to_csv(records, Path("test.csv"))
            mock_file.assert_called_once_with(Path("test.csv"), 'w', newline='', encoding='utf-8')


class TestDataClasses:
    """Test data classes"""
    
    def test_patch_placement_creation(self):
        """Test PatchPlacement data class"""
        placement = PatchPlacement(
            alt_asm_name="PATCHES",
            prim_asm_name="Primary Assembly",
            alt_scaf_name="HG2095_PATCH",
            alt_scaf_acc="KN538361.1",
            parent_type="CHROMOSOME",
            parent_name="1",
            parent_acc="CM000663.2",
            region_name="REGION200",
            ori="+",
            alt_scaf_start=1,
            alt_scaf_stop=305542,
            parent_start=17157487,
            parent_stop=17460319,
            alt_start_tail=0,
            alt_stop_tail=0
        )
        
        assert placement.alt_scaf_name == "HG2095_PATCH"
        assert placement.parent_start == 17157487
    
    def test_patch_type_creation(self):
        """Test PatchType data class"""
        patch_type = PatchType(
            alt_scaf_name="HG2095_PATCH",
            alt_scaf_acc="KN538361.1",
            patch_type="FIX"
        )
        
        assert patch_type.alt_scaf_name == "HG2095_PATCH"
        assert patch_type.patch_type == "FIX"
    
    def test_issue_info_creation(self):
        """Test IssueInfo data class"""
        issue_info = IssueInfo(
            issue_id="HG-2095",
            summary="Test summary",
            status="Fixed"
        )
        
        assert issue_info.issue_id == "HG-2095"
        assert issue_info.summary == "Test summary"
        assert issue_info.status == "Fixed"
    
    def test_final_record_creation(self):
        """Test FinalRecord data class"""
        record = FinalRecord(
            alt_scaf_name="HG2095_PATCH",
            patch_type="FIX",
            parent_type="CHROMOSOME",
            parent_name="1",
            parent_acc="CM000663.2",
            parent_start=17157487,
            parent_stop=17460319,
            ori="+",
            alt_scaf_acc="KN538361.1",
            alt_scaf_start=1,
            alt_scaf_stop=305542,
            issue_id="HG-2095"
        )
        
        assert record.alt_scaf_name == "HG2095_PATCH"
        assert record.issue_id == "HG-2095"

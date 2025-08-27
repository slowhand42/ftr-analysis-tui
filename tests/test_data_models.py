"""
Comprehensive unit tests for core data models.
Tests follow TDD methodology and focus on essential functionality.
"""

import pytest
from datetime import datetime
from src.models.data_models import SessionState, EditRecord, ClusterInfo


class TestSessionState:
    """Test suite for SessionState model."""

    def test_session_state_creation_with_required_fields(self):
        """Test creating SessionState with only required fields."""
        session = SessionState(
            last_file="/path/to/file.xlsx",
            current_sheet="SEP25",
            current_cluster=5
        )
        
        assert session.last_file == "/path/to/file.xlsx"
        assert session.current_sheet == "SEP25"
        assert session.current_cluster == 5
        assert session.current_row == 0  # default value
        assert session.window_size == (120, 40)  # default value
        assert isinstance(session.last_modified, datetime)

    def test_session_state_creation_with_all_fields(self):
        """Test creating SessionState with all fields specified."""
        test_time = datetime(2025, 1, 15, 10, 30, 45)
        session = SessionState(
            last_file="/data/analysis.xlsx",
            current_sheet="OCT25",
            current_cluster=10,
            current_row=15,
            window_size=(100, 50),
            last_modified=test_time
        )
        
        assert session.last_file == "/data/analysis.xlsx"
        assert session.current_sheet == "OCT25"
        assert session.current_cluster == 10
        assert session.current_row == 15
        assert session.window_size == (100, 50)
        assert session.last_modified == test_time

    def test_session_state_to_dict_serialization(self):
        """Test converting SessionState to dictionary for JSON serialization."""
        test_time = datetime(2025, 1, 15, 10, 30, 45)
        session = SessionState(
            last_file="/test/file.xlsx",
            current_sheet="JAN25",
            current_cluster=3,
            current_row=7,
            window_size=(80, 30),
            last_modified=test_time
        )
        
        result = session.to_dict()
        expected = {
            'last_file': '/test/file.xlsx',
            'current_sheet': 'JAN25',
            'current_cluster': 3,
            'current_row': 7,
            'window_size': [80, 30],  # tuple converted to list
            'last_modified': test_time.isoformat()
        }
        
        assert result == expected

    def test_session_state_from_dict_deserialization(self):
        """Test creating SessionState from dictionary after JSON deserialization."""
        data = {
            'last_file': '/restored/file.xlsx',
            'current_sheet': 'FEB25',
            'current_cluster': 8,
            'current_row': 12,
            'window_size': [90, 35],
            'last_modified': '2025-01-15T10:30:45'
        }
        
        session = SessionState.from_dict(data)
        
        assert session.last_file == '/restored/file.xlsx'
        assert session.current_sheet == 'FEB25'
        assert session.current_cluster == 8
        assert session.current_row == 12
        assert session.window_size == (90, 35)  # list converted back to tuple
        assert session.last_modified == datetime.fromisoformat('2025-01-15T10:30:45')

    def test_session_state_from_dict_with_missing_optional_fields(self):
        """Test SessionState creation from dict with missing optional fields uses defaults."""
        minimal_data = {
            'last_file': '/minimal/file.xlsx',
            'current_sheet': 'MAR25',
            'current_cluster': 1
        }
        
        session = SessionState.from_dict(minimal_data)
        
        assert session.last_file == '/minimal/file.xlsx'
        assert session.current_sheet == 'MAR25'
        assert session.current_cluster == 1
        assert session.current_row == 0  # default from get()
        assert session.window_size == (120, 40)  # default from get()
        assert isinstance(session.last_modified, datetime)  # default now()


class TestEditRecord:
    """Test suite for EditRecord model."""

    def test_edit_record_creation_for_view_column(self):
        """Test creating EditRecord for VIEW column edit."""
        timestamp = datetime(2025, 1, 15, 14, 30, 0)
        edit = EditRecord(
            timestamp=timestamp,
            sheet="SEP25",
            row=10,
            column="VIEW",
            old_value=100.5,
            new_value=105.2,
            cluster_id=5
        )
        
        assert edit.timestamp == timestamp
        assert edit.sheet == "SEP25"
        assert edit.row == 10
        assert edit.column == "VIEW"
        assert edit.old_value == 100.5
        assert edit.new_value == 105.2
        assert edit.cluster_id == 5
        assert edit.cuid is None  # default

    def test_edit_record_creation_for_shortlimit_column(self):
        """Test creating EditRecord for SHORTLIMIT column edit."""
        timestamp = datetime(2025, 1, 15, 14, 35, 0)
        edit = EditRecord(
            timestamp=timestamp,
            sheet="OCT25",
            row=25,
            column="SHORTLIMIT",
            old_value=-50.0,
            new_value=-45.5,
            cluster_id=12,
            cuid="CUID_12345"
        )
        
        assert edit.timestamp == timestamp
        assert edit.sheet == "OCT25"
        assert edit.row == 25
        assert edit.column == "SHORTLIMIT"
        assert edit.old_value == -50.0
        assert edit.new_value == -45.5
        assert edit.cluster_id == 12
        assert edit.cuid == "CUID_12345"

    def test_edit_record_with_none_old_value(self):
        """Test EditRecord creation with None old_value (first edit scenario)."""
        timestamp = datetime.now()
        edit = EditRecord(
            timestamp=timestamp,
            sheet="DEC25",
            row=5,
            column="VIEW",
            old_value=None,  # First time setting this value
            new_value=75.0,
            cluster_id=3
        )
        
        assert edit.old_value is None
        assert edit.new_value == 75.0
        assert edit.cluster_id == 3

    def test_edit_record_string_representation(self):
        """Test EditRecord string representation is human-readable."""
        timestamp = datetime(2025, 1, 15, 9, 45, 30)
        edit = EditRecord(
            timestamp=timestamp,
            sheet="JUL25",
            row=8,
            column="SHORTLIMIT",
            old_value=-30.0,
            new_value=-25.5,
            cluster_id=7
        )
        
        str_repr = str(edit)
        expected = "Edit at 09:45:30: JUL25[8,SHORTLIMIT] -30.0 -> -25.5"
        assert str_repr == expected


class TestClusterInfo:
    """Test suite for ClusterInfo model."""

    def test_cluster_info_creation_minimal(self):
        """Test creating ClusterInfo with minimal required fields."""
        cluster = ClusterInfo(
            cluster_id=1,
            constraint_count=5,
            cuid_list=["CUID_001", "CUID_002", "CUID_003"]
        )
        
        assert cluster.cluster_id == 1
        assert cluster.constraint_count == 5
        assert cluster.cuid_list == ["CUID_001", "CUID_002", "CUID_003"]
        assert cluster.has_sp_value is False  # default
        assert cluster.monitor is None  # default
        assert cluster.contingency is None  # default

    def test_cluster_info_creation_with_all_fields(self):
        """Test creating ClusterInfo with all fields specified."""
        cuid_list = ["CUID_100", "CUID_101", "CUID_102", "CUID_103"]
        cluster = ClusterInfo(
            cluster_id=15,
            constraint_count=4,
            cuid_list=cuid_list,
            has_sp_value=True,
            monitor="LINE_ABC",
            contingency="OUTAGE_XYZ"
        )
        
        assert cluster.cluster_id == 15
        assert cluster.constraint_count == 4
        assert cluster.cuid_list == cuid_list
        assert cluster.has_sp_value is True
        assert cluster.monitor == "LINE_ABC"
        assert cluster.contingency == "OUTAGE_XYZ"

    def test_cluster_info_string_representation(self):
        """Test ClusterInfo string representation format."""
        cluster = ClusterInfo(
            cluster_id=42,
            constraint_count=8,
            cuid_list=["CUID_A", "CUID_B"]
        )
        
        str_repr = str(cluster)
        expected = "Cluster 42 (8 constraints)"
        assert str_repr == expected

    def test_cluster_info_empty_cuid_list(self):
        """Test ClusterInfo with empty CUID list."""
        cluster = ClusterInfo(
            cluster_id=99,
            constraint_count=0,
            cuid_list=[]
        )
        
        assert cluster.cluster_id == 99
        assert cluster.constraint_count == 0
        assert cluster.cuid_list == []
        assert len(cluster.cuid_list) == 0


# Additional validation tests that should drive future improvements
class TestDataModelValidation:
    """Test validation logic that should be implemented."""

    def test_session_state_should_validate_positive_window_dimensions(self):
        """Test that window_size should be positive dimensions (future validation)."""
        # This test currently passes but indicates validation needed
        session = SessionState(
            last_file="/test.xlsx",
            current_sheet="TEST",
            current_cluster=1,
            window_size=(-10, 20)  # Negative width should be invalid
        )
        # Current implementation allows this - validation needed
        assert session.window_size == (-10, 20)

    def test_edit_record_should_validate_column_names(self):
        """Test that EditRecord should validate column names (future validation)."""
        # This test currently passes but indicates validation needed
        edit = EditRecord(
            timestamp=datetime.now(),
            sheet="TEST",
            row=1,
            column="INVALID_COLUMN",  # Should only allow VIEW or SHORTLIMIT
            old_value=10.0,
            new_value=15.0,
            cluster_id=1
        )
        # Current implementation allows this - validation needed
        assert edit.column == "INVALID_COLUMN"
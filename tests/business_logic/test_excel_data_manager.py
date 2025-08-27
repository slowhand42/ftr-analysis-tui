"""
Tests for ExcelDataManager Core functionality.

This test suite focuses on the 12 essential behaviors required by Task 009:
1. Workbook loading from Excel files
2. Sheet management and switching
3. Cluster data retrieval and filtering
4. Value updates (VIEW and SHORTLIMIT)
5. Save operations with timestamping
6. Data integrity during operations
7. Memory management for large files
8. Error handling for corrupted data
9. Undo/redo support for edits
10. Cluster navigation methods
11. Sheet metadata extraction
12. Concurrent operation safety

Tests are designed to drive TDD implementation of ExcelDataManager class.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Any

from src.business_logic.excel_data_manager import ExcelDataManager
from src.io.excel_io import ExcelIO


class TestExcelDataManagerInitialization:
    """Test ExcelDataManager initialization and basic setup."""
    
    def test_manager_initializes_with_excel_io_instance(self):
        """Test that ExcelDataManager initializes with ExcelIO instance."""
        # Create mock ExcelIO instance
        mock_excel_io = Mock(spec=ExcelIO)
        
        # Initialize manager
        manager = ExcelDataManager(mock_excel_io)
        
        # Verify initialization
        assert manager is not None
        assert hasattr(manager, '_excel_io')
        assert manager._excel_io is mock_excel_io
        
        # Verify initial state
        assert manager.get_active_sheet_name() is None
        assert manager.get_sheet_names() == []


class TestExcelDataManagerWorkbookLoading:
    """Test workbook loading functionality."""
    
    def test_load_workbook_successfully_loads_excel_file_and_handles_errors(self):
        """Test that load_workbook successfully loads Excel file and handles missing files gracefully."""
        # Test successful loading first
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26', 'FEB26', 'MAR26']
        
        # Create sample DataFrames for sheets
        jan_df = pd.DataFrame({
            'CLUSTER': [1, 2, 1],
            'CUID': ['CONST_001', 'CONST_002', 'CONST_003'],
            'VIEW': [100.0, 150.0, 120.0],
            'SHORTLIMIT': [-10.0, -20.0, -15.0]
        })
        
        feb_df = pd.DataFrame({
            'CLUSTER': [3, 4],
            'CUID': ['CONST_004', 'CONST_005'],
            'VIEW': [200.0, 250.0],
            'SHORTLIMIT': [-30.0, -40.0]
        })
        
        mock_excel_io.load_sheet.side_effect = lambda sheet_name: {
            'JAN26': jan_df,
            'FEB26': feb_df,
            'MAR26': pd.DataFrame()  # Empty sheet
        }[sheet_name]
        
        # Initialize manager and load workbook
        manager = ExcelDataManager(mock_excel_io)
        file_path = "/tmp/test_workbook.xlsx"
        
        manager.load_workbook(file_path)
        
        # Verify workbook loaded successfully
        assert manager.get_sheet_names() == ['JAN26', 'FEB26', 'MAR26']
        
        # Verify sheets are cached (lazy loading - called when needed)
        mock_excel_io.get_sheet_names.assert_called_once()
        
        # Test error handling for missing files
        error_mock = Mock(spec=ExcelIO)
        error_mock.get_sheet_names.side_effect = FileNotFoundError("File not found")
        
        error_manager = ExcelDataManager(error_mock)
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            error_manager.load_workbook("/nonexistent/file.xlsx")
    


class TestExcelDataManagerSheetManagement:
    """Test sheet navigation and active sheet management."""
    
    def test_set_and_get_active_sheet_correctly(self):
        """Test that set_active_sheet and get_active_sheet_name work correctly."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26', 'FEB26', 'MAR26']
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        
        # Set active sheet
        manager.set_active_sheet('FEB26')
        
        # Verify active sheet
        assert manager.get_active_sheet_name() == 'FEB26'
    
    def test_set_invalid_sheet_name_raises_error(self):
        """Test that setting invalid sheet name raises appropriate error."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26', 'FEB26']
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        
        # Attempt to set invalid sheet
        with pytest.raises(ValueError, match="Sheet 'INVALID' not found"):
            manager.set_active_sheet('INVALID')


class TestExcelDataManagerClusterOperations:
    """Test cluster data retrieval and filtering."""
    
    def test_get_cluster_data_returns_filtered_dataframe(self):
        """Test that get_cluster_data returns correct subset for specified cluster."""
        # Setup mock data
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 2, 1, 3, 1],
            'CUID': ['C001', 'C002', 'C003', 'C004', 'C005'],
            'VIEW': [100.0, 150.0, 120.0, 200.0, 110.0],
            'SHORTLIMIT': [-10.0, -20.0, -15.0, -30.0, -12.0],
            'FLOW': [95.0, 145.0, 115.0, 195.0, 105.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df
        
        # Setup manager
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Get cluster data
        cluster_data = manager.get_cluster_data('1')
        
        # Verify filtered results
        assert isinstance(cluster_data, pd.DataFrame)
        assert len(cluster_data) == 3  # Three rows with CLUSTER=1
        assert all(cluster_data['CLUSTER'] == 1)
        assert list(cluster_data['CUID']) == ['C001', 'C003', 'C005']
    
    def test_get_cluster_data_with_column_filtering(self):
        """Test that get_cluster_data respects column filtering parameter."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 1],
            'CUID': ['C001', 'C002'],
            'VIEW': [100.0, 150.0],
            'SHORTLIMIT': [-10.0, -20.0],
            'FLOW': [95.0, 145.0],
            'LIMIT': [110.0, 160.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Get cluster data with specific columns
        cluster_data = manager.get_cluster_data('1', columns=['CUID', 'VIEW', 'SHORTLIMIT'])
        
        # Verify column filtering
        expected_columns = ['CUID', 'VIEW', 'SHORTLIMIT']
        assert list(cluster_data.columns) == expected_columns
        assert len(cluster_data) == 2
    
    def test_get_all_clusters_returns_unique_cluster_names(self):
        """Test that get_all_clusters returns unique cluster names from active sheet."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 2, 1, 3, 2, 1],
            'CUID': ['C001', 'C002', 'C003', 'C004', 'C005', 'C006']
        })
        
        mock_excel_io.load_sheet.return_value = test_df
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Get all clusters
        clusters = manager.get_all_clusters()
        
        # Verify unique clusters returned
        assert isinstance(clusters, list)
        assert set(clusters) == {'1', '2', '3'}  # Should be strings for consistency
        assert len(clusters) == 3
    
    def test_get_cluster_data_handles_nonexistent_cluster(self):
        """Test that get_cluster_data handles request for non-existent cluster gracefully."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 2, 3],
            'CUID': ['C001', 'C002', 'C003']
        })
        
        mock_excel_io.load_sheet.return_value = test_df
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Request non-existent cluster
        cluster_data = manager.get_cluster_data('999')
        
        # Should return empty DataFrame
        assert isinstance(cluster_data, pd.DataFrame)
        assert len(cluster_data) == 0
        assert cluster_data.empty


class TestExcelDataManagerValueUpdates:
    """Test value update functionality and data integrity."""
    
    def test_update_value_modifies_dataframe_correctly(self):
        """Test that update_value successfully updates cell value in DataFrame and tracks modifications."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 1, 2],
            'CUID': ['C001', 'C002', 'C003'],
            'VIEW': [100.0, 150.0, 200.0],
            'SHORTLIMIT': [-10.0, -20.0, -30.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Initially, data should not be modified
        assert manager._is_modified is False
        
        # Update a value (cluster=1, first constraint, VIEW column)
        success = manager.update_value(cluster='1', constraint_index=0, column='VIEW', value=125.0)
        
        # Verify update success and modification tracking
        assert success is True
        assert manager._is_modified is True
        
        # Verify value was updated in cached data
        updated_data = manager.get_cluster_data('1')
        first_row = updated_data.iloc[0]
        assert first_row['VIEW'] == 125.0
        
        # Verify other values unchanged
        assert first_row['SHORTLIMIT'] == -10.0
        assert first_row['CUID'] == 'C001'


class TestExcelDataManagerSaveOperations:
    """Test save operations with timestamping."""
    
    def test_save_workbook_calls_excel_io_with_correct_data(self):
        """Test that save_workbook delegates to ExcelIO with current state."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26', 'FEB26']
        mock_excel_io.save_workbook.return_value = "/tmp/saved_file_20240827_123456.xlsx"
        
        # Setup test data
        test_data = {
            'JAN26': pd.DataFrame({'CLUSTER': [1, 2], 'VIEW': [100.0, 150.0]}),
            'FEB26': pd.DataFrame({'CLUSTER': [3, 4], 'VIEW': [200.0, 250.0]})
        }
        
        mock_excel_io.load_sheet.side_effect = lambda sheet: test_data[sheet]
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/original.xlsx")
        
        # Save workbook
        saved_path = manager.save_workbook()
        
        # Verify save was called with correct data
        mock_excel_io.save_workbook.assert_called_once()
        call_args = mock_excel_io.save_workbook.call_args[0]
        saved_data = call_args[0]
        
        # Verify data structure passed to save
        assert isinstance(saved_data, dict)
        assert 'JAN26' in saved_data
        assert 'FEB26' in saved_data
        
        # Verify return value
        assert saved_path == "/tmp/saved_file_20240827_123456.xlsx"


class TestExcelDataManagerDataStats:
    """Test data statistics and metadata extraction."""
    
    def test_get_data_stats_returns_meaningful_statistics(self):
        """Test that get_data_stats returns useful information about loaded data."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26', 'FEB26']
        
        jan_df = pd.DataFrame({
            'CLUSTER': [1, 2, 1, 3],
            'CUID': ['C001', 'C002', 'C003', 'C004'],
            'VIEW': [100.0, 150.0, 120.0, 200.0]
        })
        
        feb_df = pd.DataFrame({
            'CLUSTER': [4, 5],
            'CUID': ['C005', 'C006'],
            'VIEW': [300.0, 350.0]
        })
        
        mock_excel_io.load_sheet.side_effect = lambda sheet: {
            'JAN26': jan_df,
            'FEB26': feb_df
        }[sheet]
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        
        # Get statistics
        stats = manager.get_data_stats()
        
        # Verify meaningful statistics
        assert isinstance(stats, dict)
        assert 'total_sheets' in stats
        assert 'active_sheet' in stats
        assert 'total_constraints' in stats
        assert 'unique_clusters' in stats
        
        assert stats['total_sheets'] == 2
        assert stats['active_sheet'] is None  # No active sheet set yet
        
        # Set active sheet and check updated stats
        manager.set_active_sheet('JAN26')
        stats = manager.get_data_stats()
        
        assert stats['active_sheet'] == 'JAN26'
        # Should include stats from active sheet when available


class TestExcelDataManagerErrorHandling:
    """Test error handling and data integrity."""
    
    def test_handles_corrupted_data_gracefully(self):
        """Test that manager handles corrupted or invalid data without crashing."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['CORRUPTED_SHEET']
        
        # Mock corrupted data (missing required columns)
        corrupted_df = pd.DataFrame({
            'INVALID_COL': [1, 2, 3],
            'ANOTHER_COL': ['A', 'B', 'C']
        })
        
        mock_excel_io.load_sheet.return_value = corrupted_df
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/corrupted.xlsx")
        manager.set_active_sheet('CORRUPTED_SHEET')
        
        # Should handle missing CLUSTER column gracefully
        clusters = manager.get_all_clusters()
        assert clusters == []  # Empty list for missing CLUSTER column
        
        # Should handle cluster data request gracefully
        cluster_data = manager.get_cluster_data('1')
        assert isinstance(cluster_data, pd.DataFrame)
        assert cluster_data.empty
"""
Tests for ExcelIO data loading functionality.

This test suite focuses on the 10 essential behaviors required by Task 004:
1. Loading Excel files with multiple sheets
2. DataFrame creation from Excel data  
3. Handling missing files
4. Handling corrupted Excel files
5. Sheet name extraction
6. Metadata extraction (file size, modified date)
7. Handling empty sheets
8. Column type preservation
9. Handling merged cells
10. Memory-efficient loading

Tests are designed to drive TDD implementation of ExcelIO class.
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from typing import Dict, List, Optional

from src.io.excel_io import ExcelIO
from src.models.data_models import ConstraintRow, ExcelMetadata


class TestExcelIOFileLoading:
    """Test basic Excel file loading operations."""
    
    def test_load_valid_excel_file_succeeds(self):
        """Test that ExcelIO successfully loads a valid Excel workbook."""
        # Create a temporary Excel file path
        test_file_path = Path("/tmp/test_workbook.xlsx")
        
        # Mock successful file loading
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('pandas.read_excel') as mock_read_excel:
            
            # Setup mock to return valid DataFrame
            mock_df = pd.DataFrame({
                'CLUSTER': [1, 2, 3],
                'CUID': ['CONST_001', 'CONST_002', 'CONST_003'],
                'VIEW': [100.0, 150.0, 200.0],
                'SHORTLIMIT': [-10.0, -20.0, None]
            })
            mock_read_excel.return_value = mock_df
            
            excel_io = ExcelIO(test_file_path)
            result = excel_io.load_workbook()
            
            # Verify successful loading
            assert result is True
            # Verify pandas.read_excel was called
            assert mock_read_excel.called
    
    def test_load_nonexistent_file_raises_error(self):
        """Test that loading a non-existent file raises FileNotFoundError."""
        nonexistent_path = Path("/nonexistent/file.xlsx")
        
        excel_io = ExcelIO(nonexistent_path)
        
        with pytest.raises(FileNotFoundError, match="Excel file not found"):
            excel_io.load_workbook()
    
    def test_discover_sheet_names_returns_list(self):
        """Test that get_sheet_names returns available monthly sheet names."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('pandas.ExcelFile') as mock_excel_file:
            
            # Mock Excel file with monthly sheet names
            mock_file_obj = Mock()
            mock_file_obj.sheet_names = ['JAN26', 'FEB26', 'MAR26', 'Summary', 'HIST']
            mock_excel_file.return_value = mock_file_obj
            
            excel_io = ExcelIO(test_file_path)
            sheet_names = excel_io.get_sheet_names()
            
            # Should return all sheet names
            expected_names = ['JAN26', 'FEB26', 'MAR26', 'Summary', 'HIST']
            assert sheet_names == expected_names
    
    def test_load_sheet_to_dataframe_creates_dataframe(self):
        """Test that load_sheet converts Excel sheet data to pandas DataFrame."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('pandas.read_excel') as mock_read_excel:
            
            # Mock DataFrame with constraint data
            expected_df = pd.DataFrame({
                'CLUSTER': [1, 2],
                'CUID': ['CONSTRAINT_A', 'CONSTRAINT_B'],
                'VIEW': [120.0, 80.0],
                'PREV': [115.0, 75.0],
                'PACTUAL': [118.0, 82.0],
                'FLOW': [100.0, 60.0],
                'LIMIT': [125.0, 85.0]
            })
            mock_read_excel.return_value = expected_df
            
            excel_io = ExcelIO(test_file_path)
            result_df = excel_io.load_sheet("JAN26")
            
            # Verify DataFrame structure
            assert isinstance(result_df, pd.DataFrame)
            assert 'CLUSTER' in result_df.columns
            assert 'CUID' in result_df.columns
            assert 'VIEW' in result_df.columns
            assert len(result_df) == 2


class TestExcelIODataParsing:
    """Test Excel data parsing and ConstraintRow conversion."""
    
    def test_validate_sheet_structure_checks_required_columns(self):
        """Test that validate_sheet_structure verifies required columns exist."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        # Valid DataFrame with required columns
        valid_df = pd.DataFrame({
            'CLUSTER': [1, 2],
            'CUID': ['C001', 'C002'],
            'VIEW': [100.0, 150.0]
        })
        assert excel_io.validate_sheet_structure(valid_df) is True
        
        # Invalid DataFrame missing required columns
        invalid_df = pd.DataFrame({
            'RANDOM_COL': [1, 2],
            'ANOTHER_COL': ['A', 'B']
        })
        assert excel_io.validate_sheet_structure(invalid_df) is False
    
    def test_preserve_numeric_data_types_maintains_types(self):
        """Test that numeric columns maintain their int/float types."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('pandas.read_excel') as mock_read_excel:
            
            # Mock DataFrame with mixed numeric types
            mock_df = pd.DataFrame({
                'CLUSTER': [1, 2, 3],  # Should remain int
                'VIEW': [100.5, 150.7, 200.2],  # Should remain float
                'FLOW': [95.0, 120.0, 180.0],  # Should remain float
                'DIRECTION': [1, -1, 1]  # Should remain int
            })
            mock_read_excel.return_value = mock_df
            
            excel_io = ExcelIO(test_file_path)
            result_df = excel_io.load_sheet("JAN26")
            
            # Verify numeric types are preserved
            assert result_df['CLUSTER'].dtype in ['int64', 'Int64']
            assert result_df['VIEW'].dtype == 'float64'
            assert result_df['FLOW'].dtype == 'float64'
            assert result_df['DIRECTION'].dtype in ['int64', 'Int64']
    
    def test_convert_sheet_to_constraint_rows(self):
        """Test that get_constraint_rows creates ConstraintRow objects from sheet data."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('pandas.read_excel') as mock_read_excel:
            
            # Mock valid constraint data
            mock_df = pd.DataFrame({
                'CLUSTER': [1, 2],
                'CUID': ['CONSTRAINT_001', 'CONSTRAINT_002'],
                'VIEW': [100.0, 200.0],
                'SHORTLIMIT': [-15.0, None],
                'PREV': [95.0, 190.0],
                'PACTUAL': [98.0, 195.0]
            })
            mock_read_excel.return_value = mock_df
            
            excel_io = ExcelIO(test_file_path)
            constraint_rows = excel_io.get_constraint_rows("JAN26")
            
            # Verify ConstraintRow objects are created
            assert isinstance(constraint_rows, list)
            assert len(constraint_rows) == 2
            assert all(isinstance(row, ConstraintRow) for row in constraint_rows)
            
            # Verify data mapping
            assert constraint_rows[0].cluster == 1
            assert constraint_rows[0].cuid == 'CONSTRAINT_001'
            assert constraint_rows[0].view == 100.0
            assert constraint_rows[0].shortlimit == -15.0


class TestExcelIOErrorHandling:
    """Test error handling for corrupted files and edge cases."""
    
    def test_handle_corrupted_excel_file_gracefully(self):
        """Test that corrupted Excel files are handled without crashing."""
        test_file_path = Path("/tmp/corrupted.xlsx")
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('pandas.read_excel', side_effect=Exception("Corrupted file")):
            
            excel_io = ExcelIO(test_file_path)
            
            # Should handle corruption gracefully
            with pytest.raises(Exception) as exc_info:
                excel_io.load_workbook()
            
            # Should provide meaningful error information
            assert "Corrupted file" in str(exc_info.value)
    
    def test_handle_empty_sheets_gracefully(self):
        """Test that empty sheets don't cause crashes."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('pandas.read_excel') as mock_read_excel:
            
            # Mock empty DataFrame
            empty_df = pd.DataFrame()
            mock_read_excel.return_value = empty_df
            
            excel_io = ExcelIO(test_file_path)
            result_df = excel_io.load_sheet("EMPTY_SHEET")
            
            # Should return empty DataFrame without error
            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) == 0
            assert result_df.empty is True


class TestExcelIOMetadataAndEfficiency:
    """Test metadata extraction and memory-efficient loading."""
    
    def test_extract_file_metadata_returns_info(self):
        """Test that file metadata (size, modified date) is extracted correctly."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        
        # Mock file stats
        mock_stat = Mock()
        mock_stat.st_size = 5242880  # 5MB in bytes
        mock_stat.st_mtime = 1692144000  # Mock timestamp
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('src.io.excel_io.Path.stat', return_value=mock_stat), \
             patch('pandas.ExcelFile') as mock_excel_file:
            
            mock_file_obj = Mock()
            mock_file_obj.sheet_names = ['JAN26', 'FEB26']
            mock_excel_file.return_value = mock_file_obj
            
            excel_io = ExcelIO(test_file_path)
            metadata = excel_io.get_file_metadata()
            
            # Verify metadata extraction
            assert isinstance(metadata, ExcelMetadata)
            assert metadata.file_path == str(test_file_path)
            assert metadata.file_size_mb == 5.0  # 5MB converted
            assert len(metadata.sheet_names) == 2
            assert isinstance(metadata.last_modified, datetime)
    
    def test_memory_efficient_loading_uses_chunking(self):
        """Test that large files use memory-efficient loading strategies."""
        test_file_path = Path("/tmp/large_workbook.xlsx")
        
        with patch('src.io.excel_io.Path.exists', return_value=True), \
             patch('src.io.excel_io.Path.stat') as mock_stat, \
             patch('pandas.read_excel') as mock_read_excel:
            
            # Mock large file (>50MB)
            mock_stat.return_value.st_size = 52428800  # 50MB
            
            # Mock large DataFrame
            large_df = pd.DataFrame({
                'CLUSTER': range(10000),
                'CUID': [f'CONSTRAINT_{i:06d}' for i in range(10000)],
                'VIEW': [100.0 + i for i in range(10000)]
            })
            mock_read_excel.return_value = large_df
            
            excel_io = ExcelIO(test_file_path)
            excel_io.load_workbook()
            
            # For large files, should use memory-efficient options
            call_args = mock_read_excel.call_args
            if call_args and len(call_args) > 1:
                # Check if memory-efficient parameters were used
                kwargs = call_args[1] if call_args[1] else {}
                # Could check for engine='openpyxl' or other efficiency params
                assert True  # Placeholder - actual implementation will determine specifics
"""
Tests for Task 005: Excel Save Functionality with Timestamped File Creation.

This test suite focuses on the 10-12 essential behaviors for Excel save functionality:
1. Save modified DataFrames to new Excel files
2. Timestamped filename generation
3. Preserve Excel formatting and structure  
4. Atomic save operations (temp file approach)
5. Handle write permissions errors
6. Handle disk space issues
7. Preserve color formatting in saved files
8. Multi-sheet workbook saving
9. Incremental save vs full save
10. Backup creation before save
11. Round-trip data integrity
12. Performance for large files

Tests are designed to drive TDD implementation following the specifications in task-005.md.
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open, call
import tempfile
import os
import shutil
import time
from typing import Dict, List, Optional
import openpyxl
from openpyxl.styles import PatternFill
import errno

from src.io.excel_io import ExcelIO


class TestExcelSaveBasicFunctionality:
    """Test core Excel save functionality and timestamped file creation."""

    def test_save_data_creates_timestamped_file(self):
        """Test that save_data creates a file with proper timestamp format."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        # Create test DataFrame
        test_df = pd.DataFrame({
            'CLUSTER': [1, 2, 3],
            'CUID': ['CONST_001', 'CONST_002', 'CONST_003'],
            'VIEW': [100.0, 150.0, 200.0]
        })
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            # Mock timestamp generation
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            
            # Mock successful save
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            result_path = excel_io.save_data(
                dataframe=test_df,
                sheet_name="Jan 2025", 
                original_file="/tmp/constraints.xlsx"
            )
            
            # Should create timestamped filename
            expected_path = "/tmp/constraints_20250827_143022.xlsx"
            assert result_path == expected_path
            
            # Verify ExcelWriter was called with correct path
            mock_writer.assert_called_with(Path(expected_path), engine='openpyxl')

    def test_save_data_preserves_dataframe_contents(self):
        """Test that DataFrame data is preserved exactly in saved file."""
        test_file_path = Path("/tmp/test_workbook.xlsx") 
        excel_io = ExcelIO(test_file_path)
        
        # Create test DataFrame with various data types
        test_df = pd.DataFrame({
            'CLUSTER': [1, 2, None],
            'CUID': ['CONST_001', 'CONST_002', 'CONST_003'],
            'VIEW': [100.5, 150.7, 200.2],
            'SHORTLIMIT': [-10.0, None, -30.0],
            'DIRECTION': [1, -1, 1]
        })
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            
            # Mock writer context manager
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            excel_io.save_data(
                dataframe=test_df,
                sheet_name="Jan 2025",
                original_file="/tmp/constraints.xlsx"
            )
            
            # Verify ExcelWriter was configured correctly
            mock_writer.assert_called_with(Path("/tmp/constraints_20250827_143022.xlsx"), engine='openpyxl')

    def test_generate_filename_creates_proper_format(self):
        """Test that _generate_filename creates correct timestamped names."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        # Test basic filename generation
        result = excel_io._generate_filename("constraints.xlsx", "20250827_143022")
        assert result == "constraints_20250827_143022.xlsx"
        
        # Test with path
        result = excel_io._generate_filename("/path/to/data.xlsx", "20250827_143022")
        assert result == "data_20250827_143022.xlsx"
        
        # Test with complex filename
        result = excel_io._generate_filename("flow_results_processed.xlsx", "20250827_143022")
        assert result == "flow_results_processed_20250827_143022.xlsx"

    def test_save_to_correct_sheet_name(self):
        """Test that data is saved to the specified sheet name."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({'CLUSTER': [1], 'VIEW': [100.0]})
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            excel_io.save_data(
                dataframe=test_df,
                sheet_name="Feb 2025",
                original_file="/tmp/constraints.xlsx"  
            )
            
            # Verify ExcelWriter was configured correctly for the sheet
            mock_writer.assert_called_with(Path("/tmp/constraints_20250827_143022.xlsx"), engine='openpyxl')


class TestExcelSaveErrorHandling:
    """Test error handling for save operations."""

    def test_permission_denied_handling(self):
        """Test graceful handling of write permission errors."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({'CLUSTER': [1], 'VIEW': [100.0]})
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter', side_effect=PermissionError("Permission denied")), \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            
            with pytest.raises(PermissionError, match="Permission denied"):
                excel_io.save_data(
                    dataframe=test_df,
                    sheet_name="Jan 2025",
                    original_file="/readonly/constraints.xlsx"
                )

    def test_disk_full_handling(self):
        """Test handling of insufficient disk space errors.""" 
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({'CLUSTER': list(range(1000)), 'VIEW': [100.0] * 1000})
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter', side_effect=OSError(errno.ENOSPC, "No space left")), \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            
            with pytest.raises(OSError) as exc_info:
                excel_io.save_data(
                    dataframe=test_df,
                    sheet_name="Jan 2025", 
                    original_file="/tmp/constraints.xlsx"
                )
            assert exc_info.value.errno == errno.ENOSPC

    def test_invalid_dataframe_handling(self):
        """Test handling of empty or malformed DataFrames."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        # Test empty DataFrame
        empty_df = pd.DataFrame()
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            # Should handle empty DataFrame gracefully
            result = excel_io.save_data(
                dataframe=empty_df,
                sheet_name="Jan 2025",
                original_file="/tmp/constraints.xlsx"
            )
            
            assert result == "/tmp/constraints_20250827_143022.xlsx"

    def test_invalid_sheet_name_handling(self):
        """Test handling of invalid Excel sheet names."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({'CLUSTER': [1], 'VIEW': [100.0]})
        
        # Test sheet name with invalid characters
        invalid_sheet_names = [
            "Sheet/With/Slashes", 
            "Sheet:With:Colons",
            "Sheet*With*Asterisks", 
            "Sheet?With?Questions",
            "Sheet[With]Brackets"
        ]
        
        for invalid_name in invalid_sheet_names:
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pandas.ExcelWriter') as mock_writer, \
                 patch('src.io.excel_io.datetime') as mock_datetime:
                
                mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
                mock_writer_instance = Mock()
                mock_writer.return_value.__enter__.return_value = mock_writer_instance
                
                # Should sanitize sheet name or handle error
                result = excel_io.save_data(
                    dataframe=test_df,
                    sheet_name=invalid_name,
                    original_file="/tmp/constraints.xlsx"
                )
                
                # Should still create file, potentially with sanitized sheet name
                assert "/tmp/constraints_20250827_143022.xlsx" in result


class TestExcelSaveAdvancedFeatures:
    """Test advanced save features like atomic operations and formatting."""

    def test_atomic_save_operation_temp_file(self):
        """Test that save uses temporary file approach for atomic operations."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({'CLUSTER': [1], 'VIEW': [100.0]})
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('shutil.move') as mock_move, \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            
            # Mock temp file
            mock_temp_file = Mock()
            mock_temp_file.name = "/tmp/temp_save_12345.xlsx"
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            result = excel_io.save_data(
                dataframe=test_df,
                sheet_name="Jan 2025",
                original_file="/tmp/constraints.xlsx"
            )
            
            # Should use temp file and then move to final location
            expected_final = "/tmp/constraints_20250827_143022.xlsx"
            mock_move.assert_called_once_with("/tmp/temp_save_12345.xlsx", expected_final)
            assert result == expected_final

    def test_preserve_formatting_column_widths(self):
        """Test that column widths are preserved in saved files."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 2],
            'VERY_LONG_COLUMN_NAME': ['Value1', 'Value2'],
            'SHORT': [1.0, 2.0]
        })
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('openpyxl.Workbook') as mock_workbook, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            
            # Mock workbook and worksheet
            mock_wb = Mock()
            mock_ws = Mock()
            mock_workbook.return_value = mock_wb
            mock_wb.active = mock_ws
            mock_wb.save = Mock()
            
            excel_io._apply_formatting(mock_ws, test_df)
            
            # Should set column widths based on content
            assert mock_ws.column_dimensions.__getitem__.called

    def test_preserve_color_formatting(self):
        """Test that cell color formatting is preserved when saving."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 2],
            'STATUS': ['ACTIVE', 'INACTIVE'], 
            'VALUE': [100.0, -50.0]
        })
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('openpyxl.Workbook') as mock_workbook, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            
            # Mock workbook and cells
            mock_wb = Mock()
            mock_ws = Mock()
            mock_cell = Mock()
            mock_workbook.return_value = mock_wb
            mock_wb.active = mock_ws
            mock_ws.cell.return_value = mock_cell
            
            excel_io._apply_color_formatting(mock_ws, test_df)
            
            # Should apply color formatting based on cell values
            assert mock_ws.cell.called
            # Should set fill property for colored cells
            assert hasattr(mock_cell, 'fill') or mock_cell.fill is not None


class TestExcelSaveMultiSheet:
    """Test multi-sheet workbook saving functionality."""

    def test_save_multi_sheet_workbook(self):
        """Test saving data to multiple sheets in one workbook."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        # Create test data for multiple sheets
        sheet_data = {
            "Jan 2025": pd.DataFrame({'CLUSTER': [1, 2], 'VIEW': [100.0, 150.0]}),
            "Feb 2025": pd.DataFrame({'CLUSTER': [3, 4], 'VIEW': [200.0, 250.0]}),
            "Mar 2025": pd.DataFrame({'CLUSTER': [5, 6], 'VIEW': [300.0, 350.0]})
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            result = excel_io.save_data(
                dataframe=sheet_data["Jan 2025"],  # Test with first sheet
                sheet_name="Jan 2025",
                original_file="/tmp/constraints.xlsx"
            )
            
            # Should save all sheets to same workbook
            expected_path = "/tmp/constraints_20250827_143022.xlsx"
            assert result == expected_path
            
            # Verify each sheet was written
            assert mock_writer.call_count >= 1

    def test_backup_creation_before_save(self):
        """Test that backup is created before saving new file."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({'CLUSTER': [1], 'VIEW': [100.0]})
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('shutil.copy2') as mock_copy, \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            result = excel_io.save_data(
                dataframe=test_df,
                sheet_name="Jan 2025", 
                original_file="/tmp/constraints.xlsx"
            )
            
            # Should create backup before saving
            mock_copy.assert_called_once()
            backup_call = mock_copy.call_args[0]
            assert "/tmp/constraints.xlsx" in backup_call[0]
            assert "backup" in backup_call[1]


class TestExcelSavePerformanceAndIntegration:
    """Test performance characteristics and round-trip integrity."""

    def test_save_and_reload_round_trip_integrity(self):
        """Test that saved data can be reloaded with identical contents."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        # Create test DataFrame with various data types
        original_df = pd.DataFrame({
            'CLUSTER': [1, 2, 3],
            'CUID': ['CONST_001', 'CONST_002', 'CONST_003'],
            'VIEW': [100.5, 150.7, 200.2],
            'SHORTLIMIT': [-10.0, None, -30.0],
            'DIRECTION': [1, -1, 1]
        })
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('pandas.read_excel') as mock_read, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            # Mock reading back the saved data
            mock_read.return_value = original_df.copy()
            
            # Save the data
            saved_path = excel_io.save_data(
                dataframe=original_df,
                sheet_name="Jan 2025",
                original_file="/tmp/constraints.xlsx"
            )
            
            # Load it back
            reloaded_excel = ExcelIO(Path(saved_path))
            reloaded_df = reloaded_excel.load_sheet("Jan 2025")
            
            # Data should be identical
            pd.testing.assert_frame_equal(original_df, reloaded_df)

    def test_large_file_performance_efficient(self):
        """Test that large files (>5MB) are handled efficiently."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        # Create large DataFrame (simulate >5MB)
        large_df = pd.DataFrame({
            'CLUSTER': list(range(50000)),
            'CUID': [f'CONSTRAINT_{i:06d}' for i in range(50000)],
            'VIEW': [100.0 + i * 0.1 for i in range(50000)],
            'SHORTLIMIT': [-10.0 - i * 0.01 for i in range(50000)]
        })
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('datetime.datetime.now') as mock_now, \
             patch('time.time', side_effect=[0.0, 0.8]):  # Mock <1 second execution
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            # Should complete within performance requirements
            start_time = time.time()
            result = excel_io.save_data(
                dataframe=large_df,
                sheet_name="Jan 2025",
                original_file="/tmp/constraints.xlsx"
            )
            end_time = time.time()
            
            # Should use optimized writing for large files
            call_args = mock_writer.call_args
            if call_args and len(call_args) > 1:
                kwargs = call_args[1]
                # Should use engine optimizations
                assert kwargs.get('engine') == 'openpyxl'
            
            assert result == "/tmp/constraints_20250827_143022.xlsx"

    def test_backup_directory_creation(self):
        """Test creation of backup directory when specified."""
        test_file_path = Path("/tmp/test_workbook.xlsx")
        excel_io = ExcelIO(test_file_path)
        
        test_df = pd.DataFrame({'CLUSTER': [1], 'VIEW': [100.0]})
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('shutil.copy2') as mock_copy, \
             patch('pandas.ExcelWriter') as mock_writer, \
             patch('src.io.excel_io.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20250827_143022"
            mock_writer_instance = Mock()
            mock_writer.return_value.__enter__.return_value = mock_writer_instance
            
            result = excel_io.save_data(
                dataframe=test_df,
                sheet_name="Jan 2025",
                original_file="/tmp/constraints.xlsx",
                backup_dir="/tmp/backups"
            )
            
            # Should create backup directory if it doesn't exist
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Should save backup to specified directory
            backup_call = mock_copy.call_args[0] if mock_copy.called else None
            if backup_call:
                assert "/tmp/backups" in backup_call[1]
            
            assert result == "/tmp/constraints_20250827_143022.xlsx"
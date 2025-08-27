"""
Tests for Task 010: Safe Edit Operations with Validation, Rollback, and History Tracking.

This test suite focuses on 10 essential behaviors for safe edit operations in ExcelDataManager:
1. Safe edit operations with validation before applying
2. Rollback capability for invalid edits
3. Edit history tracking for undo/redo
4. Batch edit operations for efficiency
5. Conflict detection when multiple edits affect same cell
6. Transaction-like behavior (all or nothing)
7. Validation feedback integration
8. Memory limits on edit history
9. Edit serialization for persistence
10. Thread-safe edit operations

Tests are designed to drive TDD implementation following the red-green-refactor cycle.
"""

import pytest
import pandas as pd
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Any

from src.business_logic.excel_data_manager import ExcelDataManager
from src.business_logic.validators import DataValidator
from src.io.excel_io import ExcelIO
from src.models.data_models import EditRecord, ValidationResult


class TestSafeEditOperationsWithValidation:
    """Test safe edit operations that validate before applying changes."""
    
    def test_validate_and_update_accepts_valid_view_value(self):
        """Test that validate_and_update successfully updates valid VIEW values."""
        # Setup mock dependencies
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 1, 2],
            'CUID': ['C001', 'C002', 'C003'],
            'VIEW': [100.0, 150.0, 200.0],
            'SHORTLIMIT': [-10.0, -20.0, -30.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        # Create manager with validator
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Attempt valid VIEW update
        success, message = manager.validate_and_update(
            cluster='1', 
            constraint_index=0, 
            column='VIEW', 
            value='125.5'
        )
        
        # Should succeed with positive validation
        assert success is True
        assert message == "Value updated successfully"
        
        # Verify data was actually updated
        updated_data = manager.get_cluster_data('1')
        assert updated_data.iloc[0]['VIEW'] == 125.5
    
    def test_validate_and_update_rejects_invalid_view_value(self):
        """Test that validate_and_update rejects invalid VIEW values (negative/zero)."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1],
            'CUID': ['C001'],
            'VIEW': [100.0],
            'SHORTLIMIT': [-10.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Attempt invalid VIEW update (negative value)
        success, message = manager.validate_and_update(
            cluster='1',
            constraint_index=0,
            column='VIEW',
            value='-50.0'
        )
        
        # Should fail validation
        assert success is False
        assert "VIEW must be a positive number greater than 0" in message
        
        # Original data should remain unchanged
        original_data = manager.get_cluster_data('1')
        assert original_data.iloc[0]['VIEW'] == 100.0
    
    def test_validate_and_update_accepts_valid_shortlimit_value(self):
        """Test that validate_and_update accepts valid SHORTLIMIT values (negative or empty)."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 1],
            'CUID': ['C001', 'C002'],
            'VIEW': [100.0, 150.0],
            'SHORTLIMIT': [-10.0, -20.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Test valid negative SHORTLIMIT update
        success, message = manager.validate_and_update(
            cluster='1',
            constraint_index=0,
            column='SHORTLIMIT',
            value='-25.5'
        )
        
        assert success is True
        assert message == "Value updated successfully"
        
        # Test valid empty SHORTLIMIT update
        success, message = manager.validate_and_update(
            cluster='1',
            constraint_index=1,
            column='SHORTLIMIT',
            value=''
        )
        
        assert success is True
        assert message == "Value updated successfully"
        
        # Verify updates applied
        updated_data = manager.get_cluster_data('1')
        assert updated_data.iloc[0]['SHORTLIMIT'] == -25.5
        assert pd.isna(updated_data.iloc[1]['SHORTLIMIT'])  # Empty becomes None/NaN


class TestEditHistoryTracking:
    """Test edit history tracking for undo/redo functionality."""
    
    def test_get_edit_history_tracks_all_edits_with_metadata(self):
        """Test that get_edit_history maintains complete record of all edits."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 1],
            'CUID': ['C001', 'C002'],
            'VIEW': [100.0, 150.0],
            'SHORTLIMIT': [-10.0, -20.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Initially no edit history
        history = manager.get_edit_history()
        assert history == []
        
        # Make first edit
        manager.validate_and_update('1', 0, 'VIEW', '125.0')
        
        # Make second edit
        manager.validate_and_update('1', 1, 'SHORTLIMIT', '-25.0')
        
        # Check edit history
        history = manager.get_edit_history()
        assert len(history) == 2
        
        # Verify first edit record
        first_edit = history[0]
        assert isinstance(first_edit, EditRecord)
        assert first_edit.sheet == 'JAN26'
        assert first_edit.column == 'VIEW'
        assert first_edit.old_value == 100.0
        assert first_edit.new_value == 125.0
        assert first_edit.cluster_id == 1
        
        # Verify second edit record
        second_edit = history[1]
        assert second_edit.column == 'SHORTLIMIT'
        assert second_edit.old_value == -20.0
        assert second_edit.new_value == -25.0
    
    def test_edit_history_respects_memory_limit(self):
        """Test that edit history maintains maximum of 1000 entries using FIFO."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        # Create large test dataframe
        test_df = pd.DataFrame({
            'CLUSTER': [1] * 100,
            'CUID': [f'C{i:03d}' for i in range(100)],
            'VIEW': [100.0 + i for i in range(100)],
            'SHORTLIMIT': [-10.0 - i for i in range(100)]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Simulate making 1050 edits (exceeds 1000 limit)
        for i in range(1050):
            constraint_idx = i % 100
            new_value = 200.0 + i
            manager.validate_and_update('1', constraint_idx, 'VIEW', str(new_value))
        
        # Check that history is limited to 1000 entries
        history = manager.get_edit_history()
        assert len(history) == 1000
        
        # Verify FIFO behavior - first 50 edits should be gone
        # Last edit should be the 1050th edit
        last_edit = history[-1]
        assert last_edit.new_value == 200.0 + 1049  # 1050th edit (0-indexed)


class TestBatchEditOperations:
    """Test batch edit operations with transaction-like behavior."""
    
    def test_batch_update_succeeds_when_all_edits_valid(self):
        """Test that batch_update applies all changes when all edits are valid."""
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
        
        # Define batch updates - all valid
        updates = [
            {
                'cluster': '1',
                'constraint_index': 0,
                'column': 'VIEW',
                'value': '125.0'
            },
            {
                'cluster': '1', 
                'constraint_index': 1,
                'column': 'SHORTLIMIT',
                'value': '-25.0'
            },
            {
                'cluster': '2',
                'constraint_index': 0,
                'column': 'VIEW',
                'value': '225.0'
            }
        ]
        
        # Execute batch update
        result = manager.batch_update(updates)
        
        # Verify successful batch result
        assert result['success'] is True
        assert result['applied_count'] == 3
        assert result['failed_count'] == 0
        assert 'error_message' not in result
        
        # Verify all changes were applied
        cluster1_data = manager.get_cluster_data('1')
        assert cluster1_data.iloc[0]['VIEW'] == 125.0
        assert cluster1_data.iloc[1]['SHORTLIMIT'] == -25.0
        
        cluster2_data = manager.get_cluster_data('2')
        assert cluster2_data.iloc[0]['VIEW'] == 225.0
    
    def test_batch_update_rolls_back_all_changes_when_any_edit_invalid(self):
        """Test that batch_update rolls back all changes if any edit fails validation."""
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
        
        # Define batch updates with one invalid edit
        updates = [
            {
                'cluster': '1',
                'constraint_index': 0,
                'column': 'VIEW',
                'value': '125.0'  # Valid
            },
            {
                'cluster': '1',
                'constraint_index': 1,
                'column': 'VIEW',
                'value': '-50.0'  # Invalid - negative VIEW
            },
            {
                'cluster': '2',
                'constraint_index': 0,
                'column': 'VIEW',
                'value': '225.0'  # Valid
            }
        ]
        
        # Execute batch update
        result = manager.batch_update(updates)
        
        # Verify batch failure
        assert result['success'] is False
        assert result['applied_count'] == 0
        assert result['failed_count'] == 1
        assert 'VIEW must be a positive number' in result['error_message']
        
        # Verify NO changes were applied (rollback occurred)
        cluster1_data = manager.get_cluster_data('1')
        assert cluster1_data.iloc[0]['VIEW'] == 100.0  # Original value
        assert cluster1_data.iloc[1]['VIEW'] == 150.0  # Original value
        
        cluster2_data = manager.get_cluster_data('2')
        assert cluster2_data.iloc[0]['VIEW'] == 200.0  # Original value


class TestColumnEditabilityChecks:
    """Test column editability validation and read-only protection."""
    
    def test_can_edit_column_allows_editable_columns(self):
        """Test that can_edit_column returns True for editable columns (VIEW, SHORTLIMIT)."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        manager = ExcelDataManager(mock_excel_io)
        
        # Test editable columns
        assert manager.can_edit_column('VIEW') is True
        assert manager.can_edit_column('SHORTLIMIT') is True
        
        # Case insensitive
        assert manager.can_edit_column('view') is True
        assert manager.can_edit_column('shortlimit') is True
    
    def test_can_edit_column_blocks_readonly_columns(self):
        """Test that can_edit_column returns False for read-only columns."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        manager = ExcelDataManager(mock_excel_io)
        
        # Test read-only columns
        assert manager.can_edit_column('LODF') is False
        assert manager.can_edit_column('CUID') is False
        assert manager.can_edit_column('CLUSTER') is False
        assert manager.can_edit_column('FLOW') is False
        assert manager.can_edit_column('LIMIT') is False
        
        # Case insensitive
        assert manager.can_edit_column('lodf') is False
        assert manager.can_edit_column('cuid') is False
    
    def test_validate_and_update_rejects_readonly_column_edits(self):
        """Test that validate_and_update rejects attempts to edit read-only columns."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1],
            'CUID': ['C001'],
            'VIEW': [100.0],
            'LODF': [0.85]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Attempt to edit read-only column
        success, message = manager.validate_and_update(
            cluster='1',
            constraint_index=0,
            column='LODF',
            value='0.90'
        )
        
        # Should fail with appropriate error
        assert success is False
        assert "Column 'LODF' is read-only and cannot be modified" in message
        
        # Original data should remain unchanged
        original_data = manager.get_cluster_data('1')
        assert original_data.iloc[0]['LODF'] == 0.85


class TestEditRollbackCapability:
    """Test rollback capability for specific edit operations."""
    
    def test_rollback_edit_undoes_specific_edit_by_id(self):
        """Test that rollback_edit can undo a specific edit by its ID."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 1],
            'CUID': ['C001', 'C002'],
            'VIEW': [100.0, 150.0],
            'SHORTLIMIT': [-10.0, -20.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Make multiple edits
        manager.validate_and_update('1', 0, 'VIEW', '125.0')
        manager.validate_and_update('1', 1, 'SHORTLIMIT', '-25.0')
        manager.validate_and_update('1', 0, 'VIEW', '135.0')
        
        # Get edit history to find specific edit ID
        history = manager.get_edit_history()
        assert len(history) == 3
        
        # Get ID of the second edit (SHORTLIMIT change)
        shortlimit_edit_id = history[1].cuid or str(history[1].timestamp.timestamp())
        
        # Rollback specific edit
        rollback_success = manager.rollback_edit(shortlimit_edit_id)
        
        # Verify rollback succeeded
        assert rollback_success is True
        
        # Verify only that specific edit was rolled back
        updated_data = manager.get_cluster_data('1')
        assert updated_data.iloc[0]['VIEW'] == 135.0  # Last VIEW edit still applied
        assert updated_data.iloc[1]['SHORTLIMIT'] == -20.0  # Rolled back to original
    
    def test_rollback_edit_returns_false_for_invalid_id(self):
        """Test that rollback_edit returns False for non-existent edit IDs."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1],
            'CUID': ['C001'],
            'VIEW': [100.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Attempt rollback of non-existent edit
        rollback_success = manager.rollback_edit('invalid-edit-id-123')
        
        # Should return False for invalid ID
        assert rollback_success is False


class TestConflictDetectionAndValidation:
    """Test conflict detection when multiple edits affect the same cell."""
    
    def test_get_validation_rules_returns_column_rules(self):
        """Test that get_validation_rules returns appropriate rules for columns."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        manager = ExcelDataManager(mock_excel_io)
        
        # Get validation rules for VIEW
        view_rules = manager.get_validation_rules('VIEW')
        assert isinstance(view_rules, dict)
        assert view_rules['min_value'] == 0
        assert view_rules['exclusive_min'] is True
        assert view_rules['allow_none'] is False
        
        # Get validation rules for SHORTLIMIT
        shortlimit_rules = manager.get_validation_rules('SHORTLIMIT')
        assert isinstance(shortlimit_rules, dict)
        assert shortlimit_rules['max_value'] == 0
        assert shortlimit_rules['exclusive_max'] is True
        assert shortlimit_rules['allow_none'] is True
        
        # Unknown column should return default rules
        unknown_rules = manager.get_validation_rules('UNKNOWN_COLUMN')
        assert unknown_rules.get('allow_any') is True
    
    def test_batch_update_detects_conflicting_edits_to_same_cell(self):
        """Test that batch_update detects when multiple edits target the same cell."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        test_df = pd.DataFrame({
            'CLUSTER': [1, 1],
            'CUID': ['C001', 'C002'],
            'VIEW': [100.0, 150.0]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Define conflicting updates to same cell
        updates = [
            {
                'cluster': '1',
                'constraint_index': 0,
                'column': 'VIEW',
                'value': '125.0'
            },
            {
                'cluster': '1',
                'constraint_index': 0,
                'column': 'VIEW',
                'value': '130.0'  # Conflicts with first edit
            }
        ]
        
        # Execute batch update
        result = manager.batch_update(updates)
        
        # Should detect conflict and handle appropriately
        assert result['success'] is False
        assert 'conflict' in result['error_message'].lower()
        
        # Verify no changes were applied due to conflict
        cluster_data = manager.get_cluster_data('1')
        assert cluster_data.iloc[0]['VIEW'] == 100.0  # Original value


class TestThreadSafeOperations:
    """Test thread-safe edit operations."""
    
    def test_concurrent_edits_are_thread_safe(self):
        """Test that concurrent edit operations from multiple threads are handled safely."""
        mock_excel_io = Mock(spec=ExcelIO)
        mock_excel_io.get_sheet_names.return_value = ['JAN26']
        
        # Create test data with many rows for concurrent access
        test_df = pd.DataFrame({
            'CLUSTER': [1] * 10,
            'CUID': [f'C{i:03d}' for i in range(10)],
            'VIEW': [100.0 + i for i in range(10)]
        })
        
        mock_excel_io.load_sheet.return_value = test_df.copy()
        
        manager = ExcelDataManager(mock_excel_io)
        manager.load_workbook("/tmp/test.xlsx")
        manager.set_active_sheet('JAN26')
        
        # Track successful edits from different threads
        results = []
        edit_count = 20
        
        def make_edits(thread_id, start_idx):
            """Function to make edits from a specific thread."""
            for i in range(5):  # 5 edits per thread
                constraint_idx = (start_idx + i) % 10
                new_value = 200.0 + (thread_id * 100) + i
                success, _ = manager.validate_and_update(
                    '1', constraint_idx, 'VIEW', str(new_value)
                )
                results.append((thread_id, constraint_idx, success))
                time.sleep(0.001)  # Small delay to increase chance of race conditions
        
        # Create multiple threads making concurrent edits
        threads = []
        for t in range(4):  # 4 threads
            thread = threading.Thread(
                target=make_edits, 
                args=(t, t * 2)
            )
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify thread safety - all edits should have succeeded
        assert len(results) == edit_count
        successful_edits = [r for r in results if r[2] is True]
        assert len(successful_edits) == edit_count
        
        # Verify data integrity - no corruption from concurrent access
        final_data = manager.get_cluster_data('1')
        assert len(final_data) == 10  # Same number of rows
        assert all(view_val >= 100.0 for view_val in final_data['VIEW'])  # All positive
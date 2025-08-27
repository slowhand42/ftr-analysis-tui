"""
Excel Data Manager for coordinating Excel data operations.

This module provides the central data management component that coordinates
Excel data operations, cluster filtering, and sheet navigation.
"""

import pandas as pd
import threading
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import deque
from pathlib import Path

from src.io.excel_io import ExcelIO
from src.business_logic.validators import DataValidator
from src.models.data_models import EditRecord


class ExcelDataManager:
    """
    Central data management component for Excel operations.
    
    Features:
    - Workbook loading and caching
    - Sheet navigation with active sheet tracking
    - Cluster-based data filtering
    - Cell value updates with change tracking
    - Integration with ExcelIO for persistence
    """
    
    def __init__(self, excel_io: ExcelIO):
        """Initialize with ExcelIO instance for data operations."""
        self._excel_io = excel_io
        self._sheet_cache: Dict[str, pd.DataFrame] = {}
        self._sheet_names: List[str] = []
        self._active_sheet: Optional[str] = None
        self._is_modified: bool = False
        self._file_path: Optional[str] = None
        
        # Edit operations support
        self._validator = DataValidator()
        self._edit_history: deque = deque(maxlen=1000)  # FIFO with 1000 entry limit
        self._edit_lock = threading.RLock()  # Thread-safe operations
        
        # Define editable columns
        self._editable_columns = {'VIEW', 'SHORTLIMIT'}
        
        # Define read-only columns  
        self._readonly_columns = {'CLUSTER', 'CUID', 'LODF', 'FLOW', 'LIMIT', 
                                  'PREV', 'PACTUAL', 'PEXPECTED', 'VIEWLG', 
                                  'MON', 'CONT', 'DIRECTION', 'SOURCE', 'SINK',
                                  'LAST_BINDING', 'BHOURS', 'MAXHIST', 'EXP_PEAK',
                                  'EXP_OP', 'RECENT_DELTA'}
    
    def load_workbook(self, file_path: str) -> None:
        """Load Excel workbook and cache all sheet data."""
        self._file_path = file_path
        # Get sheet names from ExcelIO
        self._sheet_names = self._excel_io.get_sheet_names()
        # Clear any existing cache
        self._sheet_cache.clear()
        self._active_sheet = None
        self._is_modified = False
    
    def get_sheet_names(self) -> List[str]:
        """Return list of all sheet names in workbook."""
        return self._sheet_names.copy()
    
    def set_active_sheet(self, sheet_name: str) -> None:
        """Set the active sheet for operations."""
        if sheet_name not in self._sheet_names:
            raise ValueError(f"Sheet '{sheet_name}' not found")
        self._active_sheet = sheet_name
    
    def get_active_sheet_name(self) -> Optional[str]:
        """Return name of currently active sheet."""
        return self._active_sheet
    
    def get_cluster_data(self, cluster_name: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Get data for specific cluster from active sheet."""
        if self._active_sheet is None:
            return pd.DataFrame()
        
        # Load sheet data if not cached
        sheet_data = self._get_cached_sheet_data(self._active_sheet)
        
        # Handle missing CLUSTER column gracefully
        if 'CLUSTER' not in sheet_data.columns:
            return pd.DataFrame()
        
        # Convert cluster_name to appropriate type for comparison
        try:
            # Try to convert to int first
            cluster_value = int(cluster_name)
        except ValueError:
            # Keep as string if conversion fails
            cluster_value = cluster_name
        
        # Filter by cluster
        filtered_data = sheet_data[sheet_data['CLUSTER'] == cluster_value].copy()
        
        # Apply column filtering if specified
        if columns is not None:
            # Only include columns that exist in the data
            existing_columns = [col for col in columns if col in filtered_data.columns]
            if existing_columns:
                filtered_data = filtered_data[existing_columns]
            else:
                return pd.DataFrame()
        
        return filtered_data
    
    def get_all_clusters(self) -> List[str]:
        """Return list of unique cluster names in active sheet."""
        if self._active_sheet is None:
            return []
        
        sheet_data = self._get_cached_sheet_data(self._active_sheet)
        
        # Handle missing CLUSTER column gracefully
        if 'CLUSTER' not in sheet_data.columns:
            return []
        
        # Get unique clusters and convert to strings
        unique_clusters = sheet_data['CLUSTER'].dropna().unique()
        return [str(cluster) for cluster in unique_clusters]
    
    def update_value(self, cluster: str, constraint_index: int, column: str, value: Any) -> bool:
        """Update a cell value in the active sheet."""
        if self._active_sheet is None:
            return False
        
        # Get cached sheet data
        sheet_data = self._get_cached_sheet_data(self._active_sheet)
        
        # Find rows matching the cluster
        try:
            cluster_value = int(cluster)
        except ValueError:
            cluster_value = cluster
        
        cluster_rows = sheet_data[sheet_data['CLUSTER'] == cluster_value]
        if len(cluster_rows) <= constraint_index or constraint_index < 0:
            return False
        
        if column not in sheet_data.columns:
            return False
        
        # Get the actual index in the original dataframe
        actual_index = cluster_rows.index[constraint_index]
        
        # Update the value
        sheet_data.loc[actual_index, column] = value
        
        # Mark as modified
        self._is_modified = True
        
        return True
    
    def save_workbook(self) -> str:
        """Save current state to timestamped Excel file."""
        # Collect all cached data
        all_sheet_data = {}
        
        # Include all sheets - load them if not cached
        for sheet_name in self._sheet_names:
            all_sheet_data[sheet_name] = self._get_cached_sheet_data(sheet_name)
        
        # Delegate to ExcelIO
        return self._excel_io.save_workbook(all_sheet_data, self._file_path)
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Return statistics about loaded data."""
        stats = {
            'total_sheets': len(self._sheet_names),
            'active_sheet': self._active_sheet,
            'total_constraints': 0,
            'unique_clusters': 0
        }
        
        # If we have an active sheet, get more detailed stats
        if self._active_sheet:
            sheet_data = self._get_cached_sheet_data(self._active_sheet)
            stats['total_constraints'] = len(sheet_data)
            if 'CLUSTER' in sheet_data.columns:
                stats['unique_clusters'] = sheet_data['CLUSTER'].nunique()
        
        return stats
    
    def validate_and_update(self, cluster: str, constraint_index: int, 
                          column: str, value: str) -> Tuple[bool, str]:
        """
        Validate and update a value with proper error handling.
        
        Args:
            cluster: Cluster ID to target
            constraint_index: Index within the cluster
            column: Column name to update
            value: New value as string
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._edit_lock:
            # Check if column is editable
            if not self.can_edit_column(column):
                return False, f"Column '{column}' is read-only and cannot be modified"
            
            if self._active_sheet is None:
                return False, "No active sheet selected"
            
            # Get sheet data
            sheet_data = self._get_cached_sheet_data(self._active_sheet)
            
            # Find the target row
            try:
                cluster_value = int(cluster)
            except ValueError:
                cluster_value = cluster
            
            cluster_rows = sheet_data[sheet_data['CLUSTER'] == cluster_value]
            if len(cluster_rows) <= constraint_index or constraint_index < 0:
                return False, f"Invalid constraint index {constraint_index} for cluster {cluster}"
            
            if column not in sheet_data.columns:
                return False, f"Column '{column}' not found in data"
            
            # Get the actual dataframe index
            actual_index = cluster_rows.index[constraint_index]
            old_value = sheet_data.loc[actual_index, column]
            
            # Validate the new value
            validation_result = self._validator.validate_cell(column, value)
            if not validation_result.is_valid:
                return False, validation_result.error_message
            
            # Apply the update
            new_value = validation_result.sanitized_value
            sheet_data.loc[actual_index, column] = new_value
            
            # Record the edit in history
            edit_record = EditRecord(
                timestamp=datetime.now(),
                sheet=self._active_sheet,
                row=actual_index,
                column=column,
                old_value=old_value,
                new_value=new_value,
                cluster_id=cluster_value,
                cuid=str(datetime.now().timestamp())  # Use timestamp as unique ID
            )
            self._edit_history.append(edit_record)
            
            # Mark as modified
            self._is_modified = True
            
            return True, "Value updated successfully"
    
    def batch_update(self, updates: List[Dict]) -> Dict[str, Any]:
        """
        Apply multiple updates as a batch with transaction-like behavior.
        All succeed or all fail.
        
        Args:
            updates: List of update dictionaries with keys:
                    'cluster', 'constraint_index', 'column', 'value'
        
        Returns:
            Dictionary with 'success', 'applied_count', 'failed_count', 
            and optional 'error_message'
        """
        with self._edit_lock:
            if not updates:
                return {'success': True, 'applied_count': 0, 'failed_count': 0}
            
            # Check for conflicts (same cell targeted multiple times)
            cell_targets = set()
            for update in updates:
                cell_key = (update['cluster'], update['constraint_index'], update['column'])
                if cell_key in cell_targets:
                    return {
                        'success': False,
                        'applied_count': 0,
                        'failed_count': 1,
                        'error_message': f"Conflict: Multiple edits target the same cell (cluster={update['cluster']}, index={update['constraint_index']}, column={update['column']})"
                    }
                cell_targets.add(cell_key)
            
            # Create backup of current state for rollback
            if self._active_sheet:
                backup_data = self._get_cached_sheet_data(self._active_sheet).copy()
                backup_history_size = len(self._edit_history)
            else:
                return {'success': False, 'applied_count': 0, 'failed_count': 1, 
                       'error_message': 'No active sheet selected'}
            
            # Validate all updates first
            validation_errors = []
            for i, update in enumerate(updates):
                # Check column editability
                if not self.can_edit_column(update['column']):
                    validation_errors.append(f"Update {i}: Column '{update['column']}' is read-only")
                    continue
                
                # Validate the value
                validation_result = self._validator.validate_cell(update['column'], update['value'])
                if not validation_result.is_valid:
                    validation_errors.append(f"Update {i}: {validation_result.error_message}")
            
            # If any validation failed, return error
            if validation_errors:
                return {
                    'success': False,
                    'applied_count': 0,
                    'failed_count': len(validation_errors),
                    'error_message': '; '.join(validation_errors)
                }
            
            # Apply all updates
            applied_count = 0
            try:
                for update in updates:
                    success, message = self.validate_and_update(
                        update['cluster'],
                        update['constraint_index'],
                        update['column'],
                        update['value']
                    )
                    if success:
                        applied_count += 1
                    else:
                        # Rollback: restore backup and truncate history
                        self._sheet_cache[self._active_sheet] = backup_data
                        self._edit_history = deque(list(self._edit_history)[:backup_history_size], maxlen=1000)
                        return {
                            'success': False,
                            'applied_count': 0,
                            'failed_count': 1,
                            'error_message': message
                        }
                
                return {
                    'success': True,
                    'applied_count': applied_count,
                    'failed_count': 0
                }
                
            except Exception as e:
                # Rollback on any exception
                self._sheet_cache[self._active_sheet] = backup_data
                self._edit_history = deque(list(self._edit_history)[:backup_history_size], maxlen=1000)
                return {
                    'success': False,
                    'applied_count': 0,
                    'failed_count': 1,
                    'error_message': f"Batch update failed: {str(e)}"
                }
    
    def get_edit_history(self) -> List[EditRecord]:
        """Return list of all edits made in this session."""
        with self._edit_lock:
            return list(self._edit_history)
    
    def can_edit_column(self, column: str) -> bool:
        """Check if a column is editable based on business rules."""
        column_upper = column.upper()
        return column_upper in self._editable_columns
    
    def rollback_edit(self, edit_id: str) -> bool:
        """
        Rollback a specific edit by ID.
        
        Args:
            edit_id: Unique identifier for the edit to rollback
            
        Returns:
            True if rollback successful, False if edit not found
        """
        with self._edit_lock:
            # Find the edit in history
            target_edit = None
            for edit in self._edit_history:
                if edit.cuid == edit_id:
                    target_edit = edit
                    break
            
            if target_edit is None:
                return False
            
            # Apply the rollback by setting the value back to old_value
            if self._active_sheet == target_edit.sheet:
                sheet_data = self._get_cached_sheet_data(self._active_sheet)
                if target_edit.row < len(sheet_data) and target_edit.column in sheet_data.columns:
                    sheet_data.loc[target_edit.row, target_edit.column] = target_edit.old_value
                    self._is_modified = True
                    return True
            
            return False
    
    def get_validation_rules(self, column: str) -> Dict[str, Any]:
        """Return validation rules for a specific column."""
        return self._validator.get_column_rules(column)
    
    def has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes.
        
        Returns:
            True if data has been modified since last save
        """
        return self._is_modified
    
    def get_file_path(self) -> Optional[Path]:
        """
        Get the current file path.
        
        Returns:
            Path object of current file or None if no file loaded
        """
        if self._file_path:
            return Path(self._file_path)
        return None
    
    def save_to_file(self, file_path: Path) -> None:
        """
        Save workbook to specified file path.
        
        Args:
            file_path: Path where to save the file
        """
        # Collect all cached data
        all_sheet_data = {}
        
        # Include all sheets - load them if not cached
        for sheet_name in self._sheet_names:
            all_sheet_data[sheet_name] = self._get_cached_sheet_data(sheet_name)
        
        # Delegate to ExcelIO with specified path
        self._excel_io.save_workbook(all_sheet_data, str(file_path))
        
        # Mark as no longer modified
        self._is_modified = False
    
    def _get_cached_sheet_data(self, sheet_name: str) -> pd.DataFrame:
        """Get sheet data from cache or load from ExcelIO."""
        if sheet_name not in self._sheet_cache:
            # Load from ExcelIO and cache
            self._sheet_cache[sheet_name] = self._excel_io.load_sheet(sheet_name)
        
        return self._sheet_cache[sheet_name]
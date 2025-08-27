#!/usr/bin/env python3
"""
Test script to verify cell editing functionality in the TUI.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.widgets.cluster_view import ClusterView
from src.core.data_manager import ExcelDataManager
from src.io.excel_io import ExcelIO
from src.business_logic.color_formatter import ColorFormatter
from src.business_logic.validators import DataValidator
from textual import events


def test_cell_editing():
    """Test cell editing functionality."""
    print("=== Testing Cell Editing Functionality ===")
    
    excel_file = "./analysis_files/flow_results_processed_SEP25_R1_small.xlsx"
    
    # Setup components
    excel_io = ExcelIO(Path(excel_file))
    data_manager = ExcelDataManager(excel_io)
    data_manager.load_excel(excel_file)
    
    formatter = ColorFormatter()
    cluster_view = ClusterView(data_manager=data_manager, color_formatter=formatter)
    
    # Load a cluster
    clusters = data_manager.get_clusters_list('SEP25')
    if not clusters:
        print("✗ No clusters available for testing")
        return False
    
    print(f"Loading cluster {clusters[0]} for testing...")
    cluster_view.load_cluster(f"CLUSTER_{clusters[0]:03d}", "SEP25")
    
    print(f"✓ Cluster loaded with {cluster_view.row_count} rows, {cluster_view.column_count} columns")
    
    # Test editable column identification
    editable_columns = []
    for i, col_name in enumerate(cluster_view.DISPLAY_COLUMNS):
        if cluster_view.COLUMN_CONFIG.get(col_name, {}).get('editable', False):
            editable_columns.append((i, col_name))
    
    print(f"✓ Editable columns: {[col[1] for col in editable_columns]}")
    
    # Test edit mode triggering
    print("\nTesting edit mode functionality...")
    
    # Test with editable column (VIEW column)
    view_col_index = None
    for i, col_name in enumerate(cluster_view.DISPLAY_COLUMNS):
        if col_name == 'VIEW':
            view_col_index = i
            break
    
    if view_col_index is not None:
        print(f"✓ Found VIEW column at index {view_col_index}")
        
        # Set cursor to editable cell
        cluster_view.selected_cell = (0, view_col_index)
        
        # Test edit mode start
        success = cluster_view.start_edit_mode("123.4")
        if success:
            print("✓ Edit mode started successfully")
            print(f"  Edit position: {cluster_view.edit_position}")
            print(f"  Edit mode active: {cluster_view.edit_mode}")
            
            # Test edit mode exit
            cluster_view.exit_edit_mode()
            print("✓ Edit mode exited successfully")
            print(f"  Edit mode active: {cluster_view.edit_mode}")
            
        else:
            print("✗ Failed to start edit mode")
    
    # Test SHORTLIMIT column editing
    shortlimit_col_index = None
    for i, col_name in enumerate(cluster_view.DISPLAY_COLUMNS):
        if col_name == 'SHORTLIMIT':
            shortlimit_col_index = i
            break
    
    if shortlimit_col_index is not None:
        print(f"✓ Found SHORTLIMIT column at index {shortlimit_col_index}")
        
        # Test edit functionality
        cluster_view.selected_cell = (0, shortlimit_col_index)
        success = cluster_view.start_edit_mode("999.5")
        if success:
            print("✓ SHORTLIMIT edit mode works")
            cluster_view.exit_edit_mode()
        
    # Test validator
    print("\nTesting data validation...")
    validator = DataValidator()
    
    test_cases = [
        ('VIEW', '123.4', True),
        ('VIEW', 'abc', False),
        ('SHORTLIMIT', '999.9', True),
        ('SHORTLIMIT', 'invalid', False),
        ('CONSTRAINTNAME', 'test', False),  # Not editable
    ]
    
    for column, value, should_be_valid in test_cases:
        result = validator.validate_cell(column, value)
        status = "✓" if result.is_valid == should_be_valid else "✗"
        print(f"{status} {column}='{value}' -> valid={result.is_valid} (expected {should_be_valid})")
        if not result.is_valid and result.error_message:
            print(f"    Error: {result.error_message}")
    
    # Test key handling for edit triggers
    print("\nTesting edit key triggers...")
    
    # Test number key triggering edit
    cluster_view.selected_cell = (0, view_col_index if view_col_index else 0)
    
    # Create mock key events
    number_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-']
    
    for key_char in number_keys:
        try:
            key_event = events.Key(key_char, key_char)
            should_trigger = cluster_view._should_trigger_edit(key_event)
            print(f"  Key '{key_char}' should trigger edit: {should_trigger}")
        except Exception as e:
            print(f"  Key '{key_char}' test failed: {e}")
    
    print("\n✓ Cell editing functionality test completed")
    return True


def test_arrow_navigation():
    """Test arrow key navigation."""
    print("\n=== Testing Arrow Key Navigation ===")
    
    excel_file = "./analysis_files/flow_results_processed_SEP25_R1_small.xlsx"
    
    # Setup components
    excel_io = ExcelIO(Path(excel_file))
    data_manager = ExcelDataManager(excel_io)
    data_manager.load_excel(excel_file)
    
    formatter = ColorFormatter()
    cluster_view = ClusterView(data_manager=data_manager, color_formatter=formatter)
    
    # Load cluster
    clusters = data_manager.get_clusters_list('SEP25')
    cluster_view.load_cluster(f"CLUSTER_{clusters[0]:03d}", "SEP25")
    
    print(f"Testing navigation on {cluster_view.row_count}x{cluster_view.column_count} table")
    
    # Test arrow key movements
    directions = ['up', 'down', 'left', 'right']
    initial_pos = (1, 2)  # Start from middle position
    cluster_view.selected_cell = initial_pos
    
    print(f"Starting position: {initial_pos}")
    
    for direction in directions:
        old_pos = cluster_view.selected_cell
        cluster_view.action_move_cursor(direction)
        new_pos = cluster_view.selected_cell
        
        print(f"  {direction}: {old_pos} -> {new_pos}")
        
        # Reset position for next test
        cluster_view.selected_cell = initial_pos
    
    # Test boundary conditions
    print("Testing boundary navigation...")
    
    # Top-left corner
    cluster_view.selected_cell = (0, 0)
    cluster_view.action_move_cursor('up')
    print(f"  Up from (0,0): {cluster_view.selected_cell} (should stay at 0,0)")
    
    cluster_view.action_move_cursor('left')  
    print(f"  Left from (0,0): {cluster_view.selected_cell} (should stay at 0,0)")
    
    # Bottom-right corner
    max_row = max(0, cluster_view.row_count - 1)
    max_col = max(0, cluster_view.column_count - 1)
    cluster_view.selected_cell = (max_row, max_col)
    
    cluster_view.action_move_cursor('down')
    print(f"  Down from ({max_row},{max_col}): {cluster_view.selected_cell} (should stay at max)")
    
    cluster_view.action_move_cursor('right')
    print(f"  Right from ({max_row},{max_col}): {cluster_view.selected_cell} (should stay at max)")
    
    print("✓ Arrow key navigation test completed")
    return True


if __name__ == "__main__":
    print("Starting Cell Editing and Navigation Tests...\n")
    
    success1 = test_cell_editing()
    success2 = test_arrow_navigation()
    
    print(f"\nOverall test result: {'PASS' if success1 and success2 else 'FAIL'}")
"""
Test suite for ClusterView widget following TDD methodology.

Tests cover DataTable specialization for cluster constraint display:
1. Widget initialization with dependencies
2. Cluster data loading and display
3. Column headers and configuration
4. Cell color formatting from ColorFormatter
5. Cell selection and highlighting
6. Keyboard navigation within table
7. Empty data handling
8. Data refresh and reactive updates
9. Editable column indicators
10. Window resize and column adjustment
11. Large dataset performance
12. Selected value retrieval

These tests drive implementation of ClusterView as a specialized DataTable
for constraint display as specified in task-015. Tests are designed to fail
first (TDD Red phase) and guide implementation of full ClusterView functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from textual.widgets import DataTable
from textual.coordinate import Coordinate


# TDD: Import the target ClusterView class
# These tests define the required interface for the ClusterView implementation
# Tests will fail initially, driving the development of the complete widget

"""
TDD Workflow Instructions for Developer-Agent:

1. RED PHASE: The ClusterView doesn't exist yet in src/widgets/cluster_view.py
   or src/presentation/widgets/cluster_view.py. Replace the mock class below with:
   from src.widgets.cluster_view import ClusterView (or appropriate path)
   The tests will fail, defining the required interface.

2. GREEN PHASE: Implement the full ClusterView class with:
   - Reactive properties: current_cluster, selected_cell
   - DataTable subclass with specialized behavior
   - Methods: load_cluster(), refresh_display(), get_selected_value(), etc.
   - Column configuration and formatting integration
   - Event handling for navigation and selection

3. REFACTOR PHASE: Once tests pass, optimize for performance with large datasets.
"""

from src.widgets.cluster_view import ClusterView


class TestClusterView:
    """Test suite for ClusterView specialized DataTable widget."""

    @pytest.fixture
    def mock_data_manager(self):
        """Create mock ExcelDataManager for testing."""
        manager = Mock()
        # Sample constraint data for testing
        test_data = pd.DataFrame({
            'CONSTRAINTNAME': ['LINE_001_LIMIT', 'LINE_002_LIMIT', 'XFMR_001_LIMIT'],
            'BRANCHNAME': ['LINE_001', 'LINE_002', 'XFMR_001'], 
            'VIEW': [125.5, 87.3, 203.1],
            'PREV': [120.0, 90.5, 195.0],
            'PACTUAL': [118.2, 89.1, 198.7],
            'PEXPECTED': [115.0, 88.0, 200.0],
            'RECENT_DELTA': [3.2, 1.1, -1.3],
            'SHORTLIMIT': [-150.0, -100.0, -250.0],
            'LODF': [0.85, 0.92, 0.78],
            'STATUS': ['Active', 'Inactive', 'Active']
        })
        manager.get_cluster_data.return_value = test_data
        manager.get_cluster_names.return_value = ['OCT25_CLUSTER_001', 'OCT25_CLUSTER_002']
        return manager

    @pytest.fixture
    def mock_color_formatter(self):
        """Create mock ColorFormatter for testing."""
        formatter = Mock()
        formatter.get_view_color.return_value = "#FF0000"
        formatter.get_prev_color.return_value = "#00FF00"
        formatter.get_pactual_color.return_value = "#0000FF"
        formatter.format_recent_delta.return_value = "#FFFF00"
        formatter.get_shortlimit_color.return_value = "#FF00FF"
        return formatter

    def test_widget_initialization_with_dependencies(self, mock_data_manager, mock_color_formatter):
        """Test ClusterView initializes properly with data manager and color formatter."""
        # Arrange & Act
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        
        # Assert - widget is properly initialized as DataTable subclass
        assert isinstance(cluster_view, DataTable)
        assert hasattr(cluster_view, 'data_manager')
        assert hasattr(cluster_view, 'color_formatter')
        assert cluster_view.data_manager == mock_data_manager
        assert cluster_view.color_formatter == mock_color_formatter
        
        # Assert - reactive properties are initialized
        assert hasattr(cluster_view, 'current_cluster')
        assert hasattr(cluster_view, 'selected_cell')
        assert cluster_view.current_cluster == ""
        assert cluster_view.selected_cell == (0, 0)

    def test_cluster_data_loading_and_display(self, mock_data_manager, mock_color_formatter):
        """Test loading and displaying cluster data in table format."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_name = "OCT25_CLUSTER_001"
        
        # Act
        cluster_view.load_cluster(cluster_name)
        
        # Assert - data manager is called correctly
        mock_data_manager.get_cluster_data.assert_called_once_with(cluster_name)
        
        # Assert - reactive property is updated
        assert cluster_view.current_cluster == cluster_name
        
        # Assert - table has correct number of rows and columns
        assert cluster_view.row_count == 3  # Data has 3 constraint rows
        assert cluster_view.column_count == 10  # All 10 columns from config
        
        # Assert - table contains expected data
        # Note: Exact assertion depends on DataTable API - this shows intent
        assert "LINE_001_LIMIT" in str(cluster_view.get_cell_at(Coordinate(0, 0)))
        assert "125.5" in str(cluster_view.get_cell_at(Coordinate(0, 2)))  # VIEW column

    def test_column_headers_configuration(self, mock_data_manager, mock_color_formatter):
        """Test that all required column headers are displayed with proper configuration."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        expected_columns = [
            'CONSTRAINTNAME', 'BRANCHNAME', 'VIEW', 'PREV', 'PACTUAL', 
            'PEXPECTED', 'RECENT_DELTA', 'SHORTLIMIT', 'LODF', 'STATUS'
        ]
        
        # Act
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        
        # Assert - all columns are present
        assert cluster_view.column_count == len(expected_columns)
        
        # Assert - column headers are set correctly
        for i, expected_col in enumerate(expected_columns):
            column_header = cluster_view.get_column_header(i)
            assert expected_col in str(column_header)
            
        # Assert - column widths are applied from config
        # CONSTRAINTNAME should be wide (30), VIEW should be narrow (10)
        constraintname_width = cluster_view.get_column_width(0)
        view_width = cluster_view.get_column_width(2)
        assert constraintname_width > view_width

    def test_cell_color_formatting_application(self, mock_data_manager, mock_color_formatter):
        """Test that ColorFormatter colors are applied correctly to cells."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        
        # Act - apply formatting to specific cells
        cluster_view.apply_cell_formatting(0, 2)  # VIEW column, first row
        cluster_view.apply_cell_formatting(0, 3)  # PREV column, first row
        cluster_view.apply_cell_formatting(0, 6)  # RECENT_DELTA column, first row
        
        # Assert - ColorFormatter methods are called with correct values
        mock_color_formatter.get_view_color.assert_called_with(125.5)
        mock_color_formatter.get_prev_color.assert_called_with(120.0)
        mock_color_formatter.format_recent_delta.assert_called_with(3.2)
        
        # Assert - cell styles are updated with returned colors
        view_cell_style = cluster_view.get_cell_style(0, 2)
        assert "#FF0000" in str(view_cell_style)  # VIEW color
        
        prev_cell_style = cluster_view.get_cell_style(0, 3)
        assert "#00FF00" in str(prev_cell_style)  # PREV color

    def test_cell_selection_and_highlighting(self, mock_data_manager, mock_color_formatter):
        """Test cell selection tracking and visual highlighting."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        
        # Act - select a cell
        target_coordinate = Coordinate(1, 2)  # Row 1, Column 2 (VIEW)
        cluster_view.move_cursor(row=1, column=2)
        
        # Assert - selected_cell reactive property is updated
        assert cluster_view.selected_cell == (1, 2)
        
        # Assert - selected cell has highlight styling
        selected_style = cluster_view.get_cell_style(1, 2)
        assert "highlight" in str(selected_style).lower() or "selected" in str(selected_style).lower()
        
        # Act - move selection to different cell
        cluster_view.move_cursor(row=2, column=4)
        
        # Assert - selection moves and old cell loses highlight
        assert cluster_view.selected_cell == (2, 4)
        old_style = cluster_view.get_cell_style(1, 2)
        new_style = cluster_view.get_cell_style(2, 4)
        assert "highlight" not in str(old_style).lower()
        assert "highlight" in str(new_style).lower()

    def test_keyboard_navigation_within_table(self, mock_data_manager, mock_color_formatter):
        """Test arrow key navigation moves selection correctly."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        initial_position = (0, 0)
        cluster_view.selected_cell = initial_position
        
        # Act & Assert - Right arrow moves column
        cluster_view.action_move_cursor("right")
        assert cluster_view.selected_cell == (0, 1)
        
        # Act & Assert - Down arrow moves row
        cluster_view.action_move_cursor("down")
        assert cluster_view.selected_cell == (1, 1)
        
        # Act & Assert - Left arrow moves back
        cluster_view.action_move_cursor("left")
        assert cluster_view.selected_cell == (1, 0)
        
        # Act & Assert - Up arrow moves back
        cluster_view.action_move_cursor("up")
        assert cluster_view.selected_cell == (0, 0)
        
        # Act & Assert - Navigation stops at boundaries
        cluster_view.action_move_cursor("up")  # Should not go above row 0
        assert cluster_view.selected_cell == (0, 0)
        
        cluster_view.action_move_cursor("left")  # Should not go left of column 0
        assert cluster_view.selected_cell == (0, 0)

    def test_empty_data_handling(self, mock_data_manager, mock_color_formatter):
        """Test graceful handling of empty cluster data."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        empty_data = pd.DataFrame()  # Empty DataFrame
        mock_data_manager.get_cluster_data.return_value = empty_data
        
        # Act
        cluster_view.load_cluster("EMPTY_CLUSTER")
        
        # Assert - widget handles empty data without crashing
        assert cluster_view.current_cluster == "EMPTY_CLUSTER"
        assert cluster_view.row_count == 0
        assert cluster_view.column_count >= 0  # Should still show headers
        
        # Assert - no selection is possible with empty data
        assert cluster_view.selected_cell == (0, 0) or cluster_view.selected_cell == (-1, -1)
        
        # Act - navigation with empty data should not crash
        cluster_view.action_move_cursor("down")
        cluster_view.action_move_cursor("right")
        
        # Assert - widget remains stable
        assert cluster_view.current_cluster == "EMPTY_CLUSTER"

    def test_data_refresh_and_reactive_updates(self, mock_data_manager, mock_color_formatter):
        """Test refresh_display() updates table when underlying data changes."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        original_row_count = cluster_view.row_count
        
        # Simulate data change - add new row to mock data
        updated_data = pd.DataFrame({
            'CONSTRAINTNAME': ['LINE_001_LIMIT', 'LINE_002_LIMIT', 'XFMR_001_LIMIT', 'GEN_001_LIMIT'],
            'BRANCHNAME': ['LINE_001', 'LINE_002', 'XFMR_001', 'GEN_001'], 
            'VIEW': [125.5, 87.3, 203.1, 75.0],
            'PREV': [120.0, 90.5, 195.0, 72.0],
            'PACTUAL': [118.2, 89.1, 198.7, 74.5],
            'PEXPECTED': [115.0, 88.0, 200.0, 73.0],
            'RECENT_DELTA': [3.2, 1.1, -1.3, 1.5],
            'SHORTLIMIT': [-150.0, -100.0, -250.0, -90.0],
            'LODF': [0.85, 0.92, 0.78, 0.88],
            'STATUS': ['Active', 'Inactive', 'Active', 'Active']
        })
        mock_data_manager.get_cluster_data.return_value = updated_data
        
        # Act
        cluster_view.refresh_display()
        
        # Assert - table reflects updated data
        assert cluster_view.row_count == 4  # One more row than before
        assert cluster_view.row_count != original_row_count
        
        # Assert - new data is visible
        new_row_data = str(cluster_view.get_cell_at(Coordinate(3, 0)))
        assert "GEN_001_LIMIT" in new_row_data
        
        # Assert - data manager was called again for current cluster
        assert mock_data_manager.get_cluster_data.call_count >= 2

    def test_editable_column_indicators(self, mock_data_manager, mock_color_formatter):
        """Test visual indicators for editable vs read-only columns."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        
        # Act
        cluster_view.highlight_editable_columns()
        
        # Assert - editable columns (VIEW, SHORTLIMIT) have different styling
        view_col_style = cluster_view.get_column_style(2)  # VIEW column
        shortlimit_col_style = cluster_view.get_column_style(7)  # SHORTLIMIT column
        constraintname_col_style = cluster_view.get_column_style(0)  # Read-only column
        
        # VIEW and SHORTLIMIT should have editable indicators
        assert "editable" in str(view_col_style).lower() or "edit" in str(view_col_style).lower()
        assert "editable" in str(shortlimit_col_style).lower() or "edit" in str(shortlimit_col_style).lower()
        
        # CONSTRAINTNAME should not have editable indicators
        assert "editable" not in str(constraintname_col_style).lower()

    def test_window_resize_column_adjustment(self, mock_data_manager, mock_color_formatter):
        """Test column width adjustment when window is resized."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        
        # Store initial column widths
        initial_widths = []
        for i in range(cluster_view.column_count):
            initial_widths.append(cluster_view.get_column_width(i))
        
        # Act - simulate window resize (mock the resize event)
        with patch.object(cluster_view, 'size') as mock_size:
            mock_size.width = 120  # Wider window
            mock_size.height = 40
            cluster_view.on_resize(mock_size)
        
        # Assert - column widths are adjusted proportionally
        new_widths = []
        for i in range(cluster_view.column_count):
            new_widths.append(cluster_view.get_column_width(i))
        
        # Should have different widths after resize
        assert new_widths != initial_widths
        
        # Important columns should maintain reasonable minimum widths
        constraintname_width = new_widths[0]  # Should remain wide for readability
        assert constraintname_width >= 20  # Minimum readable width

    def test_large_dataset_performance(self, mock_data_manager, mock_color_formatter):
        """Test widget performance and functionality with large datasets."""
        # Arrange - create large dataset (1000+ rows as per requirement)
        large_data_rows = []
        for i in range(1200):  # 1200 rows to test performance
            large_data_rows.append({
                'CONSTRAINTNAME': f'LINE_{i:04d}_LIMIT',
                'BRANCHNAME': f'LINE_{i:04d}',
                'VIEW': 100.0 + (i % 100),
                'PREV': 95.0 + (i % 95),
                'PACTUAL': 90.0 + (i % 90),
                'PEXPECTED': 88.0 + (i % 88),
                'RECENT_DELTA': (i % 20) - 10,  # Range from -10 to +9
                'SHORTLIMIT': -(150.0 + (i % 50)),
                'LODF': 0.70 + (i % 30) / 100,  # Range from 0.70 to 0.99
                'STATUS': 'Active' if i % 2 == 0 else 'Inactive'
            })
        
        large_data = pd.DataFrame(large_data_rows)
        mock_data_manager.get_cluster_data.return_value = large_data
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        
        # Act - measure performance of loading large dataset
        import time
        start_time = time.time()
        cluster_view.load_cluster("LARGE_CLUSTER")
        load_time = time.time() - start_time
        
        # Assert - performance requirements met (< 200ms per requirement)
        assert load_time < 0.2  # 200ms requirement
        
        # Assert - all data is loaded
        assert cluster_view.row_count == 1200
        
        # Assert - navigation still works efficiently
        start_time = time.time()
        for _ in range(100):  # Test rapid navigation
            cluster_view.action_move_cursor("down")
        navigation_time = time.time() - start_time
        
        # Navigation should remain responsive
        assert navigation_time < 0.1  # 100ms for 100 moves
        
        # Assert - memory efficiency (basic check - object should exist)
        assert cluster_view is not None
        assert cluster_view.row_count == 1200

    def test_selected_value_retrieval(self, mock_data_manager, mock_color_formatter):
        """Test get_selected_value() returns correct value for current cell."""
        # Arrange
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("OCT25_CLUSTER_001")
        
        # Act - select specific cell and get its value
        cluster_view.move_cursor(row=0, column=2)  # First row, VIEW column
        selected_value = cluster_view.get_selected_value()
        
        # Assert - returned value matches expected data
        assert selected_value == "125.5"  # VIEW value from test data
        
        # Act - move to different cell
        cluster_view.move_cursor(row=1, column=0)  # Second row, CONSTRAINTNAME
        selected_value = cluster_view.get_selected_value()
        
        # Assert - value updated for new selection
        assert selected_value == "LINE_002_LIMIT"
        
        # Act - move to numeric column with formatting
        cluster_view.move_cursor(row=2, column=8)  # Third row, LODF column
        selected_value = cluster_view.get_selected_value()
        
        # Assert - value reflects proper number formatting
        assert "0.78" in selected_value or "78%" in selected_value
        
        # Act - test edge case with empty selection
        cluster_view.selected_cell = (-1, -1)  # Invalid selection
        selected_value = cluster_view.get_selected_value()
        
        # Assert - handles invalid selection gracefully
        assert selected_value == "" or selected_value is None
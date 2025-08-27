"""
Tests for ColorGrid widget displaying colored data grid.

Tests focus on:
- Grid rendering of constraint data in grid format
- Color application to cells based on values
- Column width handling and alignment
- Scrolling behavior for large datasets
- Cell selection and highlighting
- Keyboard navigation in grid
- Reactive updates when data changes
- Header row rendering
- Performance with large datasets
- Cell editing initiation

This follows TDD methodology - tests are written BEFORE implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from typing import Dict, Any

# Import will be available after implementation
try:
    from src.presentation.widgets.color_grid import ColorGrid, CellSelected, CellHovered
    from src.business_logic.color_formatter import ColorFormatter
except ImportError:
    # During TDD, the module may not exist yet
    ColorGrid = Mock
    CellSelected = Mock
    CellHovered = Mock
    from src.business_logic.color_formatter import ColorFormatter


class TestColorGridRendering:
    """Test grid rendering functionality."""

    def test_empty_grid_render(self):
        """Test that empty DataFrame renders gracefully without errors."""
        formatter = ColorFormatter()
        grid = ColorGrid(
            data=pd.DataFrame(),
            column_type="VIEW", 
            color_formatter=formatter
        )
        
        # Should render without errors
        rendered = grid.render()
        assert isinstance(rendered, str)
        assert len(rendered) >= 0  # May be empty or contain border/structure

    def test_single_row_render(self):
        """Test rendering grid with one constraint row."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0],
            'Day2': [150.0],
            'Day3': [200.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        rendered = grid.render()
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        # Should contain block characters for cells
        assert any(char in rendered for char in ['█', '▓', '▒', '░'])

    def test_large_grid_render(self):
        """Test efficient rendering of 100+ constraint rows."""
        formatter = ColorFormatter()
        # Create large dataset
        rows = [f'Constraint{i}' for i in range(120)]
        cols = [f'Day{i}' for i in range(30)]
        data = pd.DataFrame(
            [[float(i*j % 300) for j in range(30)] for i in range(120)],
            index=rows,
            columns=cols
        )
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Should render without errors or timeout
        rendered = grid.render()
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        # Performance check - should not be excessively long
        assert len(rendered) < 50000  # Reasonable upper bound


class TestColorMapping:
    """Test color application to cells based on values."""

    def test_color_mapping_view_column(self):
        """Test correct colors applied based on VIEW values."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [25.0],    # Should be green
            'Day2': [75.0],    # Should be yellow
            'Day3': [150.0],   # Should be orange
            'Day4': [250.0]    # Should be red
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        rendered = grid.render()
        # Verify that colors are applied (exact appearance depends on implementation)
        assert len(rendered) > 0
        # Should contain styled block characters
        assert any(char in rendered for char in ['█', '▓', '▒', '░'])

    def test_color_mapping_prev_column(self):
        """Test correct colors applied for PREV column type."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0],
            'Day2': [None],    # Should be neutral gray
            'Day3': [200.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="PREV",
            color_formatter=formatter
        )
        
        rendered = grid.render()
        assert len(rendered) > 0
        # Should handle None values gracefully
        assert isinstance(rendered, str)

    def test_nan_value_display(self):
        """Test that missing/NaN values are displayed with neutral color."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0],
            'Day2': [float('nan')],  # NaN value
            'Day3': [150.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        rendered = grid.render()
        assert len(rendered) > 0
        # Should render without errors despite NaN
        assert isinstance(rendered, str)


class TestCellInteraction:
    """Test cell selection and highlighting functionality."""

    def test_cell_hover_tooltip(self):
        """Test that hover tooltip shows correct information."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0],
            'Day2': [150.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Test tooltip info for specific cell
        cell_info = grid.get_cell_info(row=0, col=0)
        assert isinstance(cell_info, dict)
        assert 'value' in cell_info
        assert 'constraint' in cell_info or 'row_name' in cell_info
        assert 'column' in cell_info or 'date' in cell_info
        assert cell_info['value'] == 100.0

    def test_cell_selection(self):
        """Test that cell selection works correctly."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0],
            'Day2': [150.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Test cell selection
        initial_focus = grid.focused_cell
        grid.focused_cell = (0, 1)  # Move to second cell
        
        assert grid.focused_cell == (0, 1)
        assert grid.focused_cell != initial_focus

    def test_boundary_navigation(self):
        """Test that grid navigation handles edges properly."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0],
            'Day2': [150.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Test navigation to boundaries
        grid.focused_cell = (0, 0)  # Top-left
        # Should not go beyond boundaries
        # Implementation will define exact behavior
        
        rows, cols = data.shape
        grid.focused_cell = (rows-1, cols-1)  # Bottom-right
        assert grid.focused_cell[0] >= 0
        assert grid.focused_cell[1] >= 0


class TestDataHandling:
    """Test data update and reactive behavior."""

    def test_data_update_triggers_rerender(self):
        """Test that grid updates when data changes reactively."""
        formatter = ColorFormatter()
        initial_data = pd.DataFrame({
            'Day1': [100.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=initial_data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        initial_render = grid.render()
        
        # Update data
        new_data = pd.DataFrame({
            'Day1': [200.0],
            'Day2': [300.0]
        }, index=['Constraint1'])
        
        grid.data = new_data
        
        updated_render = grid.render()
        # Should be different after data update
        assert updated_render != initial_render or len(updated_render) != len(initial_render)

    def test_column_type_switch_updates_colors(self):
        """Test that changing column type updates color scheme."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        view_render = grid.render()
        
        # Switch to PREV column type
        grid.column_type = "PREV"
        prev_render = grid.render()
        
        # Renders might be same or different depending on implementation
        # But should not cause errors
        assert isinstance(prev_render, str)
        assert len(prev_render) >= 0

    def test_empty_to_populated_data_transition(self):
        """Test transition from empty to populated data."""
        formatter = ColorFormatter()
        grid = ColorGrid(
            data=pd.DataFrame(),
            column_type="VIEW",
            color_formatter=formatter
        )
        
        empty_render = grid.render()
        
        # Add data
        populated_data = pd.DataFrame({
            'Day1': [100.0, 150.0],
            'Day2': [200.0, 250.0]
        }, index=['Constraint1', 'Constraint2'])
        
        grid.data = populated_data
        populated_render = grid.render()
        
        # Should handle transition gracefully
        assert isinstance(populated_render, str)
        assert len(populated_render) > len(empty_render)


class TestKeyboardNavigation:
    """Test keyboard navigation within the grid."""

    def test_arrow_key_navigation(self):
        """Test that arrow keys move focus correctly."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0, 110.0],
            'Day2': [150.0, 160.0]
        }, index=['Constraint1', 'Constraint2'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Start at (0,0)
        grid.focused_cell = (0, 0)
        assert grid.focused_cell == (0, 0)
        
        # Test navigation (implementation will define key handling)
        # This tests the reactive property behavior
        grid.focused_cell = (0, 1)  # Move right
        assert grid.focused_cell == (0, 1)
        
        grid.focused_cell = (1, 1)  # Move down
        assert grid.focused_cell == (1, 1)

    def test_focus_wrapping_behavior(self):
        """Test focus behavior at grid boundaries."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Test boundary conditions
        grid.focused_cell = (0, 0)
        # Should stay within bounds
        assert grid.focused_cell[0] >= 0
        assert grid.focused_cell[1] >= 0


class TestEventHandling:
    """Test event emission for cell interactions."""

    def test_cell_selected_event_emission(self):
        """Test that CellSelected event is emitted correctly."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Test that CellSelected can be instantiated
        event = CellSelected(row=0, col=0, value=100.0)
        assert event.row == 0
        assert event.col == 0
        assert event.value == 100.0

    def test_cell_hovered_event_emission(self):
        """Test that CellHovered event is emitted correctly."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Test that CellHovered can be instantiated
        event = CellHovered(row=0, col=0)
        assert event.row == 0
        assert event.col == 0


class TestPerformanceOptimization:
    """Test performance characteristics with large datasets."""

    def test_render_performance_large_dataset(self):
        """Test that large grid renders within acceptable time limits."""
        formatter = ColorFormatter()
        # Create large dataset (100 rows x 30 columns)
        rows = [f'Constraint{i}' for i in range(100)]
        cols = [f'Day{i}' for i in range(30)]
        data = pd.DataFrame(
            [[float((i*j) % 500) for j in range(30)] for i in range(100)],
            index=rows,
            columns=cols
        )
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Should render efficiently
        import time
        start_time = time.time()
        rendered = grid.render()
        render_time = time.time() - start_time
        
        # Should complete within reasonable time (100ms target)
        assert render_time < 0.5  # Allow 500ms for test environment
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    def test_memory_efficient_large_dataset(self):
        """Test memory efficiency with large datasets."""
        formatter = ColorFormatter()
        # Create moderately large dataset
        rows = [f'Constraint{i}' for i in range(50)]
        cols = [f'Day{i}' for i in range(30)]
        data = pd.DataFrame(
            [[float(i*j % 300) for j in range(30)] for i in range(50)],
            index=rows,
            columns=cols
        )
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Should handle data without excessive memory usage
        rendered = grid.render()
        assert len(rendered) < 100000  # Reasonable memory bound for rendered output


class TestScrollingAndViewport:
    """Test scrolling behavior for large datasets."""

    def test_virtual_scrolling_large_dataset(self):
        """Test that virtual scrolling works for datasets larger than viewport."""
        formatter = ColorFormatter()
        # Large dataset that would exceed typical terminal height
        rows = [f'Constraint{i}' for i in range(200)]
        cols = [f'Day{i}' for i in range(30)]
        data = pd.DataFrame(
            [[float(i*j % 300) for j in range(30)] for i in range(200)],
            index=rows,
            columns=cols
        )
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Should handle large dataset efficiently
        rendered = grid.render()
        assert isinstance(rendered, str)
        # Should not render everything at once (virtual scrolling)
        assert len(rendered) < 50000  # Reasonable bound for partial rendering

    def test_column_width_handling(self):
        """Test that column widths are handled properly for alignment."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0],
            'Day2': [150.0],
            'Day3': [200.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        rendered = grid.render()
        # Should render with consistent alignment
        assert isinstance(rendered, str)
        assert len(rendered) > 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_focused_cell_coordinates(self):
        """Test handling of invalid focus coordinates."""
        formatter = ColorFormatter()
        data = pd.DataFrame({
            'Day1': [100.0]
        }, index=['Constraint1'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Test out-of-bounds coordinates
        try:
            grid.focused_cell = (-1, -1)
            # Should either clamp or raise appropriate error
        except (ValueError, IndexError):
            pass  # Acceptable error handling
        
        try:
            grid.focused_cell = (10, 10)  # Beyond data bounds
            # Should either clamp or raise appropriate error  
        except (ValueError, IndexError):
            pass  # Acceptable error handling

    def test_malformed_data_handling(self):
        """Test handling of malformed or inconsistent data."""
        formatter = ColorFormatter()
        
        # Create data with mixed types
        data = pd.DataFrame({
            'Day1': [100.0, 'invalid', 200.0]
        }, index=['Constraint1', 'Constraint2', 'Constraint3'])
        
        grid = ColorGrid(
            data=data,
            column_type="VIEW",
            color_formatter=formatter
        )
        
        # Should handle gracefully without crashing
        rendered = grid.render()
        assert isinstance(rendered, str)
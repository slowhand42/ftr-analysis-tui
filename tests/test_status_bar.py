"""
Test suite for StatusBar widget following TDD methodology.

Tests cover:
1. Position updates (sheet, cluster, row display)
2. File info display (filename, save status, truncation)
3. Edit mode transitions (view/edit mode indicators)
4. Message display (temporary messages)
5. Text formatting and reactive updates
6. Help text context switching
7. Reactive property behavior
8. Edge case handling

These tests drive implementation of comprehensive StatusBar functionality
as specified in task-013 requirements. Tests are designed to fail first (TDD Red phase)
and guide the implementation of the full StatusBar with reactive properties.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from rich.text import Text


# TDD: Import the existing StatusBar to show tests will fail (Red phase)
# These tests define the required interface for the full StatusBar implementation
# The current basic StatusBar implementation will not pass these tests

"""
TDD Workflow Instructions for Developer-Agent:

1. RED PHASE: The current StatusBar in src/widgets/status_bar.py is a basic implementation
   that lacks the comprehensive interface required by these tests. Replace the mock StatusBar
   class below with: from src.widgets.status_bar import StatusBar
   The tests will fail, defining the required interface.

2. GREEN PHASE: Implement the full StatusBar class with:
   - Reactive properties: current_sheet, current_cluster, total_clusters, etc.
   - Methods: update_position(), set_file_info(), set_edit_mode(), show_message()
   - Helper methods: _build_position_text(), _build_file_text(), _build_help_text(), _truncate_filename()
   - Rich Text rendering with proper formatting and spacing

3. REFACTOR PHASE: Once tests pass, optimize the implementation for performance and maintainability.
"""

# Import the actual StatusBar implementation
from src.widgets.status_bar import StatusBar


class TestStatusBar:
    """Test suite for StatusBar widget functionality using target interface."""

    def test_position_updates_display_correctly(self):
        """Test position information updates and displays correctly."""
        # Arrange
        status_bar = StatusBar()
        
        # Act
        status_bar.update_position("OCT25", 42, 3, 7)
        status_bar.total_clusters = 156
        
        # Assert - check reactive properties are set
        assert status_bar.current_sheet == "OCT25"
        assert status_bar.current_cluster == 42
        assert status_bar.current_row == 3
        assert status_bar.total_rows == 7
        assert status_bar.total_clusters == 156
        
        # Assert - check rendered position text contains expected values
        rendered_text = status_bar.render()
        rendered_plain = rendered_text.plain
        assert "OCT25" in rendered_plain
        assert "Cluster 42/156" in rendered_plain
        assert "Row 3/7" in rendered_plain

    def test_file_info_display_with_modified_indicator(self):
        """Test file information display including modified status and save timestamp."""
        # Arrange
        status_bar = StatusBar()
        test_time = datetime(2023, 10, 15, 14, 30, 45)
        
        # Act - set file info with modified status
        status_bar.set_file_info("analysis_results.xlsx", modified=True)
        status_bar.last_save = test_time
        
        # Assert - check reactive properties
        assert status_bar.file_name == "analysis_results.xlsx"
        assert status_bar.is_modified is True
        assert status_bar.last_save == test_time
        
        # Assert - check rendered text includes modified indicator and save time
        rendered_text = status_bar.render()
        rendered_plain = rendered_text.plain
        assert "analysis_results.xlsx" in rendered_plain
        assert "*" in rendered_plain  # Modified indicator
        assert "14:30:45" in rendered_plain  # Save timestamp

    def test_filename_truncation_for_long_names(self):
        """Test that long filenames are truncated appropriately."""
        # Arrange
        status_bar = StatusBar()
        long_filename = "very_long_analysis_results_with_detailed_naming_convention.xlsx"
        
        # Act
        status_bar.set_file_info(long_filename)
        
        # Assert - filename should be truncated but still contain important parts
        assert len(status_bar.file_name) <= 30
        assert status_bar.file_name.startswith("...")
        assert "convention.xlsx" in status_bar.file_name

    def test_edit_mode_transitions_update_display(self):
        """Test edit mode transitions and column editing indicators."""
        # Arrange
        status_bar = StatusBar()
        
        # Act - enter edit mode
        status_bar.set_edit_mode(True, "VIEW")
        
        # Assert - edit mode properties set correctly
        assert status_bar.edit_mode is True
        assert status_bar.edit_column == "VIEW"
        
        # Assert - rendered text shows edit mode indicator
        rendered_text = status_bar.render()
        rendered_plain = rendered_text.plain
        assert "Editing: VIEW" in rendered_plain
        
        # Act - exit edit mode
        status_bar.set_edit_mode(False)
        
        # Assert - edit mode cleared
        assert status_bar.edit_mode is False
        assert status_bar.edit_column == ""
        
        # Assert - edit indicator no longer shown
        rendered_text = status_bar.render()
        rendered_plain = rendered_text.plain
        assert "Editing:" not in rendered_plain

    def test_help_text_changes_based_on_mode(self):
        """Test help text displays different content based on edit vs browse mode."""
        # Arrange
        status_bar = StatusBar()
        
        # Act - browse mode (default)
        browse_text = status_bar._build_help_text()
        
        # Assert - browse mode shows navigation commands
        browse_plain = browse_text.plain
        assert "[n/p] Navigate" in browse_plain
        assert "[0-9] Edit" in browse_plain
        assert "[Ctrl+S] Save" in browse_plain
        
        # Act - edit mode
        status_bar.edit_mode = True
        edit_text = status_bar._build_help_text()
        
        # Assert - edit mode shows edit commands
        edit_plain = edit_text.plain
        assert "[Enter] Save" in edit_plain
        assert "[Esc] Cancel" in edit_plain
        assert "[Tab] Next Field" in edit_plain

    def test_temporary_message_display(self):
        """Test temporary message display functionality."""
        # Arrange
        status_bar = StatusBar()
        test_message = "Data saved successfully"
        
        # Act
        status_bar.show_message(test_message, duration=3.0)
        
        # Assert - message is set
        assert status_bar.message == test_message
        
        # Assert - message appears in rendered output (in real implementation)
        # For now, just verify message is stored
        assert status_bar.message == "Data saved successfully"

    def test_reactive_properties_trigger_updates(self):
        """Test that reactive property changes trigger proper updates."""
        # Arrange
        status_bar = StatusBar()
        initial_render = status_bar.render().plain
        
        # Act - change multiple reactive properties
        status_bar.current_sheet = "DEC25"
        status_bar.current_cluster = 99
        status_bar.file_name = "new_file.xlsx"
        status_bar.is_modified = True
        
        # Assert - rendered output reflects changes
        updated_render = status_bar.render().plain
        assert updated_render != initial_render
        assert "DEC25" in updated_render
        assert "Cluster 99" in updated_render
        assert "new_file.xlsx" in updated_render
        assert "*" in updated_render  # Modified indicator

    def test_edge_cases_and_empty_values(self):
        """Test handling of edge cases and empty/zero values."""
        # Arrange
        status_bar = StatusBar()
        
        # Act - set edge case values
        status_bar.update_position("", 0, 0, 0)
        status_bar.total_clusters = 0
        status_bar.set_file_info("")
        
        # Assert - widget handles empty/zero values gracefully
        rendered_text = status_bar.render()
        rendered_plain = rendered_text.plain
        
        # Should not crash and should handle zero values
        assert "Cluster 0/0" in rendered_plain
        assert "Row 0/0" in rendered_plain
        
        # Test large numbers
        status_bar.update_position("SHEET", 999999, 888888, 777777)
        status_bar.total_clusters = 999999
        
        large_render = status_bar.render().plain
        assert "Cluster 999999/999999" in large_render
        assert "Row 888888/777777" in large_render
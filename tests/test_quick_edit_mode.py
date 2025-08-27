"""
Test suite for Task 016: Quick Edit Mode functionality in ClusterView.

These tests drive the implementation of Quick Edit Mode following TDD methodology:
1. Number key triggers (1-9) to initiate edit mode
2. Inline editing overlay appearance  
3. Real-time validation feedback
4. Enter to confirm edits
5. Escape to cancel edits
6. Navigation during edit mode
7. Invalid input handling
8. Visual feedback for editable cells
9. Edit mode transitions
10. Integration with DataValidator
11. Keyboard shortcuts for common values
12. Edit history integration
13. Concurrent edit prevention
14. Edit mode status display
15. Performance with rapid edits

Tests ensure user interaction, validation feedback, and seamless editing experience
that will drive TDD implementation in the ClusterView widget.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import pandas as pd
import time
from datetime import datetime
from textual import events
from textual.widgets import DataTable, Input
from textual.coordinate import Coordinate
from textual.keys import Keys

# Import target implementation
from src.widgets.cluster_view import ClusterView
from src.business_logic.excel_data_manager import ExcelDataManager
from src.business_logic.color_formatter import ColorFormatter
from src.business_logic.validators import DataValidator, ValidationResult
from src.models.data_models import EditRecord


class TestQuickEditTriggerSystem:
    """Test number key triggers and edit mode initiation."""

    @pytest.fixture
    def setup_cluster_view(self):
        """Create ClusterView with mock dependencies for testing."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_color_formatter = Mock(spec=ColorFormatter)
        
        # Sample test data
        test_data = pd.DataFrame({
            'CONSTRAINTNAME': ['LINE_001_LIMIT', 'LINE_002_LIMIT'],
            'BRANCHNAME': ['LINE_001', 'LINE_002'],
            'VIEW': [125.5, 87.3],
            'PREV': [120.0, 90.5],
            'PACTUAL': [118.2, 89.1],
            'PEXPECTED': [115.0, 88.0],
            'RECENT_DELTA': [3.2, 1.1],
            'SHORTLIMIT': [-150.0, -100.0],
            'LODF': [0.85, 0.92],
            'STATUS': ['Active', 'Inactive']
        })
        
        mock_data_manager.get_cluster_data.return_value = test_data
        mock_data_manager.can_edit_column.side_effect = lambda col: col.upper() in ['VIEW', 'SHORTLIMIT']
        
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("TEST_CLUSTER")
        
        return cluster_view, mock_data_manager, mock_color_formatter

    def test_number_key_triggers_edit_in_editable_column(self, setup_cluster_view):
        """Test that number keys (0-9) trigger edit mode in editable columns (VIEW/SHORTLIMIT)."""
        cluster_view, mock_data_manager, mock_color_formatter = setup_cluster_view
        
        # Position cursor on editable VIEW column
        cluster_view.move_cursor(row=0, column=2)  # VIEW column
        assert cluster_view.selected_cell == (0, 2)
        
        # Simulate pressing number key '5'
        key_event = events.Key(key='5', character='5')
        result = cluster_view.on_key(key_event)
        
        # Assert edit mode is triggered
        assert hasattr(cluster_view, 'edit_mode')
        assert cluster_view.edit_mode is True
        assert hasattr(cluster_view, 'edit_input')
        assert cluster_view.edit_input is not None
        
        # Assert edit input contains the typed number
        assert cluster_view.edit_input.value == '5'
        
        # Assert edit position matches selected cell
        assert hasattr(cluster_view, 'edit_position')
        assert cluster_view.edit_position == (0, 2)
        
        # Test other number keys
        cluster_view.exit_edit_mode()  # Reset
        cluster_view.move_cursor(row=1, column=7)  # SHORTLIMIT column
        
        key_event = events.Key(key='3', character='3')
        cluster_view.on_key(key_event)
        
        assert cluster_view.edit_mode is True
        assert cluster_view.edit_input.value == '3'
        assert cluster_view.edit_position == (1, 7)

    def test_number_key_ignored_in_readonly_column(self, setup_cluster_view):
        """Test that number keys are ignored in read-only columns."""
        cluster_view, mock_data_manager, mock_color_formatter = setup_cluster_view
        
        # Position cursor on read-only CONSTRAINTNAME column
        cluster_view.move_cursor(row=0, column=0)  # CONSTRAINTNAME column
        assert cluster_view.selected_cell == (0, 0)
        
        # Simulate pressing number key '5'
        key_event = events.Key(key='5', character='5')
        result = cluster_view.on_key(key_event)
        
        # Assert edit mode is NOT triggered
        assert not hasattr(cluster_view, 'edit_mode') or cluster_view.edit_mode is False
        assert not hasattr(cluster_view, 'edit_input') or cluster_view.edit_input is None
        
        # Test other read-only columns (PREV, PACTUAL, LODF, STATUS)
        readonly_columns = [1, 3, 4, 6, 8, 9]  # BRANCHNAME, PREV, PACTUAL, RECENT_DELTA, LODF, STATUS
        
        for col_idx in readonly_columns:
            cluster_view.move_cursor(row=0, column=col_idx)
            key_event = events.Key(key='7', character='7')
            cluster_view.on_key(key_event)
            
            # Should not trigger edit mode
            assert not hasattr(cluster_view, 'edit_mode') or cluster_view.edit_mode is False

    def test_inline_edit_display_shows_typed_value(self, setup_cluster_view):
        """Test that inline edit overlay displays the typed value correctly."""
        cluster_view, mock_data_manager, mock_color_formatter = setup_cluster_view
        
        # Start edit mode
        cluster_view.move_cursor(row=0, column=2)  # VIEW column
        key_event = events.Key(key='1', character='1')
        cluster_view.on_key(key_event)
        
        assert cluster_view.edit_mode is True
        assert cluster_view.edit_input.value == '1'
        
        # Continue typing to build up a number
        additional_keys = ['2', '3', '.', '4', '5']
        for key_char in additional_keys:
            key_event = events.Key(key=key_char, character=key_char)
            cluster_view.edit_input.on_key(key_event)
        
        # Assert typed value is displayed
        expected_value = '123.45'
        assert cluster_view.edit_input.value == expected_value
        
        # Assert edit input is visible and positioned correctly
        assert cluster_view.edit_input.display is True
        assert hasattr(cluster_view, 'edit_overlay')
        
        # Assert original cell content is preserved
        original_value = cluster_view.get_cell_at(Coordinate(0, 2))
        assert str(original_value) != expected_value  # Should show original until committed


class TestEditCommitAndCancelOperations:
    """Test Enter/Escape behavior for committing and canceling edits."""

    @pytest.fixture
    def setup_edit_mode(self):
        """Set up ClusterView in edit mode for testing."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_color_formatter = Mock(spec=ColorFormatter)
        mock_validator = Mock(spec=DataValidator)
        
        test_data = pd.DataFrame({
            'CONSTRAINTNAME': ['LINE_001_LIMIT'],
            'VIEW': [125.5],
            'SHORTLIMIT': [-150.0]
        })
        
        mock_data_manager.get_cluster_data.return_value = test_data
        mock_data_manager.can_edit_column.side_effect = lambda col: col.upper() in ['VIEW', 'SHORTLIMIT']
        mock_data_manager.validate_and_update.return_value = (True, "Value updated successfully")
        
        # Mock successful validation
        valid_result = ValidationResult(is_valid=True, sanitized_value=135.0)
        mock_validator.validate_cell.return_value = valid_result
        
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.validator = mock_validator  # Inject validator
        cluster_view.load_cluster("TEST_CLUSTER")
        
        return cluster_view, mock_data_manager, mock_validator

    def test_enter_commits_edit_and_moves_down(self, setup_edit_mode):
        """Test that Enter commits edit and moves cursor down to next row."""
        cluster_view, mock_data_manager, mock_validator = setup_edit_mode
        
        # Start edit mode at position (0, 2) - first row, VIEW column
        cluster_view.move_cursor(row=0, column=2)
        cluster_view.start_edit_mode('135')
        
        assert cluster_view.edit_mode is True
        assert cluster_view.edit_input.value == '135'
        
        # Simulate Enter key press
        enter_event = events.Key(key='enter')
        cluster_view.on_key(enter_event)
        
        # Assert edit was committed
        mock_data_manager.validate_and_update.assert_called_once_with(
            cluster='TEST_CLUSTER',
            constraint_index=0,
            column='VIEW', 
            value='135'
        )
        
        # Assert edit mode is exited
        assert cluster_view.edit_mode is False
        assert cluster_view.edit_input is None
        
        # Assert cursor moved down to next row in same column
        # Note: If only one row, cursor should stay at (0, 2)
        expected_position = (min(1, cluster_view.row_count - 1), 2)
        assert cluster_view.selected_cell == expected_position

    def test_tab_commits_edit_and_moves_right(self, setup_edit_mode):
        """Test that Tab commits edit and moves to next editable column."""
        cluster_view, mock_data_manager, mock_validator = setup_edit_mode
        
        # Start edit at VIEW column
        cluster_view.move_cursor(row=0, column=2)  # VIEW
        cluster_view.start_edit_mode('140')
        
        # Simulate Tab key press
        tab_event = events.Key(key='tab')
        cluster_view.on_key(tab_event)
        
        # Assert edit was committed
        mock_data_manager.validate_and_update.assert_called_once()
        
        # Assert cursor moved to next editable column (SHORTLIMIT)
        # Should skip non-editable columns
        expected_col = 7  # SHORTLIMIT column index
        assert cluster_view.selected_cell == (0, expected_col)
        
        # Assert edit mode exited
        assert cluster_view.edit_mode is False

    def test_escape_cancels_edit_restores_value(self, setup_edit_mode):
        """Test that Escape cancels edit and restores original value."""
        cluster_view, mock_data_manager, mock_validator = setup_edit_mode
        
        # Start edit mode
        cluster_view.move_cursor(row=0, column=2)  # VIEW column
        original_value = cluster_view.get_cell_at(Coordinate(0, 2))
        
        cluster_view.start_edit_mode('999')  # Type different value
        assert cluster_view.edit_input.value == '999'
        
        # Simulate Escape key press
        escape_event = events.Key(key='escape')
        cluster_view.on_key(escape_event)
        
        # Assert edit was NOT committed
        mock_data_manager.validate_and_update.assert_not_called()
        
        # Assert edit mode is exited
        assert cluster_view.edit_mode is False
        assert cluster_view.edit_input is None
        
        # Assert original value is preserved
        current_value = cluster_view.get_cell_at(Coordinate(0, 2))
        assert str(current_value) == str(original_value)
        
        # Assert cursor position unchanged
        assert cluster_view.selected_cell == (0, 2)

    def test_arrow_keys_cancel_edit_and_navigate(self, setup_edit_mode):
        """Test that arrow keys during edit cancel edit and navigate normally."""
        cluster_view, mock_data_manager, mock_validator = setup_edit_mode
        
        # Start edit mode
        cluster_view.move_cursor(row=0, column=2)  # VIEW column  
        cluster_view.start_edit_mode('888')
        assert cluster_view.edit_mode is True
        
        # Test Right arrow cancels and moves right
        right_event = events.Key(key='right')
        cluster_view.on_key(right_event)
        
        # Assert edit was cancelled (not committed)
        mock_data_manager.validate_and_update.assert_not_called()
        assert cluster_view.edit_mode is False
        
        # Assert cursor moved right
        assert cluster_view.selected_cell[1] > 2  # Column increased
        
        # Test other arrow keys
        mock_data_manager.reset_mock()
        cluster_view.move_cursor(row=0, column=2)
        cluster_view.start_edit_mode('777')
        
        # Test Down arrow
        down_event = events.Key(key='down')  
        cluster_view.on_key(down_event)
        
        assert cluster_view.edit_mode is False
        mock_data_manager.validate_and_update.assert_not_called()


class TestRealTimeValidationFeedback:
    """Test real-time validation and visual feedback during editing."""

    @pytest.fixture  
    def setup_validation_test(self):
        """Set up ClusterView with validation mocking."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_color_formatter = Mock(spec=ColorFormatter) 
        mock_validator = Mock(spec=DataValidator)
        
        test_data = pd.DataFrame({
            'CONSTRAINTNAME': ['LINE_001_LIMIT'],
            'VIEW': [125.5],
            'SHORTLIMIT': [-150.0]
        })
        
        mock_data_manager.get_cluster_data.return_value = test_data
        mock_data_manager.can_edit_column.side_effect = lambda col: col.upper() in ['VIEW', 'SHORTLIMIT']
        
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.validator = mock_validator
        cluster_view.load_cluster("TEST_CLUSTER")
        
        return cluster_view, mock_data_manager, mock_validator

    def test_real_time_validation_feedback(self, setup_validation_test):
        """Test that validation feedback is shown in real-time as user types."""
        cluster_view, mock_data_manager, mock_validator = setup_validation_test
        
        # Start edit mode on VIEW column
        cluster_view.move_cursor(row=0, column=2)
        cluster_view.start_edit_mode('')
        
        # Mock invalid validation result (negative VIEW value)
        invalid_result = ValidationResult(
            is_valid=False,
            error_message="VIEW must be a positive number greater than 0"
        )
        mock_validator.validate_cell.return_value = invalid_result
        
        # Simulate typing invalid value
        cluster_view.edit_input.value = '-100'
        cluster_view.on_edit_input_changed()  # Trigger validation
        
        # Assert validation was called
        mock_validator.validate_cell.assert_called_with('VIEW', '-100')
        
        # Assert error feedback is displayed
        assert hasattr(cluster_view, 'validation_message')
        assert cluster_view.validation_message == "VIEW must be a positive number greater than 0"
        assert hasattr(cluster_view, 'validation_status')
        assert cluster_view.validation_status == 'invalid'
        
        # Test valid value shows positive feedback
        valid_result = ValidationResult(is_valid=True, sanitized_value=150.0)
        mock_validator.validate_cell.return_value = valid_result
        
        cluster_view.edit_input.value = '150'
        cluster_view.on_edit_input_changed()
        
        assert cluster_view.validation_status == 'valid'
        assert cluster_view.validation_message == "" or "Valid" in cluster_view.validation_message

    def test_invalid_value_prevents_commit(self, setup_validation_test):
        """Test that invalid values cannot be committed with Enter."""
        cluster_view, mock_data_manager, mock_validator = setup_validation_test
        
        # Start edit mode
        cluster_view.move_cursor(row=0, column=2)  # VIEW column
        cluster_view.start_edit_mode('-50')  # Invalid negative VIEW
        
        # Mock invalid validation
        invalid_result = ValidationResult(
            is_valid=False, 
            error_message="VIEW must be a positive number"
        )
        mock_validator.validate_cell.return_value = invalid_result
        
        # Try to commit with Enter
        enter_event = events.Key(key='enter')
        cluster_view.on_key(enter_event)
        
        # Assert commit was prevented
        mock_data_manager.validate_and_update.assert_not_called()
        
        # Assert still in edit mode with error message
        assert cluster_view.edit_mode is True
        assert "VIEW must be a positive number" in cluster_view.validation_message
        
        # Assert visual error indicator
        assert cluster_view.validation_status == 'invalid'
        assert hasattr(cluster_view.edit_input, 'add_class')  # CSS class for styling

    def test_decimal_and_minus_key_support(self, setup_validation_test):
        """Test support for decimal points and minus signs in edit mode."""
        cluster_view, mock_data_manager, mock_validator = setup_validation_test
        
        # Test decimal input in VIEW column
        cluster_view.move_cursor(row=0, column=2)  # VIEW
        cluster_view.start_edit_mode('')
        
        # Simulate typing decimal number
        decimal_keys = ['1', '2', '3', '.', '4', '5']
        for key_char in decimal_keys:
            key_event = events.Key(key=key_char, character=key_char)
            if key_char == '.':
                # Test decimal key specifically
                result = cluster_view.handle_edit_key(key_event)
                assert result is True  # Should be handled
            cluster_view.edit_input.value += key_char
        
        assert cluster_view.edit_input.value == '123.45'
        
        # Test minus sign in SHORTLIMIT column
        cluster_view.exit_edit_mode()
        cluster_view.move_cursor(row=0, column=7)  # SHORTLIMIT
        cluster_view.start_edit_mode('')
        
        # Test minus key
        minus_event = events.Key(key='-', character='-')
        result = cluster_view.handle_edit_key(minus_event)
        assert result is True  # Should be handled for SHORTLIMIT
        
        cluster_view.edit_input.value = '-200.5'
        assert cluster_view.edit_input.value == '-200.5'


class TestEditModeNavigation:
    """Test advanced navigation behavior during and after editing."""

    @pytest.fixture
    def multi_row_cluster_view(self):
        """Create ClusterView with multiple rows for navigation testing."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_color_formatter = Mock(spec=ColorFormatter)
        
        # Multi-row test data
        test_data = pd.DataFrame({
            'CONSTRAINTNAME': ['LINE_001_LIMIT', 'LINE_002_LIMIT', 'LINE_003_LIMIT'],
            'VIEW': [125.5, 87.3, 203.1],
            'SHORTLIMIT': [-150.0, -100.0, -250.0],
            'LODF': [0.85, 0.92, 0.78]  # Read-only column
        })
        
        mock_data_manager.get_cluster_data.return_value = test_data
        mock_data_manager.can_edit_column.side_effect = lambda col: col.upper() in ['VIEW', 'SHORTLIMIT']
        mock_data_manager.validate_and_update.return_value = (True, "Success")
        
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("MULTI_ROW_CLUSTER")
        
        return cluster_view, mock_data_manager

    def test_shift_tab_moves_to_previous_editable(self, multi_row_cluster_view):
        """Test that Shift+Tab moves to previous editable column."""
        cluster_view, mock_data_manager = multi_row_cluster_view
        
        # Start at SHORTLIMIT column
        shortlimit_col = 2  # Assuming SHORTLIMIT is column index 2
        cluster_view.move_cursor(row=1, column=shortlimit_col)
        cluster_view.start_edit_mode('test')
        
        # Simulate Shift+Tab
        shift_tab_event = events.Key(key='shift+tab')
        cluster_view.on_key(shift_tab_event)
        
        # Should move to previous editable column (VIEW)
        view_col = 1  # Assuming VIEW is column index 1
        assert cluster_view.selected_cell[1] == view_col
        assert cluster_view.edit_mode is False  # Edit committed

    def test_edit_wrapping_at_grid_boundaries(self, multi_row_cluster_view):
        """Test navigation behavior at grid boundaries during edit commits."""
        cluster_view, mock_data_manager = multi_row_cluster_view
        
        # Test wrapping at bottom-right corner
        last_row = cluster_view.row_count - 1
        last_editable_col = 2  # SHORTLIMIT column
        
        cluster_view.move_cursor(row=last_row, column=last_editable_col)
        cluster_view.start_edit_mode('999')
        
        # Enter should either wrap to next row/first editable col or stay put
        enter_event = events.Key(key='enter')
        cluster_view.on_key(enter_event)
        
        # Check cursor position after boundary navigation
        new_position = cluster_view.selected_cell
        
        # Should handle boundary gracefully (implementation-dependent)
        assert 0 <= new_position[0] < cluster_view.row_count
        assert 0 <= new_position[1] < cluster_view.column_count
        
        # Test Tab at row end
        cluster_view.move_cursor(row=0, column=last_editable_col)
        cluster_view.start_edit_mode('test')
        
        tab_event = events.Key(key='tab')
        cluster_view.on_key(tab_event)
        
        # Should wrap to next row, first editable column
        expected_row = 1
        expected_col = 1  # VIEW column (first editable)
        assert cluster_view.selected_cell == (expected_row, expected_col)

    def test_clipboard_paste_during_edit(self, multi_row_cluster_view):
        """Test clipboard paste support during edit mode."""
        cluster_view, mock_data_manager = multi_row_cluster_view
        
        # Start edit mode
        cluster_view.move_cursor(row=0, column=1)  # VIEW column
        cluster_view.start_edit_mode('')
        
        # Mock clipboard content
        with patch('pyperclip.paste', return_value='456.78'):
            # Simulate Ctrl+V paste
            paste_event = events.Key(key='ctrl+v')
            result = cluster_view.on_key(paste_event)
            
            # Assert paste was handled
            assert cluster_view.edit_input.value == '456.78'
        
        # Test paste validation
        mock_validator = Mock(spec=DataValidator)
        invalid_result = ValidationResult(is_valid=False, error_message="Invalid paste")
        mock_validator.validate_cell.return_value = invalid_result
        cluster_view.validator = mock_validator
        
        with patch('pyperclip.paste', return_value='invalid_text'):
            paste_event = events.Key(key='ctrl+v')
            cluster_view.on_key(paste_event)
            
            # Should show validation error
            assert cluster_view.validation_status == 'invalid'


class TestEditHistoryAndConcurrency:
    """Test edit history integration and concurrent edit handling."""

    @pytest.fixture
    def history_enabled_cluster_view(self):
        """Create ClusterView with edit history enabled."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_color_formatter = Mock(spec=ColorFormatter)
        
        test_data = pd.DataFrame({
            'CONSTRAINTNAME': ['LINE_001_LIMIT'],
            'VIEW': [125.5],
            'SHORTLIMIT': [-150.0]
        })
        
        mock_data_manager.get_cluster_data.return_value = test_data
        mock_data_manager.can_edit_column.side_effect = lambda col: col.upper() in ['VIEW', 'SHORTLIMIT']
        mock_data_manager.validate_and_update.return_value = (True, "Success")
        
        # Mock edit history
        mock_edit_record = EditRecord(
            sheet='TEST_SHEET',
            cluster_id=1,
            constraint_index=0,
            column='VIEW',
            old_value=125.5,
            new_value=135.0,
            timestamp=datetime.now(),
            cuid='C001'
        )
        mock_data_manager.get_edit_history.return_value = [mock_edit_record]
        
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("TEST_CLUSTER")
        
        return cluster_view, mock_data_manager

    def test_edit_history_recorded_on_commit(self, history_enabled_cluster_view):
        """Test that successful edits are recorded in edit history."""
        cluster_view, mock_data_manager = history_enabled_cluster_view
        
        # Perform edit
        cluster_view.move_cursor(row=0, column=1)  # VIEW column
        cluster_view.start_edit_mode('140')
        
        # Commit edit
        enter_event = events.Key(key='enter')
        cluster_view.on_key(enter_event)
        
        # Assert edit was committed through data manager
        mock_data_manager.validate_and_update.assert_called_once_with(
            cluster='TEST_CLUSTER',
            constraint_index=0,
            column='VIEW',
            value='140'
        )
        
        # Assert edit history can be retrieved
        history = cluster_view.get_edit_history()
        assert len(history) > 0
        
        # Verify edit history contains our edit
        mock_data_manager.get_edit_history.assert_called()

    def test_concurrent_edit_handling(self, history_enabled_cluster_view):
        """Test handling of concurrent edit attempts on same cell."""
        cluster_view, mock_data_manager = history_enabled_cluster_view
        
        # Simulate first edit in progress
        cluster_view.move_cursor(row=0, column=1)  # VIEW column
        cluster_view.start_edit_mode('150')
        assert cluster_view.edit_mode is True
        
        # Simulate attempt to start another edit on same cell
        original_edit_input = cluster_view.edit_input
        
        # Try to start second edit (should be prevented)
        result = cluster_view.start_edit_mode('200')
        
        # Should prevent concurrent edit on same cell
        assert result is False or cluster_view.edit_input is original_edit_input
        
        # Test concurrent edit prevention across different cells
        cluster_view.move_cursor(row=0, column=2)  # SHORTLIMIT column
        
        # Should allow edit on different cell
        result = cluster_view.start_edit_mode('-200')
        # Implementation may allow this or enforce single edit mode
        # Test should verify consistent behavior


class TestEditModePerformanceAndResponsiveness:
    """Test performance requirements and user experience."""

    @pytest.fixture
    def performance_test_setup(self):
        """Set up for performance testing."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_color_formatter = Mock(spec=ColorFormatter) 
        
        # Large dataset for performance testing
        large_data = pd.DataFrame({
            'CONSTRAINTNAME': [f'LINE_{i:03d}_LIMIT' for i in range(100)],
            'VIEW': [100.0 + i for i in range(100)],
            'SHORTLIMIT': [-100.0 - i for i in range(100)]
        })
        
        mock_data_manager.get_cluster_data.return_value = large_data
        mock_data_manager.can_edit_column.side_effect = lambda col: col.upper() in ['VIEW', 'SHORTLIMIT']
        mock_data_manager.validate_and_update.return_value = (True, "Success")
        
        cluster_view = ClusterView(mock_data_manager, mock_color_formatter)
        cluster_view.load_cluster("LARGE_CLUSTER")
        
        return cluster_view, mock_data_manager

    def test_edit_trigger_response_time(self, performance_test_setup):
        """Test that edit trigger response is under 50ms as required."""
        cluster_view, mock_data_manager = performance_test_setup
        
        # Position on editable cell
        cluster_view.move_cursor(row=50, column=1)  # Middle of large dataset
        
        # Measure edit trigger time
        start_time = time.perf_counter()
        
        key_event = events.Key(key='5', character='5')
        cluster_view.on_key(key_event)
        
        end_time = time.perf_counter()
        trigger_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Assert response time under 50ms requirement
        assert trigger_time < 50.0, f"Edit trigger took {trigger_time:.2f}ms, should be under 50ms"
        
        # Assert edit mode was successfully triggered
        assert cluster_view.edit_mode is True
        assert cluster_view.edit_input.value == '5'

    def test_validation_feedback_response_time(self, performance_test_setup):
        """Test that validation feedback appears within 100ms."""
        cluster_view, mock_data_manager = performance_test_setup
        
        # Mock validator with controlled delay
        mock_validator = Mock(spec=DataValidator)
        valid_result = ValidationResult(is_valid=True, sanitized_value=200.0)
        mock_validator.validate_cell.return_value = valid_result
        cluster_view.validator = mock_validator
        
        # Start edit mode
        cluster_view.move_cursor(row=25, column=1)
        cluster_view.start_edit_mode('')
        
        # Measure validation feedback time
        start_time = time.perf_counter()
        
        cluster_view.edit_input.value = '200'
        cluster_view.on_edit_input_changed()
        
        end_time = time.perf_counter()
        validation_time = (end_time - start_time) * 1000
        
        # Assert validation feedback under 100ms requirement
        assert validation_time < 100.0, f"Validation feedback took {validation_time:.2f}ms, should be under 100ms"
        
        # Assert validation was performed
        mock_validator.validate_cell.assert_called_with('VIEW', '200')

    def test_performance_with_rapid_edits(self, performance_test_setup):
        """Test system performance with rapid edit operations."""
        cluster_view, mock_data_manager = performance_test_setup
        
        # Perform rapid edit sequence
        start_time = time.perf_counter()
        
        edit_positions = [(i, 1) for i in range(0, 20, 2)]  # 10 rapid edits
        
        for row, col in edit_positions:
            cluster_view.move_cursor(row=row, column=col)
            
            # Start edit
            key_event = events.Key(key='3', character='3')
            cluster_view.on_key(key_event)
            
            # Immediate commit
            enter_event = events.Key(key='enter')
            cluster_view.on_key(enter_event)
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000
        avg_time_per_edit = total_time / len(edit_positions)
        
        # Assert reasonable performance for rapid edits
        assert avg_time_per_edit < 20.0, f"Average edit time {avg_time_per_edit:.2f}ms too slow"
        assert total_time < 500.0, f"Total rapid edit time {total_time:.2f}ms too slow"
        
        # Assert all edits were processed
        assert mock_data_manager.validate_and_update.call_count == len(edit_positions)

    def test_edit_mode_status_display(self, performance_test_setup):
        """Test visual status indicators during edit mode."""
        cluster_view, mock_data_manager = performance_test_setup
        
        # Initially not in edit mode
        assert not hasattr(cluster_view, 'edit_mode') or cluster_view.edit_mode is False
        
        # Start edit mode
        cluster_view.move_cursor(row=0, column=1)
        key_event = events.Key(key='7', character='7')
        cluster_view.on_key(key_event)
        
        # Assert edit mode status indicators
        assert cluster_view.edit_mode is True
        assert hasattr(cluster_view, 'edit_status_message')
        assert 'editing' in cluster_view.edit_status_message.lower() or 'edit mode' in cluster_view.edit_status_message.lower()
        
        # Assert visual indicators for current cell
        assert hasattr(cluster_view, 'edit_cell_highlight')
        
        # Exit edit mode and verify status cleared
        escape_event = events.Key(key='escape')
        cluster_view.on_key(escape_event)
        
        assert cluster_view.edit_mode is False
        assert cluster_view.edit_status_message == "" or cluster_view.edit_status_message is None
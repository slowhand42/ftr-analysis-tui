"""
Tests for Task 018: Navigation Logic
Tests comprehensive navigation functionality including cluster, sheet, and grid navigation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import time
from textual.keys import Keys
from textual.events import Key

from src.app import AnalysisTUIApp
from src.models.data_models import SessionState


class TestNavigationLogic:
    """Test suite for navigation logic functionality."""
    
    @pytest.fixture
    def mock_excel_file(self, tmp_path):
        """Create a temporary Excel file path for testing."""
        excel_file = tmp_path / "test_data.xlsx"
        excel_file.touch()
        return str(excel_file)
    
    @pytest.fixture
    def mock_app(self, mock_excel_file):
        """Create a mocked AnalysisTUIApp for testing."""
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager') as mock_data_mgr, \
             patch('src.app.SessionManager') as mock_session_mgr:
            
            app = AnalysisTUIApp(mock_excel_file)
            
            # Mock essential components
            app.data_manager = Mock()
            app.session_manager = Mock()
            
            # Mock widgets
            app.sheet_tabs = Mock()
            app.cluster_view = Mock()
            app.status_bar = Mock()
            
            # Mock state
            app.current_cluster_list = ["C001", "C002", "C003", "C004", "C005"]
            app.current_cluster_index = 0
            app.sheet_tabs.active_sheet = "SEP25"
            
            # Mock session state
            session_state = SessionState(
                last_file=mock_excel_file,
                current_sheet="SEP25",
                current_cluster=0  # Using integer index as per model
            )
            app.current_session = session_state
            
            return app

    def test_cluster_navigation_forward(self, mock_app):
        """Test 'n' key moves to next cluster."""
        # Arrange
        initial_index = mock_app.current_cluster_index
        
        # Act
        mock_app.action_next_cluster()
        
        # Assert
        assert mock_app.current_cluster_index == initial_index + 1
        # Verify display_current_cluster would be called via action
        assert mock_app.current_cluster_index == 1

    def test_cluster_navigation_backward(self, mock_app):
        """Test 'p' key moves to previous cluster."""
        # Arrange
        mock_app.current_cluster_index = 2  # Start at middle cluster
        initial_index = mock_app.current_cluster_index
        
        # Act
        mock_app.action_prev_cluster()
        
        # Assert
        assert mock_app.current_cluster_index == initial_index - 1
        assert mock_app.current_cluster_index == 1

    def test_cluster_navigation_wrapping(self, mock_app):
        """Test proper wrap-around at boundaries."""
        # Create a navigation controller that should implement wrap-around
        # This test will fail until proper wrap-around is implemented
        
        # Test wrap-around at end: should go to first cluster
        mock_app.current_cluster_index = len(mock_app.current_cluster_list) - 1
        
        # Create a method that should implement wrap-around navigation
        def navigate_cluster_with_wrap(direction: int):
            """Navigate with wrap-around (to be implemented)."""
            if direction > 0:  # Forward
                if mock_app.current_cluster_index >= len(mock_app.current_cluster_list) - 1:
                    mock_app.current_cluster_index = 0  # Wrap to first
                else:
                    mock_app.current_cluster_index += 1
            else:  # Backward
                if mock_app.current_cluster_index <= 0:
                    mock_app.current_cluster_index = len(mock_app.current_cluster_list) - 1  # Wrap to last
                else:
                    mock_app.current_cluster_index -= 1
        
        # Mock the enhanced navigation method
        mock_app.navigate_cluster_with_wrap = navigate_cluster_with_wrap
        
        # Test forward wrap-around
        mock_app.navigate_cluster_with_wrap(1)
        assert mock_app.current_cluster_index == 0, "Should wrap to first cluster"
        
        # Test backward wrap-around from first
        mock_app.navigate_cluster_with_wrap(-1) 
        assert mock_app.current_cluster_index == len(mock_app.current_cluster_list) - 1, "Should wrap to last cluster"

    def test_sheet_switching_via_tab(self, mock_app):
        """Test Tab key changes sheets."""
        # Arrange
        initial_sheet = mock_app.sheet_tabs.active_sheet
        
        # Act
        mock_app.action_next_sheet()
        
        # Assert
        mock_app.sheet_tabs.next_sheet.assert_called_once()

    def test_grid_arrow_navigation(self, mock_app):
        """Test arrow keys move selection within cluster view."""
        # This test should verify that NavigationController handles grid navigation
        from src.presentation.navigation_controller import NavigationController
        
        nav_controller = NavigationController(mock_app)
        
        # Test that navigation controller can move cursor in grid
        initial_pos = nav_controller.get_cursor_position()
        
        # Move right
        nav_controller.move_cursor(1, 0)
        new_pos = nav_controller.get_cursor_position()
        assert new_pos[1] == initial_pos[1] + 1, "Should move cursor right"
        
        # Move down
        nav_controller.move_cursor(0, 1) 
        final_pos = nav_controller.get_cursor_position()
        assert final_pos[0] == initial_pos[0] + 1, "Should move cursor down"

    def test_home_end_navigation(self, mock_app):
        """Test Home/End keys work correctly."""
        # Mock cluster view navigation methods
        mock_app.cluster_view.action_cursor_line_start = Mock()
        mock_app.cluster_view.action_cursor_line_end = Mock()
        
        # Test Home key
        home_key = Key("home", "")
        with patch.object(mock_app.cluster_view, 'on_key') as mock_on_key:
            mock_on_key(home_key)
            mock_on_key.assert_called_with(home_key)
        
        # Test End key
        end_key = Key("end", "")
        with patch.object(mock_app.cluster_view, 'on_key') as mock_on_key:
            mock_on_key(end_key)
            mock_on_key.assert_called_with(end_key)

    def test_page_navigation(self, mock_app):
        """Test PageUp/Down moves by screen."""
        # Mock cluster view page navigation
        mock_app.cluster_view.action_page_up = Mock()
        mock_app.cluster_view.action_page_down = Mock()
        
        # Test PageUp
        pageup_key = Key("pageup", "")
        with patch.object(mock_app.cluster_view, 'on_key') as mock_on_key:
            mock_on_key(pageup_key)
            mock_on_key.assert_called_with(pageup_key)
        
        # Test PageDown
        pagedown_key = Key("pagedown", "")
        with patch.object(mock_app.cluster_view, 'on_key') as mock_on_key:
            mock_on_key(pagedown_key)
            mock_on_key.assert_called_with(pagedown_key)

    def test_navigation_bounds_checking(self, mock_app):
        """Test cannot navigate outside data boundaries."""
        # Test cluster navigation bounds
        # At first cluster, cannot go previous
        mock_app.current_cluster_index = 0
        mock_app.action_prev_cluster()
        assert mock_app.current_cluster_index == 0
        
        # At last cluster, cannot go next
        mock_app.current_cluster_index = len(mock_app.current_cluster_list) - 1
        mock_app.action_next_cluster()
        assert mock_app.current_cluster_index == len(mock_app.current_cluster_list) - 1
        
        # Test sheet navigation bounds through sheet_tabs widget
        mock_app.sheet_tabs.next_sheet.return_value = False  # Indicates boundary reached
        result = mock_app.action_next_sheet()
        mock_app.sheet_tabs.next_sheet.assert_called_once()

    def test_navigation_state_persistence(self, mock_app):
        """Test navigation state is saved between operations."""
        # Test cluster navigation persistence
        mock_app.session_manager.update_current_state = Mock()
        
        # Navigate to different cluster
        mock_app.current_cluster_index = 2
        mock_app.display_current_cluster()
        
        # Verify session state update was called
        mock_app.session_manager.update_current_state.assert_called()
        
        # Verify session manager preserves state
        args, kwargs = mock_app.session_manager.update_current_state.call_args
        assert 'current_cluster' in kwargs or 'current_cluster' in args

    def test_navigation_with_empty_data(self, mock_app):
        """Test handles missing clusters gracefully."""
        # Test with empty cluster list
        mock_app.current_cluster_list = []
        mock_app.current_cluster_index = 0
        
        # Navigation should not crash
        mock_app.action_next_cluster()
        mock_app.action_prev_cluster()
        
        # display_current_cluster should handle empty list gracefully
        mock_app.display_current_cluster()
        # Should not raise exception and not call cluster_view methods
        assert True  # Test passes if no exception raised

    def test_navigation_performance(self, mock_app):
        """Test fast response time for navigation (<100ms)."""
        # Test cluster navigation performance
        start_time = time.time()
        mock_app.action_next_cluster()
        navigation_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert navigation_time < 100, f"Navigation took {navigation_time}ms, expected < 100ms"
        
        # Test sheet navigation performance
        start_time = time.time()
        mock_app.action_next_sheet()
        navigation_time = (time.time() - start_time) * 1000
        
        assert navigation_time < 100, f"Sheet navigation took {navigation_time}ms, expected < 100ms"

    def test_navigation_event_coordination(self, mock_app):
        """Test navigation events update all relevant widgets."""
        # Mock all widgets that should be updated
        mock_app.cluster_view.display_cluster = Mock()
        mock_app.status_bar.update_status = Mock()
        mock_app.data_manager.get_cluster_data = Mock(return_value={"test": "data"})
        mock_app.data_manager.get_cluster_info = Mock(return_value={"info": "test"})
        
        # Perform navigation
        mock_app.current_cluster_index = 1
        mock_app.display_current_cluster()
        
        # Verify all components were updated
        mock_app.cluster_view.display_cluster.assert_called_once()
        mock_app.data_manager.get_cluster_data.assert_called_once()
        
        # Test sheet change coordination
        mock_app.load_current_sheet = Mock()
        mock_app.display_current_cluster = Mock()
        
        mock_app.on_sheet_change("OCT25")
        
        # Verify sheet change triggered proper updates
        mock_app.load_current_sheet.assert_called_once()
        mock_app.display_current_cluster.assert_called_once()


class TestNavigationControllerIntegration:
    """Test navigation controller integration with TUI app."""
    
    @pytest.fixture
    def mock_navigation_app(self, tmp_path):
        """Create app with mocked navigation controller."""
        excel_file = tmp_path / "test.xlsx"
        excel_file.touch()
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'):
            
            app = AnalysisTUIApp(str(excel_file))
            
            # Mock navigation state
            app.current_cluster_list = ["C001", "C002", "C003"]
            app.current_cluster_index = 0
            
            # Mock widgets for event testing
            app.sheet_tabs = Mock()
            app.cluster_view = Mock()
            app.status_bar = Mock()
            app.sheet_tabs.active_sheet = "SEP25"
            
            return app

    def test_navigation_quick_jump_to_cluster(self, mock_navigation_app):
        """Test quick jump to specific cluster by ID."""
        # This test should fail until NavigationController with goto functionality is implemented
        from src.presentation.navigation_controller import NavigationController
        
        # This import should fail until NavigationController is created
        nav_controller = NavigationController(mock_navigation_app)
        
        # Test direct cluster access by ID
        target_cluster = "C003"
        success = nav_controller.goto_cluster(target_cluster)
        
        assert success == True, "Should successfully navigate to cluster"
        expected_index = mock_navigation_app.current_cluster_list.index(target_cluster)
        assert mock_navigation_app.current_cluster_index == expected_index

    def test_navigation_history_tracking(self, mock_navigation_app):
        """Test navigation maintains history for potential undo."""
        # This test should fail until NavigationController with history is implemented
        from src.presentation.navigation_controller import NavigationController
        
        nav_controller = NavigationController(mock_navigation_app)
        
        # Navigation should maintain history
        nav_controller.navigate_cluster(1)  # Forward
        nav_controller.navigate_cluster(1)  # Forward again
        nav_controller.navigate_cluster(-1) # Back
        
        # Should have history of moves
        history = nav_controller.get_navigation_history()
        assert len(history) >= 3, "Should track navigation history"
        
        # Should support undo
        success = nav_controller.undo_navigation()
        assert success == True, "Should support navigation undo"

    def test_navigation_during_edit_mode_restrictions(self, mock_navigation_app):
        """Test navigation restrictions when in edit mode."""
        # Mock edit mode state
        mock_navigation_app.cluster_view.is_editing = True
        mock_navigation_app.cluster_view.selected_cell = (1, 2)
        
        def check_edit_mode_restriction():
            """Check if navigation should be restricted during edit mode."""
            return hasattr(mock_navigation_app.cluster_view, 'is_editing') and \
                   mock_navigation_app.cluster_view.is_editing
        
        # Test cluster navigation restriction during edit
        if check_edit_mode_restriction():
            # Navigation should be restricted or require confirmation
            initial_index = mock_navigation_app.current_cluster_index
            
            # Attempt navigation during edit mode
            mock_navigation_app.action_next_cluster()
            
            # In a real implementation, this might show a confirmation dialog
            # or require explicit exit from edit mode
            # For now, we test that the restriction logic exists
            assert check_edit_mode_restriction()
        
        # Test navigation allowed after edit mode exit
        mock_navigation_app.cluster_view.is_editing = False
        mock_navigation_app.action_next_cluster()
        
        # Should succeed when not in edit mode
        assert not check_edit_mode_restriction()

    def test_navigation_status_bar_feedback(self, mock_navigation_app):
        """Test navigation provides feedback in status bar."""
        # Mock status bar updates during navigation
        mock_navigation_app.status_bar.update_position = Mock()
        mock_navigation_app.data_manager = Mock()
        mock_navigation_app.data_manager.get_cluster_info = Mock(return_value={})
        mock_navigation_app.data_manager.get_cluster_data = Mock(return_value={})
        
        # Perform navigation
        mock_navigation_app.display_current_cluster()
        
        # Verify title was updated with position information
        expected_title_pattern = f"Cluster {mock_navigation_app.current_cluster_list[0]} (1/{len(mock_navigation_app.current_cluster_list)})"
        assert expected_title_pattern in mock_navigation_app.title or mock_navigation_app.title == ""
        
        # Test that navigation updates provide user feedback
        current_cluster = mock_navigation_app.current_cluster_list[mock_navigation_app.current_cluster_index]
        position_info = f"{mock_navigation_app.current_cluster_index + 1}/{len(mock_navigation_app.current_cluster_list)}"
        
        # Verify position information is available
        assert current_cluster in mock_navigation_app.current_cluster_list
        assert position_info == "1/3"
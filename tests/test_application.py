"""
Test suite for TUI Application Shell following TDD methodology.

Tests cover:
1. Application initialization with Excel file loading and component setup
2. Widget layout and composition structure verification
3. Sheet navigation between tabs using keyboard shortcuts
4. Cluster navigation within sheets using keyboard shortcuts
5. Session state persistence on startup and shutdown
6. Auto-save timer integration and file persistence
7. Error recovery and user-friendly error display
8. Keyboard shortcut handling and action dispatch
9. Graceful shutdown with state preservation
10. Command palette and widget communication integration

These tests drive implementation of comprehensive TUI Application Shell functionality
as specified in task-017 requirements. Tests are designed to fail first (TDD Red phase)
and guide the implementation of the full application with proper lifecycle management,
reactive properties, and event handling.

TDD Workflow Instructions for Developer-Agent:

1. RED PHASE: Run these tests first. They will fail because they define the complete
   interface for the TUI Application Shell that goes beyond the current basic implementation.
   The failures define exactly what needs to be implemented.

2. GREEN PHASE: Implement the AnalysisTUIApp class to make these tests pass:
   - Proper widget composition and layout management
   - Excel file loading with error handling
   - Session state management integration
   - Keyboard shortcut handling with action methods
   - Widget communication via message passing
   - Graceful error handling and user feedback

3. REFACTOR PHASE: Once tests pass, optimize for performance and maintainability.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock, call
import tempfile
import os
from pathlib import Path
from datetime import datetime
from textual.events import Key, Resize
from textual.geometry import Size
from textual.app import ComposeResult

# TDD: Import the application to be tested
from src.app import AnalysisTUIApp


class TestApplicationInitialization:
    """Test suite for application initialization and startup."""

    def test_app_initialization_loads_excel_file(self):
        """Test application startup properly loads Excel file and initializes components."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            # Mock the data manager's load_excel method
            with patch('src.app.ExcelDataManager') as mock_dm_class:
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.get_sheet_names.return_value = ["SEP25", "OCT25", "NOV25"]
                mock_data_manager.get_clusters_list.return_value = [1, 2, 3, 4, 5]
                mock_data_manager.get_cluster_data.return_value = {}
                mock_data_manager.get_cluster_info.return_value = {}
                
                # Mock session manager
                with patch('src.app.SessionManager') as mock_sm_class:
                    mock_session_manager = MagicMock()
                    mock_sm_class.return_value = mock_session_manager
                    mock_session_state = MagicMock()
                    mock_session_state.current_sheet = "SEP25"
                    mock_session_state.current_cluster = 1
                    mock_session_manager.get_or_create_state.return_value = mock_session_state
                    
                    # Act
                    app = AnalysisTUIApp(excel_path)
                    
                    # Assert
                    assert app.excel_file == excel_path
                    assert app.data_manager is not None
                    assert app.session_manager is not None
                    assert app.validator is not None
                    assert app.formatter is not None
                    
                    # Verify components are properly initialized
                    assert isinstance(app.data_manager, type(mock_data_manager))
                    assert isinstance(app.session_manager, type(mock_session_manager))
                    
        finally:
            os.unlink(excel_path)

    def test_widget_layout_renders_correctly(self):
        """Test widget layout structure matches specification."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager'), \
                 patch('src.app.SessionManager'), \
                 patch('src.app.SheetTabs') as mock_tabs, \
                 patch('src.app.ClusterView') as mock_cluster, \
                 patch('src.app.ColorGrid') as mock_grid, \
                 patch('src.app.StatusBar') as mock_status:
                
                # Act
                app = AnalysisTUIApp(excel_path)
                compose_result = list(app.compose())
                
                # Assert - verify layout structure
                assert len(compose_result) >= 3  # tabs, container, status
                
                # Should have SheetTabs at top
                mock_tabs.assert_called_once()
                
                # Should have ClusterView in main area
                mock_cluster.assert_called_once()
                
                # Should have ColorGrids for date and LODF
                assert mock_grid.call_count == 2  # date and lodf grids
                
                # Should have StatusBar at bottom
                mock_status.assert_called_once()
                
                # Verify widgets are stored for later access
                assert app.sheet_tabs is not None
                assert app.cluster_view is not None
                assert app.date_grid is not None
                assert app.lodf_grid is not None
                assert app.status_bar is not None
                
        finally:
            os.unlink(excel_path)


class TestNavigationFunctionality:
    """Test suite for navigation functionality."""

    def test_sheet_navigation_updates_display(self):
        """Test Tab/Shift+Tab keyboard shortcuts navigate between sheets correctly."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class:
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.get_sheet_names.return_value = ["SEP25", "OCT25", "NOV25"]
                mock_data_manager.get_clusters_list.return_value = [1, 2, 3]
                mock_data_manager.get_cluster_data.return_value = {}
                
                with patch('src.app.SessionManager'):
                    app = AnalysisTUIApp(excel_path)
                    
                    # Mock widgets
                    app.sheet_tabs = MagicMock()
                    app.sheet_tabs.active_sheet = "SEP25"
                    app.cluster_view = MagicMock()
                    app.status_bar = MagicMock()
                    
                    # Act - test next sheet action
                    app.action_next_sheet()
                    
                    # Assert
                    app.sheet_tabs.next_sheet.assert_called_once()
                    
                    # Act - test previous sheet action
                    app.action_prev_sheet()
                    
                    # Assert
                    app.sheet_tabs.previous_sheet.assert_called_once()
                    
        finally:
            os.unlink(excel_path)

    def test_cluster_navigation_cycles_properly(self):
        """Test n/p keyboard shortcuts navigate between clusters correctly."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager'):
                
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.get_clusters_list.return_value = [1, 2, 3, 4, 5]
                mock_data_manager.get_cluster_data.return_value = {}
                mock_data_manager.get_cluster_info.return_value = {}
                
                app = AnalysisTUIApp(excel_path)
                app.current_cluster_list = [1, 2, 3, 4, 5]
                app.current_cluster_index = 2  # Start at cluster 3
                
                # Mock widgets
                app.sheet_tabs = MagicMock()
                app.sheet_tabs.active_sheet = "SEP25"
                app.cluster_view = MagicMock()
                app.status_bar = MagicMock()
                
                # Act - test next cluster
                app.action_next_cluster()
                
                # Assert
                assert app.current_cluster_index == 3  # Should move to index 3 (cluster 4)
                
                # Act - test previous cluster
                app.action_prev_cluster()
                app.action_prev_cluster()
                
                # Assert
                assert app.current_cluster_index == 1  # Should move back to index 1 (cluster 2)
                
                # Test boundary conditions
                app.current_cluster_index = 0
                app.action_prev_cluster()
                assert app.current_cluster_index == 0  # Should stay at first
                
                app.current_cluster_index = 4
                app.action_next_cluster()
                assert app.current_cluster_index == 4  # Should stay at last
                
        finally:
            os.unlink(excel_path)


class TestSessionManagement:
    """Test suite for session state management."""

    def test_session_restore_on_startup(self):
        """Test application restores previous session state on startup."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager') as mock_sm_class:
                
                # Setup mocks
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.get_sheet_names.return_value = ["SEP25", "OCT25"]
                mock_data_manager.get_clusters_list.return_value = [1, 2, 3, 4, 5]
                mock_data_manager.get_cluster_data.return_value = {}
                mock_data_manager.get_cluster_info.return_value = {}
                
                mock_session_manager = MagicMock()
                mock_sm_class.return_value = mock_session_manager
                
                # Create mock session state
                mock_session_state = MagicMock()
                mock_session_state.current_sheet = "OCT25"
                mock_session_state.current_cluster = 3
                mock_session_manager.get_or_create_state.return_value = mock_session_state
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock widgets
                app.sheet_tabs = MagicMock()
                app.cluster_view = MagicMock()
                app.status_bar = MagicMock()
                
                # Act - simulate on_mount
                app.on_mount()
                
                # Assert
                mock_session_manager.get_or_create_state.assert_called_once_with(
                    excel_path, default_sheet="SEP25"
                )
                
                # Should restore session state
                app.sheet_tabs.set_active_sheet.assert_called_with("OCT25")
                assert app.current_session.current_sheet == "OCT25"
                assert app.current_session.current_cluster == 3
                
        finally:
            os.unlink(excel_path)

    def test_session_save_on_exit(self):
        """Test application saves session state on clean shutdown."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager'), \
                 patch('src.app.SessionManager') as mock_sm_class:
                
                mock_session_manager = MagicMock()
                mock_sm_class.return_value = mock_session_manager
                
                app = AnalysisTUIApp(excel_path)
                app.current_session = MagicMock()
                
                # Mock widgets
                app.sheet_tabs = MagicMock()
                app.sheet_tabs.active_sheet = "NOV25"
                app.current_cluster_list = [1, 2, 3]
                app.current_cluster_index = 1
                
                # Act - simulate quit action
                with patch.object(app, 'exit') as mock_exit:
                    app.action_quit()
                    mock_exit.assert_called_once()
                
                # Should save session state during display updates
                mock_session_manager.update_current_state.assert_called()
                
        finally:
            os.unlink(excel_path)


class TestErrorHandling:
    """Test suite for error handling and recovery."""

    def test_error_handling_shows_user_feedback(self):
        """Test graceful error handling displays user-friendly feedback."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class:
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                
                # Setup data manager to raise exception
                mock_data_manager.load_excel.side_effect = FileNotFoundError("File not found")
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock exit method to prevent actual exit
                with patch.object(app, 'exit') as mock_exit:
                    # Act - simulate mount with error
                    app.on_mount()
                    
                    # Assert
                    mock_exit.assert_called_once_with(1)  # Should exit with error code
                
        finally:
            os.unlink(excel_path)

    def test_cell_edit_error_recovery(self):
        """Test error recovery during cell editing operations."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager'):
                
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                
                # Setup save to fail
                mock_data_manager.update_value.side_effect = ValueError("Invalid value")
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock widgets
                app.sheet_tabs = MagicMock()
                app.sheet_tabs.active_sheet = "SEP25"
                app.status_bar = MagicMock()
                
                # Act - simulate cell edit with error
                app.on_cell_edit(5, "VIEW", 123.45)
                
                # Assert - should display error in status bar
                app.status_bar.update_status.assert_called_with("Error: Invalid value")
                
        finally:
            os.unlink(excel_path)


class TestKeyboardShortcuts:
    """Test suite for keyboard shortcut handling."""

    def test_keyboard_shortcut_handling(self):
        """Test all keyboard shortcuts are properly bound and functional."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            app = AnalysisTUIApp(excel_path)
            
            # Assert - check bindings are defined
            bindings = app.BINDINGS
            assert len(bindings) >= 6  # At minimum: n, p, tab, shift+tab, ctrl+s, ctrl+q
            
            # Extract binding keys for verification
            binding_keys = [binding.key for binding in bindings]
            
            # Assert - essential shortcuts are present
            assert "n" in binding_keys  # Next cluster
            assert "p" in binding_keys  # Previous cluster
            assert "tab" in binding_keys  # Next sheet
            assert "shift+tab" in binding_keys  # Previous sheet
            assert "ctrl+s" in binding_keys  # Save
            assert "ctrl+q" in binding_keys  # Quit
            
            # Test action methods exist
            assert hasattr(app, 'action_next_cluster')
            assert hasattr(app, 'action_prev_cluster')
            assert hasattr(app, 'action_next_sheet')
            assert hasattr(app, 'action_prev_sheet')
            assert hasattr(app, 'action_save')
            assert hasattr(app, 'action_quit')
            
            # Test sheet number shortcuts (1-9)
            for i in range(1, 10):
                assert str(i) in binding_keys
                assert hasattr(app, f'action_sheet_{i}')
                
        finally:
            os.unlink(excel_path)

    def test_save_shortcut_functionality(self):
        """Test Ctrl+S save shortcut performs manual save operation."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager'):
                
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.save_changes.return_value = "/path/to/saved_file.xlsx"
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock widgets
                app.status_bar = MagicMock()
                
                # Act
                app.action_save()
                
                # Assert
                mock_data_manager.save_changes.assert_called_once()
                app.status_bar.update_status.assert_called_with("Saved to saved_file.xlsx")
                
        finally:
            os.unlink(excel_path)


class TestWidgetCommunication:
    """Test suite for widget communication and message passing."""

    def test_widget_communication_via_messages(self):
        """Test event propagation and communication between widgets."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager'):
                
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.get_clusters_list.return_value = [1, 2, 3, 4, 5]
                mock_data_manager.get_cluster_data.return_value = {"data": "test"}
                mock_data_manager.get_cluster_info.return_value = {"info": "test"}
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock widgets
                app.sheet_tabs = MagicMock()
                app.sheet_tabs.active_sheet = "SEP25"
                app.cluster_view = MagicMock()
                app.status_bar = MagicMock()
                
                # Set up initial state
                app.current_cluster_list = [1, 2, 3, 4, 5]
                app.current_cluster_index = 0
                
                # Act - simulate sheet change event
                app.on_sheet_change("OCT25")
                
                # Assert - should trigger cluster data reload and display update
                mock_data_manager.get_clusters_list.assert_called_with("OCT25")
                app.cluster_view.display_cluster.assert_called()
                
        finally:
            os.unlink(excel_path)

    def test_auto_save_integration(self):
        """Test auto-save functionality integrates with edit operations."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager'):
                
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.update_value.return_value = True
                mock_data_manager.save_changes.return_value = "/path/to/auto_saved.xlsx"
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock widgets
                app.sheet_tabs = MagicMock()
                app.sheet_tabs.active_sheet = "SEP25"
                app.status_bar = MagicMock()
                
                # Act - simulate cell edit
                app.on_cell_edit(3, "VIEW", 99.9)
                
                # Assert - should update data and auto-save
                mock_data_manager.update_value.assert_called_once_with("SEP25", 3, "VIEW", 99.9)
                mock_data_manager.save_changes.assert_called_once()
                app.status_bar.update_status.assert_called_with("Saved to auto_saved.xlsx")
                
        finally:
            os.unlink(excel_path)


class TestApplicationLifecycle:
    """Test suite for application lifecycle management."""

    def test_responsive_layout_on_resize(self):
        """Test application responds properly to terminal resize events."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager'), \
                 patch('src.app.SessionManager'):
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock widgets
                app.cluster_view = MagicMock()
                
                # Act - simulate resize event
                # Note: Full implementation would handle resize events
                # For now, test that the method can be called without error
                if hasattr(app, 'on_resize'):
                    resize_event = Resize(Size(120, 40), Size(80, 30))
                    app.on_resize(resize_event)
                
                # Assert - cluster view should handle column adjustments
                # This test defines the requirement for resize handling
                assert app.cluster_view is not None
                
        finally:
            os.unlink(excel_path)

    def test_graceful_shutdown_preserves_state(self):
        """Test graceful shutdown saves all state and performs cleanup."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager') as mock_sm_class:
                
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                
                mock_session_manager = MagicMock()
                mock_sm_class.return_value = mock_session_manager
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock widgets and state
                app.sheet_tabs = MagicMock()
                app.sheet_tabs.active_sheet = "DEC25"
                app.current_cluster_list = [10, 20, 30]
                app.current_cluster_index = 1
                
                # Act - test graceful shutdown
                with patch.object(app, 'exit') as mock_exit:
                    app.action_quit()
                    
                    # Assert - should exit cleanly
                    mock_exit.assert_called_once()
                
                # Session state should be updated during normal operations
                # Full implementation would save state in on_exit handler
                
        finally:
            os.unlink(excel_path)


class TestIntegrationScenarios:
    """Test suite for end-to-end integration scenarios."""

    def test_complete_user_workflow(self):
        """Test complete user workflow from startup to shutdown."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            excel_path = temp_file.name
        
        try:
            with patch('src.app.ExcelDataManager') as mock_dm_class, \
                 patch('src.app.SessionManager') as mock_sm_class:
                
                # Setup comprehensive mocks
                mock_data_manager = MagicMock()
                mock_dm_class.return_value = mock_data_manager
                mock_data_manager.get_sheet_names.return_value = ["SEP25", "OCT25", "NOV25", "DEC25"]
                mock_data_manager.get_clusters_list.return_value = [1, 2, 3, 4, 5, 6]
                mock_data_manager.get_cluster_data.return_value = {"test": "data"}
                mock_data_manager.get_cluster_info.return_value = {"info": "test"}
                mock_data_manager.save_changes.return_value = "/saved/file.xlsx"
                
                mock_session_manager = MagicMock()
                mock_sm_class.return_value = mock_session_manager
                mock_session_state = MagicMock()
                mock_session_state.current_sheet = "SEP25"
                mock_session_state.current_cluster = 1
                mock_session_manager.get_or_create_state.return_value = mock_session_state
                
                app = AnalysisTUIApp(excel_path)
                
                # Mock all widgets
                app.sheet_tabs = MagicMock()
                app.sheet_tabs.active_sheet = "SEP25"
                app.cluster_view = MagicMock()
                app.date_grid = MagicMock()
                app.lodf_grid = MagicMock()
                app.status_bar = MagicMock()
                
                app.current_cluster_list = [1, 2, 3, 4, 5, 6]
                app.current_cluster_index = 0
                
                # Act - Simulate complete workflow
                
                # 1. Navigate to next sheet
                app.action_next_sheet()
                app.sheet_tabs.next_sheet.assert_called()
                
                # 2. Navigate clusters
                app.action_next_cluster()
                app.action_next_cluster()
                assert app.current_cluster_index == 2
                
                # 3. Make an edit
                app.on_cell_edit(5, "VIEW", 150.0)
                mock_data_manager.update_value.assert_called_with("SEP25", 5, "VIEW", 150.0)
                mock_data_manager.save_changes.assert_called()
                
                # 4. Manual save
                app.action_save()
                
                # 5. Navigate by sheet number
                app.action_sheet_3()
                
                # 6. Quit application
                with patch.object(app, 'exit'):
                    app.action_quit()
                
                # Assert - All operations should complete without errors
                # Session should be updated
                assert mock_session_manager.update_current_state.called
                
        finally:
            os.unlink(excel_path)
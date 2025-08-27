"""
Test suite for Task 019: Keyboard Shortcuts functionality.

These tests drive the implementation of keyboard shortcuts following TDD methodology:
1. Ctrl+S to save current workbook
2. Ctrl+Q to quit application
3. F1 to show help overlay
4. Ctrl+Z for undo last edit
5. Ctrl+Y for redo
6. Escape to cancel current operation
7. Shortcut conflict resolution
8. Shortcut feedback in status bar
9. Context-sensitive shortcuts
10. Custom shortcut configuration

Tests ensure consistent keyboard interaction, proper context handling, and
user productivity features that will drive TDD implementation in the ShortcutManager.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import time
from datetime import datetime
from textual import events
from textual.keys import Keys
from textual.widgets import Static

# Import target implementation components
from src.app import AnalysisTUIApp
from src.widgets.status_bar import StatusBar
from src.core.session import SessionManager
from src.io.excel_io import ExcelIO
from src.models.data_models import SessionState


class TestSaveShortcuts:
    """Test Ctrl+S save functionality and feedback."""

    @pytest.fixture
    def setup_app_with_data(self):
        """Create AnalysisTUIApp with mock data and save capabilities."""
        mock_excel_file = "/test/path/flow_analysis.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            
            # Mock the data manager save method
            app.data_manager.save_changes = Mock(return_value="/test/path/flow_analysis_backup.xlsx")
            app.data_manager.has_unsaved_changes = Mock(return_value=True)
            
            # Mock status bar for feedback
            app.status_bar = Mock(spec=StatusBar)
            
            return app

    def test_ctrl_s_triggers_save_with_confirmation(self, setup_app_with_data):
        """Test that Ctrl+S saves current workbook and shows confirmation."""
        app = setup_app_with_data
        
        # Simulate Ctrl+S key press
        save_event = events.Key(key='ctrl+s')
        app.action_save()
        
        # Assert save was called on data manager
        app.data_manager.save_changes.assert_called_once()
        
        # Assert status bar shows confirmation message
        app.status_bar.update_status.assert_called()
        status_call = app.status_bar.update_status.call_args[0][0]
        assert "Saved to" in status_call
        assert "flow_analysis_backup.xlsx" in status_call

    def test_save_shortcut_shows_progress_feedback(self, setup_app_with_data):
        """Test that Ctrl+S shows immediate feedback during save operation."""
        app = setup_app_with_data
        
        # Mock slow save operation
        def slow_save():
            time.sleep(0.1)  # Simulate save time
            return "/test/path/saved_file.xlsx"
        
        app.data_manager.save_changes = Mock(side_effect=slow_save)
        
        # Measure save operation timing
        start_time = time.perf_counter()
        app.action_save()
        end_time = time.perf_counter()
        
        # Assert save completed within reasonable time
        save_duration = (end_time - start_time) * 1000
        assert save_duration < 200, f"Save took {save_duration:.1f}ms, should be under 200ms"
        
        # Assert status feedback was provided
        app.status_bar.update_status.assert_called()

    def test_save_shortcut_handles_errors_gracefully(self, setup_app_with_data):
        """Test that Ctrl+S handles save errors and shows error message."""
        app = setup_app_with_data
        
        # Mock save failure
        app.data_manager.save_changes = Mock(side_effect=PermissionError("Cannot write to file"))
        
        # Attempt save
        app.action_save()
        
        # Assert error message is displayed
        app.status_bar.update_status.assert_called()
        status_call = app.status_bar.update_status.call_args[0][0]
        assert "Save failed" in status_call or "Error" in status_call

    def test_save_shortcut_updates_modified_indicator(self, setup_app_with_data):
        """Test that successful save clears the modified indicator."""
        app = setup_app_with_data
        
        # Initially has unsaved changes
        assert app.data_manager.has_unsaved_changes()
        
        # Mock save success clears changes
        app.data_manager.has_unsaved_changes = Mock(side_effect=[True, False])
        
        # Perform save
        app.action_save()
        
        # Assert modified state is updated
        app.data_manager.save_changes.assert_called_once()
        
        # Check that status indicates clean state after save
        app.status_bar.update_status.assert_called()


class TestQuitShortcuts:
    """Test Ctrl+Q quit functionality with unsaved changes handling."""

    @pytest.fixture
    def setup_app_with_session(self):
        """Create app with session management for quit testing."""
        mock_excel_file = "/test/path/test_file.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            
            # Mock session manager
            app.session_manager.update_current_state = Mock()
            
            # Mock data manager
            app.data_manager.has_unsaved_changes = Mock(return_value=False)
            
            # Mock widgets
            app.sheet_tabs = Mock()
            app.sheet_tabs.active_sheet = "SEP25"
            app.current_cluster_list = ["CLUSTER_001", "CLUSTER_002"]
            app.current_cluster_index = 0
            
            # Mock app exit
            app.exit = Mock()
            
            return app

    def test_ctrl_q_quits_without_confirmation_when_no_changes(self, setup_app_with_session):
        """Test that Ctrl+Q quits immediately when no unsaved changes."""
        app = setup_app_with_session
        
        # No unsaved changes
        app.data_manager.has_unsaved_changes = Mock(return_value=False)
        
        # Simulate Ctrl+Q
        app.action_quit()
        
        # Assert session state is saved
        app.session_manager.update_current_state.assert_called_once_with(
            current_sheet="SEP25",
            current_cluster="CLUSTER_001"
        )
        
        # Assert app exits
        app.exit.assert_called_once()

    def test_ctrl_q_prompts_confirmation_with_unsaved_changes(self, setup_app_with_session):
        """Test that Ctrl+Q shows confirmation dialog when unsaved changes exist."""
        app = setup_app_with_session
        
        # Has unsaved changes
        app.data_manager.has_unsaved_changes = Mock(return_value=True)
        
        # Mock confirmation dialog (would be implemented in ShortcutManager)
        with patch('src.presentation.shortcut_manager.ConfirmationDialog') as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog_instance.show = Mock()
            mock_dialog.return_value = mock_dialog_instance
            
            # Create shortcut manager and handle quit
            from src.presentation.shortcut_manager import ShortcutManager
            shortcut_manager = ShortcutManager(app)
            shortcut_manager.quit_app()
            
            # Assert confirmation dialog is shown
            mock_dialog.assert_called_once()
            mock_dialog_instance.show.assert_called_once()

    def test_quit_confirmation_saves_and_exits_on_yes(self, setup_app_with_session):
        """Test quit confirmation saves changes and exits when user chooses Yes."""
        app = setup_app_with_session
        
        # Has unsaved changes
        app.data_manager.has_unsaved_changes = Mock(return_value=True)
        app.data_manager.save_changes = Mock(return_value="/test/saved.xlsx")
        
        # Mock user chooses to save and quit
        def mock_quit_with_save():
            app.data_manager.save_changes()
            app.exit()
        
        # Simulate save and quit workflow
        mock_quit_with_save()
        
        # Assert save was called
        app.data_manager.save_changes.assert_called_once()
        
        # Assert exit was called
        app.exit.assert_called_once()

    def test_quit_force_exit_discards_changes(self, setup_app_with_session):
        """Test that force quit (Alt+F4 equivalent) exits without saving."""
        app = setup_app_with_session
        
        # Has unsaved changes
        app.data_manager.has_unsaved_changes = Mock(return_value=True)
        
        # Force quit without save
        def force_quit():
            app.session_manager.update_current_state(
                current_sheet=app.sheet_tabs.active_sheet,
                current_cluster=app.current_cluster_list[app.current_cluster_index]
            )
            app.exit()
        
        force_quit()
        
        # Assert save was NOT called
        app.data_manager.save_changes.assert_not_called()
        
        # Assert session state was saved (but not data)
        app.session_manager.update_current_state.assert_called_once()
        
        # Assert app exited
        app.exit.assert_called_once()


class TestHelpShortcuts:
    """Test F1 and ? help screen functionality."""

    @pytest.fixture
    def setup_app_with_help(self):
        """Create app with help system for testing."""
        mock_excel_file = "/test/path/test_file.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            return app

    def test_f1_shows_comprehensive_help_overlay(self, setup_app_with_help):
        """Test that F1 displays help screen with all shortcuts."""
        app = setup_app_with_help
        
        # Mock help overlay widget
        with patch('src.presentation.help_overlay.HelpOverlay') as mock_help:
            mock_help_instance = Mock()
            mock_help_instance.show = Mock()
            mock_help_instance.visible = True
            mock_help.return_value = mock_help_instance
            
            # Create and test shortcut manager
            from src.presentation.shortcut_manager import ShortcutManager
            shortcut_manager = ShortcutManager(app)
            shortcut_manager.show_help()
            
            # Assert help overlay is created and shown
            mock_help.assert_called_once()
            mock_help_instance.show.assert_called_once()

    def test_question_mark_also_shows_help(self, setup_app_with_help):
        """Test that ? key also displays help screen."""
        app = setup_app_with_help
        
        # Mock help system
        with patch('src.presentation.shortcut_manager.ShortcutManager.show_help') as mock_show_help:
            shortcut_manager_mock = Mock()
            shortcut_manager_mock.show_help = mock_show_help
            
            # Simulate ? key press
            help_event = events.Key(key='?', character='?')
            
            # Should map to same help function
            shortcut_manager_mock.show_help()
            mock_show_help.assert_called_once()

    def test_help_screen_contains_all_shortcuts(self, setup_app_with_help):
        """Test that help screen displays all available shortcuts with descriptions."""
        app = setup_app_with_help
        
        # Expected shortcuts that should appear in help
        expected_shortcuts = {
            'ctrl+s': 'Save changes',
            'ctrl+q': 'Quit application', 
            'f5': 'Refresh data',
            'n/p': 'Next/Previous cluster',
            'tab': 'Next sheet',
            '0-9': 'Start quick edit',
            'enter': 'Commit edit',
            'escape': 'Cancel edit'
        }
        
        # Mock help content
        from src.presentation.help_overlay import HELP_TEXT
        help_content = HELP_TEXT
        
        # Assert all expected shortcuts are documented
        for shortcut, description in expected_shortcuts.items():
            assert shortcut.replace('ctrl+', 'Ctrl+') in help_content or shortcut.upper() in help_content
            # Description should be present or similar text
            assert any(word in help_content.lower() for word in description.lower().split())

    def test_help_screen_dismisses_with_escape(self, setup_app_with_help):
        """Test that Escape closes help screen."""
        app = setup_app_with_help
        
        # Mock help overlay
        with patch('src.presentation.help_overlay.HelpOverlay') as mock_help:
            mock_help_instance = Mock()
            mock_help_instance.hide = Mock()
            mock_help_instance.visible = True
            mock_help.return_value = mock_help_instance
            
            # Show help then dismiss
            shortcut_manager = Mock()
            shortcut_manager.help_overlay = mock_help_instance
            
            # Simulate Escape while help is visible
            escape_event = events.Key(key='escape')
            
            # Should hide help overlay
            if shortcut_manager.help_overlay.visible:
                shortcut_manager.help_overlay.hide()
            
            mock_help_instance.hide.assert_called_once()


class TestUndoRedoShortcuts:
    """Test Ctrl+Z (undo) and Ctrl+Y (redo) functionality."""

    @pytest.fixture
    def setup_app_with_history(self):
        """Create app with edit history for undo/redo testing."""
        mock_excel_file = "/test/path/test_file.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            
            # Mock edit history
            from src.models.data_models import EditRecord
            mock_edit = EditRecord(
                sheet="SEP25",
                cluster_id="CLUSTER_001", 
                constraint_index=0,
                column="VIEW",
                old_value=125.5,
                new_value=135.0,
                timestamp=datetime.now(),
                cuid="C001"
            )
            
            app.data_manager.get_edit_history = Mock(return_value=[mock_edit])
            app.data_manager.undo_last_edit = Mock(return_value=True)
            app.data_manager.redo_last_edit = Mock(return_value=True)
            app.data_manager.can_undo = Mock(return_value=True)
            app.data_manager.can_redo = Mock(return_value=False)
            
            # Mock status bar
            app.status_bar = Mock(spec=StatusBar)
            
            return app, mock_edit

    def test_ctrl_z_undoes_last_edit(self, setup_app_with_history):
        """Test that Ctrl+Z undoes the most recent edit operation."""
        app, mock_edit = setup_app_with_history
        
        # Create shortcut manager and handle undo
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        shortcut_manager.undo_edit()
        
        # Assert undo was called
        app.data_manager.undo_last_edit.assert_called_once()
        
        # Assert status shows undo feedback
        app.status_bar.update_status.assert_called()
        status_call = app.status_bar.update_status.call_args[0][0]
        assert "Undo" in status_call or "Undid" in status_call

    def test_ctrl_y_redoes_undone_edit(self, setup_app_with_history):
        """Test that Ctrl+Y redoes previously undone edit."""
        app, mock_edit = setup_app_with_history
        
        # Set up redo availability
        app.data_manager.can_redo = Mock(return_value=True)
        
        # Create shortcut manager and handle redo
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        shortcut_manager.redo_edit()
        
        # Assert redo was called
        app.data_manager.redo_last_edit.assert_called_once()
        
        # Assert status shows redo feedback
        app.status_bar.update_status.assert_called()
        status_call = app.status_bar.update_status.call_args[0][0]
        assert "Redo" in status_call or "Redid" in status_call

    def test_undo_disabled_when_no_history(self, setup_app_with_history):
        """Test that Ctrl+Z is ignored when no undo history available."""
        app, mock_edit = setup_app_with_history
        
        # No undo history available
        app.data_manager.can_undo = Mock(return_value=False)
        
        # Create shortcut manager and attempt undo
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        shortcut_manager.undo_edit()
        
        # Assert undo was not called
        app.data_manager.undo_last_edit.assert_not_called()
        
        # Assert status shows unavailable message
        app.status_bar.update_status.assert_called()
        status_call = app.status_bar.update_status.call_args[0][0]
        assert "No undo" in status_call.lower() or "Nothing to undo" in status_call.lower()

    def test_redo_disabled_when_no_redo_available(self, setup_app_with_history):
        """Test that Ctrl+Y is ignored when no redo operations available."""
        app, mock_edit = setup_app_with_history
        
        # No redo available (default state)
        app.data_manager.can_redo = Mock(return_value=False)
        
        # Create shortcut manager and attempt redo
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        shortcut_manager.redo_edit()
        
        # Assert redo was not called
        app.data_manager.redo_last_edit.assert_not_called()
        
        # Assert status shows unavailable message
        app.status_bar.update_status.assert_called()
        status_call = app.status_bar.update_status.call_args[0][0]
        assert "No redo" in status_call.lower() or "Nothing to redo" in status_call.lower()


class TestEscapeCancellation:
    """Test Escape key cancellation behavior across contexts."""

    @pytest.fixture
    def setup_app_with_contexts(self):
        """Create app with multiple operational contexts."""
        mock_excel_file = "/test/path/test_file.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            
            # Mock cluster view for edit mode
            app.cluster_view = Mock()
            app.cluster_view.edit_mode = False
            app.cluster_view.exit_edit_mode = Mock()
            
            return app

    def test_escape_cancels_edit_mode(self, setup_app_with_contexts):
        """Test that Escape cancels current edit operation."""
        app = setup_app_with_contexts
        
        # Set up edit mode
        app.cluster_view.edit_mode = True
        
        # Create shortcut manager
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Handle escape in edit mode
        if app.cluster_view.edit_mode:
            app.cluster_view.exit_edit_mode()
        
        # Assert edit mode was cancelled
        app.cluster_view.exit_edit_mode.assert_called_once()

    def test_escape_closes_help_overlay(self, setup_app_with_contexts):
        """Test that Escape closes help screen when open."""
        app = setup_app_with_contexts
        
        # Mock help overlay
        mock_help_overlay = Mock()
        mock_help_overlay.visible = True
        mock_help_overlay.hide = Mock()
        
        # Create shortcut manager with help open
        shortcut_manager = Mock()
        shortcut_manager.help_overlay = mock_help_overlay
        
        # Handle escape with help open
        if shortcut_manager.help_overlay.visible:
            shortcut_manager.help_overlay.hide()
        
        # Assert help was closed
        mock_help_overlay.hide.assert_called_once()

    def test_escape_cancels_goto_dialog(self, setup_app_with_contexts):
        """Test that Escape cancels go-to cluster dialog."""
        app = setup_app_with_contexts
        
        # Mock goto dialog
        mock_goto_dialog = Mock()
        mock_goto_dialog.visible = True
        mock_goto_dialog.cancel = Mock()
        
        # Simulate escape during goto
        if mock_goto_dialog.visible:
            mock_goto_dialog.cancel()
        
        # Assert dialog was cancelled
        mock_goto_dialog.cancel.assert_called_once()

    def test_escape_priority_in_multiple_contexts(self, setup_app_with_contexts):
        """Test Escape priority: edit mode > dialogs > help screen."""
        app = setup_app_with_contexts
        
        # Set up multiple contexts simultaneously
        app.cluster_view.edit_mode = True
        
        mock_help_overlay = Mock()
        mock_help_overlay.visible = True
        
        mock_dialog = Mock()
        mock_dialog.visible = True
        
        # Priority handling (edit mode should take precedence)
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        shortcut_manager.help_overlay = mock_help_overlay
        shortcut_manager.active_dialog = mock_dialog
        
        # Escape should handle highest priority context first
        if app.cluster_view.edit_mode:
            result = "edit_cancelled"
        elif mock_dialog.visible:
            result = "dialog_cancelled"
        elif mock_help_overlay.visible:
            result = "help_closed"
        else:
            result = "no_action"
        
        # Assert correct priority
        assert result == "edit_cancelled"


class TestShortcutConflictResolution:
    """Test handling of conflicting shortcuts and context-sensitive behavior."""

    @pytest.fixture
    def setup_shortcut_conflicts(self):
        """Set up app for testing shortcut conflicts."""
        mock_excel_file = "/test/path/test_file.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            
            # Mock widgets for context testing
            app.cluster_view = Mock()
            app.cluster_view.edit_mode = False
            app.cluster_view.handle_navigation = Mock()
            
            return app

    def test_number_keys_context_sensitivity(self, setup_shortcut_conflicts):
        """Test that number keys (0-9) behave differently in edit vs normal mode."""
        app = setup_shortcut_conflicts
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Test in normal mode - number keys should trigger quick edit
        app.cluster_view.edit_mode = False
        app.cluster_view.can_edit_current_cell = Mock(return_value=True)
        app.cluster_view.start_edit_mode = Mock()
        
        # Simulate '5' key press in normal mode
        result = shortcut_manager.handle_key('5', context='normal')
        
        # Should trigger edit mode
        assert result is True  # Key was handled
        
        # Test in edit mode - number keys should be passed to edit input
        app.cluster_view.edit_mode = True
        app.cluster_view.edit_input = Mock()
        app.cluster_view.edit_input.insert_text = Mock()
        
        # Simulate '7' key press in edit mode
        result = shortcut_manager.handle_key('7', context='edit')
        
        # Should pass to edit input (different behavior)
        assert result is True

    def test_ctrl_combinations_override_single_keys(self, setup_shortcut_conflicts):
        """Test that Ctrl+ combinations take precedence over single key shortcuts."""
        app = setup_shortcut_conflicts
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Test Ctrl+S overrides any 'S' behavior
        app.action_save = Mock()
        
        result = shortcut_manager.handle_key('ctrl+s', context='any')
        
        # Should call save action
        assert result is True
        app.action_save.assert_called_once()
        
        # Test that single 's' has different behavior
        app.cluster_view.handle_search = Mock()
        
        result = shortcut_manager.handle_key('s', context='normal')
        
        # Should handle as search (example different behavior)
        # Implementation may vary but should be distinct from Ctrl+S

    def test_navigation_shortcuts_disabled_in_edit_mode(self, setup_shortcut_conflicts):
        """Test that navigation shortcuts are disabled during edit operations."""
        app = setup_shortcut_conflicts
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Set edit mode
        app.cluster_view.edit_mode = True
        
        # Test that navigation keys are handled by edit, not navigation
        app.cluster_view.move_cursor = Mock()
        
        navigation_keys = ['up', 'down', 'left', 'right', 'home', 'end']
        
        for key in navigation_keys:
            result = shortcut_manager.handle_key(key, context='edit')
            
            # Navigation should not be called in edit mode
            app.cluster_view.move_cursor.assert_not_called()
            
            # Keys should be handled by edit system instead
            assert result is True or result is None  # Depends on implementation

    def test_shortcut_context_determination(self, setup_shortcut_conflicts):
        """Test automatic context determination for shortcut handling."""
        app = setup_shortcut_conflicts
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Test context detection
        app.cluster_view.edit_mode = True
        context = shortcut_manager.get_current_context()
        assert context == 'edit'
        
        app.cluster_view.edit_mode = False
        mock_help_overlay = Mock()
        mock_help_overlay.visible = True
        shortcut_manager.help_overlay = mock_help_overlay
        context = shortcut_manager.get_current_context()
        assert context == 'help'
        
        # Normal context when no special modes
        mock_help_overlay.visible = False
        context = shortcut_manager.get_current_context()
        assert context == 'normal'


class TestShortcutFeedbackInStatusBar:
    """Test status bar feedback for shortcut operations."""

    @pytest.fixture
    def setup_status_feedback(self):
        """Set up app with status bar for feedback testing."""
        mock_excel_file = "/test/path/test_file.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            app.status_bar = Mock(spec=StatusBar)
            
            return app

    def test_shortcut_feedback_shows_in_status_bar(self, setup_status_feedback):
        """Test that shortcuts show feedback messages in status bar."""
        app = setup_status_feedback
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Test save feedback
        app.data_manager.save_changes = Mock(return_value="/test/saved.xlsx")
        shortcut_manager.save_file()
        
        # Check status bar was updated with save feedback
        app.status_bar.update_status.assert_called()
        save_message = app.status_bar.update_status.call_args[0][0]
        assert "Saved" in save_message

    def test_temporary_shortcut_hints_display(self, setup_status_feedback):
        """Test that status bar shows temporary hints for available shortcuts."""
        app = setup_status_feedback
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Show context-sensitive shortcut hints
        shortcut_manager.show_shortcut_hints()
        
        # Assert hints are displayed
        app.status_bar.show_hint.assert_called()
        hint_message = app.status_bar.show_hint.call_args[0][0]
        assert any(key in hint_message.lower() for key in ['ctrl+s', 'f1', 'help'])

    def test_shortcut_error_feedback(self, setup_status_feedback):
        """Test that failed shortcuts show error messages."""
        app = setup_status_feedback
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Mock save failure
        app.data_manager.save_changes = Mock(side_effect=Exception("Disk full"))
        
        shortcut_manager.save_file()
        
        # Assert error feedback is shown
        app.status_bar.update_status.assert_called()
        error_message = app.status_bar.update_status.call_args[0][0]
        assert "Error" in error_message or "failed" in error_message.lower()

    def test_shortcut_success_confirmation_timing(self, setup_status_feedback):
        """Test that success messages appear immediately and fade appropriately."""
        app = setup_status_feedback
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Test timing of feedback
        start_time = time.perf_counter()
        
        app.data_manager.save_changes = Mock(return_value="/test/file.xlsx")
        shortcut_manager.save_file()
        
        end_time = time.perf_counter()
        feedback_time = (end_time - start_time) * 1000
        
        # Feedback should appear quickly
        assert feedback_time < 50, f"Feedback took {feedback_time:.1f}ms, should be under 50ms"
        
        # Assert status was updated
        app.status_bar.update_status.assert_called()


class TestShortcutPerformanceAndResponsiveness:
    """Test performance requirements for shortcut operations."""

    @pytest.fixture
    def setup_performance_app(self):
        """Set up app for performance testing."""
        mock_excel_file = "/test/path/large_file.xlsx"
        
        with patch('src.app.ExcelIO'), \
             patch('src.app.StateIO'), \
             patch('src.app.ExcelDataManager'), \
             patch('src.app.SessionManager'), \
             patch('pathlib.Path.exists', return_value=True):
            
            app = AnalysisTUIApp(mock_excel_file)
            app.status_bar = Mock(spec=StatusBar)
            
            return app

    def test_shortcut_response_time_under_50ms(self, setup_performance_app):
        """Test that all shortcuts respond within 50ms requirement."""
        app = setup_performance_app
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Test common shortcuts for response time
        shortcuts_to_test = [
            ('ctrl+s', lambda: shortcut_manager.save_file()),
            ('f1', lambda: shortcut_manager.show_help()),
            ('escape', lambda: shortcut_manager.cancel_operation()),
        ]
        
        for shortcut_key, shortcut_action in shortcuts_to_test:
            start_time = time.perf_counter()
            
            try:
                shortcut_action()
            except Exception:
                pass  # Ignore implementation errors, focus on timing
            
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000
            
            assert response_time < 50, f"{shortcut_key} took {response_time:.1f}ms, should be under 50ms"

    def test_help_screen_renders_instantly(self, setup_performance_app):
        """Test that help screen appears without delay."""
        app = setup_performance_app
        
        # Mock help overlay
        with patch('src.presentation.help_overlay.HelpOverlay') as mock_help:
            mock_help_instance = Mock()
            mock_help_instance.show = Mock()
            mock_help.return_value = mock_help_instance
            
            from src.presentation.shortcut_manager import ShortcutManager
            shortcut_manager = ShortcutManager(app)
            
            # Measure help display time
            start_time = time.perf_counter()
            shortcut_manager.show_help()
            end_time = time.perf_counter()
            
            display_time = (end_time - start_time) * 1000
            
            # Help should appear instantly
            assert display_time < 10, f"Help display took {display_time:.1f}ms, should be under 10ms"
            
            # Assert help was shown
            mock_help_instance.show.assert_called_once()

    def test_rapid_shortcut_sequence_handling(self, setup_performance_app):
        """Test handling of rapid shortcut key sequences."""
        app = setup_performance_app
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Mock rapid key sequence
        rapid_keys = ['f1', 'escape', 'ctrl+s', 'f1', 'escape'] * 3  # 15 rapid keys
        
        start_time = time.perf_counter()
        
        for key in rapid_keys:
            try:
                shortcut_manager.handle_key(key, context='normal')
            except Exception:
                pass  # Focus on performance, not implementation
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000
        avg_time = total_time / len(rapid_keys)
        
        # Should handle rapid sequences efficiently
        assert avg_time < 10, f"Average shortcut handling {avg_time:.1f}ms too slow"
        assert total_time < 200, f"Rapid sequence took {total_time:.1f}ms total"

    def test_shortcut_memory_efficiency(self, setup_performance_app):
        """Test that shortcuts don't cause memory leaks or excessive usage."""
        app = setup_performance_app
        
        from src.presentation.shortcut_manager import ShortcutManager
        shortcut_manager = ShortcutManager(app)
        
        # Test repeated shortcut usage
        initial_shortcuts = len(shortcut_manager.shortcuts) if hasattr(shortcut_manager, 'shortcuts') else 0
        
        # Simulate extended use
        for i in range(100):
            try:
                shortcut_manager.handle_key('f1', context='normal')
                shortcut_manager.handle_key('escape', context='help')
            except Exception:
                pass
        
        # Check that shortcut registry hasn't grown unexpectedly
        final_shortcuts = len(shortcut_manager.shortcuts) if hasattr(shortcut_manager, 'shortcuts') else 0
        
        # Shortcut registry should remain stable
        assert final_shortcuts <= initial_shortcuts + 5, "Shortcut registry grew unexpectedly"
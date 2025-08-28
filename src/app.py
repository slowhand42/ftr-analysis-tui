"""Main TUI application for Flow Analysis Editor."""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.binding import Binding
from pathlib import Path
import logging
import sys
from typing import Optional

from .widgets import ClusterView, SheetTabs, ColorGrid, StatusBar, LoadingScreen, LoadingManager
from .widgets.simple_cluster_view import SimpleClusterView
from .core import ExcelDataManager, DataValidator, ColorFormatter, SessionManager
from .io import ExcelIO, StateIO
from .models import SessionState


logger = logging.getLogger(__name__)


class AnalysisTUIApp(App):
    """
    Main TUI application for editing flow analysis Excel files.

    Handles application lifecycle, event routing, and widget coordination.
    """

    CSS = """
    SheetTabs {
        height: 3;
        dock: top;
        border: solid $primary;
    }

    ClusterView {
        height: 100%;
        border: solid $primary;
    }

    ColorGrid {
        height: 3;
        border: solid $primary;
        margin-top: 1;
    }

    LoadingScreen {
        height: 100%;
        align: center middle;
    }

    .loading-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }

    .loading-animation {
        text-align: center;
        color: $primary;
        margin-bottom: 1;
    }

    .loading-status {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    StatusBar {
        height: 3;
        dock: bottom;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding("n", "next_cluster", "Next Cluster"),
        Binding("p", "prev_cluster", "Previous Cluster"),
        Binding("tab", "next_sheet", "Next Sheet"),
        Binding("shift+tab", "prev_sheet", "Previous Sheet"),
        Binding("ctrl+g", "goto_cluster", "Go To Cluster"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+q", "quit", "Quit"),
        # Removed number key bindings to allow quick editing
        # Numbers 0-9 will be handled for cell editing instead
    ]

    def __init__(self, excel_file: str, **kwargs):
        """
        Initialize the application.

        Args:
            excel_file: Path to Excel file to edit
        """
        super().__init__(**kwargs)
        self.excel_file = excel_file

        # Initialize components
        self.excel_io = ExcelIO(Path(excel_file))
        self.state_io = StateIO()
        self.data_manager = ExcelDataManager(self.excel_io)
        self.validator = DataValidator()
        self.formatter = ColorFormatter()
        self.session_manager = SessionManager(self.state_io)

        # Initialize shortcut manager
        from .presentation.shortcut_manager import ShortcutManager
        self.shortcut_manager = ShortcutManager(self)

        # State
        self.current_session: Optional[SessionState] = None
        self.current_cluster_list: list = []
        self.current_cluster_index: int = 0
        self.loading_complete = False
        self.has_unsaved_changes = False

        # Widgets (will be initialized in compose)
        self.sheet_tabs: Optional[SheetTabs] = None
        self.cluster_view: Optional[ClusterView] = None
        self.date_grid: Optional[ColorGrid] = None
        self.lodf_grid: Optional[ColorGrid] = None
        self.status_bar: Optional[StatusBar] = None
        self.loading_screen: Optional[LoadingScreen] = None
        self.loading_manager: Optional[LoadingManager] = None
        
        # Number key handling is now done in SimpleClusterView.on_key()

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        # Note: SheetTabs will be initialized with proper sheets after data loads
        # For now, create with empty sheets list
        self.sheet_tabs = SheetTabs(sheets=[], on_sheet_change=self.on_sheet_change)
        # Use SimpleClusterView for now to test data display
        self.cluster_view = SimpleClusterView()
        self.date_grid = ColorGrid(grid_type="date", formatter=self.formatter)
        self.lodf_grid = ColorGrid(grid_type="lodf", formatter=self.formatter)
        self.status_bar = StatusBar()
        
        # Show loading screen initially
        self.loading_screen = LoadingScreen()
        self.loading_manager = LoadingManager(self.loading_screen)
        
        yield self.loading_screen

    def on_mount(self) -> None:
        """Initialize application on mount."""
        # Start loading process
        self.run_worker(self.load_and_switch())
    
    async def load_and_switch(self):
        """Simple loading and interface switch."""
        try:
            # Update loading screen
            if self.loading_manager:
                self.loading_manager.update_step("Loading Excel file...", 20)
            
            # Load data synchronously
            self.data_manager.load_excel(self.excel_file)
            
            if self.loading_manager:
                self.loading_manager.update_step("Initializing session...", 60)
            
            # Initialize session
            self.current_session = self.session_manager.get_or_create_state(
                self.excel_file,
                default_sheet="SEP25"
            )
            
            if self.loading_manager:
                self.loading_manager.update_step("Loading clusters...", 90)
            
            # Switch to main interface immediately
            await self.switch_to_main_interface()
            
            if self.loading_manager:
                self.loading_manager.complete()
                
        except Exception as e:
            logger.error(f"Error loading: {e}")
            import traceback
            traceback.print_exc()
    
    async def load_data_async(self):
        """Load data asynchronously with progress updates."""
        try:
            # Step 1: Load Excel file
            self.loading_manager.update_step("Loading Excel file...", 10)
            import asyncio
            await asyncio.sleep(0.1)  # Allow UI update
            
            self.data_manager.load_excel(self.excel_file)
            self.loading_manager.update_step("Excel file loaded", 40)
            await asyncio.sleep(0.1)
            
            # Step 2: Initialize session
            self.loading_manager.update_step("Initializing session...", 60)
            await asyncio.sleep(0.1)
            
            self.current_session = self.session_manager.get_or_create_state(
                self.excel_file,
                default_sheet="SEP25"
            )
            
            # Step 3: Load cluster data
            self.loading_manager.update_step("Loading cluster data...", 80)
            await asyncio.sleep(0.1)
            
            # Load cluster list for current sheet
            self.load_current_sheet()
            
            # Navigate to saved cluster
            if 0 <= self.current_session.current_cluster < len(self.current_cluster_list):
                self.current_cluster_index = self.current_session.current_cluster
            
            # Step 4: Complete loading
            self.loading_manager.update_step("Finalizing...", 95)
            await asyncio.sleep(0.1)
            
            # Mark as complete and switch to main interface
            self.loading_complete = True
            self.loading_manager.complete()
            await asyncio.sleep(0.5)  # Show completion briefly
            
            # Switch to main interface
            await self.switch_to_main_interface()
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to initialize application: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            # Show error on loading screen
            if self.loading_manager:
                self.loading_manager.loading_screen.update_progress(0, f"Error: {str(e)}")
            raise
    
    async def switch_to_main_interface(self):
        """Switch from loading screen to main interface."""
        try:
            # Remove loading screen
            if self.loading_screen:
                self.loading_screen.remove()
            
            # Get actual sheet names from the Excel file
            available_sheets = self.data_manager.get_sheet_names()
            
            # Update SheetTabs with actual sheets using the new method
            self.sheet_tabs.update_sheets(available_sheets)
            if available_sheets:
                # Set the first available sheet as active, or use saved session sheet if it exists
                if self.current_session and self.current_session.current_sheet in available_sheets:
                    self.sheet_tabs.set_active_sheet(self.current_session.current_sheet)
                else:
                    self.sheet_tabs.set_active_sheet(available_sheets[0])
            
            # Mount main interface widgets
            await self.mount(self.sheet_tabs)
            
            # Create and mount main container
            container = Container(
                self.cluster_view,
                self.date_grid,  
                self.lodf_grid,
                id="main-container"
            )
            await self.mount(container)
            await self.mount(self.status_bar)
                
            # Load cluster list for current sheet - use the actual active sheet
            sheet_name = self.sheet_tabs.active_sheet if self.sheet_tabs.active_sheet else available_sheets[0] if available_sheets else "SEP25"
            self.current_cluster_list = self.data_manager.get_clusters_list(sheet_name)
            self.current_cluster_index = 0
            
            # Debug: log cluster info
            logger.info(f"Loaded {len(self.current_cluster_list)} clusters for {sheet_name}")
            if self.current_cluster_list:
                logger.info(f"First few clusters: {self.current_cluster_list[:5]}")
            
            # Display first cluster if available
            if self.current_cluster_list:
                self.display_current_cluster()
                logger.info(f"Displaying cluster {self.current_cluster_index}")
            
            # Update status
            if self.status_bar:
                self.status_bar.update_status(
                    f"Loaded {Path(self.excel_file).name} - "
                    f"{len(self.data_manager.get_sheet_names())} sheets, "
                    f"{len(self.current_cluster_list)} clusters"
                )
            
        except Exception as e:
            logger.error(f"Error switching to main interface: {e}")
            import traceback
            traceback.print_exc()

    def load_current_sheet(self) -> None:
        """Load data for current sheet."""
        try:
            sheet = self.sheet_tabs.active_sheet
            self.current_cluster_list = self.data_manager.get_clusters_list(sheet)
            self.current_cluster_index = 0
        except KeyError as e:
            logger.error(f"Failed to load sheet {sheet}: {e}")
            self.current_cluster_list = []
            self.current_cluster_index = 0
            if self.status_bar:
                self.status_bar.update_status(f"Sheet {sheet} not available")

    def display_current_cluster(self) -> None:
        """Display the current cluster data."""
        if not self.current_cluster_list:
            return

        cluster_id = self.current_cluster_list[self.current_cluster_index]
        sheet = self.sheet_tabs.active_sheet

        try:
            # Get cluster data
            cluster_data = self.data_manager.get_cluster_data(sheet, cluster_id)

            # Update cluster view with SimpleClusterView
            if hasattr(self.cluster_view, 'load_data'):
                # Using SimpleClusterView
                self.cluster_view.load_data(cluster_data)
            else:
                # Using original ClusterView
                cluster_name = f"CLUSTER_{cluster_id:03d}"
                self.cluster_view.load_cluster(cluster_name, sheet)

            # Update grids (placeholder - need date/LODF extraction logic)
            # self.date_grid.render_grid(date_values, date_comments)
            # self.lodf_grid.render_grid(lodf_values, lodf_comments)

            # Update status bar with proper cluster information
            if self.status_bar:
                self.status_bar.current_sheet = sheet
                self.status_bar.current_cluster = self.current_cluster_index + 1
                self.status_bar.total_clusters = len(self.current_cluster_list)
                self.status_bar.current_row = 1
                self.status_bar.total_rows = len(cluster_data) if cluster_data is not None else 0

            # Update status
            self.data_manager.get_cluster_info(sheet, cluster_id)
            self.title = (f"Cluster {cluster_id} "
                          f"({self.current_cluster_index + 1}/{len(self.current_cluster_list)})")

            # Save state (use cluster index, not ID)
            self.session_manager.update_current_state(
                current_sheet=sheet,
                current_cluster=self.current_cluster_index
            )
        except Exception as e:
            import traceback
            logger.error(f"Failed to display cluster {cluster_id}: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            # Re-raise to let it bubble up
            raise

    def on_sheet_change(self, sheet: str) -> None:
        """Handle sheet change event."""
        try:
            # Check if sheet exists in data
            available_sheets = self.data_manager.get_sheet_names()
            if sheet not in available_sheets:
                logger.warning(f"Sheet {sheet} not found in data")
                # Revert to first available sheet
                if available_sheets:
                    sheet = available_sheets[0]
                    if self.sheet_tabs:
                        self.sheet_tabs.set_active_sheet(sheet)
                return
            
            # Update the sheet tabs to reflect the new sheet
            if self.sheet_tabs:
                self.sheet_tabs.active_sheet = sheet
            self.load_current_sheet()
            self.display_current_cluster()
        except Exception as e:
            logger.error(f"Error changing sheet: {e}")
            if self.status_bar:
                self.status_bar.update_status(f"Error loading sheet {sheet}")

    def on_cell_edit(self, row: int, column: str, value: float) -> None:
        """
        Handle cell edit event - save to data manager and trigger auto-save.

        Args:
            row: Row index in DataFrame
            column: Column name
            value: New value
        """
        try:
            sheet = self.sheet_tabs.active_sheet
            cluster_id = self.current_cluster_list[self.current_cluster_index]
            
            # Update data in memory (method may vary based on data manager implementation)
            # For now, we'll update the cluster data directly
            cluster_data = self.data_manager.get_cluster_data(sheet, cluster_id)
            if cluster_data is not None and row < len(cluster_data):
                cluster_data.at[row, column] = value
                
                # Auto-save disabled for performance - use Ctrl+S to save manually
                # Mark that we have unsaved changes
                self.has_unsaved_changes = True
                self.status_bar.update_status("Modified (unsaved) - Press Ctrl+S to save")
            
        except Exception as e:
            logger.error(f"Error saving cell edit: {e}")
            self.notify(f"Error saving: {e}", severity="error")

    def action_next_cluster(self) -> None:
        """Navigate to next cluster (with bounds checking)."""
        if not self.current_cluster_list:
            return

        # Bounds checking: don't go past the last cluster
        if self.current_cluster_index < len(self.current_cluster_list) - 1:
            self.current_cluster_index += 1
            self.display_current_cluster()

    def action_prev_cluster(self) -> None:
        """Navigate to previous cluster (with bounds checking)."""
        if not self.current_cluster_list:
            return

        # Bounds checking: don't go before the first cluster
        if self.current_cluster_index > 0:
            self.current_cluster_index -= 1
            self.display_current_cluster()

    def navigate_cluster_with_wrap(self, direction: int) -> None:
        """Navigate cluster with wrap-around support (used by tests)."""
        if not self.current_cluster_list:
            return

        if direction > 0:  # Forward
            if self.current_cluster_index >= len(self.current_cluster_list) - 1:
                self.current_cluster_index = 0  # Wrap to first
            else:
                self.current_cluster_index += 1
        else:  # Backward
            if self.current_cluster_index <= 0:
                self.current_cluster_index = len(self.current_cluster_list) - 1  # Wrap to last
            else:
                self.current_cluster_index -= 1

        self.display_current_cluster()

    def action_next_sheet(self) -> None:
        """Navigate to next sheet."""
        self.sheet_tabs.next_sheet()

    def action_prev_sheet(self) -> None:
        """Navigate to previous sheet."""
        self.sheet_tabs.previous_sheet()

    def action_goto_cluster(self) -> None:
        """Go to specific cluster by ID."""
        # This would show an input dialog in full implementation
        pass

    def action_save(self) -> None:
        """Manual save."""
        try:
            new_path = self.data_manager.save_changes()
            self.has_unsaved_changes = False
            self.status_bar.update_status(f"Saved to {Path(new_path).name}")
        except Exception as e:
            self.status_bar.update_status(f"Save failed: {e}")

    def action_quit(self) -> None:
        """Quit application."""
        # Save session state before exiting
        if self.session_manager and self.sheet_tabs and self.current_cluster_list:
            current_cluster = None
            if 0 <= self.current_cluster_index < len(self.current_cluster_list):
                current_cluster = self.current_cluster_list[self.current_cluster_index]

            self.session_manager.update_current_state(
                current_sheet=self.sheet_tabs.active_sheet,
                current_cluster=current_cluster
            )
        self.exit()

    # Sheet number shortcuts removed to allow number keys for cell editing
    # Number key handling is now done in SimpleClusterView.on_key()


def main():
    """Main entry point."""
    # Default to small file if no argument provided
    default_file = "./analysis_files/flow_results_processed_SEP25_R1_small.xlsx"
    
    if len(sys.argv) < 2:
        excel_file = default_file
        print(f"No file specified, using default: {excel_file}")
    else:
        excel_file = sys.argv[1]

    if not Path(excel_file).exists():
        print(f"Error: File not found: {excel_file}")
        if excel_file != default_file and Path(default_file).exists():
            print(f"Falling back to default file: {default_file}")
            excel_file = default_file
        else:
            sys.exit(1)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='analysis-tui.log'
    )

    # Run application
    app = AnalysisTUIApp(excel_file)
    app.run()


if __name__ == "__main__":
    main()

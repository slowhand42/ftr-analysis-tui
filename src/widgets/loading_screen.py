"""Loading screen widget for displaying progress during data loading."""

from textual.widgets import Static, ProgressBar
from textual.containers import Vertical, Center
from textual import work
from textual.reactive import reactive
import time
from typing import Optional


class LoadingScreen(Vertical):
    """
    Loading screen widget that displays progress and status messages.
    
    Shows animated loading text, progress bar, and current operation status.
    """
    
    # Reactive properties
    current_operation = reactive("Initializing...")
    progress = reactive(0.0)
    is_complete = reactive(False)
    
    def __init__(self, **kwargs):
        """Initialize the loading screen."""
        super().__init__(**kwargs)
        self.title_widget: Optional[Static] = None
        self.status_widget: Optional[Static] = None
        self.progress_widget: Optional[ProgressBar] = None
        self._animation_task = None
        
    def compose(self):
        """Create the loading screen layout."""
        with Center():
            yield Static("🔄 Flow Analysis TUI", id="loading-title", classes="loading-title")
        
        with Center():
            yield Static("", id="loading-animation", classes="loading-animation")
            
        with Center():
            yield ProgressBar(total=100, show_eta=False, id="loading-progress")
            
        with Center():
            yield Static("Initializing...", id="loading-status", classes="loading-status")
    
    def on_mount(self) -> None:
        """Start the loading animation when mounted."""
        self.title_widget = self.query_one("#loading-title", Static)
        self.status_widget = self.query_one("#loading-status", Static)
        self.progress_widget = self.query_one("#loading-progress", ProgressBar)
        
        # Start animation
        self._animation_task = self.animate_loading_dots()
    
    @work
    async def animate_loading_dots(self):
        """Animate loading dots with electricity theme."""
        # Electricity-themed spinner: lightning bolts, power symbols, electrical components
        animation_chars = ["⚡", "🔌", "⚡", "🔋", "⚡", "💡", "⚡", "🔆", "⚡", "⚡"]
        char_index = 0
        
        while not self.is_complete:
            if hasattr(self, 'query_one'):
                try:
                    animation_widget = self.query_one("#loading-animation", Static)
                    animation_widget.update(animation_chars[char_index])
                    char_index = (char_index + 1) % len(animation_chars)
                except:
                    pass
            import asyncio
            await asyncio.sleep(0.1)
    
    def update_progress(self, progress: float, operation: str = None):
        """
        Update the loading progress.
        
        Args:
            progress: Progress value between 0 and 100
            operation: Current operation description
        """
        self.progress = min(100, max(0, progress))
        
        if operation:
            self.current_operation = operation
        
        # Update widgets
        if self.progress_widget:
            self.progress_widget.progress = self.progress
            
        if self.status_widget:
            self.status_widget.update(self.current_operation)
    
    def complete_loading(self):
        """Mark loading as complete and stop animations."""
        self.is_complete = True
        self.progress = 100
        
        if self.progress_widget:
            self.progress_widget.progress = 100
            
        if self.status_widget:
            self.status_widget.update("✓ Loading complete!")
            
        # Stop animation
        if hasattr(self, 'query_one'):
            try:
                animation_widget = self.query_one("#loading-animation", Static)
                animation_widget.update("✓")
            except:
                pass


class LoadingManager:
    """
    Helper class to manage loading screen updates during app initialization.
    """
    
    def __init__(self, loading_screen: LoadingScreen):
        self.loading_screen = loading_screen
        self.start_time = time.time()
    
    def update_step(self, step: str, progress: float):
        """
        Update loading progress with a specific step.
        
        Args:
            step: Description of current step
            progress: Progress percentage (0-100)
        """
        elapsed = time.time() - self.start_time
        status = f"{step} ({elapsed:.1f}s)"
        self.loading_screen.update_progress(progress, status)
    
    def complete(self):
        """Mark loading as complete."""
        elapsed = time.time() - self.start_time
        final_status = f"Ready! Loaded in {elapsed:.1f}s"
        self.loading_screen.update_progress(100, final_status)
        self.loading_screen.complete_loading()
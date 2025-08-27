# Flow Analysis TUI Editor

A terminal-based application for viewing and editing power flow constraint analysis Excel files.

## Features

- **Fast Navigation**: Keyboard-driven interface for rapid data entry
- **Conditional Formatting**: Preserves Excel's color-coded visual feedback
- **Cluster-focused Workflow**: View and edit constraints cluster by cluster
- **Auto-save**: Automatically saves changes to timestamped files
- **Session Persistence**: Remembers your position between runs

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run directly
python analysis_tui.py analysis_files/flow_results_processed_SEP25_R1.xlsx

# Or after installation
pip install -e .
analysis-tui analysis_files/flow_results_processed_SEP25_R1.xlsx
```

## Keyboard Shortcuts

### Navigation
- `n` / `p` - Next/Previous cluster
- `Tab` / `Shift+Tab` - Next/Previous sheet
- `↑` / `↓` - Navigate rows
- `1-9` - Jump to sheet by number
- `Ctrl+G` - Go to cluster by ID

### Editing
- `0-9` - Start editing VIEW value
- `Enter` - Save edit and move down
- `Tab` - Save and move to SHORTLIMIT column
- `Esc` - Cancel edit

### File Operations
- `Ctrl+S` - Manual save
- `Ctrl+Q` - Quit

## Architecture

The application follows a clean MVC architecture with clear separation of concerns:

- **Presentation Layer**: Textual widgets for UI
- **Business Logic Layer**: Data management, validation, and formatting
- **Data Access Layer**: Excel and state file I/O

See `project-architecture.md` for detailed architecture documentation.

## Development

```bash
# Run tests
pytest

# Type checking
mypy src

# Linting
ruff check src
```

## License

Proprietary - FTR Analysis Team
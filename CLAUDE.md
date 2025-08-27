# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flow Analysis TUI Editor - A terminal-based Excel editor specifically designed for power flow constraint analysis files. Built with Textual framework following MVC architecture with clear separation between presentation, business logic, and data access layers.

## Environment Setup

Always use the local virtual environment:
```bash
source venv/bin/activate  # Activate before any Python operations
```

Default file loading configured to use `./analysis_files/flow_results_processed_SEP25_R1_small.xlsx` when no file specified.

## Key Commands

### Development
```bash
# Run the application (uses default small file if no argument)
python analysis_tui.py [excel_file]

# Testing
pytest                    # Run all tests
pytest tests/test_*.py    # Run specific test files

# Code Quality
mypy src                  # Type checking
ruff check src           # Linting
ruff format src          # Code formatting

# Web TUI (for development/debugging)
# Run in web interface for easier debugging of TUI components
```

### Application Shortcuts (when running)
- `n`/`p` - Navigate clusters
- `Tab`/`Shift+Tab` - Switch sheets  
- `0-9` - Edit cell values (VIEW/SHORTLIMIT columns only)
- `Enter` - Save edit and move down
- `Ctrl+S` - Manual save
- `Ctrl+Q` - Quit

## Architecture Overview

**3-Layer MVC Architecture:**

1. **Presentation Layer** (`src/widgets/`, `src/app.py`)
   - `AnalysisTUIApp` - Main application controller
   - `ClusterView` - DataTable for constraint data display/editing
   - `SheetTabs` - Monthly sheet navigation
   - `StatusBar` - Current status display
   - `LoadingScreen` - Startup loading interface

2. **Business Logic Layer** (`src/core/`, `src/business_logic/`)
   - `ExcelDataManager` - Central data management and CRUD operations
   - `DataValidator` - Input validation (VIEW >0, SHORTLIMIT <0)
   - `ColorFormatter` - Excel conditional formatting replication
   - `SessionManager` - State persistence between runs

3. **Data Access Layer** (`src/io/`, `src/models/`)
   - `ExcelIO` - Excel file operations with pandas/openpyxl
   - `StateIO` - JSON session state persistence
   - Data models for type safety

## Critical Implementation Details

### Data Flow
- Excel files loaded once into memory as pandas DataFrames
- All edits performed in-memory with auto-save to timestamped files
- Session state persists current position (sheet, cluster, row)

### Textual Widget Patterns
- `ClusterView` extends `DataTable` with custom size property handling
- Widget lifecycle: `compose()` → `mount()` → `load_cluster()`
- Exception handling in widget methods to prevent TUI crashes

### Testing Strategy
- Unit tests for all business logic (90%+ coverage target)
- Integration tests with fixture Excel files
- Mock objects for Textual widgets in test environments
- Web TUI interface available for manual testing

## File Structure Key Points

```
src/
├── app.py                  # Main TUI application
├── widgets/                # All TUI widgets
│   ├── cluster_view.py     # Primary data display/editing widget
│   └── loading_screen.py   # Startup loading interface
├── core/                   # Core business logic
│   └── data_manager.py     # Central data operations
├── business_logic/         # Domain-specific logic  
│   └── excel_data_manager.py # Excel-specific operations
└── io/                     # File I/O operations
```

## Common Development Tasks

### Adding New Validation Rules
1. Extend `DataValidator` in `src/business_logic/validators.py`
2. Update `ExcelDataManager.can_edit_column()` method
3. Add corresponding tests in `tests/business_logic/`

### Modifying Widget Behavior
1. Widget implementations in `src/widgets/`
2. Follow Textual widget lifecycle patterns
3. Handle exceptions gracefully to prevent TUI crashes
4. Test with both unit tests and web TUI interface

### Data Loading/Saving Changes
1. Core logic in `ExcelDataManager` and `ExcelIO` classes
2. Always create backups before modifications
3. Use timestamped saves to prevent overwrites
4. Test with fixture files in `tests/` directory

## Debugging

- Application logs to `analysis-tui.log`
- Web TUI interface available for visual debugging
- Use `logger.error()` for debugging widget issues
- Exception handling in widget methods logs errors but continues execution

## Important Constraints

- Only VIEW and SHORTLIMIT columns are editable
- VIEW values must be positive numbers (>0)
- SHORTLIMIT values must be negative numbers (<0) or empty
- All file operations create timestamped backups
- Session state automatically persists between runs
- when I ask you to test something, I mean run and test it in the web-tui, then examine result (read or screenshot)
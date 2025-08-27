# Product Requirements Document: Flow Analysis TUI Editor

## Executive Summary

The Flow Analysis TUI Editor is a terminal-based application designed to replace Excel for viewing and editing power flow constraint analysis files. It provides a focused, keyboard-driven interface for rapid data entry while preserving the visual feedback of Excel's conditional formatting. The tool is specifically optimized for editing VIEW and SHORTLIMIT values across multiple constraint scenarios.

## Project Overview

### Purpose
Replace Excel as the primary editor for `flow_results_processed_*.xlsx` files, providing:
- Faster, keyboard-driven data entry
- Preserved conditional formatting for visual analysis
- Focused constraint-by-constraint workflow
- Automatic saving and session persistence

### Target Users
- Power system analysts editing constraint values
- FTR (Financial Transmission Rights) traders analyzing flow patterns
- Grid operators reviewing constraint violations

## Version 0 (MVP) Scope

### Core Features

#### 1. Data Loading & Management
- **Full Excel Loading**: Load entire Excel file into memory at startup
- **Sheet Support**: Load all period sheets (SEP25, OCT25, NOV25, DEC25, JAN26, FEB26, MAR26, APR26, MAY26)
- **Exclude**: HIST, Summary, and violation sheets (future versions)
- **Working Copy**: Create immediate working copy on load for safety

#### 2. Display & Navigation

##### Cluster View
- Display one cluster at a time (all VIEW rows for that cluster)
- Show cluster ID prominently at top
- Navigate between clusters with:
  - `n`/`p` - Next/Previous cluster
  - `Ctrl+G` - Go to cluster by ID
  - Remember last position per sheet

##### Column Display (v0)
Show these columns for each constraint row:
- **CLUSTER** - Cluster identifier
- **CUID** - Constraint unique identifier (primary key!)
- **VIEW** - Primary editable value (🎨 color formatted)
- **PREV** - Previous auction's VIEW value (🎨 color formatted)
- **PACTUAL** - Predictor model with forecasted variables (🎨 color formatted)
- **PEXPECTED** - Predictor model with typical realization variables (🎨 color formatted)
- **VIEWLG** - Logarithmic view value (🎨 color formatted)
- **SHORTLIMIT** - Secondary editable value
- **MON** - Monitor/element name
- **CONT** - Contingency description  
- **DIRECTION** - Flow direction (-1/1)
- **SOURCE** - Source node (monthly sheets only)
- **SINK** - Sink node (monthly sheets only)
- **FLOW** - Current flow value (with bold for high values)
- **LIMIT** - MW limit
- **LAST_BINDING** - Last binding date
- **BHOURS** - Binding hours
- **MAXHIST** - Maximum historical value
- **EXP_PEAK** - Existing exposure peak
- **EXP_OP** - Existing exposure operating
- **RECENT_DELTA** - Recent forecast vs. realized (🎨 color formatted: blue-white-red)
- **Date Grid** - Compressed color grid with outage comment indicators
- **LODF Grid** - Compressed color grid
- **Comment Display** - Shows transmission outage info below grids (when selected)

*Exclude: All CSP* columns, all SCN* columns*
*🎨 = Has conditional formatting from Excel*

##### Sheet Tabs
- Tab bar at top showing: SEP25 | OCT25 | NOV25 | DEC25 | JAN26 | FEB26 | MAR26 | APR26 | MAY26
- Current tab highlighted
- Navigate with:
  - `Tab`/`Shift+Tab` - Next/Previous sheet
  - Number keys `1-9` - Jump to sheet

#### 3. Data Entry

##### Quick Number Entry Mode
- **Activation**: Press any number key to start editing VIEW column of current row
- **Flow**:
  1. Type number (can include decimal point)
  2. Press `Enter` or `↓` - Save and move to next row's VIEW
  3. Press `Tab` - Save and move to SHORTLIMIT column
  4. Press `Esc` - Cancel edit

##### Validation Rules
- **VIEW**: Must be positive real number (>0)
  - Invalid input: Red flash + beep
  - Valid: Update cell with new value
- **SHORTLIMIT**: Must be negative number (<0) or empty
  - Invalid input: Red flash + beep
  - Valid: Update cell with new value

##### Navigation in Edit Mode
- `↑`/`↓` - Move between rows (saves current edit)
- `Tab` - Toggle between VIEW and SHORTLIMIT
- `Enter` - Save and move down
- `Esc` - Cancel current edit

#### 4. Conditional Formatting

##### Exact Color Thresholds (from Excel)

**Core Columns (VIEW, PREV, PACTUAL, PEXPECTED, VIEWLG)**
| Value Range | Background Color | RGB |
|------------|------------------|-----|
| ≤ 0.5 | White | #FFFFFF |
| 0.5 to 4th percentile | White→Yellow gradient | #FFFFFF→#FFFF00 |
| 4th percentile to 20 | Yellow→Red gradient | #FFFF00→#FF0000 |
| > 20 | Red | #FF0000 |

**RECENT_DELTA Column**
| Value | Background Color | RGB |
|-------|------------------|-----|
| -50 | Blue | #0000FF |
| 0 | White | #FFFFFF |
| +50 | Red | #FF0000 |
| (Gradient between these points)

**Date/LODF Grid Cells**
- Displayed as colored blocks without text
- Colors based on value ranges (0-100 for dates, -1 to 1 for LODF)
- Selected cell shows actual date/value in status bar
- **Cells with comments marked with dot/asterisk** (•) or (*) overlay
- **Comments contain transmission outage info** (e.g., "NEWTON 3 TR1 XFORMER(0.4) 08/28/25 - 08/28/25")

**Special Formatting**
- **High FLOW**: Bold text when FLOW > historical maximum
- **Error cells**: Grey background for calculation errors

#### 5. File Operations

##### Auto-Save
- Trigger: After each successful edit (if fast enough <100ms)
- Formats:
  1. `.xlsx` - Excel format (exact copy structure)
  2. `.pkl` - Pickle format for fast loading
- Location: Same directory as source file
- Naming: `{original_name}_edited_{timestamp}.xlsx`

##### Session State
- Save: Current cluster, sheet, and row position
- File: `.analysis-tui-state.json` in same directory as Excel
- Auto-load on startup

#### 6. User Interface Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ SEP25 │ OCT25 │ NOV25 │ DEC25 │ JAN26 │ FEB26 │ MAR26 │ APR26 │ MAY26
├──────────────────────────────────────────────────────────────────┤
│ Cluster 42 (7 constraints)                     [< Prev] [Next >]  │
├──────────────────────────────────────────────────────────────────┤
│ VIEW    SHORTLIMIT  MON              CONT           FLOW   LIMIT  │
│ 15.23   -          NEWTON TR2       Jordan 345kV   234.5  480.0  │
│ 8.45    -2.5       NEWTON TR1       Casey 345kV    156.2  480.0  │
│ 22.10   -          ARLAND-KANSAS    Holland 345kV  445.3  500.0  │
│ ...                                                               │
├──────────────────────────────────────────────────────────────────┤
│ Date Grid: ████░░██*░░████░░░░████*███░░░░░░████                │
│ LODF Grid: ░░░░████░░░░░░██████░░░░░░░░████░░░░                 │
│ Comments: NEWTON 3 TR1 XFORMER(0.4) 08/28/25 - 08/28/25         │
├──────────────────────────────────────────────────────────────────┤
│ [n]ext [p]rev | [Tab] Switch Sheet | [↑↓] Navigate | [Esc] Menu  │
└──────────────────────────────────────────────────────────────────┘
```

### Technical Architecture

> **Design Principle**: Keep it simple! This is a single-user app. Build v0 quickly with minimal abstraction, but organize code sensibly for future additions.

#### Technology Stack
- **Framework**: Textual (TUI framework)
- **Styling**: Rich (color formatting)
- **Data**: Pandas + openpyxl (Excel I/O)
- **Config**: JSON (state persistence)

#### Simple File Structure
```
analysis-tui/
├── analysis_tui.py          # Main application (all v0 code here)
├── PRD.md                   # This document
├── requirements.txt         # Python dependencies
├── .analysis-tui-state.json # Session state (auto-generated)
├── .mcp.json               # MCP configuration
└── analysis_files/         # Excel files directory
    └── flow_results_processed_SEP25_R1.xlsx

# Future (when needed):
├── widgets.py              # Extract widgets when file gets too big
├── formatting.py           # Color logic when it gets complex
└── graphs.py              # When we add plotext graphs
```

#### Main Classes (v0 - all in one file)

```python
class AnalysisTUIApp(App):
    """Main app - handles everything"""
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.data = {}  # Simple dict of DataFrames
        self.current_cluster = 0
        self.current_sheet = "SEP25"
        self.edits = []  # Simple list for undo/redo
    
    def load_excel(self):
        """Just load all sheets with pandas"""
        for sheet in ["SEP25", "OCT25", ...]:
            self.data[sheet] = pd.read_excel(self.excel_file, sheet)
    
    def save_excel(self):
        """Save to new file with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file = f"{self.excel_file.stem}_edited_{timestamp}.xlsx"
        with pd.ExcelWriter(new_file) as writer:
            for sheet, df in self.data.items():
                df.to_excel(writer, sheet)

class ClusterTable(DataTable):
    """Shows one cluster's constraints"""
    def __init__(self, cluster_data: pd.DataFrame):
        self.cluster_data = cluster_data
        self.setup_columns()
        self.apply_colors()
    
    def on_key(self, event):
        """Handle number keys for quick entry"""
        if event.key in "0123456789":
            self.start_editing(event.key)

class ColorGrid(Static):
    """Shows date/LODF values as colored blocks with comment indicators"""
    def __init__(self, values: list, comments: dict):
        self.values = values
        self.comments = comments  # {col_idx: comment_text}
        self.render_colored_grid()
    
    def on_hover(self, col_idx: int):
        """Show comment in status area when hovering"""
        if col_idx in self.comments:
            self.show_comment(self.comments[col_idx])

# Helper functions (not classes)
def get_color_for_value(value: float, column: str) -> str:
    """Simple if/elif chain for color thresholds"""
    if column in ["VIEW", "PREV", "PACTUAL", "PEXPECTED"]:
        if value <= 0.5:
            return "white"
        elif value <= 20:
            return "yellow"
        else:
            return "red"
    # ... etc

def validate_input(value: str, column: str) -> bool:
    """Simple validation"""
    if column == "VIEW":
        return float(value) > 0
    elif column == "SHORTLIMIT":
        return float(value) < 0 or value == ""
    return True
```

#### Data Storage (KISS)
```python
# v0: Just use pandas DataFrames directly
self.data = {
    "SEP25": pd.DataFrame(...),
    "OCT25": pd.DataFrame(...),
    # ...
}

# State file: simple JSON
{
    "last_file": "flow_results_processed_SEP25_R1.xlsx",
    "current_sheet": "SEP25",
    "current_cluster": 42,
    "window_size": [120, 40]
}

# Edits tracking: simple list
self.edit_history = [
    {"sheet": "SEP25", "row": 10, "col": "VIEW", "old": 15.0, "new": 20.0},
    # ...
]
```

### Performance Requirements

- **Load Time**: < 5 seconds for 50MB Excel file
- **Edit Response**: < 50ms for value update
- **Save Time**: < 100ms for auto-save
- **Memory**: < 500MB for typical file

### Keyboard Shortcuts (v0)

| Key | Action |
|-----|--------|
| `0-9` | Start editing VIEW value |
| `↑`/`↓` | Navigate rows |
| `Tab` | Switch VIEW↔SHORTLIMIT or Next sheet |
| `Enter` | Save edit and move down |
| `Esc` | Cancel edit / Menu |
| `n`/`p` | Next/Previous cluster |
| `Ctrl+S` | Manual save |
| `Ctrl+Q` | Quit |
| `Ctrl+G` | Go to cluster |

## Future Versions Roadmap

### Version 1 - Enhanced Navigation & Search
- **Search**: Wildcard search across MON, CONT columns
- **Filter**: Show only constraints above threshold
- **Vertical Mode**: Show all periods for one constraint
- **Batch Edit**: Edit multiple constraints at once
- **URL3 Integration**: Open YesEnergy topology in browser

### Version 2 - Visualization & Analysis  
- **Graphs**: Time series plots with plotext
- **Statistics**: Cluster-level statistics panel
- **HIST Integration**: Show historical comparisons
- **Summary View**: Aggregate statistics from Summary sheet
- **Violation Panel**: Show violations in separate pane

### Version 3 - Advanced Features
- **Image Loading**: Load constraint-specific PNG plots
- **LLM Queries**: Natural language constraint search
- **Export**: Generate reports and filtered exports
- **Collaboration**: Multi-user editing via MCP
- **Audit Trail**: Track all edits with timestamps

## Implementation Guidelines

### Phase 1: Core Framework (Week 1)
1. Set up project structure
2. Implement Excel loading with openpyxl
3. Create basic Textual app with sheet tabs
4. Parse and structure constraint data

### Phase 2: Display & Navigation (Week 1-2)
1. Implement ClusterView widget
2. Add conditional formatting color mapping
3. Create date/LODF grid displays
4. Add cluster navigation

### Phase 3: Editing (Week 2)
1. Implement quick number entry mode
2. Add validation rules
3. Create auto-save functionality
4. Add session state persistence

### Phase 4: Polish & Testing (Week 3)
1. Optimize performance
2. Add error handling
3. Create test suite
4. Documentation

## Success Criteria

### v0 Must Have
- ✅ Load Excel file and display period sheets
- ✅ Show one cluster at a time with all constraints
- ✅ Edit VIEW and SHORTLIMIT with validation
- ✅ Preserve Excel's conditional formatting
- ✅ Auto-save edits
- ✅ Remember position between sessions

### v0 Nice to Have
- Undo/redo functionality
- Export to CSV
- Basic statistics display

## Dependencies

### Python Packages
```
textual>=0.47.0
rich>=13.7.0
pandas>=2.0.0
openpyxl>=3.1.0
plotext>=5.2.0  # For future
```

### System Requirements
- Python 3.8+
- Terminal with 256 color support
- 120+ character width recommended
- Linux/Mac/Windows (with Windows Terminal)

## Testing Strategy

### Unit Tests
- Value validation logic
- Color threshold calculations
- Data structure transformations

### Integration Tests
- Excel file loading/saving
- Navigation between sheets/clusters
- Edit and save workflow

### Manual Testing
- Large file performance (>100MB)
- Rapid data entry workflow
- Color accuracy verification

## Documentation Requirements

1. **README.md** - Installation and basic usage
2. **User Guide** - Detailed keyboard shortcuts and workflows
3. **Developer Guide** - Architecture and extension points
4. **API Documentation** - For future MCP integration

## Acceptance Criteria

The v0 release is complete when:
1. User can load the sample Excel file
2. User can navigate between sheets and clusters
3. User can edit VIEW values with number key shortcuts
4. User can optionally edit SHORTLIMIT values
5. Conditional formatting matches Excel exactly
6. Edits auto-save to new file
7. Session state persists between runs
8. No crashes during normal operation

---

*Document Version: 1.0*
*Last Updated: August 2025*
*Author: FTR Analysis Team*
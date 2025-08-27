"""Data model definitions for type safety and structure."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum


class ColumnType(Enum):
    """Column types for formatting and validation."""
    VIEW = "VIEW"
    SHORTLIMIT = "SHORTLIMIT"
    SP = "SP"
    PREV = "PREV"
    PACTUAL = "PACTUAL"
    PEXPECTED = "PEXPECTED"
    VIEWLG = "VIEWLG"
    CSP95 = "CSP95"
    CSP80 = "CSP80"
    CSP50 = "CSP50"
    CSP20 = "CSP20"
    CSP5 = "CSP5"
    RECENT_DELTA = "RECENT_DELTA"
    DATE_COLUMN = "DATE_COLUMN"
    LODF_COLUMN = "LODF_COLUMN"
    FLOW = "FLOW"
    OTHER = "OTHER"


@dataclass
class SessionState:
    """Persistent session state between application runs."""
    last_file: str
    current_sheet: str
    current_cluster: int
    current_row: int = 0
    window_size: Tuple[int, int] = (120, 40)
    last_modified: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'last_file': self.last_file,
            'current_sheet': self.current_sheet,
            'current_cluster': self.current_cluster,
            'current_row': self.current_row,
            'window_size': list(self.window_size),
            'last_modified': self.last_modified.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Create from dictionary."""
        return cls(
            last_file=data['last_file'],
            current_sheet=data['current_sheet'],
            current_cluster=data['current_cluster'],
            current_row=data.get('current_row', 0),
            window_size=tuple(data.get('window_size', [120, 40])),
            last_modified=datetime.fromisoformat(data.get('last_modified', datetime.now().isoformat()))
        )


@dataclass
class EditRecord:
    """Record of a single edit for undo/redo functionality."""
    sheet: str
    cluster_id: str  # Can be string identifier like "CLUSTER_001"
    constraint_index: int  # Row index within the cluster
    column: str
    old_value: Optional[float]
    new_value: float
    timestamp: datetime
    cuid: Optional[str] = None
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return (f"Edit at {self.timestamp.strftime('%H:%M:%S')}: "
                f"{self.sheet}[{self.constraint_index},{self.column}] "
                f"{self.old_value} -> {self.new_value}")


@dataclass
class ClusterInfo:
    """Information about a constraint cluster."""
    cluster_id: int
    constraint_count: int
    cuid_list: List[str]
    has_sp_value: bool = False
    monitor: Optional[str] = None
    contingency: Optional[str] = None
    
    def __str__(self) -> str:
        """Human-readable cluster description."""
        return f"Cluster {self.cluster_id} ({self.constraint_count} constraints)"


@dataclass
class ColorThreshold:
    """Color threshold definition for conditional formatting."""
    min_value: float
    max_value: float
    min_color: str  # RGB hex or color name
    max_color: str  # RGB hex or color name
    
    def get_color_at_value(self, value: float) -> str:
        """Calculate interpolated color for a given value."""
        # This is a placeholder - actual implementation will interpolate colors
        if value <= self.min_value:
            return self.min_color
        elif value >= self.max_value:
            return self.max_color
        else:
            # Linear interpolation would go here
            return self.min_color


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_value: Optional[Any] = None


@dataclass
class ExcelMetadata:
    """Metadata about the loaded Excel file."""
    file_path: str
    file_size_mb: float
    sheet_names: List[str]
    total_rows: int
    total_clusters: int
    load_time_seconds: float
    last_modified: datetime
    
    def __str__(self) -> str:
        """Summary string."""
        return (f"Excel file: {self.file_path} "
                f"({self.file_size_mb:.1f}MB, "
                f"{len(self.sheet_names)} sheets, "
                f"{self.total_clusters} clusters)")


@dataclass
class GridComment:
    """Comment associated with a date/LODF grid cell."""
    column_index: int
    comment_text: str
    is_outage: bool = False
    date_range: Optional[Tuple[datetime, datetime]] = None


@dataclass
class ConstraintRow:
    """Data model for a single constraint row with validation and DataFrame integration."""
    
    # Required fields
    cluster: int
    cuid: str
    view: float
    
    # Optional fields with defaults
    shortlimit: Optional[float] = None
    prev: float = 0.0
    pactual: float = 0.0
    pexpected: float = 0.0
    viewlg: float = 0.0
    mon: str = ""
    cont: str = ""
    direction: int = 1
    source: Optional[str] = None
    sink: Optional[str] = None
    flow: float = 0.0
    limit: float = 0.0
    last_binding: Optional[str] = None
    bhours: float = 0.0
    maxhist: float = 0.0
    exp_peak: float = 0.0
    exp_op: float = 0.0
    recent_delta: float = 0.0
    date_grid_values: List[float] = field(default_factory=list)
    date_grid_comments: Dict[int, str] = field(default_factory=dict)
    lodf_grid_values: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate fields after initialization."""
        # VIEW must be positive
        if self.view <= 0:
            raise ValueError("VIEW must be positive")
        
        # SHORTLIMIT must be negative or None
        if self.shortlimit is not None and self.shortlimit >= 0:
            raise ValueError("SHORTLIMIT must be negative")
        
        # DIRECTION must be -1 or 1
        if self.direction not in (-1, 1):
            raise ValueError("DIRECTION must be -1 or 1")
    
    @classmethod
    def from_dataframe_row(cls, row_data: Dict[str, any]) -> 'ConstraintRow':
        """Create ConstraintRow from DataFrame row data."""
        return cls(
            cluster=row_data['CLUSTER'],
            cuid=row_data['CUID'],
            view=row_data['VIEW'],
            shortlimit=row_data.get('SHORTLIMIT'),
            prev=row_data.get('PREV', 0.0),
            pactual=row_data.get('PACTUAL', 0.0),
            pexpected=row_data.get('PEXPECTED', 0.0),
            viewlg=row_data.get('VIEWLG', 0.0),
            mon=row_data.get('MON', ''),
            cont=row_data.get('CONT', ''),
            direction=row_data.get('DIRECTION', 1),
            source=row_data.get('SOURCE'),
            sink=row_data.get('SINK'),
            flow=row_data.get('FLOW', 0.0),
            limit=row_data.get('LIMIT', 0.0),
            last_binding=row_data.get('LAST_BINDING'),
            bhours=row_data.get('BHOURS', 0.0),
            maxhist=row_data.get('MAXHIST', 0.0),
            exp_peak=row_data.get('EXP_PEAK', 0.0),
            exp_op=row_data.get('EXP_OP', 0.0),
            recent_delta=row_data.get('RECENT_DELTA', 0.0)
        )
    
    def to_dataframe_dict(self) -> Dict[str, any]:
        """Convert ConstraintRow to dictionary for DataFrame updates."""
        return {
            'CLUSTER': self.cluster,
            'CUID': self.cuid,
            'VIEW': self.view,
            'SHORTLIMIT': self.shortlimit,
            'PREV': self.prev,
            'PACTUAL': self.pactual,
            'PEXPECTED': self.pexpected,
            'VIEWLG': self.viewlg,
            'MON': self.mon,
            'CONT': self.cont,
            'DIRECTION': self.direction,
            'SOURCE': self.source,
            'SINK': self.sink,
            'FLOW': self.flow,
            'LIMIT': self.limit,
            'LAST_BINDING': self.last_binding,
            'BHOURS': self.bhours,
            'MAXHIST': self.maxhist,
            'EXP_PEAK': self.exp_peak,
            'EXP_OP': self.exp_op,
            'RECENT_DELTA': self.recent_delta
        }
    
    @property
    def is_binding(self) -> bool:
        """Check if constraint is binding (flow >= 95% of limit)."""
        if self.limit == 0:
            return False
        return self.flow >= (0.95 * self.limit)
    
    @property 
    def has_outages(self) -> bool:
        """Check if constraint has outage comments."""
        return len(self.date_grid_comments) > 0
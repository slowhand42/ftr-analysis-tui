"""Central data management and business logic."""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import ClusterInfo, EditRecord, ExcelMetadata
from ..io import ExcelIO


logger = logging.getLogger(__name__)


class ExcelDataManager:
    """
    Manages Excel data in memory and coordinates business operations.
    
    This class is responsible for:
    - Loading and storing Excel data
    - Managing clusters and constraints
    - Handling data updates
    - Coordinating auto-save operations
    """
    
    def __init__(self, excel_io: Optional[ExcelIO] = None):
        """Initialize the data manager."""
        self.excel_io = excel_io or ExcelIO()
        self.data: Dict[str, pd.DataFrame] = {}
        self.metadata: Optional[ExcelMetadata] = None
        self.edit_history: List[EditRecord] = []
        self.file_path: Optional[str] = None
        self._cluster_cache: Dict[str, List[int]] = {}
        
    def load_excel(self, file_path: str) -> None:
        """
        Load Excel file into memory.
        
        Args:
            file_path: Path to the Excel file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        logger.info(f"Loading Excel file: {file_path}")
        start_time = datetime.now()
        
        # Load workbook
        self.data = self.excel_io.load_workbook(file_path)
        self.file_path = file_path
        
        # Build metadata
        self._build_metadata(start_time)
        
        # Build cluster cache
        self._build_cluster_cache()
        
        logger.info(f"Loaded {len(self.data)} sheets in {self.metadata.load_time_seconds:.2f}s")
        
    def get_cluster_data(self, sheet: str, cluster_id: int) -> pd.DataFrame:
        """
        Get all constraints for a specific cluster.
        
        Args:
            sheet: Sheet name
            cluster_id: Cluster identifier
            
        Returns:
            DataFrame with cluster's constraints
            
        Raises:
            KeyError: If sheet doesn't exist
            ValueError: If cluster doesn't exist
        """
        if sheet not in self.data:
            raise KeyError(f"Sheet '{sheet}' not found")
            
        df = self.data[sheet]
        cluster_data = df[df['CLUSTER'] == cluster_id].copy()
        
        if cluster_data.empty:
            raise ValueError(f"Cluster {cluster_id} not found in sheet {sheet}")
            
        return cluster_data
    
    def update_value(self, sheet: str, row: int, column: str, value: float) -> bool:
        """
        Update a single cell value.
        
        Args:
            sheet: Sheet name
            row: Row index
            column: Column name
            value: New value
            
        Returns:
            True if update successful
            
        Raises:
            KeyError: If sheet/column doesn't exist
            IndexError: If row is out of bounds
        """
        if sheet not in self.data:
            raise KeyError(f"Sheet '{sheet}' not found")
            
        df = self.data[sheet]
        
        if row < 0 or row >= len(df):
            raise IndexError(f"Row {row} out of bounds for sheet {sheet}")
            
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in sheet {sheet}")
        
        # Record edit
        old_value = df.at[row, column]
        cluster_id = df.at[row, 'CLUSTER']
        cuid = df.at[row, 'CUID'] if 'CUID' in df.columns else None
        
        edit = EditRecord(
            timestamp=datetime.now(),
            sheet=sheet,
            row=row,
            column=column,
            old_value=old_value if pd.notna(old_value) else None,
            new_value=value,
            cluster_id=cluster_id,
            cuid=cuid
        )
        
        # Update value
        df.at[row, column] = value
        self.edit_history.append(edit)
        
        logger.debug(f"Updated {sheet}[{row},{column}]: {old_value} -> {value}")
        return True
    
    def save_changes(self) -> str:
        """
        Save current data to a new timestamped file.
        
        Returns:
            Path to the saved file
        """
        if not self.file_path:
            raise ValueError("No file loaded")
            
        new_path = self.excel_io.save_workbook(self.data, self.file_path)
        logger.info(f"Saved changes to: {new_path}")
        return new_path
    
    def get_clusters_list(self, sheet: str) -> List[int]:
        """
        Get list of all cluster IDs in a sheet.
        
        Args:
            sheet: Sheet name
            
        Returns:
            Sorted list of cluster IDs
        """
        if sheet in self._cluster_cache:
            return self._cluster_cache[sheet]
            
        if sheet not in self.data:
            raise KeyError(f"Sheet '{sheet}' not found")
            
        clusters = self.data[sheet]['CLUSTER'].unique().tolist()
        clusters.sort()
        self._cluster_cache[sheet] = clusters
        return clusters
    
    def get_cluster_info(self, sheet: str, cluster_id: int) -> ClusterInfo:
        """
        Get detailed information about a cluster.
        
        Args:
            sheet: Sheet name
            cluster_id: Cluster identifier
            
        Returns:
            ClusterInfo object
        """
        cluster_data = self.get_cluster_data(sheet, cluster_id)
        
        # Extract info
        cuid_list = cluster_data['CUID'].tolist() if 'CUID' in cluster_data.columns else []
        has_sp = cluster_data['SP'].notna().any() if 'SP' in cluster_data.columns else False
        monitor = cluster_data['MON'].iloc[0] if 'MON' in cluster_data.columns else None
        contingency = cluster_data['CONT'].iloc[0] if 'CONT' in cluster_data.columns else None
        
        return ClusterInfo(
            cluster_id=cluster_id,
            constraint_count=len(cluster_data),
            cuid_list=cuid_list,
            has_sp_value=has_sp,
            monitor=monitor,
            contingency=contingency
        )
    
    def get_sheet_names(self) -> List[str]:
        """Get list of all sheet names."""
        return list(self.data.keys())
    
    def _build_metadata(self, start_time: datetime) -> None:
        """Build metadata about the loaded file."""
        import os
        
        total_rows = sum(len(df) for df in self.data.values())
        total_clusters = len(set(
            cluster 
            for df in self.data.values() 
            if 'CLUSTER' in df.columns
            for cluster in df['CLUSTER'].unique()
        ))
        
        file_stats = os.stat(self.file_path)
        
        self.metadata = ExcelMetadata(
            file_path=self.file_path,
            file_size_mb=file_stats.st_size / (1024 * 1024),
            sheet_names=list(self.data.keys()),
            total_rows=total_rows,
            total_clusters=total_clusters,
            load_time_seconds=(datetime.now() - start_time).total_seconds(),
            last_modified=datetime.fromtimestamp(file_stats.st_mtime)
        )
    
    def _build_cluster_cache(self) -> None:
        """Pre-build cluster lists for performance."""
        self._cluster_cache.clear()
        for sheet in self.data:
            if 'CLUSTER' in self.data[sheet].columns:
                clusters = self.data[sheet]['CLUSTER'].unique().tolist()
                clusters.sort()
                self._cluster_cache[sheet] = clusters
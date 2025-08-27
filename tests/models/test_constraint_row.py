"""
Tests for ConstraintRow data model.

Tests focus on the core functionality required by the PRD:
- Validation rules enforcement
- DataFrame integration (bidirectional conversion)
- Computed properties
- Field mapping and data integrity
"""

import pytest
from typing import Dict, Any, List
import pandas as pd

from src.models.data_models import ConstraintRow


class TestConstraintRowValidation:
    """Test validation rules for ConstraintRow fields."""
    
    def test_valid_constraint_row_creation(self):
        """Test creating a ConstraintRow with valid minimal data."""
        row = ConstraintRow(
            cluster=1,
            cuid="CONSTRAINT_001",
            view=100.0
        )
        
        assert row.cluster == 1
        assert row.cuid == "CONSTRAINT_001"
        assert row.view == 100.0
        assert row.shortlimit is None
    
    def test_view_must_be_positive(self):
        """Test that VIEW value must be greater than 0."""
        with pytest.raises(ValueError, match="VIEW must be positive"):
            ConstraintRow(
                cluster=1,
                cuid="CONSTRAINT_001",
                view=0.0  # Invalid: not positive
            )
        
        with pytest.raises(ValueError, match="VIEW must be positive"):
            ConstraintRow(
                cluster=1,
                cuid="CONSTRAINT_001",
                view=-50.0  # Invalid: negative
            )
    
    def test_shortlimit_must_be_negative_or_none(self):
        """Test that SHORTLIMIT must be negative or None."""
        # Valid: None
        row1 = ConstraintRow(
            cluster=1,
            cuid="CONSTRAINT_001", 
            view=100.0,
            shortlimit=None
        )
        assert row1.shortlimit is None
        
        # Valid: Negative value
        row2 = ConstraintRow(
            cluster=1,
            cuid="CONSTRAINT_002",
            view=100.0,
            shortlimit=-25.0
        )
        assert row2.shortlimit == -25.0
        
        # Invalid: Positive value
        with pytest.raises(ValueError, match="SHORTLIMIT must be negative"):
            ConstraintRow(
                cluster=1,
                cuid="CONSTRAINT_003",
                view=100.0,
                shortlimit=25.0
            )
        
        # Invalid: Zero
        with pytest.raises(ValueError, match="SHORTLIMIT must be negative"):
            ConstraintRow(
                cluster=1,
                cuid="CONSTRAINT_004",
                view=100.0,
                shortlimit=0.0
            )
    
    def test_direction_must_be_valid(self):
        """Test that DIRECTION must be -1 or 1."""
        # Valid directions
        row1 = ConstraintRow(cluster=1, cuid="C001", view=100.0, direction=1)
        assert row1.direction == 1
        
        row2 = ConstraintRow(cluster=1, cuid="C002", view=100.0, direction=-1)
        assert row2.direction == -1
        
        # Invalid direction
        with pytest.raises(ValueError, match="DIRECTION must be -1 or 1"):
            ConstraintRow(cluster=1, cuid="C003", view=100.0, direction=0)


class TestConstraintRowDataFrameIntegration:
    """Test bidirectional DataFrame conversion methods."""
    
    def test_from_dataframe_row_minimal(self):
        """Test creating ConstraintRow from minimal DataFrame row data."""
        row_data = {
            'CLUSTER': 5,
            'CUID': 'CONSTRAINT_ABC', 
            'VIEW': 150.0
        }
        
        row = ConstraintRow.from_dataframe_row(row_data)
        
        assert row.cluster == 5
        assert row.cuid == 'CONSTRAINT_ABC'
        assert row.view == 150.0
        assert row.shortlimit is None
        assert row.direction == 1  # default
    
    def test_from_dataframe_row_complete(self):
        """Test creating ConstraintRow from complete DataFrame row data."""
        row_data = {
            'CLUSTER': 3,
            'CUID': 'FULL_CONSTRAINT',
            'VIEW': 200.0,
            'SHORTLIMIT': -30.0,
            'PREV': 180.0,
            'PACTUAL': 190.0,
            'PEXPECTED': 185.0,
            'VIEWLG': 5.29,
            'MON': 'LINE_MONITOR',
            'CONT': 'CONTINGENCY_A',
            'DIRECTION': -1,
            'SOURCE': 'NODE_A',
            'SINK': 'NODE_B',
            'FLOW': 175.0,
            'LIMIT': 200.0,
            'LAST_BINDING': '2024-08-15',
            'BHOURS': 12.5,
            'MAXHIST': 220.0,
            'EXP_PEAK': 195.0,
            'EXP_OP': 180.0,
            'RECENT_DELTA': 15.0
        }
        
        row = ConstraintRow.from_dataframe_row(row_data)
        
        assert row.cluster == 3
        assert row.cuid == 'FULL_CONSTRAINT'
        assert row.view == 200.0
        assert row.shortlimit == -30.0
        assert row.prev == 180.0
        assert row.mon == 'LINE_MONITOR'
        assert row.cont == 'CONTINGENCY_A'
        assert row.direction == -1
        assert row.source == 'NODE_A'
        assert row.sink == 'NODE_B'
        assert row.flow == 175.0
        assert row.limit == 200.0
    
    def test_to_dataframe_dict(self):
        """Test converting ConstraintRow to dictionary for DataFrame updates."""
        row = ConstraintRow(
            cluster=2,
            cuid='TEST_CONSTRAINT',
            view=75.0,
            shortlimit=-15.0,
            prev=70.0,
            mon='TEST_MONITOR',
            direction=-1,
            flow=60.0,
            limit=80.0
        )
        
        df_dict = row.to_dataframe_dict()
        
        expected_dict = {
            'CLUSTER': 2,
            'CUID': 'TEST_CONSTRAINT',
            'VIEW': 75.0,
            'SHORTLIMIT': -15.0,
            'PREV': 70.0,
            'PACTUAL': 0.0,
            'PEXPECTED': 0.0,
            'VIEWLG': 0.0,
            'MON': 'TEST_MONITOR',
            'CONT': '',
            'DIRECTION': -1,
            'SOURCE': None,
            'SINK': None,
            'FLOW': 60.0,
            'LIMIT': 80.0,
            'LAST_BINDING': None,
            'BHOURS': 0.0,
            'MAXHIST': 0.0,
            'EXP_PEAK': 0.0,
            'EXP_OP': 0.0,
            'RECENT_DELTA': 0.0
        }
        
        assert df_dict == expected_dict


class TestConstraintRowComputedProperties:
    """Test computed properties of ConstraintRow."""
    
    def test_is_binding_property(self):
        """Test is_binding property calculation."""
        # Not binding: flow much less than limit
        row1 = ConstraintRow(
            cluster=1,
            cuid='C001',
            view=100.0,
            flow=50.0,
            limit=100.0
        )
        assert not row1.is_binding
        
        # Binding: flow >= 95% of limit
        row2 = ConstraintRow(
            cluster=1,
            cuid='C002', 
            view=100.0,
            flow=95.0,
            limit=100.0
        )
        assert row2.is_binding
        
        # Binding: flow exactly at limit
        row3 = ConstraintRow(
            cluster=1,
            cuid='C003',
            view=100.0,
            flow=100.0,
            limit=100.0
        )
        assert row3.is_binding
        
        # Binding: flow over limit
        row4 = ConstraintRow(
            cluster=1,
            cuid='C004',
            view=100.0,
            flow=105.0,
            limit=100.0
        )
        assert row4.is_binding
    
    def test_has_outages_property(self):
        """Test has_outages property based on date_grid_comments."""
        # No outages: empty comments
        row1 = ConstraintRow(
            cluster=1,
            cuid='C001',
            view=100.0,
            date_grid_comments={}
        )
        assert not row1.has_outages
        
        # Has outages: comments present
        row2 = ConstraintRow(
            cluster=1,
            cuid='C002',
            view=100.0,
            date_grid_comments={5: 'Transmission outage on line A-B'}
        )
        assert row2.has_outages
        
        # Has outages: multiple comments
        row3 = ConstraintRow(
            cluster=1,
            cuid='C003',
            view=100.0,
            date_grid_comments={
                3: 'Planned maintenance',
                7: 'Emergency outage'
            }
        )
        assert row3.has_outages


class TestConstraintRowFieldMapping:
    """Test field mapping and data integrity."""
    
    def test_all_required_fields_present(self):
        """Test that all required fields from PRD are included."""
        # Create with all fields to verify they exist
        row = ConstraintRow(
            cluster=1,
            cuid='COMPLETE_TEST',
            view=100.0,
            shortlimit=-10.0,
            prev=95.0,
            pactual=98.0,
            pexpected=97.0,
            viewlg=4.6,
            mon='MONITOR_XYZ',
            cont='CONT_123',
            direction=1,
            source='SRC_NODE',
            sink='SINK_NODE',
            flow=85.0,
            limit=100.0,
            last_binding='2024-08-20',
            bhours=8.5,
            maxhist=120.0,
            exp_peak=110.0,
            exp_op=90.0,
            recent_delta=-5.0,
            date_grid_values=[10.0, 15.0, 20.0],
            date_grid_comments={1: 'Test comment'},
            lodf_grid_values=[0.1, 0.2, 0.3]
        )
        
        # Verify all core fields
        assert hasattr(row, 'cluster')
        assert hasattr(row, 'cuid')
        assert hasattr(row, 'view')
        assert hasattr(row, 'shortlimit')
        
        # Verify predictor fields
        assert hasattr(row, 'prev')
        assert hasattr(row, 'pactual')
        assert hasattr(row, 'pexpected')
        assert hasattr(row, 'viewlg')
        
        # Verify monitor fields
        assert hasattr(row, 'mon')
        assert hasattr(row, 'cont')
        assert hasattr(row, 'direction')
        assert hasattr(row, 'source')
        assert hasattr(row, 'sink')
        
        # Verify flow fields
        assert hasattr(row, 'flow')
        assert hasattr(row, 'limit')
        assert hasattr(row, 'last_binding')
        assert hasattr(row, 'bhours')
        assert hasattr(row, 'maxhist')
        
        # Verify exposure fields
        assert hasattr(row, 'exp_peak')
        assert hasattr(row, 'exp_op')
        assert hasattr(row, 'recent_delta')
        
        # Verify grid data fields
        assert hasattr(row, 'date_grid_values')
        assert hasattr(row, 'date_grid_comments')
        assert hasattr(row, 'lodf_grid_values')
    
    def test_default_values_initialization(self):
        """Test that default values are properly initialized."""
        row = ConstraintRow(
            cluster=1,
            cuid='DEFAULT_TEST',
            view=100.0
        )
        
        # Required fields should have provided values
        assert row.cluster == 1
        assert row.cuid == 'DEFAULT_TEST'
        assert row.view == 100.0
        
        # Optional fields should have proper defaults
        assert row.shortlimit is None
        assert row.prev == 0.0
        assert row.pactual == 0.0
        assert row.pexpected == 0.0
        assert row.viewlg == 0.0
        assert row.mon == ""
        assert row.cont == ""
        assert row.direction == 1
        assert row.source is None
        assert row.sink is None
        assert row.flow == 0.0
        assert row.limit == 0.0
        assert row.last_binding is None
        assert row.bhours == 0.0
        assert row.maxhist == 0.0
        assert row.exp_peak == 0.0
        assert row.exp_op == 0.0
        assert row.recent_delta == 0.0
        assert row.date_grid_values == []
        assert row.date_grid_comments == {}
        assert row.lodf_grid_values == []
# Task 007: Implement ColorFormatter Core

## Overview
**Task ID**: task-007  
**Component**: ColorFormatter (Business Logic Layer)  
**Dependencies**: task-002 (Constraint Data Model) ✅  
**Status**: Pending  

## Description
Implement color calculation logic for VIEW/PREV/PACTUAL/PEXPECTED columns based on thresholds and gradients to visually indicate value ranges and changes.

## Architecture Context
ColorFormatter is part of the Business Logic Layer and provides:
- Color calculation based on value thresholds
- Gradient generation for value ranges
- Excel-compatible color schemes
- Performance-optimized color caching

## Implementation Requirements

### Core Functionality
1. **VIEW Column Colors**
   - Green: 0-50 MW
   - Yellow: 50-100 MW
   - Orange: 100-200 MW
   - Red: >200 MW
   - Support custom threshold configuration

2. **PREV Column Colors**
   - Match VIEW color scheme
   - Handle None/missing values
   - Indicate changes from previous values

3. **PACTUAL/PEXPECTED Colors**
   - Blue-white gradient for differences
   - Center white at zero difference
   - Blue for negative, darker for larger
   - Handle percentage calculations

4. **Color Utilities**
   - RGB to hex conversion
   - Color interpolation for gradients
   - Cache frequently used colors
   - Excel color compatibility

### Code Locations
- Implementation: `src/business_logic/color_formatter.py`
- Tests: `tests/business_logic/test_color_formatter.py`
- Uses: `src/models/constraint_row.py::ConstraintRow`

### Interface Definition
```python
@dataclass
class ColorConfig:
    thresholds: List[float]
    colors: List[str]  # Hex colors
    
class ColorFormatter:
    def __init__(self, config: Optional[ColorConfig] = None):
        """Initialize with optional custom color configuration."""
        
    def get_view_color(self, value: float) -> str:
        """Return hex color for VIEW value based on thresholds."""
        
    def get_prev_color(self, value: Optional[float]) -> str:
        """Return hex color for PREV value."""
        
    def get_pactual_color(self, actual: float, expected: float) -> str:
        """Return gradient color based on actual vs expected."""
        
    def calculate_gradient(self, value: float, min_val: float, 
                         max_val: float, color_start: str, 
                         color_end: str) -> str:
        """Calculate gradient color for value in range."""
        
    def interpolate_color(self, color1: str, color2: str, 
                         ratio: float) -> str:
        """Interpolate between two colors by ratio (0-1)."""
```

## Test Requirements (15 focused tests)

### Threshold-Based Colors
1. **test_view_green_range_0_to_50** - Values 0-50 return green
2. **test_view_yellow_range_50_to_100** - Values 50-100 return yellow
3. **test_view_orange_range_100_to_200** - Values 100-200 return orange
4. **test_view_red_above_200** - Values >200 return red
5. **test_view_boundary_values** - Test 50, 100, 200 exactly

### Gradient Calculations
6. **test_gradient_midpoint_returns_middle_color** - 50% returns mid color
7. **test_gradient_extremes_return_end_colors** - 0% and 100% correct
8. **test_pactual_zero_difference_returns_white** - Actual=Expected → white
9. **test_pactual_negative_returns_blue_shades** - Negative diffs → blue
10. **test_pactual_large_differences_saturate** - Cap at darkest shade

### Edge Cases
11. **test_handle_none_values_gracefully** - None returns neutral color
12. **test_handle_negative_view_values** - Unexpected negatives handled
13. **test_color_interpolation_accuracy** - RGB interpolation correct
14. **test_hex_color_format_consistency** - Always return #RRGGBB format
15. **test_custom_threshold_configuration** - Custom configs work

## Acceptance Criteria
- [ ] Colors match Excel visual appearance exactly
- [ ] Gradients are smooth and visually appealing
- [ ] Performance allows real-time color updates
- [ ] Custom thresholds can be configured
- [ ] All edge cases handled without errors

## Implementation Guidelines
- Use RGB color space for interpolation
- Cache color calculations for common values
- Provide sensible defaults for all thresholds
- Consider colorblind-friendly alternatives
- Keep calculations pure and fast
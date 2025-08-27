# Task 008: Implement RECENT_DELTA Formatting

## Task Overview
- **ID**: task-008
- **Name**: Implement RECENT_DELTA Formatting
- **Status**: pending
- **Dependencies**: [task-007]
- **Component**: Business Logic Layer
- **Module**: src/business_logic/color_formatter.py (extend existing)

## Task Description
Extend the ColorFormatter class to handle RECENT_DELTA column formatting with a blue-white-red gradient. This provides visual feedback on recent changes to constraint values.

## Functionality Requirements

### 1. Gradient Calculation
- **Blue (negative)**: Values < 0 scale from white to blue
- **White (zero)**: Values at or near zero (±0.01) show white
- **Red (positive)**: Values > 0 scale from white to red
- Maximum saturation at ±100 or beyond

### 2. Color Mapping
```python
# Color scale definition
DELTA_COLORS = {
    'strong_blue': (0, 0, 255),      # -100 or less
    'medium_blue': (100, 100, 255),  # -50
    'light_blue': (200, 200, 255),   # -25
    'white': (255, 255, 255),        # 0
    'light_red': (255, 200, 200),    # +25
    'medium_red': (255, 100, 100),   # +50
    'strong_red': (255, 0, 0)        # +100 or more
}
```

### 3. Implementation Details
- Linear interpolation between color stops
- Handle NaN/None values (return white or no color)
- Smooth gradient transitions
- Consistent with Excel conditional formatting

### 4. Integration with ColorFormatter
- Add method: `format_recent_delta(value: Optional[float]) -> str`
- Maintain consistency with existing color methods
- Use same RGB to terminal color conversion
- Cache computed gradients for performance

## Integration Points

### Dependencies
- **ColorFormatter class**: Extend existing class from task-007
- **Color utilities**: RGB to terminal color conversion

### Interfaces
```python
class ColorFormatter:
    def format_recent_delta(self, value: Optional[float]) -> str:
        """Format RECENT_DELTA with blue-white-red gradient"""
        pass
    
    def _compute_delta_gradient(self, value: float) -> Tuple[int, int, int]:
        """Compute RGB values for delta gradient"""
        pass
    
    def _interpolate_color(
        self, 
        value: float,
        min_val: float,
        max_val: float,
        min_color: Tuple[int, int, int],
        max_color: Tuple[int, int, int]
    ) -> Tuple[int, int, int]:
        """Linear color interpolation"""
        pass
```

## Test Requirements (10 focused tests)

### Core Gradient Tests
1. **test_zero_value_white**: Zero values return white color
2. **test_negative_values_blue**: Negative values show blue gradient
3. **test_positive_values_red**: Positive values show red gradient
4. **test_maximum_saturation**: Values ±100+ show full saturation

### Edge Cases
5. **test_nan_handling**: NaN values handled gracefully
6. **test_none_handling**: None values return appropriate default
7. **test_near_zero_values**: Values ±0.01 treated as zero

### Interpolation Tests
8. **test_linear_interpolation**: Smooth gradient between stops
9. **test_boundary_values**: Correct colors at -100, -50, 0, 50, 100
10. **test_extreme_values**: Handle values beyond ±100 correctly

## Acceptance Criteria

### Essential Behaviors
- Blue-white-red gradient matches specification
- Smooth transitions between color stops
- NaN/None values handled without errors
- Performance suitable for real-time updates

### Visual Requirements
- Colors match Excel conditional formatting closely
- Gradient is perceptually linear
- Clear distinction between positive/negative
- Zero values clearly identifiable as neutral

## Code Guidelines

### Implementation Notes
- Use efficient color interpolation algorithm
- Cache gradient calculations where possible
- Keep consistent with existing ColorFormatter patterns
- Minimize computational overhead

### Example Usage
```python
formatter = ColorFormatter()

# Zero value - white
color = formatter.format_recent_delta(0.0)  # Returns white

# Negative value - blue gradient
color = formatter.format_recent_delta(-50)  # Returns medium blue

# Positive value - red gradient  
color = formatter.format_recent_delta(75)   # Returns medium-strong red

# Apply to DataFrame column
df['RECENT_DELTA_COLOR'] = df['RECENT_DELTA'].apply(
    formatter.format_recent_delta
)
```

## Visual Examples
```
Value   | Color Description
--------|------------------
-150    | Deep blue (maximum)
-100    | Strong blue
-50     | Medium blue
-25     | Light blue
0       | White
+25     | Light red
+50     | Medium red
+100    | Strong red
+150    | Deep red (maximum)
```

## Task Completion Checklist
- [ ] All 10 tests written and passing
- [ ] Gradient calculation implemented
- [ ] Color interpolation working smoothly
- [ ] Edge cases handled properly
- [ ] Integration with ColorFormatter complete
- [ ] Performance optimized
- [ ] Visual verification against requirements
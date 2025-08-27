"""
Tests for ColorFormatter color calculation logic.

Tests focus on:
- Threshold-based color calculations for VIEW/SHORTLIMIT columns
- Gradient interpolation for PACTUAL/PEXPECTED differences
- Excel-compatible color output formats
- Custom threshold configuration
- Edge cases and error handling
- Performance considerations

This follows TDD methodology - tests are written BEFORE implementation.
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock

# Import will be available after implementation
from src.business_logic.color_formatter import ColorFormatter, ColorConfig


class TestViewColumnThresholdColors:
    """Test VIEW column color calculations based on MW thresholds."""
    
    def test_view_green_range_0_to_50(self):
        """Test that values 0-50 MW return green color."""
        formatter = ColorFormatter()
        
        # Test values in green range
        assert formatter.get_view_color(0.0) == "#00FF00"  # Green
        assert formatter.get_view_color(25.0) == "#00FF00"  # Green
        assert formatter.get_view_color(49.9) == "#00FF00"  # Green
    
    def test_view_yellow_range_50_to_100(self):
        """Test that values 50-100 MW return yellow color."""
        formatter = ColorFormatter()
        
        # Test values in yellow range
        assert formatter.get_view_color(50.0) == "#FFFF00"  # Yellow
        assert formatter.get_view_color(75.0) == "#FFFF00"  # Yellow
        assert formatter.get_view_color(99.9) == "#FFFF00"  # Yellow
    
    def test_view_orange_range_100_to_200(self):
        """Test that values 100-200 MW return orange color."""
        formatter = ColorFormatter()
        
        # Test values in orange range
        assert formatter.get_view_color(100.0) == "#FFA500"  # Orange
        assert formatter.get_view_color(150.0) == "#FFA500"  # Orange
        assert formatter.get_view_color(199.9) == "#FFA500"  # Orange
    
    def test_view_red_above_200(self):
        """Test that values >200 MW return red color."""
        formatter = ColorFormatter()
        
        # Test values in red range
        assert formatter.get_view_color(200.0) == "#FF0000"  # Red
        assert formatter.get_view_color(300.0) == "#FF0000"  # Red
        assert formatter.get_view_color(1000.0) == "#FF0000"  # Red
    
    def test_view_boundary_values(self):
        """Test exact threshold boundary values for consistent behavior."""
        formatter = ColorFormatter()
        
        # Test exact boundaries
        assert formatter.get_view_color(50.0) == "#FFFF00"  # Yellow at boundary
        assert formatter.get_view_color(100.0) == "#FFA500"  # Orange at boundary
        assert formatter.get_view_color(200.0) == "#FF0000"  # Red at boundary


class TestGradientCalculations:
    """Test gradient color interpolation logic."""
    
    def test_gradient_midpoint_returns_middle_color(self):
        """Test that 50% between colors returns interpolated middle color."""
        formatter = ColorFormatter()
        
        # Test midpoint between white (#FFFFFF) and blue (#0000FF)
        mid_color = formatter.calculate_gradient(
            value=0.5, 
            min_val=0.0, 
            max_val=1.0,
            color_start="#FFFFFF", 
            color_end="#0000FF"
        )
        assert mid_color == "#8080FF"  # Midpoint RGB values
    
    def test_gradient_extremes_return_end_colors(self):
        """Test that 0% and 100% return exact start and end colors."""
        formatter = ColorFormatter()
        
        # Test extremes
        start_color = formatter.calculate_gradient(
            value=0.0, 
            min_val=0.0, 
            max_val=1.0,
            color_start="#FF0000", 
            color_end="#00FF00"
        )
        assert start_color == "#FF0000"  # Exact start color
        
        end_color = formatter.calculate_gradient(
            value=1.0, 
            min_val=0.0, 
            max_val=1.0,
            color_start="#FF0000", 
            color_end="#00FF00"
        )
        assert end_color == "#00FF00"  # Exact end color
    
    def test_pactual_zero_difference_returns_white(self):
        """Test that zero difference between actual and expected returns white."""
        formatter = ColorFormatter()
        
        # Same values should return white
        color = formatter.get_pactual_color(actual=100.0, expected=100.0)
        assert color == "#FFFFFF"  # White for no difference
        
        # Very small differences should also return white or near-white
        color = formatter.get_pactual_color(actual=100.01, expected=100.0)
        assert color.startswith("#FF")  # Should be white or near-white
    
    def test_pactual_negative_returns_blue_shades(self):
        """Test that negative differences (actual < expected) return blue shades."""
        formatter = ColorFormatter()
        
        # Negative difference should return blue
        color = formatter.get_pactual_color(actual=80.0, expected=100.0)
        assert color.endswith("FF") or "00" in color[3:5]  # Should have blue component
        
        # Larger negative difference should return darker blue
        darker_color = formatter.get_pactual_color(actual=50.0, expected=100.0)
        assert darker_color != color  # Should be different shade
    
    def test_pactual_large_differences_saturate(self):
        """Test that very large differences saturate at darkest shade."""
        formatter = ColorFormatter()
        
        # Very large differences should saturate
        color1 = formatter.get_pactual_color(actual=0.0, expected=100.0)
        color2 = formatter.get_pactual_color(actual=-50.0, expected=100.0)
        
        # Both should saturate to same dark color
        assert color1 == color2  # Should saturate at same maximum


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    def test_handle_none_values_gracefully(self):
        """Test that None values return neutral color without errors."""
        formatter = ColorFormatter()
        
        # None should return neutral color
        color = formatter.get_prev_color(None)
        assert color == "#CCCCCC"  # Neutral gray
        
        # Should not raise exceptions
        try:
            formatter.get_view_color(None)
            assert False, "Should handle None gracefully"
        except TypeError:
            # Expected - None is not a valid float
            pass
    
    def test_handle_negative_view_values(self):
        """Test handling of unexpected negative VIEW values."""
        formatter = ColorFormatter()
        
        # Negative values should return minimum threshold color
        color = formatter.get_view_color(-10.0)
        assert color == "#00FF00"  # Should return green (minimum)
    
    def test_color_interpolation_accuracy(self):
        """Test RGB color interpolation produces accurate results."""
        formatter = ColorFormatter()
        
        # Test specific interpolation
        color = formatter.interpolate_color("#000000", "#FFFFFF", 0.5)
        assert color == "#808080"  # Exact 50% gray
        
        # Test quarter interpolation
        color = formatter.interpolate_color("#FF0000", "#0000FF", 0.25)
        assert color == "#BF0040"  # 25% toward blue
    
    def test_hex_color_format_consistency(self):
        """Test that all returned colors use consistent #RRGGBB format."""
        formatter = ColorFormatter()
        
        # All colors should be 7 characters starting with #
        colors = [
            formatter.get_view_color(25.0),
            formatter.get_view_color(75.0),
            formatter.get_view_color(150.0),
            formatter.get_view_color(250.0),
            formatter.get_prev_color(100.0),
            formatter.get_pactual_color(90.0, 100.0)
        ]
        
        for color in colors:
            assert len(color) == 7  # #RRGGBB format
            assert color.startswith("#")
            # All hex digits after #
            assert all(c in "0123456789ABCDEF" for c in color[1:].upper())
    
    def test_custom_threshold_configuration(self):
        """Test that custom threshold configurations work correctly."""
        # Custom config with different thresholds
        custom_config = ColorConfig(
            thresholds=[30.0, 80.0, 150.0],
            colors=["#00AA00", "#AAAA00", "#AA5500", "#AA0000"]
        )
        formatter = ColorFormatter(config=custom_config)
        
        # Test custom thresholds
        assert formatter.get_view_color(20.0) == "#00AA00"  # Custom green
        assert formatter.get_view_color(60.0) == "#AAAA00"  # Custom yellow
        assert formatter.get_view_color(120.0) == "#AA5500"  # Custom orange
        assert formatter.get_view_color(200.0) == "#AA0000"  # Custom red


class TestShortlimitColumnColors:
    """Test SHORTLIMIT column color calculations."""
    
    def test_shortlimit_uses_view_color_scheme(self):
        """Test that SHORTLIMIT values use same color scheme as VIEW."""
        formatter = ColorFormatter()
        
        # SHORTLIMIT should use same thresholds as VIEW
        # Note: SHORTLIMIT values are typically negative, but color based on absolute value
        assert formatter.get_shortlimit_color(-25.0) == "#00FF00"  # Green range
        assert formatter.get_shortlimit_color(-75.0) == "#FFFF00"  # Yellow range
        assert formatter.get_shortlimit_color(-150.0) == "#FFA500"  # Orange range
        assert formatter.get_shortlimit_color(-250.0) == "#FF0000"  # Red range
    
    def test_shortlimit_none_values_return_neutral(self):
        """Test that None SHORTLIMIT values return neutral color."""
        formatter = ColorFormatter()
        
        color = formatter.get_shortlimit_color(None)
        assert color == "#CCCCCC"  # Neutral gray for None


class TestExcelCompatibilityAndPerformance:
    """Test Excel color compatibility and performance optimizations."""
    
    def test_colors_match_excel_appearance(self):
        """Test that colors match Excel conditional formatting appearance."""
        formatter = ColorFormatter()
        
        # Standard Excel-compatible colors
        green = formatter.get_view_color(25.0)
        yellow = formatter.get_view_color(75.0) 
        orange = formatter.get_view_color(150.0)
        red = formatter.get_view_color(250.0)
        
        # Should be standard Excel colors
        assert green in ["#00FF00", "#00B050", "#70AD47"]  # Excel green variants
        assert yellow in ["#FFFF00", "#FFC000", "#C5C5C5"]  # Excel yellow variants
        assert orange in ["#FFA500", "#ED7D31", "#FF8C00"]  # Excel orange variants
        assert red in ["#FF0000", "#C55A5A", "#E74C3C"]  # Excel red variants
    
    def test_batch_color_calculation_performance(self):
        """Test that batch color calculations are efficient."""
        formatter = ColorFormatter()
        
        # Large batch of values
        test_values = [float(i) for i in range(0, 1000, 10)]
        
        # Should handle batch without performance issues
        colors = []
        for value in test_values:
            colors.append(formatter.get_view_color(value))
        
        # All colors should be valid
        assert len(colors) == len(test_values)
        assert all(isinstance(color, str) and color.startswith("#") for color in colors)


class TestBindingConstraintColors:
    """Test colors for binding vs non-binding constraints."""
    
    def test_binding_constraint_color_intensity(self):
        """Test that binding constraints get more intense colors."""
        formatter = ColorFormatter()
        
        # Mock constraint rows for testing
        binding_row = Mock()
        binding_row.is_binding = True
        binding_row.view = 150.0
        
        non_binding_row = Mock()
        non_binding_row.is_binding = False  
        non_binding_row.view = 150.0
        
        # Binding should be more intense
        binding_color = formatter.get_constraint_color(binding_row)
        non_binding_color = formatter.get_constraint_color(non_binding_row)
        
        # Colors should be different (binding more intense)
        assert binding_color != non_binding_color
    
    def test_color_intensity_based_on_percentage(self):
        """Test that color intensity varies based on flow percentage."""
        formatter = ColorFormatter()
        
        # Create mock rows with different flow percentages
        high_flow = Mock()
        high_flow.flow = 95.0
        high_flow.limit = 100.0  # 95% utilization
        high_flow.view = 150.0
        
        low_flow = Mock()
        low_flow.flow = 50.0
        low_flow.limit = 100.0  # 50% utilization
        low_flow.view = 150.0
        
        # Higher flow should have more intense color
        high_color = formatter.get_constraint_color(high_flow)
        low_color = formatter.get_constraint_color(low_flow)
        
        assert high_color != low_color


class TestRecentDeltaGradientFormatting:
    """Test RECENT_DELTA blue-white-red gradient formatting (Task 008)."""
    
    def test_zero_value_returns_white(self):
        """Test that zero values return white color."""
        formatter = ColorFormatter()
        
        # Exact zero should return white
        color = formatter.format_recent_delta(0.0)
        assert color == "#FFFFFF", "Zero value should return white"
        
        # Values within ±0.01 tolerance should also return white
        color = formatter.format_recent_delta(0.005)
        assert color == "#FFFFFF", "Near-zero positive value should return white"
        
        color = formatter.format_recent_delta(-0.009)
        assert color == "#FFFFFF", "Near-zero negative value should return white"
    
    def test_negative_values_return_blue_gradient(self):
        """Test that negative values show blue gradient scaling."""
        formatter = ColorFormatter()
        
        # Small negative should be light blue
        light_blue = formatter.format_recent_delta(-25.0)
        assert light_blue.startswith("#") and len(light_blue) == 7
        
        # Medium negative should be medium blue
        medium_blue = formatter.format_recent_delta(-50.0)
        assert medium_blue != light_blue, "Different negative values should produce different blues"
        
        # Large negative should be strong blue
        strong_blue = formatter.format_recent_delta(-100.0)
        assert strong_blue != medium_blue, "Larger negative should produce stronger blue"
        
        # Blue component should increase as value gets more negative
        # Extract blue component (last 2 hex digits)
        light_b = int(light_blue[-2:], 16)
        medium_b = int(medium_blue[-2:], 16)
        strong_b = int(strong_blue[-2:], 16)
        
        assert light_b > medium_b >= strong_b, "Blue component should increase with more negative values"
    
    def test_positive_values_return_red_gradient(self):
        """Test that positive values show red gradient scaling."""
        formatter = ColorFormatter()
        
        # Small positive should be light red
        light_red = formatter.format_recent_delta(25.0)
        assert light_red.startswith("#") and len(light_red) == 7
        
        # Medium positive should be medium red
        medium_red = formatter.format_recent_delta(50.0)
        assert medium_red != light_red, "Different positive values should produce different reds"
        
        # Large positive should be strong red
        strong_red = formatter.format_recent_delta(100.0)
        assert strong_red != medium_red, "Larger positive should produce stronger red"
        
        # Red component should be high, green/blue should decrease as value increases
        # Extract red component (first 2 hex digits after #)
        light_r = int(light_red[1:3], 16)
        medium_r = int(medium_red[1:3], 16)
        strong_r = int(strong_red[1:3], 16)
        
        assert light_r <= medium_r <= strong_r, "Red component should increase with more positive values"
    
    def test_maximum_saturation_at_hundred_plus(self):
        """Test that values ±100+ show full saturation."""
        formatter = ColorFormatter()
        
        # Test negative saturation
        neg_100 = formatter.format_recent_delta(-100.0)
        neg_150 = formatter.format_recent_delta(-150.0)
        neg_200 = formatter.format_recent_delta(-200.0)
        
        # Should saturate at -100, so -150 and -200 should be same as -100
        assert neg_100 == neg_150 == neg_200, "Negative values should saturate at -100"
        
        # Test positive saturation
        pos_100 = formatter.format_recent_delta(100.0)
        pos_150 = formatter.format_recent_delta(150.0)
        pos_200 = formatter.format_recent_delta(200.0)
        
        # Should saturate at +100, so +150 and +200 should be same as +100
        assert pos_100 == pos_150 == pos_200, "Positive values should saturate at +100"
    
    def test_nan_values_handled_gracefully(self):
        """Test that NaN values are handled without errors."""
        import math
        formatter = ColorFormatter()
        
        # NaN should return white or neutral color without raising exception
        color = formatter.format_recent_delta(float('nan'))
        assert color in ["#FFFFFF", "#CCCCCC"], "NaN should return white or neutral color"
        
        # Should not raise exceptions
        assert isinstance(color, str) and color.startswith("#")
    
    def test_none_values_handled_gracefully(self):
        """Test that None values return appropriate default."""
        formatter = ColorFormatter()
        
        # None should return neutral color without raising exception
        color = formatter.format_recent_delta(None)
        assert color in ["#FFFFFF", "#CCCCCC"], "None should return white or neutral color"
        
        # Should not raise exceptions
        assert isinstance(color, str) and color.startswith("#")
    
    def test_near_zero_threshold_tolerance(self):
        """Test that values ±0.01 are treated as zero."""
        formatter = ColorFormatter()
        
        # Values at ±0.01 boundary should return white
        color_pos = formatter.format_recent_delta(0.01)
        color_neg = formatter.format_recent_delta(-0.01)
        white = formatter.format_recent_delta(0.0)
        
        assert color_pos == white, "Value of +0.01 should be treated as zero"
        assert color_neg == white, "Value of -0.01 should be treated as zero"
        
        # Values just outside tolerance should not be white
        color_pos_outside = formatter.format_recent_delta(0.02)
        color_neg_outside = formatter.format_recent_delta(-0.02)
        
        assert color_pos_outside != white, "Value of +0.02 should not be treated as zero"
        assert color_neg_outside != white, "Value of -0.02 should not be treated as zero"
    
    def test_linear_gradient_interpolation_accuracy(self):
        """Test that gradient interpolation produces smooth transitions."""
        formatter = ColorFormatter()
        
        # Test midpoint values produce expected interpolated colors
        white = formatter.format_recent_delta(0.0)
        blue_50 = formatter.format_recent_delta(-50.0)
        red_50 = formatter.format_recent_delta(50.0)
        
        # Colors should be valid hex format
        assert all(len(c) == 7 and c.startswith("#") for c in [white, blue_50, red_50])
        
        # White should be exactly white
        assert white == "#FFFFFF"
        
        # Test that interpolation is smooth - values between should have intermediate colors
        blue_25 = formatter.format_recent_delta(-25.0)
        blue_75 = formatter.format_recent_delta(-75.0)
        
        # Extract RGB components for comparison
        def hex_to_rgb(hex_color):
            return int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        
        white_rgb = hex_to_rgb(white)
        blue_25_rgb = hex_to_rgb(blue_25)
        blue_50_rgb = hex_to_rgb(blue_50)
        blue_75_rgb = hex_to_rgb(blue_75)
        
        # Blue component should increase smoothly
        assert white_rgb[2] >= blue_25_rgb[2] >= blue_50_rgb[2] >= blue_75_rgb[2]
    
    def test_boundary_color_values_exact_match(self):
        """Test exact colors at key boundary values (-100, -50, 0, 50, 100)."""
        formatter = ColorFormatter()
        
        # Test exact boundary values
        neg_100 = formatter.format_recent_delta(-100.0)
        neg_50 = formatter.format_recent_delta(-50.0)
        zero = formatter.format_recent_delta(0.0)
        pos_50 = formatter.format_recent_delta(50.0)
        pos_100 = formatter.format_recent_delta(100.0)
        
        # Zero should be white
        assert zero == "#FFFFFF"
        
        # All should be valid hex colors
        colors = [neg_100, neg_50, zero, pos_50, pos_100]
        for color in colors:
            assert len(color) == 7 and color.startswith("#")
            # Verify all characters are valid hex
            assert all(c in "0123456789ABCDEF" for c in color[1:].upper())
        
        # Negative values should have high blue component
        assert int(neg_50[-2:], 16) > 200, "-50 should have strong blue component"
        assert int(neg_100[-2:], 16) == 255, "-100 should have maximum blue component"
        
        # Positive values should have high red component
        assert int(pos_50[1:3], 16) > 200, "+50 should have strong red component"
        assert int(pos_100[1:3], 16) == 255, "+100 should have maximum red component"
    
    def test_extreme_values_beyond_saturation(self):
        """Test that values beyond ±100 are handled correctly."""
        formatter = ColorFormatter()
        
        # Test extreme negative values
        extreme_neg = [-500.0, -1000.0, -10000.0]
        saturated_color = formatter.format_recent_delta(-100.0)
        
        for value in extreme_neg:
            color = formatter.format_recent_delta(value)
            assert color == saturated_color, f"Value {value} should saturate to same color as -100"
        
        # Test extreme positive values
        extreme_pos = [500.0, 1000.0, 10000.0]
        saturated_color = formatter.format_recent_delta(100.0)
        
        for value in extreme_pos:
            color = formatter.format_recent_delta(value)
            assert color == saturated_color, f"Value {value} should saturate to same color as +100"
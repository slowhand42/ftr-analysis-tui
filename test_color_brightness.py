#!/usr/bin/env python3
"""Test script to verify text color adaptation based on background brightness."""

from src.core.formatter import ColorFormatter

def test_text_color_for_backgrounds():
    """Test that text colors are chosen appropriately for different backgrounds."""
    formatter = ColorFormatter(theme="dark")
    
    test_cases = [
        # (background_hex, expected_text_color, description)
        ("#000000", "white", "Black background"),
        ("#FFFFFF", "black", "White background"),
        ("#FF0000", "white", "Red background"),
        ("#FFFF00", "black", "Yellow background"),
        ("#0000FF", "white", "Blue background"),
        ("#00FF00", "black", "Green background"),
        ("#808080", "black", "Gray background"),
        ("#404040", "white", "Dark gray background"),
        ("#C0C0C0", "black", "Light gray background"),
        ("#FFA500", "black", "Orange background"),
        ("#800080", "white", "Purple background"),
        ("#FFC0CB", "black", "Pink background"),
        ("#1A1A1A", "white", "Very dark gray (neutral dark)"),
        ("#F0F0F0", "black", "Very light gray"),
    ]
    
    print("Testing text color selection based on background brightness:\n")
    print("Background | Text Color | Result | Description")
    print("-" * 60)
    
    all_passed = True
    for bg_color, expected, description in test_cases:
        result = formatter.get_text_color_for_background(bg_color)
        passed = result == expected
        status = "✓" if passed else "✗"
        
        if not passed:
            all_passed = False
            
        print(f"{bg_color:10} | {result:10} | {status:6} | {description}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Text colors adapt correctly.")
    else:
        print("❌ Some tests failed. Check the implementation.")
    
    # Test specific color gradients
    print("\n\nTesting color gradients from ColorFormatter:")
    print("-" * 60)
    
    # Test neutral to yellow to red gradient (core columns)
    test_values = [0.0, 0.5, 0.75, 1.0, 5.0, 10.0, 15.0, 20.0, 25.0]
    print("\nCore column colors (VIEW, PREV, etc.):")
    print("Value | Background Color | Text Color")
    print("-" * 40)
    
    for val in test_values:
        bg = formatter._get_core_column_color(val)
        if bg not in ["#FFFFFF", "#1A1A1A"]:  # Skip neutral colors
            text = formatter.get_text_color_for_background(bg)
            print(f"{val:5.1f} | {bg:16} | {text}")
    
    # Test blue to neutral to red gradient (RECENT_DELTA)
    test_values = [-60, -50, -25, 0, 25, 50, 60]
    print("\nRECENT_DELTA colors:")
    print("Value | Background Color | Text Color")
    print("-" * 40)
    
    for val in test_values:
        bg = formatter._get_recent_delta_color(val)
        if bg not in ["#FFFFFF", "#1A1A1A"]:  # Skip neutral colors
            text = formatter.get_text_color_for_background(bg)
            print(f"{val:5} | {bg:16} | {text}")

if __name__ == "__main__":
    test_text_color_for_backgrounds()
"""
Test suite for DataValidator class following TDD methodology.
Tests cover input validation, edge cases, and error handling.
"""

import pytest
from typing import Any, Optional
from dataclasses import dataclass

# Import will be available after implementation
try:
    from src.business_logic.validators import DataValidator, ValidationResult
except ImportError:
    # For TDD - these will be implemented after tests
    @dataclass
    class ValidationResult:
        is_valid: bool
        error_message: Optional[str] = None
        sanitized_value: Optional[Any] = None
    
    class DataValidator:
        pass


class TestDataValidatorViewValidation:
    """Test VIEW column validation (must be positive)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_view_accepts_positive_integers(self):
        """Test 1: VIEW accepts valid positive integer values."""
        # Test various positive integers
        test_values = [1, 100, 9999, 42]
        
        for value in test_values:
            result = self.validator.validate_view(value)
            assert result.is_valid is True
            assert result.error_message is None
            assert result.sanitized_value == value
    
    def test_view_rejects_zero_and_negative(self):
        """Test 2: VIEW rejects zero and negative values."""
        # Test invalid values
        test_values = [0, -1, -100, -0.5]
        
        for value in test_values:
            result = self.validator.validate_view(value)
            assert result.is_valid is False
            assert result.error_message is not None
            assert "positive" in result.error_message.lower()
            assert result.sanitized_value is None
    
    def test_view_handles_string_conversion(self):
        """Test 3: VIEW converts valid string numbers correctly."""
        # Test string inputs that should convert to valid values
        test_cases = [
            ("100", 100),
            ("1", 1),
            ("9999", 9999),
            ("42.0", 42.0)
        ]
        
        for input_str, expected_value in test_cases:
            result = self.validator.validate_view(input_str)
            assert result.is_valid is True
            assert result.error_message is None
            assert result.sanitized_value == expected_value
    
    def test_view_rejects_non_numeric(self):
        """Test 4: VIEW rejects non-numeric string inputs."""
        # Test invalid string inputs
        test_values = ["abc", "100abc", "!@#", "", "None", "null"]
        
        for value in test_values:
            result = self.validator.validate_view(value)
            assert result.is_valid is False
            assert result.error_message is not None
            assert "numeric" in result.error_message.lower() or "number" in result.error_message.lower()
            assert result.sanitized_value is None


class TestDataValidatorShortlimitValidation:
    """Test SHORTLIMIT column validation (must be negative or None)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_shortlimit_accepts_negative_numbers(self):
        """Test 5: SHORTLIMIT accepts negative values."""
        # Test various negative numbers
        test_values = [-1, -100, -9999, -0.5, -100.5]
        
        for value in test_values:
            result = self.validator.validate_shortlimit(value)
            assert result.is_valid is True
            assert result.error_message is None
            assert result.sanitized_value == value
    
    def test_shortlimit_accepts_none_empty(self):
        """Test 6: SHORTLIMIT allows None/empty values for clearing."""
        # Test None and empty values
        test_values = [None, "", "   "]
        
        for value in test_values:
            result = self.validator.validate_shortlimit(value)
            assert result.is_valid is True
            assert result.error_message is None
            assert result.sanitized_value is None
    
    def test_shortlimit_rejects_positive_and_zero(self):
        """Test 7: SHORTLIMIT rejects positive values and zero."""
        # Test invalid values
        test_values = [0, 1, 100, 0.5, 999.9]
        
        for value in test_values:
            result = self.validator.validate_shortlimit(value)
            assert result.is_valid is False
            assert result.error_message is not None
            assert "negative" in result.error_message.lower()
            assert result.sanitized_value is None
    
    def test_shortlimit_handles_string_conversion(self):
        """Test 8: SHORTLIMIT converts valid negative string numbers."""
        # Test string inputs that should convert to valid values
        test_cases = [
            ("-100", -100),
            ("-1", -1),
            ("-0.5", -0.5),
            ("-999.99", -999.99)
        ]
        
        for input_str, expected_value in test_cases:
            result = self.validator.validate_shortlimit(input_str)
            assert result.is_valid is True
            assert result.error_message is None
            assert result.sanitized_value == expected_value


class TestDataValidatorEdgeCases:
    """Test edge cases and special input handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_handle_whitespace_in_inputs(self):
        """Test 9: Handle whitespace correctly in string inputs."""
        # Test whitespace trimming for both VIEW and SHORTLIMIT
        view_cases = [
            ("  100  ", 100),
            ("\t42\n", 42),
            (" 1 ", 1)
        ]
        
        for input_str, expected_value in view_cases:
            result = self.validator.validate_view(input_str)
            assert result.is_valid is True
            assert result.sanitized_value == expected_value
        
        shortlimit_cases = [
            ("  -100  ", -100),
            ("\t-42\n", -42),
            (" -1.5 ", -1.5),
            ("   ", None)  # Empty whitespace becomes None
        ]
        
        for input_str, expected_value in shortlimit_cases:
            result = self.validator.validate_shortlimit(input_str)
            assert result.is_valid is True
            assert result.sanitized_value == expected_value
    
    def test_handle_decimal_inputs(self):
        """Test 10: Handle decimal number inputs appropriately."""
        # VIEW should accept positive decimals
        view_decimals = [100.5, 1.1, 999.99]
        
        for value in view_decimals:
            result = self.validator.validate_view(value)
            assert result.is_valid is True
            assert result.sanitized_value == value
        
        # SHORTLIMIT should accept negative decimals
        shortlimit_decimals = [-100.5, -1.1, -999.99]
        
        for value in shortlimit_decimals:
            result = self.validator.validate_shortlimit(value)
            assert result.is_valid is True
            assert result.sanitized_value == value
    
    def test_handle_scientific_notation(self):
        """Test 11: Parse scientific notation correctly."""
        # Test scientific notation for VIEW (positive values)
        view_scientific = [
            ("1e3", 1000.0),
            ("1.5E2", 150.0),
            ("2e0", 2.0)
        ]
        
        for input_str, expected_value in view_scientific:
            result = self.validator.validate_view(input_str)
            assert result.is_valid is True
            assert result.sanitized_value == expected_value
        
        # Test scientific notation for SHORTLIMIT (negative values)
        shortlimit_scientific = [
            ("-1e2", -100.0),
            ("-2.5E1", -25.0),
            ("-1e0", -1.0)
        ]
        
        for input_str, expected_value in shortlimit_scientific:
            result = self.validator.validate_shortlimit(input_str)
            assert result.is_valid is True
            assert result.sanitized_value == expected_value
        
        # Positive scientific notation should be rejected for SHORTLIMIT
        result = self.validator.validate_shortlimit("1e2")
        assert result.is_valid is False
        assert "negative" in result.error_message.lower()
    
    def test_provide_helpful_error_messages(self):
        """Test 12: Error messages are clear and actionable."""
        # Test VIEW error messages
        view_result = self.validator.validate_view(-100)
        assert "VIEW must be a positive number greater than 0" in view_result.error_message
        
        view_text_result = self.validator.validate_view("abc")
        assert "unable to convert" in view_text_result.error_message.lower()
        assert "number" in view_text_result.error_message.lower()
        
        # Test SHORTLIMIT error messages
        shortlimit_result = self.validator.validate_shortlimit(100)
        assert "SHORTLIMIT must be negative or empty" in shortlimit_result.error_message
        
        shortlimit_zero_result = self.validator.validate_shortlimit(0)
        assert "SHORTLIMIT cannot be zero" in shortlimit_zero_result.error_message
        
        # Error messages should be specific to the column
        assert "VIEW" in view_result.error_message
        assert "SHORTLIMIT" in shortlimit_result.error_message


class TestDataValidatorGeneralFunctionality:
    """Test general validation functionality and utility methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_validate_cell_routes_correctly(self):
        """Test that validate_cell routes to appropriate column validators."""
        # Test VIEW column routing
        result = self.validator.validate_cell("VIEW", 100)
        assert result.is_valid is True
        
        result = self.validator.validate_cell("VIEW", -100)
        assert result.is_valid is False
        
        # Test SHORTLIMIT column routing
        result = self.validator.validate_cell("SHORTLIMIT", -100)
        assert result.is_valid is True
        
        result = self.validator.validate_cell("SHORTLIMIT", 100)
        assert result.is_valid is False
    
    def test_sanitize_numeric_input_edge_cases(self):
        """Test numeric input sanitization handles edge cases."""
        # Test various input formats
        test_cases = [
            ("100", 100.0),
            ("-100", -100.0),
            ("100.5", 100.5),
            ("1e3", 1000.0),
            ("  100  ", 100.0),
            ("", None),
            (None, None),
            ("abc", None),
            ("100abc", None),
            ("--100", None)  # Invalid format
        ]
        
        for input_val, expected in test_cases:
            result = self.validator.sanitize_numeric_input(input_val)
            assert result == expected
    
    def test_get_column_rules_returns_correct_rules(self):
        """Test that column rules are returned correctly."""
        # Test VIEW column rules
        view_rules = self.validator.get_column_rules("VIEW")
        assert view_rules["min_value"] == 0
        assert view_rules["exclusive_min"] is True
        assert view_rules["allow_none"] is False
        
        # Test SHORTLIMIT column rules
        shortlimit_rules = self.validator.get_column_rules("SHORTLIMIT")
        assert shortlimit_rules["max_value"] == 0
        assert shortlimit_rules["exclusive_max"] is True
        assert shortlimit_rules["allow_none"] is True
        
        # Test unknown column returns default rules
        unknown_rules = self.validator.get_column_rules("UNKNOWN")
        assert "allow_any" in unknown_rules
        assert unknown_rules["allow_any"] is True
    
    def test_batch_validation_performance(self):
        """Test batch validation of multiple values."""
        # Simulate validating multiple VIEW values at once
        view_values = [1, 100, 500, 1000, 2000]
        
        # This should be efficient and not fail
        for value in view_values:
            result = self.validator.validate_view(value)
            assert result.is_valid is True
        
        # Test mixed valid/invalid batch
        mixed_values = [100, -50, "abc", 200, 0]
        results = []
        
        for value in mixed_values:
            results.append(self.validator.validate_view(value))
        
        # Should have 2 valid results (100, 200) and 3 invalid
        valid_results = [r for r in results if r.is_valid]
        invalid_results = [r for r in results if not r.is_valid]
        
        assert len(valid_results) == 2
        assert len(invalid_results) == 3
    
    def test_validation_result_structure(self):
        """Test that ValidationResult has proper structure."""
        # Test successful validation result
        valid_result = self.validator.validate_view(100)
        assert hasattr(valid_result, 'is_valid')
        assert hasattr(valid_result, 'error_message')
        assert hasattr(valid_result, 'sanitized_value')
        assert isinstance(valid_result.is_valid, bool)
        
        # Test failed validation result
        invalid_result = self.validator.validate_view(-100)
        assert invalid_result.is_valid is False
        assert isinstance(invalid_result.error_message, str)
        assert invalid_result.sanitized_value is None
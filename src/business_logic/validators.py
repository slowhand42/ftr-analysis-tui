"""
DataValidator implementation for input validation and business rule enforcement.

Provides comprehensive validation for VIEW (positive numbers) and SHORTLIMIT
(negative numbers or None) columns with detailed error messages and edge case handling.
"""

from typing import Any, Dict, Optional
from src.models.data_models import ValidationResult


class DataValidator:
    """
    Validates user inputs according to business rules.

    Key validation rules:
    - VIEW: Must be positive number (>0)
    - SHORTLIMIT: Must be negative number (<0) or None/empty
    """

    def __init__(self):
        """Initialize validator with column rules."""
        self._column_rules = {
            "VIEW": {
                "min_value": 0,
                "exclusive_min": True,
                "allow_none": False,
                "description": "VIEW must be a positive number greater than 0"
            },
            "SHORTLIMIT": {
                "max_value": 0,
                "exclusive_max": True,
                "allow_none": True,
                "description": "SHORTLIMIT must be negative or empty"
            }
        }

    def validate_view(self, value: Any) -> ValidationResult:
        """
        Validate VIEW column input (must be positive number > 0).

        Args:
            value: Input value to validate (can be number, string, or None)

        Returns:
            ValidationResult with validation status, error message, and sanitized value
        """
        # Handle None/empty values
        if value is None:
            return ValidationResult(
                is_valid=False,
                error_message="VIEW must be a positive number greater than 0",
                sanitized_value=None
            )

        # Try to convert to numeric value
        numeric_value = self.sanitize_numeric_input(value)

        # Check if conversion failed
        if numeric_value is None:
            return ValidationResult(
                is_valid=False,
                error_message="Unable to convert input to a number",
                sanitized_value=None
            )

        # Check if value is positive
        if numeric_value <= 0:
            return ValidationResult(
                is_valid=False,
                error_message="VIEW must be a positive number greater than 0",
                sanitized_value=None
            )

        # Value is valid
        return ValidationResult(
            is_valid=True,
            error_message=None,
            sanitized_value=numeric_value
        )

    def validate_shortlimit(self, value: Any) -> ValidationResult:
        """
        Validate SHORTLIMIT column input (must be negative number < 0 or None).

        Args:
            value: Input value to validate (can be number, string, or None)

        Returns:
            ValidationResult with validation status, error message, and sanitized value
        """
        # Handle None/empty values - these are allowed for SHORTLIMIT
        if value is None:
            return ValidationResult(
                is_valid=True,
                error_message=None,
                sanitized_value=None
            )

        # Handle empty strings and whitespace-only strings
        if isinstance(value, str):
            stripped_value = value.strip()
            if not stripped_value:
                return ValidationResult(
                    is_valid=True,
                    error_message=None,
                    sanitized_value=None
                )

        # Try to convert to numeric value
        numeric_value = self.sanitize_numeric_input(value)

        # Check if conversion failed
        if numeric_value is None:
            return ValidationResult(
                is_valid=False,
                error_message="Unable to convert input to a number",
                sanitized_value=None
            )

        # Check if value is zero (special case)
        if numeric_value == 0:
            return ValidationResult(
                is_valid=False,
                error_message="SHORTLIMIT cannot be zero - must be negative or empty",
                sanitized_value=None
            )

        # Check if value is positive (not allowed)
        if numeric_value > 0:
            return ValidationResult(
                is_valid=False,
                error_message="SHORTLIMIT must be negative or empty",
                sanitized_value=None
            )

        # Value is valid (negative)
        return ValidationResult(
            is_valid=True,
            error_message=None,
            sanitized_value=numeric_value
        )

    def validate_cell(self, column: str, value: Any) -> ValidationResult:
        """
        Validate any cell based on column rules (generic routing method).

        Args:
            column: Column name (e.g., "VIEW", "SHORTLIMIT")
            value: Input value to validate

        Returns:
            ValidationResult with validation status, error message, and sanitized value
        """
        column_upper = column.upper()

        if column_upper == "VIEW":
            return self.validate_view(value)
        elif column_upper == "SHORTLIMIT":
            return self.validate_shortlimit(value)
        else:
            # Unknown column - allow any value
            return ValidationResult(
                is_valid=True,
                error_message=None,
                sanitized_value=value
            )

    def sanitize_numeric_input(self, value: Any) -> Optional[float]:
        """
        Clean and convert string input to number, handling edge cases.

        Args:
            value: Input value (string, number, or None)

        Returns:
            Converted float value or None if conversion fails
        """
        # Handle None
        if value is None:
            return None

        # Handle already numeric values
        if isinstance(value, (int, float)):
            return float(value)

        # Handle string inputs
        if isinstance(value, str):
            # Strip whitespace
            cleaned = value.strip()

            # Handle empty strings
            if not cleaned:
                return None

            # Try to convert to float
            try:
                return float(cleaned)
            except ValueError:
                # Conversion failed
                return None

        # Handle other types - try conversion
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def get_column_rules(self, column: str) -> Dict[str, Any]:
        """
        Return validation rules for a column.

        Args:
            column: Column name to get rules for

        Returns:
            Dictionary of validation rules for the column
        """
        column_upper = column.upper()

        if column_upper in self._column_rules:
            return self._column_rules[column_upper].copy()
        else:
            # Default rules for unknown columns
            return {"allow_any": True}

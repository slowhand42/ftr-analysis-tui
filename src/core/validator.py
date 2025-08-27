"""Input validation logic for editable fields."""

import logging

from ..models import ValidationResult, ColumnType


logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates user inputs according to business rules.

    Validation rules:
    - VIEW: Must be positive real number (>0)
    - SHORTLIMIT: Must be negative number (<0) or empty
    - SP: Must be positive real number (>0)
    """

    def validate(self, value: str, column_type: ColumnType) -> ValidationResult:
        """
        Validate input based on column type.

        Args:
            value: String input from user
            column_type: Type of column being edited

        Returns:
            ValidationResult with parsed value or error
        """
        # Map column type to validation method
        validators = {
            ColumnType.VIEW: self.validate_view,
            ColumnType.SHORTLIMIT: self.validate_shortlimit,
            ColumnType.SP: self.validate_sp,
        }

        validator = validators.get(column_type, self.validate_generic)
        return validator(value)

    def validate_view(self, value: str) -> ValidationResult:
        """
        Validate VIEW column input.

        VIEW must be a positive real number (>0).
        """
        value = value.strip()

        if not value:
            return ValidationResult(
                is_valid=False,
                error_message="VIEW cannot be empty"
            )

        try:
            parsed = float(value)
            if parsed <= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="VIEW must be positive (>0)"
                )

            return ValidationResult(
                is_valid=True,
                sanitized_value=parsed
            )

        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid number: {value}"
            )

    def validate_shortlimit(self, value: str) -> ValidationResult:
        """
        Validate SHORTLIMIT column input.

        SHORTLIMIT must be negative (<0) or empty.
        """
        value = value.strip()

        # Empty is valid for SHORTLIMIT
        if not value:
            return ValidationResult(
                is_valid=True,
                sanitized_value=None
            )

        try:
            parsed = float(value)
            if parsed >= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="SHORTLIMIT must be negative (<0)"
                )

            return ValidationResult(
                is_valid=True,
                sanitized_value=parsed
            )

        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid number: {value}"
            )

    def validate_sp(self, value: str) -> ValidationResult:
        """
        Validate SP column input.

        SP must be a positive real number (>0).
        """
        # Same rules as VIEW
        return self.validate_view(value)

    def validate_generic(self, value: str) -> ValidationResult:
        """
        Generic validation for numeric columns.

        Accepts any valid number.
        """
        value = value.strip()

        if not value:
            return ValidationResult(
                is_valid=True,
                sanitized_value=None
            )

        try:
            parsed = float(value)
            return ValidationResult(
                is_valid=True,
                sanitized_value=parsed
            )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid number: {value}"
            )

    def is_editable_column(self, column_name: str) -> bool:
        """
        Check if a column is editable.

        Args:
            column_name: Name of the column

        Returns:
            True if column can be edited
        """
        editable_columns = {'VIEW', 'SHORTLIMIT', 'SP'}
        return column_name.upper() in editable_columns

    def get_column_type(self, column_name: str) -> ColumnType:
        """
        Map column name to ColumnType enum.

        Args:
            column_name: Name of the column

        Returns:
            ColumnType enum value
        """
        column_map = {
            'VIEW': ColumnType.VIEW,
            'SHORTLIMIT': ColumnType.SHORTLIMIT,
            'SP': ColumnType.SP,
            'PREV': ColumnType.PREV,
            'PACTUAL': ColumnType.PACTUAL,
            'PEXPECTED': ColumnType.PEXPECTED,
            'VIEWLG': ColumnType.VIEWLG,
            'CSP95': ColumnType.CSP95,
            'CSP80': ColumnType.CSP80,
            'CSP50': ColumnType.CSP50,
            'CSP20': ColumnType.CSP20,
            'CSP5': ColumnType.CSP5,
            'RECENT_DELTA': ColumnType.RECENT_DELTA,
            'FLOW': ColumnType.FLOW,
        }

        upper_name = column_name.upper()

        # Check if it's a date column (YYYY-MM-DD format)
        if '-' in column_name and len(column_name) == 10:
            try:
                # Simple date format check
                parts = column_name.split('-')
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    return ColumnType.DATE_COLUMN
            except (ValueError, AttributeError):
                pass

        # Check if it's a LODF column
        if column_name.startswith('LODF'):
            return ColumnType.LODF_COLUMN

        return column_map.get(upper_name, ColumnType.OTHER)

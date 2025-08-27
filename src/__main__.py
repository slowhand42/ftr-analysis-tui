"""Entry point for the Flow Analysis TUI application."""

import sys
from pathlib import Path
from .app import AnalysisTUIApp


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python -m src <excel_file>")
        print("Example: python -m src analysis_files/flow_results_processed_SEP25_R1.xlsx")
        sys.exit(1)
    
    excel_file = Path(sys.argv[1])
    if not excel_file.exists():
        print(f"Error: File '{excel_file}' not found")
        sys.exit(1)
    
    app = AnalysisTUIApp(str(excel_file))
    app.run()


if __name__ == "__main__":
    main()
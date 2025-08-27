#!/usr/bin/env python3
"""
Simple entry point for the Analysis TUI application.

This file allows running the app directly without installation:
    python analysis_tui.py <excel_file>
"""

import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent))

from src.app import main

if __name__ == "__main__":
    main()
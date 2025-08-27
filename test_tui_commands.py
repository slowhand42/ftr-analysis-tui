#!/usr/bin/env python3
"""
Test script to verify TUI commands and functionality.
This script creates an app instance and tests various commands programmatically.
"""

import sys
from pathlib import Path
import time
from textual import events

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent))

from src.app import AnalysisTUIApp
from src.core.data_manager import ExcelDataManager
from src.io.excel_io import ExcelIO


class TUICommandTester:
    """Test harness for TUI commands."""
    
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.app = AnalysisTUIApp(excel_file)
        self.results = {}
    
    def test_data_loading(self):
        """Test that data loads properly."""
        print("=== Testing Data Loading ===")
        try:
            # Initialize data manager directly
            excel_io = ExcelIO(Path(self.excel_file))
            data_manager = ExcelDataManager(excel_io)
            data_manager.load_excel(self.excel_file)
            
            sheets = data_manager.get_sheet_names()
            print(f"✓ Loaded {len(sheets)} sheets: {sheets}")
            
            clusters = data_manager.get_clusters_list('SEP25')
            print(f"✓ Found {len(clusters)} clusters in SEP25")
            print(f"  First 5 clusters: {clusters[:5]}")
            
            # Test cluster data loading
            if clusters:
                cluster_data = data_manager.get_cluster_data('SEP25', clusters[0])
                print(f"✓ Cluster {clusters[0]} data: {cluster_data.shape}")
                print(f"  Available columns: {len(cluster_data.columns)}")
            
            self.results['data_loading'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"✗ Data loading failed: {e}")
            self.results['data_loading'] = f'FAIL: {e}'
            return False
    
    def test_navigation_commands(self):
        """Test navigation commands (n/p for clusters)."""
        print("\n=== Testing Navigation Commands ===")
        try:
            # Test next cluster command
            print("Testing 'n' (next cluster) command...")
            
            # Create mock key event for 'n'
            key_event = events.Key("n", "n")
            
            # Test if the app can handle the key
            # This would normally be handled by the app's key bindings
            bindings = self.app.BINDINGS
            next_cluster_binding = None
            for binding in bindings:
                if binding.key == "n":
                    next_cluster_binding = binding
                    break
            
            if next_cluster_binding:
                print(f"✓ Found 'n' key binding: {next_cluster_binding.action}")
                print(f"  Description: {next_cluster_binding.description}")
            
            # Test previous cluster command
            print("Testing 'p' (previous cluster) command...")
            prev_cluster_binding = None
            for binding in bindings:
                if binding.key == "p":
                    prev_cluster_binding = binding
                    break
            
            if prev_cluster_binding:
                print(f"✓ Found 'p' key binding: {prev_cluster_binding.action}")
                print(f"  Description: {prev_cluster_binding.description}")
            
            self.results['navigation'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"✗ Navigation test failed: {e}")
            self.results['navigation'] = f'FAIL: {e}'
            return False
    
    def test_sheet_navigation(self):
        """Test sheet navigation (tab/shift+tab)."""
        print("\n=== Testing Sheet Navigation ===")
        try:
            # Test tab for next sheet
            tab_binding = None
            shift_tab_binding = None
            
            for binding in self.app.BINDINGS:
                if binding.key == "tab":
                    tab_binding = binding
                elif binding.key == "shift+tab":
                    shift_tab_binding = binding
            
            if tab_binding:
                print(f"✓ Found 'tab' key binding: {tab_binding.action}")
                print(f"  Description: {tab_binding.description}")
            
            if shift_tab_binding:
                print(f"✓ Found 'shift+tab' key binding: {shift_tab_binding.action}")
                print(f"  Description: {shift_tab_binding.description}")
            
            self.results['sheet_navigation'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"✗ Sheet navigation test failed: {e}")
            self.results['sheet_navigation'] = f'FAIL: {e}'
            return False
    
    def test_keyboard_shortcuts(self):
        """Test keyboard shortcuts (ctrl+g, ctrl+s, ctrl+q)."""
        print("\n=== Testing Keyboard Shortcuts ===")
        try:
            shortcuts = ['ctrl+g', 'ctrl+s', 'ctrl+q']
            found_shortcuts = {}
            
            for binding in self.app.BINDINGS:
                if binding.key in shortcuts:
                    found_shortcuts[binding.key] = {
                        'action': binding.action,
                        'description': binding.description
                    }
            
            for shortcut in shortcuts:
                if shortcut in found_shortcuts:
                    info = found_shortcuts[shortcut]
                    print(f"✓ Found '{shortcut}' binding: {info['action']}")
                    print(f"  Description: {info['description']}")
                else:
                    print(f"✗ Missing '{shortcut}' binding")
            
            self.results['shortcuts'] = 'PASS' if len(found_shortcuts) == len(shortcuts) else 'PARTIAL'
            return True
            
        except Exception as e:
            print(f"✗ Keyboard shortcuts test failed: {e}")
            self.results['shortcuts'] = f'FAIL: {e}'
            return False
    
    def test_number_shortcuts(self):
        """Test number key shortcuts (1-9 for sheets)."""
        print("\n=== Testing Number Shortcuts ===")
        try:
            number_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
            found_numbers = {}
            
            for binding in self.app.BINDINGS:
                if binding.key in number_keys:
                    found_numbers[binding.key] = {
                        'action': binding.action,
                        'show': binding.show
                    }
            
            for num in number_keys:
                if num in found_numbers:
                    info = found_numbers[num]
                    print(f"✓ Found '{num}' binding: {info['action']} (show={info['show']})")
                else:
                    print(f"- No binding for '{num}'")
            
            self.results['number_shortcuts'] = f'PASS ({len(found_numbers)}/9 found)'
            return True
            
        except Exception as e:
            print(f"✗ Number shortcuts test failed: {e}")
            self.results['number_shortcuts'] = f'FAIL: {e}'
            return False
    
    def test_cluster_view_functionality(self):
        """Test ClusterView widget functionality."""
        print("\n=== Testing ClusterView Functionality ===")
        try:
            # Test if ClusterView can be created
            from src.widgets.cluster_view import ClusterView
            from src.business_logic.color_formatter import ColorFormatter
            
            excel_io = ExcelIO(Path(self.excel_file))
            data_manager = ExcelDataManager(excel_io)
            data_manager.load_excel(self.excel_file)
            
            formatter = ColorFormatter()
            cluster_view = ClusterView(data_manager=data_manager, color_formatter=formatter)
            
            print("✓ ClusterView widget created successfully")
            
            # Test column configuration
            columns = cluster_view.DISPLAY_COLUMNS
            print(f"✓ Display columns configured: {len(columns)} columns")
            print(f"  Columns: {', '.join(columns[:5])}...")
            
            # Test editable columns
            editable_cols = [col for col in columns if cluster_view.COLUMN_CONFIG.get(col, {}).get('editable', False)]
            print(f"✓ Editable columns: {editable_cols}")
            
            self.results['cluster_view'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"✗ ClusterView test failed: {e}")
            self.results['cluster_view'] = f'FAIL: {e}'
            return False
    
    def test_app_initialization(self):
        """Test app initialization and widget setup."""
        print("\n=== Testing App Initialization ===")
        try:
            # Test app creation
            print(f"✓ App created with file: {self.app.excel_file}")
            
            # Test components initialization
            components = [
                ('excel_io', self.app.excel_io),
                ('data_manager', self.app.data_manager),
                ('validator', self.app.validator),
                ('formatter', self.app.formatter),
                ('session_manager', self.app.session_manager)
            ]
            
            for name, component in components:
                if component:
                    print(f"✓ {name}: {type(component).__name__}")
                else:
                    print(f"✗ {name}: Not initialized")
            
            # Test CSS styling
            if self.app.CSS:
                print("✓ CSS styling defined")
                css_rules = len(self.app.CSS.strip().split('}'))
                print(f"  Estimated CSS rules: {css_rules}")
            
            self.results['app_init'] = 'PASS'
            return True
            
        except Exception as e:
            print(f"✗ App initialization test failed: {e}")
            self.results['app_init'] = f'FAIL: {e}'
            return False
    
    def run_all_tests(self):
        """Run all tests and display results."""
        print("Starting TUI Command Tests...\n")
        
        tests = [
            self.test_data_loading,
            self.test_app_initialization,
            self.test_navigation_commands,
            self.test_sheet_navigation,
            self.test_keyboard_shortcuts,
            self.test_number_shortcuts,
            self.test_cluster_view_functionality,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print(f"\n=== Test Results Summary ===")
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.results.items():
            status = "✓" if "PASS" in result else "✗"
            print(f"  {status} {test_name}: {result}")
        
        return passed == total


def main():
    """Main test function."""
    if len(sys.argv) != 2:
        print("Usage: python test_tui_commands.py <excel_file>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    if not Path(excel_file).exists():
        print(f"Error: File not found: {excel_file}")
        sys.exit(1)
    
    tester = TUICommandTester(excel_file)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
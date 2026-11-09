"""
Comprehensive test runner for all Confluence MCP tests with coverage reporting.
This file runs all test files and provides detailed coverage analysis.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_tests_with_coverage(test_files=None, verbose=False, html_report=False):
    """Run all Confluence tests with coverage reporting."""
    
    # Default test files if none specified
    if test_files is None:
        test_files = [
            "test_server.py",
            "test_service.py", 
            "test_tools.py"
        ]
    
    # Ensure we are in the correct directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    print("=" * 80)
    print("CONFLUENCE MCP COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Test Directory: {test_dir}")
    print(f"Project Root: {project_root}")
    print(f"Test Files: {', '.join(test_files)}")
    print("=" * 80)
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=src.confluence",
        "--cov-report=term-missing",
        "--cov-report=term:skip-covered",
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ]
    
    if verbose:
        cmd.append("-v")
    
    if html_report:
        cmd.extend(["--cov-report=html:htmlcov"])
    
    # Add test files
    cmd.extend(test_files)
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 80)
    
    try:
        # Run the tests
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        print("=" * 80)
        if result.returncode == 0:
            print(" ALL TESTS PASSED SUCCESSFULLY!")
        else:
            print(" SOME TESTS FAILED!")
        print("=" * 80)
        
        if html_report:
            html_path = test_dir / "htmlcov" / "index.html"
            if html_path.exists():
                print(f" HTML Coverage Report: {html_path}")
                print(f"   Open in browser: file://{html_path.absolute()}")
        
        return result.returncode
        
    except Exception as e:
        print(f" Error running tests: {e}")
        return 1

def run_individual_test_suites():
    """Run each test suite individually with detailed reporting."""
    
    test_suites = [
        ("Server Tests", "test_server.py"),
        ("Service Tests", "test_service.py"),
        ("Tools Tests", "test_tools.py")
    ]
    
    print("=" * 80)
    print("RUNNING INDIVIDUAL TEST SUITES")
    print("=" * 80)
    
    results = {}
    
    for suite_name, test_file in test_suites:
        print(f"\n Running {suite_name} ({test_file})")
        print("-" * 60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=src.confluence",
            "--cov-report=term-missing",
            "--tb=short",
            "-v",
            test_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            results[suite_name] = result.returncode == 0
            
            if result.returncode == 0:
                print(f" {suite_name} PASSED")
            else:
                print(f" {suite_name} FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                
        except Exception as e:
            print(f" Error running {suite_name}: {e}")
            results[suite_name] = False
    
    print("\n" + "=" * 80)
    print("INDIVIDUAL TEST SUITE RESULTS")
    print("=" * 80)
    
    for suite_name, passed in results.items():
        status = " PASSED" if passed else " FAILED"
        print(f"{suite_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall Result: {' ALL SUITES PASSED' if all_passed else ' SOME SUITES FAILED'}")
    
    return 0 if all_passed else 1

def main():
    """Main entry point for the test runner."""
    
    parser = argparse.ArgumentParser(
        description="Comprehensive Confluence MCP Test Runner with Coverage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run all tests with basic coverage
  python run_all_tests.py --verbose          # Run with verbose output
  python run_all_tests.py --html             # Generate HTML coverage report
  python run_all_tests.py --individual       # Run each test suite individually
  python run_all_tests.py --files test_server.py test_service.py  # Run specific files
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose test output"
    )
    
    parser.add_argument(
        "--html",
        action="store_true", 
        help="Generate HTML coverage report"
    )
    
    parser.add_argument(
        "--individual",
        action="store_true",
        help="Run each test suite individually with detailed reporting"
    )
    
    parser.add_argument(
        "--files",
        nargs="+",
        help="Specific test files to run"
    )
    
    args = parser.parse_args()
    
    # Check if required packages are installed
    try:
        import coverage
        import pytest
    except ImportError as e:
        print(f" Missing required package: {e}")
        print("Please install required packages:")
        print("  pip install pytest pytest-cov coverage")
        return 1
    
    # Run appropriate test mode
    if args.individual:
        return run_individual_test_suites()
    else:
        return run_tests_with_coverage(
            test_files=args.files,
            verbose=args.verbose,
            html_report=args.html
        )

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

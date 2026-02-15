#!/usr/bin/env python3
"""
Test runner for comprehensive File Organizer testing.
Runs all test categories and generates a report.
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_tests(category=None, verbose=True):
    """Run pytest with optional category filter."""
    cmd = [sys.executable, "-m", "pytest", "tests_new", "-v"]
    
    if category:
        cmd.extend(["-m", category])
    
    cmd.extend([
        "--tb=short",
        "--cov=src/core" if category != "ui" else "",
        "--cov-report=term-missing" if category != "ui" else "",
        "-x"  # Stop on first failure
    ])
    
    # Remove empty strings
    cmd = [c for c in cmd if c]
    
    print(f"\n{'='*60}")
    print(f"Running tests: {category or 'ALL'}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def generate_report():
    """Generate comprehensive test report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "categories": {}
    }
    
    categories = ["unit", "integration", "ui", "security", "edge_case"]
    
    for category in categories:
        cmd = [sys.executable, "-m", "pytest", "tests_new", "-m", category, "--collect-only", "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Count tests
        test_count = result.stdout.count("::")
        report["categories"][category] = {
            "test_count": test_count
        }
    
    return report


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run File Organizer tests")
    parser.add_argument(
        "category",
        nargs="?",
        choices=["unit", "integration", "ui", "security", "edge_case", "all"],
        default="all",
        help="Test category to run"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate test report"
    )
    
    args = parser.parse_args()
    
    if args.report:
        report = generate_report()
        print("\n" + "="*60)
        print("TEST REPORT")
        print("="*60)
        print(json.dumps(report, indent=2))
        return 0
    
    category = None if args.category == "all" else args.category
    return run_tests(category)


if __name__ == "__main__":
    sys.exit(main())

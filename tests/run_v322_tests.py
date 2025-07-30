#!/usr/bin/env python3
"""
Test runner for v3.2.2 hotfix validation
Runs all spot-check tests to verify functionality
"""

import subprocess
import sys
import os

def run_test(test_file, description):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print('='*60)
    
    try:
        result = subprocess.run([
            sys.executable, test_file
        ], check=True, capture_output=True, text=True)
        
        print("✅ PASSED")
        if result.stdout:
            print("Output:", result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        if e.stdout:
            print("STDOUT:", e.stdout.strip())
        if e.stderr:
            print("STDERR:", e.stderr.strip())
        return False

def main():
    """Run all v3.2.2 hotfix tests"""
    print("🧪 v3.2.2 Hotfix Test Suite")
    print("Testing routing, QA reporting, and summary enhancements")
    
    # Set up environment
    os.environ["PYTHONPATH"] = "."
    os.environ["AUTO_APPROVE"] = "1"
    os.environ["BUDGET_EUR"] = "8"
    
    tests = [
        ("tests/test_routing.py", "Routing System Tests"),
        ("tests/test_qa_report.py", "QA Reporting Tests"), 
        ("tests/test_v322_summary.py", "v3.2.2 Summary Enhancement Tests")
    ]
    
    passed = 0
    total = len(tests)
    
    for test_file, description in tests:
        if run_test(test_file, description):
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! v3.2.2 hotfix is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

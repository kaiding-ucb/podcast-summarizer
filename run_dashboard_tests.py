#!/usr/bin/env python3
"""
Comprehensive test runner for dashboard metadata verification.
This script will:
1. Set up test data in the database
2. Check if the FastAPI app is running (or provide instructions to start it)
3. Run Playwright tests to verify dashboard metadata display
4. Generate a test report
"""

import subprocess
import sys
import time
import requests
import os
from setup_test_data import create_test_data

def check_app_running(url="http://127.0.0.1:8000", timeout=5):
    """Check if the FastAPI app is running"""
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False

def main():
    print("🚀 Dashboard Metadata Test Runner")
    print("=" * 50)
    
    # Step 1: Set up test data
    print("\n📊 Step 1: Setting up test data...")
    if create_test_data():
        print("✅ Test data created successfully")
    else:
        print("❌ Failed to create test data")
        return False
    
    # Step 2: Check if app is running
    print("\n🌐 Step 2: Checking if FastAPI app is running...")
    if check_app_running():
        print("✅ FastAPI app is running on http://127.0.0.1:8000")
    else:
        print("❌ FastAPI app is not running")
        print("\n📋 To start the app, run:")
        print("   cd /Users/kai/Documents/wt-frontend-ui")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
        print("\nThen run this script again.")
        return False
    
    # Step 3: Run Playwright tests
    print("\n🎭 Step 3: Running Playwright tests...")
    try:
        # Run tests with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_dashboard_metadata.py", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=True, text=True, cwd="/Users/kai/Documents/wt-frontend-ui")
        
        print("Test Output:")
        print(result.stdout)
        
        if result.stderr:
            print("Test Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ All dashboard metadata tests passed!")
            print("\n📋 Test Summary:")
            print("   ✓ Dashboard page loads successfully")
            print("   ✓ API returns proper test data")
            print("   ✓ Channel names display correctly (not 'Unknown')")
            print("   ✓ Publish dates display in proper format (not 'Unknown')")
            print("   ✓ Video durations display in MM:SS format (not 'Unknown')")
            print("   ✓ All video cards have complete metadata")
            print("   ✓ Specific test videos are visible with correct formatting")
            return True
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Dashboard metadata verification completed successfully!")
        print("\nThe dashboard correctly displays:")
        print("   • Channel names instead of 'Unknown'")
        print("   • Publish dates in proper format instead of 'Unknown'") 
        print("   • Video durations in MM:SS format instead of 'Unknown'")
    else:
        print("❌ Dashboard metadata verification failed")
        print("Please check the output above for details.")
    
    sys.exit(0 if success else 1)
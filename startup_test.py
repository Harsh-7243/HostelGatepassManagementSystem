#!/usr/bin/env python3
"""
Startup test script for Azure deployment verification
"""
import os
import sys

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import flask
        import flask_login
        import werkzeug
        import sqlite3
        print("✅ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test that the Flask app can be created"""
    try:
        from app import app
        print("✅ Flask app created successfully")
        print(f"✅ App name: {app.name}")
        print(f"✅ Secret key configured: {'Yes' if app.secret_key else 'No'}")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def test_database():
    """Test database initialization"""
    try:
        from db_init import initialize_db
        initialize_db()
        print("✅ Database initialization successful")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Azure deployment readiness tests...\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Flask App Creation", test_app_creation),
        ("Database Initialization", test_database)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for Azure deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

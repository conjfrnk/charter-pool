#!/usr/bin/env python3
"""
Quick test to verify error handling changes work correctly
Run this before deploying to ensure changes are functional
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_import():
    """Test that config loads with error handling"""
    print("Testing config import...")
    try:
        from config import Config
        assert hasattr(Config, 'SECRET_KEY'), "SECRET_KEY not found"
        assert hasattr(Config, 'SQLALCHEMY_DATABASE_URI'), "Database URI not found"
        print("✓ Config loads successfully")
        return True
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False

def test_auth_import():
    """Test that auth module imports correctly"""
    print("Testing auth import...")
    try:
        from auth import login_manager, load_user
        print("✓ Auth module imports successfully")
        return True
    except Exception as e:
        print(f"✗ Auth import failed: {e}")
        return False

def test_models_import():
    """Test that models import correctly"""
    print("Testing models import...")
    try:
        from models import db, User, Admin, Game
        print("✓ Models import successfully")
        return True
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False

def test_app_has_health_endpoint():
    """Test that health endpoint exists"""
    print("Testing health endpoint...")
    try:
        # Import without initializing database
        import app as app_module
        
        # Check if health route exists
        rules = [str(rule) for rule in app_module.app.url_map.iter_rules()]
        
        if '/health' in rules:
            print("✓ Health endpoint exists")
            return True
        else:
            print("✗ Health endpoint not found in routes")
            return False
    except Exception as e:
        print(f"✗ Health endpoint check failed: {e}")
        return False

def test_error_handlers_exist():
    """Test that error handlers are present"""
    print("Testing error handlers...")
    try:
        import app as app_module
        
        # Check if error handlers are registered
        handlers = app_module.app.error_handler_spec
        
        if handlers and None in handlers and 404 in handlers[None]:
            print("✓ 404 error handler exists")
        else:
            print("✗ 404 error handler missing")
            return False
            
        if handlers and None in handlers and 500 in handlers[None]:
            print("✓ 500 error handler exists")
        else:
            print("✗ 500 error handler missing")
            return False
            
        return True
    except Exception as e:
        print(f"✗ Error handler check failed: {e}")
        return False

def test_admin_login_route():
    """Test that admin login route exists"""
    print("Testing admin login route...")
    try:
        import app as app_module
        
        rules = [str(rule) for rule in app_module.app.url_map.iter_rules()]
        
        if '/admin/login' in rules:
            print("✓ Admin login route exists")
            return True
        else:
            print("✗ Admin login route not found")
            return False
    except Exception as e:
        print(f"✗ Admin login route check failed: {e}")
        return False

def test_context_processors():
    """Test that context processors are registered"""
    print("Testing context processors...")
    try:
        import app as app_module
        
        # Check if context processors exist
        processors = app_module.app.template_context_processors[None]
        
        processor_names = [p.__name__ for p in processors]
        
        if 'inject_version' in processor_names:
            print("✓ inject_version context processor exists")
        else:
            print("✗ inject_version context processor missing")
            return False
            
        if 'inject_user' in processor_names:
            print("✓ inject_user context processor exists")
        else:
            print("✗ inject_user context processor missing")
            return False
            
        return True
    except Exception as e:
        print(f"✗ Context processor check failed: {e}")
        return False

def main():
    print("=" * 60)
    print("TESTING OPENBSD FIX CHANGES")
    print("=" * 60)
    print()
    
    tests = [
        test_config_import,
        test_auth_import,
        test_models_import,
        test_app_has_health_endpoint,
        test_error_handlers_exist,
        test_admin_login_route,
        test_context_processors,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
            print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED - Ready to deploy!")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME TESTS FAILED - Fix issues before deploying")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())


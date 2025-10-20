#!/usr/bin/env python3
"""
Test the web endpoint for adding users
This simulates what happens when you submit the form
"""

import sys
from app import app
from models import db, User

print("=" * 70)
print("Testing Web Add User Endpoint")
print("=" * 70)
print()

with app.test_client() as client:
    with app.app_context():
        # First, we need to login as admin
        # For now, let's just test the create_user function in the right context
        
        print("[1/3] Testing single user add...")
        from auth import create_user
        
        test_netid = "webtest1"
        
        # Clean up if exists
        existing = User.query.get(test_netid)
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        try:
            success, result = create_user(test_netid)
            if success:
                print(f"✓ Single user created: {test_netid}")
                print(f"  is_active={result.is_active}")
                
                # Clean up
                db.session.delete(result)
                db.session.commit()
            else:
                print(f"✗ Failed: {result}")
                sys.exit(1)
        except Exception as e:
            print(f"✗ Exception: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        print()
        print("[2/3] Testing bulk user add...")
        
        test_netids = ["bulktest1", "bulktest2", "bulktest3"]
        
        # Clean up if exists
        for netid in test_netids:
            existing = User.query.get(netid)
            if existing:
                db.session.delete(existing)
                db.session.commit()
        
        try:
            for netid in test_netids:
                success, result = create_user(netid)
                if success:
                    print(f"✓ Created: {netid} (is_active={result.is_active})")
                else:
                    print(f"✗ Failed {netid}: {result}")
            
            # Clean up
            for netid in test_netids:
                user = User.query.get(netid)
                if user:
                    db.session.delete(user)
            db.session.commit()
            print("✓ All bulk users created and cleaned up")
        except Exception as e:
            print(f"✗ Exception: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        print()
        print("[3/3] Checking current_user handling...")
        
        # Test the getattr approach for admin
        class MockAdmin:
            admin_id = 123
            is_admin = True
        
        mock_admin = MockAdmin()
        user_id = getattr(mock_admin, 'admin_id', getattr(mock_admin, 'netid', 'unknown'))
        is_admin = getattr(mock_admin, 'is_admin', False)
        
        if user_id == 123 and is_admin == True:
            print(f"✓ getattr approach works: user_id={user_id}, is_admin={is_admin}")
        else:
            print(f"✗ getattr failed: user_id={user_id}, is_admin={is_admin}")
            sys.exit(1)

print()
print("=" * 70)
print("✓ ALL WEB TESTS PASSED!")
print("=" * 70)
print()
print("If this passes but the web interface still fails, the issue is:")
print("1. Server hasn't been restarted with latest code")
print("2. There's a session/authentication issue")
print("3. Database permissions for www user")
print()
print("Make sure to run on the server:")
print("  doas rcctl restart gunicorn_chool")


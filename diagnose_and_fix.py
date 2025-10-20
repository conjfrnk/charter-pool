#!/usr/bin/env python3
"""
Diagnostic and fix script for Charter Pool database issues
This script checks and fixes common database problems
"""

import sys
import os

# Change to the app directory
os.chdir('/var/www/htdocs/www.chool.app')
sys.path.insert(0, '/var/www/htdocs/www.chool.app')

print("=" * 70)
print("Charter Pool - Database Diagnostics")
print("=" * 70)
print()

# Test 1: Can we import the app?
print("[1/5] Testing imports...")
try:
    from app import app
    from models import db, User
    print("✓ Successfully imported app and models")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Can we connect to the database?
print("\n[2/5] Testing database connection...")
try:
    with app.app_context():
        db.engine.connect()
        print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check if users table exists
print("\n[3/5] Checking users table...")
try:
    with app.app_context():
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """))
        exists = result.fetchone()[0]
        if exists:
            print("✓ Users table exists")
        else:
            print("✗ Users table does not exist")
            print("  Run: python init_db.py")
            sys.exit(1)
except Exception as e:
    print(f"✗ Error checking table: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check if is_active column exists
print("\n[4/5] Checking is_active column...")
try:
    with app.app_context():
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='is_active';
        """))
        
        if result.fetchone():
            print("✓ is_active column exists")
        else:
            print("✗ is_active column is MISSING - this is likely the problem!")
            print()
            print("Attempting to add is_active column...")
            
            try:
                # Add the column
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT FALSE;
                """))
                db.session.commit()
                print("✓ Successfully added is_active column")
                
                # Update existing users
                print("\nUpdating existing users...")
                db.session.execute(text("""
                    UPDATE users 
                    SET is_active = TRUE 
                    WHERE first_name IS NOT NULL AND last_name IS NOT NULL;
                """))
                db.session.commit()
                
                count_active = db.session.execute(text("SELECT COUNT(*) FROM users WHERE is_active = TRUE")).fetchone()[0]
                count_inactive = db.session.execute(text("SELECT COUNT(*) FROM users WHERE is_active = FALSE")).fetchone()[0]
                
                print(f"✓ Updated users: {count_active} active, {count_inactive} inactive")
                
            except Exception as e:
                print(f"✗ Failed to add column: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
                
except Exception as e:
    print(f"✗ Error checking column: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Try to create a test user
print("\n[5/5] Testing user creation...")
try:
    with app.app_context():
        from auth import create_user
        
        test_netid = "test_diagnostic_user"
        
        # Clean up if exists
        existing = User.query.get(test_netid)
        if existing:
            db.session.delete(existing)
            db.session.commit()
            print(f"  (Cleaned up existing test user)")
        
        # Try to create
        success, result = create_user(test_netid)
        
        if success:
            print(f"✓ Successfully created test user: {test_netid}")
            
            # Clean up
            db.session.delete(result)
            db.session.commit()
            print(f"✓ Cleaned up test user")
        else:
            print(f"✗ Failed to create test user: {result}")
            sys.exit(1)
            
except Exception as e:
    print(f"✗ Error testing user creation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ ALL DIAGNOSTICS PASSED!")
print("=" * 70)
print()
print("The database should now be working correctly.")
print("Restart the application:")
print("  doas rcctl restart gunicorn_chool")
print()


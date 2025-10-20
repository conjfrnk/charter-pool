#!/bin/sh
# Quick test of the user creation fix

echo "Testing user creation with fixed code..."
cd /var/www/htdocs/www.chool.app

python3 << 'EOF'
from app import app
from auth import create_user
from models import db, User

with app.app_context():
    test_netid = "quicktest123"
    
    # Clean up if exists
    existing = User.query.get(test_netid)
    if existing:
        db.session.delete(existing)
        db.session.commit()
    
    print("Creating test user (no names)...")
    success, result = create_user(test_netid)
    
    if success:
        print(f"✓ Success! User created with is_active={result.is_active}")
        
        if result.is_active == False:
            print("✓ PERFECT! is_active is correctly set to False")
        else:
            print(f"✗ Problem: is_active is {result.is_active}, should be False")
        
        # Clean up
        db.session.delete(result)
        db.session.commit()
        print("✓ Test user cleaned up")
    else:
        print(f"✗ Failed: {result}")
EOF

echo ""
echo "If you see '✓ PERFECT!' above, the fix is working!"
echo "Now restart the application:"
echo "  doas rcctl restart gunicorn_chool"


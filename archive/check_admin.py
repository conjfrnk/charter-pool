#!/usr/bin/env python3
"""Check and fix admin account"""
from app import app, db
from models import Admin
from config import Config

with app.app_context():
    print("Checking admin accounts...")
    admins = Admin.query.all()
    print(f"Found {len(admins)} admin(s)")
    
    for admin in admins:
        print(f"\nAdmin: {admin.username} (ID: {admin.id})")
        print(f"Password hash: {admin.password_hash[:80]}...")
        print(f"Hash method: {admin.password_hash.split('$')[0] if '$' in admin.password_hash else 'unknown'}")
    
    print("\n" + "="*50)
    print("Recreating default admin with pbkdf2:sha256...")
    
    # Delete all admins
    Admin.query.delete()
    db.session.commit()
    print("Deleted all existing admins")
    
    # Create new admin with working hash
    admin = Admin(username=Config.DEFAULT_ADMIN_USERNAME)
    admin.set_password(Config.DEFAULT_ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.commit()
    
    print(f"Created admin: {admin.username}")
    print(f"New password hash: {admin.password_hash[:80]}...")
    
    # Test the password
    print("\nTesting password check...")
    result = admin.check_password(Config.DEFAULT_ADMIN_PASSWORD)
    print(f"Password check result: {result}")
    
    if result:
        print("\n✓ Admin account is working correctly!")
    else:
        print("\n✗ Admin account password check failed!")


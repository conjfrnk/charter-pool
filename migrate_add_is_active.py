#!/usr/bin/env python3
"""
Migration script to add is_active column to users table.

This script adds the is_active column and sets it to:
- True for users who have both first_name and last_name
- False for users who don't have first_name or last_name (pending activation)

Usage:
    python migrate_add_is_active.py
"""

import sys
from app import app
from models import db, User
from sqlalchemy import text

def migrate_add_is_active():
    """Add is_active column and populate it based on existing data"""
    
    with app.app_context():
        print("Starting migration: add is_active column to users table...")
        
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='is_active';
            """))
            
            if result.fetchone():
                print("✓ Column 'is_active' already exists. Skipping column creation.")
            else:
                # Add the column with default False
                print("Adding 'is_active' column...")
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT FALSE;
                """))
                db.session.commit()
                print("✓ Column 'is_active' added successfully.")
            
            # Update existing users: set is_active=True if they have both first_name and last_name
            print("\nUpdating existing users...")
            users = User.query.all()
            
            active_count = 0
            inactive_count = 0
            
            for user in users:
                if user.first_name and user.last_name:
                    user.is_active = True
                    active_count += 1
                else:
                    user.is_active = False
                    inactive_count += 1
            
            db.session.commit()
            
            print(f"✓ Updated {len(users)} users:")
            print(f"  - {active_count} users set to active (have first_name and last_name)")
            print(f"  - {inactive_count} users set to inactive (missing first_name or last_name)")
            
            # Display inactive users
            if inactive_count > 0:
                print("\nInactive users (pending profile completion):")
                inactive_users = User.query.filter_by(is_active=False).all()
                for user in inactive_users:
                    print(f"  - {user.netid}")
            
            print("\n✓ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Restart your application server")
            print("2. Inactive users will need to log in and complete their profile")
            print("3. Only active users will appear on the leaderboard for regular users")
            print("4. Admins can see all users (active and inactive) in the admin panel")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("Charter Pool - Add is_active column migration")
    print("=" * 70)
    print()
    
    response = input("This will modify the database. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    print()
    migrate_add_is_active()


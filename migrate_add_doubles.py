"""
Database Migration: Add Doubles Support
Adds game_type, player3_netid, and player4_netid columns to games table
"""
import sys
from app import app
from models import db
from sqlalchemy import text

def migrate():
    """Add doubles support columns to games table"""
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='games' AND column_name IN ('game_type', 'player3_netid', 'player4_netid')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'game_type' in existing_columns and 'player3_netid' in existing_columns and 'player4_netid' in existing_columns:
                print("[INFO] All columns already exist. No migration needed.")
                return
            
            print("[INFO] Starting database migration to add doubles support...")
            
            # Add game_type column
            if 'game_type' not in existing_columns:
                print("[INFO] Adding game_type column...")
                db.session.execute(text("""
                    ALTER TABLE games 
                    ADD COLUMN game_type VARCHAR(20) DEFAULT 'singles' NOT NULL
                """))
                print("[SUCCESS] Added game_type column")
            else:
                print("[INFO] game_type column already exists")
            
            # Add player3_netid column
            if 'player3_netid' not in existing_columns:
                print("[INFO] Adding player3_netid column...")
                db.session.execute(text("""
                    ALTER TABLE games 
                    ADD COLUMN player3_netid VARCHAR(50) REFERENCES users(netid)
                """))
                print("[SUCCESS] Added player3_netid column")
            else:
                print("[INFO] player3_netid column already exists")
            
            # Add player4_netid column
            if 'player4_netid' not in existing_columns:
                print("[INFO] Adding player4_netid column...")
                db.session.execute(text("""
                    ALTER TABLE games 
                    ADD COLUMN player4_netid VARCHAR(50) REFERENCES users(netid)
                """))
                print("[SUCCESS] Added player4_netid column")
            else:
                print("[INFO] player4_netid column already exists")
            
            # Commit changes
            db.session.commit()
            print("[SUCCESS] Database migration completed successfully!")
            
            # Verify the migration
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name='games' AND column_name IN ('game_type', 'player3_netid', 'player4_netid')
                ORDER BY column_name
            """))
            print("\n[INFO] Verification - New columns:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Doubles Support")
    print("=" * 60)
    migrate()


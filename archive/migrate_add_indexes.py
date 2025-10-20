#!/usr/bin/env python3
"""
Migration script to add database indexes for performance improvements.
Run this script to add indexes without recreating the database.
"""

import sys
from sqlalchemy import create_engine, text
from config import Config

def add_indexes():
    """Add indexes to existing database tables"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    indexes_to_add = [
        # User table indexes
        "CREATE INDEX IF NOT EXISTS idx_users_elo_rating ON users(elo_rating);",
        "CREATE INDEX IF NOT EXISTS idx_users_archived ON users(archived);",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
        
        # Game table indexes
        "CREATE INDEX IF NOT EXISTS idx_games_player1_netid ON games(player1_netid);",
        "CREATE INDEX IF NOT EXISTS idx_games_player2_netid ON games(player2_netid);",
        "CREATE INDEX IF NOT EXISTS idx_games_player3_netid ON games(player3_netid);",
        "CREATE INDEX IF NOT EXISTS idx_games_player4_netid ON games(player4_netid);",
        "CREATE INDEX IF NOT EXISTS idx_games_timestamp ON games(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_games_tournament_id ON games(tournament_id);",
        
        # Tournament table indexes
        "CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments(status);",
        "CREATE INDEX IF NOT EXISTS idx_tournaments_created_at ON tournaments(created_at);",
    ]
    
    print("Adding database indexes for performance improvements...")
    
    with engine.connect() as conn:
        for idx, sql in enumerate(indexes_to_add, 1):
            try:
                print(f"[{idx}/{len(indexes_to_add)}] {sql.split('INDEX')[1].split('ON')[0].strip()}...", end=" ")
                conn.execute(text(sql))
                conn.commit()
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")
                # Continue with other indexes even if one fails
    
    print("\n✓ Database index migration completed!")
    print("Note: Indexes already existing are skipped automatically.")

if __name__ == "__main__":
    try:
        add_indexes()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


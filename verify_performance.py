#!/usr/bin/env python3
"""
Performance verification script for Charter Pool.
Tests database indexes, caching, and overall performance.

Usage:
    python3 verify_performance.py

This script will:
1. Verify database connection
2. Check for performance indexes
3. Test caching infrastructure
4. Measure query performance
5. Generate performance report
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config import Config

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(test_name, passed, details=""):
    """Print a test result"""
    status = "✓" if passed else "✗"
    color = "" if passed else ""
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def test_database_connection():
    """Test database connection"""
    print_header("1. Database Connection")
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print_result("Database connection", True, f"PostgreSQL connected")
            return True, engine
    except Exception as e:
        print_result("Database connection", False, f"Error: {e}")
        return False, None

def test_indexes(engine):
    """Test that performance indexes exist"""
    print_header("2. Performance Indexes")
    
    required_indexes = [
        'idx_users_active_elo',
        'idx_games_p1_timestamp',
        'idx_games_p2_timestamp',
        'idx_games_winner_timestamp',
        'idx_tournaments_status_created',
    ]
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE indexname LIKE 'idx_%'
            """))
            
            existing_indexes = [row[0] for row in result.fetchall()]
            
            all_present = True
            for idx in required_indexes:
                present = idx in existing_indexes
                print_result(idx, present)
                if not present:
                    all_present = False
            
            if all_present:
                print(f"\n✓ All {len(required_indexes)} required indexes present")
            else:
                print(f"\n⚠ Some indexes missing. Run: python3 migrate_add_composite_indexes.py")
            
            return all_present
    except Exception as e:
        print_result("Index check", False, f"Error: {e}")
        return False

def test_query_performance(engine):
    """Test query performance"""
    print_header("3. Query Performance")
    
    queries = [
        ("User count", "SELECT COUNT(*) FROM users"),
        ("Game count", "SELECT COUNT(*) FROM games"),
        ("Leaderboard (top 10)", """
            SELECT * FROM users 
            WHERE archived = false AND is_active = true 
            ORDER BY elo_rating DESC 
            LIMIT 10
        """),
        ("Recent games (10)", """
            SELECT * FROM games 
            ORDER BY timestamp DESC 
            LIMIT 10
        """),
    ]
    
    try:
        total_time = 0
        for name, query in queries:
            start = time.time()
            with engine.connect() as conn:
                conn.execute(text(query))
            elapsed = (time.time() - start) * 1000  # Convert to ms
            total_time += elapsed
            
            # Query should be < 100ms for good performance
            passed = elapsed < 100
            print_result(name, passed, f"{elapsed:.2f}ms")
        
        avg_time = total_time / len(queries)
        print(f"\n✓ Average query time: {avg_time:.2f}ms")
        return avg_time < 50  # Target: < 50ms average
        
    except Exception as e:
        print_result("Query performance", False, f"Error: {e}")
        return False

def test_cache_config():
    """Test cache configuration"""
    print_header("4. Cache Configuration")
    
    try:
        cache_type = getattr(Config, 'CACHE_TYPE', None)
        cache_timeout = getattr(Config, 'CACHE_DEFAULT_TIMEOUT', None)
        pool_size = Config.SQLALCHEMY_ENGINE_OPTIONS.get('pool_size', 0)
        
        print_result("Cache type configured", cache_type is not None, f"Type: {cache_type}")
        print_result("Cache timeout set", cache_timeout is not None, f"Timeout: {cache_timeout}s")
        print_result("Connection pool optimized", pool_size >= 20, f"Pool size: {pool_size}")
        
        return cache_type is not None and pool_size >= 20
    except Exception as e:
        print_result("Cache config", False, f"Error: {e}")
        return False

def test_assets():
    """Test that minified assets exist"""
    print_header("5. Optimized Assets")
    
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    assets = [
        ('style.min.css', 'Minified CSS'),
        ('main.min.js', 'Minified JavaScript'),
    ]
    
    all_present = True
    for filename, name in assets:
        path = os.path.join(static_dir, filename)
        exists = os.path.exists(path)
        
        if exists:
            size = os.path.getsize(path)
            print_result(name, True, f"{size:,} bytes")
        else:
            print_result(name, False, "Not found")
            all_present = False
    
    if not all_present:
        print("\n⚠ Missing assets. Run: python3 build_assets.py")
    
    return all_present

def generate_report(results):
    """Generate final performance report"""
    print_header("Performance Report")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    print(f"\nTests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All performance checks passed!")
        print("Your Charter Pool app is running at Porsche-level performance!")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠ Most checks passed, but some optimizations are missing.")
        print("Review the failures above and run the suggested commands.")
    else:
        print("\n✗ Several performance checks failed.")
        print("Please complete the optimization steps:")
        print("  1. python3 migrate_add_composite_indexes.py")
        print("  2. python3 build_assets.py")
        print("  3. Restart application")
    
    print("\n" + "=" * 70)
    
    return passed_tests == total_tests

def main():
    """Run all performance verification tests"""
    print("=" * 70)
    print("  CHARTER POOL PERFORMANCE VERIFICATION")
    print("  v2.0.0 'Porsche Edition'")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Database connection
    db_ok, engine = test_database_connection()
    results['database'] = db_ok
    
    if not db_ok:
        print("\n✗ Cannot proceed without database connection.")
        print("Please check your database configuration in config.py")
        return False
    
    # Test 2: Indexes
    results['indexes'] = test_indexes(engine)
    
    # Test 3: Query performance
    results['queries'] = test_query_performance(engine)
    
    # Test 4: Cache configuration
    results['cache'] = test_cache_config()
    
    # Test 5: Optimized assets
    results['assets'] = test_assets()
    
    # Generate final report
    return generate_report(results)

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


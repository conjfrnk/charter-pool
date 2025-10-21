"""
Advanced caching utilities for Charter Pool application.
Implements multi-level caching with smart invalidation.
"""

from functools import wraps
from flask import request
import hashlib
import json
import logging

# Cache tags for dependency tracking
CACHE_TAGS = {
    'users': ['leaderboard', 'user_stats', 'user_search'],
    'games': ['game_history', 'recent_games', 'user_stats', 'leaderboard'],
    'tournaments': ['tournament_list', 'tournament_detail'],
}

class CacheManager:
    """
    Smart cache manager with tag-based invalidation and warming.
    """
    
    def __init__(self, cache):
        self.cache = cache
        self.logger = logging.getLogger(__name__)
    
    def generate_cache_key(self, prefix, *args, **kwargs):
        """
        Generate a consistent cache key from arguments.
        """
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"cache:{prefix}:{key_hash}"
    
    def invalidate_by_tag(self, tag):
        """
        Invalidate all cache entries associated with a tag.
        """
        try:
            # SimpleCache doesn't support tag-based invalidation directly,
            # so we track keys in a separate cache entry
            tag_key = f"tag:{tag}"
            cached_keys = self.cache.get(tag_key) or []
            
            for key in cached_keys:
                self.cache.delete(key)
            
            self.cache.delete(tag_key)
            self.logger.info(f"Invalidated {len(cached_keys)} cache entries for tag '{tag}'")
        except Exception as e:
            self.logger.error(f"Failed to invalidate cache tag '{tag}': {e}")
    
    def invalidate_tags(self, tags):
        """
        Invalidate multiple cache tags.
        """
        for tag in tags:
            self.invalidate_by_tag(tag)
    
    def cache_with_tags(self, timeout=300, tags=None):
        """
        Decorator for caching function results with tag support.
        
        Usage:
            @cache_manager.cache_with_tags(timeout=300, tags=['users', 'games'])
            def expensive_function(arg1, arg2):
                return result
        """
        tags = tags or []
        
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Generate cache key
                cache_key = self.generate_cache_key(f.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = f(*args, **kwargs)
                
                # Store in cache
                self.cache.set(cache_key, result, timeout=timeout)
                
                # Track cache key in tags
                for tag in tags:
                    tag_key = f"tag:{tag}"
                    tag_keys = self.cache.get(tag_key) or []
                    if cache_key not in tag_keys:
                        tag_keys.append(cache_key)
                        self.cache.set(tag_key, tag_keys, timeout=timeout * 2)
                
                return result
            
            return decorated_function
        return decorator
    
    def warm_cache(self, app):
        """
        Warm critical caches on application startup.
        """
        with app.app_context():
            try:
                from models import User, Tournament
                
                # Warm leaderboard cache
                self.logger.info("Warming leaderboard cache...")
                User.query.filter_by(archived=False, is_active=True)\
                    .order_by(User.elo_rating.desc())\
                    .limit(10).all()
                
                # Warm tournament list cache
                self.logger.info("Warming tournament cache...")
                Tournament.query.filter_by(status='open').all()
                Tournament.query.filter_by(status='active').all()
                
                self.logger.info("Cache warming completed successfully")
            except Exception as e:
                self.logger.error(f"Failed to warm cache: {e}")


def make_cache_key(*args, **kwargs):
    """
    Generate a cache key for Flask-Caching.
    Includes request path and query parameters for request-level caching.
    """
    cache_dict = {
        'path': request.path,
        'args': request.args.to_dict(),
        'user': getattr(request, 'user_id', 'anonymous')
    }
    return hashlib.md5(json.dumps(cache_dict, sort_keys=True).encode()).hexdigest()


def invalidate_game_caches(cache_manager):
    """
    Invalidate all game-related caches.
    Call this after game creation, deletion, or ELO updates.
    """
    cache_manager.invalidate_tags(['games', 'user_stats', 'leaderboard'])


def invalidate_user_caches(cache_manager):
    """
    Invalidate all user-related caches.
    Call this after user creation, archival, or profile updates.
    """
    cache_manager.invalidate_tags(['users', 'leaderboard', 'user_search'])


def invalidate_tournament_caches(cache_manager):
    """
    Invalidate all tournament-related caches.
    Call this after tournament creation, activation, or match updates.
    """
    cache_manager.invalidate_tags(['tournaments'])


class QueryResultCache:
    """
    Cache for expensive query results with automatic invalidation.
    """
    
    def __init__(self, cache, timeout=300):
        self.cache = cache
        self.timeout = timeout
    
    def get_or_compute(self, key, compute_fn):
        """
        Get value from cache or compute it.
        """
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        
        result = compute_fn()
        self.cache.set(key, result, timeout=self.timeout)
        return result
    
    def invalidate(self, key):
        """
        Invalidate a specific cache entry.
        """
        self.cache.delete(key)


# Memoization decorator for pure functions
_memo_cache = {}

def memoize(f):
    """
    Simple memoization for pure functions (no Flask context needed).
    Use for calculations that don't depend on database state.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = (f.__name__, args, tuple(sorted(kwargs.items())))
        if key not in _memo_cache:
            _memo_cache[key] = f(*args, **kwargs)
        return _memo_cache[key]
    return decorated_function


def clear_memoization_cache():
    """
    Clear the global memoization cache.
    """
    global _memo_cache
    _memo_cache.clear()


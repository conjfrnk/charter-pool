"""
Performance monitoring and profiling utilities for Charter Pool.
Tracks request times, database queries, and cache performance.
"""

import time
import logging
from functools import wraps
from flask import g, request
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Performance metrics storage (in-memory, consider using Redis for production)
_performance_metrics = {
    'requests': [],
    'slow_queries': [],
    'cache_hits': 0,
    'cache_misses': 0,
}

# Configuration
SLOW_QUERY_THRESHOLD = 0.05  # 50ms
REQUEST_TIME_THRESHOLD = 1.0  # 1 second


class PerformanceMonitor:
    """
    Monitor application performance and collect metrics.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize performance monitoring for Flask app.
        """
        # Add before_request handler to start timing
        app.before_request(self._before_request)
        
        # Add after_request handler to record timing
        app.after_request(self._after_request)
        
        # Add SQLAlchemy query monitoring
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            
            # Log slow queries
            if total > SLOW_QUERY_THRESHOLD:
                logger.warning(f"Slow query ({total:.3f}s): {statement[:200]}")
                _performance_metrics['slow_queries'].append({
                    'duration': total,
                    'query': statement[:500],
                    'timestamp': time.time()
                })
                
                # Keep only last 100 slow queries
                if len(_performance_metrics['slow_queries']) > 100:
                    _performance_metrics['slow_queries'] = _performance_metrics['slow_queries'][-100:]
    
    def _before_request(self):
        """
        Called before each request to start timing.
        """
        g.start_time = time.time()
        g.query_count = 0
    
    def _after_request(self, response):
        """
        Called after each request to record metrics.
        """
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            
            # Log slow requests
            if elapsed > REQUEST_TIME_THRESHOLD:
                logger.warning(
                    f"Slow request ({elapsed:.3f}s): {request.method} {request.path}"
                )
            
            # Store request metrics
            metric = {
                'method': request.method,
                'path': request.path,
                'duration': elapsed,
                'timestamp': time.time(),
                'status_code': response.status_code
            }
            
            _performance_metrics['requests'].append(metric)
            
            # Keep only last 1000 requests
            if len(_performance_metrics['requests']) > 1000:
                _performance_metrics['requests'] = _performance_metrics['requests'][-1000:]
            
            # Add performance header (only in debug mode)
            if self.app.debug:
                response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
        
        return response
    
    def get_metrics(self):
        """
        Get current performance metrics.
        """
        requests = _performance_metrics['requests']
        
        if not requests:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'slow_requests': 0,
                'slow_queries': len(_performance_metrics['slow_queries']),
                'cache_hit_rate': 0
            }
        
        avg_time = sum(r['duration'] for r in requests) / len(requests)
        slow_requests = sum(1 for r in requests if r['duration'] > REQUEST_TIME_THRESHOLD)
        
        total_cache_ops = _performance_metrics['cache_hits'] + _performance_metrics['cache_misses']
        cache_hit_rate = (_performance_metrics['cache_hits'] / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        return {
            'total_requests': len(requests),
            'avg_response_time': round(avg_time, 3),
            'slow_requests': slow_requests,
            'slow_queries': len(_performance_metrics['slow_queries']),
            'cache_hit_rate': round(cache_hit_rate, 1)
        }
    
    def reset_metrics(self):
        """
        Reset all performance metrics.
        """
        _performance_metrics['requests'].clear()
        _performance_metrics['slow_queries'].clear()
        _performance_metrics['cache_hits'] = 0
        _performance_metrics['cache_misses'] = 0


def profile_function(f):
    """
    Decorator to profile function execution time.
    
    Usage:
        @profile_function
        def expensive_operation():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - start_time
        
        if elapsed > 0.1:  # Log if > 100ms
            logger.info(f"Function {f.__name__} took {elapsed:.3f}s")
        
        return result
    return decorated_function


def track_cache_hit():
    """
    Track a cache hit for metrics.
    """
    _performance_metrics['cache_hits'] += 1


def track_cache_miss():
    """
    Track a cache miss for metrics.
    """
    _performance_metrics['cache_misses'] += 1


class QueryCounter:
    """
    Context manager to count queries in a block of code.
    
    Usage:
        with QueryCounter() as counter:
            # ... database operations ...
            pass
        print(f"Queries executed: {counter.count}")
    """
    
    def __init__(self):
        self.count = 0
        self.queries = []
    
    def __enter__(self):
        event.listen(Engine, "before_cursor_execute", self._before_cursor_execute)
        return self
    
    def __exit__(self, type, value, traceback):
        event.remove(Engine, "before_cursor_execute", self._before_cursor_execute)
    
    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self.queries.append({
            'statement': statement[:200],
            'parameters': str(parameters)[:100] if parameters else None
        })


def analyze_query_performance(query):
    """
    Analyze SQLAlchemy query for potential performance issues.
    
    Returns:
        dict: Analysis results with warnings and suggestions
    """
    query_str = str(query)
    warnings = []
    suggestions = []
    
    # Check for missing joins (potential N+1)
    if 'SELECT' in query_str and 'JOIN' not in query_str:
        if query_str.count('SELECT') > 1:
            warnings.append("Potential N+1 query detected")
            suggestions.append("Consider using joinedload() or subqueryload()")
    
    # Check for missing limit
    if 'SELECT' in query_str and 'LIMIT' not in query_str:
        warnings.append("Query without LIMIT clause")
        suggestions.append("Add .limit() to prevent loading too much data")
    
    # Check for SELECT *
    if 'SELECT *' in query_str:
        warnings.append("Using SELECT * may load unnecessary columns")
        suggestions.append("Specify only needed columns with .with_entities()")
    
    return {
        'warnings': warnings,
        'suggestions': suggestions,
        'query': query_str[:500]
    }


# Export performance monitor instance
performance_monitor = PerformanceMonitor()


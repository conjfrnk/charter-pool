import os
from datetime import timedelta

class Config:
    # Secret key for session management
    # Priority: secrets.txt > environment variable > dev fallback
    secret_path = os.path.join(os.path.dirname(__file__), "secrets.txt")
    try:
        with open(secret_path, "r") as f:
            SECRET_KEY = f.read().strip()
            print(f"[INFO] Loaded SECRET_KEY from {secret_path}")
    except FileNotFoundError:
        print(f"[WARNING] secrets.txt not found at {secret_path}, using fallback")
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    except Exception as e:
        print(f"[ERROR] Failed to read secrets.txt: {e}")
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://charter_pool@localhost/charter_pool'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection pooling for performance (optimized for OpenBSD)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,          # Increased for better concurrency (was 10)
        'pool_recycle': 300,      # Recycle connections after 5 minutes for OpenBSD stability
        'pool_pre_ping': True,    # Verify connections before using
        'max_overflow': 30,       # Allow up to 30 additional connections (was 20)
        'pool_timeout': 30,       # Timeout after 30 seconds
        'echo_pool': False,       # Set to True for connection pool debugging
        'pool_use_lifo': True,    # Use LIFO for better connection reuse
    }
    
    # Flask-Compress configuration
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript',
        'text/javascript'
    ]
    COMPRESS_LEVEL = 6  # Compression level (1-9, 6 is default)
    COMPRESS_MIN_SIZE = 500  # Only compress responses larger than 500 bytes
    
    # Session configuration (no auto-logout)
    PERMANENT_SESSION_LIFETIME = timedelta(days=365)  # Sessions last 1 year (effectively permanent)
    # HTTPS enforcement toggle (set FORCE_HTTPS=true in environment for production)
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'false').lower() == 'true'
    SESSION_COOKIE_SECURE = FORCE_HTTPS  # Secure cookies in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Cache configuration (optimized for performance)
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default
    CACHE_THRESHOLD = 500        # Maximum number of items to cache
    CACHE_KEY_PREFIX = 'charter_pool_'
    
    # ELO rating configuration
    ELO_K_FACTOR = 32
    ELO_DEFAULT_RATING = 1200
    
    # Admin configuration
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin'

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()


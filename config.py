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
    
    # Session configuration (no auto-logout)
    PERMANENT_SESSION_LIFETIME = timedelta(days=365)  # Sessions last 1 year (effectively permanent)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ELO rating configuration
    ELO_K_FACTOR = 32
    ELO_DEFAULT_RATING = 1200
    
    # Admin configuration
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin'


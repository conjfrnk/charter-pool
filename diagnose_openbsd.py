#!/usr/bin/env python3
"""
Diagnostic script for OpenBSD deployment issues
Run this on the OpenBSD server to identify problems
"""

import os
import sys
import pwd
import grp

def check_file_permissions(filepath):
    """Check if file is readable"""
    try:
        if os.path.exists(filepath):
            stat_info = os.stat(filepath)
            mode = oct(stat_info.st_mode)[-3:]
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
            group = grp.getgrgid(stat_info.st_gid).gr_name
            readable = os.access(filepath, os.R_OK)
            return {
                "exists": True,
                "mode": mode,
                "owner": owner,
                "group": group,
                "readable": readable
            }
        else:
            return {"exists": False}
    except Exception as e:
        return {"exists": True, "error": str(e)}

def main():
    print("=" * 60)
    print("Charter Pool OpenBSD Diagnostic Tool")
    print("=" * 60)
    print()
    
    # Check current user
    print(f"Running as user: {os.getuid()} ({pwd.getpwuid(os.getuid()).pw_name})")
    print()
    
    # Get app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"App directory: {app_dir}")
    print()
    
    # Check critical files
    critical_files = [
        "app.py",
        "auth.py",
        "models.py",
        "config.py",
        "secrets.txt",
        "VERSION",
        "templates/admin/login.html",
        "templates/layout.html",
        "templates/login.html",
        "static/style.css"
    ]
    
    print("Checking file permissions:")
    print("-" * 60)
    for filename in critical_files:
        filepath = os.path.join(app_dir, filename)
        info = check_file_permissions(filepath)
        if info["exists"]:
            if "error" in info:
                print(f"✗ {filename}: ERROR - {info['error']}")
            else:
                status = "✓" if info["readable"] else "✗"
                print(f"{status} {filename}: {info['mode']} {info['owner']}:{info['group']} (readable: {info['readable']})")
        else:
            print(f"✗ {filename}: NOT FOUND")
    print()
    
    # Check directory permissions
    dirs = ["templates", "templates/admin", "static"]
    print("Checking directory permissions:")
    print("-" * 60)
    for dirname in dirs:
        dirpath = os.path.join(app_dir, dirname)
        info = check_file_permissions(dirpath)
        if info["exists"]:
            if "error" in info:
                print(f"✗ {dirname}: ERROR - {info['error']}")
            else:
                status = "✓" if info["readable"] else "✗"
                print(f"{status} {dirname}: {info['mode']} {info['owner']}:{info['group']} (readable: {info['readable']})")
        else:
            print(f"✗ {dirname}: NOT FOUND")
    print()
    
    # Test database connection
    print("Testing database connection:")
    print("-" * 60)
    try:
        from config import Config
        print(f"Database URI: {Config.SQLALCHEMY_DATABASE_URI}")
        
        # Try to connect
        from sqlalchemy import create_engine, text
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Test template loading
    print("Testing template loading:")
    print("-" * 60)
    try:
        from flask import Flask
        test_app = Flask(__name__)
        test_app.config.from_object('config.Config')
        with test_app.app_context():
            test_app.jinja_env.get_template("admin/login.html")
            print("✓ Template loading successful")
    except Exception as e:
        print(f"✗ Template loading failed: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Test imports
    print("Testing Python imports:")
    print("-" * 60)
    modules = ["flask", "flask_login", "flask_sqlalchemy", "flask_talisman", "werkzeug", "sqlalchemy", "psycopg2"]
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
    print()
    
    print("=" * 60)
    print("Diagnostic complete")
    print("=" * 60)

if __name__ == "__main__":
    main()


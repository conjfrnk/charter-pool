"""
Database initialization script
Run this to create all tables and initialize default admin account
"""
from app import app, db
from models import Admin
from config import Config

def init_database():
    """Initialize the database with tables and default admin"""
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Check if default admin exists
        admin = Admin.query.filter_by(username=Config.DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            print(f"Creating default admin account (username: {Config.DEFAULT_ADMIN_USERNAME})...")
            admin = Admin(username=Config.DEFAULT_ADMIN_USERNAME)
            admin.set_password(Config.DEFAULT_ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
            print("Default admin account created!")
        else:
            print("Default admin account already exists.")
        
        print("\nDatabase initialization complete!")
        print(f"Default admin credentials: {Config.DEFAULT_ADMIN_USERNAME} / {Config.DEFAULT_ADMIN_PASSWORD}")
        print("Please change the default admin password after first login.")

if __name__ == '__main__':
    init_database()


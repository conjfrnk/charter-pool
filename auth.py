"""
Authentication utilities for user and admin login
"""
import re
from flask_login import LoginManager, UserMixin
from models import User, Admin, db

login_manager = LoginManager()

class UserSession(UserMixin):
    """Wrapper class for Flask-Login user sessions"""
    def __init__(self, netid, is_admin=False):
        self.id = netid
        self.netid = netid
        self.is_admin = is_admin
    
    def get_id(self):
        return self.netid

class AdminSession(UserMixin):
    """Wrapper class for Flask-Login admin sessions"""
    def __init__(self, admin_id, username):
        self.id = f"admin_{admin_id}"
        self.admin_id = admin_id
        self.username = username
        self.is_admin = True
    
    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    """Load user from session"""
    try:
        if user_id.startswith('admin_'):
            # Admin session
            admin_id = int(user_id.replace('admin_', ''))
            admin = Admin.query.get(admin_id)
            if admin:
                return AdminSession(admin.id, admin.username)
        else:
            # Regular user session
            user = User.query.get(user_id)
            if user and not user.archived and user.is_active:
                return UserSession(user.netid)
    except Exception as e:
        import logging, traceback
        logging.error(f"Failed to load user from session (user_id={user_id}): {e}")
        traceback.print_exc()
    return None

def get_current_user():
    """Get the current User object (not UserSession)"""
    try:
        from flask_login import current_user
        if current_user.is_authenticated and not current_user.is_admin:
            user = User.query.get(current_user.netid)
            if user and not user.archived:
                return user
    except Exception as e:
        import logging
        logging.error(f"Failed to get current user: {e}")
    return None

def get_current_admin():
    """Get the current Admin object (not AdminSession)"""
    try:
        from flask_login import current_user
        if current_user.is_authenticated and current_user.is_admin:
            return Admin.query.get(current_user.admin_id)
    except Exception as e:
        import logging
        logging.error(f"Failed to get current admin: {e}")
    return None

def login_user_by_netid(netid):
    """
    Login a user by their netid
    Returns (success, user_or_error_message, needs_setup)
    """
    try:
        if not netid:
            return False, "NetID cannot be empty", False
        
        netid = netid.strip().lower()
        
        if not netid or len(netid) > 50:
            return False, "Invalid NetID format", False
        
        # Check if user exists
        user = User.query.get(netid)
    except Exception as e:
        print(f"[ERROR] Error in login_user_by_netid: {e}")
        return False, "An error occurred during login. Please try again.", False
    
    if user:
        if user.archived:
            return False, "This account has been archived. Please contact an administrator.", False
        
        # Check if user needs to complete profile
        if user.needs_profile_setup:
            return True, user, True  # Existing user but needs to complete profile
        
        # User exists and profile is complete, log them in
        from flask_login import login_user
        session_user = UserSession(user.netid)
        login_user(session_user, remember=True)
        return True, user, False
    else:
        # User not found - admin must create account first
        return False, "NetID not found. Please contact an administrator to create your account.", False

def login_admin(username, password):
    """
    Login an admin by username and password
    Returns (success, admin_or_error_message)
    """
    import logging
    logging.debug(f"login_admin called with username: {username}")
    admin = Admin.query.filter_by(username=username).first()
    logging.debug(f"Admin found: {admin is not None}")
    
    if admin:
        logging.debug(f"Admin username: {admin.username}, ID: {admin.id}")
        logging.debug(f"Checking password...")
        try:
            password_valid = admin.check_password(password)
            logging.debug(f"Password valid: {password_valid}")
        except Exception as e:
            logging.debug(f"Password check error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Password check error: {e}"
        
        if password_valid:
            from flask_login import login_user
            session_admin = AdminSession(admin.id, admin.username)
            login_user(session_admin, remember=True)
            return True, admin
    
    return False, "Invalid username or password"

def create_user(netid, first_name=None, last_name=None):
    """
    Create a new user account
    Can be called by admin (netid only) or by user completing profile (with names)
    Returns (success, user_or_error_message)
    """
    import logging
    logging.debug(f"create_user called with netid='{netid}', first_name='{first_name}', last_name='{last_name}'")
    
    netid = netid.strip().lower()
    logging.debug(f"Cleaned netid: '{netid}'")
    
    if not netid:
        logging.debug(f"NetID is empty after cleaning")
        return False, "NetID is required"
    
    # Check if user already exists
    logging.debug(f"Checking if user '{netid}' already exists...")
    try:
        existing_user = User.query.get(netid)
        logging.debug(f"Query result: existing_user={existing_user}")
    except Exception as e:
        logging.debug(f"Error checking existing user: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Database error checking user: {str(e)}"
    
    if existing_user:
        logging.debug(f"User '{netid}' already exists")
        return False, "A user with this NetID already exists"
    
    # Create new user (names can be None if added by admin)
    logging.debug(f"Creating new user object for '{netid}'")
    try:
        user = User(netid=netid)
        if first_name:
            user.first_name = first_name.strip()
        if last_name:
            user.last_name = last_name.strip()
        
        # Set is_active to True only if both names are provided, False otherwise
        if first_name and last_name:
            user.is_active = True
        else:
            user.is_active = False
        
        logging.debug(f"User object created: netid={user.netid}, is_active={user.is_active}")
        logging.debug(f"Adding user to database session...")
        db.session.add(user)
        
        logging.debug(f"Committing database session...")
        db.session.commit()
        
        logging.debug(f"User '{netid}' successfully created in database")
        return True, user
    except Exception as e:
        logging.debug(f"Error creating user '{netid}': {e}")
        import traceback
        traceback.print_exc()
        try:
            db.session.rollback()
            logging.debug(f"Database session rolled back")
        except Exception as rollback_error:
            print(f"[DEBUG] Error rolling back: {rollback_error}")
        return False, f"Database error creating user: {str(e)}"

def complete_user_profile(user, first_name, last_name):
    """
    Complete a user's profile with first and last name
    Returns (success, user_or_error_message)
    """
    first_name = first_name.strip()
    last_name = last_name.strip()
    
    if not all([first_name, last_name]):
        return False, "First and last name are required"
    
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = True  # Activate user when profile is completed
    db.session.commit()
    
    return True, user

def validate_admin_password(password):
    """
    Validate that an admin password meets security requirements
    Returns (valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, None


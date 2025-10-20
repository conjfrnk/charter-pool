"""
Authentication utilities for user and admin login
"""
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
            if user and not user.archived:
                return UserSession(user.netid)
    except Exception as e:
        print(f"[ERROR] Failed to load user from session (user_id={user_id}): {e}")
        import traceback
        traceback.print_exc()
    return None

def get_current_user():
    """Get the current User object (not UserSession)"""
    from flask_login import current_user
    if current_user.is_authenticated and not current_user.is_admin:
        return User.query.get(current_user.netid)
    return None

def get_current_admin():
    """Get the current Admin object (not AdminSession)"""
    from flask_login import current_user
    if current_user.is_authenticated and current_user.is_admin:
        return Admin.query.get(current_user.admin_id)
    return None

def login_user_by_netid(netid):
    """
    Login a user by their netid
    Returns (success, user_or_error_message, needs_setup)
    """
    netid = netid.strip().lower()
    
    if not netid:
        return False, "NetID cannot be empty", False
    
    # Check if user exists
    user = User.query.get(netid)
    
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
        # New user, needs to set up profile
        return True, netid, True

def login_admin(username, password):
    """
    Login an admin by username and password
    Returns (success, admin_or_error_message)
    """
    print(f"[DEBUG] login_admin called with username: {username}")
    admin = Admin.query.filter_by(username=username).first()
    print(f"[DEBUG] Admin found: {admin is not None}")
    
    if admin:
        print(f"[DEBUG] Admin username: {admin.username}, ID: {admin.id}")
        print(f"[DEBUG] Checking password...")
        try:
            password_valid = admin.check_password(password)
            print(f"[DEBUG] Password valid: {password_valid}")
        except Exception as e:
            print(f"[DEBUG] Password check error: {e}")
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
    netid = netid.strip().lower()
    
    if not netid:
        return False, "NetID is required"
    
    # Check if user already exists
    existing_user = User.query.get(netid)
    if existing_user:
        return False, "A user with this NetID already exists"
    
    # Create new user (names can be None if added by admin)
    user = User(netid=netid)
    if first_name:
        user.first_name = first_name.strip()
    if last_name:
        user.last_name = last_name.strip()
    
    db.session.add(user)
    db.session.commit()
    
    return True, user

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
    db.session.commit()
    
    return True, user


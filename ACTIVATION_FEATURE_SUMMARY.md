# User Activation Feature - Implementation Summary

## Overview
This feature adds user activation functionality to distinguish between users who have completed their profile setup and those who haven't. Only active users (those who have logged in and added their first name/last name) appear on the leaderboard for regular users. Inactive users are only visible to admins.

## Changes Made

### 1. Database Schema Changes
**File: `models.py`**
- Added `is_active` boolean column to the `User` model (defaults to `False`)
- Updated `needs_profile_setup` property to check `is_active` status

### 2. Authentication Updates
**File: `auth.py`**
- Modified `create_user()` to set `is_active=True` when both first_name and last_name are provided
- Modified `complete_user_profile()` to set `is_active=True` when profile is completed
- Updated `load_user()` to check `is_active` status when loading user sessions

### 3. Application Logic Updates
**File: `app.py`**

#### Leaderboard Route (`/leaderboard`)
- Regular users: Only see users with `is_active=True` and `archived=False`
- Admins: See all users (including inactive ones)

#### Dashboard Route (`/`)
- Updated leaderboard preview to show only active users
- User rank calculation only considers active users

#### User Search Route (`/users/search`)
- Only returns active users in search results

#### Game Reporting Routes (`/games/report`)
- Added validation to prevent reporting games with inactive users
- Users must complete their profile before playing games

#### Admin Dashboard Route (`/admin`)
- Updated statistics to show:
  - Total Users (all non-archived users)
  - Active Users (profile completed)
  - Inactive Users (pending activation)

#### Admin Users Route (`/admin/users`)
- Separates users into three categories:
  1. **Active Users**: Users who have completed their profile
  2. **Inactive Users**: Users added but not yet activated (pending profile completion)
  3. **Archived Users**: Previously archived users

### 4. Template Updates

#### `templates/leaderboard.html`
- Added "Inactive" badge for admins viewing inactive users
- Badge appears next to username when admin views inactive user

#### `templates/admin/users.html`
- Added separate section for inactive users
- Shows "Pending Activation" badge for inactive users
- Includes helpful descriptions for each user category

#### `templates/admin/dashboard.html`
- Added "Inactive Users" stat card to dashboard

### 5. Styling Updates
**File: `static/style.css`**
- Added `.badge-inactive` class for styling inactive user badges
- Badge has gray background (#6c757d) with white text

### 6. Database Migration
**File: `migrate_add_is_active.py`**
- Created migration script to add `is_active` column to existing databases
- Automatically sets `is_active=True` for users with both first_name and last_name
- Sets `is_active=False` for users missing names (pending activation)

## How It Works

### For New Users
1. Admin adds user by NetID only → User created with `is_active=False`
2. User logs in for first time → Redirected to profile setup
3. User completes profile (adds first/last name) → `is_active=True`
4. User now appears on leaderboard and can play games

### For Existing Users (after migration)
1. Run migration script: `python migrate_add_is_active.py`
2. Users with first_name AND last_name → `is_active=True`
3. Users missing first_name OR last_name → `is_active=False`

### Visibility Rules

#### Regular Users See:
- ✅ Active users on leaderboard
- ✅ Active users in search results
- ✅ Only can report games with active users
- ❌ Cannot see inactive users

#### Admins See:
- ✅ All users (active and inactive) on leaderboard
- ✅ "Inactive" badge next to inactive users
- ✅ Separate sections in user management for active/inactive users
- ✅ Statistics showing active vs inactive counts

## Installation Instructions

### Step 1: Apply the Code Changes
The code changes have already been made to the following files:
- `models.py`
- `auth.py`
- `app.py`
- `templates/leaderboard.html`
- `templates/admin/users.html`
- `templates/admin/dashboard.html`
- `static/style.css`

### Step 2: Run the Database Migration
```bash
cd /Users/connor/projects/charter-pool
python migrate_add_is_active.py
```

The migration script will:
1. Add the `is_active` column to the `users` table
2. Set `is_active=True` for users with complete profiles
3. Set `is_active=False` for users with incomplete profiles
4. Display a summary of changes

### Step 3: Restart the Application
After running the migration, restart your application server:
```bash
# If using gunicorn (production)
sudo rcctl restart gunicorn_chool

# If using Flask development server
# Just restart the server
```

### Step 4: Verify the Changes
1. **As Admin:**
   - Log in to admin panel
   - Check dashboard shows "Active Users" and "Inactive Users" counts
   - Visit "Manage Users" page
   - Verify users are separated into Active/Inactive sections

2. **As Regular User:**
   - Log in as regular user
   - Check leaderboard only shows active users
   - Try searching for users (should only see active ones)

## Behavior Summary

### Leaderboard Visibility
| User Type | Sees Active Users | Sees Inactive Users | Notes |
|-----------|------------------|---------------------|-------|
| Regular User | ✅ Yes | ❌ No | Only active users visible |
| Admin | ✅ Yes | ✅ Yes | All users visible, inactive labeled |

### Game Reporting
- ✅ Can report games with active users
- ❌ Cannot report games with inactive users
- Error message: "Cannot report games with inactive users. The user must complete their profile first."

### User Search
- Only returns active users in autocomplete
- Inactive users not searchable by regular users

### Admin Features
- Full visibility of all users
- Clear labeling of inactive users
- Separate management sections
- Statistics showing active vs inactive counts

## Rollback Instructions

If you need to rollback these changes:

1. **Revert code changes:**
   ```bash
   git checkout HEAD -- models.py auth.py app.py templates/ static/style.css
   ```

2. **Remove is_active column from database:**
   ```sql
   ALTER TABLE users DROP COLUMN is_active;
   ```

3. **Restart application**

## Testing Checklist

- [ ] Migration runs successfully
- [ ] Existing users with names show as active
- [ ] Existing users without names show as inactive
- [ ] Admin can see all users on leaderboard
- [ ] Regular users only see active users on leaderboard
- [ ] Inactive badge appears for admins
- [ ] User search only returns active users
- [ ] Cannot report games with inactive users
- [ ] Admin dashboard shows active/inactive counts
- [ ] Admin users page shows three sections correctly
- [ ] New user activation flow works (add user → login → complete profile → becomes active)

## Notes

- **Backward Compatibility:** The migration script handles existing databases gracefully
- **Data Integrity:** No user data is lost; only activation status is tracked
- **Performance:** Minimal impact; simple boolean column with index-friendly queries
- **Future Enhancement:** Could add email notifications to inactive users

## Support

If you encounter any issues:
1. Check the migration script output for errors
2. Verify database schema includes `is_active` column
3. Check application logs for authentication errors
4. Ensure all code files were updated correctly


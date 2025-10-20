import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_talisman import Talisman
from flask_login import login_required, logout_user, current_user
from sqlalchemy import or_, desc

from config import Config
from models import db, User, Admin, Game, Tournament, TournamentParticipant, TournamentMatch
from auth import login_manager, login_user_by_netid, login_admin, create_user, get_current_user, get_current_admin
from elo import update_ratings_after_game
from tournament_logic import activate_tournament, report_match_result

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

logging.basicConfig(level=logging.INFO)

csp = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'"],
}
Talisman(
    app,
    content_security_policy=csp,
    force_https=False,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
)

# ============================================================================
# USER AUTHENTICATION ROUTES
# ============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """User login page - NetID only, no password"""
    if current_user.is_authenticated and not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        netid = request.form.get("netid", "").strip().lower()
        success, result, needs_setup = login_user_by_netid(netid)
        
        if success:
            if needs_setup:
                # User needs to complete profile setup
                # result could be a User object (admin-created) or string (brand new)
                if isinstance(result, User):
                    return redirect(url_for('profile_setup', netid=result.netid))
                else:
                    return redirect(url_for('profile_setup', netid=result))
            else:
                # Existing user with complete profile, redirect to dashboard
                flash(f"Welcome back, {result.full_name}!", "success")
                return redirect(url_for('index'))
        else:
            flash(result, "error")
    
    return render_template("login.html")

@app.route("/profile/setup", methods=["GET", "POST"])
def profile_setup():
    """First-time user profile setup"""
    netid = request.args.get("netid") or request.form.get("netid")
    
    if not netid:
        return redirect(url_for('login'))
    
    # Check if user exists
    existing_user = User.query.get(netid)
    
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        
        if not first_name or not last_name:
            flash("First and last name are required.", "error")
            return render_template("profile_setup.html", netid=netid)
        
        if existing_user:
            # User exists (added by admin), complete their profile
            from auth import complete_user_profile
            success, result = complete_user_profile(existing_user, first_name, last_name)
        else:
            # Brand new user, create account
            success, result = create_user(netid, first_name, last_name)
        
        if success:
            # Log the user in
            login_user_by_netid(netid)
            flash(f"Welcome to Charter Pool, {result.full_name}!", "success")
            return redirect(url_for('index'))
        else:
            flash(result, "error")
    
    return render_template("profile_setup.html", netid=netid)

@app.route("/logout")
@login_required
def logout():
    """Log out current user or admin"""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ============================================================================
# USER DASHBOARD AND GAME ROUTES
# ============================================================================

@app.route("/")
@login_required
def index():
    """Main dashboard for logged-in users"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    user = get_current_user()
    recent_games = user.get_all_games()[:10]
    
    # Get leaderboard (top 10)
    leaderboard = User.query.filter_by(archived=False).order_by(desc(User.elo_rating)).limit(10).all()
    
    # Get user's rank
    user_rank = User.query.filter(User.elo_rating > user.elo_rating, User.archived == False).count() + 1
    
    # Get open tournaments
    open_tournaments = Tournament.query.filter_by(status='open').order_by(desc(Tournament.created_at)).all()
    
    # Get active tournaments user is in
    user_tournaments = Tournament.query.join(TournamentParticipant).filter(
        TournamentParticipant.user_netid == user.netid,
        Tournament.status.in_(['open', 'active'])
    ).all()
    
    return render_template(
        "index.html",
        user=user,
        recent_games=recent_games,
        leaderboard=leaderboard,
        user_rank=user_rank,
        open_tournaments=open_tournaments,
        user_tournaments=user_tournaments
    )

@app.route("/games/report", methods=["GET", "POST"])
@login_required
def report_game():
    """Report a game result"""
    if current_user.is_admin:
        flash("Admins cannot report games. Please log in with a user account.", "error")
        return redirect(url_for('admin_dashboard'))
    
    user = get_current_user()
    
    if request.method == "POST":
        opponent_netid = request.form.get("opponent_netid", "").strip().lower()
        winner_netid = request.form.get("winner_netid", "").strip().lower()
        
        # Validate opponent
        opponent = User.query.get(opponent_netid)
        if not opponent:
            flash("Opponent not found.", "error")
            return redirect(url_for('report_game'))
        
        if opponent.archived:
            flash("Cannot report games with archived users.", "error")
            return redirect(url_for('report_game'))
        
        if opponent_netid == user.netid:
            flash("You cannot play against yourself!", "error")
            return redirect(url_for('report_game'))
        
        # Validate winner
        if winner_netid not in [user.netid, opponent_netid]:
            flash("Winner must be one of the players.", "error")
            return redirect(url_for('report_game'))
        
        # Determine winner and loser
        if winner_netid == user.netid:
            winner = user
            loser = opponent
        else:
            winner = opponent
            loser = user
        
        # Update ELO ratings
        elo_change = update_ratings_after_game(winner, loser, Config.ELO_K_FACTOR)
        
        # Create game record
        game = Game(
            player1_netid=user.netid,
            player2_netid=opponent_netid,
            winner_netid=winner_netid,
            elo_change=elo_change
        )
        db.session.add(game)
        db.session.commit()
        
        flash(f"Game recorded! {winner.full_name} won (+{elo_change} ELO)", "success")
        return redirect(url_for('index'))
    
    return render_template("report_game.html", user=user)

@app.route("/games/history")
@login_required
def game_history():
    """View game history"""
    if current_user.is_admin:
        # Show all games for admin
        games = Game.query.order_by(desc(Game.timestamp)).limit(100).all()
    else:
        user = get_current_user()
        games = user.get_all_games()
    
    return render_template("game_history.html", games=games)

@app.route("/leaderboard")
@login_required
def leaderboard():
    """Full ELO leaderboard"""
    users = User.query.filter_by(archived=False).order_by(desc(User.elo_rating)).all()
    return render_template("leaderboard.html", users=users)

@app.route("/users/search")
@login_required
def search_users():
    """Search users by NetID or name (AJAX endpoint)"""
    query = request.args.get("q", "").strip().lower()
    
    if len(query) < 2:
        return jsonify([])
    
    # Search by netid, first name, or last name
    users = User.query.filter(
        or_(
            User.netid.ilike(f"%{query}%"),
            User.first_name.ilike(f"%{query}%"),
            User.last_name.ilike(f"%{query}%")
        ),
        User.archived == False
    ).limit(10).all()
    
    results = [{
        "netid": user.netid,
        "name": user.full_name,
        "elo": user.elo_rating
    } for user in users]
    
    return jsonify(results)

# ============================================================================
# TOURNAMENT ROUTES
# ============================================================================

@app.route("/tournaments")
@login_required
def tournaments():
    """List all tournaments"""
    open_tournaments = Tournament.query.filter_by(status='open').order_by(desc(Tournament.created_at)).all()
    active_tournaments = Tournament.query.filter_by(status='active').order_by(desc(Tournament.created_at)).all()
    completed_tournaments = Tournament.query.filter_by(status='completed').order_by(desc(Tournament.created_at)).limit(10).all()
    
    return render_template(
        "tournaments.html",
        open_tournaments=open_tournaments,
        active_tournaments=active_tournaments,
        completed_tournaments=completed_tournaments
    )

@app.route("/tournaments/<int:tournament_id>")
@login_required
def tournament_detail(tournament_id):
    """View tournament details and bracket"""
    tournament = Tournament.query.get_or_404(tournament_id)
    participants = tournament.participants.order_by(TournamentParticipant.seed).all()
    matches = tournament.matches.order_by(
        TournamentMatch.bracket,
        TournamentMatch.round_number,
        TournamentMatch.match_number
    ).all()
    
    # Group matches by bracket and round
    matches_by_bracket = {}
    for match in matches:
        if match.bracket not in matches_by_bracket:
            matches_by_bracket[match.bracket] = {}
        if match.round_number not in matches_by_bracket[match.bracket]:
            matches_by_bracket[match.bracket][match.round_number] = []
        matches_by_bracket[match.bracket][match.round_number].append(match)
    
    # Check if current user is participating
    user_participant = None
    if not current_user.is_admin:
        user = get_current_user()
        user_participant = TournamentParticipant.query.filter_by(
            tournament_id=tournament_id,
            user_netid=user.netid
        ).first()
    
    return render_template(
        "tournament_detail.html",
        tournament=tournament,
        participants=participants,
        matches_by_bracket=matches_by_bracket,
        user_participant=user_participant
    )

@app.route("/tournaments/<int:tournament_id>/signup", methods=["POST"])
@login_required
def tournament_signup(tournament_id):
    """Sign up for a tournament"""
    if current_user.is_admin:
        flash("Admins cannot sign up for tournaments.", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    tournament = Tournament.query.get_or_404(tournament_id)
    user = get_current_user()
    
    if not tournament.can_signup():
        flash("This tournament is not open for signups.", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Check if already signed up
    existing = TournamentParticipant.query.filter_by(
        tournament_id=tournament_id,
        user_netid=user.netid
    ).first()
    
    if existing:
        flash("You are already signed up for this tournament.", "info")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Get self-rating
    self_rating = request.form.get("self_rating", type=int)
    if not self_rating or not (1 <= self_rating <= 10):
        flash("Please provide a valid self-rating (1-10).", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Create participant
    participant = TournamentParticipant(
        tournament_id=tournament_id,
        user_netid=user.netid,
        self_rating=self_rating
    )
    db.session.add(participant)
    db.session.commit()
    
    flash(f"Successfully signed up for {tournament.name}!", "success")
    return redirect(url_for('tournament_detail', tournament_id=tournament_id))

@app.route("/tournaments/<int:tournament_id>/matches/<int:match_id>/report", methods=["POST"])
@login_required
def report_tournament_match(tournament_id, match_id):
    """Report a tournament match result"""
    if current_user.is_admin:
        flash("Admins cannot report matches. Players should report their own results.", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    tournament = Tournament.query.get_or_404(tournament_id)
    match = TournamentMatch.query.get_or_404(match_id)
    user = get_current_user()
    
    if match.tournament_id != tournament_id:
        flash("Match does not belong to this tournament.", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    if not tournament.can_report_results():
        flash("This tournament is not active.", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    winner_netid = request.form.get("winner_netid", "").strip().lower()
    
    # Validate that reporter is one of the players
    if user.netid not in [match.player1_netid, match.player2_netid]:
        flash("You are not a participant in this match.", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Get players
    player1 = User.query.get(match.player1_netid)
    player2 = User.query.get(match.player2_netid)
    
    if winner_netid == player1.netid:
        winner = player1
        loser = player2
    elif winner_netid == player2.netid:
        winner = player2
        loser = player1
    else:
        flash("Invalid winner selection.", "error")
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Update ELO ratings
    elo_change = update_ratings_after_game(winner, loser, Config.ELO_K_FACTOR)
    
    # Create game record
    game = Game(
        player1_netid=player1.netid,
        player2_netid=player2.netid,
        winner_netid=winner_netid,
        tournament_id=tournament_id,
        elo_change=elo_change
    )
    db.session.add(game)
    db.session.commit()
    
    # Report match result and advance bracket
    success, message = report_match_result(match, winner_netid, game.id)
    
    if success:
        flash(f"Match result recorded! {winner.full_name} wins.", "success")
    else:
        flash(message, "error")
    
    return redirect(url_for('tournament_detail', tournament_id=tournament_id))

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    print(f"[DEBUG] admin_login route called, method: {request.method}")
    if current_user.is_authenticated and current_user.is_admin:
        print("[DEBUG] User already authenticated as admin, redirecting")
        return redirect(url_for('admin_dashboard'))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        print(f"[DEBUG] POST request - username: '{username}', password length: {len(password)}")
        
        try:
            success, result = login_admin(username, password)
            print(f"[DEBUG] login_admin returned: success={success}, result={result}")
            
            if success:
                flash(f"Welcome, {result.username}!", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash(result, "error")
        except Exception as e:
            print(f"[DEBUG] Exception in admin_login: {e}")
            import traceback
            traceback.print_exc()
            flash(f"Login error: {e}", "error")
    
    return render_template("admin/login.html")

@app.route("/admin")
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash("You must be an admin to access this page.", "error")
        return redirect(url_for('index'))
    
    admin = get_current_admin()
    
    # Statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(archived=False).count()
    total_games = Game.query.count()
    total_tournaments = Tournament.query.count()
    active_tournaments = Tournament.query.filter_by(status='active').count()
    
    recent_games = Game.query.order_by(desc(Game.timestamp)).limit(10).all()
    
    return render_template(
        "admin/dashboard.html",
        admin=admin,
        total_users=total_users,
        active_users=active_users,
        total_games=total_games,
        total_tournaments=total_tournaments,
        active_tournaments=active_tournaments,
        recent_games=recent_games
    )

@app.route("/admin/users")
@login_required
def admin_users():
    """Manage users"""
    if not current_user.is_admin:
        flash("You must be an admin to access this page.", "error")
        return redirect(url_for('index'))
    
    active_users = User.query.filter_by(archived=False).order_by(User.netid).all()
    archived_users = User.query.filter_by(archived=True).order_by(User.netid).all()
    
    return render_template(
        "admin/users.html",
        active_users=active_users,
        archived_users=archived_users
    )

@app.route("/admin/users/add", methods=["POST"])
@login_required
def admin_add_user():
    """Add a new user (NetID only - user will complete profile on first login)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    netid = request.form.get("netid", "").strip().lower()
    
    if not netid:
        flash("NetID is required.", "error")
        return redirect(url_for('admin_users'))
    
    # Create user with just NetID (no names yet)
    success, result = create_user(netid)
    
    if success:
        flash(f"User {result.netid} added successfully. They will complete their profile on first login.", "success")
    else:
        flash(result, "error")
    
    return redirect(url_for('admin_users'))

@app.route("/admin/users/<netid>/archive", methods=["POST"])
@login_required
def admin_archive_user(netid):
    """Archive a user"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    user = User.query.get_or_404(netid)
    user.archived = True
    db.session.commit()
    
    flash(f"User {user.full_name} archived.", "success")
    return redirect(url_for('admin_users'))

@app.route("/admin/users/<netid>/unarchive", methods=["POST"])
@login_required
def admin_unarchive_user(netid):
    """Unarchive a user"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    user = User.query.get_or_404(netid)
    user.archived = False
    db.session.commit()
    
    flash(f"User {user.full_name} unarchived.", "success")
    return redirect(url_for('admin_users'))

@app.route("/admin/users/<netid>/delete", methods=["POST"])
@login_required
def admin_delete_user(netid):
    """Delete a user (only if no games played)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    user = User.query.get_or_404(netid)
    
    # Check if user has any games
    if user.get_all_games():
        flash("Cannot delete user with game history. Archive instead.", "error")
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User {user.full_name} deleted.", "success")
    return redirect(url_for('admin_users'))

@app.route("/admin/admins")
@login_required
def admin_manage_admins():
    """Manage admin accounts"""
    if not current_user.is_admin:
        flash("You must be an admin to access this page.", "error")
        return redirect(url_for('index'))
    
    admins = Admin.query.order_by(Admin.username).all()
    return render_template("admin/admins.html", admins=admins)

@app.route("/admin/admins/add", methods=["POST"])
@login_required
def admin_add_admin():
    """Add a new admin"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    # Check if username exists
    existing = Admin.query.filter_by(username=username).first()
    if existing:
        flash("An admin with this username already exists.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    admin = Admin(username=username)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    
    flash(f"Admin {username} created successfully.", "success")
    return redirect(url_for('admin_manage_admins'))

@app.route("/admin/admins/<int:admin_id>/change_password", methods=["POST"])
@login_required
def admin_change_password(admin_id):
    """Change admin password"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    current_admin = get_current_admin()
    target_admin = Admin.query.get_or_404(admin_id)
    
    # Only allow changing own password or if you're the default admin
    if current_admin.id != target_admin.id and current_admin.username != Config.DEFAULT_ADMIN_USERNAME:
        flash("You can only change your own password.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    new_password = request.form.get("new_password", "")
    
    if not new_password:
        flash("New password cannot be empty.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    target_admin.set_password(new_password)
    db.session.commit()
    
    flash("Password changed successfully.", "success")
    return redirect(url_for('admin_manage_admins'))

@app.route("/admin/tournaments/create", methods=["GET", "POST"])
@login_required
def admin_create_tournament():
    """Create a new tournament"""
    if not current_user.is_admin:
        flash("You must be an admin to access this page.", "error")
        return redirect(url_for('index'))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        format_type = request.form.get("format", "").strip()
        
        if not name or not format_type:
            flash("Tournament name and format are required.", "error")
            return render_template("admin/tournament_create.html")
        
        if format_type not in ['single_elim', 'double_elim', 'round_robin']:
            flash("Invalid tournament format.", "error")
            return render_template("admin/tournament_create.html")
        
        admin = get_current_admin()
        tournament = Tournament(
            name=name,
            format=format_type,
            created_by_admin_id=admin.id
        )
        db.session.add(tournament)
        db.session.commit()
        
        flash(f"Tournament '{name}' created successfully!", "success")
        return redirect(url_for('tournament_detail', tournament_id=tournament.id))
    
    return render_template("admin/tournament_create.html")

@app.route("/admin/tournaments/<int:tournament_id>/activate", methods=["POST"])
@login_required
def admin_activate_tournament(tournament_id):
    """Activate a tournament"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    tournament = Tournament.query.get_or_404(tournament_id)
    
    success, message = activate_tournament(tournament)
    
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    
    return redirect(url_for('tournament_detail', tournament_id=tournament_id))

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.context_processor
def inject_version():
    """Inject version into all templates"""
    try:
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        with open(version_path, "r") as vf:
            version = vf.read().strip()
    except Exception:
        version = "unknown"
    return {"version": version}

@app.context_processor
def inject_user():
    """Inject current user/admin into all templates"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return {"current_admin": get_current_admin(), "current_user": None}
        else:
            return {"current_user": get_current_user(), "current_admin": None}
    return {"current_user": None, "current_admin": None}

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)

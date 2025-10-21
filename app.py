import os
import re
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_talisman import Talisman
from flask_compress import Compress
from flask_login import login_required, logout_user, current_user
from sqlalchemy import or_, desc, text
from sqlalchemy.orm import joinedload
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from config import Config
from flask_wtf.csrf import CSRFProtect
from models import db, User, Admin, Game, Tournament, TournamentParticipant, TournamentMatch
from auth import login_manager, login_user_by_netid, login_admin, create_user, get_current_user, get_current_admin, validate_admin_password
from elo import update_ratings_after_game, update_ratings_after_doubles_game
from tournament_logic import activate_tournament, report_match_result

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

print(f"[INFO] Flask app initialized")
print(f"[INFO] Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"[INFO] Secret key configured: {bool(app.config.get('SECRET_KEY'))}")
print(f"[INFO] Template folder: {app.template_folder}")
print(f"[INFO] Static folder: {app.static_folder}")

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Compress for response compression
compress = Compress(app)

# Enable CSRF protection
csrf = CSRFProtect(app)

# Rate limiting and caching
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per 15 minutes"])
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 120})

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, logging.INFO))

# ============================================================================
# ERROR HANDLING DECORATOR
# ============================================================================

def handle_db_errors(f):
    """Decorator to handle database errors and rollback on failure"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            logging.error(f"Database error in {f.__name__}: {e}")
            import traceback
            traceback.print_exc()
            flash("An error occurred. Please try again.", "error")
            return redirect(request.referrer or url_for('index'))
    return decorated_function

# Test database connection on startup
with app.app_context():
    try:
        db.engine.connect()
        print("[INFO] Database connection successful")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        import traceback
        traceback.print_exc()

csp = {
    "default-src": ["'self'"],
    # Allow inline scripts for existing templates. Consider migrating to nonces later.
    "script-src": ["'self'", "'unsafe-inline'"],
    # Keep inline styles allowed due to templates/CSS classes; can tighten later
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'"],
}
Talisman(
    app,
    content_security_policy=csp,
    force_https=Config.FORCE_HTTPS,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    referrer_policy='no-referrer',
    permissions_policy={
        'geolocation': '()',
        'camera': '()',
        'microphone': '()'
    },
)

# ============================================================================
# DEBUG MIDDLEWARE
# ============================================================================

@app.before_request
def log_request():
    logging.debug(f"Request: {request.method} {request.path}")

@app.after_request
def add_cache_headers(response):
    """Add caching headers appropriate to route type and auth state"""
    if request.path.startswith('/static/'):
        # Cache static files for 1 year (with cache busting via version param)
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
    elif request.path == '/health':
        # Don't cache health checks
        response.cache_control.no_cache = True
    else:
        # Do not cache personalized content for authenticated users
        try:
            if current_user.is_authenticated:
                response.cache_control.no_store = True
            else:
                # Cache public HTML pages briefly
                response.cache_control.max_age = 300
        except Exception:
            response.cache_control.max_age = 300
    return response

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
    
    # Check if user exists - only admin-created users can set up profiles
    existing_user = User.query.get(netid)
    
    if not existing_user:
        flash("Account not found. Please contact an administrator to create your account.", "error")
        return redirect(url_for('login'))
    
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        
        if not first_name or not last_name:
            flash("First and last name are required.", "error")
            return render_template("profile_setup.html", netid=netid)
        
        # User exists (added by admin), complete their profile
        from auth import complete_user_profile, UserSession
        success, result = complete_user_profile(existing_user, first_name, last_name)
        
        if success:
            # Log the user in directly with UserSession
            from flask_login import login_user
            session_user = UserSession(result.netid)
            login_user(session_user, remember=True)
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
    
    # Get recent games with eager loading - limit to 10 directly
    recent_games = Game.query.options(
        joinedload(Game.player1),
        joinedload(Game.player2),
        joinedload(Game.player3),
        joinedload(Game.player4)
    ).filter(
        or_(
            Game.player1_netid == user.netid,
            Game.player2_netid == user.netid,
            Game.player3_netid == user.netid,
            Game.player4_netid == user.netid
        )
    ).order_by(desc(Game.timestamp)).limit(10).all()
    
    # Get leaderboard (top 10) - only active users
    leaderboard = User.query.filter_by(archived=False, is_active=True).order_by(desc(User.elo_rating)).limit(10).all()
    
    # Get user's rank (among active users only)
    user_rank = User.query.filter(User.elo_rating > user.elo_rating, User.archived == False, User.is_active == True).count() + 1
    
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
    """Report a game result (singles or doubles)"""
    if current_user.is_admin:
        flash("Admins cannot report games. Please log in with a user account.", "error")
        return redirect(url_for('admin_dashboard'))
    
    user = get_current_user()
    if not user:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for('login'))
    
    if request.method == "POST":
        try:
            game_type = request.form.get("game_type", "singles").strip().lower()
            
            if game_type == "singles":
                # Original singles game logic
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
                
                if not opponent.is_active:
                    flash("Cannot report games with inactive users. The user must complete their profile first.", "error")
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
                    game_type='singles',
                    player1_netid=user.netid,
                    player2_netid=opponent_netid,
                    winner_netid=winner_netid,
                    elo_change=elo_change
                )
                db.session.add(game)
                db.session.commit()
                try:
                    cache.delete_memoized(leaderboard)
                except Exception:
                    pass
                
                flash(f"Game recorded! {winner.full_name} won (+{elo_change} ELO)", "success")
                return redirect(url_for('index'))
            
            elif game_type == "doubles":
                # Doubles game logic
                partner_netid = request.form.get("partner_netid", "").strip().lower()
                opponent1_netid = request.form.get("opponent1_netid", "").strip().lower()
                opponent2_netid = request.form.get("opponent2_netid", "").strip().lower()
                winning_team = request.form.get("winning_team", "").strip()  # "team1" or "team2"
                
                # Validate all players exist
                partner = User.query.get(partner_netid)
                opponent1 = User.query.get(opponent1_netid)
                opponent2 = User.query.get(opponent2_netid)
                
                if not partner:
                    flash("Partner not found.", "error")
                    return redirect(url_for('report_game'))
                if not opponent1:
                    flash("First opponent not found.", "error")
                    return redirect(url_for('report_game'))
                if not opponent2:
                    flash("Second opponent not found.", "error")
                    return redirect(url_for('report_game'))
                
                # Check for archived users
                if partner.archived or opponent1.archived or opponent2.archived:
                    flash("Cannot report games with archived users.", "error")
                    return redirect(url_for('report_game'))
                
                # Check for inactive users
                if not partner.is_active or not opponent1.is_active or not opponent2.is_active:
                    flash("Cannot report games with inactive users. All users must complete their profiles first.", "error")
                    return redirect(url_for('report_game'))
                
                # Validate all 4 players are unique
                all_netids = [user.netid, partner_netid, opponent1_netid, opponent2_netid]
                if len(set(all_netids)) != 4:
                    flash("All 4 players must be different!", "error")
                    return redirect(url_for('report_game'))
                
                # Validate winning team
                if winning_team not in ["team1", "team2"]:
                    flash("Invalid winning team selection.", "error")
                    return redirect(url_for('report_game'))
                
                # Setup teams
                team1_players = [user, partner]
                team2_players = [opponent1, opponent2]
                
                # Determine winner netid (use first player of winning team)
                if winning_team == "team1":
                    winner_netid = user.netid
                    winning_team_num = 1
                else:
                    winner_netid = opponent1_netid
                    winning_team_num = 2
                
                # Update ELO ratings for all 4 players
                elo_change = update_ratings_after_doubles_game(
                    team1_players, 
                    team2_players, 
                    winning_team_num, 
                    Config.ELO_K_FACTOR
                )
                
                # Create game record
                game = Game(
                    game_type='doubles',
                    player1_netid=user.netid,
                    player2_netid=partner_netid,
                    player3_netid=opponent1_netid,
                    player4_netid=opponent2_netid,
                    winner_netid=winner_netid,
                    elo_change=elo_change
                )
                db.session.add(game)
                db.session.commit()
                try:
                    cache.delete_memoized(leaderboard)
                except Exception:
                    pass
                
                if winning_team == "team1":
                    flash(f"Doubles game recorded! Your team won (+{elo_change} ELO each)", "success")
                else:
                    flash(f"Doubles game recorded! Opponent team won ({elo_change} ELO each)", "success")
                return redirect(url_for('index'))
        
            else:
                flash("Invalid game type.", "error")
                return redirect(url_for('report_game'))
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error reporting game: {e}")
            import traceback
            traceback.print_exc()
            flash("Error reporting game. Please try again.", "error")
            return redirect(url_for('report_game'))
    
    return render_template("report_game.html", user=user)

@app.route("/games/history")
@login_required
def game_history():
    """View game history with pagination"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = max(1, min(per_page, 100))  # Clamp per_page 1..100
        page = max(1, page)  # Clamp page >= 1
        
        if current_user.is_admin:
            # Show all games for admin with eager loading
            games = Game.query.options(
                joinedload(Game.player1),
                joinedload(Game.player2),
                joinedload(Game.player3),
                joinedload(Game.player4)
            ).order_by(desc(Game.timestamp)).limit(per_page).offset((page - 1) * per_page).all()
            
            total_games = Game.query.count()
        else:
            user = get_current_user()
            if not user:
                flash("User not found. Please log in again.", "error")
                return redirect(url_for('login'))
            
            # Get user's games with eager loading and pagination
            games = Game.query.options(
                joinedload(Game.player1),
                joinedload(Game.player2),
                joinedload(Game.player3),
                joinedload(Game.player4)
            ).filter(
                or_(
                    Game.player1_netid == user.netid,
                    Game.player2_netid == user.netid,
                    Game.player3_netid == user.netid,
                    Game.player4_netid == user.netid
                )
            ).order_by(desc(Game.timestamp)).limit(per_page).offset((page - 1) * per_page).all()
            
            total_games = Game.query.filter(
                or_(
                    Game.player1_netid == user.netid,
                    Game.player2_netid == user.netid,
                    Game.player3_netid == user.netid,
                    Game.player4_netid == user.netid
                )
            ).count()
        
        total_pages = (total_games + per_page - 1) // per_page  # Ceiling division
        
        return render_template("game_history.html", 
                             games=games, 
                             page=page, 
                             total_pages=total_pages,
                             total_games=total_games)
    except Exception as e:
        logging.error(f"Error loading game history: {e}")
        import traceback
        traceback.print_exc()
        flash("Error loading game history.", "error")
        return redirect(url_for('index'))

@app.route("/games/<int:game_id>/delete", methods=["POST"])
@login_required
def delete_game(game_id):
    """Delete a game if it was recent and user participated"""
    try:
        if current_user.is_admin:
            flash("Admins cannot delete games from this view. Contact system administrator for database operations.", "error")
            return redirect(url_for('game_history'))
        
        user = get_current_user()
        if not user:
            flash("User not found. Please log in again.", "error")
            return redirect(url_for('login'))
        
        game = Game.query.get(game_id)
        if not game:
            flash("Game not found.", "error")
            return redirect(url_for('game_history'))
        
        # Check if user participated in the game
        if user.netid not in game.get_all_player_netids():
            flash("You can only delete games you participated in.", "error")
            return redirect(url_for('game_history'))
        
        # Check if game is a tournament game
        if game.tournament_id:
            flash("Tournament games cannot be deleted.", "error")
            return redirect(url_for('game_history'))
        
        # Check if game is recent (within 15 minutes)
        time_diff = datetime.utcnow() - game.timestamp
        if time_diff.total_seconds() > 900:  # 900 seconds = 15 minutes
            flash("You can only delete games within 15 minutes of creation.", "error")
            return redirect(url_for('game_history'))
        
        # Reverse ELO changes
        if game.is_doubles():
            # For doubles, reverse ELO for all 4 players
            player1 = User.query.get(game.player1_netid)
            player2 = User.query.get(game.player2_netid)
            player3 = User.query.get(game.player3_netid)
            player4 = User.query.get(game.player4_netid)
            
            # Check all players exist
            if not all([player1, player2, player3, player4]):
                flash("Error: Some players not found.", "error")
                return redirect(url_for('game_history'))
            
            # Determine winning and losing teams
            if game.winner_netid in game.get_team1_netids():
                # Team 1 won
                player1.elo_rating -= game.elo_change
                player2.elo_rating -= game.elo_change
                player3.elo_rating += game.elo_change
                player4.elo_rating += game.elo_change
            else:
                # Team 2 won
                player1.elo_rating += game.elo_change
                player2.elo_rating += game.elo_change
                player3.elo_rating -= game.elo_change
                player4.elo_rating -= game.elo_change
        else:
            # For singles, reverse ELO for both players
            winner = User.query.get(game.winner_netid)
            loser_netid = game.get_loser_netid()
            loser = User.query.get(loser_netid)
            
            if not winner or not loser:
                flash("Error: Players not found.", "error")
                return redirect(url_for('game_history'))
            
            winner.elo_rating -= game.elo_change
            loser.elo_rating += game.elo_change
        
        # Delete the game
        db.session.delete(game)
        db.session.commit()
        
        flash("Game deleted successfully. ELO ratings have been reversed.", "success")
        return redirect(url_for('game_history'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting game {game_id}: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error deleting game. Please try again.", "error")
        return redirect(url_for('game_history'))

@app.route("/leaderboard")
@login_required
@cache.cached(timeout=60)
def leaderboard():
    """Full ELO leaderboard"""
    if current_user.is_admin:
        # Admins can see all users (including inactive ones)
        users = User.query.filter_by(archived=False).order_by(desc(User.elo_rating)).all()
    else:
        # Regular users only see active users
        users = User.query.filter_by(archived=False, is_active=True).order_by(desc(User.elo_rating)).all()
    return render_template("leaderboard.html", users=users)

@app.route("/users/search")
@login_required
@limiter.limit("10/minute")
def search_users():
    """Search users by NetID or name (AJAX endpoint)"""
    query = request.args.get("q", "").strip().lower()
    
    if len(query) < 2:
        return jsonify([])
    
    # Search by netid, first name, or last name
    # Only show active users (admins can see all via admin panel)
    users = User.query.filter(
        or_(
            User.netid.ilike(f"%{query}%"),
            User.first_name.ilike(f"%{query}%"),
            User.last_name.ilike(f"%{query}%")
        ),
        User.archived == False,
        User.is_active == True
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
@cache.cached(timeout=60)
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
    try:
        cache.delete_memoized(leaderboard)
        cache.delete_memoized(tournaments)
    except Exception:
        pass
    
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
@limiter.limit("5/minute")
def admin_login():
    """Admin login page"""
    try:
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
        
        print("[DEBUG] About to render admin/login.html")
        return render_template("admin/login.html")
    except Exception as e:
        print(f"[DEBUG] EXCEPTION IN admin_login ROUTE: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.route("/admin")
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash("You must be an admin to access this page.", "error")
        return redirect(url_for('index'))
    
    admin = get_current_admin()
    
    # Statistics
    total_users = User.query.filter_by(archived=False).count()
    active_users = User.query.filter_by(archived=False, is_active=True).count()
    inactive_users = User.query.filter_by(archived=False, is_active=False).count()
    total_games = Game.query.count()
    total_tournaments = Tournament.query.count()
    active_tournaments = Tournament.query.filter_by(status='active').count()
    
    # Recent games with eager loading
    recent_games = Game.query.options(
        joinedload(Game.player1),
        joinedload(Game.player2),
        joinedload(Game.player3),
        joinedload(Game.player4)
    ).order_by(desc(Game.timestamp)).limit(10).all()
    
    return render_template(
        "admin/dashboard.html",
        admin=admin,
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
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
    
    # Separate active users (profile completed) and inactive users (profile not completed)
    active_users = User.query.filter_by(archived=False, is_active=True).order_by(User.netid).all()
    inactive_users = User.query.filter_by(archived=False, is_active=False).order_by(User.netid).all()
    archived_users = User.query.filter_by(archived=True).order_by(User.netid).all()
    
    return render_template(
        "admin/users.html",
        active_users=active_users,
        inactive_users=inactive_users,
        archived_users=archived_users
    )

@app.route("/admin/users/add", methods=["POST"])
@login_required
def admin_add_user():
    """Add new user(s) - supports bulk add with space or comma separation"""
    user_id = getattr(current_user, 'admin_id', getattr(current_user, 'netid', 'unknown'))
    print(f"[DEBUG] admin_add_user called by {user_id} (is_admin={getattr(current_user, 'is_admin', False)})")
    
    if not current_user.is_admin:
        print(f"[DEBUG] Unauthorized access attempt")
        return jsonify({"error": "Unauthorized"}), 403
    
    netid_input = request.form.get("netid", "").strip()
    print(f"[DEBUG] Raw netid input: '{netid_input}'")
    
    if not netid_input:
        print(f"[DEBUG] Empty netid input")
        flash("NetID is required.", "error")
        return redirect(url_for('admin_users'))
    
    # Parse input - split by commas and/or spaces
    netids = re.split(r'[,\s]+', netid_input)
    netids = [n.strip().lower() for n in netids if n.strip()]
    print(f"[DEBUG] Parsed netids: {netids}")
    
    if not netids:
        print(f"[DEBUG] No valid netids after parsing")
        flash("No valid NetIDs provided.", "error")
        return redirect(url_for('admin_users'))
    
    # Add each user
    added = []
    skipped = []
    errors = []
    
    print(f"[DEBUG] Starting to process {len(netids)} netid(s)")
    for netid in netids:
        print(f"[DEBUG] Processing netid: {netid}")
        try:
            success, result = create_user(netid)
            print(f"[DEBUG] create_user returned: success={success}, result={result}")
            if success:
                added.append(netid)
                print(f"[DEBUG] Successfully added: {netid}")
            else:
                if "already exists" in result.lower():
                    skipped.append(netid)
                    print(f"[DEBUG] Skipped (already exists): {netid}")
                else:
                    errors.append(f"{netid}: {result}")
                    print(f"[DEBUG] Error adding {netid}: {result}")
        except Exception as e:
            error_msg = f"{netid}: {str(e)}"
            errors.append(error_msg)
            print(f"[DEBUG] Exception adding {netid}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"[DEBUG] Results - Added: {len(added)}, Skipped: {len(skipped)}, Errors: {len(errors)}")
    
    # Display results
    if added:
        if len(added) == 1:
            flash(f"User {added[0]} added successfully. They will complete their profile on first login.", "success")
        else:
            flash(f"Added {len(added)} users: {', '.join(added)}. They will complete their profiles on first login.", "success")
    
    if skipped:
        if len(skipped) == 1:
            flash(f"User {skipped[0]} already exists.", "info")
        else:
            flash(f"Skipped {len(skipped)} existing users: {', '.join(skipped)}", "info")
    
    if errors:
        for error in errors:
            flash(error, "error")
    
    print(f"[DEBUG] Redirecting to admin_users")
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
    
    # Validate password strength
    valid, error_message = validate_admin_password(password)
    if not valid:
        flash(error_message, "error")
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
    
    # Don't allow changing password for the default admin user (unless it's themselves)
    if target_admin.username == Config.DEFAULT_ADMIN_USERNAME and current_admin.id != target_admin.id:
        flash("Cannot change password for the admin user.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    # Only allow changing own password or if you're the default admin
    if current_admin.id != target_admin.id and current_admin.username != Config.DEFAULT_ADMIN_USERNAME:
        flash("You can only change your own password.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    new_password = request.form.get("new_password", "")
    
    if not new_password:
        flash("New password cannot be empty.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    # Validate password strength
    valid, error_message = validate_admin_password(new_password)
    if not valid:
        flash(error_message, "error")
        return redirect(url_for('admin_manage_admins'))
    
    target_admin.set_password(new_password)
    db.session.commit()
    
    flash("Password changed successfully.", "success")
    return redirect(url_for('admin_manage_admins'))

@app.route("/admin/admins/<int:admin_id>/delete", methods=["POST"])
@login_required
def admin_delete_admin(admin_id):
    """Delete an admin account"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    current_admin = get_current_admin()
    target_admin = Admin.query.get_or_404(admin_id)
    
    # Don't allow deleting the default admin user
    if target_admin.username == Config.DEFAULT_ADMIN_USERNAME:
        flash("Cannot delete the admin user.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    # Don't allow deleting yourself
    if current_admin.id == target_admin.id:
        flash("Cannot delete your own account.", "error")
        return redirect(url_for('admin_manage_admins'))
    
    db.session.delete(target_admin)
    db.session.commit()
    
    flash(f"Admin {target_admin.username} deleted successfully.", "success")
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
        try:
            cache.delete_memoized(tournaments)
        except Exception:
            pass
        
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
    try:
        cache.delete_memoized(tournaments)
    except Exception:
        pass
    return redirect(url_for('tournament_detail', tournament_id=tournament_id))

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.context_processor
def inject_version():
    """Inject version into all templates for cache busting"""
    try:
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        with open(version_path, "r") as vf:
            version = vf.read().strip()
    except Exception as e:
        print(f"[WARNING] Could not read VERSION file: {e}")
        version = "unknown"
    
    # Add cache busting parameter for static files
    return {
        "version": version,
        "cache_bust": version.replace(".", "")  # Remove dots for URL param
    }

@app.context_processor
def inject_utility_functions():
    """Inject utility functions into templates"""
    return {
        "now": datetime.utcnow
    }

@app.context_processor
def inject_user():
    """Inject current user/admin into all templates"""
    try:
        if current_user.is_authenticated:
            if current_user.is_admin:
                admin = get_current_admin()
                if admin is None:
                    print(f"[ERROR] Admin session exists but admin not found in DB: {current_user.admin_id}")
                    return {"current_admin": None, "current_user": None}
                return {"current_admin": admin, "current_user": None}
            else:
                user = get_current_user()
                if user is None:
                    print(f"[ERROR] User session exists but user not found in DB: {current_user.netid}")
                    return {"current_user": None, "current_admin": None}
                return {"current_user": user, "current_admin": None}
    except AttributeError as e:
        print(f"[WARNING] AttributeError in inject_user: {e}")
        return {"current_user": None, "current_admin": None}
    except Exception as e:
        print(f"[ERROR] Unexpected error in inject_user context processor: {e}")
        import traceback
        traceback.print_exc()
    return {"current_user": None, "current_admin": None}

@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    checks = {
        "status": "ok",
        "database": "unknown",
        "templates": "unknown"
    }
    
    # Check database
    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    
    # Check templates
    try:
        app.jinja_env.get_template("login.html")
        checks["templates"] = "ok"
    except Exception as e:
        checks["templates"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    
    return jsonify(checks), 200 if checks["status"] == "ok" else 503

@app.errorhandler(400)
def bad_request_error(error):
    """Handle bad request errors"""
    logging.warning(f"400 Bad Request: {error}")
    try:
        return render_template('errors/400.html'), 400
    except Exception:
        return "<h1>400 Bad Request</h1><p>The request could not be understood.</p>", 400

@app.errorhandler(403)
def forbidden_error(error):
    """Handle forbidden errors"""
    logging.warning(f"403 Forbidden: {error}")
    try:
        return render_template('errors/403.html'), 403
    except Exception:
        return "<h1>403 Forbidden</h1><p>You don't have permission to access this resource.</p>", 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Enhanced 500 error handler with better logging and fallbacks"""
    import traceback
    
    # Log full error details
    print(f"[ERROR] 500 Internal Server Error: {error}")
    print(f"[ERROR] Error type: {type(error).__name__}")
    print(f"[ERROR] Request path: {request.path if request else 'Unknown'}")
    print(f"[ERROR] Request method: {request.method if request else 'Unknown'}")
    traceback.print_exc()
    
    # Get error details
    error_type = type(error).__name__
    error_message = str(error)
    
    # Get traceback for admins
    tb = None
    try:
        if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
            tb = traceback.format_exc()
    except Exception as tb_error:
        print(f"[WARNING] Could not get traceback for admin: {tb_error}")
    
    # Try to rollback database session
    try:
        db.session.rollback()
        print(f"[INFO] Database session rolled back successfully")
    except Exception as rollback_error:
        print(f"[ERROR] Failed to rollback database session: {rollback_error}")
    
    # Try to render error template
    try:
        return render_template('errors/500.html', 
                             error_type=error_type,
                             error_message=error_message,
                             traceback=tb), 500
    except Exception as template_error:
        print(f"[ERROR] Failed to render 500 error template: {template_error}")
        traceback.print_exc()
        
        # Fallback to plain HTML if template rendering fails
        admin_info = ""
        if tb:
            admin_info = f"<pre style='background: #f0f0f0; padding: 15px; overflow: auto;'>{tb}</pre>"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>500 Internal Server Error</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                h1 {{ color: #d32f2f; }}
                .error-box {{ background: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 20px 0; }}
                a {{ color: #1976d2; }}
            </style>
        </head>
        <body>
            <h1>500 Internal Server Error</h1>
            <div class="error-box">
                <h2>{error_type}</h2>
                <p><strong>Error:</strong> {error_message}</p>
            </div>
            <p>Something went wrong. Please try again later or contact an administrator.</p>
            {admin_info}
            <p><a href="/">← Go Home</a></p>
        </body>
        </html>
        """, 500

if __name__ == "__main__":
    app.run(debug=True)

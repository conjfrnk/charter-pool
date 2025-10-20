from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    netid = db.Column(db.String(50), primary_key=True)
    first_name = db.Column(db.String(100), nullable=True)  # Nullable until user completes profile
    last_name = db.Column(db.String(100), nullable=True)   # Nullable until user completes profile
    elo_rating = db.Column(db.Integer, default=1200, nullable=False, index=True)  # Index for leaderboard sorting
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    archived = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Index for filtering
    is_active = db.Column(db.Boolean, default=False, nullable=False, server_default='false', index=True)  # Index for filtering
    
    # Relationships
    games_as_player1 = db.relationship('Game', foreign_keys='Game.player1_netid', backref='player1', lazy='dynamic')
    games_as_player2 = db.relationship('Game', foreign_keys='Game.player2_netid', backref='player2', lazy='dynamic')
    tournament_participations = db.relationship('TournamentParticipant', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return self.netid
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.netid  # Fallback if names not set yet
    
    @property
    def needs_profile_setup(self):
        """Check if user needs to complete their profile"""
        return not self.is_active
    
    def get_all_games(self):
        """Get all games this user participated in (singles and doubles)"""
        return Game.query.filter(
            (Game.player1_netid == self.netid) | 
            (Game.player2_netid == self.netid) |
            (Game.player3_netid == self.netid) | 
            (Game.player4_netid == self.netid)
        ).order_by(Game.timestamp.desc()).all()
    
    def get_game_stats(self):
        """
        Get game statistics efficiently (wins, losses, total) in a single pass.
        Returns a dict with 'wins', 'losses', 'total', and 'win_rate'.
        """
        games = self.get_all_games()
        total = len(games)
        
        if total == 0:
            return {'wins': 0, 'losses': 0, 'total': 0, 'win_rate': 0}
        
        wins = 0
        for game in games:
            try:
                if game.is_doubles():
                    # Check if user is on winning team
                    if self.netid in game.get_winning_team_netids():
                        wins += 1
                else:
                    # Singles game
                    if game.winner_netid == self.netid:
                        wins += 1
            except Exception as e:
                # Log error but continue counting
                print(f"[WARNING] Error processing game {game.id} stats: {e}")
                continue
        
        losses = total - wins
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0
        
        return {
            'wins': wins,
            'losses': losses,
            'total': total,
            'win_rate': win_rate
        }
    
    def get_win_count(self):
        """Get number of games won (singles and doubles)"""
        # For backwards compatibility - use get_game_stats for efficiency
        return self.get_game_stats()['wins']
    
    def get_loss_count(self):
        """Get number of games lost (singles and doubles)"""
        # For backwards compatibility - use get_game_stats for efficiency
        return self.get_game_stats()['losses']
    
    def get_win_rate(self):
        """Calculate win rate percentage"""
        # For backwards compatibility - use get_game_stats for efficiency
        return self.get_game_stats()['win_rate']


class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    created_tournaments = db.relationship('Tournament', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        print(f"[DEBUG] set_password called for admin")
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        print(f"[DEBUG] password_hash set: {self.password_hash[:50]}...")
    
    def check_password(self, password):
        print(f"[DEBUG] check_password called")
        print(f"[DEBUG] stored hash: {self.password_hash[:50]}...")
        print(f"[DEBUG] password to check: '{password}'")
        result = check_password_hash(self.password_hash, password)
        print(f"[DEBUG] check_password_hash result: {result}")
        return result
    
    def __repr__(self):
        return self.username


class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    game_type = db.Column(db.String(20), default='singles', nullable=False)  # 'singles' or 'doubles'
    player1_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=False, index=True)
    player2_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=False, index=True)
    player3_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=True, index=True)  # Team 2, Player 1 (for doubles)
    player4_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=True, index=True)  # Team 2, Player 2 (for doubles)
    winner_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)  # Index for sorting by time
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=True, index=True)
    elo_change = db.Column(db.Integer, nullable=False)  # ELO change for the winner(s)
    
    def __repr__(self):
        return f'Game {self.id}'
    
    def is_doubles(self):
        """Check if this is a doubles game"""
        return self.game_type == 'doubles'
    
    def get_team1_netids(self):
        """Get Team 1 player netids (always player1 and player2)"""
        return [self.player1_netid, self.player2_netid]
    
    def get_team2_netids(self):
        """Get Team 2 player netids (player3 and player4 for doubles, empty for singles)"""
        if self.is_doubles():
            return [self.player3_netid, self.player4_netid]
        return []
    
    def get_winning_team_netids(self):
        """Get the netids of the winning team/player"""
        if self.is_doubles():
            # For doubles, winner_netid represents one player, find their team
            if self.winner_netid in self.get_team1_netids():
                return self.get_team1_netids()
            else:
                return self.get_team2_netids()
        else:
            return [self.winner_netid]
    
    def get_losing_team_netids(self):
        """Get the netids of the losing team/player"""
        if self.is_doubles():
            winning_team = self.get_winning_team_netids()
            if self.winner_netid in self.get_team1_netids():
                return self.get_team2_netids()
            else:
                return self.get_team1_netids()
        else:
            return [self.get_loser_netid()]
    
    def get_loser_netid(self):
        """Get the netid of the loser (singles only, for backward compatibility)"""
        if self.winner_netid == self.player1_netid:
            return self.player2_netid
        return self.player1_netid
    
    def get_all_player_netids(self):
        """Get all players in the game"""
        players = [self.player1_netid, self.player2_netid]
        if self.is_doubles():
            players.extend([self.player3_netid, self.player4_netid])
        return players


class Tournament(db.Model):
    __tablename__ = 'tournaments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    format = db.Column(db.String(50), nullable=False)  # single_elim, double_elim, round_robin
    status = db.Column(db.String(50), default='open', nullable=False, index=True)  # Index for filtering tournaments
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    
    # Relationships
    participants = db.relationship('TournamentParticipant', backref='tournament', lazy='dynamic', cascade='all, delete-orphan')
    games = db.relationship('Game', backref='tournament', lazy='dynamic')
    matches = db.relationship('TournamentMatch', backref='tournament', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return self.name
    
    def get_participant_count(self):
        return self.participants.count()
    
    def can_signup(self):
        return self.status == 'open'
    
    def can_report_results(self):
        return self.status == 'active'


class TournamentParticipant(db.Model):
    __tablename__ = 'tournament_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    user_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=False)
    self_rating = db.Column(db.Integer, nullable=False)  # 1-10 scale
    seed = db.Column(db.Integer, nullable=True)  # Assigned when tournament starts
    placement = db.Column(db.Integer, nullable=True)  # Final placement when tournament ends
    eliminated = db.Column(db.Boolean, default=False, nullable=False)  # For elimination tournaments
    
    __table_args__ = (
        db.UniqueConstraint('tournament_id', 'user_netid', name='unique_tournament_participant'),
    )
    
    def __repr__(self):
        return f'{self.user_netid} in {self.tournament.name}'


class TournamentMatch(db.Model):
    __tablename__ = 'tournament_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    match_number = db.Column(db.Integer, nullable=False)  # Position in round
    bracket = db.Column(db.String(50), nullable=False)  # 'winners', 'losers', 'main' (for single elim/round robin)
    player1_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=True)  # Can be null if TBD
    player2_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=True)
    winner_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'Match {self.match_number} (Round {self.round_number})'
    
    def is_ready(self):
        """Check if both players are assigned"""
        return self.player1_netid is not None and self.player2_netid is not None


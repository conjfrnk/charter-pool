from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    netid = db.Column(db.String(50), primary_key=True)
    first_name = db.Column(db.String(100), nullable=True)  # Nullable until user completes profile
    last_name = db.Column(db.String(100), nullable=True)   # Nullable until user completes profile
    elo_rating = db.Column(db.Integer, default=1200, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    archived = db.Column(db.Boolean, default=False, nullable=False)
    
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
        return not self.first_name or not self.last_name
    
    def get_all_games(self):
        """Get all games this user participated in"""
        return Game.query.filter(
            (Game.player1_netid == self.netid) | (Game.player2_netid == self.netid)
        ).order_by(Game.timestamp.desc()).all()
    
    def get_win_count(self):
        """Get number of games won"""
        return Game.query.filter(Game.winner_netid == self.netid).count()
    
    def get_loss_count(self):
        """Get number of games lost"""
        return Game.query.filter(
            ((Game.player1_netid == self.netid) | (Game.player2_netid == self.netid)) &
            (Game.winner_netid != self.netid)
        ).count()
    
    def get_win_rate(self):
        """Calculate win rate percentage"""
        total_games = len(self.get_all_games())
        if total_games == 0:
            return 0
        wins = self.get_win_count()
        return round((wins / total_games) * 100, 1)


class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    created_tournaments = db.relationship('Tournament', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return self.username


class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    player1_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=False)
    player2_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=False)
    winner_netid = db.Column(db.String(50), db.ForeignKey('users.netid'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=True)
    elo_change = db.Column(db.Integer, nullable=False)  # ELO change for the winner
    
    def __repr__(self):
        return f'Game {self.id}'
    
    def get_loser_netid(self):
        """Get the netid of the loser"""
        if self.winner_netid == self.player1_netid:
            return self.player2_netid
        return self.player1_netid


class Tournament(db.Model):
    __tablename__ = 'tournaments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    format = db.Column(db.String(50), nullable=False)  # single_elim, double_elim, round_robin
    status = db.Column(db.String(50), default='open', nullable=False)  # open, active, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
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


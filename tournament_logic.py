"""
Tournament bracket generation and management logic
Supports single elimination, double elimination, and round robin formats
"""
import math
from models import TournamentParticipant, TournamentMatch, Tournament, db

def seed_participants(tournament):
    """
    Seed participants based on a combination of self-rating and ELO
    - New players (few games): Weight self-rating more heavily
    - Experienced players (many games): Use ELO primarily
    """
    try:
        if not tournament:
            raise ValueError("Tournament cannot be None")
        
        participants = tournament.participants.all()
        if not participants:
            return []
    except Exception as e:
        print(f"[ERROR] Failed to get tournament participants: {e}")
        raise
    
    def calculate_seed_score(participant):
        """
        Calculate a composite score for seeding
        Returns higher score for better players
        """
        user = participant.user
        games_played = len(user.get_all_games())
        
        # Normalize self-rating to 0-1 scale (1-10 scale)
        self_rating_normalized = participant.self_rating / 10.0
        
        # Normalize ELO to approximate 0-1 scale (assuming 800-1600 range)
        # 1200 is default, so center around that
        elo_normalized = (user.elo_rating - 800) / 800.0
        elo_normalized = max(0, min(1, elo_normalized))  # Clamp to 0-1
        
        # Calculate weight based on games played
        # 0 games = 100% self-rating, 0% ELO
        # 10+ games = 10% self-rating, 90% ELO
        # Use sigmoid-like curve for smooth transition
        if games_played == 0:
            self_weight = 1.0
            elo_weight = 0.0
        elif games_played < 10:
            # Linear transition from 1.0 to 0.1 for self_weight
            self_weight = 1.0 - (games_played * 0.09)
            elo_weight = games_played * 0.09
        else:
            # After 10 games, heavily favor ELO
            self_weight = 0.1
            elo_weight = 0.9
        
        # Calculate composite score
        composite_score = (self_rating_normalized * self_weight) + (elo_normalized * elo_weight)
        
        return composite_score
    
    # Sort by composite score (descending) and then by signup time
    sorted_participants = sorted(
        participants,
        key=lambda p: (-calculate_seed_score(p), p.id)
    )
    
    # Assign seeds
    for i, participant in enumerate(sorted_participants, 1):
        participant.seed = i
    
    db.session.commit()
    return sorted_participants

def get_next_power_of_two(n):
    """Get the next power of 2 greater than or equal to n"""
    return 2 ** math.ceil(math.log2(n))

def create_single_elimination_bracket(tournament):
    """Create matches for single elimination tournament"""
    participants = seed_participants(tournament)
    n_participants = len(participants)
    
    if n_participants < 2:
        return False, "Need at least 2 participants"
    
    # Calculate bracket size (next power of 2)
    bracket_size = get_next_power_of_two(n_participants)
    n_rounds = int(math.log2(bracket_size))
    
    # Create first round matches with proper seeding
    # Standard bracket seeding: 1v16, 8v9, 4v13, 5v12, 2v15, 7v10, 3v14, 6v11
    seeding_order = generate_seeding_order(bracket_size)
    
    round_1_matches = []
    for i in range(0, len(seeding_order), 2):
        seed1 = seeding_order[i]
        seed2 = seeding_order[i + 1]
        
        # Get participants by seed (if they exist)
        player1 = next((p for p in participants if p.seed == seed1), None)
        player2 = next((p for p in participants if p.seed == seed2), None)
        
        match = TournamentMatch(
            tournament_id=tournament.id,
            round_number=1,
            match_number=(i // 2) + 1,
            bracket='main',
            player1_netid=player1.user_netid if player1 else None,
            player2_netid=player2.user_netid if player2 else None
        )
        round_1_matches.append(match)
        db.session.add(match)
    
    # Create placeholder matches for subsequent rounds
    for round_num in range(2, n_rounds + 1):
        n_matches = bracket_size // (2 ** round_num)
        for match_num in range(1, n_matches + 1):
            match = TournamentMatch(
                tournament_id=tournament.id,
                round_number=round_num,
                match_number=match_num,
                bracket='main'
            )
            db.session.add(match)
    
    db.session.commit()
    return True, "Single elimination bracket created"

def create_double_elimination_bracket(tournament):
    """Create matches for double elimination tournament"""
    participants = seed_participants(tournament)
    n_participants = len(participants)
    
    if n_participants < 2:
        return False, "Need at least 2 participants"
    
    bracket_size = get_next_power_of_two(n_participants)
    n_rounds = int(math.log2(bracket_size))
    
    # Create winners bracket (same as single elimination)
    seeding_order = generate_seeding_order(bracket_size)
    
    # Winners bracket round 1
    for i in range(0, len(seeding_order), 2):
        seed1 = seeding_order[i]
        seed2 = seeding_order[i + 1]
        
        player1 = next((p for p in participants if p.seed == seed1), None)
        player2 = next((p for p in participants if p.seed == seed2), None)
        
        match = TournamentMatch(
            tournament_id=tournament.id,
            round_number=1,
            match_number=(i // 2) + 1,
            bracket='winners',
            player1_netid=player1.user_netid if player1 else None,
            player2_netid=player2.user_netid if player2 else None
        )
        db.session.add(match)
    
    # Create placeholder matches for subsequent winners bracket rounds
    for round_num in range(2, n_rounds + 1):
        n_matches = bracket_size // (2 ** round_num)
        for match_num in range(1, n_matches + 1):
            match = TournamentMatch(
                tournament_id=tournament.id,
                round_number=round_num,
                match_number=match_num,
                bracket='winners'
            )
            db.session.add(match)
    
    # Create losers bracket (approximately same number of rounds)
    # Losers bracket has alternating rounds of different sizes
    for round_num in range(1, n_rounds * 2):
        # Simplified losers bracket structure
        if round_num == 1:
            n_matches = bracket_size // 4
        else:
            n_matches = max(1, bracket_size // (2 ** (round_num // 2 + 2)))
        
        for match_num in range(1, n_matches + 1):
            match = TournamentMatch(
                tournament_id=tournament.id,
                round_number=round_num,
                match_number=match_num,
                bracket='losers'
            )
            db.session.add(match)
    
    # Create grand finals match
    match = TournamentMatch(
        tournament_id=tournament.id,
        round_number=1,
        match_number=1,
        bracket='grand_finals'
    )
    db.session.add(match)
    
    db.session.commit()
    return True, "Double elimination bracket created"

def create_round_robin_matches(tournament):
    """Create all matches for round robin tournament"""
    participants = seed_participants(tournament)
    n_participants = len(participants)
    
    if n_participants < 2:
        return False, "Need at least 2 participants"
    
    # Create matches for every pair of participants
    match_num = 1
    for i in range(n_participants):
        for j in range(i + 1, n_participants):
            match = TournamentMatch(
                tournament_id=tournament.id,
                round_number=1,  # All matches are in "round 1" for round robin
                match_number=match_num,
                bracket='main',
                player1_netid=participants[i].user_netid,
                player2_netid=participants[j].user_netid
            )
            db.session.add(match)
            match_num += 1
    
    db.session.commit()
    return True, f"Round robin schedule created with {match_num - 1} matches"

def generate_seeding_order(bracket_size):
    """
    Generate standard tournament seeding order
    For 8 players: [1, 8, 4, 5, 2, 7, 3, 6]
    For 16 players: [1, 16, 8, 9, 4, 13, 5, 12, 2, 15, 7, 10, 3, 14, 6, 11]
    """
    rounds = int(math.log2(bracket_size))
    seeds = [1, 2]
    
    for _ in range(rounds - 1):
        new_seeds = []
        for seed in seeds:
            new_seeds.append(seed)
            new_seeds.append(bracket_size + 1 - seed)
        seeds = new_seeds
        bracket_size //= 2
    
    return seeds

def activate_tournament(tournament):
    """
    Activate a tournament and generate its bracket
    """
    try:
        if not tournament:
            return False, "Tournament not found"
        
        if tournament.status != 'open':
            return False, "Tournament must be in 'open' status to activate"
        
        participant_count = tournament.get_participant_count()
        if participant_count < 2:
            return False, "Need at least 2 participants to start tournament"
    except Exception as e:
        print(f"[ERROR] Error checking tournament activation requirements: {e}")
        return False, f"Error activating tournament: {str(e)}"
    
    # Generate bracket based on format
    try:
        if tournament.format == 'single_elim':
            success, message = create_single_elimination_bracket(tournament)
        elif tournament.format == 'double_elim':
            success, message = create_double_elimination_bracket(tournament)
        elif tournament.format == 'round_robin':
            success, message = create_round_robin_matches(tournament)
        else:
            return False, f"Unknown tournament format: {tournament.format}"
        
        if success:
            tournament.status = 'active'
            db.session.commit()
            return True, f"Tournament activated. {message}"
        
        return False, message
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error generating tournament bracket: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error generating bracket: {str(e)}"

def report_match_result(match, winner_netid, game_id):
    """
    Report the result of a tournament match
    Updates the match and advances bracket
    """
    try:
        if not match:
            return False, "Match not found"
        
        if match.completed:
            return False, "This match has already been completed"
        
        if not match.is_ready():
            return False, "Both players must be assigned before reporting result"
        
        if not winner_netid or winner_netid not in [match.player1_netid, match.player2_netid]:
            return False, "Winner must be one of the match participants"
    except Exception as e:
        print(f"[ERROR] Error validating match result: {e}")
        return False, f"Error validating match: {str(e)}"
    
    # Update match
    try:
        match.winner_netid = winner_netid
        match.game_id = game_id
        match.completed = True
        
        # Advance bracket
        tournament = match.tournament
        if not tournament:
            return False, "Tournament not found"
        
        loser_netid = match.player1_netid if winner_netid == match.player2_netid else match.player2_netid
        
        if tournament.format == 'single_elim':
            advance_single_elimination(match, winner_netid, loser_netid)
        elif tournament.format == 'double_elim':
            advance_double_elimination(match, winner_netid, loser_netid)
        # Round robin doesn't need advancement, all matches are predetermined
        
        db.session.commit()
        
        # Check if tournament is complete
        check_tournament_completion(tournament)
        
        return True, "Match result recorded"
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error reporting match result: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error recording match: {str(e)}"

def advance_single_elimination(match, winner_netid, loser_netid):
    """Advance winner to next round in single elimination"""
    tournament = match.tournament
    
    # Mark loser as eliminated
    loser = TournamentParticipant.query.filter_by(
        tournament_id=tournament.id,
        user_netid=loser_netid
    ).first()
    if loser:
        loser.eliminated = True
    
    # Find next match for winner
    next_round = match.round_number + 1
    next_match_number = (match.match_number + 1) // 2
    
    next_match = TournamentMatch.query.filter_by(
        tournament_id=tournament.id,
        round_number=next_round,
        match_number=next_match_number,
        bracket='main'
    ).first()
    
    if next_match:
        # Assign winner to next match
        if match.match_number % 2 == 1:  # Odd match goes to player1
            next_match.player1_netid = winner_netid
        else:  # Even match goes to player2
            next_match.player2_netid = winner_netid

def advance_double_elimination(match, winner_netid, loser_netid):
    """Advance players in double elimination (winners to winners, losers to losers)"""
    tournament = match.tournament
    
    if match.bracket == 'winners':
        # Winner advances in winners bracket
        next_round = match.round_number + 1
        next_match_number = (match.match_number + 1) // 2
        
        next_match = TournamentMatch.query.filter_by(
            tournament_id=tournament.id,
            round_number=next_round,
            bracket='winners'
        ).first()
        
        if next_match:
            if match.match_number % 2 == 1:
                next_match.player1_netid = winner_netid
            else:
                next_match.player2_netid = winner_netid
        else:
            # Winners bracket complete, advance to grand finals
            grand_finals = TournamentMatch.query.filter_by(
                tournament_id=tournament.id,
                bracket='grand_finals'
            ).first()
            if grand_finals and not grand_finals.player1_netid:
                grand_finals.player1_netid = winner_netid
        
        # Loser drops to losers bracket
        loser_match = find_next_losers_bracket_slot(tournament, match.round_number)
        if loser_match:
            if not loser_match.player1_netid:
                loser_match.player1_netid = loser_netid
            else:
                loser_match.player2_netid = loser_netid
    
    elif match.bracket == 'losers':
        # Winner advances in losers bracket
        next_loser_match = find_next_losers_bracket_match(tournament, match)
        if next_loser_match:
            if not next_loser_match.player1_netid:
                next_loser_match.player1_netid = winner_netid
            else:
                next_loser_match.player2_netid = winner_netid
        else:
            # Losers bracket complete, advance to grand finals
            grand_finals = TournamentMatch.query.filter_by(
                tournament_id=tournament.id,
                bracket='grand_finals'
            ).first()
            if grand_finals and not grand_finals.player2_netid:
                grand_finals.player2_netid = winner_netid
        
        # Loser is eliminated
        participant = TournamentParticipant.query.filter_by(
            tournament_id=tournament.id,
            user_netid=loser_netid
        ).first()
        if participant:
            participant.eliminated = True

def find_next_losers_bracket_slot(tournament, winners_round):
    """Find the appropriate losers bracket match for a player dropping from winners"""
    # Simplified logic - find first available slot in losers bracket
    losers_matches = TournamentMatch.query.filter_by(
        tournament_id=tournament.id,
        bracket='losers',
        completed=False
    ).order_by(TournamentMatch.round_number, TournamentMatch.match_number).all()
    
    for match in losers_matches:
        if not match.player1_netid or not match.player2_netid:
            return match
    
    return None

def find_next_losers_bracket_match(tournament, current_match):
    """Find the next losers bracket match"""
    next_match = TournamentMatch.query.filter_by(
        tournament_id=tournament.id,
        bracket='losers',
        round_number=current_match.round_number + 1,
        completed=False
    ).first()
    
    return next_match

def check_tournament_completion(tournament):
    """Check if tournament is complete and assign placements"""
    incomplete_matches = TournamentMatch.query.filter_by(
        tournament_id=tournament.id,
        completed=False
    ).count()
    
    if incomplete_matches == 0:
        tournament.status = 'completed'
        assign_placements(tournament)
        db.session.commit()

def assign_placements(tournament):
    """Assign final placements to tournament participants"""
    if tournament.format == 'round_robin':
        # Count wins for each participant
        participants = tournament.participants.all()
        standings = []
        
        for participant in participants:
            wins = TournamentMatch.query.filter_by(
                tournament_id=tournament.id,
                winner_netid=participant.user_netid
            ).count()
            standings.append((participant, wins))
        
        # Sort by wins (descending)
        standings.sort(key=lambda x: -x[1])
        
        # Assign placements
        for i, (participant, wins) in enumerate(standings, 1):
            participant.placement = i
    
    else:  # Elimination tournaments
        # Winner is the last uneliminated player or grand finals winner
        if tournament.format == 'double_elim':
            grand_finals = TournamentMatch.query.filter_by(
                tournament_id=tournament.id,
                bracket='grand_finals'
            ).first()
            if grand_finals and grand_finals.completed:
                winner_netid = grand_finals.winner_netid
                winner = TournamentParticipant.query.filter_by(
                    tournament_id=tournament.id,
                    user_netid=winner_netid
                ).first()
                if winner:
                    winner.placement = 1
        else:  # single_elim
            # Find the winner (last match in highest round)
            final_match = TournamentMatch.query.filter_by(
                tournament_id=tournament.id,
                bracket='main'
            ).order_by(TournamentMatch.round_number.desc()).first()
            
            if final_match and final_match.completed:
                winner = TournamentParticipant.query.filter_by(
                    tournament_id=tournament.id,
                    user_netid=final_match.winner_netid
                ).first()
                if winner:
                    winner.placement = 1


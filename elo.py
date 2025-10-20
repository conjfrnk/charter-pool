"""
ELO Rating System for Pool Games

Standard ELO calculation with K-factor of 32
"""
import math

def calculate_expected_score(rating_a, rating_b):
    """
    Calculate the expected score for player A against player B
    Returns a value between 0 and 1
    """
    return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

def calculate_elo_change(winner_rating, loser_rating, k_factor=32):
    """
    Calculate the ELO rating change for both players after a game
    
    Args:
        winner_rating: Current ELO rating of the winner
        loser_rating: Current ELO rating of the loser
        k_factor: K-factor for ELO calculation (default 32)
    
    Returns:
        Tuple of (winner_change, loser_change) - loser_change will be negative
    """
    expected_winner = calculate_expected_score(winner_rating, loser_rating)
    expected_loser = calculate_expected_score(loser_rating, winner_rating)
    
    # Winner gets 1 point (win), loser gets 0 points (loss)
    winner_change = round(k_factor * (1 - expected_winner))
    loser_change = round(k_factor * (0 - expected_loser))
    
    return winner_change, loser_change

def update_ratings_after_game(winner, loser, k_factor=32):
    """
    Update ELO ratings for both players after a game
    
    Args:
        winner: User object (winner)
        loser: User object (loser)
        k_factor: K-factor for ELO calculation
    
    Returns:
        The ELO change amount (positive integer for winner)
    """
    try:
        # Validate inputs
        if not winner or not loser:
            raise ValueError("Both winner and loser must be provided")
        
        if not hasattr(winner, 'elo_rating') or not hasattr(loser, 'elo_rating'):
            raise ValueError("Players must have elo_rating attribute")
        
        winner_change, loser_change = calculate_elo_change(
            winner.elo_rating,
            loser.elo_rating,
            k_factor
        )
        
        winner.elo_rating += winner_change
        loser.elo_rating += loser_change
        
        return winner_change
    except Exception as e:
        print(f"[ERROR] Failed to update ratings: {e}")
        raise

def calculate_team_average_rating(player1_rating, player2_rating):
    """
    Calculate the average rating for a team of 2 players
    
    Args:
        player1_rating: ELO rating of first player
        player2_rating: ELO rating of second player
    
    Returns:
        Average rating (rounded to nearest integer)
    """
    return round((player1_rating + player2_rating) / 2)

def update_ratings_after_doubles_game(team1_players, team2_players, winning_team, k_factor=32):
    """
    Update ELO ratings for all 4 players after a doubles game
    Uses team average rating for calculation
    
    Args:
        team1_players: List of 2 User objects (team 1)
        team2_players: List of 2 User objects (team 2)
        winning_team: Either 1 or 2 (which team won)
        k_factor: K-factor for ELO calculation (default 32)
    
    Returns:
        The ELO change amount (positive integer for winners)
    """
    try:
        # Validate inputs
        if not team1_players or len(team1_players) != 2:
            raise ValueError("Team 1 must have exactly 2 players")
        if not team2_players or len(team2_players) != 2:
            raise ValueError("Team 2 must have exactly 2 players")
        if winning_team not in [1, 2]:
            raise ValueError("Winning team must be 1 or 2")
        
        # Validate all players have elo_rating
        for player in team1_players + team2_players:
            if not player or not hasattr(player, 'elo_rating'):
                raise ValueError("All players must have elo_rating attribute")
        
        # Calculate team average ratings
        team1_avg = calculate_team_average_rating(
            team1_players[0].elo_rating,
            team1_players[1].elo_rating
        )
        team2_avg = calculate_team_average_rating(
            team2_players[0].elo_rating,
            team2_players[1].elo_rating
        )
    except Exception as e:
        print(f"[ERROR] Failed to validate doubles game inputs: {e}")
        raise
    
    # Calculate ELO changes based on team averages
    if winning_team == 1:
        winner_change, loser_change = calculate_elo_change(team1_avg, team2_avg, k_factor)
        # Apply changes to team 1 (winners)
        team1_players[0].elo_rating += winner_change
        team1_players[1].elo_rating += winner_change
        # Apply changes to team 2 (losers)
        team2_players[0].elo_rating += loser_change
        team2_players[1].elo_rating += loser_change
    else:  # winning_team == 2
        winner_change, loser_change = calculate_elo_change(team2_avg, team1_avg, k_factor)
        # Apply changes to team 2 (winners)
        team2_players[0].elo_rating += winner_change
        team2_players[1].elo_rating += winner_change
        # Apply changes to team 1 (losers)
        team1_players[0].elo_rating += loser_change
        team1_players[1].elo_rating += loser_change
    
    return abs(winner_change)


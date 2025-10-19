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
    winner_change, loser_change = calculate_elo_change(
        winner.elo_rating,
        loser.elo_rating,
        k_factor
    )
    
    winner.elo_rating += winner_change
    loser.elo_rating += loser_change
    
    return winner_change


# Doubles Feature Implementation

## Overview

The Charter Pool ELO ranking system now supports both **Singles (1v1)** and **Doubles (2v2)** games. Players maintain a single unified ELO rating that applies to both game types.

## Features

### Singles Games (1v1)
- Original functionality preserved
- One player vs one player
- Winner takes ELO points from loser

### Doubles Games (2v2)
- Four players total (two teams of two)
- Team 1 (you + partner) vs Team 2 (two opponents)
- ELO calculated using team average rating
- All players on winning team gain ELO
- All players on losing team lose ELO

## ELO Calculation for Doubles

For doubles games, the system uses **team average rating**:

1. Calculate Team 1 average: `(Player1 ELO + Player2 ELO) / 2`
2. Calculate Team 2 average: `(Player3 ELO + Player4 ELO) / 2`
3. Use standard ELO formula with team averages
4. Apply the same ELO change to both players on each team

### Example
- Team 1: Alice (1300) & Bob (1200) → Team Average: 1250
- Team 2: Carol (1280) & Dave (1220) → Team Average: 1250
- If Team 1 wins, both Alice and Bob gain the same amount (e.g., +16 each)
- Carol and Dave both lose the same amount (e.g., -16 each)

## Database Changes

New columns added to the `games` table:
- `game_type` (VARCHAR): 'singles' or 'doubles'
- `player3_netid` (VARCHAR): Team 2, Player 1 (for doubles only)
- `player4_netid` (VARCHAR): Team 2, Player 2 (for doubles only)

For singles games, `player3_netid` and `player4_netid` remain NULL.

## Migration Instructions

### Running the Migration

To add doubles support to your existing database:

```bash
# Activate your virtual environment
source venv/bin/activate

# Run the migration script
python migrate_add_doubles.py
```

The migration script will:
1. Check if columns already exist
2. Add `game_type`, `player3_netid`, and `player4_netid` columns
3. Set default value 'singles' for existing games
4. Verify the migration succeeded

### Migration Safety

- The script checks for existing columns before attempting to add them
- All existing games are automatically marked as 'singles'
- The migration can be safely re-run (it's idempotent)
- Transaction-based: rolls back on error

## Using the Doubles Feature

### Reporting a Doubles Game

1. Navigate to "Report Game Result"
2. Select "Doubles (2v2)" as the game type
3. Enter your partner (Team 1)
4. Enter both opponents (Team 2)
5. Select which team won
6. Submit

### Viewing Game History

- Game history displays both singles and doubles games
- Doubles games show:
  - Badge indicating "Doubles"
  - All 4 players with team groupings
  - Winning team highlighted
- Singles games display as before

### Leaderboard

- Single unified leaderboard for all players
- ELO rating reflects performance in both singles and doubles
- Win/loss counts include both game types

## API/Data Structure

### Game Model

```python
class Game(db.Model):
    game_type = 'singles' | 'doubles'
    player1_netid  # Team 1, Player 1 (always present)
    player2_netid  # Team 1, Player 2 (partner in doubles, opponent in singles)
    player3_netid  # Team 2, Player 1 (doubles only)
    player4_netid  # Team 2, Player 2 (doubles only)
    winner_netid   # One player from winning team/player
```

### Helper Methods

- `game.is_doubles()` - Check if game is doubles
- `game.get_team1_netids()` - Get Team 1 player IDs
- `game.get_team2_netids()` - Get Team 2 player IDs (or [] for singles)
- `game.get_winning_team_netids()` - Get all winners
- `game.get_losing_team_netids()` - Get all losers

## Tournaments

**Note:** Tournaments currently remain **singles-only**. The tournament system has not been modified to support doubles brackets. Only casual doubles games can be reported.

## Testing

To test the doubles feature:

1. Run the migration
2. Create/login with test users
3. Report a doubles game with 4 different players
4. Verify ELO changes are equal for teammates
5. Check game history displays correctly
6. Verify leaderboard includes both game types

## Rollback (if needed)

If you need to remove doubles support:

```sql
ALTER TABLE games DROP COLUMN game_type;
ALTER TABLE games DROP COLUMN player3_netid;
ALTER TABLE games DROP COLUMN player4_netid;
```

**Warning:** This will permanently delete all doubles game data!


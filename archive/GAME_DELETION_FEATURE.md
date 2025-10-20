# Game Deletion Feature

## Overview
Users can now delete their own recent games in case they make an error when reporting game results. This feature helps correct mistakes without requiring administrator intervention.

## Implementation Date
October 20, 2025

## Features

### User-Facing
- **Delete Button**: Visible on game history page for eligible games
- **Time Limit**: Games can only be deleted within 15 minutes of creation
- **Participant Restriction**: Users can only delete games they participated in
- **Tournament Protection**: Tournament games cannot be deleted
- **Confirmation Dialog**: Prevents accidental deletions
- **Visual Feedback**: Delete button only shows for eligible games, disabled state for ineligible games

### Backend Logic
- **ELO Reversal**: Automatically reverses ELO changes for all players
- **Singles Games**: Reverses winner's gain and loser's loss
- **Doubles Games**: Reverses ELO changes for all 4 players on both teams
- **Error Handling**: Transaction rollback on failure
- **Security Validation**: Multiple checks ensure only valid deletions occur

## Files Modified

### 1. `/app.py`
- Added `delete_game(game_id)` route at line 349
- Added `inject_utility_functions()` context processor at line 1021
- Provides `now()` function to templates for time calculations

### 2. `/templates/game_history.html`
- Added "Actions" column to game history table
- Added delete form with confirmation for eligible games
- Added visual indicator for ineligible games
- Added CSS styling for delete button
- Added JavaScript confirmation dialog

### 3. `/README.md`
- Added "Game Deletion" section under Game Management
- Updated API endpoints to include delete route
- Documented all deletion rules and restrictions

## Validation Rules

### A game can be deleted if:
1. ✅ Current user is not an admin (admins should use database tools)
2. ✅ User participated in the game (player1, player2, player3, or player4)
3. ✅ Game is not a tournament game (tournament_id is NULL)
4. ✅ Game was created within the last 15 minutes

### Error Messages
- **Admin attempt**: "Admins cannot delete games from this view..."
- **Non-participant**: "You can only delete games you participated in."
- **Tournament game**: "Tournament games cannot be deleted."
- **Too old**: "You can only delete games within 15 minutes of creation."
- **Success**: "Game deleted successfully. ELO ratings have been reversed."

## ELO Reversal Logic

### Singles Games
```python
winner.elo_rating -= game.elo_change  # Remove winner's gain
loser.elo_rating += game.elo_change   # Remove loser's loss
```

### Doubles Games
```python
# Team 1 won scenario
player1.elo_rating -= game.elo_change  # Remove gains
player2.elo_rating -= game.elo_change
player3.elo_rating += game.elo_change  # Remove losses
player4.elo_rating += game.elo_change

# Team 2 won scenario (reverse of above)
```

## User Experience

### Game History Page
1. User views game history at `/games/history`
2. Recent games (< 15 min) show a red "🗑️ Delete" button
3. Older games or tournament games show "—" with tooltip explanation
4. Clicking delete shows confirmation dialog
5. On confirmation, game is deleted and ELO is reversed
6. Success message appears and page refreshes

### Confirmation Dialog
```
Are you sure you want to delete this game? 
This will reverse the ELO changes for all players.
```

## Technical Details

### Route
```
POST /games/<int:game_id>/delete
```

### Permissions
- Requires login (`@login_required`)
- User-only (admins blocked)
- Participant validation
- Time-based validation

### Database Operations
1. Query game by ID (404 if not found)
2. Validate all deletion rules
3. Load all player objects
4. Calculate and apply ELO reversals
5. Delete game record
6. Commit transaction
7. Rollback on error

### Template Context
- `now()` function available via context processor
- Calculates time difference in template
- Determines button visibility dynamically

## Testing Checklist

- [ ] User can delete own recent game (< 15 min)
- [ ] User cannot delete old game (> 15 min)
- [ ] User cannot delete tournament game
- [ ] User cannot delete game they didn't play in
- [ ] Admin cannot delete games from this view
- [ ] ELO correctly reversed for singles games
- [ ] ELO correctly reversed for doubles games
- [ ] Confirmation dialog appears
- [ ] Success message displays
- [ ] Error messages display appropriately
- [ ] Page refreshes after deletion
- [ ] Delete button only shows for eligible games

## Future Enhancements (Optional)

1. **Admin Override**: Allow admins to delete any game with special confirmation
2. **Audit Log**: Track game deletions for accountability
3. **Extended Window**: Make time limit configurable (env variable)
4. **Bulk Delete**: Allow deleting multiple games at once
5. **Undo Feature**: Add ability to restore recently deleted games
6. **Notification**: Notify other players when shared game is deleted

## Security Considerations

- ✅ User authentication required
- ✅ Participant verification prevents unauthorized deletions
- ✅ Time restriction limits abuse
- ✅ Tournament protection maintains competitive integrity
- ✅ Transaction rollback prevents partial deletions
- ✅ XSS protection via Jinja2 escaping
- ✅ CSRF protection via Flask session tokens

## Performance Impact

- **Minimal**: Single database query + delete operation
- **ELO Updates**: O(n) where n = number of players (2 or 4)
- **No indices needed**: Uses existing primary key and foreign keys
- **Transaction-safe**: Rollback on any error

## Maintenance Notes

- Time limit constant: 900 seconds (15 minutes) in line 372 of app.py
- Can be adjusted by changing the comparison value
- ELO reversal logic must match the ELO calculation logic in elo.py
- Template requires `now()` function from context processor


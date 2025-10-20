-- Fix Charter Pool database - add is_active column
-- Run this with: psql -U charter_pool -d charter_pool -f fix_database.sql

-- Check if column exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='is_active'
    ) THEN
        -- Add the is_active column
        ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT FALSE;
        
        -- Set is_active to TRUE for users who have completed their profile
        UPDATE users 
        SET is_active = TRUE 
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL;
        
        RAISE NOTICE 'Successfully added is_active column and updated existing users';
    ELSE
        RAISE NOTICE 'Column is_active already exists - no changes needed';
    END IF;
END $$;

-- Show results
SELECT 
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_users,
    COUNT(*) FILTER (WHERE is_active = FALSE) as inactive_users,
    COUNT(*) as total_users
FROM users
WHERE archived = FALSE;


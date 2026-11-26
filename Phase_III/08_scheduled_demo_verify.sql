-- Read-only verification after manual install. Demo view must contain exactly
-- the three requested fixtures, SCHEDULED, Synthetic demonstration, in UTC.
SELECT * FROM tl_demo_v_scheduled_fixtures ORDER BY kickoff_at,match_id;
SELECT COUNT(*) AS demo_seasons FROM tl_demo_seasons;
SELECT COUNT(*) AS demo_memberships FROM tl_demo_season_teams;
SELECT COUNT(*) AS demo_fixtures FROM tl_demo_fixtures;
-- Expect 1 season, 6 memberships, 3 fixtures. IDs are generated, not 73-75.
-- Expect zero duplicate rows and zero invalid membership rows.
SELECT season_id,home_team_id,away_team_id,kickoff_at,COUNT(*) AS copies
 FROM tl_demo_fixtures GROUP BY season_id,home_team_id,away_team_id,kickoff_at HAVING COUNT(*)>1;
SELECT f.match_id FROM tl_demo_fixtures f
 LEFT JOIN tl_demo_season_teams h ON h.season_id=f.season_id AND h.team_id=f.home_team_id
 LEFT JOIN tl_demo_season_teams a ON a.season_id=f.season_id AND a.team_id=f.away_team_id
 WHERE h.team_id IS NULL OR a.team_id IS NULL;
-- Compare all following counts with preflight: no differences.
SELECT COUNT(*) AS original_matches FROM matches;
SELECT COUNT(*) AS provider_mappings FROM provider_matches;
SELECT COUNT(*) AS provider_player_statistics FROM provider_player_stats;
SELECT COUNT(*) AS current_scheduled FROM tl_v_scheduled_fixtures;
SELECT COUNT(*) AS original_scheduled FROM v_scheduled_fixtures;
-- Expected 20 base tables and 26 views on the existing 17-table/25-view installation.
SELECT TABLE_TYPE,COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() GROUP BY TABLE_TYPE;
-- For idempotency verification, repeat 08 after inspecting objects; run this
-- file again and confirm the same three IDs and counts. Never delete test rows.

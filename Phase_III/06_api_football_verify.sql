-- READ ONLY. Run after an approved migration, BEFORE enabling API-Football or importing.
USE group12_football_phase2;
SELECT table_type,COUNT(*) AS object_count FROM information_schema.tables
 WHERE table_schema=DATABASE() GROUP BY table_type;
-- Expected: 17 base tables, 25 views (10 original + 5 helpers + 10 scoped).
SELECT 'matches' AS entity,COUNT(*) AS row_count FROM matches
 UNION ALL SELECT 'imported_matches',COUNT(*) FROM imported_matches
 UNION ALL SELECT 'teams',COUNT(*) FROM teams
 UNION ALL SELECT 'players',COUNT(*) FROM players
 UNION ALL SELECT 'player_match_stats',COUNT(*) FROM player_match_stats
 UNION ALL SELECT 'users',COUNT(*) FROM users
 UNION ALL SELECT 'login_credentials',COUNT(*) FROM login_credentials
 UNION ALL SELECT 'web_sessions',COUNT(*) FROM web_sessions
 UNION ALL SELECT 'seasons',COUNT(*) FROM seasons
 UNION ALL SELECT 'season_teams',COUNT(*) FROM season_teams;
-- Compare with preflight: ONLY seasons +1 and season_teams +6. All other counts unchanged.
SELECT COUNT(*) AS missing_or_changed_legacy_links FROM imported_matches i
 LEFT JOIN provider_matches p ON p.provider='football-data.org' AND p.external_id=i.external_id
 WHERE p.match_id IS NULL OR p.match_id<>i.match_id;
-- Require zero; 30 legacy namespace links below, zero API-Football links before import.
SELECT provider,COUNT(*) AS links FROM provider_matches GROUP BY provider;
SELECT s.season_id,s.season_label,s.start_date,s.end_date,t.team_name
 FROM tl_seasons s JOIN tl_season_teams st USING(season_id) JOIN teams t USING(team_id);
-- Exactly six rows; separate 2023/24 season, dates 2023-07-01 through 2024-06-30.
SELECT * FROM tl_v_match_details LIMIT 1;
SELECT * FROM tl_v_above_any_team_goal_total LIMIT 1;
SELECT * FROM tl_v_players_with_goals LIMIT 1;
SELECT * FROM tl_v_match_stat_coverage LIMIT 1;
SELECT * FROM tl_v_goal_or_assist_players LIMIT 1;
SELECT * FROM tl_v_league_standings;
SELECT * FROM tl_v_player_totals LIMIT 1;
SELECT * FROM tl_v_match_results LIMIT 1;
SELECT * FROM tl_v_scheduled_fixtures LIMIT 1;
SELECT * FROM tl_v_team_home_away LIMIT 1;
-- Nine scoped reports empty; standings show six clubs with zero played/points before import.
-- Original views must still execute; definitions unchanged, results can include new memberships.
SELECT COUNT(*) FROM v_match_details;
SELECT COUNT(*) FROM v_above_any_team_goal_total;
SELECT COUNT(*) FROM v_players_with_goals;
SELECT COUNT(*) FROM v_match_stat_coverage;
SELECT COUNT(*) FROM v_goal_or_assist_players;
SELECT COUNT(*) FROM v_league_standings;
SELECT COUNT(*) FROM v_player_totals;
SELECT COUNT(*) FROM v_match_results;
SELECT COUNT(*) FROM v_scheduled_fixtures;
SELECT COUNT(*) FROM v_team_home_away;

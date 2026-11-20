-- READ ONLY. Run in Workbench before approving 06_api_football.sql.
-- Stop Flask and all other writers first. Review every result; this is not an automatic gate.
USE group12_football_phase2;
SELECT DATABASE() AS target_schema, VERSION() AS mysql_version, @@foreign_key_checks AS fk_checks;
-- Require MySQL >= 8.0.16 (not MariaDB), fk_checks=1, correct target schema.
SELECT table_type, COUNT(*) AS object_count FROM information_schema.tables
 WHERE table_schema=DATABASE() GROUP BY table_type;
-- Expected starting state: 11 base tables and 10 views.
SELECT table_name,table_type FROM information_schema.tables
 WHERE table_schema=DATABASE() AND (LEFT(table_name,9)='provider_' OR LEFT(table_name,3)='tl_');
-- Must return ZERO rows. Existing objects or a partial migration require separate review.
SELECT competition_id,competition_name,competition_type,country FROM competitions
 WHERE competition_name='Premier League';
-- Exactly one row, LEAGUE, England.
SELECT team_id,team_name FROM teams WHERE team_name IN
 ('Arsenal','Chelsea','Liverpool','Manchester City','Manchester United','Tottenham Hotspur');
-- Exactly six rows, matching names. Also expect six clubs total below.
SELECT s.season_id,s.season_label,s.start_date,s.end_date FROM seasons s
 JOIN competitions c USING(competition_id)
 WHERE c.competition_name='Premier League' AND s.season_label='2023/24';
-- Must return ZERO rows for this first-run migration.
SELECT MAX(season_id) AS highest_season_id FROM seasons;
-- Must be less than 2147483647; all writers must remain stopped during allocation.
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
-- Save these counts privately. imported_matches=30; all other baseline records must survive.
SELECT COUNT(*) AS orphan_legacy_links FROM imported_matches i
 LEFT JOIN matches m USING(match_id) WHERE m.match_id IS NULL;
-- Require zero.
SELECT s.season_label,COUNT(*) AS linked_matches FROM imported_matches i
 JOIN matches m USING(match_id) JOIN seasons s USING(season_id) GROUP BY s.season_label;
-- Expected existing provider data: 30 links in 2025/26. Review discrepancies.
SELECT COUNT(*) AS trigger_count FROM information_schema.triggers WHERE trigger_schema=DATABASE();
-- Expected zero. Have the migration administrator verify sufficient TRIGGER privilege to see all triggers.
SELECT table_name,engine FROM information_schema.tables
 WHERE table_schema=DATABASE() AND table_type='BASE TABLE';
-- Require InnoDB. Schema/FK type compatibility was checked against the supplied backup;
-- if the live schema changed since that backup, review it again before execution.

-- Read-only. Select YOUR target Touchline schema in Workbench first.
-- Require the intended database, MySQL 8.0.16+, and authorized CREATE TABLE/VIEW
-- privileges (DROP on the new demo view for CREATE OR REPLACE); do not expand app grants.
SELECT DATABASE() AS selected_schema,VERSION() AS mysql_version;
SHOW GRANTS FOR CURRENT_USER;
-- Require exactly six distinct named clubs, with existing INT team IDs.
SELECT team_id,team_name FROM teams WHERE team_name IN
 ('Arsenal','Chelsea','Liverpool','Manchester City','Manchester United','Tottenham Hotspur');
SHOW CREATE TABLE teams;
-- First run: zero rows. Rerun: three demo tables plus one demo view.
-- If objects already exist, inspect SHOW CREATE for each and compare with 08.
-- STOP for incompatible definitions, unrecognized data, or unexpected clubs/dates.
SELECT TABLE_NAME,TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()
 AND TABLE_NAME IN ('tl_demo_seasons','tl_demo_season_teams','tl_demo_fixtures','tl_demo_v_scheduled_fixtures');
-- Save counts; require unchanged after seed (with writers paused).
SELECT COUNT(*) AS original_matches FROM matches;
SELECT COUNT(*) AS provider_mappings FROM provider_matches;
SELECT COUNT(*) AS provider_player_statistics FROM provider_player_stats;
SELECT COUNT(*) AS current_scheduled FROM tl_v_scheduled_fixtures;
SELECT COUNT(*) AS original_scheduled FROM v_scheduled_fixtures;

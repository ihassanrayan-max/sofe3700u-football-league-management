-- Read-only. Select group12_football_phase2 as Workbench's default schema first.
-- Require database_matches=1 and MySQL 8; stop otherwise.
SELECT DATABASE() AS selected_schema, DATABASE()='group12_football_phase2' AS database_matches, VERSION() AS mysql_version;
SHOW GRANTS FOR CURRENT_USER;
-- Require four VIEW rows below. Save SHOW CREATE output privately for reference.
SELECT TABLE_NAME,TABLE_TYPE FROM information_schema.TABLES
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN
 ('tl_v_player_totals','tl_players','tl_player_match_stats','tl_matches');
SHOW CREATE VIEW group12_football_phase2.tl_v_player_totals;
-- Require zero duplicate rows. Existing helper view must still use minutes>0.
SELECT match_id,player_id,COUNT(*) AS copies FROM group12_football_phase2.tl_player_match_stats
 GROUP BY match_id,player_id HAVING COUNT(*)>1;
SHOW CREATE VIEW group12_football_phase2.tl_player_match_stats;
-- Save counts and compare after migration (pause other imports/edits first).
SELECT COUNT(*) AS stats_rows, SUM(goals) AS known_goals, SUM(assists) AS known_assists
 FROM group12_football_phase2.provider_player_stats;
SELECT COUNT(*) AS fixtures FROM group12_football_phase2.matches;
-- Proposed subtotals before any change. NULL-only groups remain NULL.
SELECT p.player_id,p.full_name,COUNT(s.match_id) AS appearances,
 SUM(s.goals) AS known_goals,COUNT(s.goals) AS known_goal_appearances,
 COUNT(s.match_id)-COUNT(s.goals) AS unknown_goal_appearances,
 SUM(s.assists) AS known_assists,COUNT(s.assists) AS known_assist_appearances,
 COUNT(s.match_id)-COUNT(s.assists) AS unknown_assist_appearances
 FROM group12_football_phase2.tl_players p
 JOIN group12_football_phase2.tl_player_match_stats s USING(player_id)
 GROUP BY p.player_id,p.full_name;

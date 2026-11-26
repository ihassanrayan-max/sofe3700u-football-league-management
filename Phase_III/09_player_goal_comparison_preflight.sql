-- Read-only. Confirm intended schema and MySQL 8. Save existing view privately.
SELECT DATABASE() AS selected_schema,VERSION() AS mysql_version;
SHOW GRANTS FOR CURRENT_USER;
SHOW CREATE VIEW tl_v_above_any_team_goal_total;
SHOW CREATE VIEW tl_players;
SHOW CREATE VIEW tl_player_match_stats;
-- No duplicate appearances should be returned.
SELECT match_id,player_id,COUNT(*) copies FROM tl_player_match_stats
 GROUP BY match_id,player_id HAVING COUNT(*)>1;
-- Known subtotals, not scoreboard/full-season totals; NULL is not zero.
SELECT p.team_id,t.team_name,SUM(s.goals) known_goals,COUNT(*) appearances,COUNT(s.goals) known_values
 FROM tl_players p JOIN teams t USING(team_id) JOIN tl_player_match_stats s USING(player_id)
 GROUP BY p.team_id,t.team_name;
-- Save source counts/sums; compare after migration with writers paused.
SELECT COUNT(*) rows_count,SUM(goals) known_goals FROM provider_player_stats;
SELECT COUNT(*) matches_count FROM matches;
SELECT COUNT(*) original_view_rows FROM v_above_any_team_goal_total;

-- Read-only verification, after manually applying 07_player_totals.sql.
USE group12_football_phase2;
-- Require zero mismatches (NULL-safe comparison preserves unknown vs zero).
SELECT v.player_id FROM tl_v_player_totals v
 JOIN (SELECT player_id,COUNT(*) appearances,SUM(goals) goals,SUM(assists) assists,
 COUNT(goals) known_goals,COUNT(assists) known_assists
 FROM tl_player_match_stats GROUP BY player_id) s USING(player_id)
 WHERE NOT(v.recorded_goals <=> s.goals) OR NOT(v.recorded_assists <=> s.assists)
 OR v.recorded_appearances<>s.appearances
 OR v.known_goal_appearances<>s.known_goals
 OR v.unknown_goal_appearances<>s.appearances-s.known_goals
 OR v.known_assist_appearances<>s.known_assists
 OR v.unknown_assist_appearances<>s.appearances-s.known_assists;
SELECT * FROM tl_v_player_totals ORDER BY recorded_goals DESC,player_id;
-- Compare with preflight: unchanged absent concurrent imports/edits.
SELECT COUNT(*) AS stats_rows,SUM(goals) AS known_goals,SUM(assists) AS known_assists FROM provider_player_stats;
SELECT COUNT(*) AS fixtures FROM matches;
-- Ten original Phase II views must remain present.
SELECT TABLE_NAME FROM information_schema.VIEWS
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME LIKE 'v!_%' ESCAPE '!';

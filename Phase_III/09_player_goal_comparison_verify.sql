-- Read-only after manual migration; same selected schema as preflight.
SELECT * FROM tl_v_above_any_team_goal_total ORDER BY recorded_goals DESC,player_id;
-- Zero missing/extra/mismatched rows expected.
WITH expected AS (
 SELECT p.player_id,SUM(s.goals) recorded_goals FROM tl_players p
 JOIN tl_player_match_stats s USING(player_id) GROUP BY p.player_id
 HAVING SUM(s.goals)>ANY(SELECT SUM(s2.goals) FROM tl_players p2
 JOIN tl_player_match_stats s2 USING(player_id) GROUP BY p2.team_id)
)
SELECT e.player_id FROM expected e LEFT JOIN tl_v_above_any_team_goal_total v USING(player_id)
 WHERE v.player_id IS NULL OR NOT(v.recorded_goals <=> e.recorded_goals)
UNION ALL
SELECT v.player_id FROM tl_v_above_any_team_goal_total v LEFT JOIN expected e USING(player_id)
 WHERE e.player_id IS NULL;
SELECT COUNT(*) rows_count,SUM(goals) known_goals FROM provider_player_stats;
SELECT COUNT(*) matches_count FROM matches;
SELECT COUNT(*) original_view_rows FROM v_above_any_team_goal_total;

-- Manual, forward-only, idempotent MySQL 8 view update. No table records changed.
-- Run 09_player_goal_comparison_preflight.sql first; inspect results and backup.
-- Select YOUR Touchline schema as default. Finish open transactions first.
-- Requires CREATE VIEW, DROP on this view, and SELECT on dependencies.
-- Stop on errors. DDL implicitly commits. Do not rerun earlier migrations.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW tl_v_above_any_team_goal_total AS
SELECT p.player_id, p.full_name, t.team_name, SUM(s.goals) AS recorded_goals
FROM tl_players AS p
JOIN teams AS t ON t.team_id = p.team_id
JOIN tl_player_match_stats AS s ON s.player_id = p.player_id
GROUP BY p.player_id, p.full_name, t.team_name
HAVING SUM(s.goals) > ANY (
  SELECT SUM(s2.goals)
  FROM tl_players AS p2
  JOIN tl_player_match_stats AS s2 ON s2.player_id = p2.player_id
  GROUP BY p2.team_id
);

-- Forward-only, repeatable MySQL 8 view update. Does not change table records.
-- FIRST run 07_player_totals_preflight.sql and review every result.
-- STOP if wrong schema, missing dependencies, duplicate appearance keys, or
-- insufficient privileges. Requires CREATE VIEW, DROP on this view, and SELECT
-- on dependencies. Use an authorized administrator; do not broaden app grants.
-- CREATE OR REPLACE is atomic on MySQL 8, but DDL implicitly commits.
-- Run separately from any open data-edit transaction. Do not rerun migration 06.
USE group12_football_phase2;
CREATE OR REPLACE SQL SECURITY INVOKER VIEW tl_v_player_totals AS
SELECT p.player_id, p.full_name, t.team_name, p.position,
       COUNT(s.match_id) AS recorded_appearances,
       COALESCE(SUM(s.minutes_played), 0) AS recorded_minutes,
       SUM(s.goals) AS recorded_goals,
       SUM(s.assists) AS recorded_assists,
       COUNT(s.goals) AS known_goal_appearances,
       COUNT(s.match_id)-COUNT(s.goals) AS unknown_goal_appearances,
       COUNT(s.assists) AS known_assist_appearances,
       COUNT(s.match_id)-COUNT(s.assists) AS unknown_assist_appearances
FROM tl_players AS p
JOIN teams AS t ON t.team_id = p.team_id
LEFT JOIN tl_player_match_stats AS s ON s.player_id = p.player_id
GROUP BY p.player_id, p.full_name, t.team_name, p.position;

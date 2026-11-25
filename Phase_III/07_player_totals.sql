-- Repeatable legacy player-totals view update; does not change table records.
-- Run the 07 preflight and verification scripts. DDL commits implicitly.
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

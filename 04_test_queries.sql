-- View results and data checks
USE group12_football_phase2;

SELECT * FROM v_match_details ORDER BY match_id;
SELECT * FROM v_above_any_team_goal_total ORDER BY recorded_goals DESC, full_name;
SELECT * FROM v_players_with_goals ORDER BY team_name, full_name;
SELECT * FROM v_match_stat_coverage ORDER BY match_id, player_id;
SELECT * FROM v_goal_or_assist_players ORDER BY team_name, full_name;
SELECT * FROM v_league_standings ORDER BY season_id, league_position;
SELECT * FROM v_player_totals ORDER BY recorded_goals DESC, full_name;
SELECT * FROM v_match_results ORDER BY kickoff_at;
SELECT * FROM v_scheduled_fixtures ORDER BY kickoff_at;
SELECT * FROM v_team_home_away ORDER BY team_name, venue;

-- Tables with fewer than six rows.
SELECT table_name, actual_rows
FROM (
  SELECT 'users' AS table_name, COUNT(*) AS actual_rows FROM users
  UNION ALL SELECT 'competitions', COUNT(*) FROM competitions
  UNION ALL SELECT 'seasons', COUNT(*) FROM seasons
  UNION ALL SELECT 'teams', COUNT(*) FROM teams
  UNION ALL SELECT 'season_teams', COUNT(*) FROM season_teams
  UNION ALL SELECT 'players', COUNT(*) FROM players
  UNION ALL SELECT 'matches', COUNT(*) FROM matches
  UNION ALL SELECT 'player_match_stats', COUNT(*) FROM player_match_stats
) AS counts
WHERE actual_rows < 6;

-- Views with no rows.
SELECT view_name, actual_rows
FROM (
  SELECT 'v_match_details' AS view_name, COUNT(*) AS actual_rows FROM v_match_details
  UNION ALL SELECT 'v_above_any_team_goal_total', COUNT(*) FROM v_above_any_team_goal_total
  UNION ALL SELECT 'v_players_with_goals', COUNT(*) FROM v_players_with_goals
  UNION ALL SELECT 'v_match_stat_coverage', COUNT(*) FROM v_match_stat_coverage
  UNION ALL SELECT 'v_goal_or_assist_players', COUNT(*) FROM v_goal_or_assist_players
  UNION ALL SELECT 'v_league_standings', COUNT(*) FROM v_league_standings
  UNION ALL SELECT 'v_player_totals', COUNT(*) FROM v_player_totals
  UNION ALL SELECT 'v_match_results', COUNT(*) FROM v_match_results
  UNION ALL SELECT 'v_scheduled_fixtures', COUNT(*) FROM v_scheduled_fixtures
  UNION ALL SELECT 'v_team_home_away', COUNT(*) FROM v_team_home_away
) AS counts
WHERE actual_rows = 0;

-- Player stats linked to the wrong club or an incomplete match.
SELECT s.match_id, s.player_id, p.team_id
FROM player_match_stats AS s
JOIN players AS p ON p.player_id = s.player_id
JOIN matches AS m ON m.match_id = s.match_id
WHERE p.team_id NOT IN (m.home_team_id, m.away_team_id)
   OR m.match_status <> 'COMPLETED';

-- Recorded goals greater than the match score.
SELECT m.match_id, p.team_id, SUM(s.goals) AS recorded_goals,
       CASE WHEN p.team_id = m.home_team_id THEN m.home_score
            ELSE m.away_score END AS match_score
FROM player_match_stats AS s
JOIN players AS p ON p.player_id = s.player_id
JOIN matches AS m ON m.match_id = s.match_id
GROUP BY m.match_id, p.team_id, m.home_team_id, m.home_score, m.away_score
HAVING recorded_goals > match_score;

-- Match or stat rows missing the synthetic flag.
SELECT 'matches' AS table_name, match_id AS row_id FROM matches
WHERE is_synthetic <> TRUE
UNION ALL
SELECT 'player_match_stats', match_id FROM player_match_stats
WHERE is_synthetic <> TRUE;

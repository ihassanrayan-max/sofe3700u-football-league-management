-- Phase II views
USE group12_football_phase2;

-- View 1: match details from five tables.
CREATE OR REPLACE VIEW v_match_details AS
SELECT m.match_id, c.competition_name, s.season_label,
       m.kickoff_at, h.team_name AS home_team, a.team_name AS away_team,
       m.match_status, m.home_score, m.away_score, m.is_synthetic
FROM matches AS m
JOIN seasons AS s ON s.season_id = m.season_id
JOIN competitions AS c ON c.competition_id = s.competition_id
JOIN teams AS h ON h.team_id = m.home_team_id
JOIN teams AS a ON a.team_id = m.away_team_id;

-- View 2: players above at least one club's recorded goal total.
CREATE OR REPLACE VIEW v_above_any_team_goal_total AS
SELECT p.player_id, p.full_name, t.team_name, SUM(s.goals) AS recorded_goals
FROM players AS p
JOIN teams AS t ON t.team_id = p.team_id
JOIN player_match_stats AS s ON s.player_id = p.player_id
GROUP BY p.player_id, p.full_name, t.team_name
HAVING SUM(s.goals) > ANY (
  SELECT SUM(s2.goals)
  FROM players AS p2
  JOIN player_match_stats AS s2 ON s2.player_id = p2.player_id
  GROUP BY p2.team_id
);

-- View 3: players with a recorded goal.
CREATE OR REPLACE VIEW v_players_with_goals AS
SELECT p.player_id, p.full_name, t.team_name
FROM players AS p
JOIN teams AS t ON t.team_id = p.team_id
WHERE EXISTS (
  SELECT 1
  FROM player_match_stats AS s
  WHERE s.player_id = p.player_id AND s.goals > 0
);

-- View 4: MySQL has no FULL OUTER JOIN. The UNION ALL adds any right-only rows.
-- The foreign key means right-only rows cannot occur in this data.
CREATE OR REPLACE VIEW v_match_stat_coverage AS
SELECT COALESCE(m.match_id, s.match_id) AS match_id,
       s.player_id, 'MATCH_OR_BOTH' AS coverage_side
FROM matches AS m
LEFT JOIN player_match_stats AS s ON s.match_id = m.match_id
UNION ALL
SELECT COALESCE(m.match_id, s.match_id) AS match_id,
       s.player_id, 'STAT_ONLY' AS coverage_side
FROM player_match_stats AS s
LEFT JOIN matches AS m ON m.match_id = s.match_id
WHERE m.match_id IS NULL;

-- View 5: players with a goal or assist.
CREATE OR REPLACE VIEW v_goal_or_assist_players AS
SELECT p.player_id, p.full_name, t.team_name
FROM players AS p
JOIN teams AS t ON t.team_id = p.team_id
WHERE p.player_id IN (
  SELECT player_id FROM player_match_stats WHERE goals > 0
  UNION
  SELECT player_id FROM player_match_stats WHERE assists > 0
);

-- View 6: standings from completed matches.
CREATE OR REPLACE VIEW v_league_standings AS
SELECT ROW_NUMBER() OVER (
         PARTITION BY x.season_id
         ORDER BY x.points DESC, x.goal_difference DESC,
                  x.goals_for DESC, x.team_name ASC
       ) AS league_position,
       x.season_id, x.season_label, x.team_id, x.team_name,
       x.played, x.wins, x.draws, x.losses, x.goals_for,
       x.goals_against, x.goal_difference, x.points
FROM (
  SELECT st.season_id, se.season_label, t.team_id, t.team_name,
         COUNT(r.match_id) AS played,
         COALESCE(SUM(r.wins), 0) AS wins,
         COALESCE(SUM(r.draws), 0) AS draws,
         COALESCE(SUM(r.losses), 0) AS losses,
         COALESCE(SUM(r.goals_for), 0) AS goals_for,
         COALESCE(SUM(r.goals_against), 0) AS goals_against,
         CAST(COALESCE(SUM(r.goals_for), 0) AS SIGNED)
           - CAST(COALESCE(SUM(r.goals_against), 0) AS SIGNED)
           AS goal_difference,
         COALESCE(SUM(3 * r.wins + r.draws), 0) AS points
  FROM season_teams AS st
  JOIN seasons AS se ON se.season_id = st.season_id
  JOIN teams AS t ON t.team_id = st.team_id
  LEFT JOIN (
    SELECT match_id, season_id, home_team_id AS team_id,
           home_score AS goals_for, away_score AS goals_against,
           (home_score > away_score) AS wins,
           (home_score = away_score) AS draws,
           (home_score < away_score) AS losses
    FROM matches WHERE match_status = 'COMPLETED'
    UNION ALL
    SELECT match_id, season_id, away_team_id AS team_id,
           away_score AS goals_for, home_score AS goals_against,
           (away_score > home_score) AS wins,
           (away_score = home_score) AS draws,
           (away_score < home_score) AS losses
    FROM matches WHERE match_status = 'COMPLETED'
  ) AS r ON r.season_id = st.season_id AND r.team_id = st.team_id
  GROUP BY st.season_id, se.season_label, t.team_id, t.team_name
) AS x;

-- View 7: recorded player totals.
CREATE OR REPLACE VIEW v_player_totals AS
SELECT p.player_id, p.full_name, t.team_name, p.position,
       COUNT(s.match_id) AS recorded_appearances,
       COALESCE(SUM(s.minutes_played), 0) AS recorded_minutes,
       COALESCE(SUM(s.goals), 0) AS recorded_goals,
       COALESCE(SUM(s.assists), 0) AS recorded_assists
FROM players AS p
JOIN teams AS t ON t.team_id = p.team_id
LEFT JOIN player_match_stats AS s ON s.player_id = p.player_id
GROUP BY p.player_id, p.full_name, t.team_name, p.position;

-- View 8: completed match results.
CREATE OR REPLACE VIEW v_match_results AS
SELECT m.match_id, m.kickoff_at,
       h.team_name AS home_team, a.team_name AS away_team,
       m.home_score, m.away_score,
       CASE WHEN m.home_score > m.away_score THEN h.team_name
            WHEN m.home_score < m.away_score THEN a.team_name
            ELSE 'Draw' END AS result,
       m.is_synthetic
FROM matches AS m
JOIN teams AS h ON h.team_id = m.home_team_id
JOIN teams AS a ON a.team_id = m.away_team_id
WHERE m.match_status = 'COMPLETED';

-- View 9: scheduled fixtures.
CREATE OR REPLACE VIEW v_scheduled_fixtures AS
SELECT m.match_id, m.kickoff_at, s.season_label,
       h.team_name AS home_team, a.team_name AS away_team, m.is_synthetic
FROM matches AS m
JOIN seasons AS s ON s.season_id = m.season_id
JOIN teams AS h ON h.team_id = m.home_team_id
JOIN teams AS a ON a.team_id = m.away_team_id
WHERE m.match_status = 'SCHEDULED';

-- View 10: home and away records.
CREATE OR REPLACE VIEW v_team_home_away AS
SELECT t.team_id, t.team_name, r.venue,
       COUNT(*) AS played,
       SUM(r.goals_for) AS goals_for,
       SUM(r.goals_against) AS goals_against,
       SUM(CASE WHEN r.goals_for > r.goals_against THEN 3
                WHEN r.goals_for = r.goals_against THEN 1
                ELSE 0 END) AS points
FROM (
  SELECT home_team_id AS team_id, 'HOME' AS venue,
         home_score AS goals_for, away_score AS goals_against
  FROM matches WHERE match_status = 'COMPLETED'
  UNION ALL
  SELECT away_team_id AS team_id, 'AWAY' AS venue,
         away_score AS goals_for, home_score AS goals_against
  FROM matches WHERE match_status = 'COMPLETED'
) AS r
JOIN teams AS t ON t.team_id = r.team_id
GROUP BY t.team_id, t.team_name, r.venue;

-- REVIEW ONLY. Do not run until the owner approves a backup and this migration.
-- Additive MySQL 8.0.16+ migration: retains every existing record and original view.
-- FIRST RUN ONLY. Run 06_api_football_preflight.sql and inspect every result first.
-- Stop all writers. In Workbench DISABLE continuation after SQL errors.
-- If any statement fails: STOP, ROLLBACK uncommitted DML, and review partial DDL.
-- Never rerun this file blindly. DDL commits implicitly and cannot be rolled back.
-- All provider_* / tl_* names and the EPL 2023/24 season must be absent initially.
USE group12_football_phase2;

CREATE TABLE provider_teams (
 provider VARCHAR(32) NOT NULL, external_id INT NOT NULL, team_id INT NOT NULL,
 PRIMARY KEY(provider,external_id), UNIQUE(provider,team_id),
 FOREIGN KEY(team_id) REFERENCES teams(team_id)
) ENGINE=InnoDB;
CREATE TABLE provider_matches (
 provider VARCHAR(32) NOT NULL, external_id INT NOT NULL, match_id INT NOT NULL,
 PRIMARY KEY(provider,external_id), UNIQUE(provider,match_id),
 FOREIGN KEY(match_id) REFERENCES matches(match_id)
) ENGINE=InnoDB;
-- Independent historical profiles avoid rewriting seeded players or their club assignments.
CREATE TABLE provider_players (
 player_id INT AUTO_INCREMENT PRIMARY KEY,
 provider VARCHAR(32) NOT NULL, external_id INT NOT NULL, team_id INT NOT NULL,
 full_name VARCHAR(100) NOT NULL, position ENUM('GK','DEF','MID','FWD') NULL,
 UNIQUE(provider,external_id,team_id), FOREIGN KEY(team_id) REFERENCES teams(team_id)
) ENGINE=InnoDB;
CREATE TABLE provider_player_stats (
 match_id INT NOT NULL, player_id INT NOT NULL,
 minutes_played TINYINT UNSIGNED NULL, goals TINYINT UNSIGNED NULL, assists TINYINT UNSIGNED NULL,
 details JSON NOT NULL, PRIMARY KEY(match_id,player_id),
 FOREIGN KEY(match_id) REFERENCES matches(match_id),
 FOREIGN KEY(player_id) REFERENCES provider_players(player_id),
 CHECK(minutes_played BETWEEN 0 AND 120), CHECK(goals<=20), CHECK(assists<=20)
) ENGINE=InnoDB;
CREATE TABLE provider_team_stats (
 match_id INT NOT NULL, team_id INT NOT NULL, details JSON NOT NULL,
 PRIMARY KEY(match_id,team_id), FOREIGN KEY(match_id) REFERENCES matches(match_id),
 FOREIGN KEY(team_id) REFERENCES teams(team_id)
) ENGINE=InnoDB;
CREATE TABLE provider_enrichment (
 match_id INT PRIMARY KEY, player_count INT NOT NULL, team_count INT NOT NULL,
 FOREIGN KEY(match_id) REFERENCES matches(match_id)
) ENGINE=InnoDB;

-- One transaction for all data additions. No UPDATE, DELETE, REPLACE or IGNORE.
-- No target-table subqueries inside INSERT statements (MySQL restriction).
START TRANSACTION;
SET @tl_next_season_id = (SELECT COALESCE(MAX(season_id),0)+1 FROM seasons);
INSERT INTO seasons(season_id,competition_id,season_label,start_date,end_date)
 SELECT @tl_next_season_id,c.competition_id,'2023/24','2023-07-01','2024-06-30'
 FROM competitions c WHERE c.competition_name='Premier League';
INSERT INTO season_teams(season_id,team_id)
 SELECT @tl_next_season_id,t.team_id FROM teams t
 WHERE t.team_name IN ('Arsenal','Chelsea','Liverpool','Manchester City','Manchester United','Tottenham Hotspur');
-- Preserve legacy IDs in their own namespace; no existing legacy row is updated.
INSERT INTO provider_matches(provider,external_id,match_id)
 SELECT 'football-data.org',i.external_id,i.match_id FROM imported_matches i;
COMMIT;

CREATE SQL SECURITY INVOKER VIEW tl_seasons AS
 SELECT s.* FROM seasons s JOIN competitions c USING(competition_id)
 WHERE c.competition_name='Premier League' AND s.season_label='2023/24';
CREATE SQL SECURITY INVOKER VIEW tl_season_teams AS
 SELECT st.* FROM season_teams st JOIN tl_seasons s USING(season_id)
 JOIN teams t USING(team_id)
 WHERE t.team_name IN ('Arsenal','Chelsea','Liverpool','Manchester City','Manchester United','Tottenham Hotspur');
CREATE SQL SECURITY INVOKER VIEW tl_matches AS
 SELECT m.* FROM matches m JOIN tl_seasons s USING(season_id)
 JOIN tl_season_teams h ON h.season_id=m.season_id AND h.team_id=m.home_team_id
 JOIN tl_season_teams a ON a.season_id=m.season_id AND a.team_id=m.away_team_id
 WHERE m.is_synthetic=0 AND EXISTS(SELECT 1 FROM provider_matches p WHERE p.match_id=m.match_id AND p.provider='api-football');
CREATE SQL SECURITY INVOKER VIEW tl_player_match_stats AS
 SELECT ps.match_id,ps.player_id,ps.minutes_played,ps.goals,ps.assists,0 AS is_synthetic
 FROM provider_player_stats ps JOIN tl_matches m USING(match_id)
 WHERE ps.minutes_played>0;
CREATE SQL SECURITY INVOKER VIEW tl_players AS
 SELECT p.player_id,p.team_id,p.full_name,p.position FROM provider_players p
 WHERE p.provider='api-football' AND EXISTS(SELECT 1 FROM tl_player_match_stats s WHERE s.player_id=p.player_id);

-- Ten scoped equivalents. Original v_* views remain unchanged for Phase II review.
-- View 1: match details from five tables.
CREATE SQL SECURITY INVOKER VIEW tl_v_match_details AS
SELECT m.match_id, c.competition_name, s.season_label,
       m.kickoff_at, h.team_name AS home_team, a.team_name AS away_team,
       m.match_status, m.home_score, m.away_score, m.is_synthetic
FROM tl_matches AS m
JOIN tl_seasons AS s ON s.season_id = m.season_id
JOIN competitions AS c ON c.competition_id = s.competition_id
JOIN teams AS h ON h.team_id = m.home_team_id
JOIN teams AS a ON a.team_id = m.away_team_id;

-- View 2: tl_players above at least one club's recorded goal total.
CREATE SQL SECURITY INVOKER VIEW tl_v_above_any_team_goal_total AS
SELECT p.player_id, p.full_name, t.team_name, SUM(s.goals) AS recorded_goals
FROM tl_players AS p
JOIN teams AS t ON t.team_id = p.team_id
JOIN tl_player_match_stats AS s ON s.player_id = p.player_id
GROUP BY p.player_id, p.full_name, t.team_name
HAVING COUNT(s.goals)=COUNT(*) AND SUM(s.goals) > ANY (
  SELECT SUM(s2.goals)
  FROM tl_players AS p2
  JOIN tl_player_match_stats AS s2 ON s2.player_id = p2.player_id
  GROUP BY p2.team_id HAVING COUNT(s2.goals)=COUNT(*)
);

-- View 3: tl_players with a recorded goal.
CREATE SQL SECURITY INVOKER VIEW tl_v_players_with_goals AS
SELECT p.player_id, p.full_name, t.team_name
FROM tl_players AS p
JOIN teams AS t ON t.team_id = p.team_id
WHERE EXISTS (
  SELECT 1
  FROM tl_player_match_stats AS s
  WHERE s.player_id = p.player_id AND s.goals > 0
);

-- View 4: MySQL has no FULL OUTER JOIN. The UNION ALL adds any right-only rows.
-- The foreign key means right-only rows cannot occur in this data.
CREATE SQL SECURITY INVOKER VIEW tl_v_match_stat_coverage AS
SELECT COALESCE(m.match_id, s.match_id) AS match_id,
       s.player_id, 'MATCH_OR_BOTH' AS coverage_side
FROM tl_matches AS m
LEFT JOIN tl_player_match_stats AS s ON s.match_id = m.match_id
UNION ALL
SELECT COALESCE(m.match_id, s.match_id) AS match_id,
       s.player_id, 'STAT_ONLY' AS coverage_side
FROM tl_player_match_stats AS s
LEFT JOIN tl_matches AS m ON m.match_id = s.match_id
WHERE m.match_id IS NULL;

-- View 5: tl_players with a goal or assist.
CREATE SQL SECURITY INVOKER VIEW tl_v_goal_or_assist_players AS
SELECT p.player_id, p.full_name, t.team_name
FROM tl_players AS p
JOIN teams AS t ON t.team_id = p.team_id
WHERE p.player_id IN (
  SELECT player_id FROM tl_player_match_stats WHERE goals > 0
  UNION
  SELECT player_id FROM tl_player_match_stats WHERE assists > 0
);

-- View 6: standings from completed tl_matches.
CREATE SQL SECURITY INVOKER VIEW tl_v_league_standings AS
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
  FROM tl_season_teams AS st
  JOIN tl_seasons AS se ON se.season_id = st.season_id
  JOIN teams AS t ON t.team_id = st.team_id
  LEFT JOIN (
    SELECT match_id, season_id, home_team_id AS team_id,
           home_score AS goals_for, away_score AS goals_against,
           (home_score > away_score) AS wins,
           (home_score = away_score) AS draws,
           (home_score < away_score) AS losses
    FROM tl_matches WHERE match_status = 'COMPLETED'
    UNION ALL
    SELECT match_id, season_id, away_team_id AS team_id,
           away_score AS goals_for, home_score AS goals_against,
           (away_score > home_score) AS wins,
           (away_score = home_score) AS draws,
           (away_score < home_score) AS losses
    FROM tl_matches WHERE match_status = 'COMPLETED'
  ) AS r ON r.season_id = st.season_id AND r.team_id = st.team_id
  GROUP BY st.season_id, se.season_label, t.team_id, t.team_name
) AS x;

-- View 7: recorded player totals.
CREATE SQL SECURITY INVOKER VIEW tl_v_player_totals AS
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

-- View 8: completed match results.
CREATE SQL SECURITY INVOKER VIEW tl_v_match_results AS
SELECT m.match_id, m.kickoff_at,
       h.team_name AS home_team, a.team_name AS away_team,
       m.home_score, m.away_score,
       CASE WHEN m.home_score > m.away_score THEN h.team_name
            WHEN m.home_score < m.away_score THEN a.team_name
            ELSE 'Draw' END AS result,
       m.is_synthetic
FROM tl_matches AS m
JOIN teams AS h ON h.team_id = m.home_team_id
JOIN teams AS a ON a.team_id = m.away_team_id
WHERE m.match_status = 'COMPLETED';

-- View 9: scheduled fixtures.
CREATE SQL SECURITY INVOKER VIEW tl_v_scheduled_fixtures AS
SELECT m.match_id, m.kickoff_at, s.season_label,
       h.team_name AS home_team, a.team_name AS away_team, m.is_synthetic
FROM tl_matches AS m
JOIN tl_seasons AS s ON s.season_id = m.season_id
JOIN teams AS h ON h.team_id = m.home_team_id
JOIN teams AS a ON a.team_id = m.away_team_id
WHERE m.match_status = 'SCHEDULED';

-- View 10: home and away records.
CREATE SQL SECURITY INVOKER VIEW tl_v_team_home_away AS
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
  FROM tl_matches WHERE match_status = 'COMPLETED'
  UNION ALL
  SELECT away_team_id AS team_id, 'AWAY' AS venue,
         away_score AS goals_for, home_score AS goals_against
  FROM tl_matches WHERE match_status = 'COMPLETED'
) AS r
JOIN teams AS t ON t.team_id = r.team_id
GROUP BY t.team_id, t.team_name, r.venue;

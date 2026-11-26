-- REVIEW AND RUN MANUALLY ONLY. MySQL 8.0.16+; current selected schema.
-- First run 08_scheduled_demo_preflight.sql. Keep a private backup.
-- Disable Workbench continuation after errors. Pause writers for this install.
-- Three NEW isolated tables; no existing table/view definitions are altered.
-- IF NOT EXISTS supports reruns, not incompatible preexisting objects: inspect first.
-- DDL implicitly commits. On any seed error STOP and ROLLBACK.
CREATE TABLE IF NOT EXISTS tl_demo_seasons (
 season_id INT AUTO_INCREMENT PRIMARY KEY,
 season_label VARCHAR(80) NOT NULL UNIQUE,
 start_date DATE NOT NULL, end_date DATE NOT NULL,
 CHECK(start_date < end_date)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS tl_demo_season_teams (
 season_id INT NOT NULL, team_id INT NOT NULL,
 PRIMARY KEY(season_id,team_id),
 FOREIGN KEY(season_id) REFERENCES tl_demo_seasons(season_id),
 FOREIGN KEY(team_id) REFERENCES teams(team_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS tl_demo_fixtures (
 match_id INT AUTO_INCREMENT PRIMARY KEY,
 season_id INT NOT NULL, home_team_id INT NOT NULL, away_team_id INT NOT NULL,
 kickoff_at DATETIME NOT NULL,
 match_status VARCHAR(12) NOT NULL DEFAULT 'SCHEDULED',
 is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
 UNIQUE(season_id,home_team_id,away_team_id,kickoff_at),
 FOREIGN KEY(season_id,home_team_id) REFERENCES tl_demo_season_teams(season_id,team_id),
 FOREIGN KEY(season_id,away_team_id) REFERENCES tl_demo_season_teams(season_id,team_id),
 CHECK(home_team_id<>away_team_id),
 CHECK(match_status='SCHEDULED'),
 CHECK(is_synthetic=1),
 CHECK(kickoff_at BETWEEN '2024-05-01 00:00:00' AND '2024-05-31 23:59:59')
) ENGINE=InnoDB;

START TRANSACTION;
INSERT INTO tl_demo_seasons(season_label,start_date,end_date)
 SELECT 'Phase II Demo - Synthetic Fixtures','2024-05-01','2024-05-31'
 FROM (SELECT 1 AS seed_row) seed LEFT JOIN tl_demo_seasons existing
 ON existing.season_label='Phase II Demo - Synthetic Fixtures' WHERE existing.season_id IS NULL;
INSERT INTO tl_demo_season_teams(season_id,team_id)
 SELECT s.season_id,t.team_id FROM tl_demo_seasons s CROSS JOIN teams t
 LEFT JOIN tl_demo_season_teams st ON st.season_id=s.season_id AND st.team_id=t.team_id
 WHERE s.season_label='Phase II Demo - Synthetic Fixtures'
 AND t.team_name IN ('Arsenal','Chelsea','Liverpool','Manchester City','Manchester United','Tottenham Hotspur')
 AND st.team_id IS NULL;
INSERT INTO tl_demo_fixtures(season_id,home_team_id,away_team_id,kickoff_at,match_status,is_synthetic)
 SELECT s.season_id,h.team_id,a.team_id,'2024-05-19 16:00:00','SCHEDULED',1
 FROM tl_demo_seasons s
 JOIN teams h ON h.team_name='Manchester United'
 JOIN teams a ON a.team_name='Arsenal'
 LEFT JOIN tl_demo_fixtures f ON f.season_id=s.season_id
 AND f.home_team_id=h.team_id AND f.away_team_id=a.team_id AND f.kickoff_at='2024-05-19 16:00:00'
 WHERE s.season_label='Phase II Demo - Synthetic Fixtures' AND f.match_id IS NULL;
INSERT INTO tl_demo_fixtures(season_id,home_team_id,away_team_id,kickoff_at,match_status,is_synthetic)
 SELECT s.season_id,h.team_id,a.team_id,'2024-05-22 19:45:00','SCHEDULED',1
 FROM tl_demo_seasons s
 JOIN teams h ON h.team_name='Chelsea'
 JOIN teams a ON a.team_name='Liverpool'
 LEFT JOIN tl_demo_fixtures f ON f.season_id=s.season_id
 AND f.home_team_id=h.team_id AND f.away_team_id=a.team_id AND f.kickoff_at='2024-05-22 19:45:00'
 WHERE s.season_label='Phase II Demo - Synthetic Fixtures' AND f.match_id IS NULL;
INSERT INTO tl_demo_fixtures(season_id,home_team_id,away_team_id,kickoff_at,match_status,is_synthetic)
 SELECT s.season_id,h.team_id,a.team_id,'2024-05-26 15:00:00','SCHEDULED',1
 FROM tl_demo_seasons s
 JOIN teams h ON h.team_name='Tottenham Hotspur'
 JOIN teams a ON a.team_name='Manchester City'
 LEFT JOIN tl_demo_fixtures f ON f.season_id=s.season_id
 AND f.home_team_id=h.team_id AND f.away_team_id=a.team_id AND f.kickoff_at='2024-05-26 15:00:00'
 WHERE s.season_label='Phase II Demo - Synthetic Fixtures' AND f.match_id IS NULL;
COMMIT;
CREATE OR REPLACE SQL SECURITY INVOKER VIEW tl_demo_v_scheduled_fixtures AS
 SELECT f.match_id,f.kickoff_at,s.season_label,h.team_name AS home_team,
 a.team_name AS away_team,f.match_status,'Synthetic demonstration' AS data_source
 FROM tl_demo_fixtures f JOIN tl_demo_seasons s USING(season_id)
 JOIN teams h ON h.team_id=f.home_team_id JOIN teams a ON a.team_id=f.away_team_id
 WHERE s.season_label='Phase II Demo - Synthetic Fixtures'
 AND f.is_synthetic=1 AND f.match_status='SCHEDULED';

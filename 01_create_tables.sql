-- Group 12 - Phase II schema
-- Running this again resets the sample tables.
CREATE DATABASE IF NOT EXISTS group12_football_phase2
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE group12_football_phase2;

DROP VIEW IF EXISTS v_team_home_away;
DROP VIEW IF EXISTS v_scheduled_fixtures;
DROP VIEW IF EXISTS v_match_results;
DROP VIEW IF EXISTS v_player_totals;
DROP VIEW IF EXISTS v_league_standings;
DROP VIEW IF EXISTS v_goal_or_assist_players;
DROP VIEW IF EXISTS v_match_stat_coverage;
DROP VIEW IF EXISTS v_players_with_goals;
DROP VIEW IF EXISTS v_above_any_team_goal_total;
DROP VIEW IF EXISTS v_match_details;

DROP TABLE IF EXISTS player_match_stats;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS season_teams;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS seasons;
DROP TABLE IF EXISTS competitions;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  user_id INT PRIMARY KEY,
  display_name VARCHAR(80) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  role ENUM('ADMIN', 'USER', 'GUEST') NOT NULL DEFAULT 'USER'
) ENGINE=InnoDB;

CREATE TABLE competitions (
  competition_id INT PRIMARY KEY,
  competition_name VARCHAR(100) NOT NULL UNIQUE,
  competition_type ENUM('LEAGUE', 'CUP') NOT NULL,
  country VARCHAR(60) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE seasons (
  season_id INT PRIMARY KEY,
  competition_id INT NOT NULL,
  season_label CHAR(7) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  CONSTRAINT uq_season_competition_label UNIQUE (competition_id, season_label),
  CONSTRAINT fk_seasons_competition FOREIGN KEY (competition_id)
    REFERENCES competitions (competition_id),
  CONSTRAINT chk_season_dates CHECK (start_date < end_date)
) ENGINE=InnoDB;

CREATE TABLE teams (
  team_id INT PRIMARY KEY,
  team_name VARCHAR(100) NOT NULL UNIQUE,
  city VARCHAR(80) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE season_teams (
  season_id INT NOT NULL,
  team_id INT NOT NULL,
  PRIMARY KEY (season_id, team_id),
  CONSTRAINT fk_season_teams_season FOREIGN KEY (season_id)
    REFERENCES seasons (season_id),
  CONSTRAINT fk_season_teams_team FOREIGN KEY (team_id)
    REFERENCES teams (team_id)
) ENGINE=InnoDB;

-- Each player has one club in this sample.
CREATE TABLE players (
  player_id INT PRIMARY KEY,
  team_id INT NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  position ENUM('GK', 'DEF', 'MID', 'FWD') NOT NULL,
  CONSTRAINT uq_player_team_name UNIQUE (team_id, full_name),
  CONSTRAINT fk_players_team FOREIGN KEY (team_id)
    REFERENCES teams (team_id)
) ENGINE=InnoDB;

CREATE TABLE matches (
  match_id INT PRIMARY KEY,
  season_id INT NOT NULL,
  home_team_id INT NOT NULL,
  away_team_id INT NOT NULL,
  kickoff_at DATETIME NOT NULL,
  match_status ENUM('SCHEDULED', 'COMPLETED') NOT NULL,
  home_score TINYINT UNSIGNED NULL,
  away_score TINYINT UNSIGNED NULL,
  is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_match_fixture UNIQUE (season_id, home_team_id, away_team_id, kickoff_at),
  CONSTRAINT fk_matches_home_member FOREIGN KEY (season_id, home_team_id)
    REFERENCES season_teams (season_id, team_id),
  CONSTRAINT fk_matches_away_member FOREIGN KEY (season_id, away_team_id)
    REFERENCES season_teams (season_id, team_id),
  CONSTRAINT chk_distinct_teams CHECK (home_team_id <> away_team_id),
  CONSTRAINT chk_match_score_status CHECK (
    (match_status = 'SCHEDULED' AND home_score IS NULL AND away_score IS NULL)
    OR (match_status = 'COMPLETED' AND home_score IS NOT NULL AND away_score IS NOT NULL)
  )
) ENGINE=InnoDB;

CREATE TABLE player_match_stats (
  match_id INT NOT NULL,
  player_id INT NOT NULL,
  minutes_played TINYINT UNSIGNED NOT NULL,
  goals TINYINT UNSIGNED NOT NULL DEFAULT 0,
  assists TINYINT UNSIGNED NOT NULL DEFAULT 0,
  is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (match_id, player_id),
  CONSTRAINT fk_stats_match FOREIGN KEY (match_id)
    REFERENCES matches (match_id),
  CONSTRAINT fk_stats_player FOREIGN KEY (player_id)
    REFERENCES players (player_id),
  CONSTRAINT chk_minutes CHECK (minutes_played BETWEEN 1 AND 120),
  CONSTRAINT chk_goals_possible CHECK (goals <= 20),
  CONSTRAINT chk_assists_possible CHECK (assists <= 20)
) ENGINE=InnoDB;

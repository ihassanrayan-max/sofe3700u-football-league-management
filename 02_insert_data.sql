-- Sample data: match results and player statistics are fictional.
USE group12_football_phase2;

INSERT INTO users (user_id, display_name, email, role) VALUES
  (1, 'Demo Admin One', 'admin.one@example.com', 'ADMIN'),
  (2, 'Demo Admin Two', 'admin.two@example.com', 'ADMIN'),
  (3, 'Demo Reader One', 'reader.one@example.com', 'USER'),
  (4, 'Demo Reader Two', 'reader.two@example.com', 'USER'),
  (5, 'Demo Guest One', 'guest.one@example.com', 'GUEST'),
  (6, 'Demo Guest Two', 'guest.two@example.com', 'GUEST');

INSERT INTO competitions (competition_id, competition_name, competition_type, country) VALUES
  (1, 'Premier League', 'LEAGUE', 'England'),
  (2, 'EFL Championship', 'LEAGUE', 'England'),
  (3, 'EFL League One', 'LEAGUE', 'England'),
  (4, 'EFL League Two', 'LEAGUE', 'England'),
  (5, 'FA Cup', 'CUP', 'England'),
  (6, 'EFL Cup', 'CUP', 'England');

-- These season dates are simplified for the sample.
INSERT INTO seasons (season_id, competition_id, season_label, start_date, end_date) VALUES
  (1, 1, '2025/26', '2025-08-01', '2026-06-30'),
  (2, 2, '2025/26', '2025-08-01', '2026-06-30'),
  (3, 3, '2025/26', '2025-08-01', '2026-06-30'),
  (4, 4, '2025/26', '2025-08-01', '2026-06-30'),
  (5, 5, '2025/26', '2025-08-01', '2026-06-30'),
  (6, 6, '2025/26', '2025-08-01', '2026-06-30');

INSERT INTO teams (team_id, team_name, city) VALUES
  (1, 'Arsenal', 'London'),
  (2, 'Chelsea', 'London'),
  (3, 'Liverpool', 'Liverpool'),
  (4, 'Manchester City', 'Manchester'),
  (5, 'Manchester United', 'Manchester'),
  (6, 'Tottenham Hotspur', 'London');

INSERT INTO season_teams (season_id, team_id) VALUES
  (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6);

INSERT INTO players (player_id, team_id, full_name, position) VALUES
  (1, 1, 'Bukayo Saka', 'FWD'),
  (2, 1, 'Declan Rice', 'MID'),
  (3, 2, 'Cole Palmer', 'MID'),
  (4, 2, 'Reece James', 'DEF'),
  (5, 3, 'Mohamed Salah', 'FWD'),
  (6, 3, 'Dominik Szoboszlai', 'MID'),
  (7, 4, 'Erling Haaland', 'FWD'),
  (8, 4, 'Phil Foden', 'MID'),
  (9, 5, 'Bruno Fernandes', 'MID'),
  (10, 5, 'Bryan Mbeumo', 'FWD'),
  (11, 6, 'Richarlison', 'FWD'),
  (12, 6, 'James Maddison', 'MID');

INSERT INTO matches
  (match_id, season_id, home_team_id, away_team_id, kickoff_at,
   match_status, home_score, away_score, is_synthetic) VALUES
  (1, 1, 1, 2, '2025-09-06 15:00:00', 'COMPLETED', 2, 1, TRUE),
  (2, 1, 3, 4, '2025-09-13 15:00:00', 'COMPLETED', 2, 2, TRUE),
  (3, 1, 5, 6, '2025-09-20 15:00:00', 'COMPLETED', 1, 0, TRUE),
  (4, 1, 2, 3, '2025-10-04 15:00:00', 'COMPLETED', 1, 3, TRUE),
  (5, 1, 4, 1, '2025-10-11 15:00:00', 'COMPLETED', 3, 1, TRUE),
  (6, 1, 6, 2, '2025-10-18 15:00:00', 'COMPLETED', 2, 2, TRUE),
  (7, 1, 1, 3, '2025-11-01 15:00:00', 'COMPLETED', 0, 1, TRUE),
  (8, 1, 5, 4, '2025-11-08 15:00:00', 'COMPLETED', 2, 2, TRUE),
  (9, 1, 6, 1, '2025-11-15 15:00:00', 'COMPLETED', 1, 1, TRUE),
  (10, 1, 2, 5, '2025-11-22 15:00:00', 'COMPLETED', 0, 0, TRUE),
  (11, 1, 3, 6, '2026-03-07 15:00:00', 'SCHEDULED', NULL, NULL, TRUE),
  (12, 1, 4, 2, '2026-03-14 15:00:00', 'SCHEDULED', NULL, NULL, TRUE);

-- Stats cover selected players only, not every player in each match.
INSERT INTO player_match_stats
  (match_id, player_id, minutes_played, goals, assists, is_synthetic) VALUES
  (1, 1, 90, 1, 0, TRUE),
  (1, 2, 90, 0, 1, TRUE),
  (1, 3, 90, 1, 0, TRUE),
  (2, 5, 90, 1, 1, TRUE),
  (2, 6, 90, 1, 0, TRUE),
  (2, 7, 90, 2, 0, TRUE),
  (3, 9, 90, 1, 0, TRUE),
  (3, 11, 90, 0, 0, TRUE),
  (4, 3, 90, 1, 0, TRUE),
  (4, 5, 90, 2, 0, TRUE),
  (4, 6, 90, 1, 1, TRUE),
  (5, 7, 90, 2, 0, TRUE),
  (5, 8, 90, 1, 1, TRUE),
  (5, 1, 90, 1, 0, TRUE),
  (6, 11, 90, 1, 0, TRUE),
  (6, 12, 90, 1, 1, TRUE),
  (6, 3, 90, 2, 0, TRUE),
  (7, 5, 90, 1, 0, TRUE),
  (7, 1, 90, 0, 0, TRUE),
  (8, 9, 90, 1, 0, TRUE),
  (8, 10, 90, 1, 1, TRUE),
  (8, 7, 90, 2, 0, TRUE),
  (9, 11, 90, 1, 0, TRUE),
  (9, 2, 90, 1, 0, TRUE);

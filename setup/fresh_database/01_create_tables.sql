-- Fresh schema only. Stop on errors; do not rerun in an existing schema.

CREATE DATABASE touchline_clean_20261124 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

USE touchline_clean_20261124;

SET NAMES utf8mb4;

SET SESSION foreign_key_checks=1;

CREATE TABLE `competitions` (
  `competition_id` int NOT NULL,
  `competition_name` varchar(100) NOT NULL,
  `competition_type` enum('LEAGUE','CUP') NOT NULL,
  `country` varchar(60) NOT NULL,
  PRIMARY KEY (`competition_id`),
  UNIQUE KEY `competition_name` (`competition_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `teams` (
  `team_id` int NOT NULL,
  `team_name` varchar(100) NOT NULL,
  `city` varchar(80) NOT NULL,
  PRIMARY KEY (`team_id`),
  UNIQUE KEY `team_name` (`team_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `users` (
  `user_id` int NOT NULL,
  `display_name` varchar(80) NOT NULL,
  `email` varchar(254) NOT NULL,
  `role` enum('ADMIN','USER','GUEST') NOT NULL DEFAULT 'USER',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `login_credentials` (
  `user_id` int NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `login_credentials_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `players` (
  `player_id` int NOT NULL,
  `team_id` int NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `position` enum('GK','DEF','MID','FWD') NOT NULL,
  PRIMARY KEY (`player_id`),
  UNIQUE KEY `uq_player_team_name` (`team_id`,`full_name`),
  CONSTRAINT `fk_players_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `provider_players` (
  `player_id` int NOT NULL AUTO_INCREMENT,
  `provider` varchar(32) NOT NULL,
  `external_id` int NOT NULL,
  `team_id` int NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `position` enum('GK','DEF','MID','FWD') DEFAULT NULL,
  PRIMARY KEY (`player_id`),
  UNIQUE KEY `provider` (`provider`,`external_id`,`team_id`),
  KEY `team_id` (`team_id`),
  CONSTRAINT `provider_players_ibfk_1` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB AUTO_INCREMENT=156 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `provider_teams` (
  `provider` varchar(32) NOT NULL,
  `external_id` int NOT NULL,
  `team_id` int NOT NULL,
  PRIMARY KEY (`provider`,`external_id`),
  UNIQUE KEY `provider` (`provider`,`team_id`),
  KEY `team_id` (`team_id`),
  CONSTRAINT `provider_teams_ibfk_1` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `seasons` (
  `season_id` int NOT NULL,
  `competition_id` int NOT NULL,
  `season_label` char(7) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  PRIMARY KEY (`season_id`),
  UNIQUE KEY `uq_season_competition_label` (`competition_id`,`season_label`),
  CONSTRAINT `fk_seasons_competition` FOREIGN KEY (`competition_id`) REFERENCES `competitions` (`competition_id`),
  CONSTRAINT `chk_season_dates` CHECK ((`start_date` < `end_date`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `web_sessions` (
  `session_id` char(64) NOT NULL,
  `user_id` int NOT NULL,
  `expires_at` datetime NOT NULL,
  PRIMARY KEY (`session_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `web_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `season_teams` (
  `season_id` int NOT NULL,
  `team_id` int NOT NULL,
  PRIMARY KEY (`season_id`,`team_id`),
  KEY `fk_season_teams_team` (`team_id`),
  CONSTRAINT `fk_season_teams_season` FOREIGN KEY (`season_id`) REFERENCES `seasons` (`season_id`),
  CONSTRAINT `fk_season_teams_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `matches` (
  `match_id` int NOT NULL,
  `season_id` int NOT NULL,
  `home_team_id` int NOT NULL,
  `away_team_id` int NOT NULL,
  `kickoff_at` datetime NOT NULL,
  `match_status` enum('SCHEDULED','COMPLETED') NOT NULL,
  `home_score` tinyint unsigned DEFAULT NULL,
  `away_score` tinyint unsigned DEFAULT NULL,
  `is_synthetic` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`match_id`),
  UNIQUE KEY `uq_match_fixture` (`season_id`,`home_team_id`,`away_team_id`,`kickoff_at`),
  KEY `fk_matches_away_member` (`season_id`,`away_team_id`),
  CONSTRAINT `fk_matches_away_member` FOREIGN KEY (`season_id`, `away_team_id`) REFERENCES `season_teams` (`season_id`, `team_id`),
  CONSTRAINT `fk_matches_home_member` FOREIGN KEY (`season_id`, `home_team_id`) REFERENCES `season_teams` (`season_id`, `team_id`),
  CONSTRAINT `chk_distinct_teams` CHECK ((`home_team_id` <> `away_team_id`)),
  CONSTRAINT `chk_match_score_status` CHECK ((((`match_status` = _utf8mb4'SCHEDULED') and (`home_score` is null) and (`away_score` is null)) or ((`match_status` = _utf8mb4'COMPLETED') and (`home_score` is not null) and (`away_score` is not null))))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `imported_matches` (
  `external_id` int NOT NULL,
  `match_id` int NOT NULL,
  PRIMARY KEY (`external_id`),
  UNIQUE KEY `match_id` (`match_id`),
  CONSTRAINT `imported_matches_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `player_match_stats` (
  `match_id` int NOT NULL,
  `player_id` int NOT NULL,
  `minutes_played` tinyint unsigned NOT NULL,
  `goals` tinyint unsigned NOT NULL DEFAULT '0',
  `assists` tinyint unsigned NOT NULL DEFAULT '0',
  `is_synthetic` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`match_id`,`player_id`),
  KEY `fk_stats_player` (`player_id`),
  CONSTRAINT `fk_stats_match` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`),
  CONSTRAINT `fk_stats_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `chk_assists_possible` CHECK ((`assists` <= 20)),
  CONSTRAINT `chk_goals_possible` CHECK ((`goals` <= 20)),
  CONSTRAINT `chk_minutes` CHECK ((`minutes_played` between 1 and 120))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `provider_enrichment` (
  `match_id` int NOT NULL,
  `player_count` int NOT NULL,
  `team_count` int NOT NULL,
  PRIMARY KEY (`match_id`),
  CONSTRAINT `provider_enrichment_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `provider_matches` (
  `provider` varchar(32) NOT NULL,
  `external_id` int NOT NULL,
  `match_id` int NOT NULL,
  PRIMARY KEY (`provider`,`external_id`),
  UNIQUE KEY `provider` (`provider`,`match_id`),
  KEY `match_id` (`match_id`),
  CONSTRAINT `provider_matches_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `provider_player_stats` (
  `match_id` int NOT NULL,
  `player_id` int NOT NULL,
  `minutes_played` tinyint unsigned DEFAULT NULL,
  `goals` tinyint unsigned DEFAULT NULL,
  `assists` tinyint unsigned DEFAULT NULL,
  `details` json NOT NULL,
  PRIMARY KEY (`match_id`,`player_id`),
  KEY `player_id` (`player_id`),
  CONSTRAINT `provider_player_stats_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`),
  CONSTRAINT `provider_player_stats_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `provider_players` (`player_id`),
  CONSTRAINT `provider_player_stats_chk_1` CHECK ((`minutes_played` between 0 and 120)),
  CONSTRAINT `provider_player_stats_chk_2` CHECK ((`goals` <= 20)),
  CONSTRAINT `provider_player_stats_chk_3` CHECK ((`assists` <= 20))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `provider_team_stats` (
  `match_id` int NOT NULL,
  `team_id` int NOT NULL,
  `details` json NOT NULL,
  PRIMARY KEY (`match_id`,`team_id`),
  KEY `team_id` (`team_id`),
  CONSTRAINT `provider_team_stats_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`match_id`),
  CONSTRAINT `provider_team_stats_ibfk_2` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

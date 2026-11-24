-- Read-only checks. Counts apply before creating passwords or using the application.

USE touchline_clean_20261124;

SELECT DATABASE() AS selected_schema, VERSION() AS mysql_version;

SELECT TABLE_TYPE,COUNT(*) AS object_count FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() GROUP BY TABLE_TYPE;

SELECT 'competitions' AS table_name,COUNT(*) AS actual_rows,6 AS expected_rows,COUNT(*)=6 AS passed FROM `competitions` UNION ALL SELECT 'teams' AS table_name,COUNT(*) AS actual_rows,6 AS expected_rows,COUNT(*)=6 AS passed FROM `teams` UNION ALL SELECT 'users' AS table_name,COUNT(*) AS actual_rows,3 AS expected_rows,COUNT(*)=3 AS passed FROM `users` UNION ALL SELECT 'login_credentials' AS table_name,COUNT(*) AS actual_rows,0 AS expected_rows,COUNT(*)=0 AS passed FROM `login_credentials` UNION ALL SELECT 'players' AS table_name,COUNT(*) AS actual_rows,12 AS expected_rows,COUNT(*)=12 AS passed FROM `players` UNION ALL SELECT 'provider_players' AS table_name,COUNT(*) AS actual_rows,155 AS expected_rows,COUNT(*)=155 AS passed FROM `provider_players` UNION ALL SELECT 'provider_teams' AS table_name,COUNT(*) AS actual_rows,6 AS expected_rows,COUNT(*)=6 AS passed FROM `provider_teams` UNION ALL SELECT 'seasons' AS table_name,COUNT(*) AS actual_rows,7 AS expected_rows,COUNT(*)=7 AS passed FROM `seasons` UNION ALL SELECT 'web_sessions' AS table_name,COUNT(*) AS actual_rows,0 AS expected_rows,COUNT(*)=0 AS passed FROM `web_sessions` UNION ALL SELECT 'season_teams' AS table_name,COUNT(*) AS actual_rows,12 AS expected_rows,COUNT(*)=12 AS passed FROM `season_teams` UNION ALL SELECT 'matches' AS table_name,COUNT(*) AS actual_rows,72 AS expected_rows,COUNT(*)=72 AS passed FROM `matches` UNION ALL SELECT 'imported_matches' AS table_name,COUNT(*) AS actual_rows,30 AS expected_rows,COUNT(*)=30 AS passed FROM `imported_matches` UNION ALL SELECT 'player_match_stats' AS table_name,COUNT(*) AS actual_rows,24 AS expected_rows,COUNT(*)=24 AS passed FROM `player_match_stats` UNION ALL SELECT 'provider_enrichment' AS table_name,COUNT(*) AS actual_rows,12 AS expected_rows,COUNT(*)=12 AS passed FROM `provider_enrichment` UNION ALL SELECT 'provider_matches' AS table_name,COUNT(*) AS actual_rows,60 AS expected_rows,COUNT(*)=60 AS passed FROM `provider_matches` UNION ALL SELECT 'provider_player_stats' AS table_name,COUNT(*) AS actual_rows,478 AS expected_rows,COUNT(*)=478 AS passed FROM `provider_player_stats` UNION ALL SELECT 'provider_team_stats' AS table_name,COUNT(*) AS actual_rows,24 AS expected_rows,COUNT(*)=24 AS passed FROM `provider_team_stats`;

SELECT 'tl_seasons' AS view_name,COUNT(*) AS row_count FROM `tl_seasons`;

SELECT 'v_above_any_team_goal_total' AS view_name,COUNT(*) AS row_count FROM `v_above_any_team_goal_total`;

SELECT 'v_goal_or_assist_players' AS view_name,COUNT(*) AS row_count FROM `v_goal_or_assist_players`;

SELECT 'v_league_standings' AS view_name,COUNT(*) AS row_count FROM `v_league_standings`;

SELECT 'v_match_details' AS view_name,COUNT(*) AS row_count FROM `v_match_details`;

SELECT 'v_match_results' AS view_name,COUNT(*) AS row_count FROM `v_match_results`;

SELECT 'v_match_stat_coverage' AS view_name,COUNT(*) AS row_count FROM `v_match_stat_coverage`;

SELECT 'v_player_totals' AS view_name,COUNT(*) AS row_count FROM `v_player_totals`;

SELECT 'v_players_with_goals' AS view_name,COUNT(*) AS row_count FROM `v_players_with_goals`;

SELECT 'v_scheduled_fixtures' AS view_name,COUNT(*) AS row_count FROM `v_scheduled_fixtures`;

SELECT 'v_team_home_away' AS view_name,COUNT(*) AS row_count FROM `v_team_home_away`;

SELECT 'tl_season_teams' AS view_name,COUNT(*) AS row_count FROM `tl_season_teams`;

SELECT 'tl_matches' AS view_name,COUNT(*) AS row_count FROM `tl_matches`;

SELECT 'tl_player_match_stats' AS view_name,COUNT(*) AS row_count FROM `tl_player_match_stats`;

SELECT 'tl_v_league_standings' AS view_name,COUNT(*) AS row_count FROM `tl_v_league_standings`;

SELECT 'tl_v_match_details' AS view_name,COUNT(*) AS row_count FROM `tl_v_match_details`;

SELECT 'tl_v_match_results' AS view_name,COUNT(*) AS row_count FROM `tl_v_match_results`;

SELECT 'tl_v_scheduled_fixtures' AS view_name,COUNT(*) AS row_count FROM `tl_v_scheduled_fixtures`;

SELECT 'tl_v_team_home_away' AS view_name,COUNT(*) AS row_count FROM `tl_v_team_home_away`;

SELECT 'tl_players' AS view_name,COUNT(*) AS row_count FROM `tl_players`;

SELECT 'tl_v_match_stat_coverage' AS view_name,COUNT(*) AS row_count FROM `tl_v_match_stat_coverage`;

SELECT 'tl_v_above_any_team_goal_total' AS view_name,COUNT(*) AS row_count FROM `tl_v_above_any_team_goal_total`;

SELECT 'tl_v_goal_or_assist_players' AS view_name,COUNT(*) AS row_count FROM `tl_v_goal_or_assist_players`;

SELECT 'tl_v_player_totals' AS view_name,COUNT(*) AS row_count FROM `tl_v_player_totals`;

SELECT 'tl_v_players_with_goals' AS view_name,COUNT(*) AS row_count FROM `tl_v_players_with_goals`;

SELECT provider,COUNT(*) AS fixture_count FROM provider_matches GROUP BY provider;

SELECT is_synthetic,COUNT(*) AS match_count FROM matches GROUP BY is_synthetic;

SELECT user_id,display_name,email,role FROM users ORDER BY user_id;

SELECT 'login_credentials -> users' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `login_credentials` c WHERE c.`user_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `users` p WHERE c.`user_id`=p.`user_id`);

SELECT 'players -> teams' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `players` c WHERE c.`team_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `teams` p WHERE c.`team_id`=p.`team_id`);

SELECT 'provider_players -> teams' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_players` c WHERE c.`team_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `teams` p WHERE c.`team_id`=p.`team_id`);

SELECT 'provider_teams -> teams' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_teams` c WHERE c.`team_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `teams` p WHERE c.`team_id`=p.`team_id`);

SELECT 'seasons -> competitions' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `seasons` c WHERE c.`competition_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `competitions` p WHERE c.`competition_id`=p.`competition_id`);

SELECT 'web_sessions -> users' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `web_sessions` c WHERE c.`user_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `users` p WHERE c.`user_id`=p.`user_id`);

SELECT 'season_teams -> seasons' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `season_teams` c WHERE c.`season_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `seasons` p WHERE c.`season_id`=p.`season_id`);

SELECT 'season_teams -> teams' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `season_teams` c WHERE c.`team_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `teams` p WHERE c.`team_id`=p.`team_id`);

SELECT 'matches -> season_teams' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `matches` c WHERE c.`season_id` IS NOT NULL AND c.`away_team_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `season_teams` p WHERE c.`season_id`=p.`season_id` AND c.`away_team_id`=p.`team_id`);

SELECT 'matches -> season_teams' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `matches` c WHERE c.`season_id` IS NOT NULL AND c.`home_team_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `season_teams` p WHERE c.`season_id`=p.`season_id` AND c.`home_team_id`=p.`team_id`);

SELECT 'imported_matches -> matches' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `imported_matches` c WHERE c.`match_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `matches` p WHERE c.`match_id`=p.`match_id`);

SELECT 'player_match_stats -> matches' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `player_match_stats` c WHERE c.`match_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `matches` p WHERE c.`match_id`=p.`match_id`);

SELECT 'player_match_stats -> players' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `player_match_stats` c WHERE c.`player_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `players` p WHERE c.`player_id`=p.`player_id`);

SELECT 'provider_enrichment -> matches' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_enrichment` c WHERE c.`match_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `matches` p WHERE c.`match_id`=p.`match_id`);

SELECT 'provider_matches -> matches' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_matches` c WHERE c.`match_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `matches` p WHERE c.`match_id`=p.`match_id`);

SELECT 'provider_player_stats -> matches' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_player_stats` c WHERE c.`match_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `matches` p WHERE c.`match_id`=p.`match_id`);

SELECT 'provider_player_stats -> provider_players' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_player_stats` c WHERE c.`player_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `provider_players` p WHERE c.`player_id`=p.`player_id`);

SELECT 'provider_team_stats -> matches' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_team_stats` c WHERE c.`match_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `matches` p WHERE c.`match_id`=p.`match_id`);

SELECT 'provider_team_stats -> teams' AS foreign_key_check,COUNT(*) AS orphan_rows FROM `provider_team_stats` c WHERE c.`team_id` IS NOT NULL AND NOT EXISTS(SELECT 1 FROM `teams` p WHERE c.`team_id`=p.`team_id`);

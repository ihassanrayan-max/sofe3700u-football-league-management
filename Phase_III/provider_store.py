"""Persistence called only by the authenticated, CSRF-protected import save route."""
import json
from flask import abort
from api_football import CLUBS, SEASON, PROVIDER


def resolve_match(sql, row, season, teams):
    """EPL has one home/away pairing per season; kickoff changes cannot duplicate it."""
    mapped = sql('SELECT match_id FROM provider_matches WHERE provider=%s AND external_id=%s FOR UPDATE',
                 [PROVIDER,row['external_id']])
    candidates = sql('SELECT * FROM matches WHERE season_id=%s AND home_team_id=%s AND away_team_id=%s FOR UPDATE',
                     [season,teams[row['home_external_id']],teams[row['away_external_id']]])
    if len(candidates)>1 or (mapped and (not candidates or mapped[0]['match_id'] != candidates[0]['match_id'])):
        abort(409, 'Ambiguous fixture mapping. Review existing records; no rows were changed.')
    if candidates:
        match = candidates[0]
        if match['is_synthetic']:
            abort(409, 'A fictional fixture occupies this season and pairing. Resolve it separately before import.')
        # Reuse cross-provider identity, never silently rewrite a conflicting result.
        if any(match[k] != row[k] for k in ('match_status','home_score','away_score')) or str(match['kickoff_at']).replace('T',' ') != row['kickoff_at']:
            abort(409, 'Existing fixture differs from the preview. Manual reconciliation is required.')
        mid = match['match_id']
    else:
        top = sql('SELECT match_id FROM matches ORDER BY match_id DESC LIMIT 1 FOR UPDATE')
        mid = top[0]['match_id']+1 if top else 1
        sql('INSERT INTO matches (match_id,season_id,home_team_id,away_team_id,kickoff_at,match_status,home_score,away_score,is_synthetic) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0)',
            [mid,season,teams[row['home_external_id']],teams[row['away_external_id']],row['kickoff_at'],row['match_status'],row['home_score'],row['away_score']])
    if not mapped:
        sql('INSERT INTO provider_matches (provider,external_id,match_id) VALUES (%s,%s,%s)',[PROVIDER,row['external_id'],mid])
    return mid


def save_snapshot(sql, connection, data):
    try:
        seasons = sql("SELECT s.season_id,s.start_date,s.end_date FROM seasons s JOIN competitions c USING(competition_id) WHERE c.competition_name='Premier League' AND s.season_label=%s FOR UPDATE",[SEASON])
        if len(seasons)!=1: abort(409, 'Apply the reviewed 06 migration and 2023/24 memberships before importing.')
        season = seasons[0]['season_id']
        if any(not str(seasons[0]['start_date']) <= row['kickoff_at'][:10] <= str(seasons[0]['end_date']) for row in data['fixtures']):
            abort(409, 'The existing season dates do not cover these fixtures. Review the season before importing.')
        members = sql('SELECT t.team_id,t.team_name FROM season_teams st JOIN teams t USING(team_id) WHERE st.season_id=%s',[season])
        by_name = {r['team_name']:r['team_id'] for r in members}
        if set(by_name)!=set(CLUBS.values()): abort(409, '2023/24 must contain exactly the six project clubs.')
        teams = {pid:by_name[name] for pid,name in CLUBS.items()}
        for external,local in teams.items():
            existing = sql('SELECT team_id FROM provider_teams WHERE provider=%s AND external_id=%s',[PROVIDER,external])
            if existing and existing[0]['team_id']!=local: abort(409, 'Conflicting provider club mapping.')
            if not existing: sql('INSERT INTO provider_teams VALUES (%s,%s,%s)',[PROVIDER,external,local])
        saved = 0
        for row in data['fixtures']:
            mid = resolve_match(sql,row,season,teams)
            for player in row.get('players',[]):
                # Historical club memberships are separate profiles, never mutate a seeded player.
                identity = [PROVIDER,player['external_id'],teams[player['team_external_id']]]
                found = sql('SELECT player_id FROM provider_players WHERE provider=%s AND external_id=%s AND team_id=%s',identity)
                if not found:
                    sql('INSERT INTO provider_players (provider,external_id,team_id,full_name,position) VALUES (%s,%s,%s,%s,%s)',identity+[player['full_name'],player['position']])
                    found = sql('SELECT player_id FROM provider_players WHERE provider=%s AND external_id=%s AND team_id=%s',identity)
                pid = found[0]['player_id']
                sql('INSERT INTO provider_player_stats (match_id,player_id,minutes_played,goals,assists,details) VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE minutes_played=VALUES(minutes_played),goals=VALUES(goals),assists=VALUES(assists),details=VALUES(details)',
                    [mid,pid,player['minutes_played'],player['goals'],player['assists'],json.dumps(player['details'])])
            for stats in row.get('team_stats',[]):
                sql('INSERT INTO provider_team_stats (match_id,team_id,details) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE details=VALUES(details)',[mid,teams[stats['team_external_id']],json.dumps(stats['details'])])
            if 'players' in row:
                sql('INSERT INTO provider_enrichment (match_id,player_count,team_count) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE player_count=VALUES(player_count),team_count=VALUES(team_count)',[mid,len(row['players']),len(row['team_stats'])])
            saved += 1
        connection.commit()
        return saved
    except Exception:
        connection.rollback()
        raise

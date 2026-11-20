"""API-Football v3 adapter. No network or database work at module import."""
import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from flask import abort

PROVIDER = 'api-football'
SEASON = '2023/24'
CLUBS = {42:'Arsenal', 49:'Chelsea', 40:'Liverpool', 50:'Manchester City',
         33:'Manchester United', 47:'Tottenham Hotspur'}
POSITIONS = {'G':'GK', 'D':'DEF', 'M':'MID', 'F':'FWD',
             'Goalkeeper':'GK', 'Defender':'DEF', 'Midfielder':'MID', 'Attacker':'FWD'}


def integer(value, maximum=2147483647, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError('Invalid provider integer')
    return value


def envelope(payload):
    if not isinstance(payload, dict) or payload.get('errors'):
        abort(502, 'API-Football reported an error. Check plan access or quota in the provider dashboard.')
    rows = payload.get('response')
    if not isinstance(rows, list) or payload.get('results') != len(rows):
        abort(502, 'Invalid API-Football response envelope.')
    paging = payload.get('paging', {})
    if not isinstance(paging,dict) or type(paging.get('total',1)) is not int:
        abort(502, 'Invalid API-Football pagination metadata.')
    if paging.get('total', 1) > 1:
        abort(502, 'Incomplete paginated response; nothing was imported.')
    return rows


class Cache:
    """Process-safe local cache and rolling quota ledger; never contains the API key.

    Reserve before network I/O, including failed calls. A rolling 24-hour cap is
    conservative regardless of the provider's quota reset time. Shared by workers.
    """
    def __init__(self, path=None):
        self.path = Path(path or Path(__file__).parent / 'work' / 'api-football.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, expires REAL)')
            con.execute('CREATE TABLE IF NOT EXISTS calls (at REAL NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS controls (key TEXT PRIMARY KEY, until_at REAL)')

    @contextmanager
    def connect(self):
        con = sqlite3.connect(str(self.path), timeout=15)
        try:
            with con:
                yield con
        finally:
            con.close()

    def get(self, key):
        with self.connect() as con:
            row = con.execute('SELECT value FROM cache WHERE key=? AND expires>?', (key,time.time())).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key, value, ttl=604800):
        with self.connect() as con:
            con.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)', (key,json.dumps(value),time.time()+ttl))

    def reserve(self):
        now = time.time()
        try:
            limit = min(100, max(1, int(os.getenv('API_FOOTBALL_DAILY_LIMIT','90'))))
        except ValueError:
            abort(503, 'API_FOOTBALL_DAILY_LIMIT must be an integer between 1 and 100.')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            blocked = con.execute('SELECT until_at FROM controls WHERE key=?', ('blocked',)).fetchone()
            daily = con.execute('SELECT COUNT(*) FROM calls WHERE at>?', (now-86400,)).fetchone()[0]
            minute = con.execute('SELECT COUNT(*) FROM calls WHERE at>?', (now-60,)).fetchone()[0]
            if (blocked and blocked[0] > now) or daily >= limit or minute >= 10:
                abort(429, 'Local API-Football quota reached. Wait before retrying; cached previews remain available.')
            con.execute('INSERT INTO calls VALUES (?)', (now,))

    def block(self):
        with self.connect() as con:
            con.execute('INSERT OR REPLACE INTO controls VALUES (?,?)', ('blocked',time.time()+86400))

    def fetch(self, endpoint, **params):
        key = endpoint+'?'+urlencode(sorted(params.items()))
        cached = self.get(key)
        if cached is not None:
            return cached
        token = os.getenv('API_FOOTBALL_KEY')
        if not token:
            abort(503, 'Set API_FOOTBALL_KEY in the private .env and restart Flask.')
        self.reserve()
        req = Request('https://v3.football.api-sports.io/'+key, headers={'x-apisports-key':token})
        try:
            with urlopen(req, timeout=20) as response:
                payload = json.load(response)
                remaining = response.headers.get('x-ratelimit-requests-remaining')
                if remaining == '0': self.block()
        except HTTPError as exc:
            if exc.code == 429:
                self.block()
                abort(429, 'API-Football quota exhausted. No automatic retries were made.')
            abort(502, 'API-Football denied or failed the request. Check your provider dashboard.')
        except (URLError, TimeoutError, ValueError):
            abort(502, 'API-Football unavailable or returned unreadable data.')
        envelope(payload)
        self.put(key, payload)
        return payload


def parse_fixtures(payload):
    rows = []; skipped = 0; seen = set()
    for item in envelope(payload):
        try:
            league = item['league']; teams = item['teams']; fixture = item['fixture']
            if league['id'] != 39 or league['season'] != 2023:
                raise ValueError()
            home, away = teams['home']['id'], teams['away']['id']
            if home not in CLUBS or away not in CLUBS:
                continue
            if home == away: raise ValueError()
            external = integer(fixture['id'], minimum=1)
            if external in seen: abort(502, 'Duplicate API-Football fixture IDs.')
            seen.add(external)
            status = {'FT':'COMPLETED','NS':'SCHEDULED'} .get(fixture['status']['short'])
            if status is None:
                skipped += 1; continue
            kickoff = datetime.fromisoformat(fixture['date'].replace('Z','+00:00'))
            if not kickoff.tzinfo: raise ValueError()
            kickoff = kickoff.astimezone(timezone.utc)
            if not datetime(2023,7,1,tzinfo=timezone.utc) <= kickoff < datetime(2024,7,1,tzinfo=timezone.utc):
                raise ValueError()
            goals = [integer(item['goals'][side],255) for side in ('home','away')] if status == 'COMPLETED' else [None,None]
            rows.append(dict(external_id=external,home_external_id=home,away_external_id=away,
                home_team=CLUBS[home],away_team=CLUBS[away],kickoff_at=kickoff.strftime('%Y-%m-%d %H:%M:%S'),
                match_status=status,home_score=goals[0],away_score=goals[1]))
        except (KeyError, TypeError, ValueError, AttributeError):
            abort(502, 'Malformed eligible API-Football fixture. Nothing was imported.')
    return sorted(rows,key=lambda row:row['external_id']), skipped


def parse_players(payload, fixture):
    rows = []; seen = set()
    allowed = {fixture['home_external_id'], fixture['away_external_id']}
    for team in envelope(payload):
        try:
            tid = integer(team['team']['id'], minimum=1)
            if tid not in allowed: raise ValueError()
            for entry in team['players']:
                player = entry['player']; pid = integer(player['id'],minimum=1)
                if pid in seen: raise ValueError()
                seen.add(pid)
                name = player['name']
                if not isinstance(name,str) or not name.strip() or len(name)>100: raise ValueError()
                if len(entry['statistics']) != 1: raise ValueError()
                stats = entry['statistics'][0]; games = stats['games']; goals = stats['goals']
                minutes = games.get('minutes')
                if minutes is not None: integer(minutes,120)
                goal, assist = goals.get('total'), goals.get('assists')
                for value in (goal,assist):
                    if value is not None: integer(value,20)
                position = POSITIONS.get(games.get('position'))
                rows.append(dict(external_id=pid,team_external_id=tid,full_name=name.strip(),position=position,
                    minutes_played=minutes,goals=goal,assists=assist,details=stats))
        except (KeyError, TypeError, ValueError, AttributeError):
            abort(502, 'Malformed API-Football player statistics. Nothing was imported.')
    for tid,score in ((fixture['home_external_id'],fixture['home_score']),(fixture['away_external_id'],fixture['away_score'])):
        if score is not None and sum(r['goals'] or 0 for r in rows if r['team_external_id']==tid)>score:
            abort(502, 'Provider player goals exceed the fixture score.')
    return rows


def parse_team_stats(payload, fixture):
    result = []; seen = set()
    for entry in envelope(payload):
        try:
            tid = entry['team']['id']
            if tid not in (fixture['home_external_id'],fixture['away_external_id']) or tid in seen: raise ValueError()
            seen.add(tid)
            stats = entry['statistics']
            if not isinstance(stats,list): raise ValueError()
            for stat in stats:
                if not isinstance(stat.get('type'),str) or not isinstance(stat.get('value'),(str,int,float,type(None))): raise ValueError()
            result.append(dict(team_external_id=tid,details=stats))
        except (KeyError, TypeError, ValueError):
            abort(502, 'Malformed API-Football team statistics.')
    return result


def snapshot(cache, data):
    digest = hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
    cache.put('preview:'+digest,data,3600)
    return digest

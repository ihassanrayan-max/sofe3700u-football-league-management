"""Offline provider tests. Fixtures here are test inputs, never application data."""
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from werkzeug.exceptions import HTTPException
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import api_football as af
import provider_store as store
import app as core
import services


def payload(rows):
    return {'errors':[], 'results':len(rows), 'paging':{'current':1,'total':1}, 'response':rows}


def fixture():
    return {'league':{'id':39,'season':2023},'fixture':{'id':123,'date':'2023-09-01T16:00:00+01:00','status':{'short':'FT'}},
            'teams':{'home':{'id':42},'away':{'id':49}},'goals':{'home':2,'away':1}}


def player(minutes=90,goals=1,assists=None):
    return {'team':{'id':42},'players':[{'player':{'id':77,'name':'Test player'},'statistics':[
        {'games':{'minutes':minutes,'position':'F'},'goals':{'total':goals,'assists':assists}}]}]}


class ParsingTests(unittest.TestCase):
    def setUp(self): self.row=af.parse_fixtures(payload([fixture()]))[0][0]

    def test_mapping_scope_and_utc(self):
        self.assertEqual((self.row['home_team'],self.row['away_team']),('Arsenal','Chelsea'))
        self.assertEqual(self.row['kickoff_at'],'2023-09-01 15:00:00')
        other=fixture(); other['teams']['away']['id']=999
        self.assertEqual(af.parse_fixtures(payload([other])),([],0))

    def test_empty_and_error_envelopes(self):
        self.assertEqual(af.parse_fixtures(payload([])),([],0))
        for bad in ({'errors':{'token':'private provider error'}}, {'response':[]}, payload([])|{'paging':{'total':2}}):
            with self.assertRaises(HTTPException): af.parse_fixtures(bad)

    def test_duplicate_and_wrong_season_rejected(self):
        with self.assertRaises(HTTPException): af.parse_fixtures(payload([fixture(),fixture()]))
        bad=fixture();bad['league']['season']=2025
        with self.assertRaises(HTTPException): af.parse_fixtures(payload([bad]))

    def test_in_progress_skipped_and_scheduled_has_no_score(self):
        row=fixture();row['fixture']['status']['short']='1H'
        self.assertEqual(af.parse_fixtures(payload([row])),([],1))
        row['fixture']['status']['short']='NS'
        self.assertIsNone(af.parse_fixtures(payload([row]))[0][0]['home_score'])

    def test_malformed_completed_score_rejected(self):
        for score in (None,True,-1,256):
            row=fixture();row['goals']['home']=score
            with self.assertRaises(HTTPException): af.parse_fixtures(payload([row]))

    def test_player_nulls_zero_minutes_and_positions(self):
        rows=af.parse_players(payload([player()]),self.row)
        self.assertEqual(rows[0]['position'],'FWD')
        self.assertIsNone(rows[0]['assists'])
        rows=af.parse_players(payload([player(0,0,0)]),self.row)
        self.assertEqual(rows[0]['minutes_played'],0)
        self.assertEqual(rows[0]['assists'],0)
        self.assertEqual(af.parse_players(payload([]),self.row),[])

    def test_player_wrong_team_duplicate_and_excess_goals(self):
        bad=player();bad['team']['id']=33
        for rows in ([bad],[player(),player()],[player(goals=3)]):
            with self.assertRaises(HTTPException): af.parse_players(payload(rows),self.row)

    def test_team_stats_preserve_missing_and_percentage(self):
        rows=af.parse_team_stats(payload([{'team':{'id':42},'statistics':[
            {'type':'Ball Possession','value':'52%'},{'type':'Shots on Goal','value':None}]}]),self.row)
        self.assertEqual(rows[0]['details'][0]['value'],'52%')
        self.assertIsNone(rows[0]['details'][1]['value'])


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.cache=af.Cache(Path(self.temp.name)/'cache.sqlite3')

    def test_cache_hit_costs_no_network_or_quota(self):
        self.cache.put('fixtures?league=39&season=2023',payload([]))
        with patch.object(af,'urlopen') as network,patch.object(self.cache,'reserve') as reserve:
            self.assertEqual(self.cache.fetch('fixtures',league=39,season=2023),payload([]))
            network.assert_not_called();reserve.assert_not_called()

    def test_missing_key_no_request(self):
        with patch.dict(os.environ,{'API_FOOTBALL_KEY':''}),patch.object(af,'urlopen') as network:
            with self.assertRaises(HTTPException) as caught: self.cache.fetch('fixtures',league=39,season=2023)
            self.assertEqual(caught.exception.code,503);network.assert_not_called()

    def test_quota_is_shared_and_failed_requests_count(self):
        with patch.dict(os.environ,{'API_FOOTBALL_DAILY_LIMIT':'1','API_FOOTBALL_KEY':'offline-test'}),patch.object(af,'urlopen',side_effect=af.URLError('test')):
            with self.assertRaises(HTTPException): self.cache.fetch('fixtures')
        with patch.dict(os.environ,{'API_FOOTBALL_DAILY_LIMIT':'1'}):
            with self.assertRaises(HTTPException) as caught: af.Cache(self.cache.path).reserve()
            self.assertEqual(caught.exception.code,429)

    def test_minute_limit_and_expiry(self):
        with patch.dict(os.environ,{'API_FOOTBALL_DAILY_LIMIT':'100'}):
            for _ in range(10): self.cache.reserve()
            with self.assertRaises(HTTPException): self.cache.reserve()
        self.cache.put('expired',{},ttl=-1)
        self.assertIsNone(self.cache.get('expired'))

    def test_snapshot_round_trip(self):
        data={'fixtures':[{'external_id':1}]}
        digest=af.snapshot(self.cache,data)
        self.assertEqual(self.cache.get('preview:'+digest),data)

    def test_http_200_provider_error_is_not_cached(self):
        response=io.BytesIO(json.dumps({'errors':{'token':'do not expose'},'response':[],'results':0}).encode())
        response.headers={}
        with patch.dict(os.environ,{'API_FOOTBALL_KEY':'offline-test'}),patch.object(af,'urlopen',return_value=response):
            with self.assertRaises(HTTPException) as caught:self.cache.fetch('fixtures')
        self.assertNotIn('do not expose',caught.exception.description)
        self.assertIsNone(self.cache.get('fixtures?'))

    def test_provider_exhaustion_blocks_fresh_calls(self):
        response=io.BytesIO(json.dumps(payload([])).encode());response.headers={'x-ratelimit-requests-remaining':'0'}
        with patch.dict(os.environ,{'API_FOOTBALL_KEY':'offline-test'}),patch.object(af,'urlopen',return_value=response):
            self.cache.fetch('fixtures')
        with self.assertRaises(HTTPException):self.cache.reserve()
        self.assertEqual(self.cache.fetch('fixtures'),payload([]))


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.row=af.parse_fixtures(payload([fixture()]))[0][0]
        self.teams={42:1,49:2}
        self.match={'match_id':55,'is_synthetic':0,**{k:self.row[k] for k in ('match_status','home_score','away_score','kickoff_at')}}

    def resolver(self,mapped=False,matches=None):
        def sql(stmt,args=()):
            if stmt.startswith('SELECT match_id FROM provider_matches'): return [{'match_id':55}] if mapped else []
            if stmt.startswith('SELECT * FROM matches'): return matches if matches is not None else [self.match]
            if stmt.startswith('SELECT match_id FROM matches'):return [{'match_id':70}]
            return []
        return Mock(side_effect=sql)

    def test_cross_provider_match_reused_without_update(self):
        sql=self.resolver()
        self.assertEqual(store.resolve_match(sql,self.row,7,self.teams),55)
        writes=[c.args[0] for c in sql.call_args_list if not c.args[0].startswith('SELECT')]
        self.assertEqual(len(writes),1);self.assertTrue(writes[0].startswith('INSERT INTO provider_matches'))

    def test_same_provider_reimport_is_idempotent(self):
        sql=self.resolver(mapped=True)
        self.assertEqual(store.resolve_match(sql,self.row,7,self.teams),55)
        self.assertTrue(all(c.args[0].startswith('SELECT') for c in sql.call_args_list))

    def test_new_match_is_separate_season_and_nonsynthetic(self):
        sql=self.resolver(matches=[])
        self.assertEqual(store.resolve_match(sql,self.row,7,self.teams),71)
        insert=next(c for c in sql.call_args_list if c.args[0].startswith('INSERT INTO matches'))
        self.assertEqual(insert.args[1][:4],[71,7,1,2]);self.assertTrue(insert.args[0].endswith(',0)'))

    def test_synthetic_conflicting_and_ambiguous_matches_stop(self):
        for matches in ([self.match|{'is_synthetic':1}],[self.match|{'home_score':9}],[self.match,self.match]):
            sql=self.resolver(matches=matches)
            with self.assertRaises(HTTPException):store.resolve_match(sql,self.row,7,self.teams)
            self.assertTrue(all(c.args[0].startswith('SELECT') for c in sql.call_args_list))

    def test_failed_save_rolls_back(self):
        connection=Mock()
        with self.assertRaises(HTTPException):store.save_snapshot(Mock(return_value=[]),connection,{'fixtures':[self.row]})
        connection.rollback.assert_called_once();connection.commit.assert_not_called()

    def test_player_mapping_uses_provider_and_historical_club(self):
        row=self.row|{'players':af.parse_players(payload([player()]),self.row),'team_stats':[]}
        def sql(stmt,args=()):
            if stmt.startswith('SELECT s.season_id'):return [{'season_id':7,'start_date':'2023-07-01','end_date':'2024-06-30'}]
            if stmt.startswith('SELECT t.team_id'):return [{'team_id':i,'team_name':name} for i,name in af.CLUBS.items()]
            if stmt.startswith('SELECT player_id'):return [{'player_id':101}]
            return []
        query=Mock(side_effect=sql);connection=Mock()
        with patch.object(store,'resolve_match',return_value=55):store.save_snapshot(query,connection,{'fixtures':[row]})
        lookup=next(c for c in query.call_args_list if c.args[0].startswith('SELECT player_id'))
        self.assertEqual(lookup.args[1],['api-football',77,42])
        insert=next(c for c in query.call_args_list if c.args[0].startswith('INSERT INTO provider_player_stats'))
        self.assertEqual(insert.args[1][:5],[55,101,90,1,None]);connection.commit.assert_called_once()


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.mode=patch.dict(core.os.environ,{'TOUCHLINE_PROVIDER':'api-football'})
        self.mode.start();self.addCleanup(self.mode.stop)
        self.client=core.app.test_client()
        self.auth=patch.object(core,'sql',return_value=[{'user_id':1,'display_name':'Admin','role':'ADMIN'}]);self.auth.start();self.addCleanup(self.auth.stop)
        with self.client.session_transaction() as session:session.update(uid=1,sid='test',csrf='test')
        self.headers={'X-CSRF-Token':'test'}

    def test_save_uses_snapshot_without_network(self):
        with self.client.session_transaction() as session:session['api_football_preview']='digest'
        cache=Mock();cache.get.return_value={'fixtures':[{'external_id':123}]}
        with patch.object(services.af,'Cache',return_value=cache),patch.object(services,'save_snapshot',return_value=2) as save,patch.object(services,'db'):
            response=self.client.post('/api/import/save',json={'preview_id':'digest'},headers=self.headers)
        self.assertEqual(response.json,{'saved':2});cache.fetch.assert_not_called();save.assert_called_once()

    def test_empty_preview_disables_save_data_without_inventing_rows(self):
        cache=Mock();cache.fetch.return_value=payload([])
        with patch.object(services.af,'Cache',return_value=cache):
            response=self.client.post('/api/import/preview',json={},headers=self.headers)
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['rows'],[])

    def test_enrichment_only_pending_two(self):
        cache=Mock();cache.fetch.side_effect=[payload([fixture()]),payload([player()]),payload([])]
        with patch.object(services.af,'Cache',return_value=cache),patch.object(services,'sql',return_value=[{'external_id':123}]) as query:
            response=self.client.post('/api/import/preview',json={'kind':'enrichment'},headers=self.headers)
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['rows'][0]['player_records'],1)
        self.assertIn('LIMIT 2',query.call_args.args[0]);self.assertEqual(cache.fetch.call_count,3)

    def test_all_ten_reports_query_scoped_views(self):
        def query(stmt,args=()):
            self.assertIn('tl_v_',stmt)
            return [{'Field':'match_id'}] if stmt.startswith('SHOW') else []
        with patch.object(services,'sql',side_effect=query):
            for view in core.VIEWS:self.assertEqual(self.client.get('/api/reports/'+view).status_code,200)

    def test_legacy_mode_keeps_original_views_and_season(self):
        with patch.dict(os.environ,{'TOUCHLINE_PROVIDER':'football-data.org'}):
            page=self.client.get('/import')
            self.assertIn(b'2025/26',page.data);self.assertNotIn(b'id="import-kind"',page.data)
            with patch.object(services,'sql',side_effect=lambda stmt,args=(): [{'Field':'match_id'}] if stmt.startswith('SHOW') else []) as query:
                self.assertEqual(self.client.get('/api/reports/v_match_results').status_code,200)
                self.assertTrue(all('tl_' not in c.args[0] for c in query.call_args_list))

    def test_cross_tab_or_expired_preview_cannot_write(self):
        with self.client.session_transaction() as session:session['api_football_preview']='current'
        cache=Mock();cache.get.return_value=None
        with patch.object(services.af,'Cache',return_value=cache),patch.object(services,'db') as database:
            for digest in ('other','current'):
                response=self.client.post('/api/import/save',json={'preview_id':digest},headers=self.headers)
                self.assertEqual(response.status_code,409)
            database.assert_not_called()

    def test_new_provider_match_is_protected_from_crud(self):
        def query(stmt,args=()):
            if 'web_sessions' in stmt:return [{'user_id':1,'display_name':'Admin','role':'ADMIN'}]
            if 'imported_matches' in stmt:return []
            if stmt.startswith('SELECT'):return [{'match_id':55}]
            self.fail('Unexpected mutation: '+stmt)
        with patch.object(core,'sql',side_effect=query),patch.object(core,'db') as database:
            response=self.client.delete('/api/records/matches/55',headers=self.headers)
            self.assertEqual(response.status_code,409);database.assert_not_called()


if __name__=='__main__': unittest.main()

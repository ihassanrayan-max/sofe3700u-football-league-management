"""Frontend integration checks. No database connections or writes are made."""
import unittest
import tempfile
from unittest.mock import patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as core
import services

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.mode=patch.dict(core.os.environ,{'TOUCHLINE_PROVIDER':'api-football'})
        self.mode.start();self.addCleanup(self.mode.stop)
        # Every route test gets a real, isolated cache; never touch the local quota ledger.
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.cache=services.af.Cache(Path(temporary.name)/'api-football.sqlite3')
        self.enterContext(patch.object(services.af,'Cache',return_value=self.cache))
        self.client = core.app.test_client()
        self.role = 'ADMIN'
        self.auth = patch.object(core, 'sql', side_effect=lambda *args: [{'user_id': 1, 'display_name': 'Test <Admin>', 'role': self.role}])
        self.auth.start()
        with self.client.session_transaction() as session:
            session.update(uid=1, sid='test', csrf='test')

    def tearDown(self):
        self.auth.stop()

    def test_all_workspace_templates_render(self):
        for path, marker in [('/', b'Match centre'), ('/reports', b'report-filter'), ('/manage', b'editor-title'), ('/import', b'Fetch preview'), ('/login', b'Your seat awaits')]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(marker, response.data)
                self.assertNotIn(b'Test <Admin>', response.data)

    def test_guest_sees_only_permitted_features(self):
        self.role = 'GUEST'
        home = self.client.get('/').data
        self.assertIn(b'Match centre', home)
        for forbidden in [b'id="chart"', b'href="/manage"', b'href="/import"']:
            self.assertNotIn(forbidden, home)
        report = self.client.get('/reports').data
        self.assertNotIn(b'id="csv"', report)
        self.assertNotIn(b'value="v_league_standings"', report)
        self.assertEqual(self.client.get('/manage').status_code, 403)
        self.assertEqual(self.client.get('/api/reports/v_league_standings').status_code, 403)

    def test_reader_cannot_manage(self):
        self.role = 'USER'
        self.assertEqual(self.client.get('/import').status_code, 403)
        self.assertEqual(self.client.get('/api/records/teams').status_code, 403)
        self.assertIn(b'id="chart"', self.client.get('/').data)

    def test_anonymous_redirect_and_api_guard(self):
        with self.client.session_transaction() as session:
            session.clear()
        self.assertEqual(self.client.get('/').status_code, 302)
        self.assertEqual(self.client.get('/api/reports/v_match_results').status_code, 401)
        self.assertEqual(self.client.post('/api/logout', json={}).status_code, 403)

    def test_reports_and_exports_preserve_filter(self):
        def report_sql(query, args=()):
            if query.startswith('SHOW'):
                return [{'Field':'team_name'}, {'Field':'points'}]
            self.assertIn('LOCATE(%s', query)
            self.assertEqual(args, ['Arsenal'])
            return [{'team_name':'Arsenal', 'points':7}]
        with patch.object(services, 'sql', side_effect=report_sql):
            for fmt in ['json', 'csv', 'pdf']:
                response = self.client.get('/api/reports/v_league_standings?q=Arsenal&field=team_name&format='+fmt)
                self.assertEqual(response.status_code, 200)
                if fmt=='json': self.assertEqual(response.json['rows'][0]['points'],7)
                if fmt=='csv': self.assertIn(b'Arsenal,7', response.data)
                if fmt=='pdf': self.assertTrue(response.data.startswith(b'%PDF'))

    def test_group_branding_and_dashboard_contract(self):
        response=self.client.get('/')
        for marker in [b'GROUP 20', b'id="featured-match"', b'id="fixture-spotlight"', b'id="chart-measure"', b'id="chart-summary"']:
            self.assertIn(marker,response.data)
        self.assertNotIn(b'GROUP 12',response.data)
        self.assertNotIn(b'Live match',response.data)

    def test_all_ten_report_routes_keep_json_contract(self):
        with patch.object(services,'sql',side_effect=lambda stmt,args=(): [{'Field':'match_id'}] if stmt.startswith('SHOW') else []):
            for view in core.VIEWS:
                response=self.client.get('/api/reports/'+view)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json,{'columns':['match_id'],'rows':[]})

    def test_missing_provider_token_is_actionable(self):
        with patch.dict(core.os.environ,{'API_FOOTBALL_KEY':''}), patch.object(services.af,'urlopen') as provider, patch.object(self.cache,'reserve') as reserve:
            for state in ('absent','expired'):
                with self.subTest(cache=state):
                    if state=='expired':
                        self.cache.put('fixtures?league=39&season=2023',{'response':[]},ttl=-1)
                    response=self.client.post('/api/import/preview',json={},headers={'X-CSRF-Token':'test'})
                    self.assertEqual(response.status_code,503)
                    self.assertIn('API_FOOTBALL_KEY',response.json['error'])
                    self.assertIn('restart Flask',response.json['error'])
            provider.assert_not_called()
            reserve.assert_not_called()

    def test_missing_provider_token_preserves_valid_cached_preview(self):
        fixture={'league':{'id':39,'season':2023},
                 'fixture':{'id':123,'date':'2023-09-01T15:00:00Z','status':{'short':'FT'}},
                 'teams':{'home':{'id':42},'away':{'id':49}},'goals':{'home':2,'away':1}}
        payload={'errors':[],'results':1,'paging':{'current':1,'total':1},'response':[fixture]}
        self.cache.put('fixtures?league=39&season=2023',payload)
        with patch.dict(core.os.environ,{'API_FOOTBALL_KEY':''}), patch.object(services.af,'urlopen') as provider, patch.object(self.cache,'reserve') as reserve:
            response=self.client.post('/api/import/preview',json={},headers={'X-CSRF-Token':'test'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json['skipped'],0)
            self.assertEqual(len(response.json['rows']),1)
            row=response.json['rows'][0]
            self.assertEqual((row['external_id'],row['home_team'],row['away_team'],row['home_score'],row['away_score']),
                             (123,'Arsenal','Chelsea',2,1))
            digest=response.json['preview_id']
            self.assertEqual(self.cache.get('preview:'+digest),{'fixtures':response.json['rows']})
            with self.client.session_transaction() as session:
                self.assertEqual(session['api_football_preview'],digest)
            provider.assert_not_called()
            reserve.assert_not_called()

    def test_import_save_requires_matching_preview(self):
        with patch.object(services,'fetch_matches',return_value=([{'external_id':1}],0)), patch.object(services,'db') as connection:
            response=self.client.post('/api/import/save',json={},headers={'X-CSRF-Token':'test'})
            self.assertEqual(response.status_code,409)
            connection.assert_not_called()

    def test_duplicate_provider_ids_are_rejected(self):
        from io import BytesIO
        import json
        fixture={'id':1,'homeTeam':{'id':57},'awayTeam':{'id':61},
                 'competition':{'code':'PL'},'season':{'startDate':'2025-08-01'},
                 'status':'SCHEDULED','utcDate':'2025-09-06T15:00:00Z'}
        with patch.dict(core.os.environ,{'FOOTBALL_DATA_TOKEN':'unit-test-placeholder'}), patch.object(services,'urlopen',return_value=BytesIO(json.dumps({'matches':[fixture,fixture]}).encode())):
            with core.app.test_request_context():
                from werkzeug.exceptions import HTTPException
                with self.assertRaises(HTTPException) as caught:
                    services.fetch_matches()
                self.assertEqual(caught.exception.code,502)
                self.assertIn('duplicate',caught.exception.description)

if __name__ == '__main__':
    unittest.main()

"""Frontend integration checks. No database connections or writes are made."""
import unittest
from unittest.mock import patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as core
import services

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
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

if __name__ == '__main__':
    unittest.main()

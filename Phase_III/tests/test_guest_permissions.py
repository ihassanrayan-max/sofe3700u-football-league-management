"""Role authorization and directory filtering; no live database or provider calls."""
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as core
import services


class RoleAccessTests(unittest.TestCase):
    def setUp(self):
        self.client=core.app.test_client()
        self.role='GUEST'
        self.enterContext(patch.object(core,'sql',side_effect=self.query))
        with self.client.session_transaction() as session:
            session.update(uid=1,sid='test',csrf='test')
        self.headers={'X-CSRF-Token':'test'}
        self.database=sqlite3.connect(':memory:')
        self.addCleanup(self.database.close)
        self.database.row_factory=sqlite3.Row
        self.database.create_function('LOCATE',2,lambda query,name:name.lower().find(query.lower())+1)
        self.database.execute('CREATE TABLE teams(team_id INTEGER,team_name TEXT,city TEXT)')
        self.database.executemany('INSERT INTO teams VALUES(?,?,?)',[
            (1,'Arsenal','London'),(2,'Chelsea','London'),(3,'Liverpool','Liverpool'),
            (4,'Manchester City','Manchester'),(5,'Manchester United','Manchester'),
            (6,'Tottenham Hotspur','London'),(7,'Unrelated club','Private city')])

    def query(self,statement,args=()):
        if 'web_sessions' in statement:
            return [{'user_id':1,'display_name':'Guest <script>','role':self.role}]
        self.assertTrue(statement.startswith('SELECT'))
        return [dict(row) for row in self.database.execute(statement.replace('%s','?'),args)]

    def test_direct_webpage_access_for_all_roles(self):
        for role in ('ADMIN','USER','GUEST'):
            self.role=role
            for path in ('/','/reports','/manage','/import'):
                expected=200 if role=='ADMIN' or path=='/' or (role=='USER' and path=='/reports') else 403
                with self.subTest(role=role,path=path):
                    response=self.client.get(path)
                    self.assertEqual(response.status_code,expected)
                    if role=='GUEST' and expected==403:
                        self.assertIn(b'Access denied',response.data)
                        self.assertEqual(response.mimetype,'text/html')

    def test_every_report_and_export_is_denied_to_guests(self):
        with patch.object(services,'sql') as query:
            for name in core.VIEWS:
                for fmt in ('json','csv','pdf'):
                    with self.subTest(view=name,format=fmt):
                        response=self.client.get('/api/reports/'+name+'?format='+fmt)
                        self.assertEqual(response.status_code,403)
                        self.assertEqual(set(response.json),{'error'})
            query.assert_not_called()

    def test_admin_and_reader_keep_all_reports_and_exports(self):
        with patch.object(services,'sql',side_effect=lambda query,args=(): [{'Field':'match_id'}] if query.startswith('SHOW') else []):
            for role in ('ADMIN','USER'):
                self.role=role
                for name in core.VIEWS:
                    for fmt in ('json','csv','pdf'):
                        with self.subTest(role=role,view=name,format=fmt):
                            response=self.client.get('/api/reports/'+name+'?format='+fmt)
                            self.assertEqual(response.status_code,200)

    def test_crud_and_import_role_matrix_before_handlers(self):
        paths=[]
        for table in core.FIELDS:
            paths.extend([('GET','/api/records/'+table),('POST','/api/records/'+table),
                          ('GET','/api/records/'+table+'/1'),('PUT','/api/records/'+table+'/1'),
                          ('DELETE','/api/records/'+table+'/1')])
        paths.extend([('GET','/api/import/history'),('GET','/api/import/statistics?match_id=1'),
                      ('POST','/api/import/preview'),('POST','/api/import/save')])
        # Replace only route bodies: real authentication, CSRF and role guards still execute.
        for role in ('ADMIN','USER','GUEST'):
            self.role=role
            handler=Mock(return_value=({'ok':True},200))
            with patch.dict(core.app.view_functions,{'records':handler,'imports':handler}):
                for method,path in paths:
                    handler.reset_mock()
                    with self.subTest(role=role,method=method,path=path):
                        response=self.client.open(path,method=method,json={},headers=self.headers)
                        self.assertEqual(response.status_code,200 if role=='ADMIN' else 403)
                        if role=='ADMIN':handler.assert_called_once()
                        else:handler.assert_not_called()

    def test_directory_scope_fields_and_filters(self):
        cases=[({},[1,2,3,4,5,6]),({'q':'chester'},[4,5]),({'city':'London'},[1,2,6]),
               ({'q':'city','city':'Manchester'},[4]),({'q':"' OR 1=1 --"},[]),
               ({'city':'Private city'},[]),({'q':'%'},[])]
        for params,ids in cases:
            with self.subTest(filters=params):
                response=self.client.get('/api/teams',query_string=params)
                self.assertEqual(response.status_code,200)
                self.assertEqual(sorted(r['team_id'] for r in response.json),ids)
                for row in response.json:self.assertEqual(set(row),{'team_id','team_name','city'})

    def test_directory_validates_queries_and_is_read_only(self):
        for params in ({'format':'csv'},{'field':'password_hash'},{'q':'x'*101},{'city':'x'*81}):
            self.assertEqual(self.client.get('/api/teams',query_string=params).status_code,400)
        for method in ('POST','PUT','DELETE'):
            self.assertIn(self.client.open('/api/teams',method=method,json={},headers=self.headers).status_code,(403,405))

    def test_guest_alternate_methods_cannot_reach_restricted_handlers(self):
        handler=Mock(return_value=({'restricted':'must never be returned'},200))
        paths=['/reports','/manage','/import','/api/reports/v_match_results',
               '/api/records/players/1','/api/records/matches','/api/import/history',
               '/api/import/statistics?match_id=1','/api/import/preview']
        with patch.dict(core.app.view_functions,{'page':handler,'reports':handler,'records':handler,'imports':handler}):
            for path in paths:
                for method in ('HEAD','OPTIONS','PATCH','TRACE','POST','PUT','DELETE'):
                    with self.subTest(path=path,method=method):
                        response=self.client.open(path,method=method,json={},headers=self.headers)
                        self.assertIn(response.status_code,(403,405))
                        self.assertNotIn(b'must never be returned',response.data)
            handler.assert_not_called()

    def test_guest_cannot_override_database_role_with_request_claims(self):
        with self.client.session_transaction() as session:
            session['role']='ADMIN'  # Even a signed but stale role claim is ignored.
        handler=Mock(return_value=({'ok':True},200))
        with patch.dict(core.app.view_functions,{'records':handler,'imports':handler,'reports':handler}):
            for path in ('/api/reports/v_player_totals?role=ADMIN','/api/records/users?role=ADMIN','/api/import/history?role=ADMIN'):
                self.assertEqual(self.client.get(path,headers={'X-Role':'ADMIN'}).status_code,403)
            response=self.client.post('/api/import/save',json={'role':'ADMIN'},headers={**self.headers,'X-Role':'ADMIN'})
            self.assertEqual(response.status_code,403)
            handler.assert_not_called()

    def test_directory_projection_and_role_specific_dashboard_payloads(self):
        import json
        import re
        original_query=self.query
        def query(statement,args=()):
            if statement.startswith('SELECT team_id,team_name,city'):
                return [{'team_id':1,'team_name':'Arsenal','city':'London','restricted_extra':'must not leak'}]
            return original_query(statement,args)
        with patch.object(core,'sql',side_effect=query):
            self.assertEqual(self.client.get('/api/teams').json,[{'team_id':1,'team_name':'Arsenal','city':'London'}])
        home=self.client.get('/').data.decode()
        config=json.loads(re.search(r'<script id="config" type="application/json">(.*?)</script>',home)[1])
        self.assertEqual(set(config),{'csrf'})
        for forbidden in ('featured-match','fixture-spotlight','standings','leaders','report-filter','/api/reports','/api/import'):
            self.assertNotIn(forbidden,home)
        for role in ('ADMIN','USER'):
            self.role=role
            home=self.client.get('/').data
            for marker in (b'id="chart"',b'id="featured-match"',b'id="standings"',b'id="leaders"',b'href="/reports"',b'/static/ui.js'):
                self.assertIn(marker,home)
            self.assertNotIn(b'/static/guest.js',home)

    def test_guest_html_is_directory_only_with_escaped_filters(self):
        response=self.client.get('/',query_string={'q':'<script>'})
        self.assertEqual(response.status_code,200)
        self.assertIn(b'No teams found',response.data)
        self.assertIn(b'&lt;script&gt;',response.data)
        for value in (b'<script>',b'Match centre',b'Goal leaders',b'id="chart"',b'chart.umd',b'href="/reports',b'/static/ui.js',b'player_match_stats'):
            self.assertNotIn(value,response.data)
        home=self.client.get('/').data
        self.assertIn(b'Arsenal',home)
        self.assertNotIn(b'Unrelated club',home)
        self.assertNotIn(b'Private city',home)
        self.assertIn(b'/static/guest.js',home)

    def test_anonymous_and_expired_sessions_cannot_read_directory(self):
        with patch.object(core,'sql',return_value=[]):
            self.assertEqual(self.client.get('/api/teams').status_code,401)
        self.assertEqual(self.client.get('/api/teams').status_code,401)
        self.assertEqual(self.client.get('/').status_code,302)

    def test_login_page_and_logout_remain_available(self):
        self.assertEqual(self.client.get('/login').status_code,200)
        with patch.object(core,'sql') as query,patch.object(core,'db') as connection:
            response=self.client.post('/api/logout',json={},headers=self.headers)
            self.assertEqual(response.status_code,200)
            query.assert_called_once_with('DELETE FROM web_sessions WHERE session_id=%s',['test'])
            connection.return_value.commit.assert_called_once()
        self.assertEqual(self.client.get('/api/teams').status_code,401)

    def test_guest_can_authenticate_with_existing_hash_and_csrf(self):
        password='offline-test-password'
        hashed=core.generate_password_hash(password)
        def query(statement,args=()):
            if statement.startswith('SELECT user_id,password_hash'):
                return [{'user_id':5,'password_hash':hashed}]
            return []
        with patch.object(core,'sql',side_effect=query),patch.object(core,'db') as connection:
            self.assertEqual(self.client.post('/api/login',json={'email':'guest.one@example.com','password':password}).status_code,403)
            response=self.client.post('/api/login',json={'email':'guest.one@example.com','password':password},headers=self.headers)
            self.assertEqual(response.status_code,200)
            connection.return_value.commit.assert_called_once()
        with self.client.session_transaction() as session:
            self.assertEqual(session['uid'],5)
            self.assertNotEqual(session['sid'],'test')


if __name__=='__main__':unittest.main()

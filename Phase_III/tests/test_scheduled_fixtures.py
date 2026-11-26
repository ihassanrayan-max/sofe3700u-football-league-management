"""Offline scheduled-report regression fixtures; never application records."""
import csv
import io
from pathlib import Path
import re
import sqlite3
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import app as core
import services
from test_api_football import fixture, payload


class ScheduledReportTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.row_factory=sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.create_function('LOCATE',2,lambda q,v:str(v).lower().find(q.lower())+1)
        self.db.executescript('''
        CREATE TABLE competitions(competition_id PRIMARY KEY,competition_name);
        CREATE TABLE seasons(season_id PRIMARY KEY,competition_id,season_label);
        CREATE TABLE teams(team_id PRIMARY KEY,team_name);
        CREATE TABLE season_teams(season_id,team_id,PRIMARY KEY(season_id,team_id));
        CREATE TABLE matches(match_id PRIMARY KEY,season_id,home_team_id,away_team_id,kickoff_at,match_status,is_synthetic);
        CREATE TABLE provider_matches(provider,external_id,match_id,PRIMARY KEY(provider,external_id));
        INSERT INTO competitions VALUES(1,'Premier League'),(2,'Other league');
        INSERT INTO seasons VALUES(1,1,'2023/24'),(2,1,'2025/26'),(3,2,'2023/24');
        INSERT INTO teams VALUES(1,'Arsenal'),(2,'Chelsea'),(3,'Outside club');
        INSERT INTO season_teams VALUES(1,1),(1,2),(1,3),(2,1),(2,2),(3,1),(3,2);
        ''')
        # Extract and execute the real scoped filter and report definitions.
        canonical=(ROOT/'06_api_football.sql').read_text(encoding='utf-8')
        for name in ('tl_seasons','tl_season_teams','tl_matches','tl_v_scheduled_fixtures'):
            sql=re.search(r'CREATE SQL SECURITY INVOKER VIEW '+name+r' AS.*?;',canonical,re.S)[0]
            self.db.execute(sql.replace(' SQL SECURITY INVOKER',''))
        original=(ROOT.parent/'03_create_views.sql').read_text(encoding='utf-8')
        self.db.execute(re.search(r'CREATE OR REPLACE VIEW v_scheduled_fixtures AS.*?;',original,re.S)[0].replace(' OR REPLACE',''))
        self.client=core.app.test_client()
        with self.client.session_transaction() as session:session.update(uid=1,sid='test',csrf='test')
        self.role='USER'
        self.enterContext(patch.dict(core.os.environ,{'TOUCHLINE_PROVIDER':'api-football'}))
        self.enterContext(patch.object(core,'sql',side_effect=lambda *args:[{'user_id':1,'display_name':'Test','role':self.role}]))
        self.report_query=self.enterContext(patch.object(services,'sql',side_effect=self.query))

    def query(self,sql,args=()):
        if sql.startswith('SHOW COLUMNS FROM '):
            return [{'Field':r['name']} for r in self.db.execute('PRAGMA table_info('+sql.split()[-1]+')')]
        self.assertTrue(sql.startswith('SELECT'))
        return [dict(r) for r in self.db.execute(sql.replace('%s','?'),args)]

    def add(self,mid,status='SCHEDULED',season=1,synthetic=0,provider='api-football',away=2,date='2023-09-01 15:00:00'):
        self.db.execute('INSERT INTO matches VALUES(?,?,1,?,?,?,?)',(mid,season,away,date,status,synthetic))
        if provider:self.db.execute('INSERT INTO provider_matches VALUES(?,?,?)',(provider,mid,mid))

    def report(self,suffix=''):return self.client.get('/api/reports/v_scheduled_fixtures'+suffix)

    def test_scope_status_chronology_and_no_duplicate_counting(self):
        self.add(9,date='2023-08-01 15:00:00');self.add(1)
        self.add(2,status='COMPLETED');self.add(3,season=2)
        self.add(4,synthetic=1);self.add(5,provider='football-data.org')
        self.add(6,away=3);self.add(7,season=3);self.add(8,provider=None)
        self.db.execute("INSERT INTO provider_matches VALUES('football-data.org',999,9)")
        before=[tuple(r) for r in self.db.execute('SELECT * FROM matches ORDER BY match_id')]
        response=self.report()
        self.assertEqual(response.status_code,200)
        self.assertEqual([r['match_id'] for r in response.json['rows']],[9,1])
        for row in response.json['rows']:
            self.assertEqual((row['match_status'],row['season_label'],row['is_synthetic']),('SCHEDULED','2023/24',0))
        self.assertEqual(before,[tuple(r) for r in self.db.execute('SELECT * FROM matches ORDER BY match_id')])

    def test_completed_only_and_filtered_empty_exports(self):
        self.add(1,status='COMPLETED')
        self.assertEqual(self.report().json['rows'],[])
        for suffix,expected in (('?format=pdf','No scheduled fixtures are available'),('?format=pdf&q=Chelsea','No scheduled fixtures match the current search')):
            with patch.object(services,'Paragraph',wraps=services.Paragraph) as paragraph:
                response=self.report(suffix)
                self.assertEqual(response.status_code,200)
                self.assertTrue(response.data.startswith(b'%PDF'))
                texts=' '.join(str(c.args[0]) for c in paragraph.call_args_list)
                self.assertIn(expected,texts)
                self.assertIn('2023/24 is a completed season',texts)
        csv_response=self.report('?format=csv')
        self.assertIn('Match Status',csv_response.text)
        self.assertEqual(list(csv.DictReader(io.StringIO(csv_response.text))),[])

    def test_search_fields_and_exports_for_admin_reader(self):
        self.add(1)
        for role in ('ADMIN','USER'):
            self.role=role
            for field,q in (('home_team','Arsenal'),('match_status','SCHEDULED'),('season_label','2023/24')):
                for fmt in ('json','csv','pdf'):
                    response=self.report('?format='+fmt+'&field='+field+'&q='+q)
                    self.assertEqual(response.status_code,200)
                    if fmt=='json':self.assertEqual(len(response.json['rows']),1)
                    if fmt=='csv':
                        row=list(csv.DictReader(io.StringIO(response.text)))[0]
                        self.assertEqual((row['Match Status'],row['Season Label']),('SCHEDULED','2023/24'))
                    if fmt=='pdf':self.assertTrue(response.data.startswith(b'%PDF'))
        self.assertEqual(self.report('?field=season_label&q=2025').json['rows'],[])

    def test_guest_direct_access_and_methods(self):
        self.role='GUEST'
        for fmt in ('json','csv','pdf'):self.assertEqual(self.report('?format='+fmt).status_code,403)
        self.assertEqual(self.client.get('/reports?view=v_scheduled_fixtures').status_code,403)
        for method in ('post','put','delete'):
            response=getattr(self.client,method)('/api/reports/v_scheduled_fixtures',headers={'X-CSRF-Token':'test'})
            self.assertIn(response.status_code,(403,405))
        self.report_query.assert_not_called()

    def test_existing_legacy_mode_keeps_fictional_rows_separate(self):
        self.add(1,status='COMPLETED');self.add(2,season=2,synthetic=1,provider=None)
        self.assertEqual(self.report().json['rows'],[])
        with patch.dict(core.os.environ,{'TOUCHLINE_PROVIDER':'football-data.org'}):
            row=self.report().json['rows'][0]
            self.assertEqual((row['match_id'],row['is_synthetic'],row['season_label']),(2,1,'2025/26'))

    def test_provider_statuses_do_not_infer_from_dates(self):
        for status,expected in (('FT','COMPLETED'),('NS','SCHEDULED')):
            item=fixture();item['fixture']['status']['short']=status
            rows,skipped=services.af.parse_fixtures(payload([item]))
            self.assertEqual((rows[0]['match_status'],skipped),(expected,0))
        for status in ('PST','CANC','ABD','1H'):
            item=fixture();item['fixture']['status']['short']=status
            self.assertEqual(services.af.parse_fixtures(payload([item])),([],1))


if __name__=='__main__':unittest.main()

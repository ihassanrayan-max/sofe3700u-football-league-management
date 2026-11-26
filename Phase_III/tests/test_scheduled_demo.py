"""Execute the shipped demo seed and report queries offline; no MySQL writes."""
import csv
import io
import re
import unittest
from unittest.mock import patch
import test_scheduled_fixtures as baseline
from test_scheduled_fixtures import ROOT,core,services


class ScheduledDemoTests(unittest.TestCase):
    def setUp(self):
        baseline.ScheduledReportTests.setUp(self)
        self.db.commit()
        self.db.execute('PRAGMA foreign_keys=ON')
    add=baseline.ScheduledReportTests.add
    report=baseline.ScheduledReportTests.report

    def query(self,sql,args=()):
        if 'information_schema.VIEWS' in sql:
            return [dict(r) for r in self.db.execute("SELECT 1 FROM sqlite_master WHERE type='view' AND name='tl_demo_v_scheduled_fixtures'")]
        return baseline.ScheduledReportTests.query(self,sql,args)

    def seed(self):
        text=(ROOT/'08_scheduled_demo.sql').read_text(encoding='utf-8')
        text=re.sub(r'--[^\n]*','',text)
        for statement in text.split(';'):
            statement=statement.strip()
            if not statement or statement in ('START TRANSACTION','COMMIT'):continue
            statement=statement.replace('INT AUTO_INCREMENT PRIMARY KEY','INTEGER PRIMARY KEY AUTOINCREMENT')
            statement=statement.replace(' ENGINE=InnoDB','').replace('CREATE OR REPLACE SQL SECURITY INVOKER VIEW','CREATE VIEW IF NOT EXISTS')
            self.db.execute(statement)

    def prepare(self):
        # IDs deliberately differ from provider IDs; no assumption about 73-75.
        self.db.executemany('INSERT INTO teams VALUES(?,?)',[(44,'Manchester United'),(55,'Liverpool'),(66,'Tottenham Hotspur'),(77,'Manchester City')])
        self.seed()

    def test_seed_repeated_preserves_ids_and_all_existing_records(self):
        self.add(73,status='COMPLETED')
        before=[tuple(r) for r in self.db.execute('SELECT * FROM matches')]
        mappings=[tuple(r) for r in self.db.execute('SELECT * FROM provider_matches')]
        self.prepare()
        initial=[tuple(r) for r in self.db.execute('SELECT * FROM tl_demo_fixtures ORDER BY match_id')]
        self.seed()
        self.assertEqual(initial,[tuple(r) for r in self.db.execute('SELECT * FROM tl_demo_fixtures ORDER BY match_id')])
        self.assertEqual(len(initial),3)
        self.assertEqual(before,[tuple(r) for r in self.db.execute('SELECT * FROM matches')])
        self.assertEqual(mappings,[tuple(r) for r in self.db.execute('SELECT * FROM provider_matches')])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM tl_demo_season_teams').fetchone()[0],6)
        self.assertEqual(self.report().json['rows'],[])

    def test_explicit_source_only_correct_fixture_values(self):
        self.prepare()
        response=self.report('?source=phase2-demo')
        self.assertEqual(response.status_code,200)
        rows=response.json['rows']
        self.assertEqual([(r['home_team'],r['away_team'],r['kickoff_at']) for r in rows],[
            ('Manchester United','Arsenal','2024-05-19 16:00:00'),
            ('Chelsea','Liverpool','2024-05-22 19:45:00'),
            ('Tottenham Hotspur','Manchester City','2024-05-26 15:00:00')])
        self.assertTrue(all(r['match_status']=='SCHEDULED' and r['data_source']=='Synthetic demonstration' for r in rows))
        self.assertEqual(self.report().json['rows'],[])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM v_scheduled_fixtures').fetchone()[0],0)
        self.assertEqual(self.client.get('/api/reports/v_player_totals?source=phase2-demo').status_code,400)
        self.assertEqual(self.report('?source=unknown').status_code,400)

    def test_missing_install_actionable_and_default_unaffected(self):
        response=self.report('?source=phase2-demo')
        self.assertEqual(response.status_code,503)
        self.assertIn('08_scheduled_demo.sql',response.json['error'])
        self.assertEqual(self.report().status_code,200)

    def test_search_exports_roles_and_no_guest_queries(self):
        self.prepare()
        for role in ('ADMIN','USER'):
            self.role=role
            for fmt in ('json','csv','pdf'):
                with patch.object(services,'Paragraph',wraps=services.Paragraph) as paragraph:
                    response=self.report('?source=phase2-demo&q=Chelsea&field=home_team&format='+fmt)
                    self.assertEqual(response.status_code,200)
                    if fmt=='json':self.assertEqual(len(response.json['rows']),1)
                    if fmt=='csv':
                        rows=list(csv.DictReader(io.StringIO(response.text)))
                        self.assertEqual(len(rows),1)
                        self.assertEqual(rows[0]['Data Source'],'Synthetic demonstration')
                    if fmt=='pdf':
                        self.assertTrue(response.data.startswith(b'%PDF'))
                        self.assertIn('fictional fixtures',' '.join(str(c.args[0]) for c in paragraph.call_args_list))
        self.role='GUEST';self.report_query.reset_mock()
        for fmt in ('json','csv','pdf'):self.assertEqual(self.report('?source=phase2-demo&format='+fmt).status_code,403)
        self.report_query.assert_not_called()

    def test_seed_writes_only_new_demo_tables(self):
        sql=re.sub(r'--[^\n]*','',(ROOT/'08_scheduled_demo.sql').read_text())
        self.assertNotRegex(sql,r'(?i)\b(DELETE|UPDATE|TRUNCATE|DROP|ALTER|IGNORE)\b')
        self.assertEqual(set(re.findall(r'INSERT INTO (\w+)',sql)),{'tl_demo_seasons','tl_demo_season_teams','tl_demo_fixtures'})
        self.assertEqual(re.findall(r'CREATE OR REPLACE SQL SECURITY INVOKER VIEW (\w+)',sql),['tl_demo_v_scheduled_fixtures'])
        self.assertNotIn('NOT EXISTS(SELECT',sql) # MySQL target-table subquery restriction.

    def test_memberships_status_and_uniqueness_are_enforced(self):
        import sqlite3
        self.prepare()
        row=self.db.execute('SELECT * FROM tl_demo_fixtures LIMIT 1').fetchone()
        season=row['season_id']
        for home,away,status,synthetic in ((1,3,'SCHEDULED',1),(1,2,'COMPLETED',1),(1,2,'SCHEDULED',0),(1,1,'SCHEDULED',1)):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute('INSERT INTO tl_demo_fixtures(season_id,home_team_id,away_team_id,kickoff_at,match_status,is_synthetic) VALUES(?,?,?,\'2024-05-20 16:00:00\',?,?)',(season,home,away,status,synthetic))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO tl_demo_fixtures(season_id,home_team_id,away_team_id,kickoff_at) VALUES(?,?,?,?)',(season,row['home_team_id'],row['away_team_id'],row['kickoff_at']))


if __name__=='__main__':unittest.main()

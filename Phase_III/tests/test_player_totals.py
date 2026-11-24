"""Execute the production aggregate offline; no MySQL or provider access."""
import csv
import io
import re
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as core
import services


class PlayerTotalsTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript('''CREATE TABLE teams(team_id PRIMARY KEY,team_name);
            CREATE TABLE tl_players(player_id PRIMARY KEY,full_name,team_id,position);
            CREATE TABLE tl_player_match_stats(match_id,player_id,minutes_played,goals,assists,PRIMARY KEY(match_id,player_id));
            INSERT INTO teams VALUES(1,'Club'); INSERT INTO tl_players VALUES(1,'Player',1,'MID');''')
        canonical = (ROOT/'06_api_football.sql').read_text(encoding='utf-8')
        self.view = re.search(r'CREATE SQL SECURITY INVOKER VIEW tl_v_player_totals AS.*?;',canonical,re.S)[0]
        self.db.execute(self.view.replace(' SQL SECURITY INVOKER',''))

    def totals(self, goals, assists=None):
        self.db.executemany('INSERT INTO tl_player_match_stats VALUES(?,1,90,?,?)',
            [(i,g,a) for i,(g,a) in enumerate(zip(goals, assists or [None]*len(goals)))])
        return dict(self.db.execute('SELECT * FROM tl_v_player_totals').fetchone())

    def test_partial_positive(self):
        row=self.totals([None,2,1])
        self.assertEqual((row['recorded_goals'],row['known_goal_appearances'],row['unknown_goal_appearances']),(3,2,1))

    def test_all_unknown(self):
        row=self.totals([None,None])
        self.assertIsNone(row['recorded_goals'])
        self.assertEqual((row['known_goal_appearances'],row['unknown_goal_appearances']),(0,2))

    def test_zero_partial(self):
        row=self.totals([0,None])
        self.assertEqual((row['recorded_goals'],row['unknown_goal_appearances']),(0,1))

    def test_complete_observed(self):
        row=self.totals([1,1])
        self.assertEqual((row['recorded_goals'],row['recorded_appearances'],row['unknown_goal_appearances']),(2,2,0))

    def test_assists_independent(self):
        row=self.totals([None,None,None],[None,2,1])
        self.assertIsNone(row['recorded_goals'])
        self.assertEqual((row['recorded_assists'],row['known_assist_appearances'],row['unknown_assist_appearances']),(3,2,1))

    def test_assist_zero_and_unknown(self):
        row=self.totals([1,1],[0,None])
        self.assertEqual((row['recorded_assists'],row['unknown_assist_appearances']),(0,1))

    def test_duplicate_appearance_rejected(self):
        self.totals([1])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO tl_player_match_stats VALUES(0,1,90,1,NULL)')
        self.assertEqual(self.db.execute('SELECT recorded_goals FROM tl_v_player_totals').fetchone()[0],1)

    def test_zero_export_is_not_blank(self):
        row=self.totals([0,None],[None,None])
        client=core.app.test_client()
        with client.session_transaction() as session: session.update(uid=1,sid='test',csrf='test')
        with patch.dict(core.os.environ,{'TOUCHLINE_PROVIDER':'api-football'}), \
             patch.object(core,'sql',return_value=[{'user_id':1,'display_name':'Test','role':'USER'}]), \
             patch.object(services,'sql',side_effect=lambda q,args=(): [{'Field':c} for c in row] if q.startswith('SHOW') else [row]):
            response=client.get('/api/reports/v_player_totals?format=csv')
            self.assertEqual(response.status_code,200)
            exported=list(csv.DictReader(io.StringIO(response.text)))[0]
            self.assertEqual(exported['Recorded Goals'],'0')
            self.assertEqual(exported['Recorded Assists'],'')

    def test_migration_only_replaces_target_with_canonical_definition(self):
        script=(ROOT/'07_player_totals.sql').read_text(encoding='utf-8')
        sql=re.sub(r'--[^\n]*','',script).strip()
        self.assertEqual(sql,'USE group12_football_phase2;\n'+self.view.replace('CREATE SQL','CREATE OR REPLACE SQL'))
        for filename in ('07_player_totals_preflight.sql','07_player_totals_verify.sql'):
            read_only=re.sub(r'--[^\n]*','',(ROOT/filename).read_text(encoding='utf-8'))
            self.assertNotRegex(read_only,r'(?i)\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)\b(?!\s+VIEW)')

    def test_report_exports_and_roles(self):
        row=self.totals([None,2,1])
        client=core.app.test_client()
        with client.session_transaction() as session: session.update(uid=1,sid='test',csrf='test')
        def query(statement,args=()):
            if statement.startswith('SHOW'): return [{'Field':c} for c in row]
            self.assertIn('tl_v_player_totals',statement)
            return [row]
        with patch.dict(core.os.environ,{'TOUCHLINE_PROVIDER':'api-football'}),patch.object(services,'sql',side_effect=query) as report:
            for role in ('ADMIN','USER','GUEST'):
                with patch.object(core,'sql',return_value=[{'user_id':1,'display_name':'Test','role':role}]):
                    for fmt in ('json','csv','pdf'):
                        response=client.get('/api/reports/v_player_totals?format='+fmt)
                        self.assertEqual(response.status_code,403 if role=='GUEST' else 200)
                        if role=='GUEST': continue
                        if fmt=='json': self.assertEqual(response.json['rows'],[row])
                        if fmt=='csv':
                            exported=list(csv.DictReader(io.StringIO(response.text)))[0]
                            self.assertEqual(exported['Recorded Goals'],'3')
                            self.assertEqual(exported['Recorded Assists'],'')
                            self.assertEqual(exported['Unknown Goal Appearances'],'1')
                        if fmt=='pdf': self.assertTrue(response.data.startswith(b'%PDF'))
                    if role=='GUEST':
                        before=report.call_count
                        self.assertEqual(client.get('/api/reports/v_player_totals').status_code,403)
                        self.assertEqual(report.call_count,before)


if __name__=='__main__': unittest.main()

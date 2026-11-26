"""Offline execution of the canonical aggregate; MySQL ANY selection is adapted
to MIN in SQLite (equivalent TRUE matches, including empty/all-NULL sets)."""
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

class GoalComparisonTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.create_function('LOCATE',2,lambda q,v:str(v).lower().find(q.lower())+1)
        self.db.executescript("""
        CREATE TABLE teams(team_id PRIMARY KEY,team_name);
        CREATE TABLE tl_players(player_id PRIMARY KEY,full_name,team_id);
        CREATE TABLE tl_player_match_stats(match_id,player_id,goals,PRIMARY KEY(match_id,player_id));
        INSERT INTO teams VALUES(1,'Club A'),(2,'Club B'),(3,'Club C');
        INSERT INTO tl_players VALUES(1,'Player A',1),(2,'Player B',2),(3,'Player C',3);
        """)
        sql=(ROOT/'06_api_football.sql').read_text(encoding='utf-8')
        self.definition=re.search(r'CREATE SQL SECURITY INVOKER VIEW tl_v_above_any_team_goal_total AS.*?;',sql,re.S)[0]
        prefix,sub=self.definition.split('HAVING SUM(s.goals) > ANY (')
        inner=sub.rsplit(')',1)[0].replace('SELECT SUM(s2.goals)','SELECT SUM(s2.goals) AS team_goals')
        adapted=prefix.replace(' SQL SECURITY INVOKER','')+'HAVING SUM(s.goals) > (SELECT MIN(team_goals) FROM ('+inner+') AS team_totals)'
        self.db.execute(adapted)

    def fill(self,groups):
        for pid,values in enumerate(groups,1):
            self.db.executemany('INSERT INTO tl_player_match_stats VALUES(?,?,?)',[(i,pid,v) for i,v in enumerate(values)])
    def rows(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM tl_v_above_any_team_goal_total ORDER BY recorded_goals DESC,player_id')]

    def test_partial_player_and_team_subtotals_qualify(self):
        self.fill([[None,2,1],[None,1],[None,None]])
        self.assertEqual([(r['player_id'],r['recorded_goals']) for r in self.rows()],[(1,3)])

    def test_equal_totals_and_unknown_only_teams_do_not_qualify(self):
        self.fill([[None,1],[1],[None]])
        self.assertEqual(self.rows(),[])

    def test_explicit_zero_is_valid_comparison_not_unknown(self):
        self.fill([[2,None],[0,None],[None]])
        self.assertEqual([r['player_id'] for r in self.rows()],[1])

    def test_empty_and_all_unknown_sets(self):
        self.assertEqual(self.rows(),[])
        self.fill([[None],[None],[None]])
        self.assertEqual(self.rows(),[])

    def test_any_is_at_least_one_not_every_team(self):
        self.fill([[4],[1],[10]])
        self.assertEqual([r['player_id'] for r in self.rows()],[3,1])

    def test_migration_only_replaces_target_with_canonical_any(self):
        sql=re.sub(r'--[^\n]*','',(ROOT/'09_player_goal_comparison.sql').read_text()).strip()
        self.assertEqual(sql,self.definition.replace('CREATE SQL','CREATE OR REPLACE SQL'))
        self.assertIn('> ANY (',sql)
        self.assertNotIn('COUNT(',sql)
        self.assertNotRegex(sql,r'(?i)\b(INSERT|DELETE|UPDATE|DROP|ALTER|TRUNCATE)\b')

    def test_endpoints_labels_exports_and_roles(self):
        self.fill([[None,2,1],[1],[None]])
        client=core.app.test_client()
        with client.session_transaction() as session:session.update(uid=1,sid='test',csrf='test')
        def query(statement,args=()):
            if statement.startswith('SHOW'):
                return [{'Field':r['name']} for r in self.db.execute('PRAGMA table_info(tl_v_above_any_team_goal_total)')]
            return [dict(r) for r in self.db.execute(statement.replace('%s','?'),args)]
        with patch.dict(core.os.environ,{'TOUCHLINE_PROVIDER':'api-football'}),patch.object(services,'sql',side_effect=query) as report:
            for role in ('ADMIN','USER','GUEST'):
                with patch.object(core,'sql',return_value=[{'user_id':1,'display_name':'Test','role':role}]):
                    before=report.call_count
                    for fmt in ('json','csv','pdf'):
                        with patch.object(services,'Paragraph',wraps=services.Paragraph) as paragraph:
                            response=client.get('/api/reports/v_above_any_team_goal_total?format='+fmt)
                            self.assertEqual(response.status_code,403 if role=='GUEST' else 200)
                            if role=='GUEST':continue
                            if fmt=='json':self.assertEqual(response.json['rows'][0]['recorded_goals'],3)
                            if fmt=='csv':self.assertEqual(list(csv.DictReader(io.StringIO(response.text)))[0]['Recorded Goals'],'3')
                            if fmt=='pdf':
                                texts=[str(c.args[0]) for c in paragraph.call_args_list]
                                self.assertIn('Player Goal Comparison',texts)
                                self.assertTrue(any('strict SQL ANY' in t for t in texts))
                    if role=='GUEST':self.assertEqual(report.call_count,before)
                    else:
                        html=client.get('/reports').text
                        self.assertIn('2 · Player Goal Comparison',html)
                        self.assertIn('value="v_above_any_team_goal_total"',html)

if __name__=='__main__':unittest.main()

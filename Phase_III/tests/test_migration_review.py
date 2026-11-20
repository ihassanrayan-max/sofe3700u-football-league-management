"""Offline migration checks; never connect to MySQL or read the private backup."""
from pathlib import Path
import re
import sqlite3
import unittest

ROOT=Path(__file__).resolve().parents[1]
SQL=re.sub(r'--[^\n]*','',(ROOT/'06_api_football.sql').read_text())
STATEMENTS=[s.strip() for s in SQL.split(';') if s.strip()]
INSERTS=[s for s in STATEMENTS if s.startswith('INSERT INTO')]


class MigrationReviewTests(unittest.TestCase):
    def test_no_destructive_or_silent_overwrite_operations(self):
        self.assertNotRegex(SQL,r'(?i)\b(DROP|TRUNCATE|DELETE|UPDATE|REPLACE|IGNORE|ALTER)\b')
        self.assertNotIn('IF NOT EXISTS',SQL)
        self.assertNotIn('FOREIGN_KEY_CHECKS',SQL.upper())

    def test_exact_additive_objects_and_original_views_untouched(self):
        tables=re.findall(r'CREATE TABLE (\w+)',SQL)
        self.assertEqual(set(tables),{'provider_teams','provider_matches','provider_players',
            'provider_player_stats','provider_team_stats','provider_enrichment'})
        views=re.findall(r'CREATE SQL SECURITY INVOKER VIEW (\w+)',SQL)
        self.assertEqual(len(views),15)
        original=re.findall(r'CREATE OR REPLACE VIEW (\w+)',(ROOT.parent/'03_create_views.sql').read_text())
        self.assertEqual({v for v in views if v.startswith('tl_v_')},{'tl_'+v for v in original})
        self.assertTrue(all(v.startswith('tl_') for v in views))

    def test_no_insert_target_subquery_and_only_permitted_data_additions(self):
        self.assertEqual(len(INSERTS),3)
        self.assertEqual({re.match(r'INSERT INTO (\w+)',s)[1] for s in INSERTS},
                         {'seasons','season_teams','provider_matches'})
        for statement in INSERTS:
            self.assertEqual(len(re.findall(r'\bSELECT\b',statement)),1)

    def test_foreign_keys_reference_existing_parents_in_creation_order(self):
        known={'teams','matches'}
        for statement in STATEMENTS:
            if not statement.startswith('CREATE TABLE'):continue
            name=re.match(r'CREATE TABLE (\w+)',statement)[1]
            for parent in re.findall(r'REFERENCES (\w+)\(',statement):self.assertIn(parent,known)
            self.assertNotIn('CASCADE',statement)
            known.add(name)

    def test_validation_scripts_are_read_only(self):
        for name in ('06_api_football_preflight.sql','06_api_football_verify.sql'):
            content=re.sub(r'--[^\n]*','',(ROOT/name).read_text())
            for statement in content.split(';'):
                if statement.strip():self.assertRegex(statement.strip(),r'^(SELECT|USE)\b')

    def test_insert_semantics_preserve_old_season_and_provider_ids(self):
        # Only the three portable INSERT statements are exercised in memory.
        # This does not validate MySQL DDL, view compilation, or server privileges.
        con=sqlite3.connect(':memory:');self.addCleanup(con.close)
        con.executescript('''CREATE TABLE competitions(competition_id INTEGER PRIMARY KEY,competition_name TEXT UNIQUE);
        CREATE TABLE seasons(season_id INTEGER PRIMARY KEY,competition_id INTEGER,season_label TEXT,start_date TEXT,end_date TEXT,UNIQUE(competition_id,season_label));
        CREATE TABLE teams(team_id INTEGER PRIMARY KEY,team_name TEXT);
        CREATE TABLE season_teams(season_id INTEGER,team_id INTEGER,PRIMARY KEY(season_id,team_id));
        CREATE TABLE imported_matches(external_id INTEGER PRIMARY KEY,match_id INTEGER UNIQUE);
        CREATE TABLE provider_matches(provider TEXT,external_id INTEGER,match_id INTEGER,PRIMARY KEY(provider,external_id),UNIQUE(provider,match_id));
        INSERT INTO competitions VALUES(77,'Premier League');
        INSERT INTO seasons VALUES(42,77,'2025/26','2025-08-01','2026-06-30');
        INSERT INTO imported_matches VALUES(999,123);''')
        clubs=['Arsenal','Chelsea','Liverpool','Manchester City','Manchester United','Tottenham Hotspur']
        con.executemany('INSERT INTO teams VALUES(?,?)',enumerate(clubs,101))
        con.executemany('INSERT INTO season_teams VALUES(42,?)',[(i,) for i in range(101,107)])
        old=con.execute('SELECT * FROM seasons').fetchall()
        for statement in INSERTS:con.execute(statement.replace('@tl_next_season_id','43'))
        self.assertEqual(con.execute('SELECT * FROM seasons WHERE season_id=42').fetchall(),old)
        self.assertEqual(con.execute('SELECT competition_id,season_label FROM seasons WHERE season_id=43').fetchone(),(77,'2023/24'))
        self.assertEqual(con.execute('SELECT COUNT(*) FROM season_teams').fetchone()[0],12)
        self.assertEqual(con.execute('SELECT * FROM imported_matches').fetchall(),[(999,123)])
        self.assertEqual(con.execute('SELECT * FROM provider_matches').fetchall(),[('football-data.org',999,123)])
        with self.assertRaises(sqlite3.IntegrityError):con.execute(INSERTS[0].replace('@tl_next_season_id','44'))


if __name__=='__main__':unittest.main()

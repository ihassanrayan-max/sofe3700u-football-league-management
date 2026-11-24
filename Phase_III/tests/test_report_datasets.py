"""Both report sources must use real SQL views and preserve export filtering."""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as core
import services


class ReportDatasetTests(unittest.TestCase):
    def setUp(self):
        self.client=core.app.test_client()
        with self.client.session_transaction() as session:
            session.update(uid=1,sid='test',csrf='test')

    def test_both_sources_all_views_and_exports(self):
        with patch.dict(core.os.environ,TOUCHLINE_PROVIDER='api-football'), patch.object(core,'sql',return_value=[{'user_id':1,'display_name':'Admin','role':'ADMIN'}]):
            for dataset,prefix in [('active','tl_'),('phase2','')]:
                for view in core.VIEWS:
                    for fmt in ['json','csv','pdf']:
                        with self.subTest(dataset=dataset,view=view,format=fmt):
                            def query(sql,args=()):
                                if sql.startswith('SHOW'):
                                    self.assertEqual(sql,'SHOW COLUMNS FROM '+prefix+view)
                                    return [{'Field':'team_name'}]
                                self.assertIn('FROM '+prefix+view+' WHERE LOCATE(%s',sql)
                                self.assertEqual(args,['Arsenal'])
                                return [{'team_name':'Arsenal'}]
                            with patch.object(services,'sql',side_effect=query):
                                result=self.client.get('/api/reports/'+view,query_string={'dataset':dataset,'format':fmt,'q':'Arsenal','field':'team_name'})
                                self.assertEqual(result.status_code,200)

    def test_invalid_source_and_guest_access(self):
        with patch.object(core,'sql',return_value=[{'user_id':1,'display_name':'Admin','role':'ADMIN'}]):
            self.assertEqual(self.client.get('/api/reports/v_match_results?dataset=invalid').status_code,400)
        with patch.object(core,'sql',return_value=[{'user_id':1,'display_name':'Guest','role':'GUEST'}]):
            for dataset in ['active','phase2']:
                self.assertEqual(self.client.get('/api/reports/v_match_results?dataset='+dataset).status_code,403)

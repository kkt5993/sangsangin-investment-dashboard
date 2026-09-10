import copy,unittest
from unittest.mock import patch
from pipeline.dragon_research import catalog,views


class ResearchCatalogTests(unittest.TestCase):
    def graph(self):
        nodes=[dict(id=id,name=id,entity=id!='theme:x') for id in ['stock:A','stock:B','theme:x']]
        edges=[dict(source='stock:A',target='theme:x',url='https://example.org/report',basis='business',reviewed_at='2026-09-09'),dict(source='stock:B',target='stock:A',url='https://example.org/report',basis='supply',reviewed_at='2026-09-10'),dict(source='stock:A',target='stock:B',relation='correlation')]
        return dict(type='relationlab',nodes=nodes,links=edges)

    @patch('pipeline.dragon_research.read_json',return_value={'sources':{}})
    def test_url_deduplication_preserves_all_targets_and_review_date(self,_):
        graph=self.graph();before=copy.deepcopy(graph);rows=[r for r in catalog(graph) if r['kind']=='official']
        self.assertEqual(len(rows),1);r=rows[0]
        self.assertEqual(len(r['targets']),3);self.assertEqual(r['evidence'],['business','supply'])
        self.assertEqual(r['date'],'2026-09-09');self.assertEqual(r['date_kind'],'근거 검토일');self.assertIsNone(r['period_end'])
        self.assertEqual(graph,before)
        graph['links'].reverse();self.assertEqual([r for r in catalog(graph) if r['kind']=='official'],rows)

    @patch('pipeline.dragon_research.read_json',return_value={'sources':{}})
    def test_unsafe_sources_are_not_catalog_documents(self,_):
        graph=self.graph()
        for url in ['javascript:alert(1)','https://user:password@example.org/report','http://example.org/report','']:
            graph['links'].append(dict(source='stock:A',target='stock:B',url=url,basis='invalid'))
        self.assertEqual(len([r for r in catalog(graph) if r['kind']=='official']),1)

    @patch('pipeline.dragon_research.read_json',return_value={'sources':{}})
    def test_rebuild_replaces_only_research_catalog_and_does_not_duplicate_gap(self,_):
        keep=dict(type='table',group='지금 주목',rows=[]);obj=dict(sections=[self.graph(),keep,dict(type='library',group='리서치',items=[])],missing=[])
        views(None,obj);before=copy.deepcopy(obj);views(None,obj)
        self.assertEqual(obj,before);self.assertIn(keep,obj['sections']);self.assertEqual(obj['sections'][-1]['coverage']['official'],1)

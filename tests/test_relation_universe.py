import copy,unittest
from pipeline import relation_universe as U
from pipeline.relation_views import companies

class RelationUniverseTest(unittest.TestCase):
    def test_collision_and_aliases(self):
        c=U.settings();aliases={a:r['symbol'] for r in c['companies'] for a in r['aliases']}
        self.assertNotIn('TEL',aliases);self.assertIn('TEL',[r['alias'] for r in c['unresolved']])
        self.assertEqual(aliases['HANMI'],'042700.KS');self.assertEqual(aliases['008930'],'008930.KS')
        self.assertEqual(aliases['APPLEINC'],aliases['AAPL']);self.assertEqual(aliases['CHEVRONCORPO'],aliases['CVX'])
        self.assertEqual(len(c['companies']),107);self.assertEqual(len(aliases),110);self.assertEqual(len(c['unresolved']),49)
    def test_symbol_registry_deduplicates(self):
        symbols=[r['symbol'] for r in companies()];self.assertEqual(len(symbols),len(set(symbols)))
        self.assertNotIn('TEL',symbols);self.assertIn('AES',symbols)
        self.assertTrue({r['symbol'] for r in U.settings()['companies']}<=set(symbols))
    def test_bad_mapping_rejected(self):
        c=U.settings();c['companies'][1]['aliases'].append(c['companies'][0]['aliases'][0])
        with self.assertRaises(AssertionError):U.validate(c)
        c=U.settings();c['companies'][0]['identity']['source']='https://secret@example.com/'
        with self.assertRaises(AssertionError):U.validate(c)
        c=U.settings();c['companies'][0]['market']='JP'
        with self.assertRaises(AssertionError):U.validate(c)
    def test_coverage_does_not_invent_business_edges(self):
        c=U.settings();nodes=[dict(id='stock:'+r['symbol'],symbol=r['symbol'],date=None,entity=True) for r in c['companies']]
        graph=dict(nodes=nodes,links=[]);v=U.coverage(graph)
        self.assertTrue(all(r['business_relations']==0 and r['price_date'] is None for r in v['companies']))
        graph['universe_coverage']=v;U.verify(graph)

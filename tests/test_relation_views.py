import base64
import unittest
import numpy as np
import pandas as pd
from pipeline.relation_views import correlation_pack,graph_data,presets
from pipeline.relation_model import run_scenario


class DataFixture:
    as_of='2026-09-08'
    def price(self,s):
        dates=pd.bdate_range('2024-01-01',self.as_of)
        if s=='missing':return pd.Series(dtype=float,index=pd.DatetimeIndex([]))
        r=np.sin(np.arange(len(dates))*.23)*.01
        p=pd.Series(100*np.exp(np.cumsum(-r if s=='B' else r)),index=dates)
        return p.tail(100) if s=='short' else p.iloc[:100] if s=='stale' else p*0+100 if s=='flat' else p
    def mac(self,s):return self.price(s)


class RelationViewTests(unittest.TestCase):
    def test_packed_correlation_roundtrip_and_missing(self):
        names=['A','B','flat','short','stale','missing'];p=correlation_pack(DataFixture(),[dict(id=s,symbol=s) for s in names])
        corr=np.frombuffer(base64.b64decode(p['correlations']),dtype='<i2');counts=np.frombuffer(base64.b64decode(p['counts']),dtype='uint8')
        self.assertEqual(len(corr),len(names)*(len(names)-1)//2);self.assertEqual(len(counts),len(corr))
        self.assertLess(corr[0],-9999);self.assertEqual(counts[0],252)
        for name in names[2:]:
            i=p['ids'].index(name);self.assertEqual(corr[i*(i-1)//2],32767)
        self.assertEqual(p['window'],252);self.assertLessEqual(p['end'],DataFixture.as_of)
        self.assertFalse(p['diagonal_valid'][p['ids'].index('flat')]);self.assertTrue(p['diagonal_valid'][0])
    def test_empty_pack(self):
        p=correlation_pack(DataFixture(),[]);self.assertEqual(p['correlations'],'');self.assertEqual(p['window'],0);self.assertIsNone(p['end'])
        p=correlation_pack(DataFixture(),[dict(id='missing',symbol='missing')]);self.assertEqual(p['diagonal'],[0])
    def test_graph_source_paths_and_presets(self):
        g=graph_data(DataFixture(),dict(entities=[]));ids={n['id'] for n in g['nodes']}
        self.assertEqual(len(ids),len(g['nodes']));self.assertEqual(len(presets()),8)
        for e in g['links']:
            self.assertIn(e['source'],ids);self.assertIn(e['target'],ids);self.assertTrue(e['basis'])
            if e['relation']!='correlated':self.assertTrue(e['url'].startswith('https://'))
        for s in presets():
            self.assertTrue(all(seed['id'] in ids for seed in s['seeds']));self.assertTrue(run_scenario(g,s['seeds']))
        for n in g['nodes']:
            if n.get('date'):self.assertLessEqual(n['date'],DataFixture.as_of)
            self.assertEqual(len(n['position']),3)


if __name__=='__main__':unittest.main()

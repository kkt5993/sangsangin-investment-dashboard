import unittest
import numpy as np
import pandas as pd
from pipeline.relation_model import adjacency,propagate,run_scenario,centrality,correlations


def graph(edges):
    return dict(nodes=[dict(id=id) for id in sorted({id for a,b,rel in edges for id in [a,b]})],links=[dict(id=str(i),source=a,target=b,relation=rel,weight=1) for i,(a,b,rel) in enumerate(edges)])


class RelationTests(unittest.TestCase):
    def test_supply_direction_and_competition(self):
        g=graph([('supplier','customer','supplies'),('customer','competitor','competes')])
        a=propagate(g,'supplier');b=propagate(g,'customer')
        self.assertAlmostEqual(a['customer']['value'],.28*.8*.9,6);self.assertAlmostEqual(b['supplier']['value'],.72*.8*.9,6)
        self.assertAlmostEqual(a['competitor']['value'],.28*.8*.9*-.5*.8*.9,6)
        self.assertEqual(a['competitor']['path'],['supplier','customer','competitor'])
    def test_strongest_path_not_same_seed_sum(self):
        g=graph([('A','B','exposed-to'),('A','C','supplies'),('B','D','exposed-to'),('C','D','competes')])
        result=propagate(g,'A');self.assertAlmostEqual(result['D']['value'],.36**2,6);self.assertEqual(result['D']['path'],['A','B','D'])
        reversed_graph=dict(g,links=g['links'][::-1]);self.assertEqual(result,propagate(reversed_graph,'A'))
    def test_cycles_hops_and_negative_shock(self):
        g=graph([('A','B','exposed-to'),('B','C','exposed-to'),('C','A','exposed-to'),('C','D','exposed-to'),('D','E','exposed-to'),('E','F','exposed-to')])
        out=propagate(g,'A');self.assertNotIn('A',out);self.assertNotIn('F',out)
        self.assertTrue(all(len(r['path'])==len(set(r['path'])) for r in out.values()))
        down=propagate(g,'A',-1)
        for id,r in out.items():self.assertEqual(down[id]['value'],-r['value'])
        self.assertNotIn('D',propagate(g,'A',hops=1))
    def test_multiple_seeds_cancel_with_provenance(self):
        g=graph([('A','C','exposed-to'),('B','C','exposed-to')]);out=run_scenario(g,[dict(id='A',value=1),dict(id='B',value=-1)],hops=1)
        self.assertEqual(out['C']['value'],0);self.assertEqual(len(out['C']['contributions']),2);self.assertTrue(out['A']['seed'])
    def test_signed_correlations_opt_in(self):
        g=graph([('A','B','correlated')]);g['links'][0]['corr']=-.9
        self.assertEqual(propagate(g,'A'),{});self.assertLess(propagate(g,'A',include_correlations=True)['B']['value'],0)
        g['links'][0]['corr']=None
        with self.assertRaises(ValueError):adjacency(g)
    def test_invalid_inputs_and_hub(self):
        g=graph([('A','B','supplies')]);self.assertEqual(centrality(g)[0]['id'],'B')
        for kwargs in [dict(start='missing'),dict(start='A',shock=float('nan')),dict(start='A',hops=4)]:
            with self.assertRaises(ValueError):propagate(g,**kwargs)
        g['links'][0]['weight']=0
        with self.assertRaises(ValueError):adjacency(g)
    def test_correlations_common_window_and_missing(self):
        dates=pd.bdate_range('2024-01-01','2026-09-08');r=np.sin(np.arange(len(dates))*.3)*.01
        p=pd.Series(100*np.exp(np.cumsum(r)),index=dates);q=pd.Series(100*np.exp(np.cumsum(-r)),index=dates)
        class D:
            as_of='2026-09-08'
            def price(self,s):return {'A':p,'B':q,'short':p.tail(100),'flat':p*0+100,'stale':p.iloc[:200]}[s]
        out=correlations(D(),['A','B','short','flat','stale']);self.assertEqual(len(out),1);self.assertLess(out[0]['corr'],-.9999)
        self.assertEqual(out[0]['observations'],252);self.assertGreater(out[0]['start'],'2025-09-01')

if __name__=='__main__':unittest.main()

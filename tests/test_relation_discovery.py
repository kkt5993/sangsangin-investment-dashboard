import copy,unittest,warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests
from pipeline.relation_discovery import lag_test,build,views


class Prices:
    def __init__(self):
        rng=np.random.default_rng(7821);self.index=pd.bdate_range('2026-01-01',periods=200)
        x=rng.normal(0,.01,200);y=np.roll(x,1)*.9+rng.normal(0,.003,200)
        self.frames={s:pd.Series(100*np.cumprod(1+r),index=self.index) for s,r in [('AAA',x),('BBB',y),('CCC',rng.normal(0,.01,200)),('000001.KS',x),('SPY',x),('^KS11',y)]}
        self.as_of=str(self.index[-20].date());self.vintage='fixture'
    def price(self,s):return self.frames.get(s,pd.Series(dtype=float)).dropna()


def graph():
    return dict(nodes=[dict(id='stock:'+s,symbol=s,name=s,kind='company') for s in ['AAA','BBB','CCC','000001.KS']],links=[dict(id='business',source='stock:AAA',target='stock:BBB',relation='supplies',weight=1)])


class RelationDiscoveryTests(unittest.TestCase):
    def test_f_matches_independent_statsmodels_implementation(self):
        rng=np.random.default_rng(50);frame=pd.DataFrame(rng.normal(size=(200,2)),index=pd.bdate_range('2025-01-01',periods=200),columns=['X','Y'])
        for lag in [1,3,5]:
            actual=lag_test(frame,'X','Y',lag,frame.index[0]-pd.Timedelta(days=1))
            with warnings.catch_warnings():
                warnings.simplefilter('ignore');expected=grangercausalitytests(frame[['Y','X']].to_numpy(),[lag],verbose=False)[lag][0]['ssr_ftest']
            self.assertAlmostEqual(actual['f'],expected[0],10);self.assertAlmostEqual(actual['p'],expected[1],10)

    def test_direction_and_calendar_hole_not_compressed(self):
        d=Prices();f=pd.DataFrame({k:d.price(k).pct_change(fill_method=None) for k in ['AAA','BBB']}).dropna();start=f.index[0]-pd.Timedelta(days=1)
        forward=lag_test(f,'AAA','BBB',1,start);reverse=lag_test(f,'BBB','AAA',1,start)
        self.assertGreater(forward['corr'],.9);self.assertGreater(forward['corr'],reverse['corr']+.5)
        hole=f.copy();hole.iloc[50,0]=np.nan;out=lag_test(hole,'AAA','BBB',1,start)
        self.assertEqual(out['observations'],forward['observations']-2)

    def test_future_changes_do_not_change_current_output(self):
        d=Prices();before=build(d,graph())
        for s in d.frames:d.frames[s].loc[d.frames[s].index>pd.Timestamp(d.as_of)]*=100
        self.assertEqual(before,build(d,graph()))
        self.assertEqual(before['coverage']['tests'],3*2*3)
        self.assertTrue(all(r['market']=='US' for r in before['tests']))
        self.assertTrue(all(r['end']<=d.as_of for r in before['tests']))

    def test_invalid_and_stale_prices_do_not_become_signals(self):
        d=Prices();d.frames['CCC'][:]=100;d.frames['BBB']=d.frames['BBB'].iloc[:30]
        out=build(d,graph());self.assertTrue(any(r['symbol']=='BBB' for r in out['excluded']))
        self.assertTrue(all(r['p'] is None and not r['candidate'] for r in out['tests']))
        self.assertTrue(all(r['corr'] is None for r in out['pairs'] if 'CCC' in [r['a'],r['b']]))

    def test_correction_population_and_graph_are_repeatable(self):
        d=Prices();g=graph();g['type']='relationlab';obj={'sections':[g]}
        views(d,obj);first=copy.deepcopy(obj);views(d,obj);self.assertEqual(first,obj)
        out=obj['sections'][0]
        self.assertTrue(all(0<=r['p']<=r['q']<=1 for r in out['tests'] if r['p'] is not None))
        self.assertEqual(sum(e['relation']=='correlated' for e in g['links']),len(out['hidden']))
        self.assertTrue(all(r['screen_pass']==(r['candidate'] and r['q'] is not None and r['q']<=.1) for r in out['tests']))

    def test_stale_market_calendar_disables_its_pairs(self):
        d=Prices();d.frames['SPY']=d.frames['SPY'].iloc[:50]
        out=build(d,graph());self.assertEqual(out['windows']['US']['sessions'],0)
        self.assertEqual(out['coverage']['tests'],0)
        self.assertEqual(out['coverage']['priced'],1)


if __name__=='__main__':unittest.main()

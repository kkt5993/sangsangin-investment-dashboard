import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.engine import Data
from pipeline.quant_screens import pair_metrics,stock_metrics,factor_scores,bab_legs,tsmom,FEATURES

class QuantScreensTests(unittest.TestCase):
    def pair(self):
        rng=np.random.default_rng(843);idx=pd.bdate_range('2023-01-02',periods=600)
        b=pd.Series(100*np.exp(np.cumsum(rng.normal(0,.02,len(idx)))),index=idx)
        noise=rng.normal(0,.006,len(idx));a=b*(1+noise)
        return a,b
    def test_ratio_z_and_ou_match_direct_calculation(self):
        a,b=self.pair();r=pair_metrics(a,b);self.assertIsNotNone(r);ratio=(a/b).tail(505)
        self.assertAlmostEqual(r['z'],(ratio.iloc[-1]-ratio.tail(252).mean())/ratio.tail(252).std(ddof=0),places=5)
        self.assertEqual(r['observations'],504);self.assertEqual(r['curve'].index[-1],a.index[-1])
        X=np.column_stack([np.ones(len(ratio)-1),ratio.iloc[:-1]]);slope=np.linalg.lstsq(X,np.diff(ratio),rcond=None)[0][1]
        self.assertAlmostEqual(r['phi'],1+slope,places=5)
    def test_ratio_scale_invariance_and_gap_retention(self):
        a,b=self.pair();r=pair_metrics(a,b);scaled=pair_metrics(a*12,b*3)
        self.assertEqual(r['z'],scaled['z']);self.assertEqual(r['hurst'],scaled['hurst'])
        a.iloc[-100]=np.nan;g=pair_metrics(a,b);self.assertEqual(g['observations'],502)
        self.assertTrue(pd.isna(g['curve'].loc[a.index[-100]]));self.assertEqual(len(g['curve']),252)
        a.iloc[-1]=np.nan;self.assertIsNone(pair_metrics(a,b))
    def fixture(self):
        d=object.__new__(Data);idx=pd.bdate_range('2023-01-02',periods=800);rng=np.random.default_rng(27)
        p=pd.Series(100*np.exp(np.cumsum(rng.normal(.0003,.01,len(idx)))),index=idx)
        d.as_of=str(idx[-1].date());d.frames={s:pd.DataFrame(dict(close=p,adjusted_close=p,volume=1000.)) for s in ['X','^KS11']}
        return d,idx
    def test_stock_compounded_reversal_and_partial_month(self):
        d,idx=self.fixture();r=stock_metrics(d,dict(symbol='X',name='X'),idx);p=d.price('X');five=p.pct_change(5)*100
        self.assertAlmostEqual(r['reversal_z'],((five-five.rolling(252).mean())/five.rolling(252).std(ddof=0)).iloc[-1],places=5)
        self.assertAlmostEqual(r['beta'],1.,places=5)
        old=r['stability'];d.frames['X'].loc[idx[-1],['close','adjusted_close']]*=1.01
        self.assertEqual(stock_metrics(d,dict(symbol='X',name='X'),idx)['stability'],old)
    def test_missing_prices_excluded_and_future_ignored(self):
        d,idx=self.fixture();original=stock_metrics(d,dict(symbol='X',name='X'),idx)
        future=idx[-1]+pd.Timedelta(days=30);d.frames['X'].loc[future]=[1e9,1e9,1e9]
        self.assertEqual(stock_metrics(d,dict(symbol='X',name='X'),idx),original)
        d.frames['X'].loc[idx[-5],['close','adjusted_close']]=np.nan
        self.assertIn('최근127시장일 또는12M 기준가격 결측',stock_metrics(d,dict(symbol='X',name='X'),idx)['excluded'])
    def test_factor_missing_not_zero_and_contribution_sum(self):
        rows=[dict(symbol=str(i),excluded=[],**{k:float(i*j) for j,(k,_,_,_) in enumerate(FEATURES,1)}) for i in range(20)]
        rows[-1]['excluded']=['팩터 결측'];rows[-1]['vol']=None;scored=factor_scores(rows)
        self.assertEqual(len(scored),19);self.assertIsNone(rows[-1]['factor'])
        for r in scored:
            self.assertEqual(len(r['components']),8);self.assertAlmostEqual(r['factor'],sum(c['contribution'] for c in r['components']),places=5)
            self.assertTrue(all(abs(c['z'])<=2.5 for c in r['components']))
    def test_bab_leg_neutrality_and_empty_side(self):
        rows=[dict(symbol=str(i),name=str(i),date='2026-09-10',beta=.1+i*.1,r1y=20.) for i in range(20)]
        b=bab_legs(rows);self.assertEqual(b['quintile'],4);self.assertAlmostEqual(b['net_beta'],0.,places=5)
        self.assertAlmostEqual(b['legs'][0]['beta_exposure'],1.,places=5);self.assertAlmostEqual(b['legs'][1]['beta_exposure'],-1.,places=5)
        for r in rows[:4]:r['r1y']=-1
        b=bab_legs(rows);self.assertFalse(b['complete']);self.assertIsNone(b['net_beta']);self.assertIsNone(b['legs'][0]['beta_exposure'])
    def test_tsmom_dates_and_yield_not_bond_return(self):
        d,idx=self.fixture();d.frames['^TNX']=d.frames['X'].copy();d.frames['^GSPC']=d.frames['X'].copy()
        out=tsmom(d);rate=next(r for r in out if r['symbol']=='^TNX');equity=next(r for r in out if r['symbol']=='^GSPC')
        self.assertTrue(rate['available']);self.assertIsNone(rate['exposure']);self.assertLessEqual(abs(equity['exposure']),2)
        target=idx[-1]-pd.DateOffset(months=12);base=d.price('^GSPC').loc[:target]
        self.assertEqual(equity['start12'],str(base.index[-1].date()));self.assertEqual(len(out),12)
        self.assertFalse(next(r for r in out if r['symbol']=='^KQ11')['available'])

if __name__=='__main__':unittest.main()

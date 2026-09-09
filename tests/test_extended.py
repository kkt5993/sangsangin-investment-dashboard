import unittest
import numpy as np
import pandas as pd
from pipeline.engine import observed_resample,expanding_z,rsi,Data,ret,performance,monthly_portfolio
from pipeline.ml_models import walk_forward
from pipeline.maximus_model import gated
from pipeline.financial_modules import pct
from pipeline.quant_modules import hurst
from pipeline.patterns import candidates,pivots

class ExtendedTests(unittest.TestCase):
    def test_drawdown_includes_initial_capital(self):
        self.assertEqual(performance(pd.Series([-.2,.05,0.]))['mdd'],-20)
    def test_monthly_portfolio_drifts_and_charges_first_trade(self):
        idx=pd.to_datetime(['2026-01-30','2026-02-02','2026-02-03','2026-03-02'])
        r=pd.DataFrame({'a':[0,.1,.1,0],'b':[0,0,0,0]},index=idx);w=pd.DataFrame(.5,index=idx,columns=['a','b'])
        out=monthly_portfolio(r,w,5)
        self.assertAlmostEqual(out.iloc[0],.05-.0005)
        self.assertAlmostEqual(out.iloc[1],(.55/1.05)*.1)
        drift=(.5*1.1**2)/(.5*1.1**2+.5)
        self.assertAlmostEqual(out.iloc[2],-2*abs(drift-.5)*.0005)
    def test_partial_period_never_uses_future_date(self):
        s=pd.Series(np.arange(8.)+100,index=pd.bdate_range('2026-08-28',periods=8))
        for freq in ['ME','W-FRI']:
            r=observed_resample(s,freq);self.assertEqual(r.index[-1],s.index[-1]);self.assertEqual(r.iloc[-1],s.iloc[-1]);self.assertTrue(r.index.is_unique)
    def test_prediction_monthly_excludes_partial_month(self):
        d=object.__new__(Data);d.as_of='2026-09-08';p=pd.Series(np.arange(270.)+100,index=pd.bdate_range(end=d.as_of,periods=270));d.frames={'test':pd.DataFrame({'adjusted_close':p,'close':p})}
        self.assertEqual(d.monthly('test').index[-1],pd.Timestamp('2026-08-31'))
    def test_expanding_risk_is_prefix_invariant(self):
        rng=np.random.default_rng(17);s=pd.Series(rng.normal(size=400));s2=s.copy();s2.iloc[300:]=1e6
        pd.testing.assert_series_equal(expanding_z(s,30).iloc[:300],expanding_z(s2,30).iloc[:300])
    def test_zero_negative_earnings_base_is_not_growth(self):
        self.assertIsNone(pct(10,-5));self.assertIsNone(pct(10,0));self.assertEqual(pct(-5,10),-150);self.assertEqual(pct(15,10),50)
    def test_rsi_one_direction_and_flat(self):
        self.assertEqual(rsi(pd.Series(np.arange(50.))).iloc[-1],100);self.assertEqual(rsi(pd.Series(np.ones(50))).iloc[-1],50)
    def test_walk_forward_purges_unmatured_targets(self):
        idx=pd.date_range('2010-01-31',periods=90,freq='ME');rng=np.random.default_rng(4)
        p=pd.Series(np.exp(np.cumsum(rng.normal(.004,.03,90)))*100,index=idx);X=pd.DataFrame({'momentum':p.pct_change().fillna(0),'trend':np.arange(90)/90},index=idx)
        r,_=walk_forward(X,p,3,min_train=24)
        self.assertTrue(r)
        for row in r:
            self.assertLessEqual(row['train_target_end'],row['origin']);self.assertLess(row['train_last_origin'],row['origin'])
        # Future price shocks cannot change an already issued forecast or its band.
        p2=p.copy();p2.iloc[60:]*=2;r2,_=walk_forward(X,p2,3,min_train=24)
        for a,b in zip(r,r2):
            if a['origin']<str(idx[60].date()):self.assertEqual(a['prediction'],b['prediction']);self.assertEqual(a['interval'],b['interval'])
    def test_moe_gate_ignores_unrealized_results(self):
        records=[]
        for i,t in enumerate(pd.date_range('2020-01-31',periods=40,freq='ME')):records.append(dict(origin=str(t.date()),target=str((t+pd.offsets.MonthEnd()).date()),actual=float(i%3),models={'a':1.,'b':2.}))
        baseline=gated(records);records[-1]['actual']=1e9;changed=gated(records)
        self.assertEqual(baseline[-1]['weights'],changed[-1]['weights']);self.assertAlmostEqual(sum(baseline[-1]['weights'].values()),1,places=5)
    def test_hurst_differentiates_stationary_and_trending(self):
        rng=np.random.default_rng(9);noise=pd.Series(rng.normal(size=2000));walk=noise.cumsum()
        self.assertLess(hurst(noise),.2);self.assertGreater(hurst(walk),.3)
    def test_pattern_requires_confirmed_pivots_and_no_future(self):
        idx=pd.bdate_range('2026-01-01',periods=150)
        values=np.interp(np.arange(150),[0,50,65,80,95,119,149],[110,108,90,108,92,112,500])
        p=pd.Series(values,index=idx);cut=idx[119];a=candidates(p,str(cut.date()))
        self.assertIn('W바닥',[x['name'] for x in a])
        self.assertEqual(a,candidates(p.loc[:cut],str(cut.date())))
        self.assertEqual(candidates(pd.Series(100.,index=idx),str(idx[-1].date())),[])
        self.assertNotIn(4,pivots(pd.Series([5,4,3,2,1,2]),width=3))
        for x in a:self.assertLessEqual(x['confirmed_at'],str(cut.date()))

if __name__=='__main__':unittest.main()

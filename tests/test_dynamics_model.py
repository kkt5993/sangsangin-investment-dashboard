import unittest
import numpy as np
import pandas as pd
from pipeline.dynamics_model import indicators,monthly,recent,simulate

class DynamicsTests(unittest.TestCase):
    def price(self):
        rng=np.random.default_rng(889);return pd.Series(100*np.exp(np.cumsum(rng.normal(.0002,.013,1000))),index=pd.bdate_range('2020-01-01',periods=1000))
    def test_formulas_and_future_invariance(self):
        p=self.price();f=indicators(p);r=p.pct_change();beta=r.rolling(21).mean()/r.rolling(21).std(ddof=0)*np.sqrt(252)
        tau=r.diff().abs().rolling(21).std(ddof=0)/r.abs().rolling(21).mean();pd.testing.assert_series_equal(f.beta,beta,check_names=False);pd.testing.assert_series_equal(f.tau,tau,check_names=False)
        p2=p.copy();p2.iloc[800:]*=30;pd.testing.assert_frame_equal(f.iloc[:800],indicators(p2).iloc[:800])
        row=f.dropna().iloc[-1];self.assertAlmostEqual(row.risk,100/(1+np.exp(-(row.z_tau-.5*row.z_beta-.5*row.z_alpha))))
        self.assertAlmostEqual(row.exposure,min(1.5,.15/(row.vol/100))*(1-.6*row.risk/100))
    def test_gap_never_compresses_returns_and_zero_variance(self):
        p=self.price();p.iloc[400]=np.nan;f=indicators(p)
        self.assertTrue(f.ret.iloc[400:402].isna().all());self.assertTrue(f.beta.iloc[400:422].isna().all())
        constant=indicators(pd.Series(100.,index=p.index));self.assertTrue(constant.risk.isna().all());self.assertTrue(constant.exposure.isna().all())
    def frame(self):
        return pd.DataFrame(dict(ret=[np.nan,.1,-.05,.03,.01],exposure=[.5,1.2,.8,1.1,.9]),index=pd.bdate_range('2026-01-01',periods=5))
    def test_previous_signal_drift_cost_and_financing(self):
        f=self.frame();c=simulate(f,5,3);a,b=c['rows'][:2];fee=.5*.0005;first=.5*.1-fee;held=.5*1.1/(1+first)
        self.assertAlmostEqual(a['weight'],.5);self.assertAlmostEqual(a['nav'],100*(1+first),places=5)
        self.assertAlmostEqual(b['held'],held,places=5);self.assertAlmostEqual(b['turnover'],abs(1.2-held),places=5)
        self.assertAlmostEqual(b['financing_pct'],.2*.03/252*100,places=5)
        expected=1.2*-.05-abs(1.2-held)*.0005-.2*.03/252
        self.assertAlmostEqual(b['net_return_pct'],expected*100,places=5)
        self.assertEqual(a['signal_date'],str(f.index[0].date()));self.assertEqual(c['chart']['series'][0]['points'][0],[str(f.index[0].date()),100.])
    def test_returns_not_shifted_twice_and_future_neutral(self):
        f=self.frame();c=simulate(f);a=c['rows'];self.assertAlmostEqual(a[0]['gross_return_pct'],5.)
        f.iloc[-1,f.columns.get_loc('ret')]=.7;b=simulate(f)['rows'];self.assertEqual(a[:-1],b[:-1])
        self.assertEqual(c['model']['sessions'],c['benchmark']['sessions'])
    def test_missing_signal_restarts_common_period(self):
        f=self.frame();f.iloc[2,f.columns.get_loc('exposure')]=np.nan;c=simulate(f)
        self.assertEqual(c['start'],str(f.index[4].date()));self.assertEqual(c['origin'],str(f.index[3].date()));self.assertEqual(c['sessions'],1)
        f.iloc[-1,f.columns.get_loc('ret')]=np.nan;self.assertFalse(simulate(f)['available'])
    def test_bankruptcy_stops_instead_of_negative_nav(self):
        f=self.frame();f['exposure']=1.5;f.iloc[1,f.columns.get_loc('ret')]=-.9;c=simulate(f)
        self.assertTrue(c['bankrupt']);self.assertEqual(c['sessions'],1);self.assertEqual(c['rows'][0]['nav'],0);self.assertEqual(c['model']['mdd'],-100)
    def test_monthly_actual_date_and_calendar_window(self):
        f=pd.DataFrame({'x':[1,2,3]},index=pd.to_datetime(['2026-01-29','2026-02-26','2026-03-10']))
        self.assertEqual(monthly(f).index[-1],pd.Timestamp('2026-03-10'));self.assertEqual(len(recent(f,2,'2026-03-10')),2)

if __name__=='__main__':unittest.main()

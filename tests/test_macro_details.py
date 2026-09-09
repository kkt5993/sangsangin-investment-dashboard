import unittest
import numpy as np
import pandas as pd
from pipeline.pm_details import trend_model,align_observations
from pipeline.reflexivity import acceleration,ols,csad_regression,champion,rolling_ar1
from pipeline.industry_details import change
from pipeline.ecos_data import period_date

class MacroDetailTests(unittest.TestCase):
    def test_autocorrelation_only_uses_pairs_inside_window(self):
        s=pd.Series([100.,1,3,2,5,7])
        self.assertAlmostEqual(rolling_ar1(s,5).iloc[-1],s.iloc[-5:].autocorr())
    def test_acceleration_recovers_known_log_curve_and_no_future(self):
        rng=np.random.default_rng(16);t=np.arange(520)/252
        p=pd.Series(np.exp(4+.1*t+.2*t*t+rng.normal(0,.00001,520)),index=pd.bdate_range('2020-01-01',periods=520))
        got=acceleration(p);self.assertAlmostEqual(got.acceleration.iloc[-1],40,places=2)
        changed=p.copy();changed.iloc[400:]*=3
        pd.testing.assert_frame_equal(got.loc[:p.index[399]],acceleration(changed).loc[:p.index[399]])
    def test_ols_recovers_negative_csad_curvature(self):
        rng=np.random.default_rng(33);r=rng.normal(0,.015,240)
        y=.01+.4*abs(r)-2*r*r+rng.normal(0,.00001,240)
        b,t=ols(y,np.column_stack([np.ones(240),abs(r),r*r]))
        self.assertAlmostEqual(b[2],-2,places=2);self.assertLess(t[2],-1.64)
    def test_csad_missing_names_not_filled_with_zero(self):
        idx=pd.bdate_range('2020-01-01',periods=150);r=pd.Series(np.sin(np.arange(150))*.02,index=idx)
        stocks=pd.DataFrame({str(i):r+.001*(i-5) for i in range(10)})
        stocks.iloc[:50,:2]=np.nan
        regression,csad=csad_regression(stocks,r)
        self.assertTrue(csad.iloc[:50].isna().all());self.assertTrue(regression.empty)
    def test_cta_weights_are_lagged_and_charge_initial_cost(self):
        rng=np.random.default_rng(14);p=pd.DataFrame(np.exp(np.cumsum(rng.normal(.001,.008,(400,3)),axis=0))*100,index=pd.bdate_range('2020-01-01',periods=400),columns=list('abc'))
        model=trend_model(p);start=model['returns'].index[0];i=p.index.get_loc(start);w=model['targets'].iloc[i-1]
        expected=(w*p.pct_change(fill_method=None).iloc[i]).sum()-w.abs().sum()*.0005
        self.assertAlmostEqual(model['returns'].iloc[0],expected)
        p2=p.copy();p2.iloc[340:]*=3;m2=trend_model(p2)
        pd.testing.assert_series_equal(model['returns'].loc[:p.index[339]],m2['returns'].loc[:p.index[339]])
        self.assertTrue((model['targets'].abs().max()<=2/3).all())
    def test_month_and_quarter_dates_are_economic_periods(self):
        a=pd.Series([3,4],index=pd.to_datetime(['2026-01-03','2026-02-04']))
        b=pd.Series([1,2],index=pd.to_datetime(['2026-01-01','2026-02-01']))
        f=align_observations(dict(a=a,b=b));self.assertEqual(list(f.a-f.b),[2,2])
        self.assertEqual(period_date('2026Q2','Q'),pd.Timestamp('2026-04-01'))
    def test_rates_use_differences_and_prices_calendar_months(self):
        s=pd.Series([1,2,3],index=pd.to_datetime(['2026-06-30','2026-07-31','2026-08-31']))
        self.assertEqual(change(s,1,True),1);self.assertEqual(change(s,1),50)
        self.assertIsNone(change(s,3))

if __name__=='__main__':unittest.main()

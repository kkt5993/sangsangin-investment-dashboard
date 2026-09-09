import unittest
import numpy as np
import pandas as pd
from pipeline.allocation_views import constrained_target,simulate,mapped_signal,CAPS,GROUPS
from pipeline.allocation_model import walk_forward,ASSETS,STATES,aligned_price,feature_frame


class AllocationTests(unittest.TestCase):
    def test_cli_level_and_macro_lag_use_complete_month_axis(self):
        dates=pd.date_range('2000-01-31',periods=70,freq='ME');x=np.arange(70)
        class Data:
            as_of='2005-11-08'
            def monthly(self,s):return pd.Series(100+x,index=dates)
            def price(self,s):return self.monthly(s)
            def mac(self,k):return pd.Series(100+x if k.startswith('OECD_CLI_') else 100+x*x,index=dates)
        f,_,clock=feature_frame(Data())
        self.assertEqual(len(f.columns),74)
        self.assertEqual(f.OECD_CLI_USA.iloc[-1],67)
        self.assertEqual(f.OECD_CLI_USA_3m.iloc[-1],3)
        self.assertEqual(clock.iloc[-1],'회복')

    def test_caps_cash_and_no_leverage_after_vol_scaling(self):
        symbols=['SPY','IEF','BTC-USD','BIL'];cov=np.diag(np.array([.4,.15,.9,.001])**2)
        w,vol=constrained_target(cov,symbols,{'BTC-USD':200,'SPY':50,'IEF':-5},.05)
        self.assertAlmostEqual(w.sum(),1)
        self.assertLessEqual(vol,.050001);self.assertTrue((w>=0).all())
        self.assertTrue((w.drop('BIL')<=.100001).all())
        for group,cap in CAPS.items():self.assertLessEqual(sum(v for s,v in w.items() if GROUPS[s]==group),cap+1e-6)

    def test_close_execution_drift_and_both_trade_legs(self):
        days=pd.to_datetime(['2026-02-02','2026-02-03','2026-02-04'])
        prices=pd.DataFrame({'SPY':[100.,110.,121.],'BIL':[100.,100.,100.]},index=days)
        targets={'2026-01-31':pd.Series({'SPY':1.}),'2026-02-02':pd.Series({'BIL':1.})}
        r,trades,held=simulate(prices,targets,10)
        self.assertAlmostEqual(r.iloc[0],-.002)
        self.assertAlmostEqual(r.iloc[1],1.1*.998-1)
        self.assertAlmostEqual(r.iloc[2],0)
        self.assertEqual(trades[0]['gross_turnover'],200)
        self.assertEqual(trades[0]['one_way_turnover'],100)
        self.assertAlmostEqual(held.BIL,1)
        missing=prices.copy();missing.loc[days[1],'SPY']=np.nan
        with self.assertRaises(ValueError):simulate(missing,targets)

    def test_currency_signal_uses_signed_observed_beta(self):
        index=pd.date_range('2020-01-31',periods=40,freq='ME');usd=np.sin(np.arange(40))
        r=pd.DataFrame({'UUP':usd,'FXE':-2*usd},index=index)
        mapped=mapped_signal({'달러':2},r,index[-1],['UUP','FXE','BIL'])
        self.assertAlmostEqual(mapped['UUP'],2);self.assertAlmostEqual(mapped['FXE'],-4)

    def test_crypto_utc_bar_is_not_used_before_its_close(self):
        dates=pd.date_range('2026-09-04',periods=5)
        class Data:
            def price(self,s):return pd.Series(range(100,105),index=dates) if s=='BTC-USD' else pd.Series(1.,index=dates[dates.dayofweek<5])
        p=aligned_price(Data(),'BTC-USD')
        self.assertEqual(p.loc['2026-09-07'],102)

    def test_walkforward_future_changes_do_not_change_prediction(self):
        rng=np.random.default_rng(23);dates=pd.date_range('2015-01-31',periods=40,freq='ME')
        X=pd.DataFrame(rng.normal(size=(40,8)),index=dates,columns=['x'+str(j) for j in range(8)])
        returns=pd.DataFrame(rng.normal(size=(40,7))*3,index=dates,columns=list(ASSETS))
        clock=pd.Series([STATES[i%4] for i in range(40)],index=dates)
        a=walk_forward(X.iloc[:38],returns,clock,min_train=36,sequence=False,boruta_iterations=12)
        future_X=X.copy();future_X.iloc[37:]*=1000;future_returns=returns.copy();future_returns.iloc[37:]*=-100
        b=walk_forward(future_X.iloc[:38],future_returns,clock,min_train=36,sequence=False,boruta_iterations=12)
        for key in ['mu','parts','selection','p_riskon','clock','cycle_perf']:
            self.assertEqual(a[0][key],b[0][key],key)
        for row in a:
            self.assertLessEqual(row['train_target_end'],row['origin'])
            self.assertLess(row['origin'],row['target'])
            self.assertLessEqual(pd.Timestamp(row['clock_label_cutoff'])+pd.offsets.MonthEnd(2),pd.Timestamp(row['origin']))


if __name__=='__main__':unittest.main()

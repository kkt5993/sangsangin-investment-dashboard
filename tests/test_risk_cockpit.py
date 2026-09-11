import copy
import unittest
import numpy as np
import pandas as pd
from pipeline.risk_cockpit import (validated_weights, monthly_returns, fixed_book,
    factor_exposure, stress_results, directional_confidence, FACTORS)
from pipeline.allocation_views import UNIVERSE
from pipeline.store import ROOT, read_json


class CockpitTests(unittest.TestCase):
    def contract(self):
        return dict(schema_version=1,label='ML 국면',as_of='2026-09-08',origin='2026-08-31',target='2026-09-30',
                    weights=[dict(symbol=s,weight_pct=50 if s in ['SPY','BIL'] else 0) for s,_,_ in UNIVERSE])

    def test_target_shares_allocation_and_rejects_stale_nonfinite_duplicate_weights(self):
        b=self.contract();w=validated_weights(b,'2026-09-08')
        self.assertAlmostEqual(w.SPY,.5);self.assertAlmostEqual(w.BIL,.5)
        for change in ['stale','nan','negative','duplicate','sum','target']:
            bad=copy.deepcopy(b)
            if change=='stale':bad['origin']='2026-07-31'
            elif change=='target':bad['target']='2026-10-31'
            elif change=='nan':bad['weights'][0]['weight_pct']=float('nan')
            elif change=='negative':bad['weights'][0]['weight_pct']=-50
            elif change=='duplicate':bad['weights'].append(bad['weights'][0])
            else:bad['weights'][0]['weight_pct']=25
            with self.assertRaises(ValueError,msg=change):validated_weights(bad,'2026-09-08')

    def test_closed_month_calendar_does_not_bridge_gap_or_use_stale_quote(self):
        index=pd.bdate_range('2025-01-01','2025-07-08')
        class Data:
            as_of='2025-07-08'
            def price(self,s):
                p=pd.Series(np.arange(len(index))+100.,index=index)
                if s=='GAP':return p[p.index.month!=3]
                if s=='STALE':return p.drop(pd.Timestamp('2025-05-30'))
                return p
        r=monthly_returns(Data(),['SPY','GAP','STALE'])
        self.assertEqual(str(r.index[-1].date()),'2025-06-30')
        self.assertTrue(pd.isna(r.loc['2025-03-31','GAP']))
        self.assertTrue(pd.isna(r.loc['2025-04-30','GAP']))
        self.assertTrue(pd.isna(r.loc['2025-05-31','STALE']))
        self.assertTrue(pd.isna(r.loc['2025-06-30','STALE']))

    def test_crypto_bar_available_before_us_month_close(self):
        daily=pd.date_range('2025-01-01','2025-04-08')
        class Data:
            as_of='2025-04-08'
            def price(self,s):
                p=pd.Series(np.arange(len(daily))+100.,index=daily)
                return p if s=='BTC-USD' else p[p.index.dayofweek<5]
        d=Data();r=monthly_returns(d,['SPY','BTC-USD']);p=d.price('BTC-USD')
        self.assertAlmostEqual(r.loc['2025-03-31','BTC-USD'],p['2025-03-30']/p['2025-02-27']-1)

    def test_return_sign_tail_mdd_initial_wealth_and_weight_change(self):
        idx=pd.date_range('2020-01-31',periods=120,freq='ME')
        f=pd.DataFrame({'SPY':[-.2]+[0.]*119,'BIL':0.},index=idx)
        book,wealth,dd,m=fixed_book(f,pd.Series({'SPY':.5,'BIL':.5}))
        self.assertEqual(m['mdd_pct'],-10);self.assertEqual(m['cash_pct'],50)
        self.assertEqual(m['effective_assets'],2);self.assertEqual(m['var95_pct'],0)
        self.assertLess(m['cvar95_pct'],0);self.assertAlmostEqual(wealth.iloc[0],.9)
        self.assertEqual(fixed_book(f,pd.Series({'SPY':1.,'BIL':0.}))[3]['mdd_pct'],-20)
        f['SPY']=np.linspace(-.12,.10,120)
        m=fixed_book(f,pd.Series({'SPY':1.,'BIL':0.}))[3]
        self.assertAlmostEqual(m['var95_pct'],-10.9)
        self.assertLessEqual(m['cvar95_pct'],m['var95_pct']);self.assertLessEqual(m['var99_pct'],m['var95_pct'])

    def test_missing_held_return_is_not_zero_or_silently_renormalized(self):
        idx=pd.date_range('2020-01-31',periods=120,freq='ME')
        f=pd.DataFrame({'SPY':.01,'BIL':0.},index=idx);f.iloc[40,0]=np.nan
        with self.assertRaises(ValueError):fixed_book(f,pd.Series({'SPY':.5,'BIL':.5}))
        self.assertEqual(fixed_book(f,pd.Series({'SPY':0.,'BIL':1.}))[3]['vol_pct'],0)

    def test_multivariate_factor_recovers_known_coefficients(self):
        rng=np.random.default_rng(703);idx=pd.date_range('2021-01-31',periods=60,freq='ME')
        x=rng.normal(0,.03,(60,9));r=pd.DataFrame(index=idx)
        r['SPY']=x[:,0];r['IEF']=rng.normal(0,.01,60)
        for i,(_,a,b) in enumerate(FACTORS):r[a]=x[:,i]+(r[b] if b else 0)
        betas=np.array([.8,.2,-.4,.7,.1,-.6,.3,-.2,.5]);book=pd.Series(.002+x@betas,index=idx)
        f=factor_exposure(r,book)
        np.testing.assert_allclose([a['beta'] for a in f['exposures']],betas,atol=1e-6)
        self.assertEqual(f['r2'],1);self.assertEqual(f['intercept_pct'],.2);self.assertEqual(f['rank'],10)
        r['IWM']=r['SPY']
        with self.assertRaises(ValueError):factor_exposure(r,book)

    def test_stress_contributions_mapping_and_bp_matrix(self):
        config=read_json(ROOT/'config/risk_stress.json')
        result=stress_results(pd.Series({'SPY':.4,'TLT':.4,'BIL':.2}),config)
        for s in result['scenarios']:
            self.assertAlmostEqual(s['impact_pct'],sum(s['contributions_pct']),places=5)
        self.assertEqual(next(s for s in result['scenarios'] if s['id']=='rates_100bp')['impact_pct'],-9.6)
        self.assertEqual(sum(result['weights_pct']),100)
        with self.assertRaises(ValueError):stress_results(pd.Series({'UNKNOWN':1.}),config)
        bad=copy.deepcopy(config);bad['scenarios'][0]['shocks_pct'][0]=-101
        with self.assertRaises(ValueError):stress_results(pd.Series({'SPY':1.}),bad)

    def records(self):
        return [dict(origin=str(t.date()),target=str((t+pd.offsets.MonthEnd(1)).date()),
                     train_target_end=str(t.date()),prediction=p,actual=a)
                for t,p,a in zip(pd.date_range('2025-01-31',periods=6,freq='ME'),[2,-2,1,-1,3,0],[2,0,1,-1,-3,4])]

    def test_neutral_boundaries_and_actual_neutral_is_direction_miss(self):
        s=directional_confidence(self.records(),'2025-08-08')
        self.assertEqual(s['all']['n'],6);self.assertEqual(s['all']['hits'],3)
        self.assertEqual(s['directional']['n'],3);self.assertEqual(s['directional']['hits'],1)
        self.assertEqual(s['neutral']['n'],3);self.assertEqual(s['neutral']['hits'],2)

    def test_future_unmatured_missing_actual_and_overlapping_horizon(self):
        records=self.records();records[-1]['actual']=None
        s=directional_confidence(records,'2025-06-08')
        self.assertEqual(s['all']['n'],4);self.assertEqual(s['excluded'],2)
        records[0]['train_target_end']='2025-02-28'
        with self.assertRaises(ValueError):directional_confidence(records,'2025-06-08')
        records=self.records()
        for r in records:r['target']=str((pd.Timestamp(r['origin'])+pd.offsets.MonthEnd(3)).date())
        self.assertEqual(directional_confidence(records,'2025-06-08',3)['all']['n'],2)
        self.assertIsNone(directional_confidence([],'2025-06-08')['up']['hit_pct'])


if __name__=='__main__':unittest.main()

import unittest,json
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.maximus_features import StationarySIS,target_series,target_labels,endpoint_cycle
from pipeline.maximus_moe import walk_forward,known_before,gate,crash_adjustment,NAMES


class MaximusTests(unittest.TestCase):
    def test_sp500_relative_strength_uses_cross_index(self):
        from pipeline.maximus_features import build_inputs
        dates=pd.date_range('2019-01-31',periods=80,freq='ME');t=np.arange(80)
        sp=pd.Series(100*np.exp(.01*t+.05*np.sin(t/3)),index=dates)
        kr=pd.Series(100*np.exp(.004*t+.04*np.cos(t/4)),index=dates)
        keys=['OWN_VOL12','OWN_MA10_DISTANCE','UMCSENT','RSAFS','KR_EXPORT','SOX_3m','FEDFUNDS','KR_BASE','T10Y2Y','CPIAUCSL','PCEPILFE','OIL_YoY','INDPRO','PAYEMS','PERMIT','NFCI','VIX','BAMLH0A0HYM2','VIX_z','GAMMA_TERM','SKEW_z']
        shared=pd.DataFrame({k:np.sin(t/6)+t*.01 for k in keys},index=dates)
        class D:
            as_of='2025-09-08'
            def price(self,key):return {'^GSPC':sp,'^KS11':kr}.get(key,pd.Series(dtype=float))
            def monthly(self,key):return self.price(key)
        with patch('pipeline.maximus_features.build_features',return_value=(shared,None)):
            x,_=build_inputs(D(),'^GSPC','idx')
        expected=(sp.pct_change(6)-kr.pct_change(6))*100
        pd.testing.assert_series_equal(x['tech_relative6'],expected,check_names=False)
        self.assertGreater(x['tech_relative6'].abs().max(),1)

    def test_ten_experts_and_future_invariance_with_embargo(self):
        rng=np.random.default_rng(33);dates=pd.date_range('2010-01-31',periods=57,freq='ME')
        X=pd.DataFrame(rng.normal(size=(57,5)),index=dates,columns=['macro','tech_return1','cmp_crash','cmp_overheat','anchor_gap'])
        p=pd.Series(100*np.exp(np.cumsum(rng.normal(0,.03,57))),index=dates)
        ctx=dict(level=p,kind='ret');a=walk_forward(X,ctx,min_train=48,epochs=2,explain=True)
        json.dumps(a,allow_nan=False)
        changed=X.copy();changed.iloc[-1]*=1000
        b=walk_forward(changed,ctx,min_train=48,epochs=2,explain=False)
        self.assertEqual(a['records'][:-1],b['records'][:-1])
        for r in a['records']:
            self.assertEqual(list(r['experts']),NAMES);self.assertAlmostEqual(sum(r['weights'].values()),1,places=5)
            self.assertLess(r['train_target_end'],r['origin']);self.assertEqual(r['prediction'],r['override']['adjusted'])
        e=a['explanation'];self.assertAlmostEqual(e['base']+e['rational']+e['irrational']+e['interaction'],e['prediction'],places=4)
        from pipeline.maximus_views import target_card
        missing=json.loads(json.dumps(a));missing['records'][-1]['current']=None
        missing.update(symbol='DGS10',name='10Y',mode='macro',kind='ret',unit='%',observation_lag=0,history=[])
        card=target_card(missing)
        self.assertIsNone(card['bp_change']);self.assertIsNone(card['forecast']);self.assertIsNone(card['probability'])
        self.assertEqual(card['bands'],{});self.assertNotIn('strategy',card)

    def test_cpi_is_yoy_change_with_information_month_and_missing_label(self):
        index=pd.date_range('2020-01-01','2026-08-01',freq='MS');raw=pd.Series(100+np.arange(len(index))*.5,index=index)
        raw.loc['2025-10-01']=np.nan
        class D:
            as_of='2026-09-08'
            def mac(self,key):return raw
        ctx=target_series(D(),'CPIAUCSL','macro');y=target_labels(ctx)
        self.assertEqual(ctx['kind'],'diff');self.assertEqual(ctx['observation_lag'],1)
        self.assertAlmostEqual(ctx['level'].loc['2026-08-31'],(raw.loc['2026-07-01']/raw.loc['2025-07-01']-1)*100)
        self.assertTrue(pd.isna(ctx['level'].loc['2025-11-30']))
        self.assertTrue(pd.isna(y.loc['2025-10-31']))

    def test_gate_cannot_observe_adjacent_month_and_crash_units(self):
        r=dict(target='2020-03-31',actual=2.,experts=dict.fromkeys(NAMES,1.))
        self.assertEqual(known_before([r],'2020-03-31'),[])
        self.assertEqual(len(known_before([r],'2020-04-30')),1)
        down,meta=crash_adjustment(10,3,1,2,'ret');self.assertEqual(down,1);self.assertEqual(meta['severity'],1)
        same,meta=crash_adjustment(.4,3,1,2,'diff');self.assertEqual(same,.4);self.assertFalse(meta['applied'])

    def test_hp_endpoint_does_not_use_future_observations(self):
        x=pd.Series(np.sin(np.arange(85)/5)+np.arange(85)*.1,index=pd.date_range('2010-01-31',periods=85,freq='ME'))
        a=endpoint_cycle(x);b=endpoint_cycle(x.iloc[:75]);pd.testing.assert_series_equal(a.iloc[:75],b)

    def test_forecast_test_nulls_and_direction_skill(self):
        from pipeline.maximus_views import directional_test,loss_test
        actual=np.tile([-1.,1.],50)
        self.assertLess(directional_test(actual,actual),.001)
        self.assertIsNone(directional_test(np.ones(100),actual))
        self.assertEqual(loss_test(np.zeros(100),actual),1.)
        self.assertLess(loss_test(actual*.8,np.tile([-.8,1.,-1.2,1.5],25)),.001)


if __name__=='__main__':unittest.main()

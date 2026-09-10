import unittest
import numpy as np
import pandas as pd
from pipeline.strategy_cards import pair_observation,annual_rebound,recovery,settings,pairs,turnaround,views


class StrategyCardTests(unittest.TestCase):
    def pair_prices(self):
        rng=np.random.default_rng(912);dates=pd.bdate_range('2024-01-01',periods=600)
        x=np.cumsum(rng.normal(0,.015,600))+5;residual=rng.normal(0,.03,600)
        return pd.Series(np.exp(1.25*x+residual),index=dates),pd.Series(np.exp(x),index=dates)

    def test_pair_fit_lookback_sample_deviation_and_display_midrange(self):
        a,b=self.pair_prices();cut=str(a.index[-1].date());r=pair_observation(a,b,cut)
        self.assertAlmostEqual(r['beta'],1.25,delta=.04)
        self.assertEqual(r['fit_start'],str(a.index[-252].date()));self.assertEqual(r['z_start'],str(a.index[-120].date()))
        self.assertEqual(len(r['spark']),44);self.assertEqual(r['spark'][-1][0],cut)
        self.assertEqual(r['spark'][0][0],str(a.index[-130].date()))
        self.assertAlmostEqual(r['midrange'],(min(v for _,v in r['spark'])+max(v for _,v in r['spark']))/2,places=5)
        self.assertLess(r['pvalue'],.05)

    def test_future_price_shocks_have_no_effect(self):
        a,b=self.pair_prices();cut=str(a.index[-2].date());r=pair_observation(a,b,cut)
        a.iloc[-1]=1e20;b.iloc[-1]=1e-20
        self.assertEqual(pair_observation(a,b,cut),r)

    def test_pair_missing_stale_constant_duplicate_and_alignment(self):
        a,b=self.pair_prices();cut=str(a.index[-1].date())
        self.assertEqual(pair_observation(a.tail(251),b,cut)['signal'],'missing')
        self.assertEqual(pair_observation(a,b*0+1,cut)['signal'],'missing')
        self.assertEqual(pair_observation(a,b,str((a.index[-1]+pd.Timedelta(days=8)).date()))['signal'],'missing')
        with self.assertRaises(ValueError):pair_observation(pd.concat([a,a.tail(1)]),b,cut)
        self.assertEqual(pair_observation(a,b.iloc[:-1],cut)['date'],str(b.index[-2].date()))

    def test_signal_direction_uses_unrounded_z(self):
        a,b=self.pair_prices();cut=str(a.index[-1].date())
        a.iloc[-1]*=.6;self.assertEqual(pair_observation(a,b,cut)['signal'],'long_a')
        a.iloc[-1]/=.36;self.assertEqual(pair_observation(a,b,cut)['signal'],'short_a')

    def annual(self,values=(100,-50,20)):
        return pd.Series(values,index=pd.to_datetime(['2023-12-31','2024-12-31','2025-12-31']))

    def test_annual_rebound_is_not_quarterly_or_future_profit(self):
        self.assertTrue(annual_rebound(self.annual(),'2026-09-08')['blackink'])
        self.assertFalse(annual_rebound(self.annual((100,50,80)),'2026-09-08')['blackink'])
        self.assertIsNone(annual_rebound(self.annual((100,50,-10)),'2026-09-08'))
        self.assertIsNone(annual_rebound(self.annual().set_axis(pd.to_datetime(['2025-06-30','2025-09-30','2025-12-31'])),'2026-09-08'))
        self.assertIsNone(annual_rebound(self.annual(),'2025-09-08'))

    def test_recovery_price_conditions_score_and_dates(self):
        dates=pd.bdate_range(end='2026-09-08',periods=300);p=pd.Series(100.,index=dates);p.iloc[-252]=200;p.iloc[-1]=150
        r=recovery(self.annual(),p,'2026-09-08',15)
        self.assertEqual(r['score_parts'],[1,1,1,0]);self.assertEqual(r['score'],3)
        self.assertEqual(recovery(self.annual(),p,'2026-09-08',15.01)['score'],4)
        self.assertEqual(r['off_low'],50);self.assertEqual(r['off_high'],-25);self.assertEqual(len(r['spark']),44)
        p.iloc[-1]=199;self.assertIsNone(recovery(self.annual(),p,'2026-09-08',20))

    def test_designated_inventory_and_missing_pairs_are_preserved(self):
        self.assertEqual(len(settings()['pairs']),13)
        self.assertEqual(sum(r[3]=='US' for r in settings()['pairs']),9)
        class Empty:
            as_of='2026-09-08'
            def price(self,s):return pd.Series(dtype=float)
        r=pairs(Empty());self.assertEqual(len(r['rows']),13);self.assertEqual(r['scope']['available'],0)

    def test_official_membership_and_financial_coverage(self):
        class Empty:
            as_of='2026-09-08';fund={}
            members={'us_largecap':{'as_of':'2026-09-04','members':[{'symbol':'US1','name':'US1'}]},'kr_largecap':{'members':[{'symbol':'KR1','name':'KR1'}]},'kospi200':{'members':[{'symbol':'KR1','name':'KR1'}]}}
        r=turnaround(Empty());self.assertEqual(r['scope']['expected'],2);self.assertEqual(r['scope']['available'],0);self.assertEqual(r['rows'],[])

    def test_module_cards_follow_the_renderer_schema_on_rebuild(self):
        class Empty:
            as_of='2026-09-08';fund={};members={}
            def price(self,s):return pd.Series(dtype=float)
        obj=dict(sections=[],cards=[['old quarterly count',10]],method_note='',missing=[])
        views(Empty(),obj);views(Empty(),obj)
        self.assertEqual(obj['cards'],[['연간 반등 후보',0],['재무 표본 / 공식 대상','0 / 0'],['지정 페어',13]])
        self.assertEqual(len(obj['sections']),2);self.assertEqual(len(obj['missing']),1)

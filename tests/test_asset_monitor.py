import unittest
import numpy as np
import pandas as pd
from pipeline.asset_monitor import observation,monitor,views,INSTRUMENTS,ETF
from pipeline.catalog import extra_price_symbols


class MonitorTests(unittest.TestCase):
    def prices(self):
        dates=pd.bdate_range('2024-01-01','2026-09-08')
        return pd.Series(np.arange(len(dates),dtype=float)+100,index=dates)

    def test_observation_intervals_and_ytd_first_close(self):
        p=self.prices();r=observation(p,'2026-09-08')
        for j,n in [(0,1),(1,5),(2,21),(3,63),(5,252)]:
            self.assertAlmostEqual(r['values'][j],(p.iloc[-1]/p.iloc[-n-1]-1)*100,places=5)
            self.assertEqual(r['anchors'][j],str(p.index[-n-1].date()))
        year=p.loc['2026'];self.assertEqual(r['anchors'][4],str(year.index[0].date()))
        self.assertAlmostEqual(r['values'][4],(p.iloc[-1]/year.iloc[0]-1)*100,places=5)
        self.assertNotAlmostEqual(r['values'][4],(p.iloc[-1]/p.loc[:'2025'].iloc[-1]-1)*100,places=5)

    def test_future_prices_do_not_change_any_observation(self):
        p=self.prices();future=pd.concat([p,pd.Series([1e12],index=pd.to_datetime(['2026-09-09']))])
        self.assertEqual(observation(p,'2026-09-08'),observation(future,'2026-09-08'))

    def test_three_trend_states_and_insufficient_history(self):
        p=self.prices();self.assertEqual(observation(p,'2026-09-08')['signal'],'long')
        self.assertEqual(observation(p.iloc[::-1].set_axis(p.index),'2026-09-08')['signal'],'short')
        self.assertEqual(observation(p*0+100,'2026-09-08')['signal'],'neutral')
        short=observation(p.iloc[-199:],'2026-09-08');self.assertIsNone(short['ma200']);self.assertEqual(short['signal'],'missing')
        self.assertIsNotNone(short['values'][2]);self.assertIsNone(short['values'][5])

    def test_crypto_uses_observations_without_dropping_weekends(self):
        p=pd.Series(range(100,465),index=pd.date_range('2025-09-09',periods=365))
        r=observation(p,'2026-09-08');self.assertEqual(r['anchors'][1],'2026-09-03')
        self.assertEqual(r['anchors'][2],'2026-08-18')

    def test_missing_stale_midyear_and_duplicate_dates(self):
        p=self.prices();r=observation(p.loc[:'2026-08-01'],'2026-09-08')
        self.assertTrue(all(v is None for v in r['values']));self.assertEqual(r['signal'],'missing')
        self.assertEqual(observation(p.iloc[:0],'2026-09-08')['observations'],0)
        self.assertIsNone(observation(p.loc['2026-07':],'2026-09-08')['values'][4])
        with self.assertRaises(ValueError):observation(pd.concat([p,p.iloc[-1:]]),'2026-09-08')

    def test_inventory_price_basis_cards_and_rebuild(self):
        p=self.prices();calls=[]
        class Data:
            as_of='2026-09-08'
            def price(self,s,adjusted=True):
                calls.append((s,adjusted));return p.iloc[:0] if s=='^RUT' else p
        d=Data();s=monitor(d)
        self.assertEqual(len(s['rows']),21);self.assertEqual(len(s['cards']),4)
        self.assertEqual(len({r['group'] for r in s['rows']}),6)
        self.assertIn(('^GSPC',False),calls);self.assertIn(('^IXIC',False),calls);self.assertIn(('GC=F',False),calls)
        for e in ETF:self.assertIn((e,True),calls)
        self.assertEqual(s['cards'][0]['value'],20);self.assertEqual(s['cards'][1]['value'],0)
        self.assertEqual(next(r for r in s['rows'] if r['symbol']=='^RUT')['signal'],'missing')
        self.assertIn('^RUT',extra_price_symbols())
        obj=dict(sections=[{'type':'bars','group':'자산 모니터'},{'type':'scanner','group':'패턴 스캐너'}],method_note='배분 설명',missing=[])
        views(d,obj);once=obj.copy();views(d,obj)
        self.assertEqual(len(obj['sections']),2);self.assertEqual(len(obj['missing']),1);self.assertEqual(obj['method_note'],once['method_note'])

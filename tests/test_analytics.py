import unittest
import numpy as np
import pandas as pd
from pipeline.analytics import align, cumulative_excess, relative_strength, stock_ranking, trailing_return, ytd_return
from pipeline.build import make_snapshots
from pipeline.universe import PAIRS, ASSETS


class Calculations(unittest.TestCase):
    def test_return_units_and_off_by_one(self):
        s = pd.Series([100,101,102,103,104,110], index=pd.bdate_range('2025-01-01',periods=6))
        self.assertAlmostEqual(trailing_return(s,5),10)
        self.assertIsNone(trailing_return(s,6))

    def test_alignment_never_fills_holidays_or_uses_future(self):
        a = pd.Series([100,200,400],index=pd.to_datetime(['2025-01-01','2025-01-02','2025-01-03']))
        b = pd.Series([100,400],index=pd.to_datetime(['2025-01-01','2025-01-03']))
        f = align(a,b,'2025-01-02')
        self.assertEqual(list(f.index), [pd.Timestamp('2025-01-01')])

    def test_spread_z_hand_calculation_and_ddof(self):
        # One-session spreads are exactly [10,20,30] pp. Population z at 30 = sqrt(1.5).
        f = pd.DataFrame({'a':[100,110,132,171.6],'b':[100,100,100,100]})
        r = relative_strength(f,window=3,lag=1)
        self.assertAlmostEqual(r.spread_pp.iloc[-1],30)
        self.assertAlmostEqual(r.z.iloc[-1],np.sqrt(1.5))
        self.assertTrue(r.z.iloc[:3].isna().all())

    def test_ratio_curve_is_not_arithmetic_spread(self):
        f = pd.DataFrame({'a':[100,130], 'b':[100,110]},index=pd.to_datetime(['2025-01-01','2025-04-01']))
        s,base = cumulative_excess(f,3)
        self.assertEqual(base,'2025-01-01')
        self.assertEqual(s.iloc[0],0)
        self.assertAlmostEqual(s.iloc[-1],100*(1.3/1.1-1))
        self.assertNotAlmostEqual(s.iloc[-1],20)

    def test_ytd_uses_previous_year_close(self):
        s = pd.Series([100,105,120],index=pd.to_datetime(['2024-12-31','2025-01-02','2025-09-08']))
        self.assertAlmostEqual(ytd_return(s),20)
        self.assertIsNone(ytd_return(s.iloc[1:]))

    def test_future_append_leaves_historical_z_unchanged(self):
        f = pd.DataFrame({'a':100+np.sin(np.arange(1500)/17)*10+np.arange(1500)/10,'b':100+np.arange(1500)/20})
        pd.testing.assert_frame_equal(relative_strength(f.iloc[:1400]),relative_strength(f).iloc[:1400])

    def test_flat_series_remains_missing_not_infinite(self):
        f = pd.DataFrame({'a':[100]*1400,'b':[100]*1400})
        self.assertTrue(relative_strength(f).z.isna().all())

    def test_universe_contract_and_no_fabricated_missing(self):
        self.assertEqual(len(PAIRS),35)
        self.assertEqual(sum(p['sector'] for p in PAIRS),24)
        self.assertEqual(len(ASSETS),32)
        r,m = make_snapshots({},dict(provider='fixture',vintage='2025-01-01',instruments={}), '2025-01-01')
        self.assertEqual(r['coverage']['pairs'],0)
        self.assertEqual(m['coverage']['assets'],0)
        self.assertTrue(all(x['z'] is None and x['reason'] for x in r['pairs']))

    def test_equal_stock_scores_receive_equal_percentile(self):
        s = pd.Series(np.arange(100,400),index=pd.bdate_range('2024-01-01',periods=300))
        out = stock_ranking({'A':s,'B':s},[dict(symbol='A',name='a'),dict(symbol='B',name='b')],str(s.index[-1].date()))
        self.assertEqual(out['leaders'][0]['rs_rating'],out['leaders'][1]['rs_rating'])


if __name__ == '__main__':
    unittest.main()

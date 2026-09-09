import unittest
import numpy as np
import pandas as pd
from pipeline.technical_scan import wilder,indicators,scan


def candles(flat=False,volume=1000):
    dates=pd.bdate_range('2024-01-01',periods=320)
    close=np.full(320,100.) if flat else 100+np.arange(320)*.2+np.sin(np.arange(320))
    return pd.DataFrame(dict(open=close,high=close+(0 if flat else 1),low=close-(0 if flat else 1),close=close,adjusted_close=close,volume=volume),index=dates)


class ScanTests(unittest.TestCase):
    def test_wilder_initial_mean_and_recursive_update(self):
        s=pd.Series(range(1,20),dtype=float);a=wilder(s,14)
        self.assertTrue(a.iloc[:13].isna().all());self.assertEqual(a.iloc[13],7.5)
        self.assertAlmostEqual(a.iloc[14],(7.5*13+15)/14)

    def test_flat_market_has_neutral_defined_indicators(self):
        r=scan(candles(flat=True))
        self.assertEqual(r['rsi'],50);self.assertEqual(r['adx'],0);self.assertEqual(r['position'],50)
        self.assertEqual(r['score'],0);self.assertEqual(r['available'],12)

    def test_score_evidence_and_no_volume_data(self):
        r=scan(candles(volume=0))
        self.assertEqual(len(r['rules']),12);self.assertEqual(r['available'],11)
        self.assertIsNone(next(a for a in r['rules'] if a['key']=='거래량')['value'])
        self.assertEqual(r['score'],sum(a['value'] for a in r['rules'] if a['value'] is not None))
        self.assertEqual(len(r['candles']),90);self.assertEqual([l['name'] for l in r['lines']],['MA20','MA60'])
        self.assertTrue(0<=r['adx']<=100 and 0<=r['rsi']<=100)

    def test_adx_is_scale_invariant_and_uses_directional_movement(self):
        f=candles();a=indicators(f);g=f.copy();g['adjusted_close']*=2;b=indicators(g)
        self.assertAlmostEqual(a['adx'].iloc[-1],b['adx'].iloc[-1])
        self.assertAlmostEqual(a['atr'].iloc[-1]*2,b['atr'].iloc[-1])
        self.assertGreater(a['plus_di'].iloc[-1],a['minus_di'].iloc[-1])
        self.assertTrue(a['adx'].iloc[:27].isna().all());self.assertTrue(pd.notna(a['adx'].iloc[27]))

    def test_future_bars_do_not_change_past_indicators(self):
        f=candles();before=indicators(f.iloc[:280]);changed=f.copy();changed.loc[changed.index[280:],['open','high','low','close','adjusted_close']]*=10
        after=indicators(changed)
        for k in ['adx','atr','rsi','macd','cci','stoch_k','width']:
            self.assertAlmostEqual(before[k].iloc[-1],after[k].loc[before[k].index[-1]],places=9)


if __name__=='__main__':unittest.main()

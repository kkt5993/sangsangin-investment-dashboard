import unittest
import numpy as np
from pipeline.wagdog import profile,roots
from pipeline.options_data import normalize
import pandas as pd

class OptionProfileTests(unittest.TestCase):
    def test_cboe_occ_parser_and_atm_quality_gate(self):
        options=[]
        for expiry in ['260917','260918','260925','261002']:
            for strike in range(95,106):
                for side in ['C','P']:options.append(dict(option=f'TEST{expiry}{side}{strike*1000:08d}',open_interest=10,iv=.25,bid=1,ask=2,volume=5))
        raw=dict(symbol='TEST',timestamp='2026-09-09 03:00:00',data=dict(current_price=100,options=options))
        out=normalize(raw,'TEST',pd.Timestamp('2026-09-09T08:00Z'))
        self.assertEqual(len(out['expiries']),3);self.assertEqual(len(out['records']),66);self.assertEqual(out['quality']['atm_positive_oi'],66)
        self.assertEqual(out['records'][0]['strike'],95)
        for r in raw['data']['options']:r['open_interest']=0
        with self.assertRaisesRegex(ValueError,'coverage'):normalize(raw,'TEST',pd.Timestamp('2026-09-09T08:00Z'))
    def raw(self):
        records=[]
        for k in [80,90,100,110,120]:
            for side in ['call','put']:records.append(dict(strike=k,side=side,expiry='2026-10-02',openInterest=100,impliedVolatility=.25,contractSize='REGULAR'))
        return dict(symbol='TEST',records=records,retrieved_at='2026-09-09T08:00:00+00:00',expiries=['2026-10-02'])
    def test_equal_call_put_gamma_offsets_oi_stays_positive(self):
        p=profile(self.raw(),100,.03);self.assertAlmostEqual(p['net'],0)
        self.assertIsNone(p['flip'])
        self.assertEqual(p['put_call'],1);self.assertTrue(all(r['gex']==0 and r['call_oi']==r['put_oi']==100 for r in p['profile']))
    def test_missing_iv_keeps_oi_but_excludes_gamma(self):
        r=self.raw();r['records'][0]['impliedVolatility']=None;r['records'][1]['impliedVolatility']=None
        p=profile(r,100,.03);self.assertEqual(p['valid_gamma'],8);self.assertEqual(p['valid_oi'],10)
        self.assertIsNone(p['profile'][0]['gex']);self.assertEqual(p['profile'][0]['put_oi'],100)
    def test_expired_and_nonstandard_excluded(self):
        r=self.raw();r['records'][0]['expiry']='2026-09-08';r['records'][1]['contractSize']='MINI'
        p=profile(r,100,.03);self.assertEqual(p['valid_oi'],8);self.assertEqual(p['valid_gamma'],8)
    def test_no_crossing_is_not_a_zero_flip(self):
        self.assertEqual(roots(np.array([80,100,120]),np.array([2.,3.,4.])),[])
        self.assertEqual(roots(np.array([80,100,120]),np.array([-2.,2.,0.])),[90.,120.])
    def test_expected_move_scales_iv_to_30_days(self):
        p=profile(self.raw(),100,.03);self.assertAlmostEqual(p['em'],.25*np.sqrt(30/365.25)*100,places=5)
        self.assertAlmostEqual(p['em_high']+p['em_low'],200)

if __name__=='__main__':unittest.main()

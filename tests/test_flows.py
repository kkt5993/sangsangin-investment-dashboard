import unittest
from pipeline.flows import coefficient,straddle,sensitivity,theme_rows

class FlowTests(unittest.TestCase):
    def test_daily_reset_not_leveraged_notional(self):
        # A $100 fund at +2x and a $100 fund at -2x together need $40
        # additional notional after a hypothetical +5% underlying move.
        self.assertEqual(coefficient([dict(leverage=2,aum=100),dict(leverage=-2,aum=100)])*.05,40)
        self.assertEqual(coefficient([dict(leverage=1,aum=100)]),0)
        self.assertEqual(coefficient([dict(leverage=-1,aum=100)])*-.05,-10)

    def test_same_strike_and_live_two_sided_quotes(self):
        raw=dict(spot=100,expiry='2026-09-18',records=[dict(strike=100,side=s,bid=b,ask=b+1,openInterest=20,expiry='2026-09-18',contractSize='REGULAR') for s,b in [('call',4),('put',5)]])
        a=straddle(raw);self.assertEqual(a['move_pct'],10);self.assertEqual((a['low'],a['high']),(90,110))
        raw['records'][1]['strike']=101
        self.assertNotEqual(straddle(raw)['status'],'관측','cannot combine different ATM strikes')
        raw['records'][1]['strike']=100;raw['records'][1]['bid']=0
        self.assertNotEqual(straddle(raw)['status'],'관측','zero bid is not a valid midpoint')

    def test_abs_gamma_and_missing_factor(self):
        rows=[dict(gamma_mcap_bp=g,letf_adv_pct=l,option_mcap_pct=o,short_float_pct=s) for g,l,o,s in [(-3,3,3,3),(1,1,1,1),(2,None,2,2)]]
        out=sensitivity(rows);self.assertGreater(out[0]['sensitivity'],out[1]['sensitivity']);self.assertIsNone(out[2]['sensitivity']);self.assertEqual(out[2]['factor_count'],3)

    def test_themes_no_double_count_or_missing_return_zero(self):
        data=[dict(name='AI반도체',code='1',aum_krw=100,nav_1m_pct=10,traded_value=5),dict(name='반도체신규',code='2',aum_krw=100,nav_1m_pct=None,traded_value=5),dict(name='반도체레버리지',code='3',aum_krw=900,nav_1m_pct=30,traded_value=5)]
        themes,members=theme_rows(data);self.assertEqual(len(themes),1);r=themes[0]
        self.assertEqual((r['theme'],r['aum_krw'],r['nav_1m_pct'],r['return_coverage']),('반도체',200,10,50));self.assertEqual(len(members),2)

if __name__=='__main__':unittest.main()

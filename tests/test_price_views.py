import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.analytics import rs_percentiles
from pipeline.etf_details import etf_row, observed_frequency, monitor
from pipeline.market_modules import rankings
from pipeline.engine import Data
from pipeline.build import make_snapshots


def fixture_frame(start='2024-01-01',end='2026-09-09'):
    dates=pd.bdate_range(start,end)
    return pd.DataFrame(dict(close=100.,adjusted_close=100.,dividend=0.,split=0.),index=dates)


class PriceViews(unittest.TestCase):
    def test_rank_range_ties_and_singleton(self):
        np.testing.assert_allclose(rs_percentiles(pd.Series([20.,10.,30.])),[50,1,99])
        np.testing.assert_allclose(rs_percentiles(pd.Series([10.,10.,10.])),[50,50,50])
        self.assertEqual(rs_percentiles(pd.Series([10.])).iloc[0],50)
        self.assertTrue(rs_percentiles(pd.Series(dtype=float)).empty)

    def test_weekly_extremes_are_worst_first_and_keep_eight_table_rows(self):
        d=Data.__new__(Data);d.as_of='2026-09-08';d.frames={};d.members={}
        members=[]
        for i in range(20):
            s=str(i);f=fixture_frame(end=d.as_of)
            f['adjusted_close']=100*np.exp(np.arange(len(f))*((i-10)/10000))
            d.frames[s]=f;members.append(dict(symbol=s,name=s,sector='test'))
        d.members={k:dict(members=members) for k in ['kr_largecap','us_largecap','kospi200']}
        result=rankings(d)['US']
        self.assertEqual([r['symbol'] for r in result['strong']],list(map(str,range(19,11,-1))))
        self.assertEqual([r['symbol'] for r in result['weak_table']],list(map(str,range(8))))
        self.assertEqual([r['symbol'] for r in result['weak']],list(map(str,range(6))))
        self.assertEqual(result['rows'][0]['rs'],99)
        self.assertEqual(result['rows'][-1]['rs'],1)

    def test_cash_window_exdates_and_future_prices(self):
        f=fixture_frame();f.loc['2025-09-08','dividend']=90 # left endpoint excluded
        f.loc['2026-09-08','dividend']=12;f.loc['2026-09-09','dividend']=50
        f.loc['2026-09-09','close']=1;f.loc['2026-09-08','split']=5
        d=SimpleNamespace(as_of='2026-09-08',frames={'X':f},quality={})
        r=etf_row(d,dict(symbol='X',name='fixture'))
        self.assertEqual(r['events'],[['2026-09-08',12.]])
        self.assertEqual(r['yield_pct'],12.)
        self.assertEqual(r['monthly_per_10m'],100000.)
        self.assertEqual(r['as_of'],'2026-09-08')
        self.assertEqual(r['returns'],[0,0,0,0])

    def test_no_cash_is_zero_but_short_missing_or_stale_is_unknown(self):
        full=fixture_frame(end='2026-09-08')
        d=SimpleNamespace(as_of='2026-09-08',frames={'X':full},quality={})
        self.assertEqual(etf_row(d,dict(symbol='X',name='x'))['yield_pct'],0)
        d.frames['X']=full.loc['2026-08-01':]
        r=etf_row(d,dict(symbol='X',name='x'))
        self.assertIsNone(r['yield_pct']);self.assertFalse(r['complete_12m'])
        self.assertIsNone(r['returns'][1])
        d.frames['X']=full.drop(columns=['dividend'])
        self.assertIsNone(etf_row(d,dict(symbol='X',name='x'))['yield_pct'])
        d.frames['X']=full.loc[:'2026-08-01']
        self.assertIn('오래됨',etf_row(d,dict(symbol='X',name='x'))['reason'])
        self.assertIsNone(etf_row(d,dict(symbol='NONE',name='none'))['payments'])

    def test_recent_distribution_spacing_overrides_old_monthly_observations(self):
        dates=list(pd.date_range('2025-10-01',periods=5,freq='MS'))+list(pd.date_range('2026-07-01',periods=9,freq='7D'))
        self.assertEqual(observed_frequency(pd.Series(1.,index=dates)),'주간 간격')
        self.assertEqual(observed_frequency(pd.Series(1.,index=pd.date_range('2025-10-01',periods=12,freq='MS'))),'월간 간격')
        self.assertEqual(observed_frequency(pd.Series(1.,index=pd.date_range('2025-10-01',periods=4,freq='3MS'))),'분기 간격')
        self.assertEqual(observed_frequency(pd.Series([1],index=pd.to_datetime(['2026-01-01']))),'1회 관측')

    def test_category_keeps_unavailable_positions_and_sorts_known_yields(self):
        f=fixture_frame(end='2026-09-08');g=f.copy();f.loc['2026-09-08','dividend']=5;g.loc['2026-09-08','dividend']=2
        d=SimpleNamespace(as_of='2026-09-08',frames={'HIGH':f,'LOW':g},quality={})
        cat=[dict(id='monthly',name='test',items=[dict(symbol=s,name=s) for s in ['NONE','LOW','HIGH']])]
        with patch('pipeline.etf_details.etfs',return_value=cat):out=monitor(d)
        self.assertEqual([r['symbol'] for r in out['sections'][0]['rows']],['HIGH','LOW','NONE'])
        self.assertEqual(out['status'],'partial')

    def test_stale_asset_cannot_backdate_all_current_assets(self):
        dates=pd.bdate_range('2025-01-01','2026-09-08')
        prices={s:pd.Series(np.arange(len(dates))+100.,index=dates) for s in ['SPY','A']}
        prices['OLD']=prices['A'].loc[:'2026-08-01']
        assets=[dict(symbol=s,name=s,group='country') for s in ['A','OLD']]
        with patch('pipeline.build.ASSETS',assets):_,m=make_snapshots(prices,dict(provider='test',vintage='test',instruments={}), '2026-09-08')
        self.assertEqual(m['asset_as_of'],'2026-09-08')
        self.assertIsNotNone(m['assets'][0]['returns']['3M'])
        self.assertIsNone(m['assets'][1]['returns']['3M'])


if __name__=='__main__':unittest.main()

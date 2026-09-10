import csv,io,unittest,tempfile,hashlib
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.us100_data import parse,collect
from pipeline.momentum_highs import observations,build
from pipeline.engine import Data
from pipeline.incremental import universe_symbols
from pipeline.cache import load_into
from pipeline.store import write_json


def holdings(date='Sep 04, 2026',duplicate=False):
    buf=io.StringIO();w=csv.writer(buf)
    w.writerow(['iShares S&P 100 ETF']);w.writerow(['Fund Holdings as of',date]);w.writerow([])
    w.writerow(['Ticker','Name','Sector','Asset Class','Weight (%)','Currency'])
    for i in range(100):w.writerow(['BRKB' if i==0 or duplicate and i==1 else f'T{i}',f'company {i}','Financials','Equity','0.998','USD'])
    w.writerow(['USD','Cash','Cash','Cash','0.2','USD'])
    w.writerow(['ESU6','Future','Other','Futures','0','USD'])
    return buf.getvalue().encode('utf8')


def frame():
    idx=pd.bdate_range('2025-01-01',periods=300)
    f=pd.DataFrame(dict(open=95.,close=95.,high=100.,low=90.,adjusted_close=95.),index=idx)
    return f


class NewHighsTests(unittest.TestCase):
    def test_official_csv_class_mapping_and_non_equities(self):
        r=parse(holdings(),'2026-09-08')
        self.assertEqual(r['as_of'],'2026-09-04');self.assertEqual(len(r['members']),100)
        self.assertEqual(r['members'][0]['symbol'],'BRK-B');self.assertEqual(r['excluded_non_equities'],2)
        self.assertEqual(universe_symbols({'us100':r}),{m['symbol'] for m in r['members']})

    def test_official_csv_future_stale_duplicate_wrong_fund_and_partial_are_rejected(self):
        for content in [holdings('Sep 09, 2026'),holdings('Aug 01, 2026'),holdings(duplicate=True),holdings().replace(b'S&P 100 ETF',b'Other ETF'),holdings().replace(b'0.998',b'0.01')]:
            with self.assertRaises(ValueError):parse(content,'2026-09-08')

    def test_failed_collection_is_recorded_once_without_replacing_membership(self):
        with tempfile.TemporaryDirectory() as temp,patch('pipeline.us100_data.requests.get',side_effect=RuntimeError('provider unavailable')) as get:
            p=Path(temp);result=collect(p,'2026-09-08')
            self.assertEqual(result['status'],'error');self.assertFalse((p/'us100.json').exists())
            self.assertEqual(collect(p,'2026-09-08'),result);get.assert_called_once()

    def test_membership_loading_verifies_original_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);raw=holdings();(p/'oef_holdings.csv').write_bytes(raw)
            metadata=parse(raw,'2026-09-08');metadata.update(raw_file='oef_holdings.csv',sha256=hashlib.sha256(raw).hexdigest())
            write_json(p/'us100.json',metadata)
            def data():return SimpleNamespace(as_of='2026-09-08',frames={},members={},macro={},fund={})
            with patch('pipeline.cache.chain',return_value=[p]):
                d=data();load_into(d,p,'test');self.assertEqual(len(d.members['us100']['members']),100)
                (p/'oef_holdings.csv').write_bytes(raw+b'tamper')
                with self.assertRaisesRegex(ValueError,'checksum'):load_into(data(),p,'test')

    def test_proximity_boundary_high_vs_close_and_intraday_flag(self):
        f=frame();asof=str(f.index[-1].date());r=observations(f,asof)
        self.assertAlmostEqual(r['from_high'],-5);self.assertEqual(r['high52'],100)
        self.assertFalse(r['new_high']) # touching an old high is not a new extreme
        f.iloc[-1,f.columns.get_loc('high')]=101;r=observations(f,asof)
        self.assertTrue(r['new_high']);self.assertLess(r['from_high'],-5)
        self.assertEqual(r['price'],95) # an intraday breakout need not close at its high

    def test_adjusted_prices_share_the_highs_units_and_keep_endpoints(self):
        f=frame();f.iloc[:-20,f.columns.get_loc('adjusted_close')]*=.5
        f.iloc[:-20,f.columns.get_loc('high')]=180
        r=observations(f,str(f.index[-1].date()))
        self.assertEqual(r['high52'],100) # adjusted historical 180 becomes 90
        self.assertEqual(r['spark'][0],[str(f.index[-130].date()),47.5])
        self.assertEqual(r['spark'][-1],[str(f.index[-1].date()),95.])
        self.assertEqual(len(r['spark']),44)

    def test_future_append_does_not_change_historical_screen(self):
        f=frame();asof=str(f.index[-2].date());before=observations(f.iloc[:-1],asof)
        f.iloc[-1]=1e6
        self.assertEqual(observations(f,asof),before)

    def test_253_bar_requirement_ohlc_and_staleness(self):
        f=frame();asof=str(f.index[-1].date())
        for bad,date in [(f.tail(252),asof),(f, str((f.index[-1]+pd.Timedelta(days=9)).date())),(f.drop(columns=['high']),asof)]:
            with self.assertRaises(ValueError):observations(bad,date)
        f.iloc[-1,f.columns.get_loc('high')]=80
        with self.assertRaisesRegex(ValueError,'OHLC'):observations(f,asof)

    def test_rank_before_filter_and_do_not_substitute_sp500_for_missing_sp100(self):
        d=Data.__new__(Data);f=frame();d.as_of=str(f.index[-1].date());d.frames={};members=[]
        for i in range(10):
            s=str(i);g=f.copy();g['adjusted_close']=95*np.exp(np.linspace(-.04*i,0,len(g)))
            d.frames[s]=g;members.append(dict(symbol=s,name=s,sector='test'))
        # Most strong stocks are deliberately far from their highs. Removing
        # them before ranking would incorrectly promote a weaker candidate.
        for i in range(7,10):d.frames[str(i)].iloc[-10:,d.frames[str(i)].columns.get_loc('high')]=130
        d.members={'us100':dict(members=members,as_of=d.as_of),'kospi200':dict(members=members,as_of=d.as_of)}
        d.resource=lambda _:Path('nonexistent-source-fixture')
        result=build(d)['groups'][0]
        self.assertEqual([r['symbol'] for r in result['rows']],['6'])
        self.assertAlmostEqual(result['rows'][0]['rs'],66.333333)
        d.members['us_largecap']=d.members.pop('us100')
        missing=build(d)['groups'][0]
        self.assertEqual(missing['status'],'missing');self.assertEqual(missing['rows'],[])


if __name__=='__main__':unittest.main()

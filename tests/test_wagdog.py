import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import numpy as np
from pipeline.wagdog import profile,roots,packets
from pipeline.options_data import normalize,collect,FLOW_SCOPE
from pipeline.flows_data import collect_us_options
from pipeline.events_data import save,read
import pandas as pd

class OptionProfileTests(unittest.TestCase):
    def test_cboe_occ_parser_and_atm_quality_gate(self):
        options=[]
        for expiry in ['260917','260918','260925','261002']:
            for strike in range(95,106):
                for side in ['C','P']:options.append(dict(option=f'TEST{expiry}{side}{strike*1000:08d}',open_interest=10,iv=.25,bid=1,ask=2,volume=5))
        raw=dict(symbol='TEST',timestamp='2026-09-09 03:00:00',data=dict(current_price=100,options=options))
        out=normalize(raw,'TEST',pd.Timestamp('2026-09-09T08:00Z'))
        self.assertEqual(len(out['expiries']),4);self.assertEqual(len(out['records']),88);self.assertEqual(out['quality']['atm_positive_oi'],88)
        legacy=normalize(raw,'TEST',pd.Timestamp('2026-09-09T08:00Z'),scope=FLOW_SCOPE)
        self.assertEqual(len(legacy['expiries']),3);self.assertEqual(len(legacy['records']),66)
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

    def test_scope_edges_duplicate_and_timezone(self):
        options=[dict(option=f'TEST{e}{s}{k:08d}',open_interest=10,iv=.25) for e in ['260915','260916','260918','260925','261029','261030'] for s in ['C','P'] for k in [84999,85000,95000,99000,100000,101000,105000,115000,115001]]
        raw=dict(symbol='TEST',data=dict(current_price=100,options=options))
        out=normalize(raw,'TEST','2026-09-09T20:00Z')
        self.assertEqual(out['expiries'],['2026-09-16','2026-09-18','2026-09-25','2026-10-29'])
        self.assertEqual({r['strike'] for r in out['records']},{85,95,99,100,101,105,115})
        self.assertTrue(out['quality']['scope_complete'])
        with self.assertRaisesRegex(ValueError,'timezone'):normalize(raw,'TEST','2026-09-09')
        raw['data']['options'].append(options[0])
        with self.assertRaisesRegex(ValueError,'Duplicate'):normalize(raw,'TEST','2026-09-09T20:00Z')
        raw['data']['current_price']=float('nan')
        with self.assertRaisesRegex(ValueError,'underlying'):normalize(raw,'TEST','2026-09-09T20:00Z')

    def test_maturity_totals_reconcile_and_unmatched_atm_is_missing(self):
        raw=self.raw();raw['records'][0]['expiry']='2026-10-09';raw['records'][1]['impliedVolatility']=None
        p=profile(raw,100,.03)
        self.assertAlmostEqual(sum(r['gex'] or 0 for r in p['maturity']),p['net'],places=6)
        self.assertEqual(sum(r['valid_oi'] for r in p['maturity']),p['valid_oi'])
        self.assertEqual(sum(r['valid_gamma'] for r in p['maturity']),p['valid_gamma'])
        self.assertAlmostEqual(sum(r['oi_pct'] for r in p['maturity']),100)
        raw=self.raw()
        for row in raw['records']:
            if row['side']=='put':row['strike']+=1
        p=profile(raw,100,.03)
        self.assertIsNone(p['em']);self.assertIsNone(p['em_strike'])

    def test_archived_options_keep_original_spot_and_rate_with_new_prices(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);raw=dict(self.raw(),symbol='SPY',underlying_price=100,provider_timestamp='2026-09-09 03:00:00')
            save(base/'options/SPY.json.gz',raw)
            d=Mock();d.bases=[base];d.resource=lambda name:base/name
            d.price.return_value=pd.Series([100.,160.],index=pd.to_datetime(['2026-09-08','2026-10-01']))
            d.mac.return_value=pd.Series([3.,15.],index=pd.to_datetime(['2026-09-08','2026-10-01']))
            # Mock fabricates every attribute; use a plain fixture for cache checks.
            class Fixture:pass
            fixture=Fixture();fixture.bases=d.bases;fixture.resource=d.resource;fixture.price=d.price;fixture.mac=d.mac
            p=packets(fixture)[0]
            self.assertEqual(p['spot'],100);self.assertEqual(p['reference_close'],160)
            self.assertEqual(p['price_date'],'2026-10-01');self.assertEqual(p['rate'],3)
            self.assertEqual(p['retrieved_at'],raw['retrieved_at'])
            self.assertEqual(p['provider_timestamp'],raw['provider_timestamp'])
            self.assertFalse(p['scope_complete'])

class OptionCollectionTests(unittest.TestCase):
    def fixture(self,path):
        class Fixture:
            base=path/'child'
            def resource(self,name):
                child=self.base/name
                return child if child.exists() else path/'parent'/name
        return Fixture()

    def test_automatic_access_defaults_to_no_requests_and_no_redating(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=self.fixture(Path(tmp));old=dict(symbol='SPY',status='ok',retrieved_at='2026-09-09T08:00Z',records=[])
            save(d.resource('options/SPY.json.gz'),old);save(d.resource('flows/options_SPY.json.gz'),old)
            fetch=Mock(side_effect=AssertionError('No network allowed'))
            report=collect(d,fetch=fetch)
            with patch('pipeline.flows_data.US_STOCKS',['SPY']):flow=collect_us_options(d,{'NEW':'2026-09-18T20:00Z'},fetch=fetch)
            fetch.assert_not_called()
            self.assertEqual(report['rows'][0]['status'],'retained_permission_required')
            self.assertEqual(next(r for r in flow['rows'] if r['symbol']=='NEW')['status'],'missing_permission_required')
            self.assertEqual(read(d.resource('options/SPY.json.gz')),old)
            self.assertFalse((d.base/'options/SPY.json.gz').exists())
            self.assertFalse((d.base/'flows/earnings_NEW.json.gz').exists())

    def test_authorized_provider_failure_preserves_old_observation(self):
        with tempfile.TemporaryDirectory() as tmp,patch('pipeline.options_data.time.sleep'),patch('pipeline.flows_data.time.sleep'):
            d=self.fixture(Path(tmp));old=dict(symbol='SPY',status='ok',retrieved_at='2026-09-09T08:00Z',records=[])
            save(d.resource('options/SPY.json.gz'),old);save(d.resource('flows/options_SPY.json.gz'),old)
            fetch=Mock(side_effect=TimeoutError('private provider details must not be logged'))
            report=collect(d,allow_download=True,fetch=fetch)
            with patch('pipeline.flows_data.US_STOCKS',['SPY']):flow=collect_us_options(d,{},allow_download=True,fetch=fetch)
            self.assertEqual(report['rows'][0]['status'],'retained_error');self.assertEqual(flow['rows'][0]['status'],'retained_error')
            self.assertNotIn('private',str(report)+str(flow));self.assertEqual(read(d.resource('flows/options_SPY.json.gz')),old)

    def test_sparse_gamma_sample_can_still_supply_event_straddle(self):
        with tempfile.TemporaryDirectory() as tmp,patch('pipeline.flows_data.time.sleep'),patch('pipeline.flows_data.US_STOCKS',[]):
            d=self.fixture(Path(tmp))
            raw=dict(symbol='TEST',data=dict(current_price=100,options=[dict(option='TEST260918'+side+'00100000',open_interest=20,iv=.25,bid=4,ask=5) for side in ['C','P']]))
            collect_us_options(d,{'TEST':'2026-09-17T20:00:00Z'},allow_download=True,fetch=lambda s:raw)
            event=read(d.base/'flows/earnings_TEST.json.gz')
            self.assertEqual(len(event['records']),2);self.assertEqual(event['expiry'],'2026-09-18')
            self.assertFalse((d.base/'flows/options_TEST.json.gz').exists())

if __name__=='__main__':unittest.main()

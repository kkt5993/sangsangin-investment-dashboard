import tempfile,unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock,patch
from pipeline import fundamental_universe as U
from pipeline.store import write_json
from pipeline.events_data import save,read
from pipeline.company_fundamentals import SourceRefused,fetch_fund

NOW='2026-09-13T00:00:00+00:00'

def financial(symbol,stamp=NOW):
    return dict(symbol=symbol,status='ok',retrieved_at=stamp,info={'financialCurrency':'USD'},errors=[],
        annual_income=dict(index=['NetIncome'],columns=['2025-12-31'],data=[[10]]))


class FundamentalUniverseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name)/'expanded'
        self.parent=root/'20260911T000000Z';self.base=root/'20260913T000000Z'
        self.parent.mkdir(parents=True);self.base.mkdir()
        write_json(self.base/'parent.json',dict(vintage=self.parent.name))
        self.patches=[patch('pipeline.catalog.reference_stocks',return_value=[{'symbol':'A'}]),
            patch('pipeline.strategy_cards.settings',return_value={'fundamental_support':['B']})]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in self.patches:p.stop()
        self.tmp.cleanup()
    def test_latest_membership_inherited_and_raw_csv_not_read_as_json(self):
        write_json(self.parent/'us_largecap.json',dict(members=[{'symbol':'OLD'}]))
        write_json(self.base/'us_largecap.json',dict(members=[{'symbol':'NEW'}]))
        write_json(self.parent/'us100.json',dict(members=[{'symbol':'BRK-B'},{'symbol':'A'}],raw_file='oef.csv'))
        (self.parent/'oef.csv').write_text('Ticker,Name\nBRKB,Berkshire\n')
        result=U.inventory(U.context(self.base))
        self.assertEqual([r['symbol'] for r in result['targets']],['A','B','BRK-B','NEW'])
        self.assertEqual(result['targets'][0]['groups'],['reference_stocks','us100'])
        self.assertEqual(next(s for s in result['sources'] if s['group']=='us100')['vintage'],self.parent.name)
        self.assertTrue(all(len(s['sha256'])==64 for s in result['sources']))
    def test_reuse_parent_collect_only_missing_and_resume_without_calendar(self):
        save(self.parent/'fundamentals/A.json.gz',financial('A'))
        fetch=Mock(side_effect=lambda s,p:financial(s));dates=Mock(side_effect=AssertionError('Calendar not requested'))
        first=U.collect(self.base,fund_fetch=fetch,calendar_fetch=dates,now=NOW,pause=lambda _:None)
        self.assertEqual(first['fetches'],1);self.assertEqual(fetch.call_args[0][0],'B')
        second=U.collect(self.base,fund_fetch=fetch,calendar_fetch=dates,now=NOW,pause=lambda _:None)
        self.assertEqual(second['fetches'],0);self.assertEqual(fetch.call_count,1);dates.assert_not_called()
        self.assertFalse((self.base/'company_financial/collection.json.gz').exists())
        self.assertEqual(read(self.base/U.MANIFEST)['expected'],2)
    def test_source_refusal_preserves_old_stops_batch_and_global_backoff(self):
        old=financial('A','2026-09-01T00:00:00+00:00');save(self.parent/'fundamentals/A.json.gz',old)
        fail=Mock(side_effect=SourceRefused('rate limited'))
        first=U.collect(self.base,fund_fetch=fail,now=NOW,pause=lambda _:None)
        self.assertEqual([r['status'] for r in first['rows']],['retained','deferred'])
        self.assertNotIn('attempted_at',first['rows'][1]);self.assertEqual(first['fetches'],1)
        self.assertFalse((self.base/'fundamentals/A.json.gz').exists())
        second=U.collect(self.base,fund_fetch=fail,now=NOW,pause=lambda _:None)
        self.assertEqual(second['status'],'backoff');self.assertEqual(second['fetches'],0);self.assertEqual(fail.call_count,1)
        good=Mock(side_effect=lambda s,p:financial(s,'2026-09-13T01:00:00+00:00'))
        third=U.collect(self.base,fund_fetch=good,now='2026-09-13T01:00:00+00:00',pause=lambda _:None)
        self.assertEqual(third['status'],'ok');self.assertEqual(good.call_count,2)
    def test_missing_currency_or_empty_provider_response_not_saved_as_success(self):
        bad=financial('A');bad['info']={}
        result=U.collect(self.base,limit=1,fund_fetch=lambda *a:bad,now=NOW,pause=lambda _:None)
        self.assertEqual(result['rows'][0]['status'],'missing')
        self.assertFalse((self.base/'fundamentals/A.json.gz').exists())
        self.assertEqual(read(self.base/U.MANIFEST)['selected'],1)
    def test_default_acquire_delegates_and_explicit_symbol_path_stays_separate(self):
        from pipeline.acquire import collect_fundamentals
        with patch.object(U,'collect',return_value={'status':'ok'}) as run:
            self.assertEqual(collect_fundamentals(self.base,limit=2),{'status':'ok'})
            run.assert_called_once_with(self.base,limit=2)
    def test_explicit_selection_is_dated_universe_subset(self):
        fetch=Mock(side_effect=lambda s,p:financial(s))
        result=U.collect(self.base,symbols=['B','B'],fund_fetch=fetch,now=NOW,pause=lambda _:None)
        self.assertEqual(result['expected'],1);self.assertEqual(fetch.call_args[0][0],'B')
        self.assertEqual(read(self.base/U.MANIFEST)['selected_symbols'],['B'])
        with self.assertRaises(ValueError):U.collect(self.base,symbols=['UNKNOWN'])
    def test_yfinance_rate_limit_survives_raw_collector_error_wrapper(self):
        def refused(folder,**kwargs):
            save(folder/'fundamentals/A.json.gz',dict(symbol='A',status='error',error_type='YFRateLimitError'))
        with patch('pipeline.acquire.collect_fundamentals',side_effect=refused):
            with self.assertRaises(SourceRefused):fetch_fund('A',self.base/'attempt')
    def test_partial_cache_stays_partial_when_reused(self):
        raw=financial('A');raw['errors']=['earnings_estimate:RuntimeError']
        save(self.parent/'fundamentals/A.json.gz',raw)
        fetch=Mock(side_effect=AssertionError('Fresh statement should be reused'))
        report=U.collect(self.base,symbols=['A'],fund_fetch=fetch,now=NOW,pause=lambda _:None)
        fetch.assert_not_called();self.assertEqual(report['status'],'partial')
        self.assertTrue(report['rows'][0]['partial'])
    def test_long_batch_uses_actual_time_for_each_company(self):
        later='2026-09-13T02:00:00+00:00'
        fetch=Mock(side_effect=lambda s,p:financial(s,NOW if s=='A' else later))
        with patch('pipeline.company_fundamentals.datetime') as clock:
            clock.now.side_effect=[datetime.fromisoformat(NOW),datetime.fromisoformat(NOW),datetime.fromisoformat(later)]
            report=U.collect(self.base,fund_fetch=fetch,pause=lambda _:None)
        self.assertEqual(report['status'],'ok')
        self.assertEqual(report['rows'][1]['attempted_at'],later)


if __name__=='__main__':unittest.main()

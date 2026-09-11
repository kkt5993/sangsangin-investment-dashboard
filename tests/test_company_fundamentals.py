import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from pipeline.company_fundamentals import collect,calendars,entity_events,usable_calendar
from pipeline.events_data import save

NOW='2026-09-11T06:00:00+00:00'


def financial(symbol,date=NOW):
    return dict(symbol=symbol,status='ok',retrieved_at=date,info={'financialCurrency':'USD'},errors=[],
                annual_income={'index':['NetIncome','TotalRevenue'],'columns':['2025-12-31'],'data':[[0],[200]]})


def calendar(symbol,date=NOW,event='2026-11-05T21:00:00+00:00'):
    return dict(symbol=symbol,retrieved_at=date,earnings_dates={'index':[event],'columns':['EPS Estimate'],'data':[[1.2]]})


class CompanyFundamentalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
        self.d=SimpleNamespace(base=self.base,bases=[self.base],fund={},resource=lambda name:self.base/name)
    def tearDown(self):self.tmp.cleanup()
    def test_reuse_existing_fund_and_calendar_without_fetch(self):
        self.d.fund['A']=financial('A');save(self.base/'pead_events/A.json.gz',calendar('A'))
        fail=Mock(side_effect=AssertionError('network should not be called'))
        result=collect(self.d,[{'symbol':'A'}],fail,fail,pause=lambda _:None,now=NOW)
        self.assertEqual(result['fetches'],0);self.assertTrue(all(r['status']=='reused' for r in result['rows']));fail.assert_not_called()
    def test_collect_missing_then_reuse_without_duplicate(self):
        fund=Mock(return_value=financial('A'));dates=Mock(return_value=calendar('A'))
        first=collect(self.d,[{'symbol':'A'}],fund,dates,pause=lambda _:None,now=NOW)
        self.assertEqual(first['fetches'],2);self.assertTrue((self.base/'fundamentals/A.json.gz').exists())
        second=collect(self.d,[{'symbol':'A'}],fund,dates,pause=lambda _:None,now=NOW)
        self.assertEqual(second['fetches'],0);self.assertEqual(fund.call_count,1);self.assertEqual(dates.call_count,1)
    def test_failed_refresh_preserves_old_and_backs_off(self):
        old=financial('000001.KS','2026-09-01T00:00:00+00:00');self.d.fund['000001.KS']=old
        fail=Mock(side_effect=RuntimeError('offline'))
        first=collect(self.d,[{'symbol':'000001.KS'}],fail,pause=lambda _:None,now=NOW)
        self.assertEqual(first['rows'][0]['status'],'retained');self.assertEqual(self.d.fund['000001.KS'],old)
        second=collect(self.d,[{'symbol':'000001.KS'}],fail,pause=lambda _:None,now=NOW)
        self.assertEqual(second['rows'][0]['status'],'backoff');self.assertEqual(fail.call_count,1)
        self.assertFalse((self.base/'fundamentals/000001.KS.json.gz').exists())
    def test_partial_refresh_does_not_replace_complete_statements(self):
        self.d.fund['000001.KS']=financial('000001.KS','2026-09-01T00:00:00+00:00')
        raw=financial('000001.KS');raw['errors']=['earnings_estimate:RuntimeError']
        result=collect(self.d,[{'symbol':'000001.KS'}],lambda *args:raw,pause=lambda _:None,now=NOW)
        self.assertEqual(result['rows'][0]['status'],'retained')
        self.assertEqual(self.d.fund['000001.KS']['retrieved_at'],'2026-09-01T00:00:00+00:00')
    def test_calendar_merge_keeps_unrelated_event_fields_and_latest_date(self):
        save(self.base/'events/A.json.gz',calendar('A','2026-09-08T00:00:00+00:00'))
        save(self.base/'company_events/A.json.gz',calendar('A'))
        old={'A':{**calendar('A','2026-09-08T00:00:00+00:00'),'eps_revisions':{'keep':True}}}
        merged=entity_events(self.d,old)
        self.assertEqual(merged['A']['retrieved_at'],NOW);self.assertEqual(merged['A']['eps_revisions'],{'keep':True})
        self.assertEqual(old['A']['retrieved_at'],'2026-09-08T00:00:00+00:00')
        self.assertIn('https://',merged['A']['calendar_source'])
    def test_unknown_calendar_timezone_rejected(self):
        self.assertFalse(usable_calendar(calendar('A',event='2026-11-05')))
        self.assertFalse(usable_calendar({'earnings_dates':None}))


if __name__=='__main__':unittest.main()

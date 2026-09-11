import copy,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pipeline import guru_identifiers as g
from pipeline.guru_data import save,read

NOW=datetime(2026,9,11,tzinfo=timezone.utc)
def result(ticker='GOOGL',figi='BBG009S39JX6',kind='Common Stock'):
    return dict(data=[dict(ticker=ticker,figi=figi,exchCode='US',name='ALPHABET INC-CL A',securityType=kind,marketSector='Equity',shareClassFIGI='BBG009S39JY5')])
def position(cusip='02079K305',option=None):return dict(cusip=cusip,quantity_type='SH',option=option)
ENTITIES=[dict(id='stock:GOOGL',symbol='GOOGL',market='US',name='Alphabet A'),dict(id='stock:GOOG',symbol='GOOG',market='US',name='Alphabet C')]

class IdentifierTests(unittest.TestCase):
    def test_exact_class_and_option_underlying(self):
        mappings={'02079K305':g.normalize('02079K305',result(),NOW),'02079K107':g.normalize('02079K107',result('GOOG','BBG009S3NB30'),NOW)}
        for cusip,expected in [('02079K305','GOOGL'),('02079K107','GOOG')]:
            for option in [None,'PUT','CALL']:
                e,reason=g.resolve(position(cusip,option),mappings,ENTITIES,NOW);self.assertIsNone(reason);self.assertEqual(e['symbol'],expected)
    def test_ambiguous_fund_and_missing_are_not_companies(self):
        raw=result();raw['data']+=result('GOOG','BBG009S3NB30')['data']
        for raw in [raw,result(kind='ETP'),dict(warning='No identifier found.')]:
            r=g.normalize('02079K305',raw,NOW);e,reason=g.resolve(position(),{'02079K305':r},ENTITIES,NOW);self.assertIsNone(e);self.assertTrue(reason)
    def test_stale_future_or_outside_universe(self):
        r=g.normalize('02079K305',result(),NOW)
        for now,entities in [(NOW+timedelta(days=31),ENTITIES),(NOW-timedelta(seconds=1),ENTITIES),(NOW,[])]:
            self.assertIsNone(g.resolve(position(),{'02079K305':r},entities,now)[0])
    def test_duplicate_or_wrong_market_rejected(self):
        raw=result();raw['data'].append(dict(raw['data'][0],ticker='GOOG'))
        for raw in [raw,dict(error='temporary failure'),dict(data=[]),dict(data=[dict(result()['data'][0],exchCode='LN')])]:
            with self.assertRaises(ValueError):g.normalize('02079K305',raw,NOW)
    def test_class_separator_only_not_fuzzy_name(self):
        r=g.normalize('084670702',result('BRK/B'),NOW);entities=[dict(id='stock:BRK-B',symbol='BRK-B',market='US',name='Berkshire')]
        e,_=g.resolve(position('084670702'),{'084670702':r},entities,NOW);self.assertEqual(e['id'],'stock:BRK-B')
        r['results'][0]['ticker']='BRKB';self.assertIsNone(g.resolve(position('084670702'),{'084670702':r},entities,NOW)[0])
    def test_requests_are_batched_cached_and_keep_failure_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);d=SimpleNamespace(base=base,as_of='2026-09-10',resource=lambda name:base/name);calls=[];pauses=[]
            save(base/g.REPORTS,dict(filings=[]));cusips=[f'{i:09}' for i in range(1,8)]
            selected=dict(entries=[position(c) for c in cusips]);session=SimpleNamespace(post=lambda *a,**k:(calls.append(k['json']) or SimpleNamespace(status_code=200,json=lambda:[result('TEST') for _ in k['json']])))
            with patch.object(g,'settings',return_value=[dict(cik='123')]),patch.object(g,'latest',return_value=selected):
                r=g.collect(d,session=session,now=NOW,pause=pauses.append);self.assertEqual([len(c) for c in calls],[5,2]);self.assertEqual(r['jobs'],7);self.assertEqual(pauses,[3,3]);self.assertEqual(len(read(base/g.FILE)['mappings']),7)
                self.assertEqual(g.collect(d,session=session,now=NOW+timedelta(days=1),pause=pauses.append)['requests'],0)
                failing=SimpleNamespace(post=lambda *a,**k:SimpleNamespace(status_code=429));r=g.collect(d,session=failing,now=NOW+timedelta(days=31),pause=lambda _:None);self.assertEqual(r['status'],'access_refused');self.assertEqual(r['requests'],1);self.assertEqual(len(read(base/g.FILE)['mappings']),7)
    def test_job_error_does_not_destroy_successful_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);d=SimpleNamespace(base=base,as_of='2026-09-10',resource=lambda name:base/name);old=g.normalize('02079K305',result(),NOW-timedelta(days=40));save(base/g.FILE,dict(mappings={'02079K305':old}));save(base/g.REPORTS,dict(filings=[]))
            session=SimpleNamespace(post=lambda *a,**k:SimpleNamespace(status_code=200,json=lambda:[{'error':'source unavailable'}]))
            with patch.object(g,'settings',return_value=[dict(cik='123')]),patch.object(g,'latest',return_value=dict(entries=[position()])):r=g.collect(d,session=session,now=NOW,pause=lambda _:None)
            self.assertEqual(r['status'],'error');self.assertEqual(read(base/g.FILE)['mappings']['02079K305'],old)

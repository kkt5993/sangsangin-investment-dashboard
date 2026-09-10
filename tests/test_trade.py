import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import requests
from pipeline import trade_data as t
from pipeline import trade_views as v
from pipeline.events_data import read, save


def observation(partner=410, value='100.25'):
    return dict(typeCode='C', freqCode='A', reporterCode=842, refYear=2024, period='2024',
        flowCode='X', cmdCode='TOTAL', partnerCode=partner, partner2Code=0, customsCode='C00',
        motCode=0, classificationSearchCode='HS', aggrLevel=0, primaryValue=value,
        isReported=False, isAggregate=True, classificationCode='H6')


def response(rows=None):
    rows = rows if rows is not None else [observation(0, '1000'), observation()]
    return dict(count=len(rows), data=rows, error='')


class TradeTests(unittest.TestCase):
    def setUp(self):
        # Fixture writes must not traverse the user's live multi-vintage cache.
        budget=patch('pipeline.events_data.budget');budget.start();self.addCleanup(budget.stop)

    def test_download_cap_and_decimal_parse(self):
        class Reply:
            def __init__(self,body):self.body=body
            def __enter__(self):return self
            def __exit__(self,*_):return False
            def raise_for_status(self):pass
            def iter_content(self,_):yield self.body
        class Session:
            def __init__(self,body):self.body=body
            def get(self,*args,**kwargs):return Reply(self.body)
        raw=b'{"value":1234567890123.12345}'
        packet,size,sha=t.download(Session(raw),t.API)
        self.assertEqual(packet['value'],Decimal('1234567890123.12345'));self.assertEqual(size,len(raw));self.assertEqual(len(sha),64)
        with patch.object(t,'MAX_BYTES',10),self.assertRaises(ValueError):t.download(Session(raw),t.API)

    def test_future_or_missing_cache_clock_is_not_fresh(self):
        now=datetime.now(timezone.utc)
        self.assertFalse(t.recent({},30,now))
        self.assertFalse(t.recent(dict(checked_at=(now+timedelta(days=1)).isoformat()),30,now))
        self.assertFalse(t.recent(dict(checked_at=now.replace(tzinfo=None).isoformat()),30,now))

    def test_decimal_and_world_denominator(self):
        rows=t.normalized(response([observation(0,'3000000000000.125'),observation(value=Decimal('1234567890123.12345'))]),842,2024)
        self.assertEqual(rows[1]['usd'],'1234567890123.12345')
        self.assertFalse(rows[1]['reported']);self.assertTrue(rows[1]['aggregate'])
        self.assertEqual(t.query(842,2024)['flowCode'],'X')
        self.assertNotIn('subscription-key',t.query(842,2024))

    def test_all_scope_fields_and_truncation(self):
        for key,value in [('freqCode','M'),('refYear',2025),('period','2025'),('reporterCode',410),('cmdCode','85'),('flowCode','M'),('partner2Code',1),('customsCode','C01'),('motCode',1),('aggrLevel',2)]:
            p=response();p['data'][1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):t.normalized(p,842,2024)
        for p in [dict(count=3,data=response()['data']),response([observation()]*500),dict(error='rate limit',data=[],count=0)]:
            with self.assertRaises(ValueError):t.normalized(p,842,2024)

    def test_missing_zero_and_invalid_values_are_distinct(self):
        self.assertEqual(t.normalized(response([]),842,2024),[])
        self.assertEqual(t.normalized(response([observation(0,'1000'),observation(value=0)]),842,2024)[1]['usd'],'0')
        for value in [None, True, '-1', 'NaN', 'Infinity', '1001']:
            with self.subTest(value=value),self.assertRaises(ValueError):t.normalized(response([observation(0,'1000'),observation(value=value)]),842,2024)
        with self.assertRaises(ValueError):t.normalized(response([observation()]),842,2024)
        p=response();p['data'][1]['isReported']=None
        with self.assertRaises(ValueError):t.normalized(p,842,2024)

    def test_duplicate_conflicts(self):
        with self.assertRaises(ValueError):t.normalized(response([observation(0,'1000'),observation(),observation(value='99')]),842,2024)
        self.assertEqual(len(t.normalized(response([observation(0,'1000'),observation(),observation()]),842,2024)),2)

    def test_area_codes_are_customs_areas(self):
        codes={a['id']:a['code'] for a in t.AREAS}
        self.assertEqual({k:codes[k] for k in ['CH','NO','US','FR','IN','S19','GB']},dict(CH=757,NO=579,US=842,FR=251,IN=699,S19=490,GB=826))
        packets={}
        for kind,prefix in [('reporters','reporter'),('partners','Partner')]:
            packets[kind]=dict(results=[dict(id=a['code'],**{prefix+'Code':a['code'],prefix+'Desc':a['name'],prefix+'CodeIsoAlpha2':a['id'],prefix+'CodeIsoAlpha3':'S19' if a['id']=='S19' else '', 'isGroup':a['id']=='S19'}) for a in t.AREAS])
        self.assertEqual(len(t.verify_references(packets)),45)
        packets['reporters']['results'][0]['reporterCodeIsoAlpha2']='WRONG'
        with self.assertRaises(ValueError):t.verify_references(packets)

    def fixture(self,root):
        parent=root/'parent';base=root/'child';parent.mkdir();base.mkdir()
        def resource(name):return base/name if (base/name).exists() else parent/name
        d=SimpleNamespace(base=base,as_of='2026-09-08',resource=resource)
        now=datetime.now(timezone.utc).isoformat();old=(datetime.now(timezone.utc)-timedelta(days=40)).isoformat()
        save(parent/'trade/references.json.gz',dict(checked_at=now,packets={}))
        packet=dict(reporter=842,year=2024,rows=t.normalized(response(),842,2024),checked_at=old,retrieved_at=old,official_name='USA',coverage='USA, Puerto Rico and US Virgin Islands')
        save(parent/'trade/2024/842.json.gz',packet)
        return d,parent,packet

    def test_monthly_revalidation_avoids_unchanged_raw_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            d,parent,previous=self.fixture(Path(folder))
            with patch.object(t,'AREAS',[t.AREAS[0]]),patch.object(t,'verify_references',return_value={842:{}}),patch.object(t,'download',return_value=(response(),1000,'sha')) as net:
                m=t.collect(d,session=object(),pause=lambda _:None)
                self.assertEqual(net.call_count,1);self.assertEqual(m['areas'][0]['retrieved_at'],previous['retrieved_at'])
                self.assertFalse((d.base/'trade/2024/842.json.gz').exists())
                m=t.collect(d,session=object(),pause=lambda _:None)
                self.assertEqual(net.call_count,1);self.assertEqual(m['requests'],0)

    def test_failed_or_empty_recheck_retains_observation_and_clock(self):
        for outcome in [RuntimeError('fixture'),(response([]),12,'sha')]:
            with tempfile.TemporaryDirectory() as folder:
                d,parent,previous=self.fixture(Path(folder))
                with patch.object(t,'AREAS',[t.AREAS[0]]),patch.object(t,'verify_references',return_value={842:{}}),patch.object(t,'download',side_effect=outcome if isinstance(outcome,Exception) else None,return_value=outcome):
                    m=t.collect(d,session=object(),pause=lambda _:None)
                    self.assertEqual(m['areas'][0]['state'],'error');self.assertEqual(m['areas'][0]['checked_at'],previous['checked_at'])
                    self.assertEqual(m['areas'][0]['observations'],2)
                    self.assertEqual(read(d.resource('trade/2024/842.json.gz')),previous)

    def test_rate_limit_stops_run(self):
        with tempfile.TemporaryDirectory() as folder:
            d,parent,previous=self.fixture(Path(folder));r=requests.Response();r.status_code=429
            with patch.object(t,'AREAS',t.AREAS[:2]),patch.object(t,'verify_references',return_value={842:{},124:{}}),patch.object(t,'download',side_effect=requests.HTTPError(response=r)) as net:
                m=t.collect(d,session=object(),pause=lambda _:None)
                self.assertEqual(net.call_count,1);self.assertEqual([a['state'] for a in m['areas']],['error','deferred'])

    def test_current_year_never_mixed_with_previous_year(self):
        with tempfile.TemporaryDirectory() as folder:
            d,parent,previous=self.fixture(Path(folder))
            d.as_of='2027-01-02'
            s=v.build(d);self.assertEqual(s['year'],2025)
            self.assertTrue(all(a['world_usd'] is None for a in s['areas']))

    def test_view_direction_only_keeps_configured_partners(self):
        with tempfile.TemporaryDirectory() as folder:
            d,parent,previous=self.fixture(Path(folder));previous['rows'].append(dict(partner=999,usd='17',reported=True,aggregate=False,classification='H6'))
            save(parent/'trade/2024/842.json.gz',previous)
            s=v.build(d);us=next(a for a in s['areas'] if a['id']=='US');kr=next(a for a in s['areas'] if a['id']=='KR')
            self.assertEqual(us['exports'],[['KR','100.25',False,True]])
            self.assertEqual(us['world_usd'],'1000');self.assertEqual(kr['exports'],[])
            self.assertIsNone(kr['world_usd'])


if __name__=='__main__':unittest.main()

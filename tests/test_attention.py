import copy, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import requests
from pipeline.attention_data import normalize, collect, save, read, FILE
from pipeline.attention_views import metrics, views


class AttentionTests(unittest.TestCase):
    now = datetime(2026, 9, 11, 1, tzinfo=timezone.utc)
    spec = dict(symbol='NVDA', title='Nvidia', pageid=39120, wikidata='Q182477')

    def raw(self, start='2026-08-27', count=14, split=True):
        dt = datetime.fromisoformat(start)
        return dict(items=[dict(project='en.wikipedia', article='Nvidia', access='all-access', agent='user', granularity='daily', timestamp=(dt+timedelta(days=i)).strftime('%Y%m%d00'), views=10 if i<7 or not split else 14) for i in range(count)])

    def points(self):
        return normalize(self.raw(), 'en.wikipedia.org', 'Nvidia', '2026-08-27', '2026-09-09')

    def test_population_dates_duplicate_and_values(self):
        for field,value in [('article','NVIDIA X'),('agent','all-agents'),('project','ko.wikipedia'),('views',True),('views',-1),('timestamp','2026091012')]:
            raw=self.raw();raw['items'][0][field]=value
            with self.assertRaises(ValueError):normalize(raw,'en.wikipedia.org','Nvidia','2026-08-27','2026-09-09')
        raw=self.raw();raw['items'].append(copy.deepcopy(raw['items'][0]))
        with self.assertRaises(ValueError):normalize(raw,'en.wikipedia.org','Nvidia','2026-08-27','2026-09-09')

    def test_equal_windows_zero_missing_future_and_threshold(self):
        p=self.points();m=metrics(p,'2026-09-09');self.assertEqual((m['recent'],m['previous'],m['change']),(98,70,40))
        self.assertIsNone(metrics(p[:3]+p[4:],'2026-09-09')['change'])
        self.assertFalse(metrics(p,'2026-09-08')['complete'])
        for r in p[:7]:r['views']=0
        self.assertIsNone(metrics(p,'2026-09-09')['change'])

    def packet(self):
        return dict(project='en.wikipedia.org',pages={'NVDA':dict(**self.spec,project='en.wikipedia.org',points=self.points(),checked_at=self.now.isoformat(),retrieved_at=self.now.isoformat(),requested_end='2026-09-09',source_url='https://wikimedia.org/test',error=None)})

    def test_cache_revisions_gap_and_failure_preserve(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);d=SimpleNamespace(as_of='2026-09-10',base=base,resource=lambda n:base/n);p=self.packet();save(base/FILE,p)
            session=SimpleNamespace(get=lambda *a,**k: self.fail('cached call'))
            with patch('pipeline.attention_data.settings',return_value=dict(project='en.wikipedia.org',pages=[self.spec])):
                self.assertEqual(collect(d,session,self.now,pause=lambda _:None)['requests'],0)
                response=SimpleNamespace(raise_for_status=lambda:None,json=lambda:self.raw('2026-09-03',7,False))
                session=SimpleNamespace(get=lambda *a,**k:response)
                report=collect(d,session,self.now+timedelta(hours=25),pause=lambda _:None)
                self.assertEqual(report['requests'],1)
                got=read(base/FILE)['pages']['NVDA'];self.assertEqual(got['points'][-1]['views'],10);self.assertEqual(len(got['points']),14)
                # Missing returned Sep 10 stays absent; the last observed day remains Sep 09.
                old=copy.deepcopy(got)
                def denied(*a,**k):raise requests.HTTPError(response=SimpleNamespace(status_code=429))
                session=SimpleNamespace(get=denied)
                result=collect(d,session,self.now+timedelta(hours=50),pause=lambda _:None);self.assertEqual(result['status'],'access_refused')
                got=read(base/FILE)['pages']['NVDA'];self.assertEqual(got['points'],old['points']);self.assertEqual(got['retrieved_at'],old['retrieved_at'])
                self.assertEqual(collect(d,session,self.now+timedelta(hours=50,minutes=10),pause=lambda _:None)['status'],'backoff')

    def test_view_identity_staleness_and_entity_reset(self):
        cfg=dict(project='en.wikipedia.org',pages=[self.spec]);packet=self.packet()
        d=SimpleNamespace(as_of='2026-09-10',resource=lambda n:Path(__file__))
        dragon=dict(sections=[dict(type='entities',entities=[dict(id='stock:NVDA',symbol='NVDA',attention={'old':1})])])
        with patch('pipeline.attention_views.settings',return_value=cfg),patch('pipeline.attention_views.read',return_value=packet):
            views(d,dragon,self.now);item=dragon['sections'][-1]['items'][0];self.assertTrue(item['spike']);self.assertEqual(item['entity'],'stock:NVDA')
            views(d,dragon,self.now+timedelta(days=4));self.assertFalse(dragon['sections'][-1]['items'][0]['spike'])
            for point in packet['pages']['NVDA']['points'][:7]:point['views']=0
            views(d,dragon,self.now);self.assertFalse(dragon['sections'][-1]['items'][0]['fresh'])
            packet['pages']['NVDA']['title']='different';views(d,dragon,self.now);self.assertEqual(dragon['sections'][-1]['items'][0]['points'],[])


if __name__=='__main__':unittest.main()

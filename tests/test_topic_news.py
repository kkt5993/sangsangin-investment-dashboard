import json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import requests
from pipeline import topic_news as T
from pipeline.guru_data import save,read

NOW=datetime(2026,9,11,6,tzinfo=timezone.utc)
SPEC=dict(id='fed',name='연준',kind='policy',query='"Federal Reserve" sourcelang:english',title_groups=[['Federal Reserve','FOMC']])
ARTICLE=dict(url='https://example.org/news?utm_source=test',title='Federal Reserve update',seendate='20260909T093000Z',domain='example.org',language='English')


class TopicNewsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
        self.d=SimpleNamespace(base=self.base,as_of='2026-09-10',resource=lambda name:self.base/name)
    def tearDown(self):self.tmp.cleanup()
    def session(self,articles=None):
        response=Mock(content=json.dumps({'articles':articles if articles is not None else [ARTICLE]}).encode())
        response.raise_for_status.return_value=None;return Mock(get=Mock(return_value=response))
    def test_normalize_dates_dedup_and_unsafe_url(self):
        rows,total,excluded=T.normalize(json.dumps({'articles':[ARTICLE,dict(ARTICLE,url='https://example.org/news'),dict(ARTICLE,url='javascript:alert(1)'),dict(ARTICLE,seendate='bad')]}))
        self.assertEqual((len(rows),total,excluded),(1,4,2));self.assertEqual(rows[0]['time'],'2026-09-09T09:30:00+00:00')
        self.assertEqual(rows[0]['time_basis'],'GDELT 색인 관측')
        with self.assertRaises(ValueError):T.normalize('{}')
    @patch.object(T,'settings',return_value=[SPEC,dict(SPEC,id='second')])
    def test_http_server_error_preserves_cache_and_stops_batch(self,_):
        T.collect(self.d,self.session(),NOW,lambda _:None)
        before=read(self.base/T.FILE)['feeds']['fed']
        later=NOW.replace(day=12)
        response=requests.Response();response.status_code=503
        response._content=b'{"articles":[]}'
        session=Mock(get=Mock(return_value=response))
        report=T.collect(self.d,session,later,lambda _:None)
        after=read(self.base/T.FILE)['feeds']['fed']
        self.assertEqual(report['status'],'error');self.assertEqual(session.get.call_count,1)
        self.assertEqual(report['errors'][0]['http_status'],503)
        self.assertEqual(after['items'],before['items'])
        self.assertEqual(after['retrieved_at'],before['retrieved_at'])
    @patch.object(T,'settings',return_value=[SPEC,dict(SPEC,id='second')])
    def test_plain_text_limit_response_backs_off(self,_):
        response=requests.Response();response.status_code=200
        response._content=b'Please limit requests to one every 5 seconds.'
        session=Mock(get=Mock(return_value=response))
        report=T.collect(self.d,session,NOW,lambda _:None)
        self.assertEqual(report['status'],'access_refused')
        self.assertEqual(session.get.call_count,1)
        self.assertEqual(T.collect(self.d,session,NOW,lambda _:None)['status'],'backoff')
    @patch.object(T,'settings',return_value=[SPEC])
    def test_article_mentioning_limits_is_not_rate_limit(self,_):
        session=self.session([dict(ARTICLE,title='Federal Reserve may limit requests')])
        report=T.collect(self.d,session,NOW,lambda _:None)
        self.assertEqual(report['status'],'ok')
        self.assertEqual(len(read(self.base/T.FILE)['feeds']['fed']['items']),1)
    @patch.object(T,'settings',return_value=[SPEC])
    def test_collect_reuse_and_explicit_empty_result(self,_):
        session=self.session([])
        a=T.collect(self.d,session,NOW,lambda _:None);b=T.collect(self.d,session,NOW,lambda _:None)
        self.assertEqual(a['requests'],1);self.assertEqual(b['requests'],0)
        obj={'sections':[]};T.views(self.d,obj,NOW);r=obj['sections'][0]['items'][0]
        self.assertTrue(r['available']);self.assertTrue(r['data_available']);self.assertEqual(r['sets']['gdelt']['count'],0)
    @patch.object(T,'settings',return_value=[SPEC,dict(SPEC,id='second'),dict(SPEC,id='third')])
    def test_rate_limit_stops_batch_and_backs_off(self,_):
        response=Mock(status_code=429);session=Mock();session.get.side_effect=requests.HTTPError(response=response)
        a=T.collect(self.d,session,NOW,lambda _:None);b=T.collect(self.d,session,NOW,lambda _:None)
        self.assertEqual(a['status'],'access_refused');self.assertEqual(session.get.call_count,1);self.assertEqual(b['status'],'backoff')
        self.assertEqual(b['requests'],0)
        packet=read(self.base/T.FILE)
        self.assertEqual(packet['feeds']['second']['error'],'collection_aborted')
        self.assertEqual(packet['feeds']['third']['error'],'collection_aborted')
    @patch.object(T,'settings',return_value=[SPEC,dict(SPEC,id='second')])
    def test_timeout_stops_batch(self,_):
        session=Mock();session.get.side_effect=requests.ReadTimeout()
        a=T.collect(self.d,session,NOW,lambda _:None)
        self.assertEqual(a['status'],'error');self.assertEqual(session.get.call_count,1)
        skipped=read(self.base/T.FILE)['feeds']['second']
        self.assertEqual(skipped['error'],'collection_aborted')
        self.assertEqual(skipped['abort_reason'],'ReadTimeout')
        self.assertNotIn('checked_at',skipped)
    def test_batch_abort_keeps_completed_query_and_actual_attempt_dates(self):
        second=dict(SPEC,id='second');third=dict(SPEC,id='third')
        with patch.object(T,'settings',return_value=[second,third]):
            T.collect(self.d,self.session(),NOW,lambda _:None)
        before=read(self.base/T.FILE)['feeds'];changed=dict(third,query='new query')
        session=Mock();session.get.side_effect=requests.HTTPError(response=Mock(status_code=429))
        later=NOW.replace(hour=7)
        with patch.object(T,'settings',return_value=[SPEC,second,changed]):
            T.collect(self.d,session,later,lambda _:None)
            obj={'sections':[]};T.views(self.d,obj,later)
        after=read(self.base/T.FILE)['feeds']
        self.assertEqual(after['second'],before['second'])
        self.assertEqual(after['third']['checked_at'],NOW.isoformat())
        self.assertEqual(after['third']['deferred_at'],later.isoformat())
        self.assertEqual(after['third']['abort_http_status'],429)
        self.assertEqual(after['third']['items'],before['third']['items'])
        self.assertFalse(obj['sections'][0]['items'][2]['data_available'])
        self.assertEqual(obj['sections'][0]['items'][2]['sets']['gdelt']['items'],[])
    @patch.object(T,'settings',return_value=[SPEC,dict(SPEC,id='second'),dict(SPEC,id='third')])
    def test_resume_requests_only_unfinished_queries(self,_):
        session=self.session();success=session.get.return_value
        session.get.side_effect=[success,requests.HTTPError(response=Mock(status_code=429))]
        report=T.collect(self.d,session,NOW,lambda _:None)
        self.assertEqual(report['requests'],2)
        blocked=self.session()
        self.assertEqual(T.collect(self.d,blocked,NOW.replace(minute=59),lambda _:None)['status'],'backoff')
        blocked.get.assert_not_called()
        resumed=self.session()
        report=T.collect(self.d,resumed,NOW.replace(hour=7),lambda _:None)
        self.assertEqual(report['status'],'ok');self.assertEqual(report['requests'],2)
        feeds=read(self.base/T.FILE)['feeds']
        self.assertEqual(feeds['fed']['retrieved_at'],NOW.isoformat())
        self.assertTrue(all(not f.get('error') and not f.get('deferred_at') for f in feeds.values()))
    def test_failed_changed_query_does_not_relabel_old_articles(self):
        with patch.object(T,'settings',return_value=[SPEC]):T.collect(self.d,self.session(),NOW,lambda _:None)
        changed=dict(SPEC,query='different query sourcelang:english');session=Mock();session.get.side_effect=requests.HTTPError(response=Mock(status_code=503))
        with patch.object(T,'settings',return_value=[changed]):
            T.collect(self.d,session,NOW,lambda _:None);obj={'sections':[]};T.views(self.d,obj,NOW)
        r=obj['sections'][0]['items'][0];self.assertFalse(r['data_available']);self.assertEqual(r['sets']['gdelt']['items'],[])
        saved=read(self.base/T.FILE)['feeds']['fed'];self.assertEqual(saved['data_query'],SPEC['query']);self.assertEqual(len(saved['items']),1)
    def test_title_match_requires_groups_and_word_boundaries(self):
        spec=dict(title_groups=[['China','Chinese'],['trade','semiconductor']])
        self.assertEqual(T.matched('Chinese trade rises',spec),['Chinese','trade'])
        self.assertEqual(T.matched('Chinatown trade rises',spec),[])
        self.assertEqual(T.matched('China weather',spec),[])
        self.assertEqual(T.matched('Federal Reserve news',SPEC),['Federal Reserve'])
    @patch.object(T,'settings',return_value=[SPEC])
    def test_local_dates_and_missing_search_are_not_zero_or_summed(self,_):
        save(self.base/'news.json.gz',dict(retrieved_at=NOW.isoformat(),items=[dict(url='https://example.org/a',title='FOMC news',published_at='2026-09-09T00:00:00+00:00',source='Fed'),dict(url='https://example.org/b',title='FOMC tomorrow',published_at='2026-09-11T00:00:00+00:00',source='Fed')]))
        obj={'sections':[]};T.views(self.d,obj,NOW);r=obj['sections'][0]['items'][0]
        self.assertEqual(r['sets']['local']['count'],1);self.assertEqual(r['sets']['local']['items'][0]['time_basis'],'RSS 발행')
        self.assertFalse(r['data_available']);self.assertNotIn('positive_hit',r['sets']['local']['tone_summary'])


if __name__=='__main__':unittest.main()

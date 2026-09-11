import copy,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import requests
from pipeline.company_news import normalize,canonical,collect,views,FILE,feed_url,read,save
from pipeline.dragon_signals import monitor

NOW=datetime(2026,9,11,2,tzinfo=timezone.utc)
SPEC=[dict(symbol='AAA',name='Company A')]


def rss(date='Thu, 10 Sep 2026 09:00:00 GMT',tail=''):
    return ('<rss><channel><item><title>A &amp; B</title><link>https://example.org/a?.tsrc=rss&amp;id=1</link><pubDate>'+date+'</pubDate></item>'+tail+'</channel></rss>').encode()


def resource(p):return SimpleNamespace(base=p,resource=lambda name:p/name,as_of='2026-09-10',vintage='fixture')


class Response:
    def __init__(self,content,status=200):self.content=content;self.status_code=status
    def raise_for_status(self):
        if self.status_code>=400:raise requests.HTTPError(response=self)


class Session:
    def __init__(self,response):self.response=response;self.calls=[]
    def get(self,url,**kwargs):self.calls.append(url);return self.response


class CompanyNewsTests(unittest.TestCase):
    def test_dates_entities_and_tracking_dedup(self):
        r=normalize(rss())[0];self.assertEqual(r['title'],'A & B');self.assertEqual(r['published_at'],'2026-09-10T09:00:00+00:00');self.assertEqual(r['url'],'https://example.org/a?id=1')
        self.assertEqual(canonical('https://example.org/a?id=1&utm_source=x#part'),r['url'])
        with self.assertRaises(ValueError):canonical('https://user:secret@example.org/a')
        for blob in [b'<html></html>',b'<!DOCTYPE rss><rss/>',rss(date='2026-09-10')]:
            with self.assertRaises(ValueError):normalize(blob)
        self.assertEqual(normalize(b'<rss><channel/></rss>'),[])

    def test_cache_archive_and_first_seen_survive_later_feed(self):
        with tempfile.TemporaryDirectory() as name,patch('pipeline.company_news.settings',return_value=SPEC):
            d=resource(Path(name));session=Session(Response(rss()));a=collect(d,session,NOW,lambda _:None);self.assertEqual(a['requests'],1)
            packet=read(d.resource(FILE));first=packet['feeds']['AAA']['items'][0]['first_seen_at']
            self.assertEqual(collect(d,session,NOW+timedelta(hours=2),lambda _:None)['requests'],0)
            session.response=Response(b'<rss><channel/></rss>');collect(d,session,NOW+timedelta(hours=25),lambda _:None)
            current=read(d.resource(FILE))['feeds']['AAA'];self.assertEqual(current['response_items'],0);self.assertEqual(len(current['items']),1);self.assertEqual(current['items'][0]['first_seen_at'],first)

    def test_access_failure_preserves_success_and_stops_batch(self):
        with tempfile.TemporaryDirectory() as name,patch('pipeline.company_news.settings',return_value=SPEC):
            d=resource(Path(name));session=Session(Response(rss()));collect(d,session,NOW,lambda _:None)
            old=read(d.resource(FILE))['feeds']['AAA'];session.response=Response(b'no',403)
            with patch('pipeline.company_news.settings',return_value=SPEC+[dict(symbol='BBB',name='B')]):r=collect(d,session,NOW+timedelta(days=1),lambda _:None)
            current=read(d.resource(FILE))['feeds']['AAA'];self.assertEqual(r['requests'],1);self.assertEqual(r['status'],'access_refused');self.assertEqual(current['items'],old['items']);self.assertEqual(current['retrieved_at'],old['retrieved_at'])
            self.assertEqual(collect(d,session,NOW+timedelta(days=1,minutes=30),lambda _:None)['requests'],0)

    def test_window_future_cutoff_and_failed_data_not_a_new_signal(self):
        with tempfile.TemporaryDirectory() as name,patch('pipeline.company_news.settings',return_value=SPEC):
            d=resource(Path(name));items=[dict(id=str(i),url='https://example.org/'+str(i),title=str(i),published_at='2026-09-10T09:00:00+00:00',first_seen_at=NOW.isoformat()) for i in range(8)]
            items += [dict(items[0],id='old',published_at='2026-09-03T23:59:59+00:00'),dict(items[0],id='future',published_at='2026-09-11T00:00:00+00:00')]
            packet=dict(feeds={'AAA':dict(items=items,url=feed_url('AAA'),retrieved_at=NOW.isoformat(),checked_at=NOW.isoformat(),error=None,response_items=10)});save(d.resource(FILE),packet)
            dragon=dict(sections=[dict(type='entities',entities=[dict(symbol='AAA',id='stock:AAA')])]);views(d,dragon,NOW);r=dragon['sections'][-1]['items'][0]
            self.assertEqual(r['observed_count'],8);self.assertTrue(r['volume_hit']);self.assertEqual(r['excluded_after_cutoff'],1);self.assertIsNone(r['tone'])
            packet['feeds']['AAA']['error']='HTTPError';save(d.resource(FILE),packet);views(d,dragon,NOW);self.assertFalse(dragon['sections'][-1]['items'][0]['volume_hit']);self.assertEqual(dragon['sections'][-1]['items'][0]['observed_count'],8)

    def test_news_weight_is_one_and_does_not_require_equal_price_date(self):
        news=dict(symbol='AAA',available=True,volume_hit=True,latest='2026-09-09T12:00:00+00:00',observed_count=8,start='2026-09-04',end='2026-09-10',retrieved_at=NOW.isoformat())
        e=dict(symbol='AAA',id='stock:AAA',name='A',market='US',sector='Technology',date='2026-09-10',company_news=news)
        d=dict(as_of='2026-09-10',sections=[dict(type='entities',entities=[e]),dict(type='companynews',items=[news,copy.deepcopy(news)])]);rows,_=monitor(d,{'sections':[]},{})
        self.assertEqual(len(rows[0]['hits']),1);self.assertEqual(rows[0]['observed_score'],1);self.assertIsNone(rows[0]['total_score'])
        news['available']=False;rows,_=monitor(d,{'sections':[]},{})
        # The copied second entry still carries the valid observation.
        self.assertEqual(rows[0]['observed_score'],1)


if __name__=='__main__':unittest.main()

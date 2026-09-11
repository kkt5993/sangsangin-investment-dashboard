import copy,hashlib,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pipeline.news_tone import collect,annotate,key,valid,verify_model,FILE,settings
from pipeline.guru_data import save,read
from pipeline.dragon_signals import monitor

NOW=datetime(2026,9,11,4,tzinfo=timezone.utc)
def row(pos=.7,neg=.1):
    p=dict(positive=pos,negative=neg,neutral=1-pos-neg)
    return dict(available=True,probabilities=p,label=max(p,key=p.get),score=pos-neg,tokens=12,analyzed_at=NOW.isoformat())
def resource(path):return SimpleNamespace(base=path,resource=lambda f:path/f)
def feed(path,titles):save(path/'company_news/feeds.json.gz',dict(feeds={'A':{'items':[dict(title=t) for t in titles]}}))

class ToneTests(unittest.TestCase):
    def test_exact_input_reuse_shared_titles_and_changed_revision(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);d=resource(p);feed(p,['Profit up','Profit  up','Loss down']);calls=[]
            def factory(spec):
                return lambda titles:calls.append(titles) or [row() for _ in titles]
            self.assertEqual(collect(d,factory,NOW)['classified'],2)
            self.assertEqual(collect(d,lambda _:self.fail('loaded cached model'),NOW)['status'],'reused')
            feed(p,['Profit falls']);self.assertEqual(collect(d,factory,NOW)['classified'],1)
            spec=settings();spec['revision']='another';self.assertEqual(collect(d,factory,NOW,spec)['classified'],1)
            self.assertEqual(len(read(p/FILE)['entries']),4)

    def test_model_failure_preserves_results_and_backoff(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);d=resource(p);feed(p,['A profits']);collect(d,lambda _:lambda _: [row()],NOW);old=read(p/FILE)['entries']
            feed(p,['A profits','B losses'])
            def fail(_):raise RuntimeError('offline model unavailable')
            self.assertEqual(collect(d,fail,NOW)['status'],'error');self.assertEqual(read(p/FILE)['entries'],old)
            self.assertEqual(collect(d,lambda _:self.fail('backoff'),NOW+timedelta(minutes=1))['status'],'backoff')
            self.assertEqual(collect(d,lambda _:lambda _: [row(.1,.8)],NOW,retry=True)['status'],'ok')

    def test_distinct_headlines_mean_and_unknown_not_neutral(self):
        spec=settings();rows=[dict(title=t,url=str(i)) for i,t in enumerate(['A profit','A  profit','B loss','Unknown'])]
        packet={'entries':{key('A profit',spec):row(.9,.05),key('B loss',spec):row(.1,.7)}}
        articles,s=annotate(rows,packet,spec,True)
        self.assertEqual((s['total'],s['classified']),(3,2));self.assertAlmostEqual(s['score'],.125);self.assertFalse(s['complete']);self.assertFalse(s['positive_hit']);self.assertFalse(articles[-1]['tone']['available'])
        _,s=annotate(rows[:-1],packet,spec,True);self.assertTrue(s['complete']);self.assertTrue(s['positive_hit']);self.assertEqual(sum(s['labels'].values()),2)
        _,s=annotate(rows[:-1],packet,spec,False);self.assertFalse(s['positive_hit']);self.assertAlmostEqual(s['score'],.125)
        _,s=annotate([],packet,spec,True);self.assertIsNone(s['score']);self.assertFalse(s['complete'])

    def test_probabilities_and_pinned_file_integrity(self):
        self.assertTrue(valid(row()));bad=row();bad['probabilities']['positive']=float('nan');self.assertFalse(valid(bad))
        bad=row();bad['label']='negative';self.assertFalse(valid(bad));bad=row();bad['score']=.5;self.assertFalse(valid(bad))
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);(p/'model').write_bytes(b'weights');spec={'files':{'model':hashlib.sha256(b'weights').hexdigest()}};verify_model(p,spec)
            (p/'model').write_bytes(b'different')
            with self.assertRaises(ValueError):verify_model(p,spec)

    def test_tone_signal_weight_date_and_stale_feed(self):
        news=dict(symbol='AAA',available=True,volume_hit=False,latest='2026-09-09T10:00:00+00:00',tone_summary=dict(positive_hit=True,score=.2,classified=2,analyzed_at=NOW.isoformat()))
        e=dict(symbol='AAA',id='stock:AAA',name='A',market='US',sector='T',date='2026-09-10')
        dragon=dict(as_of='2026-09-10',sections=[dict(type='entities',entities=[e]),dict(type='companynews',items=[news,copy.deepcopy(news)])])
        rows,_=monitor(dragon,{'sections':[]},{});self.assertEqual(rows[0]['observed_score'],1);self.assertEqual(rows[0]['hits'][0]['id'],'tone');self.assertIsNone(rows[0]['expected_return'])
        for r in dragon['sections'][1]['items']:r['available']=False
        self.assertEqual(monitor(dragon,{'sections':[]},{})[0],[])

    def test_article_cutoff_before_tone_aggregation(self):
        from pipeline.company_news import views,feed_url
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);d=resource(p);d.as_of='2026-09-10';spec=settings()
            items=[dict(id=str(i),title=t,url='https://example.org/'+str(i),published_at=day+'T10:00:00+00:00') for i,(t,day) in enumerate([('current loss','2026-09-10'),('future gain','2026-09-11'),('old gain','2026-09-03')])]
            save(p/'company_news/feeds.json.gz',dict(feeds={'AAA':dict(items=items,url=feed_url('AAA'),retrieved_at=NOW.isoformat())}))
            save(p/FILE,dict(entries={key(a['title'],spec):row(.1,.8) if i==0 else row(.9,.05) for i,a in enumerate(items)}))
            dragon={'sections':[{'type':'entities','entities':[{'symbol':'AAA','id':'stock:AAA'}]}]}
            with patch('pipeline.company_news.settings',return_value=[dict(symbol='AAA',name='A')]):views(d,dragon,NOW)
            r=dragon['sections'][-1]['items'][0];self.assertEqual(r['observed_count'],1);self.assertAlmostEqual(r['tone'],-.7);self.assertFalse(r['tone_summary']['positive_hit'])

if __name__=='__main__':unittest.main()

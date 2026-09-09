import gzip,io,json,tempfile,unittest
from pathlib import Path
import pandas as pd
import numpy as np
from pipeline.events_data import parse_feed
from pipeline.geoecon_views import tone,corpus,keyword_data,composites,channels,topic_data,news_views
from pipeline.gpr_data import parse,COUNTRIES
from pipeline.engine import zscore

class GeoeconTests(unittest.TestCase):
    def test_rss_rdf_atom_and_timezone(self):
        rss=b'<rss><channel><item><title>Policy</title><link>https://example.org/a</link><pubDate>Tue, 08 Sep 2026 13:00:00 GMT</pubDate></item></channel></rss>'
        rdf=b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/"><item><title>World</title><link>https://example.org/b</link><dc:date>2026-09-08T13:00:00+02:00</dc:date></item></rdf:RDF>'
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>News</title><link href="https://example.org/c"/><published>2026-09-08T13:00:00Z</published></entry></feed>'
        for data in [rss,rdf,atom]:
            rows=parse_feed(data,'Provider');self.assertEqual(len(rows),1);self.assertIsNotNone(pd.Timestamp(rows[0]['published_at']).tzinfo)
        self.assertEqual(parse_feed(atom.replace(b'T13:00:00Z',b'T13:00:00'),'x'),[])
        self.assertEqual(parse_feed(atom.replace(b'https://example.org/c',b'javascript:alert(1)'),'x'),[])

    def test_tone_negation_boundary_and_both_directions(self):
        self.assertEqual(tone('No nuclear threat today')['direction'],0)
        self.assertEqual(tone('Ceasefire agreement after attack')['direction'],1)
        self.assertEqual(tone('War attack conflict')['direction'],-1)
        self.assertEqual(tone('Award winning film')['risk_words'],[])
        self.assertEqual(tone('War war war')['risk_words'],['war'])

    def test_corpus_union_cutoff_and_first_seen(self):
        with tempfile.TemporaryDirectory() as temp:
            def write(n,at,rows):
                p=Path(temp)/n;p.mkdir();(p/'news.json.gz').write_bytes(gzip.compress(json.dumps(dict(retrieved_at=at,items=rows,sources=[])).encode()));return p
            def r(id,t):return dict(title='Taiwan trade',url='https://example.org/'+id,published_at=t,source='BBC World')
            a=r('a','2026-09-08T14:59:59Z');b=r('b','2026-09-08T15:00:00Z');future=r('future','2026-09-07T12:00:00Z')
            one=write('one','2026-09-07T10:00:00Z',[future]);two=write('two','2026-09-08T15:01:00Z',[a,b]);three=write('three','2026-09-09T05:00:00Z',[a])
            class D:as_of='2026-09-08';bases=[one,two,three]
            out,cov=corpus(D());self.assertEqual(len(out),1);self.assertEqual(out[0]['first_seen'],'2026-09-08T15:01:00Z');self.assertEqual(out[0]['date'],'2026-09-08');self.assertIn('taiwan',out[0]['topics']);self.assertEqual(len(cov['captures']),3)

    def test_keyword_equal_windows_and_empty_denominator(self):
        news=[dict(date='2026-09-08',keywords=['war'],id='a'),dict(date='2026-09-02',keywords=[],id='b'),dict(date='2026-09-01',keywords=['war'],id='c'),dict(date='2026-08-26',keywords=[],id='d'),dict(date='2026-08-25',keywords=['war'],id='e')]
        news=[dict(r,direction=0) for r in news]
        r=next(r for r in keyword_data(news,'2026-09-08') if r['term']=='war')
        self.assertEqual((r['recent'],r['prior'],r['recent_total'],r['prior_total']),(1,1,2,2));self.assertEqual(r['delta'],0);self.assertEqual(len(r['daily']),30)
        empty=keyword_data([],'2026-09-08')[0];self.assertIsNone(empty['delta']);self.assertTrue(all(r['share'] is None for r in empty['daily']))

    def test_composite_two_series_sign_rolling_and_future(self):
        class D:
            as_of='2026-09-08'
            def price(self,k,adjusted=True):
                ix=pd.bdate_range('2023-01-01','2026-10-01');a=np.arange(len(ix));return pd.Series(a*.1+20+np.sin(a/(9 if k=='CL=F' else 17)),index=ix)
            def mac(self,k):return self.price(k)
        d=D();out=composites(d);self.assertEqual([r['id'] for r in out],['stress','geoenergy','policy'])
        a=d.price('CL=F').loc[:d.as_of];b=d.price('DX-Y.NYB').loc[:d.as_of];expected=(zscore(a)-zscore(b))/2
        self.assertAlmostEqual(out[1]['value'],expected.iloc[-1],places=5);self.assertAlmostEqual(out[1]['change1m'],expected.iloc[-1]-expected.iloc[-22],places=5)
        for r in out:self.assertLessEqual(r['date'],d.as_of);self.assertGreaterEqual(r['chart']['series'][0]['points'][0][0],'2025-09-08')
        class Constant(D):
            def price(self,k,adjusted=True):return super().price(k,adjusted)*0+2
        self.assertTrue(all(r['value'] is None for r in composites(Constant())))

    def test_channel_unique_article_and_after_hours_price(self):
        class D:
            as_of='2026-09-08'
            def price(self,k,adjusted=True):return pd.Series(np.arange(30)+100.,index=pd.bdate_range('2026-07-29',periods=30))
        r=dict(id='x',topics=['china','taiwan'],direction=-1,published_at='2026-09-01T21:00:00Z')
        out=channels(D(),[r]);semi=next(c for c in out if c['id']=='semi');self.assertEqual(semi['count'],1);self.assertEqual(semi['exposure'],7)
        self.assertEqual(semi['studies'][0]['first_session'],'2026-09-02');self.assertIsNone(semi['studies'][0]['excess5']);self.assertTrue(all(p['y']==0 for p in semi['studies'][0]['curve']))
        self.assertTrue(all(c['exposure'] is None for c in channels(D(),[])))

    def test_gpr_schema_completed_month_and_distinct_units(self):
        f=pd.DataFrame(dict(month=pd.to_datetime(['2026-07-01','2026-08-01','2026-09-01'])))
        for k in ['GPR','GPRT','GPRA']:f[k]=[100.,110.,120.]
        for k in ['SHAREH_CAT_'+str(i) for i in range(1,9)]+['GPRC_'+c for c in COUNTRIES]:f[k]=[.1,.2,.3]
        b=io.BytesIO();f.to_stata(b,write_index=False,convert_dates={'month':'tm'});out,_=parse(b.getvalue(),'2026-09-08')
        self.assertEqual(len(out),2);self.assertEqual(out['SHAREH_CAT_1'].iloc[-1],.2);self.assertEqual(out['GPR'].iloc[-1],110)
        b=io.BytesIO();f.drop(columns='GPRT').to_stata(b,write_index=False,convert_dates={'month':'tm'})
        with self.assertRaises(ValueError):parse(b.getvalue(),'2026-09-08')

if __name__=='__main__':unittest.main()

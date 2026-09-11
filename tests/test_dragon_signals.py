import unittest,copy
from pipeline.dragon_signals import monitor,radar,views,cross_assets
class DragonSignalsTests(unittest.TestCase):
 def fixture(self):
  entities=[dict(id='stock:'+k,symbol=k,name=k,market='US',sector='IT',date='2026-09-10') for k in ['A','B','C']]
  dragon=dict(as_of='2026-09-10',missing=[],sections=[dict(type='entities',entities=entities),dict(type='relationlab',nodes=[dict(id=e['id'],name=e['name']) for e in entities],links=[dict(source='stock:A',target='stock:B',relation='supplies',basis='filing',url='https://example.org/')]),dict(type='dragonresearch',items=[dict(id='doc',kind='official',title='Annual',url='https://example.org/',date='2026-09-09',targets=[dict(id='stock:A')])])])
  ranks={'US':{'leaders':[dict(symbol='A',as_of='2026-09-10',rs=99),dict(symbol='B',as_of='2026-09-11',rs=98),dict(symbol='C',as_of='2026-09-01',rs=97)]}}
  discovery=dict(as_of='2026-09-10',sections=[dict(type='discovery',items=[dict(symbol='A',price_date='2026-09-10',bucket='초기',reasons=['EPS']),dict(symbol='A',price_date='2026-09-10',bucket='중복',reasons=[]),dict(symbol='B',price_date='2026-09-09',bucket='과거',reasons=[])])])
  return dragon,discovery,ranks
 def test_observed_weights_unknowns_and_exact_alignment(self):
  d,x,r=self.fixture();before=copy.deepcopy((d,x,r));rows,rejected=monitor(d,x,r);a=next(r for r in rows if r['symbol']=='A');b=next(r for r in rows if r['symbol']=='B')
  self.assertEqual(a['observed_score'],4);self.assertEqual(len(a['hits']),2);self.assertEqual(a['evidence_score'],8.2);self.assertEqual(a['customers'][0]['name'],'B');self.assertIsNone(a['total_score']);self.assertIsNone(a['live']);self.assertIsNone(a['expected_return']);self.assertEqual(b['hits'],[]);self.assertEqual(len(rejected),3);self.assertEqual((d,x,r),before)
 def test_radar_inclusive_seven_days_and_no_future(self):
  geo={'sections':[dict(type='geosituations',topics=[dict(id='t',name='theme',category='macro',articles=['a','b','c','d'])],news=[dict(id=k,date=dt,title=k,url='https://example.org/',source='s') for k,dt in [('a','2026-09-04'),('b','2026-09-03'),('c','2026-09-11'),('d','2026-09-10')]])]}
  rows=radar(geo,'2026-09-10');self.assertEqual(rows[0]['count'],2);self.assertEqual([r['title'] for r in rows[0]['articles']],['d','a'])
 def test_cross_asset_uses_three_month_column_and_stable_ties(self):
  digest=dict(as_of='2026-09-10',sections=[dict(type='table',group='크로스에셋',columns=['그룹','이름','심볼','실제 가격일','1W %','3M %'],rows=[['g',s,s,dt,999,v] for s,dt,v in [('B','2026-09-10',3),('A','2026-09-10',3),('C','2026-09-10',-2),('D','2026-09-11',80),('E','2026-09-10',None)]])])
  p=cross_assets(digest);self.assertEqual(p['available'],3);self.assertEqual(p['expected'],5);self.assertEqual([x['symbol'] for x in p['leaders']],['A','B','C']);self.assertEqual(p['laggards'][0]['value'],-2)
 def test_views_idempotent_and_period_mismatch_rejected(self):
  d,x,r=self.fixture();d['sections'] += [dict(type='table',group='지금 주목'),dict(type='table',group='트리거·촉매'),dict(type='satellite',sites=[dict(id='past',name='Past',scene=dict(captured_at='2026-09-01T00:00:00Z',source='https://example.org/')),dict(id='future',name='Future',scene=dict(captured_at='2026-09-11T00:00:00Z'))])]
  objs=dict(dragonglass=d,discovery=x,ask_digest=dict(as_of=d['as_of'],sections=[]),geoecon=dict(as_of=d['as_of'],sections=[]));views(objs,r);first=copy.deepcopy(d);views(objs,r);self.assertEqual(first,d)
  alert=next(s for s in d['sections'] if s['type']=='dragontriggers');self.assertEqual(len(alert['items']),1);self.assertEqual([x['id'] for x in alert['log']],['past']);self.assertEqual(sum(r['status']=='연결' for r in alert['rules']),2)
  objs['ask_digest']['as_of']='2026-09-11'
  with self.assertRaises(ValueError):views(objs,r)
if __name__=='__main__':unittest.main()

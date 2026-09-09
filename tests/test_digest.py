import copy,unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.digest import snapshot,themes,trend_panel,stock_watch,risk_findings,key_charts,module_summaries

class Data:
    as_of='2026-09-08'
    def __init__(self):
        dates=pd.bdate_range('2023-01-01',self.as_of);self.p={'A':pd.Series(np.linspace(100,300,len(dates)),index=dates)};self.m={}
    def price(self,key,adjusted=True):return self.p.get(key,pd.Series(dtype=float))
    def mac(self,key):return self.m.get(key,pd.Series(dtype=float))

class DigestTests(unittest.TestCase):
    def test_price_cutoff_missing_and_periods(self):
        d=Data();r=snapshot(d,'A');p=d.p['A'];self.assertAlmostEqual(r['r2y'],(p.iloc[-1]/p.loc[:'2024-09-08'].iloc[-1]-1)*100,5)
        d.p['A'].loc[pd.Timestamp('2026-10-01')]=10000;self.assertEqual(r,snapshot(d,'A'))
        d.p['A']=p.iloc[:30];r=snapshot(d,'A');self.assertIsNone(r['price']);self.assertIsNone(r['r1w']);self.assertEqual(r['signal'],'미산출')
        self.assertIsNone(snapshot(d,'missing')['date'])
    def test_daily_crypto_uses_same_calendar_horizon(self):
        d=Data();dates=pd.date_range('2023-01-01',d.as_of);d.p['daily']=pd.Series(np.arange(len(dates))+100.,index=dates);r=snapshot(d,'daily')
        self.assertEqual(r['starts']['r2y'],'2024-09-08');self.assertEqual(r['starts']['r3m'],'2026-06-08')
        self.assertAlmostEqual(r['r2y'],(d.p['daily'].iloc[-1]/d.p['daily'].loc['2024-09-08']-1)*100,5)
    def test_theme_members_required_and_ties(self):
        d=Data();config={'themes':[{'id':'one','name':'one','members':[{'symbol':'A'}]},{'id':'tie','name':'tie','members':[{'symbol':'A'}]},{'id':'missing','name':'missing','members':[{'symbol':'A'},{'symbol':'B'}]}]}
        before=copy.deepcopy(config);out=themes(d,config);self.assertEqual(config,before)
        self.assertEqual(out[0]['heat'],out[1]['heat']);self.assertIsNone(out[-1]['returns']['r3m']);self.assertIsNone(out[-1]['heat']);self.assertEqual(out[-1]['available'],1)
    def test_trend_rank_and_missing(self):
        rows=[dict(name=k,symbol=k,r1m=v,group='g',date='2026-09-08') for k,v in [('A',2),('B',-1),('C',None),('D',0)]]
        out=trend_panel(rows,'r1m','1M');self.assertEqual([r['name'] for r in out['rows']],['A','D','B']);self.assertEqual(out['available'],3);self.assertEqual(out['expected'],4)
        self.assertEqual(out['laggards'][0]['name'],'B')
    def test_stock_news_word_boundaries(self):
        d=Data();ranks={m:dict(rows=[dict(symbol='TER',name='Teradyne',sector='Tech',rs=90)],membership_as_of=d.as_of) for m in ['US','KR']}
        news=[dict(title='Interest rates'),dict(title='TER rises'),dict(title='Teradyne result'),dict(title='INTEREST policy')]
        out=stock_watch(d,ranks,news);self.assertEqual(out[0]['news_count'],2);self.assertIsNone(out[0]['guru'])
    def test_risk_directions_lag_and_boundaries(self):
        d=Data();dates=pd.to_datetime(['2026-08-25','2026-09-08']);d.m['NFCI']=pd.Series([-1,3],index=dates);d.p['^VIX']=pd.Series([20,25],index=dates)
        state=[dict(inputs=dict(m2=None,sahm=.6),macro_observation_month='2026-06-30')]
        with patch('pipeline.digest.monthly_states',return_value=state):out={r['name']:r for r in risk_findings(d,{})}
        self.assertEqual(out['NFCI']['direction'],1);self.assertEqual(out['NFCI']['date'],'2026-08-25');self.assertEqual(out['VIX']['label'],'경계값')
        self.assertEqual(out['M2 YoY']['label'],'미산출');self.assertEqual(out['Sahm']['direction'],-1)
    def test_stress_delta_and_source_summary(self):
        d=Data();pts=[[str(t.date()),float(i)] for i,t in enumerate(pd.bdate_range('2025-09-01','2026-09-08'))]
        obj={'geoecon':dict(sections=[dict(type='line',group='복합지표',title='stress',series=[dict(points=pts)])])}
        charts=key_charts(d,obj);self.assertEqual(charts[-1]['change'],63);self.assertEqual(charts[-1]['change_unit'],'z 차이');self.assertIsNone(charts[0]['value'])
        source=dict(as_of=d.as_of,status='partial',method_note='method',cards=[['value',1]],sections=[dict(type='table',title='test',columns=['x'],rows=[[0],[1],[2]])],missing=['gap'])
        s=module_summaries({'risk':source,'ask_digest':source});self.assertEqual(len(s),1);self.assertEqual(s[0]['observations'][0]['rows'],[[0],[1]])

if __name__=='__main__':unittest.main()

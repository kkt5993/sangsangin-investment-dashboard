import copy,unittest
import numpy as np
import pandas as pd
from pipeline.iw_review import classify,monthly_states,timeline,monthly_reviews,preserve_weeks,composite_at,weekly_frame


class D:
    as_of='2026-09-08'
    def __init__(self):
        m=pd.date_range('2004-01-01','2026-08-01',freq='MS');t=np.arange(len(m))
        days=pd.bdate_range('2004-01-01',self.as_of);n=np.arange(len(days))
        self.macro={'INDPRO':pd.Series(100+t*.2+np.sin(t/4),index=m),'CPIAUCSL':pd.Series(100*np.exp(t*.002+.002*np.sin(t)),index=m),'M2SL':pd.Series(100+t,index=m),'SAHMREALTIME':pd.Series(.2,index=m),
            'DGS10':pd.Series(3+.6*np.sin(n/100),index=days),'NFCI':pd.Series(-.4,index=days[::5]),'BAMLH0A0HYM2':pd.Series(3.,index=days)}
        self.prices={'^VIX':pd.Series(18.,index=days),**{s:pd.Series(100+n*.01,index=days) for s in ['^GSPC','^KS11','^IXIC']}}
    def mac(self,key):return self.macro.get(key,pd.Series(dtype=float))
    def price(self,key):return self.prices.get(key,pd.Series(dtype=float))


def fixture():
    dates=pd.date_range('2024-01-31','2026-09-30',freq='ME');sections=[]
    for name,actual in [('KOSPI',1.),('NASDAQ',-1.),('S&P500',0.)]:
        records=[dict(origin=str((t-pd.offsets.MonthEnd(1)).date()),target=str(t.date()),prediction=2.,actual=actual,selected_model='fixture',train_target_end=str((t-pd.offsets.MonthEnd(2)).date()),probability=55.) for t in dates]
        sections.append(dict(type='ml',title=name+' · 1M',horizon=1,records=records))
    sections.append(dict(type='line',title='composite',group='전망 요약',left='z',right='',series=[dict(name=str(i),axis='left',points=[[str(t.date()),float(j+i)] for j,t in enumerate(dates)]) for i in range(7)]))
    return dict(sections=sections,as_of='2026-09-08')


class IWTests(unittest.TestCase):
    def test_states_thresholds_and_missing_are_not_risk_on(self):
        self.assertEqual(classify(1,-1,-.2,[False]*5),(0,0,0))
        self.assertEqual(classify(-1,1,.2,[True]*5),(2,2,2))
        self.assertIsNone(classify(1,1,0,[False]*4+[None])[2])
        self.assertIsNone(classify(1,1,0,[False]*4)[2])
        self.assertIsNone(classify(np.nan,-1,0,[False]*5)[0])

    def test_monthly_lag_prefix_and_three_panels(self):
        d=D();a=monthly_states(d);changed=D();changed.macro['CPIAUCSL'].loc['2026-03-01':]*=10;b=monthly_states(changed)
        self.assertEqual([r for r in a if r['date']<'2026-05-01'],[r for r in b if r['date']<'2026-05-01'])
        chart=timeline(a,d.as_of);self.assertEqual(len(chart['panels']),3);self.assertEqual(len(chart['rows']),36);self.assertEqual(chart['rows'][-1][0],'2026-08-31')
        self.assertEqual(a[-1]['macro_observation_month'],'2026-06-30')
        del d.macro['BAMLH0A0HYM2'];self.assertTrue(all(r['risk'] is None for r in monthly_states(d)))

    def test_review_uses_one_truth_and_excludes_future_targets(self):
        d=D();items=monthly_reviews(d,fixture(),monthly_states(d));self.assertEqual(len(items),15);self.assertEqual(items[0]['period'],'2026-08')
        for item in items:
            self.assertEqual(item['hits'],1);self.assertEqual(item['scored'],3);self.assertIn('1/3',item['summary']);self.assertEqual(sum(r[4]=='일치' for r in item['table']['rows']),1)
            self.assertTrue(all(r[7]<r[6]<item['as_of'] for r in item['table']['rows']))

    def test_archives_freeze_closed_weeks_and_keep_first_capture(self):
        first=preserve_weeks([], [dict(period='2026-W35',as_of='2026-08-28',value=1),dict(period='2026-W36',as_of='2026-09-04',value=2)],'2026-W36','2026-09-04T18:00:00Z')
        saved=copy.deepcopy(first)
        second=preserve_weeks(first,[dict(period='2026-W35',as_of='2026-08-28',value=99),dict(period='2026-W36',as_of='2026-09-04',value=3)],'2026-W36','2026-09-05T01:00:00Z')
        self.assertEqual(first,saved);self.assertEqual(second[1]['value'],1);self.assertEqual(second[0]['value'],3)
        self.assertEqual(second[0]['first_recorded_at'],first[0]['first_recorded_at']);self.assertTrue(second[1]['retrospective']);self.assertFalse(second[0]['retrospective'])

    def test_snapshot_chart_removes_future_and_rebases_prefix(self):
        ml=fixture();a=composite_at(ml,'2026-06-12');other=copy.deepcopy(ml)
        for s in other['sections'][-1]['series']:
            for p in s['points']:
                if p[0]>='2026-06-01':p[1]*=100
        self.assertEqual(a,composite_at(other,'2026-06-12'))
        self.assertTrue(all(p[0]<='2026-05-31' for s in a['series'] for p in s['points']))
        for s in a['series']:self.assertAlmostEqual(np.mean([p[1] for p in s['points']]),0,places=3)
        d=D();r=weekly_frame(d,ml,monthly_states(d),'2026-06-12');self.assertTrue(all(row[2] is None or row[2]<='2026-06-12' for row in r['forecasts']['rows']))


if __name__=='__main__':unittest.main()

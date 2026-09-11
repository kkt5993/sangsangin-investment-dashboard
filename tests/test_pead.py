import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import pandas as pd
from pipeline.pead import observation,build,views
from pipeline.pead_data import collect,sources
from pipeline.events_data import save


def raw(rows=None,retrieved='2026-09-10T00:00:00+00:00'):
    return dict(symbol='A',retrieved_at=retrieved,earnings_dates=dict(index=['2026-08-11T20:00:00Z'] if rows is None else [r[0] for r in rows],
        columns=['EPS Estimate','Reported EPS','Surprise(%)'],data=[[1,1.2,20]] if rows is None else [r[1:] for r in rows]))


class PeadTests(unittest.TestCase):
    def prices(self):
        p=pd.Series(100.,index=pd.bdate_range('2026-07-01','2026-09-10'))
        p.loc['2026-08-10':]=110;p.loc['2026-08-12':]=132;p.loc['2026-09-08':]=145.2
        return p,p*0+100

    def data(self):
        p,b=self.prices()
        return SimpleNamespace(as_of='2026-09-08',members={'us100':{'as_of':'2026-09-04','members':[dict(symbol='A',name='Company A'),dict(symbol='B',name='Company B')]}},price=lambda s:b if s=='SPY' else p)

    def test_display_includes_pre_event_but_drift_excludes_reaction(self):
        p,b=self.prices();r=observation(p,b,'2026-08-11T20:00:00Z','2026-09-08')
        self.assertEqual(r['anchor_date'],'2026-08-06');self.assertEqual(r['first_session'],'2026-08-12')
        self.assertAlmostEqual(r['display_return'],45.2);self.assertAlmostEqual(r['reaction'],20);self.assertAlmostEqual(r['drift'],10)
        self.assertEqual(r['curve'][0]['y'],0);self.assertEqual(r['days'],28)
        self.assertEqual(len(r['spark']),len(p.loc['2026-08-06':'2026-09-08']))

    def test_future_missing_and_price_staleness_are_not_zero_returns(self):
        p,b=self.prices();r=observation(p,b,'2026-08-11T20:00:00Z','2026-09-08');p.loc['2026-09-09':]=1e20
        self.assertEqual(observation(p,b,'2026-08-11T20:00:00Z','2026-09-08'),r)
        for t in ['2026-09-09T12:00:00Z','2026-08-11','2026-05-01T12:00:00Z']:
            self.assertIsNone(observation(p,b,t,'2026-09-08'))
        self.assertIsNone(observation(p.loc[:'2026-08-01'],b,'2026-08-11T12:00:00Z','2026-09-08'))
        with self.assertRaises(ValueError):observation(pd.concat([p,p.tail(1)]),b,'2026-08-11T12:00:00Z','2026-09-10')
        fresh=observation(p,b,'2026-09-08T12:00:00Z','2026-09-08');self.assertIsNone(fresh['d5']);self.assertIsNone(fresh['excess20'])

    def test_official_early_close_and_weekend_alignment(self):
        p=pd.Series(range(100,150),index=pd.bdate_range('2026-11-02',periods=50));b=p*0+100
        r=observation(p,b,'2026-11-27T18:00:00Z','2026-12-01')
        self.assertEqual(r['first_session'],'2026-11-30');self.assertEqual(r['close_hour'],13)
        self.assertEqual(observation(p,b,'2026-11-27T17:59:00Z','2026-12-01')['first_session'],'2026-11-27')
        self.assertEqual(observation(p,b,'2026-11-28T12:00:00Z','2026-12-01')['first_session'],'2026-11-30')

    def test_latest_event_selection_future_negative_and_conflicting_duplicates(self):
        d=self.data();a=raw([['2026-12-01T20:00:00Z',1,9,800],['2026-08-11T20:00:00Z',1,1.2,20],['2026-08-01T20:00:00Z',1,2,100]])
        with patch('pipeline.pead.sources',return_value={'A':a}):
            s=build(d);self.assertEqual(s['rows'][0]['surprise'],20);self.assertEqual(s['scope']['available'],1);self.assertEqual(s['scope']['expected'],2)
            a['earnings_dates']['data'][1]=[1,.9,-10];self.assertEqual(build(d)['rows'],[])
            a['earnings_dates']['index'].append('2026-08-11T20:00:00Z');a['earnings_dates']['data'].append([1,2,100]);self.assertEqual(build(d)['rows'],[])

    def test_membership_future_date_rejected_and_views_preserve_other_groups(self):
        d=self.data()
        with patch('pipeline.pead.sources',return_value={'A':raw()}):
            obj=dict(sections=[dict(group='PEAD',type='scatter'),dict(group='PEAD',type='table'),dict(group='턴어라운드',type='text',text='keep')],cards=[],method_note='',missing=[])
            views(d,obj);views(d,obj);self.assertEqual(sum(s['type']=='strategycards' for s in obj['sections']),1)
            self.assertIn(dict(group='턴어라운드',type='text',text='keep'),obj['sections']);self.assertEqual(len(obj['cards']),1)
            d.members['us100']['as_of']='2026-09-09';self.assertEqual(build(d)['rows'],[])

    def test_collector_reuses_good_pages_and_failed_fetch_keeps_prior(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp)/'old';child=Path(tmp)/'new';child.mkdir();old=raw(retrieved='2026-09-01T00:00:00+00:00');save(parent/'events/A.json.gz',old)
            d=SimpleNamespace(as_of='2026-09-08',base=child,bases=[parent,child],members={'us100':{'members':[dict(symbol='A'),dict(symbol='B')]}})
            fail=Mock(side_effect=RuntimeError('fetch failed'));r=collect(d,fetch=fail,pause=lambda _:None,now='2026-09-10T00:00:00Z')
            self.assertEqual([r['status'] for r in r['rows']],['retained','missing']);self.assertEqual(sources(d)['A'],old)
            self.assertFalse((child/'pead_events/A.json.gz').exists())
            recent=raw();save(child/'pead_events/A.json.gz',recent);f=Mock(return_value=pd.DataFrame([[1,1.2,20]],columns=['EPS Estimate','Reported EPS','Surprise(%)'],index=pd.to_datetime(['2026-08-11T20:00:00Z'])))
            r=collect(d,fetch=f,pause=lambda _:None,now='2026-09-10T01:00:00Z');f.assert_called_once_with('B');self.assertEqual(r['status'],'ok')

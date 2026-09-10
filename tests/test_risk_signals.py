import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from pipeline.risk_signals import level,observation,percentile,aggregate,risk_streak,early_warning
from pipeline.risk_signals_data import investor_rows,sentiment_rows,vkospi_rows,history,store_delta,collect,VK_NAME,VK_BLD
from pipeline.store import ROOT,read_json
from pipeline.events_data import read,save


class SignalTests(unittest.TestCase):
    def setUp(self):self.config=read_json(ROOT/'config/risk_signal_rules.json')

    def test_threshold_order_boundaries_and_unknown(self):
        high=dict(cuts=[20,25,40],direction='high');low=dict(cuts=[-2,-4,-7],direction='low')
        self.assertEqual([level(v,high) for v in [19,20,25,40]],[0,1,2,3])
        self.assertEqual([level(v,low) for v in [-1,-2,-4,-7]],[0,1,2,3])
        self.assertIsNone(level(None,high));self.assertIsNone(level(np.nan,high))
        with self.assertRaises(ValueError):level(20,dict(high,cuts=[25,20,40]))

    def test_stale_future_and_missing_are_not_zero_risk(self):
        s=pd.Series([2.,0.,100.],index=pd.to_datetime(['2026-08-28','2026-08-30','2026-09-10']))
        x=observation(s,'2026-09-08',14);self.assertEqual(x['value'],0);self.assertEqual(x['age_days'],9);self.assertTrue(x['fresh'])
        self.assertFalse(observation(s,'2026-09-08',7)['fresh'])
        self.assertIsNone(observation(s,'2026-01-01')['value'])
        rows=[{'level':0},{'level':None}];a=aggregate(rows,self.config)
        self.assertEqual(a['points'],0);self.assertEqual(a['grade'],'판정 보류');self.assertFalse(a['complete'])

    def test_percentile_ties_constant_and_future_invariance(self):
        s=pd.Series([1.,2.,2.,4.,100.]);p=percentile(s,4)
        self.assertAlmostEqual(p.iloc[3],87.5)
        self.assertAlmostEqual(percentile(pd.Series([1.,2.,2.,2.]),4).iloc[-1],62.5)
        self.assertEqual(percentile(pd.Series([3.]*5),4).iloc[-1],50)
        self.assertEqual(p.iloc[3],percentile(s.iloc[:4],4).iloc[-1])

    def test_streak_requires_complete_sessions_and_records_lower_bound(self):
        complete=lambda tier:dict(complete=True,level=tier)
        unknown=dict(complete=False,level=None)
        self.assertEqual(risk_streak([complete(1),complete(2),complete(3)]),dict(days=2,lower_bound=False))
        self.assertEqual(risk_streak([unknown,complete(2)]),dict(days=1,lower_bound=True))
        self.assertIsNone(risk_streak([complete(2),unknown])['days'])
        self.assertEqual(risk_streak([unknown,complete(1)])['days'],0)
        self.assertEqual(risk_streak([complete(2)]*63),dict(days=63,lower_bound=True))
        for tiers,points,tier in [([0],0,0),([2],3,1),([2,2],6,2),([3,3],10,3)]:
            result=aggregate([{'level':t} for t in tiers],self.config)
            self.assertEqual((result['points'],result['level']),(points,tier))

    def test_early_warning_no_future_data_and_input_formula(self):
        rng=np.random.default_rng(833);dates=pd.bdate_range('2024-01-01',periods=500)
        p=pd.Series(100*np.exp(np.cumsum(rng.normal(0,.01,500))),index=dates)
        a=early_warning(p,self.config);b=early_warning(p.iloc[:400],self.config)
        np.testing.assert_allclose(a.loc[b.index[-30:],'csd'],b.csd.tail(30),atol=1e-7)
        last=a.iloc[-1]
        self.assertAlmostEqual(last.cluster,100*(.5*np.clip(last.expansion/100,0,1)+.5*np.clip(last.abs_return_ar1,0,1)))
        self.assertTrue(a.csd.between(0,100).all());self.assertTrue(a.cluster.between(0,100).all())
        constant=early_warning(pd.Series(100.,index=dates),self.config)
        self.assertTrue(constant.csd.isna().all());self.assertTrue(constant.cluster.isna().all())


class SignalInputTests(unittest.TestCase):
    def vk_packet(self):
        return dict(name=VK_NAME,index_code='1300',unit='index_points',measure='option_implied_volatility_30d',
            query=dict(bld=VK_BLD,indTpCd='1',idxIndCd='300'),retrieved_at='2026-09-10T01:00:00Z',
            rows=[dict(TRD_DD='2026/09/08',OPNPRC_IDX='44.38',HGPRC_IDX='47.45',LWPRC_IDX='44.36',CLSPRC_IDX='47.34')])

    def test_vkospi_identity_ohlc_dates_and_units(self):
        p=self.vk_packet();r=vkospi_rows(p,'2026-09-08')[0]
        self.assertEqual(r['value'],47.34);self.assertEqual(r['date'],'2026-09-08')
        for k,v in [('name','코스피200'),('index_code','1028'),('unit','percent_fraction')]:
            with self.assertRaises(ValueError):vkospi_rows(dict(p,**{k:v}),'2026-09-08')
        with self.assertRaises(ValueError):vkospi_rows(dict(p,query=dict(p['query'],idxIndCd='028')),'2026-09-08')
        for k,v in [('HGPRC_IDX','40'),('CLSPRC_IDX','0'),('TRD_DD','2026/09/09')]:
            with self.assertRaises(ValueError):vkospi_rows(dict(p,rows=[dict(p['rows'][0],**{k:v})]),'2026-09-08')
        with self.assertRaises(ValueError):vkospi_rows(dict(p,rows=p['rows']+[dict(p['rows'][0],CLSPRC_IDX='47')]),'2026-09-08')

    def packet(self):
        values=[10,20,30,40,50,60,70,80,-450,100,-10]
        row={'TRD_DD':'2026/09/08','TRDVAL_TOT':'0',**{'TRDVAL'+str(i+1):str(v*100000000) for i,v in enumerate(values)}}
        return dict(market='KOSPI',unit='KRW',measure='net_buy',excludes=['ETF','ETN','ELW'],retrieved_at='2026-09-10T01:00:00Z',rows=[row])

    def test_investor_amount_balance_aggregate_and_other_foreign_exclusion(self):
        p=self.packet();r=investor_rows(p,'2026-09-08')[0]
        self.assertEqual(r['foreign_krw']/1e8,100);self.assertEqual(r['institution_krw']/1e8,280)
        self.assertEqual(r['other_foreign_krw']/1e8,-10)
        for change in ['blank','unbalanced','unit','future','duplicate']:
            bad=copy.deepcopy(p)
            if change=='blank':bad['rows'][0]['TRDVAL1']=''
            if change=='unbalanced':bad['rows'][0]['TRDVAL_TOT']='1'
            if change=='unit':bad['unit']='shares'
            if change=='future':bad['rows'][0]['TRD_DD']='2026/09/09'
            if change=='duplicate':
                bad['rows'].append(dict(bad['rows'][0],TRDVAL10='10100000000',TRDVAL11='-1100000000'))
            with self.assertRaises(ValueError,msg=change):investor_rows(bad,'2026-09-08')

    def test_news_provider_precision_future_and_schema(self):
        dates=pd.date_range('2025-01-01',periods=400);f=pd.DataFrame({'date':dates,'News Sentiment':np.arange(400)/123456.})
        rows=sentiment_rows(f,'2025-12-31')
        self.assertEqual(len(rows),365);self.assertEqual(float(rows[1]['value']),1/123456.)
        with self.assertRaises(ValueError):sentiment_rows(f.rename(columns={'News Sentiment':'Other'}),'2025-12-31')

    def test_revision_delta_preserves_parent_and_merges_only_changed_dates(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            class Data:
                as_of='2026-09-08';base=b;bases=[a,b]
            d=Data();original=self.packet();save(a/'risk_signals/investors.json.gz',original)
            result=store_delta(d,'investors',original);self.assertEqual(result['changed'],0)
            revised=copy.deepcopy(original);revised['rows'][0]['TRDVAL10']='10100000000';revised['rows'][0]['TRDVAL11']='-1100000000'
            self.assertEqual(store_delta(d,'investors',revised)['changed'],1)
            self.assertEqual(history(d,'investors')[0][0]['foreign_krw'],10100000000)
            self.assertEqual(store_delta(d,'investors',revised)['changed'],1)
            self.assertEqual(history(d,'investors')[0][0]['foreign_krw'],10100000000)
            self.assertEqual(read(a/'risk_signals/investors.json.gz'),original)

    def test_failure_preserves_prior_timestamp_and_permission_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            class Data:
                as_of='2026-09-09';base=b;bases=[a,b]
                def price(self,*args):return pd.Series([100.],index=pd.to_datetime(['2026-09-09']))
            save(a/'risk_signals/investors.json.gz',self.packet())
            save(a/'risk_signals/sentiment.json.gz',dict(retrieved_at='2020-01-01T00:00:00Z',rows=[dict(date='2020-01-01',value='0.1')]))
            def fail(*args):raise RuntimeError('Fixture error')
            def forbidden(*args):raise AssertionError('Unauthorized KRX fetch')
            report=collect(Data(),False,fetch_news=fail,fetch_investors=forbidden,fetch_vkospi=forbidden)
            self.assertEqual([r['status'] for r in report['parts']],['retained_error','retained_permission_required','missing_permission_required'])
            self.assertEqual(report['parts'][0]['retrieved_at'],'2020-01-01T00:00:00Z')
            self.assertFalse((b/'risk_signals/investors.json.gz').exists())

    def test_vkospi_overlap_failure_and_same_run_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            class Data:
                as_of='2026-09-09';base=b;bases=[a,b]
                def price(self,*args):return pd.Series([100.],index=pd.to_datetime(['2026-09-09']))
            packet=self.vk_packet();save(a/'risk_signals/vkospi.json.gz',packet)
            save(b/'risk_signals/sentiment.json.gz',dict(retrieved_at='2026-09-10T00:00:00Z',rows=[dict(date='2026-09-08',value='0.1')]))
            inv=self.packet();inv['rows'][0]['TRD_DD']='2026/09/09';save(b/'risk_signals/investors.json.gz',inv)
            def fail(*args):raise RuntimeError('Fixture error')
            report=collect(Data(),True,fetch_vkospi=fail)
            self.assertEqual(report['parts'][-1]['status'],'retained_error')
            self.assertEqual(report['parts'][-1]['retrieved_at'],packet['retrieved_at'])
            calls=[]
            def success(start,end):
                calls.append([start,end]);return [*packet['rows'],dict(packet['rows'][0],TRD_DD='2026/09/09')]
            report=collect(Data(),True,fetch_vkospi=success)
            self.assertEqual(calls,[['20260829','20260909']]);self.assertEqual(report['parts'][-1]['changed'],1)
            self.assertEqual(len(history(Data(),'vkospi')[0]),2)
            def forbidden(*args):raise AssertionError('Reused observation requested again')
            self.assertEqual(collect(Data(),True,fetch_vkospi=forbidden)['parts'][-1]['status'],'reused')


if __name__=='__main__':unittest.main()

import unittest
import numpy as np
import pandas as pd
from pipeline.overview_state import anchors,align,macro,history_z,relative36,liquidity,states,leaders


class Fixture:
    as_of='2026-09-08';fund={}
    def mac(self,key):
        freq='QE' if key in ['CP','GDP'] else 'W-WED' if key in ['WALCL','WTREGEN'] else 'B' if key=='RRPONTSYD' else 'ME'
        index=pd.date_range('2000-01-01',self.as_of,freq=freq);a=np.arange(len(index));level=100+np.sin(a*.1)*2+a*.03
        if key=='WALCL':level=6000000+a*100
        if key=='WTREGEN':level=500000+a*10
        if key=='RRPONTSYD':level=50+a*.005
        return pd.Series(level,index=index)
    def price(self,key,adjusted=True):
        index=pd.bdate_range('2000-01-01',self.as_of);a=np.arange(len(index));shift=sum(map(ord,key))%100
        return pd.Series(100*np.exp(a*.0003+np.sin(a*.01+shift)*.05),index=index)


class OverviewTests(unittest.TestCase):
    def test_monthly_and_quarterly_availability(self):
        class D:
            as_of='2026-09-08'
            def mac(self,key):return pd.Series([10,20],index=pd.to_datetime(['2026-01-01','2026-04-01'])) if key=='Q' else pd.Series([1,2],index=pd.to_datetime(['2026-06-01','2026-07-01']))
        index=pd.to_datetime(['2026-07-30','2026-07-31','2026-08-30','2026-08-31','2026-09-08'])
        m=macro(D(),'M',index);self.assertTrue(pd.isna(m.value.iloc[0]));self.assertEqual(m.value.iloc[1],1);self.assertEqual(m.value.iloc[2],1);self.assertEqual(m.value.iloc[3],2)
        q=macro(D(),'Q',index,freq='Q',lag_months=2);self.assertEqual(q.value.iloc[2],10);self.assertEqual(q.value.iloc[3],20);self.assertEqual(str(q.period.iloc[-1].date()),'2026-06-30')
    def test_step_alignment_expires_and_never_backfills(self):
        p=pd.Series([5.],index=pd.to_datetime(['2026-01-01']));idx=pd.to_datetime(['2025-12-31','2026-01-03','2026-01-10'])
        out=align(p,p.index+pd.Timedelta(days=1),p.index,idx,7);self.assertTrue(pd.isna(out.value.iloc[0]));self.assertEqual(out.value.iloc[1],5);self.assertTrue(pd.isna(out.value.iloc[2]))
    def test_q4_profit_extra_release_lag(self):
        class D:
            as_of='2025-03-31'
            def mac(self,key):return pd.Series([100.],index=pd.to_datetime(['2024-10-01']))
        r=macro(D(),'CP',pd.to_datetime(['2025-02-28','2025-03-30','2025-03-31']),freq='Q',lag_months=2)
        self.assertTrue(r.value.iloc[:2].isna().all());self.assertEqual(r.value.iloc[-1],100)
    def test_shutdown_release_overrides(self):
        class D:
            as_of='2026-05-01'
            def mac(self,key):return pd.Series([100.,200.],index=pd.to_datetime(['2025-07-01','2025-10-01']))
        r=macro(D(),'CP',pd.to_datetime(['2025-11-30','2025-12-31','2026-03-31','2026-04-09']),freq='Q',lag_months=2)
        self.assertTrue(pd.isna(r.value.iloc[0]));self.assertEqual(r.value.iloc[1],100);self.assertEqual(r.value.iloc[2],100);self.assertEqual(r.value.iloc[3],200)
    def test_z_has_history_only_and_constant_is_missing(self):
        s=pd.Series(np.sin(np.arange(150)*.2)+np.arange(150)*.1);z=history_z(s);self.assertTrue(z.iloc[:59].isna().all());self.assertAlmostEqual(z.iloc[70],history_z(s.iloc[:71]).iloc[-1]);self.assertTrue(history_z(s*0+1).isna().all())
        r=relative36(pd.Series(np.arange(1,101)));self.assertTrue(r.iloc[:35].isna().all());self.assertAlmostEqual(r.iloc[35],(36/18.5-1)*100)
    def test_liquidity_units_and_yoy(self):
        class D:
            as_of='2026-09-08'
            def mac(self,key):
                index=pd.date_range('2000-01-01',self.as_of,freq='B');i=np.arange(len(index))
                return pd.Series({'WALCL':6000000+i*100,'WTREGEN':500000+i*10,'RRPONTSYD':50+i*.001}[key],index=index)
        d=D();idx=anchors(d.as_of);out,parts=liquidity(d,idx);level=parts[0].value-parts[1].value-1000*parts[2].value/1000
        self.assertAlmostEqual(out.value.iloc[-1],(level.iloc[-1]/level.iloc[-13]-1)*100)
        rrp=d.mac('RRPONTSYD').loc[:idx[-1]-pd.Timedelta(days=1)].iloc[-1]
        self.assertEqual(parts[2].value.iloc[-1],rrp*1000,'RRP USD bn must be converted to USD mn')
        t=idx[-1];self.assertLess(parts[2].period.loc[t],t,'one day release lag applied')
    def test_panels_roles_provenance_and_partial_month(self):
        panels=states(Fixture());self.assertEqual([len(p['axes']) for p in panels],[6,5])
        for p in panels:
            self.assertEqual(len(p['rows']),36);self.assertEqual([m['index'] for m in p['milestones']],[11,23,29,35]);self.assertTrue(p['rows'][-1]['partial_month'])
            self.assertEqual(p['rows'][-1]['date'],Fixture.as_of)
            for row in p['rows']:
                for r in row['provenance'].values():
                    if r['available']:self.assertLessEqual(r['period'],r['available']);self.assertLessEqual(r['available'],row['date'])
        self.assertEqual({a['role'] for a in panels[0]['axes']},{'x','z','y','color','size','halo'})
        self.assertEqual(leaders(Fixture())['stocks'],[])

    def test_leaders_currency_period_and_positive_base(self):
        def raw(currency,cap,prior=10,previous_date='2025-06-30'):
            return dict(info=dict(currency=currency,marketCap=cap),retrieved_at='2026-09-08T20:00:00Z',
                quarterly_income=dict(index=['NetIncome'],columns=[previous_date,'2026-06-30'],data=[[prior,15]]))
        class D:
            as_of='2026-09-08'
            fund={'US':raw('USD',1e11),'KR':raw('KRW',1.4e14),'NEG':raw('USD',1e9,-10),'MIS':raw('USD',1e9,10,'2025-03-31'),'EUR':raw('EUR',1e12)}
            def price(self,key,adjusted=True):
                return pd.Series([1400.] if key=='KRW=X' else [100.,120.],index=pd.to_datetime(['2026-09-08'] if key=='KRW=X' else ['2025-09-08','2026-09-08']))
        result=leaders(D());self.assertEqual(result['pool'],4);self.assertEqual(result['eligible'],2)
        self.assertEqual({r['symbol'] for r in result['stocks']},{'US','KR'})
        for row in result['stocks']:
            self.assertAlmostEqual(row['cap_usd_bn'],100);self.assertAlmostEqual(row['momentum'],20);self.assertEqual(row['growth'],50)
            self.assertEqual(row['score'],0);self.assertEqual(row['prior_profit_period'],'2025-06-30')
        class Stale(D):
            def price(self,key,adjusted=True):
                return pd.Series([1400.],index=pd.to_datetime(['2026-08-31'])) if key=='KRW=X' else super().price(key,adjusted)
        self.assertEqual([r['symbol'] for r in leaders(Stale())['stocks']],['US'])


if __name__=='__main__':unittest.main()

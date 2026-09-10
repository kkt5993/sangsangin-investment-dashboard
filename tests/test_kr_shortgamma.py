import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
from pipeline.events_data import save
from pipeline.kr_shortgamma import price_diagnostics, fund_exposure, packet, views
from pipeline.kr_shortgamma_data import definitions, index_rows, expiry_dates, history


def definition(code='122630',benchmark='코스피 200',label='2X 레버리지'):
    return dict(ISU_SRT_CD=code,ISU_ABBRV='상품 '+code,ETF_OBJ_IDX_NM=benchmark,IDX_CALC_INST_NM2=label,LIST_DD='2010/02/22')


def quote(code='122630',benchmark='코스피 200',aum=100):
    return dict(code=code,name='레버리지 '+code,benchmark=benchmark,reported_net_assets=aum,nav=5,shares=30)


def prices(n=400):
    c=100*np.cumprod(1+.001+.004*np.sin(np.arange(n)/3))
    return [dict(date=t.strftime('%Y-%m-%d'),open=p,high=p*1.01,low=p*.99,close=p) for t,p in zip(pd.bdate_range('2024-01-01',periods=n),c)]


class KRShortGammaTests(unittest.TestCase):
    def test_official_benchmark_and_leverage_not_name_guess(self):
        raw=dict(rows=[definition(),definition('252670','코스피 200 선물지수','2X 인버스'),definition('114800','코스피 200 선물지수','1X 인버스'),definition('sector','코스피 200 정보기술'),definition('ordinary',label='일반'),definition('unknown',label='새로운 배율')])
        result=definitions(raw,'2026-09-08')
        self.assertEqual([r['leverage'] for r in result],[2,-2,-1,None])
        raw['rows'][0]['LIST_DD']='2026/09/09'
        self.assertNotIn('122630',[r['code'] for r in definitions(raw,'2026-09-08')])

    def test_currency_nav_and_bidirectional_flow(self):
        master=dict(rows=[definition(),definition('inv','코스피 200 선물지수','2X 인버스')])
        rows,_=fund_exposure(dict(date='20260908',etfs=[quote(),quote('inv','코스피 200 선물지수')]),master,'2026-09-08')
        self.assertEqual(sum(r['coefficient'] for r in rows),800)
        self.assertEqual(sum(r['per_1pct_krw'] for r in rows),8)
        self.assertEqual(sum(r['coefficient'] for r in rows)*-.05,-40)
        self.assertTrue(all(r['aum_krw']==100 for r in rows),'reported net assets precede rounded NAV × shares')
        rows,_=fund_exposure(dict(date='20260908',etfs=[quote(aum=None)]),dict(rows=[definition()]),'2026-09-08')
        self.assertEqual(rows[0]['aum_krw'],150)

    def test_missing_definition_aum_and_mismatched_benchmark_visible(self):
        master=dict(rows=[definition(),definition('missing')])
        rows,_=fund_exposure(dict(date='20260908',etfs=[quote(benchmark='코스피 200 정보기술'),quote('unknown')]),master,'2026-09-08')
        self.assertEqual(len(rows),3)
        self.assertTrue(all(r['per_1pct_krw'] is None and r['reason'] for r in rows))
        with self.assertRaisesRegex(ValueError,'Future'):fund_exposure(dict(date='20260909'),master,'2026-09-08')

    def test_simple_returns_sample_rv_and_no_future_leak(self):
        rows=prices();a=price_diagnostics(rows);b=price_diagnostics(rows[:350])
        pd.testing.assert_frame_equal(a.iloc[:350],b)
        c=np.array([r['close'] for r in rows]);returns=c[1:]/c[:-1]-1
        self.assertAlmostEqual(a.rv21.iloc[-1],np.std(returns[-21:],ddof=1)*np.sqrt(252)*100)
        self.assertAlmostEqual(a.vol_ratio.iloc[-1],np.std(returns[-5:],ddof=1)/np.std(returns[-21:],ddof=1))
        self.assertTrue(a.score.iloc[:272].isna().all());self.assertTrue(a.score.dropna().between(0,100).all())

    def test_extreme_window_and_zero_range_denominator(self):
        rows=[dict(date=t.strftime('%Y-%m-%d'),open=105,high=110,low=100,close=101.5 if i<7 else 105) for i,t in enumerate(pd.bdate_range('2026-01-01',periods=20))]
        a=price_diagnostics(rows);self.assertAlmostEqual(a.extreme_pct.iloc[-1],35)
        rows[-1].update(open=105,high=105,low=105,close=105)
        a=price_diagnostics(rows);self.assertEqual(a.extreme_valid.iloc[-1],19);self.assertAlmostEqual(a.extreme_pct.iloc[-1],7/19*100)
        for r in rows:r.update(open=105,high=105,low=105,close=105)
        self.assertTrue(pd.isna(price_diagnostics(rows).extreme_pct.iloc[-1]))

    def test_drawdown_gate_closes_and_constant_prices_finite(self):
        rows=prices();rows[-1].update(open=80,close=80,low=79,high=81)
        a=price_diagnostics(rows);self.assertEqual(a.score.iloc[-1],0)
        for r in rows:r.update(open=100,close=100,low=100,high=100)
        a=price_diagnostics(rows);self.assertEqual(a.score.iloc[-1],0);self.assertEqual(a.rsi.iloc[-1],50);self.assertTrue(pd.isna(a.vol_ratio.iloc[-1]))

    def test_official_expiry_holiday_and_ohlc_validation(self):
        # 2025 October's second Thursday was a holiday: actual expiry was Wednesday.
        row=dict(ISU_NM='코스피200 C 202510   335.0',SETLMULT='250,000',LIST_DD='2025/09/12',LSTTRD_DD='2025/10/08')
        self.assertEqual(expiry_dates(dict(rows=[row,row])),['2025-10-08'])
        row['SETLMULT']='50,000'
        with self.assertRaisesRegex(ValueError,'multiplier'):expiry_dates(dict(rows=[row]))
        raw=dict(TRD_DD='2026/09/08',OPNPRC_IDX='1,000',HGPRC_IDX='1,020',LWPRC_IDX='990',CLSPRC_IDX='1,010')
        self.assertEqual(index_rows([raw,raw],'2026-09-08')[0]['close'],1010)
        with self.assertRaisesRegex(ValueError,'Future'):index_rows([raw],'2026-09-07')
        raw['HGPRC_IDX']='995'
        with self.assertRaisesRegex(ValueError,'Inconsistent'):index_rows([raw],'2026-09-08')

    def test_incremental_correction_and_missing_view(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/'old';b=root/'new'
            raw=dict(TRD_DD='2026/09/08',OPNPRC_IDX='100',HGPRC_IDX='102',LWPRC_IDX='99',CLSPRC_IDX='101')
            save(a/'kr_shortgamma/index.json.gz',dict(rows=[raw]));save(b/'kr_shortgamma/index.json.gz',dict(rows=[dict(raw,CLSPRC_IDX='102')]))
            self.assertEqual(history(SimpleNamespace(bases=[a,b],as_of='2026-09-08'))[0]['close'],102)
            d=SimpleNamespace(bases=[],as_of='2026-09-08',resource=lambda name:root/'missing'/name)
            p,f=packet(d);self.assertFalse(p['complete']);self.assertTrue(p['stale']);self.assertIsNone(p['per_1pct_krw'])
            obj=dict(sections=[],method_note='',missing=[]);views(d,obj)
            self.assertEqual(len(next(s for s in obj['sections'] if s['title']=='KOSPI 숏감마 · 8개 관측')['rows']),8)

    def test_collector_delta_and_failure_preserve_previous_input(self):
        from pipeline.kr_shortgamma_data import collect
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/'old';b=root/'new';c=root/'failed'
            prior=dict(TRD_DD='2026/09/07',OPNPRC_IDX='100',HGPRC_IDX='102',LWPRC_IDX='99',CLSPRC_IDX='101')
            saved=dict(retrieved_at='2026-09-08T02:00:00+00:00',requested_as_of='2026-09-07',rows=[prior])
            save(a/'kr_shortgamma/index.json.gz',saved)
            for name in ['etf_definitions','expiries']:save(a/'kr_shortgamma'/(name+'.json.gz'),dict(retrieved_at=saved['retrieved_at'],rows=[]))
            def data(base):return SimpleNamespace(base=base,bases=[a,base],as_of='2026-09-08',resource=lambda name:base/name if (base/name).exists() else a/name)
            calls=[]
            def fetch(*args):
                calls.append(args)
                return pd.DataFrame([prior,dict(prior,TRD_DD='2026/09/08',CLSPRC_IDX='102')])
            modules={'pykrx.website.krx.market.core':SimpleNamespace(개별지수시세=lambda:SimpleNamespace(fetch=fetch)),
                     'pykrx.website.krx.etx.core':SimpleNamespace(ETF_전종목기본종목=None),
                     'pykrx.website.krx.future.core':SimpleNamespace(전종목기본정보=None)}
            with patch.dict('sys.modules',modules),patch('pipeline.kr_shortgamma_data.time.sleep'),patch('pipeline.kr_shortgamma_data.stamp',return_value='2026-09-10T03:00:00+00:00'):
                report=collect(data(b))
                from pipeline.events_data import read
                self.assertEqual([r['TRD_DD'] for r in read(b/'kr_shortgamma/index.json.gz')['rows']],['2026/09/08'])
                self.assertEqual(calls,[('028','1','20260828','20260908')])
                self.assertEqual(next(r for r in report['parts'] if r['part']=='index')['status'],'ok')
                # A later provider error cannot overwrite the prior good raw file.
                modules['pykrx.website.krx.market.core'].개별지수시세=lambda:SimpleNamespace(fetch=lambda *args:(_ for _ in ()).throw(RuntimeError('provider failure')))
                failed=collect(data(c))
                self.assertEqual(next(r for r in failed['parts'] if r['part']=='index')['status'],'error')
                self.assertFalse((c/'kr_shortgamma/index.json.gz').exists())
                self.assertEqual(history(data(c))[0]['close'],101)


if __name__=='__main__':unittest.main()

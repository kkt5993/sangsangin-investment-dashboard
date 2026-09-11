import json,gzip,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from pipeline.earnings_details import fiscal_projection,fx_rate,statements,korean_cards,global_rows

def split(f):return json.loads(f.to_json(orient='split',date_format='iso'))
def raw(end='2027-01-31',base='2026-01-31'):
    return dict(info=dict(financialCurrency='USD'),retrieved_at='2026-09-09T00:00:00Z',
        annual_income=split(pd.DataFrame({base:{'NetIncome':100.,'OperatingIncome':120.,'TotalRevenue':1000.}})),
        earnings_estimate=split(pd.DataFrame({'avg':[12.,18.],'yearAgoEps':[10.,12.],'currency':['USD','USD']},index=['0y','+1y'])),
        revenue_estimate=split(pd.DataFrame({'avg':[1200.,1600.],'yearAgoRevenue':[1000.,1200.],'currency':['USD','USD']},index=['0y','+1y'])),
        estimate_periods=[dict(period='0y',endDate=end),dict(period='+1y',endDate=str(pd.Timestamp(end)+pd.DateOffset(years=1))[:10])])

class EarningsDetailTests(unittest.TestCase):
    def test_fiscal_year_not_calendar_year_and_compounding(self):
        p=fiscal_projection(raw(),'2026-09-08');self.assertEqual(p['issues'],[])
        self.assertEqual([r['label'] for r in p['forecasts']],['2027E','2028E'])
        self.assertEqual([r['ni'] for r in p['forecasts']],[120,180]);self.assertEqual(p['forecasts'][1]['revenue'],1600)
        june=fiscal_projection(raw('2027-06-30','2026-06-30'),'2026-09-08');self.assertEqual(june['forecasts'][0]['ni'],120)

    def test_missing_period_currency_or_base_never_flat_forecast(self):
        a=raw();a['estimate_periods']=[];p=fiscal_projection(a,'2026-09-08');self.assertTrue(all(r['ni'] is None and r['revenue'] is None for r in p['forecasts']))
        a=raw();a['info']['financialCurrency']='TWD';p=fiscal_projection(a,'2026-09-08');self.assertTrue(all(r['ni'] is None and r['revenue'] is None for r in p['forecasts']))
        a=raw();a['annual_income']['data'][0][0]=-100;p=fiscal_projection(a,'2026-09-08');self.assertIsNone(p['forecasts'][0]['ni'])

    def test_rollover_and_different_estimate_basis(self):
        a=raw(end='2028-01-31');self.assertIsNone(fiscal_projection(a,'2026-09-08')['forecasts'][0]['ni'])
        a=raw();a['revenue_estimate']['data'][0][1]=850;p=fiscal_projection(a,'2026-09-08');self.assertIsNone(p['forecasts'][0]['ni']);self.assertEqual(p['forecasts'][0]['revenue'],1200)
        a=raw();a['earnings_estimate']['data'][1][1]=20;p=fiscal_projection(a,'2026-09-08');self.assertEqual(p['forecasts'][0]['ni'],120);self.assertIsNone(p['forecasts'][1]['ni'])

    def test_52week_period_tolerance_and_future_statement_cutoff(self):
        p=fiscal_projection(raw(base='2026-01-25'),'2026-09-08');self.assertEqual(p['forecasts'][0]['ni'],120)
        a=raw();a['annual_income']=split(pd.DataFrame({'2026-01-31':{'NetIncome':100},'2027-01-31':{'NetIncome':500}}));self.assertEqual(len(statements(a,'annual','2026-09-08')),1)

    def test_fx_direction_freshness_and_future_exclusion(self):
        class D:
            as_of='2026-09-08'
            def price(self,k,adjusted=False):return pd.Series([1400 if k=='KRW=X' else 1.2,9999],index=pd.to_datetime(['2026-09-08','2026-09-09']))
        self.assertEqual(fx_rate(D(),'KRW')['rate'],1/1400);self.assertEqual(fx_rate(D(),'EUR')['rate'],1.2);self.assertIsNone(fx_rate(D(),'ABC'))
        class Stale(D):
            def price(self,k,adjusted=False):return pd.Series([1400],index=pd.to_datetime(['2026-08-31']))
        self.assertIsNone(fx_rate(Stale(),'KRW'))

    def test_korean_consensus_unit_date_and_actual_loss(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'local_consensus.json.gz';rows=[]
            for key in ['E122710.M','E121500.M','E121000.M']:
                for when,value in [('2026-08-07',10000),('2026-09-09',99000)]:rows.append(dict(ticker='A005930',item_code=key,period='2026AS',as_of=when,value=value,unit='KRW 100mn'))
            path.write_bytes(gzip.compress(json.dumps(dict(rows=rows)).encode()))
            a=raw('2026-12-31','2025-12-31');a['info']['financialCurrency']='KRW';a['annual_income']=split(pd.DataFrame({'2025-12-31':{'NetIncome':-2e12,'NetIncomeCommonStockholders':-1e12,'OperatingIncome':-3e12}}))
            class D:
                as_of='2026-09-08';fund={'005930.KS':a}
                def resource(self,n):return path
                def price(self,*args,**kwargs):return pd.Series(dtype=float)
            c=korean_cards(D(),{})[0];self.assertEqual(c['metrics'][1]['rows'][0]['value'],-1);self.assertEqual(c['metrics'][1]['rows'][1]['value'],1);self.assertEqual(c['projection']['forecasts'][0]['source_dates']['ni'],'2026-08-07')

    def test_global_rank_uses_actual_not_proxy(self):
        class D:
            as_of='2026-09-08';fund={'A':raw(),'B':raw()}
        D.fund['A']['annual_income']['data'][0][0]=100e9
        D.fund['B']['annual_income']['data'][0][0]=200e9
        out=global_rows(D(),{'A':'One','B':'Two'});self.assertEqual(out['rows'][0]['symbol'],'B');self.assertEqual(out['available'],2)

    def test_collector_preserves_only_cached_period_metadata(self):
        from pipeline.acquire import collect_fundamentals
        class T:
            _analysis=type('A',(),{'_earnings_trend':[dict(period='0y',endDate='2027-01-31',secret='omit')]})()
            def get_info(self):return dict(financialCurrency='USD',lastFiscalYearEnd=10,private='omit')
            def get_income_stmt(self,**kwargs):return pd.DataFrame()
            get_earnings_estimate=get_revenue_estimate=get_earnings_history=get_income_stmt
        with tempfile.TemporaryDirectory() as temp,patch('pipeline.acquire.yf.Ticker',return_value=T()),patch('pipeline.acquire.time.sleep'):
            collect_fundamentals(Path(temp),symbols=['TEST']);out=json.loads(gzip.decompress((Path(temp)/'fundamentals/TEST.json.gz').read_bytes()))
            self.assertEqual(out['estimate_periods'],[dict(period='0y',endDate='2027-01-31')]);self.assertNotIn('private',out['info']);self.assertEqual(out['info']['lastFiscalYearEnd'],10)

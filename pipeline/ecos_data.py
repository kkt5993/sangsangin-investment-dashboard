"""Read a small public ECOS series set; keep an optional existing API key local."""
from .store import data_base
import argparse,time
import pandas as pd
import requests
from .store import DATA,read_json,write_json,digest
from .acquire import stamp
SERIES=[('KR_CPI','901Y009','M','0','한국 CPI'),('KR_LEAD','901Y067','M','I16E','한국 선행 순환변동치'),
 ('KR_COIN','901Y067','M','I16D','한국 동행 순환변동치'),('KR_BASE','722Y001','D','0101000','한국 기준금리'),
 ('KR_3Y','817Y002','D','010200000','국고채 3년'),('KR_10Y','817Y002','D','010210000','국고채 10년'),
 ('KR_AA','817Y002','D','010300000','회사채 AA- 3년'),('KR_EXPORT','901Y118','M','T002','통관 수출금액'),
 ('KR_REAL_GDP','200Y104','Q','1400','한국 실질 GDP 계절조정'),
 ('KR_CHEM_EXPORT','403Y003','M','3051AA','기초화학물질 수출물량지수'),
 ('KR_CORP_NI','501Y002','A','ZZZ00/A/270000','한국 전산업·종합 당기순손익')]
SERIES += [('KR_DEPOSIT','901Y056','M','S23A','투자자 예탁금'),('KR_MARGIN','901Y056','M','S23E','신용융자 잔고')]

def period_date(value,freq):
    return pd.Period(value,freq='Y').start_time if freq=='A' else pd.Period(value,freq='Q').start_time if freq=='Q' else pd.to_datetime(value,format='%Y%m' if freq=='M' else '%Y%m%d')
def main():
    p=argparse.ArgumentParser();p.add_argument('--key-file');p.add_argument('--as-of',default='2026-09-08');a=p.parse_args()
    from pathlib import Path
    key=read_json(Path(a.key_file)).get('ecos','sample') if a.key_file else 'sample'
    base=data_base(a.as_of)/'macro';base.mkdir(parents=True,exist_ok=True);mf=base/'manifest.json';m=read_json(mf) if mf.exists() else dict(as_of=a.as_of,instruments={})
    for symbol,stat,freq,item,name in SERIES:
        file=base/(symbol+'.csv')
        if file.exists():continue
        start='2004' if freq=='A' else '2004Q1' if freq=='Q' else '200401' if freq=='M' else '20040101'
        end=a.as_of[:4] if freq=='A' else str(pd.Period(a.as_of,freq='Q')) if freq=='Q' else a.as_of.replace('-','')[:6 if freq=='M' else 8]
        try:
            r=requests.get(f'https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/10000/{stat}/{freq}/{start}/{end}/{item}',timeout=25)
            j=r.json().get('StatisticSearch',{});rows=j.get('row',[])
            if not rows:raise ValueError('No ECOS observations')
            f=pd.DataFrame(rows);dates=f.TIME.map(lambda v:period_date(v,freq))
            out=pd.DataFrame({'observation_date':dates,symbol:pd.to_numeric(f.DATA_VALUE,errors='coerce')}).dropna().sort_values('observation_date')
            out.to_csv(file,index=False)
            m['instruments'][symbol]=dict(status='ok',source='https://ecos.bok.or.kr/',name=name,unit=f.UNIT_NAME.iloc[0],frequency=freq,stat_code=stat,item_code=item,sha256=digest(file),retrieved_at=stamp())
            print('ECOS',symbol,len(out),flush=True)
        except Exception as e:m['instruments'][symbol]=dict(status='error',error_type=type(e).__name__);print('ECOS',symbol,type(e).__name__,flush=True)
        write_json(mf,m);time.sleep(1)
if __name__=='__main__':main()

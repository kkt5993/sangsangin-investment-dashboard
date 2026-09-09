"""Explicitly authorized authenticated read of public KRX classifications only."""
from .store import data_base
import argparse,contextlib,io,time
from .store import DATA,write_json
from .acquire import stamp,budget

def main():
    p=argparse.ArgumentParser();p.add_argument('--allow-krx-auth',action='store_true');p.add_argument('--as-of',default='2026-09-08');a=p.parse_args()
    if not a.allow_krx_auth:p.error('User authorization for existing KRX authentication is required.')
    base=data_base(a.as_of);base.mkdir(parents=True,exist_ok=True)
    import requests
    original=requests.sessions.Session.request
    def bounded(self,method,url,**kwargs):
        kwargs.setdefault('timeout',25);return original(self,method,url,**kwargs)
    requests.sessions.Session.request=bounded
    # Some installed pykrx builds authenticate at import. Never expose account logs.
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        from pykrx import stock
        day=a.as_of.replace('-','')
        ids=stock.get_index_ticker_list(day,market='KOSPI')
        names={i:stock.get_index_ticker_name(i) for i in ids}
        sectors={}
        for market,suffix in [('KOSPI','.KS'),('KOSDAQ','.KQ')]:
            f=stock.get_market_sector_classifications(day,market)
            for code,row in f.iterrows():
                cap=row.get('시가총액')
                sectors[str(code)+suffix]=dict(symbol=str(code)+suffix,name=str(row.get('종목명',code)),sector=str(row.get('업종명','미분류')),exchange=market,market='KR',market_cap=int(cap) if cap is not None and cap>0 else None)
            time.sleep(1)
        for key,label in [('kr_largecap','코스피 대형주'),('kospi200','코스피 200')]:
            found=[i for i,n in names.items() if n.replace(' ','')==label.replace(' ','')]
            if len(found)!=1:raise ValueError('Official index name is ambiguous: '+label)
            code=found[0];members=stock.get_index_portfolio_deposit_file(code,day)
            result=[dict(sectors.get(str(s)+'.KS',dict(symbol=str(s)+'.KS',name=str(s),market='KR',sector='미분류')),universe=label) for s in members]
            budget();write_json(base/(key+'.json'),dict(source='https://data.krx.co.kr/',index_id=code,index_name=names[code],as_of=a.as_of,retrieved_at=stamp(),members=result))
        write_json(base/'kr_sectors.json',dict(source='https://data.krx.co.kr/',as_of=a.as_of,retrieved_at=stamp(),members=list(sectors.values())))
    print('Saved KRX Large Cap, KOSPI 200 and KRX industry classifications.')

if __name__=='__main__':main()

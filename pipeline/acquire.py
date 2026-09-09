"""Local incremental acquisition shared by every tab. Explicit execution only.

Raw caches stay outside git. No original-site request, login, paid API or schedule.
"""
from .store import data_base
import argparse
from datetime import date,datetime,timedelta,timezone
import io,json,re,time,csv
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import yfinance as yf
from .store import ROOT,DATA,digest,read_json,write_json
from .catalog import MACRO,INDICES,DYNAMICS_STOCKS,extra_price_symbols,reference_stocks


def budget(extra=0):
    n=sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())
    if n+extra>512*1024*1024:raise RuntimeError('512 MiB local budget reached; ask user before expansion.')


def stamp():return datetime.now(timezone.utc).isoformat()


def get_bytes(url):
    r=requests.get(url,timeout=25)
    r.raise_for_status();budget(len(r.content));return r.content


def collect_official_us(base):
    file=base/'ivv_holdings.csv'
    url='https://www.ishares.com/us/products/239726/ishares-core-s-p-500-etf/latest-holdings.csv'
    if not file.exists():file.write_bytes(get_bytes(url))
    content=file.read_text(encoding='utf-8-sig')
    lines=content.splitlines();header=next(i for i,l in enumerate(lines) if l.startswith('Ticker,'))
    frame=pd.read_csv(io.StringIO('\n'.join(lines[header:])))
    members=[]
    for _,r in frame.iterrows():
        if r.get('Asset Class')!='Equity' or not isinstance(r.Ticker,str):continue
        symbol=r.Ticker.replace('.','-')
        symbol={'BRKB':'BRK-B','BFB':'BF-B'}.get(symbol,symbol)
        if not re.fullmatch('[A-Z0-9-]{1,12}',symbol):continue
        members.append(dict(symbol=symbol,source_ticker=r.Ticker,name=r.Name,market='US',sector=r.Sector,universe='S&P500 (IVV disclosed equities)'))
    source_date=next(row[1] for row in csv.reader(lines[:header]) if row and row[0]=='Fund Holdings as of')
    prior=read_json(base/'us_largecap.json') if (base/'us_largecap.json').exists() else {}
    meta=dict(source=url,source_header=lines[:header],as_of=str(pd.Timestamp(source_date).date()),retrieved_at=prior.get('retrieved_at') or stamp(),sha256=digest(file),members=members)
    write_json(base/'us_largecap.json',meta)
    print('US official holdings',len(members),flush=True)


def collect_naver(base):
    members=[]
    for market,n in [('KOSPI',300),('KOSDAQ',150)]:
        rows=[]
        for page in range(1,(n+99)//100+1):
            file=base/f'{market}_marketcap_{page}.json'
            url=f'https://m.stock.naver.com/api/stocks/marketValue/{market}?page={page}&pageSize=100'
            if not file.exists():file.write_bytes(get_bytes(url));time.sleep(1)
            rows+=read_json(file)['stocks']
        for r in rows[:n]:
            name=r['stockName'];code=r['itemCode']
            if r.get('stockEndType')!='stock' or not re.fullmatch(r'\d{6}',code):continue
            if any(x in name for x in ['스팩','리츠','우B','우C']) or name.endswith('우'):continue
            members.append(dict(symbol=code+('.KS' if market=='KOSPI' else '.KQ'),name=name,market='KR',exchange=market,
                sector=None,universe='Naver market-cap screen',membership_observed_at=r.get('localTradedAt')))
    write_json(base/'kr_screen.json',dict(source='https://m.stock.naver.com/',retrieved_at=stamp(),members=members))
    print('KR market cap screen',len(members),flush=True)


def collect_prices(base,as_of,selection,symbols_override=None):
    folder=base/('stocks' if selection=='stocks' else 'prices');folder.mkdir(exist_ok=True)
    mf=folder/'manifest.json';manifest=read_json(mf) if mf.exists() else dict(provider='Yahoo Finance via yfinance',retrieved_at=stamp(),as_of=as_of,instruments={})
    long_symbols={s for _,s,_ in INDICES}|{s for s,n in DYNAMICS_STOCKS}
    members=[]
    for n in ['us_largecap','kr_largecap','kospi200','kr_screen']:
        path=base/(n+'.json')
        if path.exists():members+=read_json(path)['members']
    if selection=='core':symbols=extra_price_symbols()
    elif selection=='stocks':symbols=sorted(({m['symbol'] for m in members}|{m['symbol'] for m in reference_stocks()})-set(extra_price_symbols()))
    else:symbols=sorted(set(extra_price_symbols())|{m['symbol'] for m in members}|{m['symbol'] for m in reference_stocks()})
    if symbols_override is not None:symbols=sorted(set(symbols_override))
    start_short=str(pd.Timestamp(as_of)-pd.DateOffset(years=3))[:10]
    core_symbols=set(extra_price_symbols())
    previous_manifest=read_json(DATA/as_of/'manifest.json') if (DATA/as_of/'manifest.json').exists() else {'instruments':{}}
    for i,symbol in enumerate(symbols):
        old=manifest['instruments'].get(symbol,{})
        if old.get('status')=='error':continue
        if old.get('status')=='ok' and (folder/old['file']).exists() and digest(folder/old['file'])==old['sha256']:continue
        if selection=='core' and not old and symbol in previous_manifest['instruments']:
            prior=previous_manifest['instruments'][symbol]
            if prior.get('status')=='ok' and digest(DATA/as_of/prior['file'])==prior['sha256']:continue
        budget();time.sleep(1)
        item=dict(retrieved_at=stamp())
        start='2004-01-01' if symbol in long_symbols else ('2010-01-01' if symbol in core_symbols else start_short)
        try:
            t=yf.Ticker(symbol);f=t.history(start=start,end=str(date.fromisoformat(as_of)+timedelta(days=1)),auto_adjust=False,actions=True,repair=False,timeout=20)
            if f.empty or 'Adj Close' not in f:raise ValueError('Missing history')
            f=f.rename(columns={'Open':'open','High':'high','Low':'low','Close':'close','Adj Close':'adjusted_close','Volume':'volume','Dividends':'dividend','Stock Splits':'split'})
            f=f[['open','high','low','close','adjusted_close','volume','dividend','split']]
            f.index=f.index.tz_localize(None).normalize();f.index.name='date';f=f.loc[:as_of].dropna(subset=['close'])
            if f.empty or not f.index.is_unique or not f.index.is_monotonic_increasing or ((f.close<=0).any() and symbol!='CL=F'):raise ValueError('Invalid price series')
            dest=folder/(re.sub(r'[^A-Za-z0-9.-]','_',symbol)+'.csv.gz')
            data=f.to_csv(float_format='%.9g').encode('utf-8');import gzip;compressed=gzip.compress(data,mtime=0);budget(len(compressed));dest.write_bytes(compressed)
            meta=t.get_history_metadata()
            item.update(status='ok',file=dest.name,sha256=digest(dest),rows=len(f),first=str(f.index[0].date()),last=str(f.index[-1].date()),currency=meta.get('currency'),start_requested=start)
            print(f'PRICE {i+1}/{len(symbols)} {symbol}: {len(f)}',flush=True)
        except Exception as e:
            item.update(status='error',error_type=type(e).__name__);print(f'PRICE {symbol}: {type(e).__name__}',flush=True)
            if 'budget' in str(e):raise
        manifest['instruments'][symbol]=item;write_json(mf,manifest)


def collect_macro(base,as_of,keys=None):
    folder=base/'macro';folder.mkdir(exist_ok=True);mf=folder/'manifest.json'
    manifest=read_json(mf) if mf.exists() else dict(provider='FRED',as_of=as_of,instruments={})
    for key,(name,unit,freq) in MACRO.items():
        if keys is not None and key not in keys:continue
        file=folder/(key+'.csv')
        if file.exists() and manifest['instruments'].get(key,{}).get('status')=='ok':continue
        try:
            data=get_bytes(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={key}')
            f=pd.read_csv(io.BytesIO(data));assert key in f.columns
            file.write_bytes(data)
            manifest['instruments'][key]=dict(status='ok',name=name,unit=unit,frequency=freq,sha256=digest(file),retrieved_at=stamp())
            print('FRED',key,len(f),flush=True)
        except Exception as e:manifest['instruments'][key]=dict(status='error',error_type=type(e).__name__);print('FRED',key,type(e).__name__,flush=True)
        write_json(mf,manifest);time.sleep(1)


def collect_fundamentals(base,limit=0):
    folder=base/'fundamentals';folder.mkdir(exist_ok=True)
    # Research universe is explicit; analyst retrieval is bounded, not all 500 stocks.
    members=reference_stocks();members=members[:limit] if limit else members
    for i,m in enumerate(members):
        s=m['symbol'];file=folder/(re.sub(r'[^A-Za-z0-9.-]','_',s)+'.json')
        if file.exists() or file.with_suffix('.json.gz').exists():continue
        time.sleep(1);budget()
        out=dict(symbol=s,retrieved_at=stamp(),source='Yahoo Finance',errors=[])
        try:
            t=yf.Ticker(s)
            info=t.get_info()
            keys=['shortName','longName','sector','industry','country','marketCap','currency','financialCurrency','currentPrice','regularMarketPrice','trailingPE','forwardPE','profitMargins','operatingMargins','revenueGrowth','earningsGrowth','targetMeanPrice','recommendationMean','numberOfAnalystOpinions','totalRevenue','netIncomeToCommon','sharesOutstanding']
            out['info']={k:info.get(k) for k in keys}
            for key,func in [('annual_income',lambda:t.get_income_stmt(freq='yearly')),('quarterly_income',lambda:t.get_income_stmt(freq='quarterly')),('earnings_estimate',t.get_earnings_estimate),('revenue_estimate',t.get_revenue_estimate),('earnings_history',t.get_earnings_history)]:
                try:
                    f=func();out[key]=json.loads(f.to_json(orient='split',date_format='iso')) if f is not None and not f.empty else None
                except Exception as e:out[key]=None;out['errors'].append(key+':'+type(e).__name__)
            out['status']='ok'
        except Exception as e:out.update(status='error',error_type=type(e).__name__)
        from .events_data import save
        save(file.with_suffix('.json.gz'),out);print(f'FUND {i+1}/{len(members)} {s} {out["status"]}',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['universes','core','stocks','macro','fundamentals']);p.add_argument('--as-of',default='2026-09-08');p.add_argument('--limit',type=int,default=0);args=p.parse_args()
    if date.fromisoformat(args.as_of)>date.today():p.error('Future price date is not allowed')
    base=data_base(args.as_of);base.mkdir(parents=True,exist_ok=True)
    if args.kind=='universes':collect_official_us(base);collect_naver(base)
    elif args.kind in ['core','stocks']:collect_prices(base,args.as_of,args.kind)
    elif args.kind=='macro':collect_macro(base,args.as_of)
    else:collect_fundamentals(base,args.limit)


if __name__=='__main__':main()

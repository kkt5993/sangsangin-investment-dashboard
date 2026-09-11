"""Reuse dated company statements and earnings calendars before collecting deltas."""
import argparse
import contextlib
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import pandas as pd
from .company_news import settings
from .engine import Data
from .events_data import read, save
from .financial_modules import frame

REPORT='company_financial/collection.json.gz'


def usable_fund(raw):
    currency=raw.get('info',{}).get('financialCurrency')
    if raw.get('status')!='ok' or not isinstance(currency,str) or len(currency)!=3:return False
    for name in ['annual_income','quarterly_income']:
        f=frame(raw.get(name))
        for field in ['NetIncome','TotalRevenue']:
            if field in f.index and pd.to_numeric(f.loc[field],errors='coerce').notna().any():return True
    return False


def usable_calendar(raw):
    f=frame(raw.get('earnings_dates'))
    if not len(f):return False
    try:return all(not pd.isna(pd.Timestamp(t)) and pd.Timestamp(t).tzinfo is not None for t in f.index)
    except (TypeError,ValueError):return False


def calendars(d):
    result={}
    for base in d.bases:
        for folder in ['events','pead_events','company_events']:
            for p in (base/folder).glob('*.json.gz'):
                r=read(p);symbol=r['symbol']
                if usable_calendar(r) and (symbol not in result or r['retrieved_at']>result[symbol]['retrieved_at']):result[symbol]=r
    return result


def entity_events(d,existing):
    result={k:dict(v) for k,v in existing.items()}
    for symbol,r in calendars(d).items():
        current=result.get(symbol,{})
        if not usable_calendar(current) or r['retrieved_at']>=current.get('retrieved_at',''):
            result[symbol]={**current,'symbol':symbol,'earnings_dates':r['earnings_dates'],'retrieved_at':r['retrieved_at'],
                            'calendar_source':r.get('source_url','https://finance.yahoo.com/calendar/earnings?symbol='+quote(symbol,safe=''))}
    return result


def age(now,value):
    try:
        t=pd.Timestamp(value)
        return (now-t).total_seconds() if not pd.isna(t) and t.tzinfo is not None else float('inf')
    except (ValueError,TypeError):return float('inf')


def fetch_fund(symbol,folder):
    from .acquire import collect_fundamentals
    folder.mkdir(parents=True,exist_ok=True)
    collect_fundamentals(folder,symbols=[symbol])
    return read(folder/'fundamentals'/(symbol+'.json.gz'))


def fetch_calendar(symbol):
    import yfinance as yf
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        f=yf.Ticker(symbol).get_earnings_dates(limit=24)
    return dict(symbol=symbol,retrieved_at=datetime.now(timezone.utc).isoformat(),source='Yahoo Finance earnings dates',
                source_url='https://finance.yahoo.com/calendar/earnings?symbol='+quote(symbol,safe=''),
                earnings_dates=json.loads(f.to_json(orient='split',date_format='iso')) if f is not None and len(f) else None)


def collect(d,targets=None,fund_fetch=fetch_fund,calendar_fetch=fetch_calendar,pause=time.sleep,now=None):
    now=pd.Timestamp(now or datetime.now(timezone.utc));targets=targets if targets is not None else settings()
    prior_path=d.resource(REPORT);prior=read(prior_path) if prior_path.exists() else {}
    previous={(r['symbol'],r['kind']):r for r in prior.get('rows',[])}
    dates=calendars(d);rows=[];fetches=0
    for item in targets:
        symbol=item['symbol']
        for kind,old,days in [('financial',d.fund.get(symbol,{}),7),('calendar',dates.get(symbol,{}),3)]:
            if kind=='calendar' and symbol.endswith(('.KS','.KQ')):continue
            valid=usable_fund if kind=='financial' else usable_calendar
            row=dict(symbol=symbol,kind=kind,checked_at=now.isoformat(),retrieved_at=old.get('retrieved_at'))
            if valid(old) and 0<=age(now,old.get('retrieved_at'))<days*86400:
                rows.append(dict(row,status='reused'));continue
            before=previous.get((symbol,kind),{})
            if before.get('status') in ['retained','missing','backoff'] and 0<=age(now,before.get('attempted_at'))<3600:
                rows.append(dict(row,status='backoff',attempted_at=before['attempted_at'],error_type=before.get('error_type')));continue
            row['attempted_at']=now.isoformat();fetches+=1
            try:
                if kind=='financial':
                    attempt=d.base/'company_financial/attempts'/now.strftime('%Y%m%dT%H%M%S%fZ')/symbol
                    raw=fund_fetch(symbol,attempt)
                else:raw=calendar_fetch(symbol)
                if not valid(raw) or raw.get('symbol')!=symbol or not 0<=age(now,raw.get('retrieved_at'))<days*86400+60:
                    # Real acquisition timestamps may follow this batch start.
                    if not (valid(raw) and raw.get('symbol')==symbol and -3600<age(now,raw.get('retrieved_at'))<0):raise ValueError('Invalid or empty provider observation')
                if kind=='financial' and raw.get('errors') and valid(old):raise ValueError('Partial refresh retained previous complete observation')
                folder='fundamentals' if kind=='financial' else 'company_events'
                save(d.base/folder/(symbol+'.json.gz'),raw)
                if kind=='financial':d.fund[symbol]=raw
                else:dates[symbol]=raw
                row.update(status='collected',retrieved_at=raw['retrieved_at'],partial=bool(raw.get('errors')))
            except Exception as error:row.update(status='retained' if valid(old) else 'missing',error_type=type(error).__name__)
            rows.append(row)
            save(d.base/REPORT,dict(checked_at=now.isoformat(),fetches=fetches,rows=rows))
            print('COMPANY',kind,symbol,row['status'],flush=True);pause(1)
    report=dict(checked_at=now.isoformat(),fetches=fetches,expected=len(targets),rows=rows,
                status='partial' if any(r['status'] in ['retained','missing','backoff'] or r.get('partial') for r in rows) else 'ok')
    save(d.base/REPORT,report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();collect(Data(a.as_of))

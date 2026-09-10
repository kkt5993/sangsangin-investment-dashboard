"""Small earnings-date deltas for the official S&P100 stock membership."""
import argparse
import contextlib
import io
import json
import time
from datetime import datetime, timezone
import pandas as pd
from .engine import Data
from .events_data import read, save
from .financial_modules import frame
from .acquire import stamp


def usable(raw):
    f=frame(raw.get('earnings_dates'))
    if not len(f) or not {'Reported EPS','Surprise(%)'}<=set(f.columns):return False
    try:return all(pd.Timestamp(t).tzinfo is not None for t in f.index)
    except (ValueError,TypeError):return False


def sources(d):
    result={}
    for base in d.bases:
        for directory in ['events','pead_events']:
            for p in (base/directory).glob('*.json.gz'):
                raw=read(p);symbol=raw['symbol']
                if usable(raw) and (symbol not in result or raw['retrieved_at']>result[symbol]['retrieved_at']):result[symbol]=raw
    return result


def collect(d,fetch=None,pause=time.sleep,now=None):
    """Reuse <=3-day observations; a failed refresh cannot replace good history."""
    if fetch is None:
        import yfinance as yf
        def fetch(symbol):
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                return yf.Ticker(symbol).get_earnings_dates(limit=24)
    now=pd.Timestamp(now or datetime.now(timezone.utc));prior=sources(d);rows=[]
    members=d.members.get('us100',{}).get('members',[])
    if not members:raise ValueError('Official S&P100 membership is required')
    for m in members:
        symbol=m['symbol'];old=prior.get(symbol);age=(now-pd.Timestamp(old['retrieved_at'])).total_seconds()/86400 if old else None
        if age is not None and 0<=age<=3:
            rows.append(dict(symbol=symbol,status='reused',retrieved_at=old['retrieved_at']));continue
        try:
            f=fetch(symbol)
            raw=dict(symbol=symbol,retrieved_at=stamp(),source='Yahoo Finance earnings dates',source_url='https://finance.yahoo.com/calendar/earnings?symbol='+symbol,
                     earnings_dates=json.loads(f.to_json(orient='split',date_format='iso')) if f is not None and len(f) else None)
            if not usable(raw):raise ValueError('Empty or invalid earnings-date response')
            save(d.base/'pead_events'/(symbol+'.json.gz'),raw)
            rows.append(dict(symbol=symbol,status='collected',retrieved_at=raw['retrieved_at']))
        except Exception as error:
            rows.append(dict(symbol=symbol,status='retained' if old else 'missing',retrieved_at=old['retrieved_at'] if old else None,error_type=type(error).__name__))
        print('PEAD EVENTS',symbol,rows[-1]['status'],flush=True);pause(.7)
    report=dict(retrieved_at=stamp(),as_of=d.as_of,universe='us100',expected=len(members),rows=rows,
                status='partial' if any(r['status'] in ['missing','retained'] for r in rows) else 'ok')
    save(d.base/'pead_collection.json.gz',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();collect(Data(a.as_of))

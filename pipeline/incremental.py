"""Refresh Yahoo bars as small run deltas, never replace the base vintage."""
import contextlib,io,logging,time
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import yfinance as yf
from .cache import make_patch
from .events_data import save,read
from .engine import clean_json
from .store import digest,write_json
from .acquire import stamp

def completed_date(symbol,as_of,now=None):
    """Conservative daily-bar cutoff: 18:00 exchange local time, UTC for crypto.

    Weekends are skipped, while exchange holidays are left to provider bars.
    The two Korean scheduled runs never include an open US/European session.
    """
    now=now or datetime.now(ZoneInfo('UTC'))
    if now.tzinfo is None:raise ValueError('Timezone-aware collection time required')
    if symbol.endswith('-USD'):
        day=now.astimezone(ZoneInfo('UTC')).date()-timedelta(days=1)
        return min(day.isoformat(),as_of)
    zones={'.KS':'Asia/Seoul','.KQ':'Asia/Seoul','.T':'Asia/Tokyo','.TW':'Asia/Taipei','.HK':'Asia/Hong_Kong','.DE':'Europe/Berlin','.PA':'Europe/Paris','.L':'Europe/London','.NS':'Asia/Kolkata','.AX':'Australia/Sydney'}
    zone=next((v for suffix,v in zones.items() if symbol.endswith(suffix)),'America/New_York')
    local=now.astimezone(ZoneInfo(zone));day=local.date()
    if local.hour<18:day-=timedelta(days=1)
    day=min(day,pd.Timestamp(as_of).date())
    while day.weekday()>=5:day-=timedelta(days=1)
    return day.isoformat()

def valid_frame(f,symbol):
    if f.empty or not f.index.is_unique or not f.index.is_monotonic_increasing:raise ValueError('Invalid price dates')
    if not np.isfinite(f[['open','high','low','close','adjusted_close']].to_numpy()).all():raise ValueError('Invalid price observations')
    if (f.close<=0).any() and symbol!='CL=F':raise ValueError('Non-positive price')
    if (f.volume<0).any():raise ValueError('Negative volume')
    # Korean OHLC inconsistencies are reconciled with KRX before publication.
    return f

def universe_symbols(members):
    # kr_sectors is the classification dictionary for the entire exchange; it
    # must not silently turn a large-cap refresh into an all-listings download.
    return {m['symbol'] for key in ['kr_largecap','kospi200','us_largecap','kr_screen'] for m in members.get(key,{}).get('members',[]) if 'symbol' in m}

def prices(parent,base,as_of,members=None,now=None):
    dest=base/'price_delta.json.gz';out=read(dest) if dest.exists() else dict(as_of=as_of,instruments={},attempts={})
    logging.getLogger('yfinance').setLevel(logging.CRITICAL)
    now=now or datetime.now(ZoneInfo('UTC'))
    from .catalog import DETAIL_PRICES
    wanted=universe_symbols(members or parent.members)|set(DETAIL_PRICES)
    # Newly disclosed constituents get one bounded 3-year history. Subsequent
    # runs add only changed bars. Unavailable tickers remain explicit coverage gaps.
    additions=sorted(wanted-set(parent.frames))[:25]
    symbols=sorted(set(parent.frames)|set(additions))
    def checkpoint():
        save(dest,out);write_json(base/'price_delta_manifest.json',dict(sha256=digest(dest),as_of=as_of,updated_at=stamp()))
    for i,symbol in enumerate(symbols):
        old=parent.frames.get(symbol);cutoff=completed_date(symbol,as_of,now)
        if (old is not None and str(old.index[-1].date())>=cutoff) or symbol in out['attempts']:continue
        start=str(((old.index[-1]-pd.Timedelta(days=35)) if old is not None else pd.Timestamp(cutoff)-pd.DateOffset(years=3)).date());ticker=yf.Ticker(symbol)
        end=str((pd.Timestamp(cutoff)+pd.Timedelta(days=1)).date())
        try:
            def fetch(start):
                with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                    f=ticker.history(start=start,end=end,auto_adjust=False,actions=True,repair=False,timeout=20)
                if f.empty:raise ValueError('No price observations')
                f=f.rename(columns={'Open':'open','High':'high','Low':'low','Close':'close','Adj Close':'adjusted_close','Volume':'volume','Dividends':'dividend','Stock Splits':'split'})
                f=f[['open','high','low','close','adjusted_close','volume','dividend','split']];f.index=f.index.tz_localize(None).normalize();f.index.name='date'
                return valid_frame(f.loc[:cutoff].dropna(subset=['close','adjusted_close']),symbol)
            new=fetch(start);patch=make_patch(old,new) if old is not None else None
            if patch is None:
                if old is not None:new=fetch(str(old.index[0].date()))
                patch=dict(mode='full',columns=list(new.columns),dates=[str(t.date()) for t in new.index],data=new.to_numpy().tolist())
            if patch['dates'] or any(v!=1 for v in patch.get('scale',{}).values()):out['instruments'][symbol]=clean_json(dict(patch,retrieved_at=stamp()))
            out['attempts'][symbol]=dict(status='ok',last_date=str(new.index[-1].date()))
        except Exception as e:out['attempts'][symbol]=dict(status='error',error_type=type(e).__name__)
        if i%25==0:checkpoint();print('INCREMENTAL',i+1,len(symbols),flush=True)
        time.sleep(.7)
    checkpoint();attempts=list(out['attempts'].values());failed=sum(a['status']=='error' for a in attempts)
    if len(attempts)>=20 and failed/len(attempts)>.1:raise RuntimeError('Price provider failure exceeds 10%; publication stopped')
    return dict(attempted=len(attempts),changed=len(out['instruments']),failed=failed,new_requested=len(additions),new_deferred=max(0,len(wanted-set(parent.frames))-len(additions)))

"""Licensed/imported option snapshots; all supplied 7–50D expiries within ±15%."""
import argparse,json,math,re,time
import pandas as pd
from .acquire import get_bytes
from .events_data import save,read
from .engine import Data

SCOPE=dict(version=2,min_dte=7,max_dte=50,strike_band=.15,expiry_cap=None,
           expiry_time='16:00 America/New_York model convention',multiplier=100)
# The separate stock-flow model retains its original sampling contract.
FLOW_SCOPE=dict(SCOPE,version=1,max_dte=45,strike_band=None,expiry_cap=3)

def parse_contracts(raw,symbol):
    spot=float(raw['data']['current_price'])
    if raw.get('symbol')!=symbol or not math.isfinite(spot) or spot<=0:raise ValueError('Unexpected option underlying')
    parsed=[]
    for r in raw['data']['options']:
        m=re.fullmatch(re.escape(symbol)+r'(\d{6})([CP])(\d{8})',r['option'])
        if not m:continue
        expiry=pd.to_datetime(m[1],format='%y%m%d').strftime('%Y-%m-%d')
        parsed.append(dict(contractSymbol=r['option'],strike=int(m[3])/1000,side='call' if m[2]=='C' else 'put',expiry=expiry,bid=r.get('bid'),ask=r.get('ask'),impliedVolatility=r.get('iv'),openInterest=r.get('open_interest'),volume=r.get('volume'),lastTradeDate=r.get('last_trade_time'),contractSize='REGULAR'))
    return parsed

def normalize(raw,symbol,now=None,scope=None):
    scope=dict(SCOPE if scope is None else scope)
    now=pd.Timestamp(now or pd.Timestamp.now(tz='UTC'));data=raw['data'];spot=float(data['current_price'])
    if now.tzinfo is None:raise ValueError('Acquisition time must include a timezone')
    all_rows=parse_contracts(raw,symbol)
    if len({r['contractSymbol'] for r in all_rows})!=len(all_rows):raise ValueError('Duplicate option contracts')
    band=scope['strike_band']
    # Compare strike ratios with a tiny arithmetic tolerance at inclusive edges.
    records=[r for r in all_rows if scope['min_dte']<=(pd.Timestamp(r['expiry']+' 16:00',tz='America/New_York')-now).total_seconds()/86400<=scope['max_dte'] and r['strike']>0 and (band is None or abs(r['strike']/spot-1)<=band+1e-12)]
    if scope['expiry_cap']:
        selected=set(sorted({r['expiry'] for r in records})[:scope['expiry_cap']])
        records=[r for r in records if r['expiry'] in selected]
    records.sort(key=lambda r:(r['expiry'],r['strike'],r['side']))
    expiries=sorted({r['expiry'] for r in records})
    near=[r for r in records if .9*spot<=r['strike']<=1.1*spot]
    positive=[r for r in near if (r.get('openInterest') or 0)>0]
    if len(expiries)<3 or len(positive)<20 or {r['side'] for r in positive}!={'call','put'}:raise ValueError('Insufficient Cboe near-ATM open interest coverage')
    return dict(symbol=symbol,retrieved_at=now.isoformat(),source='Cboe delayed option observation',provider_timestamp=raw.get('timestamp'),provider_timestamp_timezone='not supplied by endpoint',underlying_price=spot,expiries=expiries,records=records,scope=scope,quality=dict(atm_contracts=len(near),atm_positive_oi=len(positive),source_contracts=len(data['options']),scope_complete=scope['expiry_cap'] is None,selected_contracts=len(records),selected_expiries=len(expiries)))


def collect(d,allow_download=False,fetch=None):
    """Automatic access needs explicit source permission; old data stay dated."""
    fetch=fetch or (lambda s:json.loads(get_bytes('https://cdn.cboe.com/api/global/delayed_quotes/options/'+s+'.json')))
    rows=[]
    for symbol in ['SPY','QQQ','IWM']:
        prior=d.resource('options/'+symbol+'.json.gz');old=read(prior) if prior.exists() else None
        if not allow_download:
            rows.append(dict(symbol=symbol,status='retained_permission_required' if old else 'missing_permission_required',retrieved_at=old.get('retrieved_at') if old else None));continue
        dest=d.base/'options'/(symbol+'.json.gz')
        if dest.exists():
            rows.append(dict(symbol=symbol,status='reused_current_run',retrieved_at=read(dest)['retrieved_at']));continue
        try:
            raw=fetch(symbol);now=pd.Timestamp.now(tz='UTC');out=normalize(raw,symbol,now)
            save(d.base/'option_sources'/(symbol+'.json.gz'),dict(retrieved_at=now.isoformat(),payload=raw))
            save(dest,out);rows.append(dict(symbol=symbol,status='collected',retrieved_at=out['retrieved_at']))
        except Exception as error:
            rows.append(dict(symbol=symbol,status='retained_error' if old else 'missing_error',retrieved_at=old.get('retrieved_at') if old else None,error_type=type(error).__name__))
        print('OPTIONS',symbol,rows[-1]['status'],flush=True);time.sleep(1)
    report=dict(retrieved_at=pd.Timestamp.now(tz='UTC').isoformat(),status='ok' if all(r['status'] in ['collected','reused_current_run'] for r in rows) else 'partial',automatic_access_authorized=allow_download,rows=rows)
    save(d.base/'option_collection.json.gz',report)
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default='2026-09-08');p.add_argument('--allow-cboe-download',action='store_true');a=p.parse_args()
    collect(Data(a.as_of),allow_download=a.allow_cboe_download)

if __name__=='__main__':main()

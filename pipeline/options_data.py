"""Cboe delayed quotes: retain three expiries and verify near-ATM OI coverage."""
import argparse,json,re,time
import pandas as pd
from .store import data_base
from .acquire import get_bytes
from .events_data import save,read

def normalize(raw,symbol,now=None):
    now=now or pd.Timestamp.now(tz='UTC');data=raw['data'];spot=float(data['current_price'])
    if raw.get('symbol')!=symbol or spot<=0:raise ValueError('Unexpected option underlying')
    parsed=[]
    for r in data['options']:
        m=re.fullmatch(re.escape(symbol)+r'(\d{6})([CP])(\d{8})',r['option'])
        if not m:continue
        expiry=pd.to_datetime(m[1],format='%y%m%d').strftime('%Y-%m-%d')
        t=(pd.Timestamp(expiry+' 16:00',tz='America/New_York')-now).total_seconds()/86400
        if not 7<=t<=45:continue
        parsed.append(dict(contractSymbol=r['option'],strike=int(m[3])/1000,side='call' if m[2]=='C' else 'put',expiry=expiry,bid=r.get('bid'),ask=r.get('ask'),impliedVolatility=r.get('iv'),openInterest=r.get('open_interest'),volume=r.get('volume'),lastTradeDate=r.get('last_trade_time'),contractSize='REGULAR'))
    expiries=sorted({r['expiry'] for r in parsed})[:3];records=[r for r in parsed if r['expiry'] in expiries]
    near=[r for r in records if .9*spot<=r['strike']<=1.1*spot]
    positive=[r for r in near if (r.get('openInterest') or 0)>0]
    if len(expiries)<3 or len(positive)<20 or {r['side'] for r in positive}!={'call','put'}:raise ValueError('Insufficient Cboe near-ATM open interest coverage')
    return dict(symbol=symbol,retrieved_at=now.isoformat(),source='Cboe public delayed option quotes',provider_timestamp=raw.get('timestamp'),provider_timestamp_timezone='not supplied by endpoint',underlying_price=spot,expiries=expiries,records=records,quality=dict(atm_contracts=len(near),atm_positive_oi=len(positive),source_contracts=len(data['options'])))

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default='2026-09-08');a=p.parse_args();base=data_base(a.as_of);folder=base/'options';folder.mkdir(exist_ok=True)
    for symbol in ['SPY','QQQ','IWM']:
        dest=folder/(symbol+'.json.gz')
        if dest.exists():continue
        probe=base/('cboe_'+symbol.lower()+'_probe.json.gz')
        raw=read(probe) if probe.exists() else json.loads(get_bytes('https://cdn.cboe.com/api/global/delayed_quotes/options/'+symbol+'.json'))
        out=normalize(raw,symbol);save(dest,out);print('CBOE OPTIONS',symbol,len(out['records']),'contracts / positive ATM OI',out['quality']['atm_positive_oi'],flush=True);time.sleep(1)

if __name__=='__main__':main()

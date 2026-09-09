"""Bounded public option snapshots: three expiries per ETF, no orders."""
from .store import data_base
import argparse,gzip,json,time
import yfinance as yf
import pandas as pd
from .store import DATA
from .acquire import stamp,budget
def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default='2026-09-08');a=p.parse_args();base=data_base(a.as_of)/'options';base.mkdir(exist_ok=True)
    for symbol in ['SPY','QQQ','IWM']:
        dest=base/(symbol+'.json.gz')
        if dest.exists():continue
        t=yf.Ticker(symbol);now=pd.Timestamp.now(tz='UTC');all_exp=t.options
        dates=[e for e in all_exp if 7<=(pd.Timestamp(e,tz='America/New_York')-now).days<=45][:3]
        records=[]
        for expiry in dates:
            chain=t.option_chain(expiry)
            for side,f in [('call',chain.calls),('put',chain.puts)]:
                cols=['contractSymbol','strike','bid','ask','impliedVolatility','openInterest','volume','lastTradeDate','contractSize'];g=f[[k for k in cols if k in f]].copy();g['side']=side;g['expiry']=expiry
                records+=json.loads(g.to_json(orient='records',date_format='iso'))
            time.sleep(1)
        raw=json.dumps(dict(symbol=symbol,retrieved_at=stamp(),source='Yahoo Finance public option chains',expiries=dates,records=records),allow_nan=False).encode();compressed=gzip.compress(raw,mtime=0);budget(len(compressed));dest.write_bytes(compressed);print('OPTIONS',symbol,len(records),'contracts',len(compressed),'bytes',flush=True)
if __name__=='__main__':main()

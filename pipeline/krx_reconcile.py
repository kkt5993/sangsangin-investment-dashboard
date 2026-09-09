"""Reconcile inconsistent Korean OHLC using bounded official cross-sectional reads."""
import argparse,contextlib,io,gzip,json,time
import numpy as np
from .engine import Data,clean_json
from .store import DATA
from .acquire import stamp,budget
def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default='2026-09-08');p.add_argument('--allow-krx-auth',action='store_true');a=p.parse_args()
    if not a.allow_krx_auth:p.error('Existing KRX account authorization is required.')
    d=Data(a.as_of);dest=d.base/'price_corrections.json.gz'
    corrections=json.loads(gzip.decompress(dest.read_bytes())) if dest.exists() else dict(source='KRX public market OHLC',retrieved_at=stamp(),records=[])
    known={(r['symbol'],r['date']) for r in corrections['records']};bad={}
    for s,f in d.frames.items():
        if not s.endswith(('.KS','.KQ')) or 'high' not in f:continue
        mask=(f.high+1e-5<f[['open','close']].max(axis=1))|(f.low-1e-5>f[['open','close']].min(axis=1))
        for t,row in f[mask].iterrows():
            if (s,str(t.date())) not in known:bad.setdefault(('KOSPI' if s.endswith('.KS') else 'KOSDAQ',str(t.date())),[]).append((s,row))
    if not bad:print('No new Korean OHLC anomalies');return
    import requests
    original=requests.sessions.Session.request
    def bounded(self,method,url,**kw):kw.setdefault('timeout',25);return original(self,method,url,**kw)
    requests.sessions.Session.request=bounded
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        from pykrx import stock
        for (market,day),items in sorted(bad.items()):
            official=stock.get_market_ohlcv_by_ticker(day.replace('-',''),market=market)
            for symbol,row in items:
                code=symbol.split('.')[0];mapping={'open':'시가','high':'고가','low':'저가','close':'종가'}
                if code not in official.index:
                    f=stock.get_etf_ohlcv_by_date(day.replace('-',''),day.replace('-',''),code)
                    o=f.iloc[0] if len(f) else None
                else:o=official.loc[code]
                record=dict(symbol=symbol,date=day,original={k:row[k] for k in [*mapping,'adjusted_close']})
                if o is None or any(o.get(k,0)<=0 for k in mapping.values()):record.update(status='quarantined',reason='No official matching OHLC')
                else:
                    ratios=[row[k]/o[v] for k,v in mapping.items() if k!='close'];factor=float(np.median(ratios))
                    if max(ratios)/min(ratios)>1.002:record.update(status='quarantined',reason='Historical split scale could not be reconciled')
                    else:
                        values={k:float(o[v])*factor for k,v in mapping.items()};values['adjusted_close']=float(row.adjusted_close/row.close*values['close'])
                        record.update(status='corrected',values=values,official={k:float(o[v]) for k,v in mapping.items()},split_scale=factor,reason='KRX OHLC with verified Yahoo split scale; dividend adjustment factor preserved')
                corrections['records'].append(clean_json(record))
            raw=json.dumps(corrections,ensure_ascii=False,allow_nan=False).encode();compressed=gzip.compress(raw,mtime=0);budget(len(compressed));dest.write_bytes(compressed);time.sleep(1)
    print('KRX reconciliation',len(corrections['records']),'rows; corrected',sum(r['status']=='corrected' for r in corrections['records']),'quarantined',sum(r['status']=='quarantined' for r in corrections['records']))
if __name__=='__main__':main()

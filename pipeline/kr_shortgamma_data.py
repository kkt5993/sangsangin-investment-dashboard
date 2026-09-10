"""Authorized, bounded KRX index/ETF definitions/expiry reads; raw stays local."""
import argparse
import contextlib
import io
import re
import time
import pandas as pd
from .acquire import stamp
from .engine import Data
from .events_data import read, save

FOLDER='kr_shortgamma/'
BENCHMARKS={'코스피200':'spot','코스피200선물지수':'futures'}


def numeric(value):
    try:
        x=float(str(value).replace(',',''))
        return x if pd.notna(x) and abs(x)<float('inf') else None
    except (ValueError,TypeError):return None


def index_rows(rows,as_of):
    """Preserve official points, rejecting malformed OHLC and conflicting dates."""
    out={}
    for r in rows:
        date=pd.Timestamp(r['TRD_DD']).strftime('%Y-%m-%d')
        if date>as_of:raise ValueError('Future KRX index observation')
        row=dict(date=date,**{k:numeric(r[v]) for k,v in {'open':'OPNPRC_IDX','high':'HGPRC_IDX','low':'LWPRC_IDX','close':'CLSPRC_IDX'}.items()})
        if any(row[k] is None or row[k]<=0 for k in ['open','high','low','close']):raise ValueError('Missing KRX OHLC')
        if row['low']>min(row['open'],row['close']) or row['high']<max(row['open'],row['close']):raise ValueError('Inconsistent KRX OHLC')
        if date in out and out[date]!=row:raise ValueError('Conflicting KRX date')
        out[date]=row
    return sorted(out.values(),key=lambda r:r['date'])


def history(d):
    out={}
    for base in d.bases:
        p=base/FOLDER/'index.json.gz'
        if p.exists():
            # Later official observations replace earlier overlapping dates.
            for r in index_rows(read(p)['rows'],d.as_of):out[r['date']]=r
    return sorted(out.values(),key=lambda r:r['date'])


def definitions(raw,as_of):
    out=[]
    for r in raw.get('rows',[]):
        benchmark=re.sub(r'\s','',r['ETF_OBJ_IDX_NM'])
        if benchmark not in BENCHMARKS:continue
        listed=pd.Timestamp(r['LIST_DD']).strftime('%Y-%m-%d')
        if listed>as_of:continue
        label=r['IDX_CALC_INST_NM2'].strip()
        if label.startswith('일반'):continue
        m=re.fullmatch(r'([123])X (레버리지|인버스)(?: \([-+\d]+\))?',label)
        leverage=int(m[1])*(-1 if m[2]=='인버스' else 1) if m else None
        out.append(dict(code=r['ISU_SRT_CD'],name=r['ISU_ABBRV'],benchmark=r['ETF_OBJ_IDX_NM'],kind=BENCHMARKS[benchmark],leverage=leverage,leverage_label=label,listed_at=listed))
    if len({r['code'] for r in out})!=len(out):raise ValueError('Duplicate ETF definition')
    return out


def expiry_dates(raw):
    out=set()
    for r in raw.get('rows',[]):
        if not re.match(r'코스피200 [CP] \d{6}\s',r['ISU_NM']):raise ValueError('Unexpected option product')
        if numeric(r['SETLMULT'])!=250000:raise ValueError('Unexpected KOSPI200 contract multiplier')
        date=pd.Timestamp(r['LSTTRD_DD']).strftime('%Y-%m-%d')
        if pd.Timestamp(r['LIST_DD'])>pd.Timestamp(date):raise ValueError('Invalid option listing date')
        out.add(date)
    return sorted(out)


def collect(d):
    import requests
    previous=history(d)
    start=(pd.Timestamp(previous[-1]['date'])-pd.Timedelta(days=10) if previous else pd.Timestamp(d.as_of)-pd.DateOffset(years=3)).strftime('%Y%m%d')
    tasks=[];results=[]
    for part in ['index','etf_definitions','expiries']:
        dest=d.base/FOLDER/(part+'.json.gz');prior=d.resource(FOLDER+part+'.json.gz')
        raw=read(prior) if prior.exists() else {}
        fresh=raw and pd.Timestamp(stamp())-pd.Timestamp(raw['retrieved_at'])<pd.Timedelta(days=7)
        same_index=part=='index' and previous and previous[-1]['date']==d.as_of
        if dest.exists() or same_index or (part!='index' and fresh):
            results.append(dict(part=part,status='reused',retrieved_at=raw.get('retrieved_at')))
        else:tasks.append((part,dest))
    original=requests.sessions.Session.request
    def bounded(self,method,url,**kwargs):
        kwargs.setdefault('timeout',25)
        return original(self,method,url,**kwargs)
    requests.sessions.Session.request=bounded
    try:
        # Installed pykrx authenticates at import and may log account details.
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            if tasks:
                from pykrx.website.krx.etx.core import ETF_전종목기본종목
                from pykrx.website.krx.market.core import 개별지수시세
                from pykrx.website.krx.future.core import 전종목기본정보
            for part,dest in tasks:
                try:
                    if part=='index':f=개별지수시세().fetch('028','1',start,d.as_of.replace('-',''))
                    elif part=='etf_definitions':f=ETF_전종목기본종목().fetch()
                    else:f=전종목기본정보().fetch('KRDRVOPK2I')
                    if f.empty:raise ValueError('Empty KRX response')
                    packet=dict(source='https://data.krx.co.kr/',retrieved_at=stamp(),requested_as_of=d.as_of,rows=f.to_dict('records'))
                    if part=='index':
                        rows=index_rows(packet['rows'],d.as_of)
                        if not rows or (pd.Timestamp(d.as_of)-pd.Timestamp(rows[-1]['date'])).days>7:raise ValueError('Stale KRX index response')
                        prior_rows={r['date']:r for r in previous}
                        changed={r['date'] for r in rows if prior_rows.get(r['date'])!=r}
                        packet['rows']=[r for r in packet['rows'] if pd.Timestamp(r['TRD_DD']).strftime('%Y-%m-%d') in changed]
                    elif part=='etf_definitions':
                        if len(definitions(packet,d.as_of))<10:raise ValueError('ETF definition coverage failure')
                    elif not expiry_dates(packet):raise ValueError('Missing official expiries')
                    save(dest,packet)
                    results.append(dict(part=part,status='ok',rows=len(packet['rows']),retrieved_at=packet['retrieved_at']))
                except Exception as e:
                    results.append(dict(part=part,status='error',error_type=type(e).__name__))
                time.sleep(.7)
    finally:requests.sessions.Session.request=original
    report=dict(retrieved_at=stamp(),requested_as_of=d.as_of,parts=results)
    save(d.base/FOLDER/'collection.json.gz',report)
    print('KR short-gamma inputs',[(r['part'],r['status']) for r in results],flush=True)
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);p.add_argument('--allow-krx-auth',action='store_true');a=p.parse_args()
    if not a.allow_krx_auth:p.error('Existing KRX account authorization required')
    collect(Data(a.as_of))


if __name__=='__main__':main()

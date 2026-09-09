"""Offline shared analytical primitives. Prices are never silently forward filled."""
from datetime import datetime,timezone
import json,math
import numpy as np
import pandas as pd
from .store import DATA,ROOT,digest,read_json,write_json

def number(x):
    try:return round(float(x),6) if np.isfinite(float(x)) else None
    except (ValueError,TypeError):return None

def clean_json(obj):
    if isinstance(obj,dict):return {str(k):clean_json(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple,np.ndarray)):return [clean_json(v) for v in obj]
    if isinstance(obj,(float,np.floating)):return number(obj)
    if isinstance(obj,np.integer):return int(obj)
    if isinstance(obj,(pd.Timestamp,datetime)):return obj.isoformat()[:10]
    return obj

def points(s,n=600):
    s=s.dropna()
    if len(s)>n:s=s.iloc[np.unique(np.linspace(0,len(s)-1,n,dtype=int))]
    return [[str(d.date()),number(v)] for d,v in s.items() if number(v) is not None]

def ret(s,n):return number((s.iloc[-1]/s.iloc[-n-1]-1)*100) if len(s)>n and s.iloc[-n-1]>0 else None

def ytd(s):
    b=s.loc[:str(s.index[-1].year-1)] if len(s) else s
    return number((s.iloc[-1]/b.iloc[-1]-1)*100) if len(b) else None

def rsi(s,n=14):
    d=s.diff();up=d.clip(lower=0).ewm(alpha=1/n,adjust=False,min_periods=n).mean();dn=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    result=100-100/(1+up/dn.replace(0,np.nan))
    return result.mask((dn==0)&(up>0),100).mask((dn==0)&(up==0),50)

def zscore(s,n=252,min_periods=None):
    r=s.rolling(n,min_periods=min_periods or n);return (s-r.mean())/r.std(ddof=0).replace(0,np.nan)

def expanding_z(s,n=252):
    return (s-s.expanding(n).mean())/s.expanding(n).std(ddof=0).replace(0,np.nan)

def observed_resample(s,freq='ME'):
    """Plot a partial period at its last actual observation, never a future date."""
    out=s.resample(freq).last().dropna()
    if len(out) and len(s) and out.index[-1]>s.index[-1]:out=out.rename(index={out.index[-1]:s.index[-1]})
    return out

def performance(r):
    r=r.dropna();wealth=(1+r).cumprod()
    if not len(r):return {}
    years=len(r)/252;vol=r.std(ddof=1)*np.sqrt(252)
    return dict(cagr=number((wealth.iloc[-1]**(1/years)-1)*100),vol=number(vol*100),sharpe=number(r.mean()*252/vol) if vol else None,mdd=number((wealth/wealth.cummax().clip(lower=1)-1).min()*100),sessions=len(r))

def monthly_portfolio(returns,targets,cost_bps=5):
    """Use previous-close targets on the first session, drift holdings in between."""
    result={};held=None;previous_month=None
    for i,t in enumerate(returns.index):
        if i==0 or returns.iloc[i].isna().any():continue
        month=(t.year,t.month);fee=0.
        if month!=previous_month and targets.iloc[i-1].notna().all():
            target=targets.iloc[i-1].to_numpy(dtype=float)
            fee=float(np.abs(target-(held if held is not None else np.zeros_like(target))).sum())*cost_bps/10000
            held=target.copy()
        previous_month=month
        if held is None:continue
        growth=held*(1+returns.iloc[i].to_numpy(dtype=float));gross=float(growth.sum())
        result[t]=gross-1-fee;held=growth/gross
    return pd.Series(result,dtype=float)

def curve(title,series,left='',right='',guides=None,limits=None,n=480):
    # Each series owns its date axis. Absent observations remain absent.
    return dict(type='line',title=title,left=left,right=right,guides=guides or [],limits=limits,
        series=[dict(name=name,points=points(s,n),axis=axis) for name,s,axis in series])

def bars(title,rows,unit='%'):return dict(type='bars',title=title,unit=unit,rows=[dict(name=n,value=number(v)) for n,v in rows])

def table(title,columns,rows):return dict(type='table',title=title,columns=columns,rows=rows)

def heat(title,columns,rows):return dict(type='heatmap',title=title,columns=columns,rows=rows)

def module(key,as_of,note,sections,cards=None,status='partial',missing=None):
    return dict(schema_version=2,module=key,as_of=as_of,generated_at=datetime.now(timezone.utc).isoformat(),status=status,
        source='KRX · iShares · Yahoo Finance · FRED (각 계산의 출처·기준일은 데이터 설명 참조)',
        method_note=note,missing=missing or [],cards=cards or [],sections=sections)

class Data:
    def __init__(self,as_of):
        self.as_of=as_of;self.base=DATA/'expanded'/as_of;self.frames={};self.macro={};self.quality={};self.members={};self.fund={}
        for folder in [DATA/as_of,self.base/'stocks',self.base/'prices']:
            mf=folder/'manifest.json'
            if not mf.exists():continue
            for s,m in read_json(mf)['instruments'].items():
                if m.get('status')!='ok':continue
                file=folder/m['file']
                if file.parent.resolve()!=folder.resolve() or digest(file)!=m['sha256']:raise ValueError('Cache checksum: '+s)
                f=pd.read_csv(file,index_col='date',parse_dates=['date']).loc[:as_of]
                if len(f) and (pd.Timestamp(as_of)-f.index[-1]).days<=7:self.frames[s]=f;self.quality[s]=m
        for key in ['kr_largecap','kospi200','us_largecap','kr_screen','kr_sectors']:
            path=self.base/(key+'.json')
            if path.exists():self.members[key]=read_json(path)
        import gzip
        correction_file=self.base/'price_corrections.json.gz';self.corrections=[];self.correction_meta={}
        if correction_file.exists():
            self.corrections=json.loads(gzip.decompress(correction_file.read_bytes()))['records']
            self.correction_meta=dict(source='KRX official OHLC reconciliation',sha256=digest(correction_file),corrected=sum(r['status']=='corrected' for r in self.corrections),quarantined=sum(r['status']=='quarantined' for r in self.corrections))
            for correction in self.corrections:
                s=correction['symbol'];t=pd.Timestamp(correction['date'])
                if s not in self.frames or t not in self.frames[s].index:continue
                if correction['status']=='corrected':
                    for key,value in correction['values'].items():self.frames[s].loc[t,key]=value
                else:self.frames[s]=self.frames[s].drop(index=t)
        mf=self.base/'macro/manifest.json'
        if mf.exists():
            for s,m in read_json(mf)['instruments'].items():
                if m.get('status')!='ok':continue
                file=mf.parent/(s+'.csv')
                if digest(file)!=m['sha256']:raise ValueError('Macro checksum: '+s)
                f=pd.read_csv(file,index_col=0,parse_dates=True);self.macro[s]=pd.to_numeric(f[s],errors='coerce').dropna().loc['2004-01-01':as_of]
        import gzip
        for path in list((self.base/'fundamentals').glob('*.json'))+list((self.base/'fundamentals').glob('*.json.gz')):
            f=json.loads(gzip.decompress(path.read_bytes())) if path.suffix=='.gz' else read_json(path)
            if f.get('status')=='ok':self.fund[f['symbol']]=f
    def price(self,s,adjusted=True):
        f=self.frames.get(s)
        if f is None:return pd.Series(dtype=float)
        return f['adjusted_close' if adjusted else 'close'].where(lambda x:x>0).dropna()
    def mac(self,s):return self.macro.get(s,pd.Series(dtype=float))
    def monthly(self,s):
        # Only completed calendar months; September 8 is not a September month-end.
        end=pd.Timestamp(self.as_of).replace(day=1)-pd.Timedelta(days=1)
        return self.price(s).loc[:end].resample('ME').last().dropna()
    def stats(self,s):
        p=self.price(s);f=self.frames.get(s)
        if len(p)<253:return None
        r=p.pct_change(fill_method=None);vol=r.iloc[-252:].std()*np.sqrt(252)
        return dict(symbol=s,as_of=str(p.index[-1].date()),price=number(p.iloc[-1]),r1d=ret(p,1),r1w=ret(p,5),r1m=ret(p,21),r3m=ret(p,63),r6m=ret(p,126),r1y=ret(p,252),ytd=ytd(p),
            rsi=number(rsi(p).iloc[-1]),vol=number(vol*100),high52=number((p.iloc[-1]/p.iloc[-252:].max()-1)*100),ma20=number(p.iloc[-20:].mean()),ma50=number(p.iloc[-50:].mean()),ma200=number(p.iloc[-200:].mean()),
            volume_ratio=number(f.volume.iloc[-5:].mean()/f.volume.iloc[-63:].mean()) if f is not None and 'volume' in f and f.volume.iloc[-63:].mean()>0 else None)
    def export(self,d):
        d['price_quality']=self.correction_meta
        write_json(ROOT/'docs/data'/(d['module']+'.json'),clean_json(d));print(d['module'],len(d.get('sections',[])),'sections',flush=True)

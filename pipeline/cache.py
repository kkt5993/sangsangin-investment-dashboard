"""Immutable run overlays: unchanged histories are inherited, changed rows stored."""
import gzip,json,re
import numpy as np
import pandas as pd
from .store import read_json,digest

def chain(data_root,vintage):
    out=[];seen=set()
    while vintage:
        if not re.fullmatch(r'[0-9TtZz_-]+',vintage) or vintage in seen:raise ValueError('Invalid cache ancestry')
        seen.add(vintage);folder=data_root/'expanded'/vintage
        if not folder.is_dir():raise ValueError('Missing cache vintage: '+vintage)
        out.append(folder);parent=folder/'parent.json';vintage=read_json(parent).get('vintage') if parent.exists() else None
    return list(reversed(out))

def unpack(path):return json.loads(gzip.decompress(path.read_bytes()))

def make_patch(old,new):
    """Full refresh is required if corporate-action scaling is not uniform."""
    if not set(new.columns)<=set(old.columns):return None
    common=old.index.intersection(new.index);scale={'price':1.,'adjusted':1.,'volume':1.}
    adjusted=old.copy()
    if len(common):
        for field,key in [('close','price'),('adjusted_close','adjusted')]:
            ratios=new.loc[common,field]/old.loc[common,field];ratios=ratios.replace([np.inf,-np.inf],np.nan).dropna()
            if len(ratios):
                factor=float(ratios.median())
                if not np.allclose(ratios,factor,rtol=2e-5,atol=1e-8):return None
                if abs(factor-1)>2e-6:scale[key]=factor
        if scale['price']!=1:
            # Split-related OHLC, volume and cash-distribution revisions need a
            # complete provider history; do not infer their different conventions.
            return None
        for k in ['open','high','low','close']:
            if k in adjusted:adjusted[k]*=scale['price']
        adjusted.adjusted_close*=scale['adjusted']
        if 'volume' in adjusted:adjusted.volume*=scale['volume']
    changed=[]
    for t,row in new.iterrows():
        if t not in adjusted.index or not np.allclose(row,adjusted.loc[t,new.columns],rtol=2e-6,atol=1e-8,equal_nan=True):changed.append(t)
    f=new.loc[changed]
    return dict(mode='patch',scale=scale,columns=list(f.columns),dates=[str(t.date()) for t in f.index],data=f.to_numpy().tolist())

def apply_patch_frame(old,patch):
    new=pd.DataFrame(patch['data'],index=pd.to_datetime(patch['dates']),columns=patch['columns']);new.index.name='date'
    if patch.get('mode')=='full' or old is None:return new.sort_index()
    out=old.copy();scale=patch.get('scale',{})
    for k in ['open','high','low','close']:
        if k in out:out[k]*=scale.get('price',1)
    out['adjusted_close']*=scale.get('adjusted',1)
    if 'volume' in out:out['volume']*=scale.get('volume',1)
    out=out.drop(index=out.index.intersection(new.index));return pd.concat([out,new]).sort_index()

def load_into(d,data_root,vintage):
    d.bases=chain(data_root,vintage);d.base=d.bases[-1];d.vintage=vintage;d.corrections=[];d.macro_meta={}
    corrections={};correction_hashes=[]
    for base in d.bases:
        for folder in [data_root/base.name,base/'stocks',base/'prices']:
            mf=folder/'manifest.json'
            if not mf.exists():continue
            for symbol,m in read_json(mf)['instruments'].items():
                if m.get('status')!='ok':continue
                path=folder/m['file']
                if path.parent.resolve()!=folder.resolve() or digest(path)!=m['sha256']:raise ValueError('Cache checksum: '+symbol)
                d.frames[symbol]=pd.read_csv(path,index_col='date',parse_dates=['date']);d.quality[symbol]=m
        pf=base/'price_delta.json.gz'
        if pf.exists():
            meta=read_json(base/'price_delta_manifest.json')
            if digest(pf)!=meta['sha256']:raise ValueError('Price delta checksum')
            for symbol,p in unpack(pf)['instruments'].items():
                d.frames[symbol]=apply_patch_frame(d.frames.get(symbol),p)
                f=d.frames[symbol];d.quality[symbol]=dict(d.quality.get(symbol,{}),status='ok',sha256=meta['sha256'],rows=len(f),first=str(f.index[0].date()),last=str(f.index[-1].date()),retrieved_at=p.get('retrieved_at'),provenance='parent + run delta')
        for key in ['kr_largecap','kospi200','us_largecap','us100','kr_screen','kr_sectors']:
            path=base/(key+'.json')
            if path.exists():
                membership=read_json(path)
                if key=='us100':
                    raw=base/membership['raw_file']
                    if raw.parent.resolve()!=base.resolve() or digest(raw)!=membership['sha256']:raise ValueError('OEF holdings checksum')
                d.members[key]=membership
        cf=base/'price_corrections.json.gz'
        if cf.exists():
            correction_hashes.append(digest(cf))
            for c in unpack(cf)['records']:
                symbol=c['symbol'];t=pd.Timestamp(c['date']);corrections[(symbol,c['date'])]=c
                if symbol not in d.frames or t not in d.frames[symbol].index:continue
                if c['status']=='corrected':
                    for k,v in c['values'].items():d.frames[symbol].loc[t,k]=v
                else:d.frames[symbol]=d.frames[symbol].drop(index=t)
        mf=base/'macro/manifest.json'
        if mf.exists():
            for symbol,m in read_json(mf)['instruments'].items():
                if m.get('status')!='ok':continue
                path=mf.parent/(symbol+'.csv')
                if digest(path)!=m['sha256']:raise ValueError('Macro checksum: '+symbol)
                f=pd.read_csv(path,index_col=0,parse_dates=True);d.macro[symbol]=pd.to_numeric(f[symbol],errors='coerce').dropna().loc['2004-01-01':d.as_of];d.macro_meta[symbol]=m
        for path in list((base/'fundamentals').glob('*.json'))+list((base/'fundamentals').glob('*.json.gz')):
            f=unpack(path) if path.suffix=='.gz' else read_json(path)
            if f.get('status')=='ok':d.fund[f['symbol']]=f
    d.frames={s:f.loc[:d.as_of] for s,f in d.frames.items() if len(f.loc[:d.as_of]) and (pd.Timestamp(d.as_of)-f.loc[:d.as_of].index[-1]).days<=7}
    d.corrections=list(corrections.values())
    import hashlib
    sha=correction_hashes[0] if len(correction_hashes)==1 else hashlib.sha256(''.join(correction_hashes).encode()).hexdigest()
    d.correction_meta=dict(source='KRX official OHLC reconciliation',sha256=sha,corrected=sum(c['status']=='corrected' for c in d.corrections),quarantined=sum(c['status']=='quarantined' for c in d.corrections))

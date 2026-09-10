"""Authors' GPR observations; preserve recent indexes and historical article shares."""
import gzip,io
import pandas as pd
import numpy as np
from .acquire import get_bytes, stamp
from .store import write_json,read_json,digest
from .events_data import save

URL='https://www.matteoiacoviello.com/gpr_files/data_gpr_export.dta'
CATEGORIES=['전쟁 위협','평화 위협','군사력 증강','핵 위협','테러 위협','전쟁 시작','전쟁 격화','테러 행위']
COUNTRIES={'USA':'미국','KOR':'한국','CHN':'중국','TWN':'대만','JPN':'일본','RUS':'러시아','UKR':'우크라이나','ISR':'이스라엘'}

def parse(blob,as_of):
    with pd.io.stata.StataReader(io.BytesIO(blob)) as reader:labels=reader.variable_labels();f=reader.read(convert_categoricals=False)
    required=['month','GPR','GPRT','GPRA']+['SHAREH_CAT_'+str(i) for i in range(1,9)]+['GPRC_'+c for c in COUNTRIES]
    if not set(required)<=set(f):raise ValueError('GPR data schema changed')
    f=f[required].copy();f['month']=pd.to_datetime(f['month']);f=f.set_index('month').sort_index()
    end=pd.Timestamp(as_of).replace(day=1)-pd.Timedelta(days=1);f=f.loc['2004-01-01':end]
    if f.empty or not f.index.is_unique or (f.index.day!=1).any():raise ValueError('Invalid GPR monthly dates')
    if f[['GPR','GPRT','GPRA']].isna().any().any() or not np.isfinite(f.to_numpy(dtype=float)).all() or (f<0).any().any():raise ValueError('Invalid GPR observations')
    return f,labels

def collect(base,as_of):
    folder=base/'macro';folder.mkdir(exist_ok=True);detail=base/'gpr_details.json.gz'
    if detail.exists() and all((folder/(k+'.csv')).exists() for k in ['GPR','GPRT','GPRA']):return
    source=base/'gpr-source.dta.gz'
    if not source.exists():
        encoded=gzip.compress(get_bytes(URL),mtime=0);source.write_bytes(encoded)
    f,labels=parse(gzip.decompress(source.read_bytes()),as_of);retrieved=stamp();mf=folder/'manifest.json';m=read_json(mf) if mf.exists() else dict(as_of=as_of,instruments={})
    for key in ['GPR','GPRT','GPRA']:
        file=folder/(key+'.csv');f[[key]].rename_axis('observation_date').to_csv(file)
        m['instruments'][key]=dict(status='ok',name=labels[key],unit='index 1985–2019=100',frequency='M',source=URL,sha256=digest(file),retrieved_at=retrieved)
    write_json(mf,m)
    save(detail,dict(as_of=as_of,retrieved_at=retrieved,source=URL,source_sha256=digest(source),source_encoding='gzip Stata',labels=labels,
        categories=[dict(key='SHAREH_CAT_'+str(i+1),name=n,unit='% of 3 historical newspapers articles') for i,n in enumerate(CATEGORIES)],
        countries=[dict(key='GPRC_'+k,name=n,unit='% of 10 recent newspapers articles') for k,n in COUNTRIES.items()],
        rows=[dict(date=str(t.date()),**r.to_dict()) for t,r in f.tail(120).iterrows()]))
    print('GPR/GPRT/GPRA',len(f),'months;8 historical categories/8 countries',flush=True)

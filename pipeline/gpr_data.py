"""Small monthly GPR observation cache from the authors' public replication data."""
import io
import pandas as pd
from .acquire import get_bytes,stamp
from .store import write_json,read_json,digest

def collect(base,as_of):
    folder=base/'macro';folder.mkdir(exist_ok=True);file=folder/'GPR.csv'
    if file.exists():return
    url='https://www.matteoiacoviello.com/gpr_files/data_gpr_export.dta'
    f=pd.read_stata(io.BytesIO(get_bytes(url)),convert_categoricals=False)
    key=next(k for k in f if k.lower()=='gpr');date=next(k for k in f if k.lower() in ['month','date'])
    out=pd.DataFrame({'observation_date':pd.to_datetime(f[date]),'GPR':pd.to_numeric(f[key],errors='coerce')}).dropna()
    out=out[(out.observation_date>='2004-01-01')&(out.observation_date<=as_of)]
    if out.empty or not out.observation_date.is_unique:raise ValueError('Invalid GPR monthly data')
    out.to_csv(file,index=False);mf=folder/'manifest.json';m=read_json(mf) if mf.exists() else dict(as_of=as_of,instruments={})
    m['instruments']['GPR']=dict(status='ok',name='Caldara–Iacoviello GPR',unit='index',frequency='M',source=url,sha256=digest(file),retrieved_at=stamp())
    write_json(mf,m);print('GPR monthly',len(out),flush=True)

"""One bounded OECD CLI request; validate units before caching monthly series."""
import argparse, io
import pandas as pd
import requests
from .acquire import budget, stamp
from .store import data_base, read_json, write_json, digest

AREAS={'USA':'미국','KOR':'한국','JPN':'일본','CHN':'중국'}
URL='https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI,/USA+KOR+JPN+CHN.M.LI...AA...H'


def parse(payload,as_of):
    f=pd.read_csv(io.BytesIO(payload),dtype=str)
    required=['REF_AREA','FREQ','MEASURE','UNIT_MEASURE','ADJUSTMENT','METHODOLOGY','UNIT_MULT','TIME_PERIOD','OBS_VALUE']
    if not set(required)<=set(f):raise ValueError('OECD CLI schema changed')
    out={};end=pd.Timestamp(as_of).replace(day=1)-pd.Timedelta(days=1)
    for area in AREAS:
        g=f[f.REF_AREA==area].copy()
        expected={'FREQ':'M','MEASURE':'LI','UNIT_MEASURE':'IX','ADJUSTMENT':'AA','METHODOLOGY':'H','UNIT_MULT':'0'}
        if g.empty or any(set(g[k])!={v} for k,v in expected.items()):raise ValueError('OECD CLI dimensions: '+area)
        g['date']=pd.to_datetime(g.TIME_PERIOD,format='%Y-%m',errors='raise')
        g['value']=pd.to_numeric(g.OBS_VALUE,errors='raise')
        g=g[(g.date>='2000-01-01')&(g.date<=end)].sort_values('date')
        if len(g)<60 or not g.date.is_unique or not g.value.between(50,150).all():raise ValueError('OECD CLI observations: '+area)
        # A monthly collector cannot quietly inherit a discontinued series.
        if end.to_period('M').ordinal-g.date.iloc[-1].to_period('M').ordinal>3:raise ValueError('OECD CLI stale: '+area)
        if not g.date.dt.to_period('M').astype('int64').diff().iloc[1:].eq(1).all():raise ValueError('OECD CLI monthly gap: '+area)
        key='OECD_CLI_'+area
        out[key]=pd.DataFrame({'observation_date':g.date.dt.strftime('%Y-%m-%d'),key:g.value})
    return out


def collect(base,as_of,payload=None):
    if payload is None:
        end=(pd.Timestamp(as_of).replace(day=1)-pd.Timedelta(days=1)).strftime('%Y-%m')
        r=requests.get(URL,params={'startPeriod':'2000-01','endPeriod':end,'dimensionAtObservation':'AllDimensions','format':'csvfilewithlabels'},timeout=45)
        r.raise_for_status();payload=r.content
    series=parse(payload,as_of);folder=base/'macro';folder.mkdir(parents=True,exist_ok=True)
    mf=folder/'manifest.json';manifest=read_json(mf) if mf.exists() else dict(as_of=as_of,instruments={})
    for key,f in series.items():
        file=folder/(key+'.csv')
        if file.exists():raise ValueError('OECD immutable observation already exists')
        encoded=f.to_csv(index=False).encode('utf-8');budget(len(encoded));file.write_bytes(encoded)
        manifest['instruments'][key]=dict(status='ok',name=AREAS[key.removeprefix('OECD_CLI_')]+' OECD 경기선행지수',unit='index, long-term average=100',frequency='M',source=URL,sha256=digest(file),retrieved_at=stamp(),last=str(f.observation_date.iloc[-1]),adjustment='amplitude adjusted',vintage_note='current revised observations; not historical release vintages')
    write_json(mf,manifest)
    write_json(base/'oecd_cli_collection.json',dict(retrieved_at=stamp(),as_of=as_of,source=URL,series={k:dict(rows=len(f),last=str(f.observation_date.iloc[-1])) for k,f in series.items()}))
    print('OECD CLI',len(series),'series',len(next(iter(series.values()))),'months',flush=True)
    return series


def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();collect(data_base(a.as_of),a.as_of)
if __name__=='__main__':main()

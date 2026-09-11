"""Bounded USGS daily events and CelesTrak OMM elements; no browser polling."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone, timedelta
import requests
from .engine import Data
from .events_data import read, save
from .acquire import stamp

QUAKES='https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson'
STATIONS='https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=JSON'
FIELDS=['OBJECT_NAME','OBJECT_ID','EPOCH','MEAN_MOTION','ECCENTRICITY','INCLINATION','RA_OF_ASC_NODE',
        'ARG_OF_PERICENTER','MEAN_ANOMALY','EPHEMERIS_TYPE','CLASSIFICATION_TYPE','NORAD_CAT_ID',
        'ELEMENT_SET_NO','REV_AT_EPOCH','BSTAR','MEAN_MOTION_DOT','MEAN_MOTION_DDOT']


def utc(value):
    t=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    # CelesTrak explicitly defines its unqualified OMM EPOCH as UTC.
    return t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)


def number(value):
    if value is None or isinstance(value,bool):raise ValueError('Missing observation')
    x=float(value)
    if not math.isfinite(x):raise ValueError('Nonfinite observation')
    return x


def quakes(raw,now):
    if raw.get('type')!='FeatureCollection' or raw.get('metadata',{}).get('status')!=200:raise ValueError('USGS schema/status')
    meta=raw['metadata'];generated=datetime.fromtimestamp(number(meta['generated'])/1000,timezone.utc)
    if generated>now+timedelta(minutes=5) or generated<now-timedelta(days=2):raise ValueError('USGS generated timestamp')
    features=raw.get('features',[])
    if meta.get('count')!=len(features) or len(features)>2000:raise ValueError('USGS incomplete response')
    rows={}
    for f in features:
        p=f['properties'];g=f['geometry'];mag=number(p['mag'])
        if g.get('type')!='Point' or len(g['coordinates'])!=3:raise ValueError('USGS point geometry')
        lon,lat,depth=map(number,g['coordinates']);event=datetime.fromtimestamp(number(p['time'])/1000,timezone.utc)
        updated=datetime.fromtimestamp(number(p['updated'])/1000,timezone.utc)
        if not (-180<=lon<=180 and -90<=lat<=90 and -10<=depth<=800 and -3<=mag<=10.5):raise ValueError('USGS event range')
        if event>generated or event<generated-timedelta(hours=25) or updated<event or updated>now+timedelta(minutes=5):raise ValueError('USGS event time')
        if p.get('type')!='earthquake' or mag<2.5:continue
        url=p.get('url','')
        if not url.startswith('https://earthquake.usgs.gov/earthquakes/eventpage/'):raise ValueError('USGS event URL')
        row=dict(id=str(f['id']),name=str(p.get('place') or f['id']),mag=mag,mag_type=p.get('magType'),lon=lon,lat=lat,
                 depth_km=depth,time=event.isoformat(),updated=updated.isoformat(),status=p.get('status'),url=url)
        if row['id'] in rows and rows[row['id']]!=row:raise ValueError('Conflicting earthquake')
        rows[row['id']]=row
    return dict(generated_at=generated.isoformat(),events=sorted(rows.values(),key=lambda r:r['time'],reverse=True))


def stations(raw,now):
    if not isinstance(raw,list) or not 1<=len(raw)<=200:raise ValueError('CelesTrak stations scope')
    out={}
    for p in raw:
        for key,value in [('CENTER_NAME','EARTH'),('REF_FRAME','TEME'),('TIME_SYSTEM','UTC'),('MEAN_ELEMENT_THEORY','SGP4')]:
            if p.get(key,value)!=value:raise ValueError('Unsupported OMM reference convention')
        if any(k not in p for k in FIELDS):raise ValueError('OMM required fields')
        r={k:p[k] for k in FIELDS};epoch=utc(r['EPOCH'])
        r['EPOCH']=epoch.isoformat().replace('+00:00','Z')
        if epoch>now+timedelta(days=1) or epoch<now-timedelta(days=90):raise ValueError('OMM epoch range')
        for key in FIELDS[3:]:
            if key=='CLASSIFICATION_TYPE':continue
            number(r[key])
        if not (0<number(r['MEAN_MOTION'])<20 and 0<=number(r['ECCENTRICITY'])<1 and 0<=number(r['INCLINATION'])<=180):raise ValueError('OMM orbital range')
        if any(not 0<=number(r[k])<360 for k in ['RA_OF_ASC_NODE','ARG_OF_PERICENTER','MEAN_ANOMALY']):raise ValueError('OMM angle')
        ident=number(r['NORAD_CAT_ID'])
        if ident!=int(ident) or not 1<=ident<10000000:raise ValueError('NORAD identity')
        for key in ['EPHEMERIS_TYPE','ELEMENT_SET_NO','REV_AT_EPOCH']:
            value=number(r[key])
            if value!=int(value) or value<0:raise ValueError('OMM integer field')
        if number(r['EPHEMERIS_TYPE']) not in [0,2] or r['CLASSIFICATION_TYPE']!='U':raise ValueError('OMM public SGP4 convention')
        if not isinstance(r['OBJECT_NAME'],str) or not r['OBJECT_NAME'].strip():raise ValueError('OMM object name')
        # Keep source decimal precision as JSON strings; satellite.js accepts numeric strings.
        for k in FIELDS[3:]:
            if k!='CLASSIFICATION_TYPE':r[k]=str(r[k])
        if ident in out and out[ident]!=r:raise ValueError('Conflicting OMM element sets')
        out[ident]=r
    return sorted(out.values(),key=lambda r:int(r['NORAD_CAT_ID']))


def download(url,session):
    with session.get(url,timeout=(10,30),stream=True,allow_redirects=False,
        headers={'User-Agent':'SangsanginResearch/1.0 (+https://github.com/kkt5993/sangsangin-investment-dashboard)'}) as response:
        if response.status_code!=200:
            error=RuntimeError('Source HTTP '+str(response.status_code));error.http_status=response.status_code;raise error
        body=bytearray()
        for part in response.iter_content(16384):
            body.extend(part)
        return json.loads(body),len(body),hashlib.sha256(body).hexdigest()


def collect(d,session=None):
    session=session or requests.Session();now=datetime.now(timezone.utc);report=dict(checked_at=stamp(),sources=[])
    for key,url,hours,normalize in [('quakes',QUAKES,1,quakes),('stations',STATIONS,2,stations)]:
        name='sauron/'+key+'.json.gz';path=d.resource(name);old=read(path) if path.exists() else {}
        halt=d.resource('sauron/stations-halted.json.gz')
        state='reused';requested=False;error_type=None;http_status=None
        age=(now-utc(old['checked_at'])).total_seconds() if old.get('checked_at') else float('inf')
        if key=='stations' and halt.exists():state='halted'
        elif not 0<=age<hours*3600:
            requested=True
            try:
                raw,size,sha=download(url,session);data=normalize(raw,now)
                packet=dict(source=url,checked_at=stamp(),retrieved_at=stamp(),data=data,sha256=sha,received_bytes=size)
                if data==old.get('data'):packet['retrieved_at']=old['retrieved_at']
                save(d.base/name,packet);old=packet;state='ok'
            except Exception as e:
                state='error';error_type=type(e).__name__;http_status=getattr(e,'http_status',None)
                if key=='stations' and hasattr(e,'http_status'):
                    save(d.base/'sauron/stations-halted.json.gz',dict(checked_at=stamp(),http_status=e.http_status));state='halted'
        report['sources'].append(dict(key=key,state=state,requested=requested,retrieved_at=old.get('retrieved_at'),checked_at=old.get('checked_at'),error_type=error_type,http_status=http_status))
        print('SAURON',key,state,flush=True)
    save(d.base/'sauron/collection.json.gz',report)
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();collect(Data(a.as_of))


if __name__=='__main__':main()

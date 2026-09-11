"""Exact city/country matching; ambiguous places require reviewed GeoNames IDs."""
import unicodedata

COUNTRIES = {'United States':'US','South Korea':'KR','Taiwan':'TW','Japan':'JP','Germany':'DE',
    'Netherlands':'NL','Sweden':'SE','Spain':'ES','United Kingdom':'GB','China':'CN','France':'FR',
    'Switzerland':'CH','Denmark':'DK','Ireland':'IE','Singapore':'SG','Luxembourg':'LU','Canada':'CA',
    'Australia':'AU','India':'IN','Saudi Arabia':'SA','Qatar':'QA','Brazil':'BR','Argentina':'AR',
    'Uruguay':'UY','Finland':'FI','Israel':'IL','Hong Kong':'HK','Italy':'IT'}


def key(value):
    value=(value or '').casefold().replace('æ','ae').replace('ø','o').replace('ł','l').replace('œ','oe')
    return ''.join(c for c in unicodedata.normalize('NFKD',value)
                   if c.isalnum() and not unicodedata.combining(c))


def places(lines):
    result = []
    for line in lines:
        f=line.split('\t')
        if len(f)!=19:raise ValueError('Gazetteer row schema')
        if f[6]!='P':continue
        lat,lon=float(f[4]),float(f[5])
        if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Gazetteer coordinate range')
        result.append(dict(id=f[0],name=f[1],primary={key(f[1]),key(f[2])},aliases={key(n) for n in [f[1],f[2]]+f[3].split(',') if n},
                           lat=lat,lon=lon,country=f[8],region=f[10],modified=f[18]))
    return result


def candidates(profile, gazetteer):
    country=COUNTRIES.get(profile.get('country'))
    if not country or not profile.get('city'):return []
    found=[p for p in gazetteer if p['country']==country and key(profile['city']) in p['aliases']]
    if country=='US' and profile.get('state'):
        found=[p for p in found if p['region']==profile['state']]
    primary=[p for p in found if key(profile['city']) in p['primary']]
    if primary:return primary
    return found


def location(profile,gazetteer):
    found=candidates(profile,gazetteer)
    if len(found)!=1:return None
    row={k:v for k,v in found[0].items() if k not in ['aliases','primary']}
    row['profile_city']=profile['city'];row['profile_country']=profile['country']
    row['source']='https://www.geonames.org/'+row['id']+'/'
    return row


def collect(d):
    import hashlib
    import json
    import zipfile
    from datetime import datetime, timezone
    import requests
    from .acquire import stamp
    from .events_data import read,save
    from .chain_data import PROFILE,age_hours
    url='https://download.geonames.org/export/dump/cities5000.zip'
    archive=d.resource('chain/cities5000.zip')
    meta_path=d.resource('chain/geonames.json.gz')
    meta=read(meta_path) if meta_path.exists() else {}
    now=datetime.now(timezone.utc);error=None
    if not archive.exists() or age_hours(meta.get('checked_at'),now)>=180*24:
        try:
            with requests.get(url,stream=True,timeout=(10,40),headers={'User-Agent':'SangsanginResearch/1.0'}) as response:
                if response.status_code!=200:raise ValueError('Gazetteer HTTP status')
                blob=bytearray()
                for part in response.iter_content(65536):
                    blob.extend(part)
            import io
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                places(z.read('cities5000.txt').decode('utf-8').splitlines())
            target=d.base/'chain/cities5000.zip';target.parent.mkdir(parents=True,exist_ok=True)
            temp=target.with_suffix('.tmp');temp.write_bytes(blob);temp.replace(target);archive=target
            meta=dict(source=url,sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob),
                      checked_at=stamp(),retrieved_at=stamp(),license='CC BY 4.0')
            save(d.base/'chain/geonames.json.gz',meta)
        except Exception as exc:error=type(exc).__name__
    if not archive.exists():return dict(state='error',error_type=error)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=meta.get('sha256'):
        raise ValueError('Gazetteer checksum')
    profiles=read(d.resource(PROFILE)).get('companies',{})
    profile_keys={s:[r['data'].get(k) for k in ['country','city','state']] for s,r in profiles.items()}
    previous_path=d.resource('chain/locations.json.gz')
    previous=read(previous_path) if previous_path.exists() else {}
    if previous.get('profile_keys')==profile_keys and previous.get('source',{}).get('sha256')==meta.get('sha256'):
        if error:
            previous=dict(previous,error_type=error,checked_at=stamp())
            save(d.base/'chain/locations.json.gz',previous)
        return previous
    with zipfile.ZipFile(archive) as z:
        gazetteer=places(z.read('cities5000.txt').decode('utf-8').splitlines())
    wanted={key(r['data'].get('city')) for r in profiles.values()}
    gazetteer=[p for p in gazetteer if p['aliases'] & wanted]
    selected={s:location(r['data'],gazetteer) for s,r in profiles.items()}
    result=dict(locations=selected,profile_keys=profile_keys,source=meta,checked_at=stamp(),error_type=error)
    save(d.base/'chain/locations.json.gz',result)
    return result

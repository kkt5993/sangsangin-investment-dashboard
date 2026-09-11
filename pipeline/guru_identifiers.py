"""Public OpenFIGI CUSIP mappings, cached outside the repository."""
import argparse,copy,re,time
from datetime import datetime,timezone
import requests
from .guru_data import FILE as REPORTS,read,save,resources,settings,latest,utc

API='https://api.openfigi.com/v3/mapping'
FILE='guru/identifiers.json.gz'

def query(cusip):return dict(idType='ID_CUSIP',idValue=cusip,exchCode='US')
def age(value,now):
    try:return (now-utc(value)).total_seconds()/86400
    except (TypeError,ValueError,AttributeError):return float('inf')

def normalize(cusip,raw,now):
    if not re.fullmatch(r'[A-Z0-9*@#]{9}',cusip) or cusip=='000000000':raise ValueError('CUSIP identity')
    if not isinstance(raw,dict) or 'error' in raw:raise ValueError('OpenFIGI job failure')
    if 'warning' in raw:
        if 'data' in raw:raise ValueError('Conflicting OpenFIGI response')
        return dict(cusip=cusip,query=query(cusip),status='unmapped',checked_at=now.isoformat(),results=[],raw=raw)
    data=raw.get('data')
    if not isinstance(data,list) or not data:raise ValueError('OpenFIGI data missing')
    unique={}
    for item in data:
        for key in ['figi','ticker','exchCode','name','securityType','marketSector']:
            if not isinstance(item.get(key),str) or not item[key]:raise ValueError('Incomplete OpenFIGI identity')
        if not re.fullmatch(r'BBG[A-Z0-9]{9}',item['figi']) or item['exchCode']!='US':raise ValueError('OpenFIGI market/FIGI')
        selected={k:item.get(k) for k in ['figi','compositeFIGI','shareClassFIGI','ticker','name','securityType','securityType2','marketSector','exchCode']}
        if item['figi'] in unique and unique[item['figi']]!=selected:raise ValueError('Conflicting FIGI result')
        unique[item['figi']]=selected
    return dict(cusip=cusip,query=query(cusip),status='mapped' if len(unique)==1 else 'ambiguous',checked_at=now.isoformat(),results=list(unique.values()),raw=raw)

def collect(d,session=None,now=None,pause=time.sleep):
    now=now or datetime.now(timezone.utc);path=d.resource(FILE);packet=read(path) if path.exists() else {'mappings':{}}
    old=packet.get('collection',{});report=dict(attempted_at=now.isoformat(),status='reused',requests=0,jobs=0,errors=[])
    if old.get('status') in ['error','access_refused'] and 0<=age(old.get('attempted_at'),now)<1/24:return dict(old,requests=0,jobs=0,cached=True)
    source=d.resource(REPORTS);reports=read(source).get('filings',[]) if source.exists() else [];cusips=set()
    for manager in settings():
        selected=latest(reports,manager['cik'],d.as_of)
        if selected:
            cusips.update(r['cusip'] for r in selected['entries'] if r['cusip']!='000000000')
    todo=[]
    for cusip in sorted(cusips):
        r=packet['mappings'].get(cusip,{})
        days=30 if r.get('status')=='mapped' else 7
        if r.get('query')!=query(cusip) or not 0<=age(r.get('checked_at'),now)<days:todo.append(cusip)
    if not todo:return report
    own=session is None;session=session or requests.Session()
    try:
        report['status']='ok'
        for start in range(0,len(todo),5):
            batch=todo[start:start+5];pause(3);report['requests']+=1;report['jobs']+=len(batch)
            response=session.post(API,json=[query(c) for c in batch],timeout=(10,30),allow_redirects=False)
            if response.status_code!=200:
                report['status']='access_refused' if response.status_code in [401,403,429] else 'error';report['http_status']=response.status_code;break
            raw=response.json()
            if not isinstance(raw,list) or len(raw)!=len(batch):raise ValueError('OpenFIGI positional response length')
            # Validate the batch before changing its cache; failed jobs preserve old values.
            updates={}
            for cusip,result in zip(batch,raw):
                try:updates[cusip]=normalize(cusip,result,now)
                except ValueError:report['errors'].append(dict(cusip=cusip,error='job_schema_or_error'))
            packet['mappings'].update(updates);packet['collection']=copy.deepcopy(report);save(d.base/FILE,packet)
        if report['errors'] and report['status']=='ok':report['status']='error'
    except (requests.RequestException,ValueError):report['status']='error'
    finally:
        if own:session.close()
    packet['collection']=report;save(d.base/FILE,packet);return report

def resolve(position,mappings,entities,now):
    record=mappings.get(position['cusip'],{})
    if record.get('query')!=query(position['cusip']):return None,'식별자 미확보'
    if not 0<=age(record.get('checked_at'),now)<=30:return None,'식별자 관측30일 초과 또는 미래'
    if record.get('status')!='mapped' or len(record.get('results',[]))!=1:return None,'여러 식별자 후보' if record.get('status')=='ambiguous' else '식별자 미확보'
    r=record['results'][0]
    if position['quantity_type']!='SH' or r['marketSector']!='Equity' or r['securityType'] not in ['Common Stock','ADR','REIT','GDR','NY Reg Shrs','MLP']:return None,'기업 주식·예탁증서·파트너십 범위 밖'
    ticker=r['ticker'];symbol=re.sub(r'^([A-Z]{1,6})[/.]([A-Z])$',r'\1-\2',ticker)
    candidates=[e for e in entities if e['market']=='US' and e['symbol']==symbol]
    if len(candidates)!=1:return None,'Entity360 유니버스 밖' if not candidates else '기업 식별자 중복'
    e=candidates[0]
    return dict(id=e['id'],symbol=e['symbol'],name=e['name'],figi=r['figi'],figi_name=r['name'],share_class_figi=r.get('shareClassFIGI'),security_type=r['securityType'],source_ticker=ticker,checked_at=record['checked_at'],url='https://www.openfigi.com/id/'+r['figi']),None

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();r=collect(resources(a.as_of));print('CUSIP',r['status'],'requests',r['requests'],'jobs',r['jobs'])
if __name__=='__main__':main()

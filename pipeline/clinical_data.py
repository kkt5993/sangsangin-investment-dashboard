"""ClinicalTrials.gov registry counts and latest records; cached, no model calls."""
import argparse,gzip,hashlib,json,os,re,time
from datetime import date,datetime,timezone
from types import SimpleNamespace
from urllib.parse import urlencode
import requests
from .store import DATA,ROOT,read_json
from .cache import chain

API='https://clinicaltrials.gov/api/v2'
FILE='clinical/observations.json.gz'
FIELDS='NCTId,BriefTitle,OverallStatus,Phase,LeadSponsorName,CollaboratorName,LastUpdatePostDate'
STUDY_FIELDS=('title','status','phases','updated','sponsor','collaborators','url')

def stamp():return datetime.now(timezone.utc).isoformat()
def read(path):return json.loads(gzip.decompress(path.read_bytes()))
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,allow_nan=False).encode(),mtime=0));temp.replace(path)
def settings():return json.loads((ROOT/'config/clinical_scopes.json').read_text(encoding='utf-8-sig'))
def identity(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def resources(asof,vintage=None):
    bases=chain(DATA,vintage or os.environ.get('SANGSANGIN_VINTAGE') or asof);base=bases[-1]
    return SimpleNamespace(as_of=asof,base=base,resource=lambda name:next((p/name for p in reversed(bases) if (p/name).exists()),base/name))
def age(value,now):
    try:return (now-datetime.fromisoformat(value)).total_seconds()/3600
    except (TypeError,ValueError):return float('inf')
def params(scope,kind):
    term='('+scope['term']+')'+(' AND AREA[Phase]PHASE3' if kind=='phase3' else '')
    p={'query.term':term,'format':'json','pageSize':5,'countTotal':'true','sort':'LastUpdatePostDate:desc','fields':FIELDS}
    if kind=='recruiting':p['filter.overallStatus']='RECRUITING'
    return p

def normalize(raw,kind,version):
    count=raw.get('totalCount');studies=raw.get('studies',[])
    if type(count)!=int or count<0 or not isinstance(studies,list) or len(studies)!=min(count,5):raise ValueError('Clinical count/sample schema')
    if count>5 and not raw.get('nextPageToken'):raise ValueError('Clinical truncated count response')
    rows=[];seen=set()
    for study in studies:
        p=study['protocolSection'];i=p['identificationModule'];s=p['statusModule'];nct=i['nctId'];updated=s['lastUpdatePostDateStruct']['date']
        if not re.fullmatch(r'NCT\d{8}',nct) or nct in seen:raise ValueError('Clinical study identity')
        seen.add(nct);date.fromisoformat(updated)
        if updated>version[:10]:raise ValueError('Clinical update later than registry date')
        title=i['briefTitle'];status=s['overallStatus'];phases=p.get('designModule',{}).get('phases',[])
        if not title or not isinstance(title,str) or not isinstance(phases,list):raise ValueError('Clinical study fields')
        if kind=='recruiting' and status!='RECRUITING':raise ValueError('Wrong recruitment filter')
        if kind=='phase3' and 'PHASE3' not in phases:raise ValueError('Wrong phase filter')
        sponsor=p.get('sponsorCollaboratorsModule',{});rows.append(dict(id=nct,title=title,status=status,phases=phases,updated=updated,sponsor=sponsor.get('leadSponsor',{}).get('name'),collaborators=[r['name'] for r in sponsor.get('collaborators',[])],url='https://clinicaltrials.gov/study/'+nct))
    if [r['updated'] for r in rows]!=sorted((r['updated'] for r in rows),reverse=True):raise ValueError('Clinical sort contract')
    return dict(count=count,latest=rows)

def retain_study_history(previous,rows,observed_at,data_version):
    """Keep state changes for studies that enter the published five-record sample.

    This deliberately is not an implied full-registry history: a study is only
    observable after it appears in one of the explicitly collected samples.
    """
    source=previous.get('study_history',{}) if isinstance(previous,dict) else {}
    history={key:[dict(item) for item in value if isinstance(item,dict)] for key,value in source.items() if isinstance(key,str) and isinstance(value,list)}
    for row in rows:
        state={key:row[key] for key in STUDY_FIELDS}
        entries=history.get(row['id'],[]);last=entries[-1] if entries else None
        earlier={key:last.get(key) for key in STUDY_FIELDS} if last else None
        changed=[key for key in STUDY_FIELDS if earlier and earlier[key]!=state[key]]
        if last and not changed:
            last['last_observed_at']=observed_at;last['last_data_version']=data_version
        else:
            entries.append(dict(**state,first_observed_at=observed_at,last_observed_at=observed_at,first_data_version=data_version,last_data_version=data_version))
        history[row['id']]=entries
        row['history']=[dict(item) for item in entries]
        row['changed_fields']=changed
    return history

def request(session,path,query,report,pause):
    pause(1);report['requests']+=1
    response=session.get(API+path,params=query,timeout=(10,30),headers={'User-Agent':'SangsanginResearch/1.0 (+https://github.com/kkt5993/sangsangin-investment-dashboard)'})
    response.raise_for_status();return response.json()

def collect(d,session=None,now=None,pause=time.sleep):
    now=now or datetime.now(timezone.utc);session=session or requests.Session();cfg=settings();config_hash=identity(cfg);path=d.resource(FILE);old=read(path) if path.exists() else {}
    report=dict(checked_at=now.isoformat(),requests=0,status='reused')
    valid=old.get('config_hash')==config_hash
    if old.get('error') and old.get('attempt_config_hash')==config_hash and 0<=age(old.get('checked_at'),now)<1:
        report['status']='backoff';return report
    if valid and not old.get('error') and 0<=age(old.get('checked_at'),now)<24:return report
    report['status']='ok'
    try:
        version=request(session,'/version',{},report,pause);dt=version['dataTimestamp'];date.fromisoformat(dt[:10])
        if dt[:10]>now.date().isoformat():raise ValueError('Future registry version')
        if valid and old.get('data_version')==dt:
            packet={**old,'checked_at':now.isoformat(),'error':None};save(d.base/FILE,packet);return report
        collected=[];responses={}
        for scope in cfg['scopes']:
            groups={}
            for kind in ['all','recruiting','phase3']:
                query=params(scope,kind);raw=request(session,'/studies',query,report,pause);groups[kind]={**normalize(raw,kind,dt),'query_url':API+'/studies?'+urlencode(query)};responses[scope['id']+':'+kind]=raw
            if any(groups[k]['count']>groups['all']['count'] for k in ['recruiting','phase3']):raise ValueError('Clinical subsets exceed total')
            previous=next((r for r in old.get('scopes',[]) if r['id']==scope['id']),None) if valid else None
            for kind,group in groups.items():
                group['study_history']=retain_study_history(previous.get('groups',{}).get(kind,{}) if previous else {},group['latest'],now.isoformat(),dt)
            collected.append(dict(**scope,groups=groups,previous_at=old.get('retrieved_at') if previous else None,changes={k:groups[k]['count']-previous['groups'][k]['count'] if previous else None for k in groups}))
        final=request(session,'/version',{},report,pause)
        if final.get('dataTimestamp')!=dt:raise ValueError('Registry changed during collection')
        packet=dict(config_hash=config_hash,checked_at=now.isoformat(),retrieved_at=now.isoformat(),data_version=dt,api_version=version['apiVersion'],scopes=collected,responses=responses,error=None)
        save(d.base/FILE,packet)
    except Exception as e:
        report['status']='error';report['error']=type(e).__name__
        # Keep successful observations, dates and their query identity on failure.
        packet={**old,'checked_at':now.isoformat(),'error':dict(type=type(e).__name__,at=now.isoformat()),'attempt_config_hash':config_hash};save(d.base/FILE,packet)
    save(d.base/'clinical/collection.json.gz',report)
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();print(json.dumps(collect(resources(a.as_of))))
if __name__=='__main__':main()

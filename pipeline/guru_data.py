"""SEC 13F observations: exact reported values, immutable filings and daily discovery.

Reviewed SEC rendered tables can be imported without inventing raw XML. The
collection contact stays in DATA/runtime/sec-contact.json, never in public output.
"""
import argparse,copy,gzip,hashlib,json,os,re,time
from datetime import date,datetime,timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import requests
from .store import DATA,ROOT,read_json
from .cache import chain

FILE='guru/observations.json.gz'
FORMS={'13F-HR','13F-HR/A','13F-NT','13F-NT/A'}

def stamp():return datetime.now(timezone.utc).isoformat()
def read(path):return json.loads(gzip.decompress(path.read_bytes()))
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    tmp.write_bytes(gzip.compress(json.dumps(obj,ensure_ascii=False,allow_nan=False).encode(),mtime=0));tmp.replace(path)
def settings():return read_json(ROOT/'config/guru_managers.json')['managers']
def resources(asof,vintage=None):
    bases=chain(DATA,vintage or os.environ.get('SANGSANGIN_VINTAGE') or asof);base=bases[-1]
    return SimpleNamespace(as_of=asof,base=base,resource=lambda name:next((p/name for p in reversed(bases) if (p/name).exists()),base/name))
def utc(value):
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('SEC acceptance timestamp needs timezone')
    return t.astimezone(timezone.utc)
def integer(value):
    text=str(value).replace(',','').strip()
    if not re.fullmatch(r'\d+',text):raise ValueError('13F nonnegative integer required')
    return int(text)
def xml(blob):
    if b'<!DOCTYPE' in blob.upper() or b'<!ENTITY' in blob.upper():raise ValueError('Unsupported XML declarations')
    root=ET.fromstring(blob)
    for e in root.iter():e.tag=e.tag.split('}')[-1]
    return root
def value(root,path,default=None):
    e=root.find(path)
    if e is None or e.text is None:
        if default is not None:return default
        raise ValueError('Missing 13F field: '+path)
    return e.text.strip()

def check_meta(meta):
    if meta['form'] not in FORMS or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',meta['accession']):raise ValueError('13F identity')
    if not re.fullmatch(r'\d{10}',meta['cik']):raise ValueError('13F CIK')
    report=date.fromisoformat(meta['report_date']);filed=date.fromisoformat(meta['filing_date']);accepted=utc(meta['accepted_at'])
    if report>filed or accepted.date()>filed:raise ValueError('13F dates')
    # Old filings need an explicit reviewed unit. No inference from dollar size.
    if meta.get('unit') not in ['USD','USD_THOUSANDS']:raise ValueError('13F value unit needs evidence')
    if not (meta['index_url'].startswith('https://www.sec.gov/Archives/edgar/data/'+str(int(meta['cik']))+'/')):raise ValueError('SEC source CIK mismatch')

def row(issuer,share_class,cusip,figi,amount,quantity,kind,option,discretion,managers,sole,shared,none):
    if not issuer.strip() or not share_class.strip() or not re.fullmatch(r'[A-Z0-9*@#]{9}',cusip):raise ValueError('13F security identity')
    kind=kind.upper();option=option.upper()
    if kind not in ['SH','PRN'] or option not in ['', 'PUT','CALL']:raise ValueError('13F position type')
    q=Decimal(str(quantity).replace(',',''))
    if not q.is_finite() or q<0:raise ValueError('13F quantity')
    return dict(issuer=issuer,share_class=share_class,cusip=cusip,figi=figi or None,value=integer(amount),quantity=str(q),quantity_type=kind,option=option or None,discretion=discretion,other_managers=managers,sole=integer(sole),shared=integer(shared),none=integer(none))

def normalized(meta,rows,entry_total,value_total,amendment=None,other_reporting=None,confidential=False):
    check_meta(meta);entry_total=integer(entry_total);value_total=integer(value_total)
    if len(rows)!=entry_total:raise ValueError('13F table count mismatch')
    table_sum=sum(r['value'] for r in rows)
    if meta['form'].endswith('/A') != bool(amendment):raise ValueError('13F amendment metadata mismatch')
    if amendment not in [None,'RESTATEMENT','NEW HOLDINGS']:raise ValueError('Unknown 13F amendment type')
    if meta['form'].startswith('13F-NT') and rows:raise ValueError('13F notice cannot contain holdings')
    return dict(**meta,entries=rows,entry_total=entry_total,value_total=value_total,table_sum=table_sum,reconciliation_difference=table_sum-value_total,amendment=amendment,other_reporting=other_reporting or [],confidential=bool(confidential))

def parse_xml(cover_blob,table_blobs,meta):
    cover=xml(cover_blob)
    if value(cover,'.//submissionType')!=meta['form']:raise ValueError('13F form mismatch')
    cik=value(cover,'.//filerInfo/filer/credentials/cik')
    if cik.zfill(10)!=meta['cik']:raise ValueError('13F cover CIK mismatch')
    period=datetime.strptime(value(cover,'.//reportCalendarOrQuarter'),'%m-%d-%Y').date().isoformat()
    if period!=meta['report_date']:raise ValueError('13F report period mismatch')
    is_amendment=value(cover,'.//isAmendment','false').lower() in ['true','1']
    amendment=value(cover,'.//amendmentType','').upper() if is_amendment else None
    rows=[]
    for blob in table_blobs:
        table=xml(blob)
        if table.tag!='informationTable':raise ValueError('Unexpected 13F table root')
        for e in table.findall('infoTable'):
            rows.append(row(value(e,'nameOfIssuer'),value(e,'titleOfClass'),value(e,'cusip'),value(e,'figi',''),value(e,'value'),value(e,'shrsOrPrnAmt/sshPrnamt'),value(e,'shrsOrPrnAmt/sshPrnamtType'),value(e,'putCall',''),value(e,'investmentDiscretion'),value(e,'otherManager',''),value(e,'votingAuthority/Sole'),value(e,'votingAuthority/Shared'),value(e,'votingAuthority/None')))
    references=[]
    for e in cover.findall('.//otherManager'):
        name=value(e,'name','');c=value(e,'cik','')
        if name:references.append(dict(name=name,cik=c.zfill(10) if c else None))
    return normalized(meta,rows,value(cover,'.//tableEntryTotal','0'),value(cover,'.//tableValueTotal','0'),amendment,references,value(cover,'.//isConfidentialOmitted','false').lower() in ['true','1'])

def parse_reviewed_table(text,meta,entry_total,value_total):
    """Explicit import of a saved SEC rendered table; reject truncated extracts."""
    if '(to the nearest dollar)' not in text or meta['unit']!='USD':raise ValueError('Rendered 13F unit evidence missing')
    rows=[]
    for line in text.splitlines():
        line=re.sub(r'^L\d+:\s*','',line)
        cells=[s.strip() for s in line.split('|')]
        if len(cells)==13 and re.fullmatch(r'[A-Z0-9*@#]{9}',cells[2]):rows.append(row(*cells))
    m=dict(meta,mode='reviewed_sec_rendered',reviewed_at=stamp(),extract_sha256=hashlib.sha256(text.encode()).hexdigest())
    return normalized(m,rows,entry_total,value_total)

def latest(records,cik,asof):
    eligible=[r for r in records if r['cik']==cik and r['filing_date']<=asof and utc(r['accepted_at']).date().isoformat()<=asof and r['report_date']<=asof]
    if not eligible:return None
    period=max(r['report_date'] for r in eligible);items=sorted((r for r in eligible if r['report_date']==period),key=lambda r:(r['accepted_at'],r['accession']))
    state=None;accessions=[]
    for r in items:
        if r['form'].startswith('13F-NT'):
            state=copy.deepcopy(r);state['resolution']='notice';accessions=[r['accession']];continue
        if not r['amendment'] or r['amendment']=='RESTATEMENT':
            state=copy.deepcopy(r);accessions=[r['accession']]
        elif state and state.get('resolution')=='holdings':
            if state['unit']!=r['unit']:raise ValueError('13F amendment units differ')
            state['entries']+=copy.deepcopy(r['entries']);state['entry_total']+=r['entry_total'];state['value_total']+=r['value_total'];state['accepted_at']=r['accepted_at'];state['filing_date']=r['filing_date'];state['confidential']|=r['confidential'];accessions.append(r['accession'])
        else:
            state=copy.deepcopy(r);state['resolution']='amendment_base_missing';accessions=[r['accession']];continue
        state['resolution']='holdings'
    state['table_sum']=sum(r['value'] for r in state['entries']);state['reconciliation_difference']=state['table_sum']-state['value_total']
    state['accessions']=accessions;return state

class Refused(Exception):pass
def collect(d,contact=None,session=None,now=None,pause=time.sleep):
    now=now or datetime.now(timezone.utc);path=d.resource(FILE);old=read(path) if path.exists() else {};packet=copy.deepcopy(old);packet.setdefault('filings',[])
    cfg=settings();config_hash=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
    if contact is None:
        local=DATA/'runtime/sec-contact.json';contact=read_json(local).get('email','') if local.exists() else ''
    contact_hash=hashlib.sha256(contact.encode()).hexdigest();previous=old.get('collection',{});report=dict(attempted_at=now.isoformat(),status='needs_contact',requests=0,errors=[],config_hash=config_hash,contact_hash=contact_hash)
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',contact):
        packet['collection']=report;save(d.base/FILE,packet);return report
    same=previous.get('contact_hash')==contact_hash and previous.get('config_hash')==config_hash
    if same and previous.get('status')=='access_refused':return dict(previous,requests=0,cached=True)
    if same and previous.get('attempted_at') and 0<=(now-utc(previous['attempted_at'])).total_seconds()<86400:return dict(previous,requests=0,cached=True)
    own=session is None;session=session or requests.Session();known={r['accession']:r for r in packet['filings']}
    def fetch(url):
        host=urlsplit(url).hostname
        if host not in ['data.sec.gov','www.sec.gov'] or not url.startswith('https://'):raise ValueError('SEC source URL')
        pause(1);report['requests']+=1;r=session.get(url,timeout=(10,30),headers={'User-Agent':'SangsanginResearch '+contact},allow_redirects=False)
        if r.status_code in [401,403,429]:raise Refused(str(r.status_code))
        if r.status_code!=200:raise ValueError('SEC HTTP '+str(r.status_code))
        return r.content
    try:
        report['status']='ok'
        for manager in cfg:
            cik=manager['cik'];raw=fetch('https://data.sec.gov/submissions/CIK'+cik+'.json');data=json.loads(raw)
            if str(data['cik']).zfill(10)!=cik:raise ValueError('SEC submissions CIK')
            recent=data['filings']['recent'];n=len(recent.get('accessionNumber',[]))
            if any(len(v)!=n for v in recent.values()):raise ValueError('SEC submissions alignment')
            rows=[{k:v[i] for k,v in recent.items()} for i in range(n)]
            rows=[r for r in rows if r['form'] in FORMS and r['filingDate']<=d.as_of]
            if not rows:report['errors'].append(dict(cik=cik,reason='recent_metadata_missing_13f'));continue
            period=max(r['reportDate'] for r in rows)
            save(d.base/('guru/submissions/'+cik+'.json.gz'),data)
            for r in sorted((r for r in rows if r['reportDate']==period),key=lambda r:r['acceptanceDateTime']):
                accession=r['accessionNumber']
                if accession in known:continue
                prefix='https://www.sec.gov/Archives/edgar/data/'+str(int(cik))+'/'+accession.replace('-','')+'/'
                meta=dict(cik=cik,accession=accession,form=r['form'],report_date=r['reportDate'],filing_date=r['filingDate'],accepted_at=utc(r['acceptanceDateTime']).isoformat(),index_url=prefix+accession+'-index.html',unit='USD',mode='direct_xml',retrieved_at=now.isoformat())
                if meta['filing_date']<'2023-01-03':raise ValueError('Historical 13F unit requires review')
                check_meta(meta);cover_name=Path(r['primaryDocument']).name
                if not re.fullmatch(r'[A-Za-z0-9_.-]+\.xml',cover_name):raise ValueError('13F primary XML filename')
                cover=fetch(prefix+cover_name);tables=[];names=[]
                if r['form'].startswith('13F-HR'):
                    index=json.loads(fetch(prefix+'index.json'))
                    names=[x['name'] for x in index['directory']['item'] if re.fullmatch(r'[A-Za-z0-9_.-]+\.xml',x['name']) and x['name']!=cover_name]
                    tables=[fetch(prefix+name) for name in names]
                parsed=parse_xml(cover,tables,meta)
                save(d.base/('guru/raw/'+accession+'.json.gz'),dict(cover=cover.decode('utf-8'),tables=[b.decode('utf-8') for b in tables],table_names=names))
                packet['filings'].append(parsed);known[accession]=parsed
        if report['errors']:report['status']='partial'
        report['succeeded_at']=now.isoformat()
    except Refused as e:report.update(status='access_refused',http_status=int(str(e)))
    except (ValueError,KeyError,ET.ParseError,requests.RequestException):report['status']='error'
    finally:
        if own:session.close()
    if report['status']!='ok' and previous.get('succeeded_at'):report['succeeded_at']=previous['succeeded_at']
    packet['collection']=report;save(d.base/FILE,packet);return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();r=collect(resources(a.as_of));print('13F',r['status'],'requests',r['requests'])
if __name__=='__main__':main()

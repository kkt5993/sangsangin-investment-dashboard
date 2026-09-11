"""SEC ownership XML, acceptance timestamps, and a bounded collector.

No account, proxy, or credential. A 403/429 stops the whole collection attempt.
Source-reviewed public facts can coexist with directly collected documents.
"""
import argparse,gzip,json,re,time
from pathlib import Path
from xml.etree import ElementTree as ET
import pandas as pd
import requests
from .engine import Data,number
from .store import ROOT,read_json
from .events_data import read,save
from .acquire import stamp

USER_AGENT='SangsanginResearch/1.0 https://github.com/kkt5993/sangsangin-investment-dashboard'
SEC='https://www.sec.gov/Archives/edgar/data/'

def accepted_utc(value,index_time=False):
    if not value:return None
    try:
        t=pd.Timestamp(value)
        if pd.isna(t):return None
        if t.tzinfo is None:
            if not index_time:return None
            t=t.tz_localize('America/New_York',ambiguous='raise',nonexistent='raise')
        return t.tz_convert('UTC').isoformat()
    except (ValueError,TypeError):return None

def parse_ownership(blob,metadata):
    if b'<!DOCTYPE' in blob.upper() or b'<!ENTITY' in blob.upper():raise ValueError('Unsupported ownership XML')
    root=ET.fromstring(blob)
    for e in root.iter():e.tag=e.tag.rsplit('}',1)[-1]
    if root.tag!='ownershipDocument':raise ValueError('Not ownership XML')
    text=lambda node,path:node.findtext(path,default='').strip()
    form=text(root,'documentType')
    if form not in ['4','4/A']:raise ValueError('Not Form4')
    cik=lambda v:str(int(v)).zfill(10) if str(v).isdigit() else None
    issuer=cik(text(root,'issuer/issuerCik'))
    if metadata.get('issuer_cik') and issuer!=str(metadata['issuer_cik']).zfill(10):raise ValueError('Issuer does not match submissions index')
    owners=[]
    for e in root.findall('reportingOwner'):
        owner=dict(cik=cik(text(e,'reportingOwnerId/rptOwnerCik')),name=text(e,'reportingOwnerId/rptOwnerName'),
            officer_title=text(e,'reportingOwnerRelationship/officerTitle'),director=text(e,'reportingOwnerRelationship/isDirector') in ['1','true'],
            officer=text(e,'reportingOwnerRelationship/isOfficer') in ['1','true'],ten_percent=text(e,'reportingOwnerRelationship/isTenPercentOwner') in ['1','true'])
        if not owner['cik']:raise ValueError('Reporting CIK missing')
        owners.append(owner)
    if not owners:raise ValueError('No reporting owner')
    footnotes={e.attrib.get('id'):''.join(e.itertext()) for e in root.findall('footnotes/footnote')}
    rows=[]
    for table,kind in [('nonDerivativeTable','nonDerivative'),('derivativeTable','derivative')]:
        for i,e in enumerate(root.findall(table+'/'+kind+'Transaction')):
            refs=[r.attrib.get('id') for r in e.findall('.//transactionPricePerShare/footnoteId')]
            notes=' '.join(footnotes.get(k,'') for k in refs).lower()
            rows.append(dict(line=i+1,kind=kind,security=text(e,'securityTitle/value'),date=text(e,'transactionDate/value'),
                code=text(e,'transactionCoding/transactionCode'),side=text(e,'transactionAmounts/transactionAcquiredDisposedCode/value'),
                shares=number(text(e,'transactionAmounts/transactionShares/value')),price=number(text(e,'transactionAmounts/transactionPricePerShare/value')),
                ownership=text(e,'ownershipNature/directOrIndirectOwnership/value'),weighted_price='weighted' in notes and 'price' in notes,
                price_footnotes=refs))
    flag=text(root,'aff10b5One')
    return dict(accession=metadata['accession'],issuer_cik=issuer,symbol=text(root,'issuer/issuerTradingSymbol'),issuer_name=text(root,'issuer/issuerName'),
        form=form,original_filing_date=text(root,'dateOfOriginalSubmission') or None,accepted_at=accepted_utc(metadata.get('accepted_at')),
        filing_date=metadata.get('filing_date'),source_url=metadata['source_url'],index_url=metadata.get('index_url'),
        retrieved_at=metadata.get('retrieved_at') or stamp(),mode='direct_xml',plan10b5=flag in ['1','true'] if flag else None,owners=owners,transactions=rows)

def records(d):
    """Accession identity prevents source-review + API double counting."""
    seed=ROOT/'config/sec_ownership_reviews.json'
    out={r['accession']:r for r in read_json(seed)['filings']} if seed.exists() else {}
    for base in d.bases:
        folder=base/'sec/parsed'
        if not folder.exists():continue
        for p in sorted(folder.glob('*.json.gz')):
            r=read(p);out[r['accession']]=r
    return list(out.values())

def candidate_symbols(d):
    return sorted({p.name.removesuffix('.json.gz') for b in d.bases for p in (b/'events').glob('*.json.gz')})

class AccessRefused(RuntimeError):pass

def fetch(session,url,base,filename):
    time.sleep(1)
    r=session.get(url,timeout=25)
    if r.status_code in [401,403,429]:raise AccessRefused('HTTP '+str(r.status_code))
    r.raise_for_status()
    encoded=gzip.compress(r.content,mtime=0);p=base/filename;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded)
    return r.content

def collect(d,max_filings=300):
    """Daily metadata, immutable accession cache, and bounded initial backfill."""
    state=d.resource('sec_collection.json.gz')
    if state.exists():
        prior=read(state)
        if (pd.Timestamp.now(tz='UTC')-pd.Timestamp(prior['retrieved_at'])).total_seconds()<86400:return prior
    report=dict(retrieved_at=stamp(),status='running',source='SEC EDGAR',issuers=[],documents=0,parsed=0,errors=[],remaining=0)
    symbols=candidate_symbols(d);known={r['accession'] for r in records(d) if r.get('mode')=='direct_xml'}
    session=requests.Session();session.headers.update({'User-Agent':USER_AGENT,'Accept-Encoding':'gzip, deflate'})
    start=str((pd.Timestamp(d.as_of)-pd.Timedelta(days=120)).date())
    try:
        mapping=json.loads(fetch(session,'https://www.sec.gov/files/company_tickers.json',d.base/'sec','company_tickers.json.gz'))
        lookup={r['ticker'].replace('.','-'):str(r['cik_str']).zfill(10) for r in mapping.values()}
        for symbol in symbols:
            cik=lookup.get(symbol)
            if not cik:report['errors'].append(dict(symbol=symbol,error='CIK missing'));continue
            data=json.loads(fetch(session,'https://data.sec.gov/submissions/CIK'+cik+'.json',d.base/'sec','submissions_'+cik+'.json.gz'))
            f=data.get('filings',{}).get('recent',{});rows=[dict(zip(f,[f[k][i] for k in f])) for i in range(len(f.get('form',[])))]
            scoped=[r for r in rows if r['form'] in ['4','4/A'] and start<=r['filingDate']<=d.as_of]
            report['issuers'].append(dict(symbol=symbol,cik=cik,filings=len(scoped),oldest=min(f.get('filingDate') or ['']),recent_window_complete=bool(f.get('filingDate')) and min(f['filingDate'])<=start))
            for r in sorted(scoped,key=lambda r:r['acceptanceDateTime']):
                accession=r['accessionNumber']
                if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession):report['errors'].append(dict(symbol=symbol,error='Invalid accession'));continue
                if accession in known:continue
                if report['documents']>=max_filings:report['remaining']+=1;continue
                # PrimaryDocument may include an SEC XSL display directory.
                name=Path(r['primaryDocument']).name
                if not re.fullmatch(r'[A-Za-z0-9_.-]+\.xml',name):report['errors'].append(dict(accession=accession,error='XML primary document unavailable'));continue
                prefix=SEC+str(int(cik))+'/'+accession.replace('-','')+'/'
                meta=dict(accession=accession,issuer_cik=cik,accepted_at=r['acceptanceDateTime'],filing_date=r['filingDate'],source_url=prefix+name,index_url=prefix+accession+'-index.htm',retrieved_at=stamp())
                report['documents']+=1
                try:
                    blob=fetch(session,meta['source_url'],d.base/'sec/raw',accession+'.xml.gz');parsed=parse_ownership(blob,meta);save(d.base/'sec/parsed'/(accession+'.json.gz'),parsed);report['parsed']+=1;known.add(accession)
                except AccessRefused:raise
                except (ValueError,ET.ParseError,requests.RequestException) as e:report['errors'].append(dict(accession=accession,error=type(e).__name__))
        report['status']='partial' if report['remaining'] or report['errors'] or any(not r['recent_window_complete'] for r in report['issuers']) else 'ok'
    except AccessRefused as e:report.update(status='access_refused',error=str(e))
    except (ValueError,requests.RequestException) as e:report.update(status='error',error=type(e).__name__)
    finally:session.close()
    save(d.base/'sec_collection.json.gz',report);return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);p.add_argument('--max-filings',type=int,default=300);a=p.parse_args();r=collect(Data(a.as_of),a.max_filings);print('SEC',r['status'],'documents',r['documents'],'parsed',r['parsed'])
if __name__=='__main__':main()

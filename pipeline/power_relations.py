"""Reviewed power purchase agreements; MW is not a shock coefficient or live flow."""
import copy
import math
from datetime import date, datetime
from urllib.parse import urlsplit
from .store import ROOT, read_json
from .events_data import read

MANIFEST='relations/power_sources.json.gz'

def settings():
    c=read_json(ROOT/'config/power_relations.json');validate(c);return c

def validate(c):
    assert c['version']==1
    symbols={r['symbol'] for r in c['companies']};assert len(symbols)==len(c['companies'])
    ids=set()
    for s in c['sources'].values():
        u=urlsplit(s['url']);assert u.scheme=='https' and u.hostname and not u.username and not u.password
        assert datetime.fromisoformat(s['reviewed_at']).tzinfo is not None
        assert date.fromisoformat(s['published_on'])<=datetime.fromisoformat(s['reviewed_at']).date()
    for r in c['contracts']:
        assert r['id'] not in ids;ids.add(r['id'])
        assert r['source'] in symbols and r['target'] in symbols and r['source']!=r['target']
        assert r['source_ids'] and set(r['source_ids'])<=c['sources'].keys()
        assert r['announced_on']==c['sources'][r['source_ids'][0]]['published_on']
        assert datetime.fromisoformat(r['reviewed_at']).tzinfo is not None
        for k in ['term_years','contract_mw','facility_mw']:
            v=r[k];assert v is None or type(v) in (int,float) and math.isfinite(v) and v>0
        assert all(r[k] for k in ['facility','delivery_status','schedule','note'])

def collect(d,**kwargs):
    from .chain_evidence import collect as check
    return check(d,config=settings(),manifest=MANIFEST,folder='relations/power_evidence',**kwargs)

def links(d,config=None):
    c=config or settings();validate(c)
    path=d.resource(MANIFEST) if hasattr(d,'resource') else None
    records=read(path).get('sources',{}) if path and path.exists() else {}
    out=[]
    for row in c['contracts']:
        # An announcement and its later amendments must all predate the price cutoff.
        if max(c['sources'][k]['published_on'] for k in row['source_ids'])>d.as_of:continue
        r=copy.deepcopy(row);r['sources']=[]
        for k in row['source_ids']:
            source=c['sources'][k];record=records.get(k,{})
            if record.get('url')!=source['url']:record={}
            r['sources'].append(dict(source,id=k,checked_at=record.get('checked_at'),attempted_at=record.get('attempted_at'),
                changed_since_review=record.get('changed_since_review',False),error_type=record.get('error_type')))
        out.append(dict(id='power:'+r['id'],source='stock:'+r['source'],target='stock:'+r['target'],relation='powers',weight=1,
            url=r['sources'][0]['url'],reviewed_at=r['reviewed_at'],evidence='공식 전력구매계약 발표',
            basis=r['facility']+' · '+r['delivery_status']+' · '+r['schedule'],contract=r))
    return out

def verify(graph,as_of):
    expected={r['id']:r for r in settings()['contracts'] if max(settings()['sources'][k]['published_on'] for k in r['source_ids'])<=as_of}
    actual=[e for e in graph['links'] if e.get('contract')]
    assert {e['contract']['id'] for e in actual}==expected.keys()
    for e in actual:
        r=e['contract'];original=expected[r['id']]
        assert all(r[k]==v for k,v in original.items())
        assert e['source']=='stock:'+r['source'] and e['target']=='stock:'+r['target'] and e['relation']=='powers' and e['weight']==1
        assert r['announced_on']<=as_of
        assert all(s['published_on']<=as_of for s in r['sources'])


if __name__=='__main__':
    import argparse,json,os
    from .guru_data import resources
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args()
    r=collect(resources(a.as_of,os.environ['SANGSANGIN_VINTAGE']))
    print(json.dumps(dict(sources=len(r['sources']),requested=sum(t['requested'] for t in r['attempts']))))

"""Explicit research aliases mapped to previously verified securities, not guessed tickers."""
from datetime import datetime,date
from urllib.parse import urlsplit
from .store import ROOT,read_json

def settings():
    c=read_json(ROOT/'config/relation_universe.json')
    additions=read_json(ROOT/'config/relation_universe_additions.json')
    assert additions['version']==1
    c={**c,'companies':c['companies']+additions['companies'],
       'unresolved':additions['unresolved'], 'reviewed_at':additions['reviewed_at'],
       'note':additions['note']}
    validate(c);return c

def price_symbols():
    """Explicit source-identified relation instruments for incremental prices."""
    return sorted(r['symbol'] for r in settings()['companies'])

def validate(c):
    assert c['version']==1 and datetime.fromisoformat(c['reviewed_at']).tzinfo is not None
    symbols=set();aliases=set()
    for r in c['companies']:
        assert r['symbol'] not in symbols;symbols.add(r['symbol'])
        assert r['market'] in ['US','KR'] and r['name'] and r['aliases']
        assert r['symbol'].endswith(('.KS','.KQ'))==(r['market']=='KR')
        for a in r['aliases']:assert a not in aliases;aliases.add(a)
        u=urlsplit(r['identity']['source']);assert u.scheme=='https' and u.hostname and not u.username and not u.password
        date.fromisoformat(r['identity']['as_of']);assert r['identity']['method'] and r['identity']['name']
    for r in c['unresolved']:assert r['alias'] not in aliases;aliases.add(r['alias']);assert r['reason']
    assert len(aliases)==c['reference_objects']
    # TEL is the research alias for Tokyo Electron, not the US security TEL.
    assert not any('TEL' in r['aliases'] and r['symbol']=='TEL' for r in c['companies'])

def coverage(graph):
    c=settings();nodes={n['symbol']:n for n in graph['nodes'] if n.get('symbol')};rows=[]
    for r in c['companies']:
        n=nodes[r['symbol']];edges=[e for e in graph['links'] if n['id'] in (e['source'],e['target']) and e['relation']!='correlated']
        rows.append(dict(r,id=n['id'],price_date=n.get('date'),business_relations=len(edges),entity=n['entity']))
    return dict(reference_objects=c['reference_objects'],reference_priced_count=c['reference_priced_count'],mapped_aliases=sum(len(r['aliases']) for r in rows),
        companies=rows,unresolved=c['unresolved'],note=c['note'],reviewed_at=c['reviewed_at'])

def verify(graph):
    current=settings();nodes={n['symbol']:n for n in graph['nodes'] if n.get('symbol')}
    stored=graph['universe_coverage']
    # A public snapshot can legitimately predate a newly staged mapping.  It
    # remains valid only as a self-contained historical coverage report; a
    # freshly built graph must contain every current configured symbol.
    if all(r['symbol'] in nodes for r in current['companies']):
        expected=coverage(graph);assert stored==expected
    else:
        rows=stored.get('companies',[]);assert rows and all(r['symbol'] in nodes for r in rows)
        assert stored['mapped_aliases']==sum(len(r['aliases']) for r in rows)
        assert len({a for r in rows for a in r['aliases']})==stored['mapped_aliases']
        assert stored['reference_objects']>=stored['mapped_aliases']+len(stored['unresolved'])
    aliases={a:r['symbol'] for r in stored['companies'] for a in r['aliases']}
    assert aliases['HANMI']=='042700.KS' and aliases['008930']=='008930.KS'
    assert aliases['APPLEINC']==aliases['AAPL'] and aliases['CHEVRONCORPO']==aliases['CVX']

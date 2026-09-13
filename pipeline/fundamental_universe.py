"""Financial coverage from inherited, dated membership; no raw CSV reparsing."""
import re
from types import SimpleNamespace
from .cache import chain
from .store import read_json,digest
from .events_data import read,save
from .company_fundamentals import collect as collect_companies,usable_fund

MEMBERSHIPS=('us_largecap','us100','kr_largecap','kr_screen','kospi200')
REPORT='fundamental_universe/collection.json.gz'
MANIFEST='fundamental_universe/manifest.json.gz'


def context(base):
    bases=chain(base.parent.parent,base.name) if (base/'parent.json').exists() else [base]
    def resource(name):return next((b/name for b in reversed(bases) if (b/name).exists()),base/name)
    fund={}
    for b in bases:
        for path in sorted((b/'fundamentals').glob('*.json*')):
            if path.suffix not in ('.json','.gz'):continue
            raw=read(path) if path.suffix=='.gz' else read_json(path)
            if usable_fund(raw):fund[raw['symbol']]=raw
    return SimpleNamespace(base=base,bases=bases,fund=fund,resource=resource)


def inventory(d):
    from .catalog import reference_stocks
    from .strategy_cards import settings
    groups={};sources=[]
    def add(symbol,group):
        if not isinstance(symbol,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*',symbol):
            raise ValueError('Invalid financial universe symbol')
        groups.setdefault(symbol,set()).add(group)
    for row in reference_stocks():add(row['symbol'],'reference_stocks')
    for symbol in settings()['fundamental_support']:add(symbol,'fundamental_support')
    for key in MEMBERSHIPS:
        path=d.resource(key+'.json')
        if not path.exists():continue
        packet=read_json(path)
        if not isinstance(packet.get('members'),list):raise ValueError('Membership rows required: '+key)
        for row in packet['members']:add(row['symbol'],key)
        sources.append(dict(group=key,vintage=path.parent.name,as_of=packet.get('as_of'),
            retrieved_at=packet.get('retrieved_at'),source=packet.get('source'),sha256=digest(path),members=len(packet['members'])))
    return dict(targets=[dict(symbol=s,groups=sorted(groups[s])) for s in sorted(groups)],sources=sources)


def collect(base,limit=0,symbols=None,**kwargs):
    if limit<0:raise ValueError('Negative selection limit')
    d=context(base);manifest=inventory(d);targets=manifest['targets']
    if symbols is not None:
        wanted=set(symbols)
        if not wanted<={r['symbol'] for r in targets}:raise ValueError('Selection outside documented universe')
        targets=[r for r in targets if r['symbol'] in wanted]
    targets=targets[:limit] if limit else targets
    manifest.update(expected=len(manifest['targets']),selected=len(targets),selected_symbols=[r['symbol'] for r in targets],selection_limit=limit)
    save(base/MANIFEST,manifest)
    return collect_companies(d,targets=targets,kinds=('financial',),report_path=REPORT,stop_on_refusal=True,**kwargs)

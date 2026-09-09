"""Financial/date/shape invariants for every new public snapshot, offline."""
from pathlib import Path
import json,math,re
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text(encoding='utf8'),parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))

def series(s,cutoff,forecast=False):
    pts=s.get('points',[]);dates=[p[0] for p in pts]
    assert dates==sorted(set(dates)),s.get('name')
    assert all(len(p)==2 and isinstance(p[1],(int,float)) and math.isfinite(p[1]) for p in pts)
    if not forecast:assert all(date.fromisoformat(t)<=date.fromisoformat(cutoff) for t in dates),(s.get('name'),dates[-1],cutoff)

def section(s,cutoff,module):
    kind=s['type']
    if kind=='rebalancing':
        assert s['stocks'] and len(s['indices'])==3
        for r in s['stocks']+s['indices']:
            assert r['coefficient']>0 and r['aum']>0 and len(r['funds'])>0
            if r['adv'] is not None:assert r['adv']>0 and r['price_date']<=cutoff
    if kind=='table':assert all(len(r)==len(s['columns']) for r in s['rows']),s['title']
    if kind=='heatmap':assert all(len(r['values'])==len(s['columns']) for r in s['rows']),s['title']
    if kind=='line':
        for line in s['series']:series(line,cutoff,s.get('forecast',False))
    if kind=='dynamics':
        a=s['surface'];assert a['windows']==[5,10,20,40,60,90,120,180];assert len(a['dates'])==len(a['values']);assert all(len(r)==8 for r in a['values']);assert a['dates'][-1]<=cutoff
        assert 0<=s['current']['risk']<=100 and 0<=s['current']['exposure']<=1.5
        for c in s['charts']:section(c,cutoff,module)
    if kind=='candles':
        for key in ['candles','weekly']:
            a=s[key];assert [x[0] for x in a]==sorted(set(x[0] for x in a));assert a[-1][0]<=cutoff
            for row in a:
                _,o,h,l,c,v=row;assert all(math.isfinite(x) for x in row[1:]);assert l<=min(o,c)<=max(o,c)<=h;assert v>=0
        if s.get('pattern'):
            p=s['pattern'];assert p['confirmed_at']<=cutoff and all(t<=cutoff for t,v in p['points'])
            assert 0<=p['score']<=100
    if kind=='ml':
        for c in s['charts']:section(c,cutoff,module)
        for r in s['records']:
            assert r['train_target_end']<=r['origin']<r['target']
            assert r['origin']<=cutoff
            if r['probability'] is not None:assert 0<=r['probability']<=100 and r['calibration_observations']>=24
            if r['interval']:assert r['interval']['0.05']<=r['interval']['0.16']<=r['interval']['0.84']<=r['interval']['0.95']
    if kind=='graph':
        ids={n['id'] for n in s['nodes']};assert len(ids)==len(s['nodes'])
        assert all(e['source'] in ids and e['target'] in ids for e in s['links'])
        assert all(len(n['position'])==3 and all(math.isfinite(x) for x in n['position']) for n in s['nodes'])
    if kind=='scatter3d':assert all(all(isinstance(p[k],(int,float)) and math.isfinite(p[k]) for k in ['x','y','z']) for p in s['points'])
    if kind=='globe':assert all(-180<=c['lon']<=180 and -90<=c['lat']<=90 and c['count']==len(c['companies']) for c in s['countries'])
    if kind=='etf':assert all(len(r['returns'])==4 and r['payments']>=0 and r['as_of']<=cutoff for r in s['rows'])
    if kind=='wordcloud':assert all(w['count']>0 and isinstance(w['count'],int) and w['term'] for w in s['words'])
    if kind=='scenario':assert all(math.isfinite(r['beta']) and 0<=r['r2']<=1 and r['observations']>=200 for r in s['rows'])
    if kind=='gauges':
        for a in s['items']:
            assert a['min']<a['max'] and a['cuts']==sorted(a['cuts'])
            if a['value'] is not None:assert math.isfinite(a['value']) and a['date']<=cutoff
    if kind=='industry':
        assert len(s['items'])==39 and len({a['sector'] for a in s['items']})==13
        for a in s['items']:
            assert a['value'] is not None and a['date']<=cutoff
            series(dict(name=a['name'],points=a['spark']),cutoff)
    if kind=='hologram':
        assert len(s['axes'])==5 and len(s['rows'])==36
        assert [r['date'] for r in s['rows']]==sorted(set(r['date'] for r in s['rows']))
        for row in s['rows']:
            assert row['date']<=cutoff and set(row['raw'])==set(a['key'] for a in s['axes'])
            assert all(v is None or math.isfinite(v) for v in [*row['raw'].values(),*row['z'].values()])
    if kind=='optionprofile':
        assert s['price_date']<=cutoff and s['spot']>0 and s['valid_gamma']<=s['valid_oi']<=s['contracts']
        ks=[p['strike'] for p in s['profile']];assert ks==sorted(set(ks))
        for r in s['profile']:
            assert r['call_oi']>=0 and r['put_oi']>=0
            assert r['gamma_available']==(r['gex'] is not None)
        if s['flip'] is not None:assert .8*s['spot']<=s['flip']<=1.2*s['spot']
        if s['em'] is not None:assert s['em_low']<s['spot']<s['em_high']

count=0
for file in (ROOT/'docs/data').glob('*.json'):
    d=load(file)
    if not isinstance(d,dict) or d.get('schema_version')!=2:continue
    assert d['module']==file.stem and d['method_note'] and d['source'] and d['sections']
    groups={s.get('group','종합') for s in d['sections']}
    for v in d['subviews']:
        assert (v['status']=='connected')==(v['name'] in groups)
        assert v['sections']==sum(s.get('group','종합')==v['name'] for s in d['sections'])
        if v['status']=='pending':assert v['reason']
    for s in d['sections']:section(s,d['as_of'],d['module'])
    count+=1
assert count==21,(count,'new schema modules expected')
meta=load(ROOT/'docs/data/status.json');assert len(meta['modules'])==25 and meta['implemented']==23
assert meta['universes']['KR']['expected']==100 and 450<=meta['universes']['US']['expected']<=550
assert 'rosenbach' not in meta['modules']
quality=meta['price_quality'];assert re.fullmatch('[a-f0-9]{64}',quality['sha256']);assert quality['corrected']>=0 and quality['quarantined']>=0
rankings=load(ROOT/'docs/data/rs.json')['stock_rankings']
for r in rankings.values():assert r['expected']==r['available']+len(r['excluded']) and r['membership_as_of']<=meta['as_of']
for s in load(ROOT/'docs/data/ml.json')['sections']:
    if s['type']=='ml':assert s['origin']<meta['as_of'] and s['latest']['target']>s['origin']
print('PASS:',count,'new modules; dated observations, forecast maturity, intervals, OHLC, official coverage, graph and table shapes.')

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
    if kind=='valuation':
        assert len(s['panels'])==3
        for p in s['panels']:
            assert len(p['rows'])==180
            for r in p['rows']:
                assert r['date']<=cutoff and r['profit_period']<=r['date']
                assert r['price']>0 and r['earnings']>0 and abs(r['price']/r['earnings']-r['ratio'])<1e-5
                assert r['carry']==(r['date']>p['last_profit_period'])
    if kind=='rebalancing':
        assert s['stocks'] and len(s['indices'])==3
        for r in s['stocks']+s['indices']:
            assert r['coefficient']>0 and r['aum']>0 and len(r['funds'])>0
            if r['adv'] is not None:assert r['adv']>0 and r['price_date']<=cutoff
    if kind=='entities':
        assert len({e['id'] for e in s['entities']})==len(s['entities'])
        for e in s['entities']:
            assert e['id']=='stock:'+e['symbol'] and e['date']<=cutoff and len(e['returns'])==5
            assert len(e['curve'])<=14 and e['curve'][0][1]==100 and e['curve'][-1][0]<=cutoff
            b=e['sensitivity']
            if b:assert b['observations']>=200 and b['start']<b['end']<=cutoff and (b['r2'] is None or 0<=b['r2']<=1)
    if kind=='table':assert all(len(r)==len(s['columns']) for r in s['rows']),s['title']
    if kind=='discovery':
        assert len(s['buckets'])==4 and len(s['items'])<=120
        assert len({r['symbol'] for r in s['items']})==len(s['items'])
        for r in s['items']:
            assert r['bucket'] in [b['name'] for b in s['buckets']] and r['price_date']<=cutoff
            assert all(r[k] is None or -3<=r[k]<=3 for k in ['score','tech','fund','smart'])
            if r['market']=='KR':assert r['score']==r['tech']
            elif r['fund'] is None or r['smart'] is None:assert r['score'] is None
            else:assert abs(r['score']-(.45*r['tech']+.3*r['fund']+.25*r['smart']))<1e-5
    if kind=='scanner':
        assert len(s['items'])==37 and len({r['symbol'] for r in s['items']})==37
        for r in s['items']:
            assert r['date']<=cutoff and len(r['candles'])==90 and len(r['rules'])==12
            assert r['score']==sum(a['value'] for a in r['rules'] if a['value'] is not None)
            assert r['available']==sum(a['value'] is not None for a in r['rules'])
            assert all(a['value'] in [-1,0,1,None] for a in r['rules'])
            assert r['rsi'] is None or 0<=r['rsi']<=100
            assert r['adx'] is None or 0<=r['adx']<=100
            assert r['candles'][-1][0]<=cutoff
            assert [a['name'] for a in r['lines']]==['MA20','MA60']
            assert all(len(a['values'])==90 for a in r['lines'])
    if kind=='allocation':
        assert abs(sum(r['value'] for r in s['weights'])-100)<1e-3
        assert all(0<=r['value']<=100 for r in s['weights'])
        section(s['chart'],cutoff,module);section(s['performance'],cutoff,module)
    if kind in ['heatmap','preference']:assert all(len(r['values'])==len(s['columns']) for r in s['rows']),s['title']
    if kind=='line':
        for line in s['series']:series(line,cutoff,s.get('forecast',False))
        for z in s.get('zones',[]):assert z['start']<z['end']<=cutoff and z['kind'] in ['high','low']
    if kind=='modelleaderboard':
        assert len(s['panels'])==3
        for p in s['panels']:
            assert len(p['rows'])==13 and len({r['name'] for r in p['rows']})==13
            assert all(len(r['values'])==2 and all(v is None or 0<=v<=100 for v in r['values']) for r in p['rows'])
    if kind=='lagcorrelation':
        assert [r['name'] for r in s['rows']]==[str(i) for i in range(-2,4)]
        assert all(r['observations']>=24 and (r['value'] is None or -1<=r['value']<=1) for r in s['rows'])
    if kind=='featureselection':
        assert len(s['panels'])==2
        for p in s['panels']:assert p['repeats']==12 and all(0<=r['value']<=12 for r in p['rows'])
    if kind=='shap':
        assert len(s['rows'])==15 and s['additive_error']<=1e-6 and 'not OOS' in s['scope']
        assert s['training_end']<=cutoff and len(s['dates'])<=120 and s['dates']==sorted(set(s['dates']))
        for r in s['rows']:assert len(r['points'])==len(s['dates']) and all(math.isfinite(p[0]) and 0<=p[1]<=1 for p in r['points'])
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
        if s.get('detail_table'):
            section(s['detail_table'],cutoff,module)
            assert len(s['detail_table']['rows'])==24 and len(s['diagnostics']['models'])==13
        for r in s['records']:
            assert r['train_target_end']<=r['origin']<r['target']
            assert r['origin']<=cutoff
            if r['probability'] is not None:assert 0<=r['probability']<=100 and r['calibration_observations']>=24
            if r['interval']:assert r['interval']['0.05']<=r['interval']['0.16']<=r['interval']['0.84']<=r['interval']['0.95']
            if r.get('selected_model'):
                assert len(r['models'])==13 and r['prediction']==r['models'][r['selected_model']]
                assert r['lstm_fit_origin']<=r['origin'] and r['transformer_fit_origin']<=r['origin']
                assert 0<r['feature_count']<=142
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

"""Financial/date/shape invariants for every new public snapshot, offline."""
from pathlib import Path
import json,math,re,base64,struct
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
    if kind=='earningsglobal':
        assert len(s['rows'])<=20 and s['available']<=s['expected']
        assert [r['values'][0] for r in s['rows']]==sorted([r['values'][0] for r in s['rows']],reverse=True)
        for r in s['rows']:
            assert len(r['values'])==3 and len(r['forecast_periods'])==2 and r['actual_period']<=cutoff and r['fx']['date']<=cutoff
    if kind=='earningsestimates':
        assert len(s['cards'])==(2 if s['market']=='KR' else 10)
        for c in s['cards']:
            assert len(c['metrics'])==2 and c['source'].startswith('https://')
            for m in c['metrics']:
                assert all(r['kind'] in ['actual','estimate'] for r in m['rows'])
                assert all(r['period']<=cutoff for r in m['rows'] if r['kind']=='actual')
                assert all(r['value'] is None or isinstance(r['value'],(int,float)) for r in m['rows'])
    if kind=='earningsactual':
        assert len({r['symbol'] for r in s['cards']})==len(s['cards'])
        for c in s['cards']:
            for key,maximum in [('annual',4),('quarterly',8)]:
                dates=[r['period'] for r in c[key]];assert dates==sorted(set(dates)) and len(dates)<=maximum and all(t<=cutoff for t in dates)
    if kind in ['geosituations','geokeywords','geochannels']:
        ids={r['id'] for r in s['news']};assert len(ids)==len(s['news'])
        for r in s['news']:assert r['date']<=cutoff and r['direction'] in [-1,0,1] and r['url'].startswith('https://') and r['first_seen']
    if kind=='geosituations':
        assert len(s['topics'])==15 and len({r['category'] for r in s['topics']})==4
        for r in s['topics']:assert r['attention']==r['count']+r['risk']*2 and set(r['articles'])<=ids
    if kind=='geokeywords':
        assert len(s['terms'])==19
        for t in s['terms']:
            assert len(t['daily'])==30 and sum(r['count'] for r in t['daily'])==t['count'] and set(t['articles'])<=ids
            assert t['recent']<=t['recent_total'] and t['prior']<=t['prior_total']
            for r in t['daily']:assert 0<=r['count']<=r['total'] and r['date']<=cutoff and (r['share'] is None or 0<=r['share']<=100)
    if kind=='geocomposites':
        assert [p['id'] for p in s['panels']]==['stress','geoenergy','policy']
        for p in s['panels']:section(p['chart'],cutoff,module);assert len(p['chart']['bands'])==2 and (p['date'] is None or p['date']<=cutoff)
    if kind=='geochannels':
        assert len(s['channels'])==6
        for c in s['channels']:
            assert c['exposure'] is None or 0<=c['exposure']<=7
            assert c['count']==sum(bool(set(c['topics'])&set(r['topics'])) for r in s['news'])
            for r in c['studies']:assert r['article'] in ids and r['first_session']<=cutoff and all(p['name']<=cutoff and 0<=p['x']<=20 for p in r['curve'])
    if kind=='geogpr':
        assert len(s['categories'])==len(s['countries'])==8 and len(s['rows'])<=120
        assert [r['date'] for r in s['rows']]==sorted(set(r['date'] for r in s['rows']))
        for r in s['rows']:assert r['date'][:7]<cutoff[:7] and all(v is None or math.isfinite(v) and v>=0 for k,v in r.items() if k!='date')
    if kind=='relationlab':
        nodes={r['id']:r for r in s['nodes']};edges={r['id']:r for r in s['links']}
        assert len(nodes)==len(s['nodes']) and len(edges)==len(s['links'])
        for n in nodes.values():
            assert len(n['position'])==3 and all(math.isfinite(v) for v in n['position'])
            assert not n.get('date') or n['date']<=cutoff
        for e in edges.values():
            assert e['source'] in nodes and e['target'] in nodes and e['source']!=e['target'] and 1<=e['weight']<=3
            assert e['relation'] in s['parameters']['transfer'] and e['basis'] and e['evidence']
            if e['relation']=='correlated':assert e['observations']>=200 and e['start']<e['end']<=cutoff and -1<=e['corr']<=1
            else:assert e['url'].startswith('https://')
        assert len(s['scenarios'])==8 and len({r['id'] for r in s['scenarios']})==8
        for scenario in s['scenarios']:
            seeds={r['id'] for r in scenario['seeds']};assert seeds<=nodes.keys()
            for id,r in scenario['impacts'].items():
                assert id in nodes and r['seed']==(id in seeds)
                assert abs(r['value']-sum(c['value'] for c in r['contributions']))<1e-5
                for c in r['contributions']:
                    assert c['source'] in seeds and c['path'][0]==c['source'] and c['path'][-1]==id
                    assert c['hop']==len(c['edges'])==len(c['path'])-1<=3 and len(c['path'])==len(set(c['path']))
                    for a,b,key in zip(c['path'],c['path'][1:],c['edges']):assert {a,b}=={edges[key]['source'],edges[key]['target']}
        p=s['portfolio_correlations'];count=len(p['ids']);length=count*(count-1)//2
        raw=base64.b64decode(p['correlations'],validate=True);obs=base64.b64decode(p['counts'],validate=True)
        assert len(set(p['ids']))==count and len(raw)==length*2 and len(obs)==length and len(p['diagonal_valid'])==count
        assert p['window']<=252 and p['minimum']==200 and (p['end'] is None or p['end']<=cutoff)
        for (value,),n in zip(struct.iter_unpack('<h',raw),obs):assert value==32767 or -10000<=value<=10000 and 200<=n<=252
    if kind=='digestbrief':assert len(s['horizons'])==3 and s['headline'] and s['note']
    if kind=='digesttrends':
        assert [p['id'] for p in s['panels']]==['short','mid','long']
        for p in s['panels']:
            assert p['available']==len(p['rows'])<=p['expected']==21
            values=[r['value'] for r in p['rows']];assert values==sorted(values,reverse=True)
            assert all(r['date']<=cutoff and math.isfinite(r['value']) for r in p['rows'])
    if kind=='digestthemes':
        assert len(s['items'])==10 and len({r['id'] for r in s['items']})==10
        for r in s['items']:
            assert r['available']<=r['expected']==len(r['members']) and r['expected']>0
            assert r['heat'] is None or 0<=r['heat']<=100
            for m in r['members']:assert m['source'].startswith('https://') and (m['date'] is None or m['date']<=cutoff)
            for key,value in r['returns'].items():
                if all(m[key] is not None for m in r['members']):assert abs(value-sum(m[key] for m in r['members'])/len(r['members']))<1e-5
                else:assert value is None
    if kind=='digeststocks':
        assert len(s['items'])==16 and len({r['symbol'] for r in s['items']})==16
        assert all(sum(r['market']==m for r in s['items'])==8 for m in ['US','KR'])
        for r in s['items']:
            assert r['date']<=cutoff and r['membership_as_of']<=cutoff and 1<=r['rs']<=99
            assert r['news_count']>=len(r['news']) and r['guru'] is None
            assert all(n['date']<=cutoff for n in r['news'])
    if kind=='digestrisk':
        assert len(s['items'])==9
        for r in s['items']:assert r['direction'] in [-1,0,1] and (r['date'] is None or r['date']<=cutoff)
    if kind=='digestcharts':
        assert len(s['items'])==4
        for r in s['items']:section(r['chart'],cutoff,module)
        assert s['items'][-1]['change_unit']=='z 차이'
    if kind=='digestmodules':
        assert len(s['items'])==20 and len({r['module'] for r in s['items']})==20
        for r in s['items']:
            assert r['as_of']<=cutoff and r['module'] not in ['ask_digest','iw','principium']
            for t in r['observations']:section(dict(t,type='table'),r['as_of'],module)
    if kind=='statetimeline':
        assert len(s['panels'])==3 and [len(p['labels']) for p in s['panels']]==[4,4,3]
        rows=s['rows'];assert len(rows)==36 and [r[0] for r in rows]==sorted(set(r[0] for r in rows))
        assert rows[-1][0]<cutoff[:7]+'-01'
        for r in rows:
            assert len(r)==4 and all(v is None or isinstance(v,int) and 0<=v<len(s['panels'][i]['labels']) for i,v in enumerate(r[1:]))
    if kind=='reviewcharts':
        assert len(s['latest'])==2 and len(s['archives'])==14
        for c in s['latest']:section(c,cutoff,module)
        for a in s['archives']:
            assert a['as_of']<=cutoff and len(a['charts'])==2 and isinstance(a['retrospective'],bool)
            for c in a['charts']:section(c,a['as_of'],module)
            assert len(a['charts'][1]['series'])==7
            assert all(p[0]<a['as_of'][:7]+'-01' for z in a['charts'][1]['series'] for p in z['points'])
    if kind=='reviewlog':
        items=s['items'];assert len(items)==(15 if s['group']=='월말 복기' else 14)
        assert [r['period'] for r in items]==sorted(set(r['period'] for r in items),reverse=True)
        for r in items:
            assert r['as_of']<=cutoff;section(r['table'],r['as_of'],module)
            if 'scored' in r:
                rows=r['table']['rows'];assert len(rows)==3
                assert r['hits']==sum(a[4]=='일치' for a in rows) and r['scored']==sum(a[4] in ['일치','불일치'] for a in rows)
                assert f"{r['hits']}/{r['scored']}" in r['summary']
                assert all(a[7]<=a[6]<r['as_of'] for a in rows if a[6] is not None)
            else:
                assert r['first_recorded_at']<=r['updated_at'] and re.fullmatch('[a-f0-9]{64}',r['model_hash'])
                assert len(r['forecasts']['rows'])==6 and len(r['macro']['rows'])==4
                assert all(a[1] is None or a[1]<=r['as_of'] for a in r['table']['rows'])
                assert all(a[2] is None or a[2]<=r['as_of'] and a[2]<a[3] for a in r['forecasts']['rows'])
                assert all(a[2] is None or a[2]<=r['as_of'] for a in r['macro']['rows'])
    if kind=='notebook':
        assert s['mode']==module and module in ['principium','iw','ask_digest']
        assert isinstance(s['items'],list)
        for r in s['items']:
            assert isinstance(r['title'],str) and isinstance(r['core'],str)
            assert isinstance(r.get('keywords',[]),list) and all(isinstance(k,str) for k in r.get('keywords',[]))
    if kind=='moe':
        assert s['cards']
        for c in s['cards']:
            assert c['origin']<c['target'] and c['origin']<=cutoff
            assert len(c['experts'])==10 and len({r['name'] for r in c['experts']})==10
            assert abs(sum(r['weight'] for r in c['experts'])-100)<1e-3
            assert all(0<=r['weight']<=100 for r in c['experts'])
            assert c['probability'] is None or 0<=c['probability']<=100
            assert len(c['history'])==36 and c['history'][-1][0]<=cutoff
            if c['bands']:
                lo,hi=c['bands']['1.96'];a,b=c['bands']['1']
                assert lo<=a<=c['forecast']<=b<=hi
                assert c['calibration_observations']>=24
            e=c['explanation']
            assert abs(e['base']+e['rational']+e['irrational']+e['interaction']-e['prediction'])<1e-4
            for table_key in ['ledger','diagnostics']:section(c[table_key],cutoff,module)
            assert all(r[2]<r[0]<r[1] for r in c['ledger']['rows'])
            if c.get('strategy_chart'):section(c['strategy_chart'],cutoff,module)
            if c['symbol'] in ['DGS10','CPIAUCSL']:assert 'strategy' not in c
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
ov=load(ROOT/'docs/data/overview_state.json');assert ov['as_of']==meta['as_of'] and ov['vintage']==meta['vintage']
assert [p['id'] for p in ov['panels']]==['tesseract','crowding'] and [len(p['axes']) for p in ov['panels']]==[6,5]
for p in ov['panels']:
    assert len(p['rows'])==36 and [m['index'] for m in p['milestones']]==[11,23,29,35]
    assert [r['date'] for r in p['rows']]==sorted(set(r['date'] for r in p['rows']))
    for row in p['rows']:
        assert row['date']<=ov['as_of'] and set(row['raw'])==set(row['z'])==set(a['key'] for a in p['axes'])
        assert all(v is None or isinstance(v,(int,float)) and math.isfinite(v) for v in [*row['raw'].values(),*row['z'].values()])
        for r in row['provenance'].values():
            if r['available']:assert r['period']<=r['available']<=row['date']
            if r.get('gdp_available'):assert r['gdp_period']<=r['gdp_available']<=row['date']
            for c in r.get('components',[]):
                if c['available']:assert c['period']<=c['available']<=row['date']
    for m in p['milestones']:assert m['date']==p['rows'][m['index']]['date']
for row in ov['panels'][0]['rows']:
    if row['date']=='2025-11-30':assert row['provenance']['profits']['period']<'2025-09-30'
    if row['date']=='2026-03-31':assert row['provenance']['profits']['period']<'2025-12-31'
assert len(ov['leaders']['stocks'])<=10 and ov['leaders']['eligible']<=ov['leaders']['pool']<=50
for r in ov['leaders']['stocks']:assert r['cap_usd_bn']>0 and r['price_date']<=ov['as_of'] and r['profit_period']<=ov['as_of'] and r['currency'] in ['USD','KRW']
print('PASS:',count,'new modules; dated observations, forecast maturity, intervals, OHLC, official coverage, graph and table shapes.')

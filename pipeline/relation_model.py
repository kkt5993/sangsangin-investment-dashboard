"""Auditable 1–3 hop relative-shock model; strengths are not return forecasts."""
import math
import numpy as np
import pandas as pd
from .engine import number

# Public structural settings, not estimated economic response coefficients.
# Pair order is source→target, target→source.
TRANSFER={'supplies':(.28,.72),'competes':(-.5,-.5),'part-of':(.42,.55),
    'exposed-to':(.5,.5),'powers':(.28,.62),'correlated':(.62,.62),
    'builds':(.22,.5),'hosts':(.58,.30),'pressures':(-.55,-.20),
    'drives':(.62,.30),'comention':(.45,.45),'collaborates':(.35,.35)}


def adjacency(graph,include_correlations=False):
    ids={n['id'] for n in graph['nodes']}
    if len(ids)!=len(graph['nodes']):raise ValueError('Duplicate relation node')
    result={id:[] for id in ids};seen=set()
    for edge in sorted(graph['links'],key=lambda e:e['id']):
        s,t,rel=edge['source'],edge['target'],edge['relation'];weight=edge.get('weight',1)
        if edge['id'] in seen or s not in ids or t not in ids or s==t or rel not in TRANSFER:raise ValueError('Invalid relation edge')
        seen.add(edge['id'])
        if not isinstance(weight,(int,float)) or not math.isfinite(weight) or not 1<=weight<=3:raise ValueError('Invalid relative edge weight')
        sign=1
        if rel=='correlated':
            corr=edge.get('corr')
            if corr is None or not math.isfinite(corr) or not -1<=corr<=1:raise ValueError('Correlation must be observed and signed')
            if not include_correlations:continue
            sign=np.sign(corr)
        for origin,target,side in [(s,t,0),(t,s,1)]:
            coefficient=TRANSFER[rel][side]*(.7+.1*weight)*.9*sign
            result[origin].append(dict(target=target,edge=edge['id'],relation=rel,coefficient=coefficient))
    return result


def propagate(graph,start,shock=1,hops=3,include_correlations=False):
    if not isinstance(shock,(int,float)) or not math.isfinite(shock) or abs(shock)>2:raise ValueError('Shock must be finite and within ±2')
    if not isinstance(hops,int) or not 1<=hops<=3:raise ValueError('Only 1–3 hops supported')
    adj=adjacency(graph,include_correlations)
    if start not in adj:raise ValueError('Unknown shock node')
    best={};frontier=[dict(value=float(shock),path=[start],edges=[],relations=[])]
    for depth in range(1,hops+1):
        following=[]
        for prefix in frontier:
            for edge in adj[prefix['path'][-1]]:
                target=edge['target']
                if target in prefix['path']:continue
                value=prefix['value']*edge['coefficient']
                if abs(value)<.03:continue
                item=dict(value=value,hop=depth,path=prefix['path']+[target],edges=prefix['edges']+[edge['edge']],relations=prefix['relations']+[edge['relation']])
                old=best.get(target)
                if old is None or abs(value)>abs(old['value'])+1e-12 or abs(abs(value)-abs(old['value']))<=1e-12 and (depth,item['edges'])<(old['hop'],old['edges']):best[target]=item
                following.append(item)
        frontier=following
    return {id:dict(item,value=number(item['value'])) for id,item in sorted(best.items())}


def run_scenario(graph,seeds,hops=3,include_correlations=False):
    if len({r['id'] for r in seeds})!=len(seeds):raise ValueError('Duplicate scenario seed')
    aggregate={}
    for seed in seeds:
        impacts=propagate(graph,seed['id'],seed['value'],hops,include_correlations)
        impacts[seed['id']]=dict(value=seed['value'],hop=0,path=[seed['id']],edges=[],relations=[])
        for id,item in impacts.items():
            aggregate.setdefault(id,dict(value=0.,seed=False,contributions=[]))
            record=aggregate[id];record['value']+=item['value'];record['seed']|=id==seed['id']
            record['contributions'].append(dict(item,source=seed['id']))
    for id,r in aggregate.items():
        r['value']=number(r['value']);r['contributions'].sort(key=lambda c:(-abs(c['value']),c['hop'],c['source']))
        r['path']=r['contributions'][0]['path'];r['edges']=r['contributions'][0]['edges'];r['hop']=r['contributions'][0]['hop']
    return dict(sorted(aggregate.items()))


def centrality(graph,include_correlations=False):
    rows=[]
    for node in graph['nodes']:
        impacts=propagate(graph,node['id'],1,3,include_correlations);material=[r for r in impacts.values() if abs(r['value'])>=.05]
        breadth=len(material);magnitude=sum(abs(r['value']) for r in material)
        rows.append(dict(id=node['id'],breadth=breadth,magnitude=number(magnitude),depth=max([r['hop'] for r in material],default=0),score=number(magnitude+.15*breadth)))
    return sorted(rows,key=lambda r:(-r['score'],r['id']))


def correlations(d,symbols):
    """Pairwise common returns within 370 calendar days, max252, min200."""
    end=pd.Timestamp(d.as_of);start=end-pd.Timedelta(days=370);returns={}
    for symbol in sorted(set(symbols)):
        price=d.price(symbol).loc[:end]
        if price.empty or (end-price.index[-1]).days>7:continue
        returns[symbol]=price.pct_change(fill_method=None).loc[start:].replace([np.inf,-np.inf],np.nan)
    result=[];symbols=sorted(returns)
    for i,a in enumerate(symbols):
        for b in symbols[i+1:]:
            pair=pd.concat([returns[a],returns[b]],axis=1).dropna().tail(252)
            if len(pair)<200 or min(pair.std(ddof=1))<=1e-12:continue
            value=number(pair.iloc[:,0].corr(pair.iloc[:,1]))
            if value is not None:result.append(dict(a=a,b=b,corr=value,observations=len(pair),start=str(pair.index[0].date()),end=str(pair.index[-1].date())))
    return result

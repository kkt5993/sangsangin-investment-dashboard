"""Three-month relation calibration and same-market lag exploration, offline."""
from itertools import combinations, permutations
import numpy as np
import pandas as pd
from scipy.stats import f as f_distribution
from statsmodels.stats.multitest import multipletests
from .relation_model import TRANSFER

LAGS=(1,3,5)
MINIMUM=45


def correlation(a,b):
    if len(a)<MINIMUM or min(np.std(a),np.std(b))<1e-12:return None
    return float(np.corrcoef(a,b)[0,1])


def lag_test(frame,lead,follow,lag,start):
    # Shift on the full market calendar BEFORE removing missing observations.
    columns={'y':frame[follow],'x0':frame[lead]}
    columns.update({f'y{k}':frame[follow].shift(k) for k in range(1,lag+1)})
    columns.update({f'x{k}':frame[lead].shift(k) for k in range(1,lag+1)})
    aligned=pd.DataFrame(columns).loc[lambda x:x.index>start].dropna()
    out=dict(lead=lead,follow=follow,lag=lag,observations=len(aligned),corr=None,contemporaneous=None,edge=None,f=None,p=None,q=None,
        start=str(aligned.index[0].date()) if len(aligned) else None,end=str(aligned.index[-1].date()) if len(aligned) else None,reason='')
    if len(aligned)<MINIMUM:out['reason']='유효 관측45개 미만';return out
    y=aligned.y.to_numpy();c=correlation(aligned[f'x{lag}'],y);c0=correlation(aligned.x0,y)
    if c is None or c0 is None:out['reason']='상수·유효 분산 부족';return out
    out.update(corr=c,contemporaneous=c0,edge=abs(c)-abs(c0))
    restricted=np.column_stack([np.ones(len(y)),aligned[[f'y{k}' for k in range(1,lag+1)]]])
    full=np.column_stack([restricted,aligned[[f'x{k}' for k in range(1,lag+1)]]])
    if np.linalg.matrix_rank(full)<full.shape[1]:out['reason']='회귀 설명변수 선형 종속';return out
    e0=y-restricted@np.linalg.lstsq(restricted,y,rcond=None)[0];e1=y-full@np.linalg.lstsq(full,y,rcond=None)[0]
    ss0=float(e0@e0);ss1=float(e1@e1);df=len(y)-full.shape[1]
    if ss1<=1e-20 or df<=0:out['reason']='잔차 분산·자유도 부족';return out
    stat=max(0.,(ss0-ss1)/lag/(ss1/df))
    out.update(f=stat,p=float(f_distribution.sf(stat,lag,df)),df_numerator=lag,df_denominator=df)
    return out


def build(d,graph):
    end=pd.Timestamp(d.as_of);start=end-pd.DateOffset(months=3)
    nodes={n['symbol']:n for n in graph['nodes'] if n.get('kind')=='company' and n.get('symbol')}
    frames={};excluded=[];universe=[];windows={}
    for market,benchmark in [('US','SPY'),('KR','^KS11')]:
        calendar=d.price(benchmark).loc[start-pd.Timedelta(days=40):end].index
        if len(calendar) and (end-calendar[-1]).days>7:calendar=calendar[:0]
        windows[market]=dict(benchmark=benchmark,sessions=int(sum(calendar>start)),start=str(calendar[calendar>start][0].date()) if any(calendar>start) else None,end=str(calendar[-1].date()) if len(calendar) else None)
        prices={}
        for symbol,n in sorted(nodes.items()):
            if ('KR' if symbol.endswith('.KS') else 'US')!=market:continue
            p=d.price(symbol).loc[:end]
            if not len(calendar) or p.empty or (end-p.index[-1]).days>7:
                excluded.append(dict(symbol=symbol,reason='시장 달력·최근7일 가격 미확보'));continue
            returns=p.reindex(calendar).pct_change(fill_method=None).replace([np.inf,-np.inf],np.nan)
            if returns.loc[lambda x:x.index>start].notna().sum()<MINIMUM:
                excluded.append(dict(symbol=symbol,reason='3개월 일 수익률45개 미만'));continue
            prices[symbol]=returns
            universe.append(dict(symbol=symbol,id=n['id'],name=n['name'],market=market,last_date=str(p.index[-1].date())))
        frames[market]=pd.DataFrame(prices,index=calendar)
    all_returns=pd.concat(list(frames.values()),axis=1).sort_index().loc[lambda x:x.index>start]
    formal={}
    for edge in graph['links']:
        a=edge['source'].removeprefix('stock:');b=edge['target'].removeprefix('stock:')
        if edge['relation']!='correlated' and a in nodes and b in nodes:
            formal.setdefault(tuple(sorted([a,b])),[]).append(edge)
    pairs=[];hidden=[];consistent=[];divergent=[]
    for a,b in combinations(sorted(all_returns.columns),2):
        p=all_returns[[a,b]].dropna();c=correlation(p[a],p[b]);edges=formal.get((a,b),[])
        row=dict(a=a,b=b,corr=c,observations=len(p),start=str(p.index[0].date()) if len(p) else None,end=str(p.index[-1].date()) if len(p) else None,
            same_market=a.endswith('.KS')==b.endswith('.KS'),relations=[e['relation'] for e in edges])
        pairs.append(row)
        if c is None:continue
        if not edges and abs(c)>=.6:hidden.append(row)
        for edge in edges:
            sign=int(np.sign(TRANSFER[edge['relation']][0]));item=dict(row,relation=edge['relation'],expected_sign=sign,url=edge.get('url'),basis=edge.get('basis'),edge_id=edge['id'])
            if sign*c>0:consistent.append(item)
            elif sign*c<0:divergent.append(item)
    tests=[]
    for market,frame in frames.items():
        for lead,follow in permutations(sorted(frame.columns),2):
            for lag in LAGS:tests.append(dict(lag_test(frame,lead,follow,lag,start),market=market))
    valid=[r for r in tests if r['p'] is not None]
    if valid:
        # Shared firms and overlapping lags make these tests dependent.
        q=multipletests([r['p'] for r in valid],method='fdr_by')[1]
        for r,value in zip(valid,q):r['q']=float(value)
    best={}
    for r in tests:
        r['candidate']=r['corr'] is not None and abs(r['corr'])>=.25 and r['edge']>=.1
        r['screen_pass']=r['candidate'] and r['q'] is not None and r['q']<=.1
        if r['candidate']:
            key=(r['lead'],r['follow']);old=best.get(key)
            if old is None or (r['edge'],abs(r['corr']),-r['lag'])>(old['edge'],abs(old['corr']),-old['lag']):best[key]=r
    leads=sorted(best.values(),key=lambda r:(-r['edge'],-abs(r['corr']),r['lead'],r['follow']))
    sort=lambda rows:sorted(rows,key=lambda r:(-abs(r['corr']),r['a'],r['b']))
    return dict(type='relationdiscovery',group='관계 지도',title='관계 대조·선행/후행 탐색',as_of=d.as_of,vintage=d.vintage,
        period_start=str(start.date()),period_end=d.as_of,universe=universe,windows=windows,excluded=excluded,pairs=pairs,
        hidden=sort(hidden),consistent=sort(consistent),divergent=sort(divergent),leadlag=leads,tests=tests,
        settings=dict(months=3,minimum=MINIMUM,lags=list(LAGS),hidden_abs_correlation=.6,lag_abs_correlation=.25,lag_advantage=.1,q_threshold=.1,correction='Benjamini–Yekutieli'),
        coverage=dict(expected=len(nodes),priced=len(universe),pairs=len(pairs),valid_pairs=sum(r['corr'] is not None for r in pairs),tests=len(tests),valid_tests=len(valid),candidates=len(leads),screen_pass=sum(r['screen_pass'] for r in leads)),
        note='3개월 조정종가 일 수익률. 관계망 기업 표본의 비연결 고상관·전달 가정 부호 대조와 동일 시장1/3/5거래일 시차 탐색입니다. 시차를 만든 뒤 결측을 제외하며 상관의 향상은 같은 표본의 동시 상관과 비교합니다. 회귀 F검정과 전체 방향·시차의 BY 보정을 별도로 표시합니다. 시차 상관·표본 내 검정 통과는 경제적 인과나 표본 밖 예측력·매매 신호를 입증하지 않습니다.')


def views(d,obj):
    graph=next(s for s in obj['sections'] if s['type']=='relationlab')
    obj['sections']=[s for s in obj['sections'] if s['type']!='relationdiscovery']
    section=build(d,graph)
    pairs={tuple(sorted([r['a'],r['b']])):r for r in section['pairs']}
    graph['links']=[e for e in graph['links'] if e['relation']!='correlated']
    for edge in graph['links']:
        pair=pairs.get(tuple(sorted([edge['source'].removeprefix('stock:'),edge['target'].removeprefix('stock:')])))
        for key in ['corr','correlation_observations','correlation_start','correlation_end']:edge.pop(key,None)
        if pair:edge.update(corr=pair['corr'],correlation_observations=pair['observations'],correlation_start=pair['start'],correlation_end=pair['end'])
    for r in section['hidden']:
        graph['links'].append(dict(id='corr:'+r['a']+':'+r['b'],source='stock:'+r['a'],target='stock:'+r['b'],relation='correlated',weight=1,
            corr=r['corr'],correlation_observations=r['observations'],correlation_start=r['start'],correlation_end=r['end'],
            observations=r['observations'],start=r['start'],end=r['end'],basis='최근3개월 비연결 쌍의 |상관|≥0.6 · 인과 아님',evidence='관측 계산',url=None,reviewed_at=d.as_of))
    graph['pairs']=section['pairs']
    graph['correlation_window']=dict(months=3,minimum=MINIMUM,start=section['period_start'],end=d.as_of)
    obj['sections'].insert(obj['sections'].index(graph),section)
    return obj

"""Source-backed company graph, relative-shock scenarios and observed correlations."""
import base64
import numpy as np
import pandas as pd
import networkx as nx
from .engine import number,table
from .store import ROOT,read_json
from .relation_model import run_scenario,centrality,correlations,TRANSFER

LABELS={'supplies':'공급','competes':'경쟁','part-of':'사업 연관','exposed-to':'노출','powers':'전력 공급','correlated':'실현 상관','builds':'건설·소유','hosts':'거점','pressures':'압박','drives':'유도','comention':'동시 언급','collaborates':'기술 협업'}


def inputs():return read_json(ROOT/'config/relation_evidence.json'),read_json(ROOT/'config/digest_themes.json')


def companies():
    evidence,themes=inputs();records={r['symbol']:dict(symbol=r['symbol'],name=r['name']) for r in evidence['companies']}
    for t in themes['themes']:
        for r in t['members']:records.setdefault(r['symbol'],dict(symbol=r['symbol'],name=r['name']))
    return list(records.values())


def presets():
    C=lambda s:'stock:'+s;T=lambda s:'theme:'+s
    specs=[('rates_up','금리 재상승','거시',[("macro:ust10",.5),(C('NVDA'),-.5),(T('ai_datacenter'),-.4),(C('JPM'),.4),('commodity:gold',.3),(T('glp1'),-.2)]),
        ('capex_cut','AI CapEx 둔화','산업',[('macro:ai_capex',-.7),(C('NVDA'),-.5),(T('ai_datacenter'),-.5)]),
        ('tsmc_shock','TSMC 공급 차질','공급',[(C('TSM'),-.6)]),
        ('power_squeeze','데이터센터 전력 병목','인프라',[('macro:power_demand',.6),(T('power_cooling'),.5),(T('nuclear'),.4)]),
        ('hbm_accel','HBM 사이클 가속','산업',[(T('hbm'),.6),(C('000660.KS'),.4)]),
        ('geopolitics','지정학 격화','지정학',[(T('defense'),.6),('commodity:gold',.4),(T('lng'),.3),(C('NVDA'),-.2)]),
        ('glp1','GLP-1·GIP 확산','산업',[(T('glp1'),.6),(C('LLY'),.4)]),
        ('risk_off','위험선호 후퇴','거시',[('commodity:gold',.5),(C('NVDA'),-.4),(T('ai_datacenter'),-.3),(C('JPM'),-.2)])]
    return [dict(id=id,name=name,category=cat,seeds=[dict(id=k,value=v) for k,v in seeds],note='일차 강도는 공개 원본 설정에 대응한 정규화 가정입니다. 금리 bp·CapEx 변화율에서 종목 수익률로 추정한 값이 아닙니다.') for id,name,cat,seeds in specs]


def correlation_pack(d,entities):
    """Compact lower triangle; latest252 union dates, minimum200 pair observations."""
    ids=sorted(e['id'] for e in entities);lookup={e['id']:e['symbol'] for e in entities};returns={};end=pd.Timestamp(d.as_of)
    calendars={k:d.price(k).index for k in ['^KS11','SPY']}
    for id in ids:
        p=d.price(lookup[id]).loc[:end]
        if len(p) and (end-p.index[-1]).days<=7:
            native=calendars['^KS11' if lookup[id].endswith(('.KS','.KQ')) else 'SPY'].union(p.index)
            p=p.reindex(native[(native>=p.index[0])&(native<=p.index[-1])])
            returns[id]=p.pct_change(fill_method=None).loc[end-pd.Timedelta(days=370):]
    f=pd.DataFrame(returns).replace([np.inf,-np.inf],np.nan).sort_index().tail(252).reindex(columns=ids)
    mask=f.notna().to_numpy(dtype=np.int16);counts=mask.T@mask
    c=f.corr(min_periods=200).to_numpy();tri=np.tril_indices(len(ids),-1);values=c[tri]
    packed=np.full(len(values),32767,dtype='<i2');valid=np.isfinite(values);packed[valid]=np.rint(np.clip(values[valid],-1,1)*10000).astype('<i2')
    count_bytes=counts[tri].astype('uint8')
    return dict(ids=ids,correlations=base64.b64encode(packed.tobytes()).decode(),counts=base64.b64encode(count_bytes.tobytes()).decode(),diagonal=counts.diagonal().tolist(),diagonal_valid=np.isfinite(np.diag(c)).tolist(),
        start=str(f.index[0].date()) if len(f) else None,end=str(f.index[-1].date()) if len(f) else None,window=len(f),minimum=200,scale=10000,missing=32767,
        note='각 시장 달력에서 누락일을 보존해 일 수익률을 계산한 뒤 최근252개 공통 달력의 거래 관측일 창, 쌍별 최소200개. 아래삼각 Int16 little-endian/10000,32767은결측. 관측 수는Uint8. 반올림오차 최대0.00005. 통화별 현지 수익률 상관입니다.')


def graph_data(d,entity_section):
    evidence,themes=inputs();entities={r['id']:r for r in entity_section['entities']};nodes={};links=[]
    for r in companies():
        id='stock:'+r['symbol'];e=entities.get(id);p=d.price(r['symbol'])
        nodes[id]=dict(id=id,name=r['name'],symbol=r['symbol'],kind='company',entity=bool(e),date=e['date'] if e else str(p.index[-1].date()) if len(p) else None,
            r1m=e['returns'][1] if e else None,r3m=e['returns'][2] if e else None,rs=e['rs'] if e else None,role=e['sector'] if e else '공식 업종 미확보')
    for t in themes['themes']+evidence['extra_themes']:
        id='theme:'+t['id'];nodes[id]=dict(id=id,name=t['name'],kind='theme',entity=False,role='출처를 확인한 사업 관찰 목록',reviewed_at=evidence['reviewed_at'])
        for r in t['members']:
            source=evidence['sources'][r['source_id']]['url'] if r.get('source_id') else r['source']
            links.append(dict(id='member:'+r['symbol']+':'+t['id'],source='stock:'+r['symbol'],target=id,relation='part-of',weight=1,basis=r['role'],url=source,reviewed_at=evidence['reviewed_at'],evidence='사업 설명'))
    for r in evidence['links']:
        src=evidence['sources'][r['source_id']]
        links.append(dict(r,source='stock:'+r['source'],target='stock:'+r['target'],url=src['url'],reviewed_at=evidence['reviewed_at'],evidence='공시' if r['source_id'].startswith('nvda') else '공식 발표'))
    for id,name,kind,s in [('macro:ust10','미국 국채10Y','macro',d.mac('DGS10')),('commodity:gold','금 선물','commodity',d.price('GC=F'))]:
        nodes[id]=dict(id=id,name=name,kind=kind,entity=False,role='시나리오 입력',value=number(s.iloc[-1]) if len(s) else None,date=str(s.index[-1].date()) if len(s) else None)
    for id,name in [('macro:ai_capex','AI CapEx 가정'),('macro:power_demand','전력 수요 가정')]:nodes[id]=dict(id=id,name=name,kind='assumption',entity=False,role='관측 수치가 없는 가정 입력',date=None,value=None)
    pair=correlations(d,[r['symbol'] for r in companies()]);lookup={tuple(sorted([r['a'],r['b']])):r for r in pair};formal={tuple(sorted([r['source'],r['target']])) for r in links};observed=[]
    for edge in links:
        r=lookup.get(tuple(sorted([edge['source'].removeprefix('stock:'),edge['target'].removeprefix('stock:')])))
        if r:edge.update(corr=r['corr'],correlation_observations=r['observations'],correlation_start=r['start'],correlation_end=r['end'])
    for symbol in sorted({r['symbol'] for r in companies()}):
        eligible=[r for r in pair if symbol in [r['a'],r['b']] and abs(r['corr'])>=.6 and tuple(sorted(['stock:'+r['a'],'stock:'+r['b']])) not in formal]
        if eligible:observed.append(max(eligible,key=lambda r:abs(r['corr'])))
    for r in {r['a']+'|'+r['b']:r for r in observed}.values():
        links.append(dict(id='corr:'+r['a']+':'+r['b'],source='stock:'+r['a'],target='stock:'+r['b'],relation='correlated',weight=1,basis='가격 수익률의 실현 상관 · 인과 아님',evidence='관측 계산',url=None,reviewed_at=d.as_of,**r))
    g=nx.Graph();g.add_nodes_from(nodes);g.add_edges_from((r['source'],r['target']) for r in links if r['relation']!='correlated');pos=nx.spring_layout(g,dim=3,seed=832,k=1.2,iterations=100)
    for id,n in nodes.items():n.update(position=[number(v) for v in pos[id]],degree=g.degree(id))
    return dict(nodes=list(nodes.values()),links=links,pairs=pair,relation_labels=LABELS,reviewed_at=evidence['reviewed_at'])


def relation_views(d,obj):
    obj['sections']=[s for s in obj['sections'] if s['type'] not in ['relationlab','relationscenario'] and s.get('title')!='관계망 관측·근거 범위']
    entity_section=next(s for s in obj['sections'] if s['type']=='entities');graph=graph_data(d,entity_section);scenarios=presets()
    for s in scenarios:s['impacts']=run_scenario(graph,s['seeds'])
    lab=dict(type='relationlab',title='사업·공급·경쟁·실현 상관 관계망',group='관계 지도',**graph,scenarios=scenarios,
        hubs=centrality(graph),portfolio_correlations=correlation_pack(d,entity_section['entities']),
        parameters=dict(transfer={k:list(v) for k,v in TRANSFER.items()},edge_weight_formula='(.7+.1×weight)×.9',minimum=.03,centrality_minimum=.05,breadth_minimum=.12,ranking_minimum=.06,max_hops=3),
        note='관계 존재는 공시·기업 사업 설명으로 확인했습니다. 전달계수·일차 충격은 별도의 시나리오 가정이며 인과 효과·주가 변화율·발생확률이 아닙니다. 실현 상관은 기본 전파에서 제외하고 선택할 때 음의 부호도 보존합니다.')
    for s in obj['sections']:
        if s['type']=='graph':s['group']='공식 분류'
        if s['type']=='scenario':s['group']='시장 Beta 민감도'
    obj['sections'].insert(0,lab)
    obj['sections'].append(dict(type='relationscenario',title='8개 관계 시나리오 · 가정 전파',group='시나리오'))
    obj['sections'].append(dict(table('관계망 관측·근거 범위',['항목','값'],[['객체',len(graph['nodes'])],['사업/공급/경쟁/협업',sum(r['relation']!='correlated' for r in graph['links'])],['가격 기반 상관 연결',sum(r['relation']=='correlated' for r in graph['links'])],['시나리오',len(scenarios)],['추가 사업 Entity',len(entity_section.get('extra_symbols',[]))],['원장 상관 대상',len(entity_section['entities'])]]),group='현황판'))
    obj['method_note']='공식 분류 관계와 기업 공시·사업 설명에 근거한 사업 관계를 탐색합니다. 객체/관계 필터·단일 충격·최대3단계 전파·8시나리오·근거 경로·실현 상관과 결정 원장을 연결합니다. 노드/관계의 공개 근거와 시나리오 전달계수는 구분합니다. Beta 시장 충격은 별도 화면입니다. 모든 계산은 PC에서 갱신하고 개인 원장은 브라우저 로컬에 보관합니다.'
    for s in obj['sections']:
        if s['type']=='text' and s.get('group')=='방법론':s['text']=obj['method_note']+' 근거 확인일과 가격 기준일을 구분합니다. 실행 상태 결정만 포트폴리오로 집계하며 미입력·미연결은 미산출로 표시합니다. 관계 전달은 가정 강도이며 수익률·인과 추정이 아닙니다. 관측 상관과 가정 계수를 대조하고 사용자 입력 EV를 보존합니다.'
    obj['missing']=['사업·공급·경쟁 관계는 출처 확인한 표본이며 전체 공급망·거래금액·고객별 매출 비중이 아닙니다. 원본의 전체255객체/581관계를 독립 검증한 범위는 아닙니다.',
        '단계 전파와 프리셋 충격은 가정입니다. 상관은 인과 검증이 아니고 기준일·유니버스·선택 편향의 영향을 받습니다. 거시 가정 입력 중AI CapEx/전력 수요는 실제 관측 수치가 없습니다.',
        '위성 시설 관측·일부 임상/13F 촉매·구루 원문 검증·팀 공용 DB는 남아 있습니다. 개인 확신도를 실제 성공확률이나 자동 주문으로 바꾸지 않습니다.']

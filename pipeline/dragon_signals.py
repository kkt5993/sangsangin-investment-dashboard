"""Observed DRAGONGLASS signals; no network, invented live score or thesis."""
from copy import deepcopy
from math import isfinite
from datetime import date,timedelta

RULES=[dict(id='guru',name='구루 보유',weight=3,status='미확보',basis='13F 보유 원장 미연결'),
 dict(id='leaders',name='주도주',weight=2,status='연결',basis='공식 한국 대형주·미국 IVV 표본의 시장별 RS 상위15'),
 dict(id='discovery',name='종목 발굴',weight=2,status='연결',basis='발굴 화면에 실제 선별된 기업 · 4분류 중 포함'),
 dict(id='attention',name='관심도 급등',weight=2,status='미확보',basis='기업별 관심도 +40% 이상 시계열 미연결'),
 dict(id='thesis',name='리서치 상승뷰',weight=2,status='미확보',basis='숫자 기대수익이 양수인 검토 리포트 미확보'),
 dict(id='volume',name='기업 뉴스 8건 이상',weight=1,status='미확보',basis='기업별 전체 뉴스 표본 미연결'),
 dict(id='tone',name='감성 우호',weight=1,status='미확보',basis='기업 뉴스 감성 관측 미연결')]


def section(obj,kind):
    return next((s for s in obj.get('sections',[]) if s['type']==kind),{})


def fresh(value,asof):
    try:return date.fromisoformat(asof)-timedelta(days=7)<=date.fromisoformat(value)<=date.fromisoformat(asof)
    except (TypeError,ValueError):return False


def monitor(dragon,discovery,ranks):
    asof=dragon['as_of'];graph=section(dragon,'relationlab');entities=section(dragon,'entities').get('entities',[])
    docs=section(dragon,'dragonresearch').get('items',[]);nodes={r['id']:r for r in graph.get('nodes',[])}
    signals={};rejected=[]
    def add(symbol,key,label,dt,detail):
        if not fresh(dt,asof):rejected.append(dict(symbol=symbol,signal=key,date=dt,reason='가격일이 기준일 이후이거나7일 초과'));return
        signals.setdefault(symbol,{})[key]=dict(id=key,label=label,weight=2,date=dt,detail=detail)
    for market in ['KR','US']:
        for i,r in enumerate(ranks.get(market,{}).get('leaders',[])):
            add(r['symbol'],'leaders',f'{market} RS 상위{i+1}',r.get('as_of'),f"RS {r.get('rs')} · 표본 내 상대순위")
    for r in section(discovery,'discovery').get('items',[]):
        add(r['symbol'],'discovery','발굴 · '+r['bucket'],r.get('price_date'),' / '.join(r.get('reasons',[])))
    rows=[]
    known={e['symbol'] for e in entities}
    for symbol,items in signals.items():
        if symbol not in known:
            for h in items.values():rejected.append(dict(symbol=symbol,signal=h['id'],date=h['date'],reason='현재 Entity360 유니버스에 없음'))
    for e in entities:
        hits=list(signals.get(e['symbol'],{}).values())
        if not fresh(e.get('date'),asof):
            for h in hits:rejected.append(dict(symbol=e['symbol'],signal=h['id'],date=h['date'],reason='Entity360 가격일이 오래되거나 미래임'))
            continue
        for h in hits:
            if h['date']!=e['date']:rejected.append(dict(symbol=e['symbol'],signal=h['id'],date=h['date'],reason='Entity360 가격일 '+e['date']+'과 불일치'))
        hits=[h for h in hits if h['date']==e['date']]
        related=[r for r in docs if r['kind']=='official' and any(t['id']==e['id'] for t in r['targets'])]
        edges=[r for r in graph.get('links',[]) if e['id'] in [r['source'],r['target']]]
        suppliers=[];customers=[]
        for r in edges:
            if r['relation']!='supplies':continue
            upstream=r['target']==e['id'];other=r['source'] if upstream else r['target']
            if other in nodes:(suppliers if upstream else customers).append(dict(id=other,name=nodes[other]['name'],basis=r.get('basis',''),url=r.get('url','')))
        if not hits and not related and not edges:continue
        rows.append(dict(id=e['id'],name=e['name'],symbol=e['symbol'],market=e['market'],sector=e['sector'],date=e['date'],hits=hits,
          observed_score=sum(h['weight'] for h in hits),total_score=None,degree=len(edges),documents=len(related),
          evidence_score=round(len(edges)*2.2+len(related)*6,6),live=None,expected_return=None,
          suppliers=suppliers,customers=customers,documents_detail=[dict(id=r['id'],title=r['title'],url=r['url'],date=r['date']) for r in related]))
    rows.sort(key=lambda r:(-r['observed_score'],-r['evidence_score'],r['id']))
    return rows,rejected


def radar(geo,asof):
    source=section(geo,'geosituations');news={r['id']:r for r in source.get('news',[])};rows=[]
    for t in source.get('topics',[]):
        articles=[news[i] for i in t['articles'] if i in news and fresh(news[i].get('date'),asof) and news[i]['date']>=(date.fromisoformat(asof)-timedelta(days=6)).isoformat()]
        if not articles:continue
        articles.sort(key=lambda r:(r['date'],r['id']),reverse=True)
        rows.append(dict(id=t['id'],name=t['name'],category=t['category'],count=len(articles),articles=[dict(title=r['title'],url=r['url'],date=r['date'],source=r['source']) for r in articles]))
    return sorted(rows,key=lambda r:(-r['count'],r['id']))


def cross_assets(digest):
    source=next((s for s in digest.get('sections',[]) if s.get('group')=='크로스에셋' and s['type']=='table'),{})
    if source and source['columns'][2:6]!=['심볼','실제 가격일','1W %','3M %']:raise ValueError('Cross-asset column contract changed')
    rows=[dict(group=r[0],name=r[1],symbol=r[2],date=r[3],value=r[5]) for r in source.get('rows',[]) if isinstance(r[5],(int,float)) and isfinite(r[5]) and fresh(r[3],digest['as_of'])]
    rows.sort(key=lambda r:(-r['value'],r['symbol']))
    return dict(key='r3m',available=len(rows),expected=len(source.get('rows',[])),rows=rows,leaders=rows[:3],laggards=sorted(rows,key=lambda r:(r['value'],r['symbol']))[:3])


def views(objects,ranks):
    dragon=objects['dragonglass'];asof=dragon['as_of'];digest=objects['ask_digest']
    for key in ['discovery','ask_digest','geoecon']:
        if objects[key]['as_of']!=asof:raise ValueError('Signal inputs must have the same snapshot date: '+key)
    rows,rejected=monitor(dragon,objects['discovery'],ranks)
    themes=deepcopy(section(digest,'digestthemes').get('items',[]))
    themes=[t for t in themes if t.get('heat') is not None][:6]
    cross=cross_assets(digest)
    log=[]
    for s in section(dragon,'satellite').get('sites',[]):
        scene=s.get('scene') or {};captured=scene.get('captured_at','')
        if not captured or captured[:10]>asof:continue
        log.append(dict(id=s['id'],date=captured,title=s['name'],kind='위성 촬영',detail='촬영일 기준 · 가동률·건설 진척 신호가 아님',url=scene.get('source','')))
    log.sort(key=lambda r:(r['date'],r['id']),reverse=True)
    common=dict(rules=deepcopy(RULES),as_of=asof,coverage=dict(entities=len(section(dragon,'entities').get('entities',[])),candidates=len(rows),leaders=sum(any(h['id']=='leaders' for h in r['hits']) for r in rows),discovery=sum(any(h['id']=='discovery' for h in r['hits']) for r in rows),discovery_input=len(section(objects['discovery'],'discovery').get('items',[])),rules_available=2,rules_total=7),excluded=rejected,
       scope='확인된 주도주·발굴 신호만 합산합니다. 두 신호는 서로 독립인 확률이 아닙니다. 미확보5항목을0점으로 확정하지 않으며 전체 점수와 원본 live·기대수익은 미산출입니다. 가격일이 동일하고 기준일로부터7일 이내인 관측만 결합합니다.')
    focus=dict(type='dragonfocus',title='지금 주목 · 신호·관계·근거',group='지금 주목',items=rows[:15],**common,
        risk=deepcopy(section(digest,'digestrisk').get('items',[])),themes=themes,cross=cross,radar=radar(objects['geoecon'],asof),
        ranking='확인된 신호 가중합 우선, 동점은 관계수×2.2+공식 문서수×6, 마지막은 객체 ID 순. 원본 전체 점수 순위와 다릅니다.')
    triggers=dict(type='dragontriggers',title='트리거 · 다중 신호와 촬영 원장',group='트리거·촉매',items=[r for r in rows if len(r['hits'])>=2][:16],log=log[:8],**common)
    for new in [focus,triggers]:
        position=next((i for i,s in enumerate(dragon['sections']) if s.get('group')==new['group']),len(dragon['sections']))
        dragon['sections']=[s for s in dragon['sections'] if not(s.get('group')==new['group'] and s['type'] in ['table','dragonfocus','dragontriggers'])]
        dragon['sections'].insert(position,new)
    gap='지금 주목·트리거는 주도주/발굴·공식 근거·촬영일을 연결합니다. 전체 뉴스량/감성/관심급등·13F·정량 투자뷰·원본 live는 미확보이며 완전한 합성점수는 미산출입니다.'
    if gap not in dragon['missing']:dragon['missing'].append(gap)
    return dragon

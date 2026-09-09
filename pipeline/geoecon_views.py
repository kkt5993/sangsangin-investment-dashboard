"""Observed headlines, transparent topic rules and market channels; no causal claims."""
import re,hashlib
from collections import Counter
import pandas as pd
import numpy as np
from .engine import number,curve,table,zscore,clean_json
from .events_data import read

RESEARCH='https://www.federalreserve.gov/econres/notes/feds-notes/the-effect-of-the-war-in-ukraine-on-global-activity-and-inflation-20220527.html'
TOPICS=[
 ('korea','한국 경제','한반도',r'\b(korea|korean)\b',['semi','fx']),
 ('north','북한·안보','한반도',r'\b(north korea|north korean|kim jong)\b',['defense']),
 ('taiwan','대만·반도체 공급','분쟁·핫스팟',r'\b(taiwan|taiwanese|tsmc)\b',['semi']),
 ('mideast','중동·해상 운송','분쟁·핫스팟',r'\b(iran|israel|gaza|hormuz|lebanon|middle east|red sea)\b',['energy','defense']),
 ('ukraine','러시아·우크라이나','분쟁·핫스팟',r'\b(russia|russian|ukraine|ukrainian)\b',['energy','defense']),
 ('southchina','남중국해','분쟁·핫스팟',r'\b(south china sea|philippines)\b',['semi','defense']),
 ('fed','미국 통화정책','국가·정책',r'\b(federal reserve|fomc|powell|fed)\b',['rates','credit','fx']),
 ('ecb','유럽 통화정책','국가·정책',r'\b(ecb|european central bank|lagarde)\b',['rates','fx']),
 ('treasury','미국 재정·국채','국가·정책',r'\b(treasury|budget|fiscal|government debt)\b',['rates','credit']),
 ('china','중국 경제·통상','국가·정책',r'\b(china|chinese|beijing)\b',['semi','fx']),
 ('trade','무역·관세','국가·정책',r'\b(trade|tariff|tariffs|wto|export controls?)\b',['semi','energy']),
 ('inflation','물가','시장 요인',r'\b(inflation|consumer prices|cpi)\b',['rates','credit']),
 ('energy','에너지','시장 요인',r'\b(oil|energy|lng|gas|opec)\b',['energy']),
 ('credit','신용·채무','시장 요인',r'\b(credit|debt|default|bankruptcy|bonds?)\b',['credit']),
 ('fx','환율·안전자산','시장 요인',r'\b(dollar|currency|currencies|gold|yen|won)\b',['fx']),
]
REGIONS=[('대만해협',119.5,24.5,['taiwan']),('중동',45,28,['mideast']),('우크라이나',32,49,['ukraine']),('한반도',127.5,38.3,['korea','north']),('남중국해',115,15,['southchina'])]
CHANNELS=[('defense','방산·안보',['ITA'],'분쟁·안보 뉴스 → 방위 지출과 조달 기대 → 방산 주식 관측'),
 ('semi','반도체·기술',['SMH','TSM','NVDA'],'대만·통상 뉴스 → 생산·수출 제약 가능성 → 반도체 가격 관측'),
 ('rates','금리·채권',['TLT'],'물가·통화·재정 뉴스 → 금리 기대 → 장기 국채 가격 관측'),
 ('energy','에너지·원자재',['XLE'],'분쟁·운송 뉴스 → 공급·수요 불확실성 → 에너지 주식 관측'),
 ('credit','신용·크레딧',['HYG'],'통화·신용 뉴스 → 금융여건 → 하이일드 ETF 가격 관측'),
 ('fx','안전자산·환율',['GLD','UUP'],'정책·지정학 뉴스 → 위험선호·통화 수요 → 금·달러 ETF 관측')]
RISK_WORDS={'war','attack','attacks','conflict','conflicts','threat','threats','sanctions','invasion','strike','strikes','crisis','default','escalation','missile','nuclear','blockade','collapse','collapsed','killed','dead'}
EASE_WORDS={'peace','ceasefire','truce','agreement','deal','deescalation','recovery','cooperation'}
KEYWORDS=['war','tariff','trade','inflation','rates','energy','oil','sanctions','conflict','debt','growth','China','Taiwan','Iran','Ukraine','Russia','Korea','peace','ceasefire']

def tone(title):
    words=re.findall(r'[a-z]+',title.lower());risk=[];ease=[]
    for i,w in enumerate(words):
        if any(x in ['no','not','without','never'] for x in words[max(0,i-3):i]):continue
        if w in RISK_WORDS:risk.append(w)
        if w in EASE_WORDS:ease.append(w)
    risk=sorted(set(risk));ease=sorted(set(ease));direction=-1 if len(risk)>len(ease) else 1 if len(ease)>len(risk) else 0
    return dict(direction=direction,risk_words=risk,ease_words=ease)

def corpus(d):
    """Union preserved vintages by URL; cutoff is the earlier of retrieval and KST day end."""
    end=(pd.Timestamp(d.as_of,tz='Asia/Seoul')+pd.Timedelta(days=1)).tz_convert('UTC');start=end-pd.Timedelta(days=30)
    found={};captures=[];latest={}
    for base in d.bases:
        path=base/'news.json.gz'
        if not path.exists():continue
        raw=read(path);stamp=pd.Timestamp(raw['retrieved_at'])
        if stamp.tzinfo is None:continue
        captures.append(raw['retrieved_at']);latest=raw
        for r in raw['items']:
            t=pd.Timestamp(r['published_at'])
            if t.tzinfo is None or not start<=t<end or t>stamp or not r['url'].startswith('https://'):continue
            row=dict(r,first_seen=raw['retrieved_at'])
            if r['url'] in found:row['first_seen']=min(found[r['url']]['first_seen'],row['first_seen'])
            found[r['url']]=row
    rows=[]
    for r in found.values():
        topics=[k for k,_,_,pattern,_ in TOPICS if re.search(pattern,r['title'],re.I)]
        keywords=[k for k in KEYWORDS if re.search(r'\b'+re.escape(k)+r'\b',r['title'],re.I)]
        regions=[name for name,_,_,ids in REGIONS if set(ids)&set(topics)];t=pd.Timestamp(r['published_at']).tz_convert('Asia/Seoul')
        rows.append(dict(r,id=hashlib.sha256(r['url'].encode()).hexdigest()[:16],date=str(t.date()),topics=topics,keywords=keywords,regions=regions,
            **tone(r['title']),kind='보도 헤드라인' if r['source'] in ['BBC World','DW'] else '공식 발표',core=r['title'],evidence=' · '.join(regions+keywords) or '분류어 미검출'))
    rows.sort(key=lambda r:(pd.Timestamp(r['published_at']),r['url']),reverse=True)
    return rows,dict(captures=captures,latest=latest.get('retrieved_at'),sources=latest.get('sources',[]),start=str(start.tz_convert('Asia/Seoul').date()),end=d.as_of,
        note='보존한 RSS 제목의 발행일 분포입니다. 전체 기사량이나 완전한 과거 일별 수집이 아닙니다. 보도 시각·최초 수집 시각을 구분하고 가격 기준일의 한국시간 종료 이후 기사는 제외합니다.')

def keyword_data(news,as_of):
    end=pd.Timestamp(as_of);days=pd.date_range(end-pd.Timedelta(days=29),end,freq='D');daily=Counter(r['date'] for r in news);rows=[]
    for term in KEYWORDS:
        subset=[r for r in news if term in r['keywords']];counts=Counter(r['date'] for r in subset)
        recent=[r for r in news if r['date']>str((end-pd.Timedelta(days=7)).date())];prior=[r for r in news if str((end-pd.Timedelta(days=14)).date())<r['date']<=str((end-pd.Timedelta(days=7)).date())]
        a=sum(term in r['keywords'] for r in recent);b=sum(term in r['keywords'] for r in prior)
        share=a/len(recent)*100 if recent else None;before=b/len(prior)*100 if prior else None
        rows.append(dict(term=term,count=len(subset),recent=a,prior=b,recent_total=len(recent),prior_total=len(prior),share=number(share),prior_share=number(before),delta=number(share-before) if share is not None and before is not None else None,
            risk=sum(r['direction']<0 for r in subset),ease=sum(r['direction']>0 for r in subset),daily=[dict(date=str(t.date()),count=counts[str(t.date())],total=daily[str(t.date())],share=number(100*counts[str(t.date())]/daily[str(t.date())]) if daily[str(t.date())] else None) for t in days],articles=[r['id'] for r in subset]))
    return sorted(rows,key=lambda r:(-r['count'],r['term']))

def composites(d):
    s={'vix':d.price('^VIX',False),'hy':d.mac('BAMLH0A0HYM2'),'oil':d.price('CL=F',False),'dxy':d.price('DX-Y.NYB',False),'epu':d.mac('USEPUINDXD'),'rate':d.mac('DGS10')};out=[]
    for key,name,pairs in [('stress','매크로 스트레스',[('vix',1),('hy',1)]),('geoenergy','지정학 에너지 프리미엄',[('oil',1),('dxy',-1)]),('policy','정책·금리 압력',[('epu',1),('rate',1)])]:
        f=pd.concat({k:s[k].loc[:d.as_of] for k,_ in pairs},axis=1).dropna();z=f.apply(lambda col:zscore(col,252));mix=sum(z[k]*sign for k,sign in pairs)/len(pairs);valid=mix.dropna()
        latest=valid.iloc[-1] if len(valid) and (pd.Timestamp(d.as_of)-valid.index[-1]).days<=7 else None;date=str(valid.index[-1].date()) if len(valid) else None
        chart=curve(name+' · 최근1년',[(name,mix.loc[pd.Timestamp(d.as_of)-pd.DateOffset(years=1):],'left')],'z',guides=[-2,-1,0,1,2],n=400)
        chart['bands']=[dict(low=-1,high=1,color='#e4eee8'),dict(low=1,high=2,color='#f4ebd6')]
        out.append(dict(id=key,name=name,value=number(latest),date=date,change1w=number(latest-valid.iloc[-6]) if latest is not None and len(valid)>5 else None,change1m=number(latest-valid.iloc[-22]) if latest is not None and len(valid)>21 else None,
            level='미산출' if latest is None else '2z 이상' if latest>=2 else '1z 이상' if latest>=1 else '−1z 이하' if latest<=-1 else '중간 구간',
            formula='('+' + '.join(('−' if sign<0 else '')+'z('+k+')' for k,sign in pairs)+') / 2',chart=chart))
    return out

def topic_data(news):
    result=[]
    for key,name,category,pattern,channels in TOPICS:
        items=[r for r in news if key in r['topics']];risk=sum(r['direction']<0 for r in items);ease=sum(r['direction']>0 for r in items)
        result.append(dict(id=key,name=name,category=category,channels=channels,count=len(items),risk=risk,ease=ease,attention=len(items)+risk*2,
            direction=-1 if risk>ease else 1 if ease>risk else 0,articles=[r['id'] for r in items[:6]],pattern=pattern))
    return result

def channels(d,news):
    from .subview_modules import event_returns
    rows=[]
    for id,name,symbols,path in CHANNELS:
        topics=[k for k,_,_,_,cs in TOPICS if id in cs];items=[r for r in news if set(r['topics'])&set(topics)];risk=sum(r['direction']<0 for r in items);ease=sum(r['direction']>0 for r in items)
        studies=[]
        for article in items[:3]:
            for symbol in symbols:
                p=d.price(symbol);bench=d.price('SPY')
                if p.empty:continue
                result=event_returns(p,bench,article['published_at'])
                if result:studies.append(dict(symbol=symbol,article=article['id'],**result))
        rows.append(dict(id=id,name=name,symbols=symbols,path=path,topics=topics,count=len(items),exposure=number(7*len(items)/len(news)) if news else None,risk=risk,ease=ease,
            direction=-1 if risk>ease else 1 if ease>risk else 0,articles=[r['id'] for r in items[:6]],studies=studies,source=RESEARCH))
    return sorted(rows,key=lambda r:(-(r['exposure'] or 0),r['id']))

def gpr_panel(d):
    file=d.resource('gpr_details.json.gz')
    if not file.exists():return None
    raw=read(file);rows=[r for r in raw['rows'] if (pd.Timestamp(r['date'])+pd.offsets.MonthEnd(0))<=pd.Timestamp(d.as_of)]
    return dict(type='geogpr',group='GPR 세부',title='공식 GPR · 위협/행위·8분류·8국가',rows=rows,categories=raw['categories'],countries=raw['countries'],source=raw['source'],retrieved_at=raw['retrieved_at'],
        note='GPR/GPRT/GPRA는10개 신문·1985–2019 평균100 지수입니다. 8분류 SHAREH는3개 역사 신문의 기사 비중(%), 국가 GPRC는10개 신문의 국가 관련 기사 비중(%)입니다. 신문 표본과 단위가 다르고 겹치는 기사가 있어 합계나 구성 기여율로 해석하지 않습니다. 관측월말까지 표시하되 당시 발표 빈티지는 아닙니다.')

def news_views(d,obj):
    news,coverage=corpus(d);topics=topic_data(news);terms=keyword_data(news,d.as_of);panels=composites(d)
    # Rebuild only this module's news-derived groups; retain its 3 market panels.
    obj['sections']=[dict(s,group='시장 지표') for s in obj['sections'] if not s.get('group') or s.get('group')=='시장 지표']
    for s in obj['sections']:
        for series in s.get('series',[]):series['points']=[p for p in series['points'] if p[0]>=str((pd.Timestamp(d.as_of)-pd.DateOffset(years=1)).date())]
    common=dict(news=news,coverage=coverage)
    obj['sections'].extend([
        dict(type='geosituations',group='주목 상황',title='주목 상황·제목 표현·카테고리',topics=topics,**common),
        dict(type='geocomposites',group='복합지표',title='3개 지경학 복합지표',panels=panels,note='각 패널의 두 지표가 함께 관측된252개 날짜로 각각 z(ddof0)를 계산해 동일평균합니다. 달러만 부호를 반전합니다. 1W/1M 변화는5/21공통관측 z 차이이며 수익률이 아닙니다. 현재값7일 초과는 미산출입니다.'),
        dict(type='geokeywords',group='키워드 트렌드',title='30일 보존 제목 · 최근7일/직전7일',terms=terms,**common),
        dict(type='geochannels',group='인과·영향 모델',title='6개 영향 채널 · 기사에서 관측 자산까지',channels=channels(d,news),topics=topics,**common),
        dict(type='library',group='뉴스 원장',title='발행일·원문·최초 수집 원장',items=news),
        dict(table('수집 상태 · 원문 본문 미수집',['제공처','상태','제목 수'],[[s['name'],s['status'],s.get('items',0)] for s in coverage['sources']]),group='뉴스 원장')])
    countries=[]
    for name,lon,lat,ids in REGIONS:
        items=[r for r in news if set(r['topics'])&set(ids)];countries.append(dict(name=name,lon=lon,lat=lat,count=len(items),companies=[dict(name=r['title'],symbol=r['source'],sector='뉴스',ytd=None,margin=None) for r in items],news=[dict(title=r['title'],url=r['url'],date=r['date']) for r in items]))
    obj['sections'].append(dict(type='globe',group='지역 모니터',title='5개 관심 지역 · 기사 언급 지도',countries=countries))
    gpr=gpr_panel(d)
    if gpr:obj['sections'].append(gpr)
    obj['method_note']='보존 RSS 제목을 URL별로 합치고 한국시간 기준일까지의30일 발행 기사만 사용합니다. 15주제/4카테고리·위험/완화 단어·6채널 규칙은 공개 팀 설정입니다. 시장 3개 이중축·3개 복합 z는 최근1년 구조로 정렬합니다. 월간 GPR의 원지수와 다른 신문 표본의 기사 비중은 별도 축입니다.'
    obj['missing']=['제목 표현 분류는 기사 전체의 LLM 감성·사실 검증이 아닙니다. 채널 화살표는 경제적 경로 가정, 노출0~7은 현재 기사 표본 비중×7이며 피해 크기·수익률·확률이 아닙니다. 보도 이후 가격은 인과 효과가 아닙니다.',
        'RSS 보존 이력이 짧고 제공처별 발행주기/수집 실패가 달라 전체 뉴스량이나 완전한 일별 과거 표본을 확보하지 않았습니다. 위성 배경·시설 관측과 원본 비공개 감성 가중치는 미연결입니다.']
    obj['news_as_of']=coverage['latest'];return clean_json(news)

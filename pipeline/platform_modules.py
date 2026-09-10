"""Own research library, local journal, taxonomic networks and annual return quilt."""
import math
import numpy as np
import pandas as pd
import networkx as nx
from .engine import *

LIBRARY=[dict(kind='primer',title='공식 유니버스로 상대강도를 비교하는 방법',source='상상인 팀 구현 노트',date='2026-09-09',keywords=['RS','KRX','GICS'],
 core='한국 대형주는 KRX의 코스피 대형주 구성목록을 사용하고, 미국은 IVV가 공시한 S&P 500 편입 주식을 사용한다. 서로 다른 지수와 임의 시가총액 상위 목록을 섞으면 순위가 달라진다.',evidence='종목 구성 기준일과 가격 기준일을 별도로 저장한다.',url='https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf'),
 dict(kind='primer',title='수익률·환율·컨센서스의 단위',source='상상인 팀 구현 노트',date='2026-09-09',keywords=['단위','실적','데이터'],
 core='가격 수익률, 배당 재투자 수익률, 금리 변화(%p)는 서로 다른 값이다. EPS는 주당 이익이고 영업이익·순이익은 기업 전체의 이익이다. 해외 주식의 거래통화와 재무제표 표시통화도 다를 수 있다.',evidence='차트마다 분모, 단위, 기간 및 발표 빈티지를 함께 확인한다.'),
 dict(kind='article',title='월말 예측을 시간순으로 검증하기',source='상상인 팀 구현 노트',date='2026-09-09',keywords=['ML','OOS','시차'],
 core='3개월 뒤 수익률을 예측할 때는 학습 시점에 그 3개월이 끝난 과거 샘플만 사용할 수 있다. 표준화와 피처 선택도 학습 구간 안에서 해야 한다. 최신 수정 경제지표의 역사값은 당시 실시간 정보와 다르다.',evidence='현재 기준모형은 학습 타깃 만기와 잔차 보정 샘플 수를 각 예측에 저장한다.',url='https://fred.stlouisfed.org/docs/api/fred/'),
 dict(kind='report',title='리스크 수치의 해석 범위',source='상상인 팀 구현 노트',date='2026-09-09',keywords=['리스크','VaR','변동성'],
 core='과거 손익분포에서 계산한 VaR는 정해진 기간과 포트폴리오 비중을 전제로 한다. 국면 진단 점수를 폭락 확률이라고 해석할 수 없으며, 시나리오의 가정된 충격은 예측과 구분해야 한다.',evidence='포트폴리오 비중, 월간 관측 수, 신뢰수준을 콕핏에 표시한다.')]

def principium(as_of):
    return module('principium',as_of,'논문·리포트·프라이머를 제목/메타·핵심·아이디어·근거·시사점의5단으로 열람하고 등록·수정합니다. 제목 노드의 공유 키워드 관계와 빈도 구체를 문서에서 계산합니다. PDF의 제목·저자·페이지별 본문을 읽고 원문 해시·페이지를 근거에 연결합니다. 초기 공개 콘텐츠는 팀 구현 노트이며 새 글·첨부·추출 본문은 이 브라우저의 로컬 자료입니다.',
        [dict(type='notebook',title='리서치 아카이브',group='리서치 아카이브',mode='principium',items=LIBRARY)],missing=['PDF 텍스트 추출은 파일당25MiB·300쪽·20만자 범위입니다. 스캔·그림의 OCR, LLM 요약·번역은 추가 구현 대상이며 원문 배치·표 읽기 순서는 검토가 필요합니다.','이 브라우저의 IndexedDB에 저장합니다. 팀 공용 DB·서버 인증/공개 배포·서버 조회 통계는 추가 구현 대상입니다.'])
def libraries(d):
    lib=principium(d.as_of)
    digest=[]
    for s,n in [('SPY','S&P500 ETF'),('^KS11','KOSPI'),('TLT','미국 장기국채 ETF'),('GLD','금 ETF')]:
        a=d.stats(s)
        if a:digest.append(dict(kind='market',title=n+' 시장 메모',source='로컬 가격 계산',date=d.as_of,keywords=['시장','모멘텀'],core=f"1M {a['r1m']:.2f}%, 3M {a['r3m']:.2f}%, YTD {a['ytd']:.2f}%. RSI14 {a['rsi']:.1f}.",evidence=f"가격 관측일 {a['as_of']} · {s} · 배당 조정종가"))
    ask=module('ask_digest',d.as_of,'시장 수치·근거 원문과 질문/답변 메모를 구분합니다. 질문·내 해석·참조 근거·추가 확인을 기록하고 PDF·이미지를 첨부할 수 있습니다. 기록은 이 브라우저에만 보관하며 자동 AI 답변으로 표시하지 않습니다.',[dict(type='library',title='시장 다이제스트',group='시장',items=digest),dict(type='library',title='방법론',group='방법론',items=LIBRARY),dict(type='notebook',title='질문·근거 기록',group='질문·근거 기록',mode='ask_digest',items=[])],missing=['원본 brief/기간별 추세·테마·종목·모듈별 위험 집계는 추가 구현 대상입니다. 외부 ASK 토론·원본 자동 AI 질의 서버와 연결하지 않았습니다.','기록·첨부는 브라우저 로컬이며 팀 공용 저장·자동 LLM 요약은 미연결입니다.'])
    iw=module('iw',d.as_of,'관측·판단·근거·대응을 구분하고 방향·기간·확신도·무효화·재검토 날짜를 기록합니다. PDF·이미지 첨부, 수정/휴지통/복원/백업을 제공하며 기본 시장 요약은 계산된 수치입니다. 새 기록은 이 브라우저에 보관합니다.',[dict(type='library',title='이번 주 관측',group='관측 요약',items=digest),dict(type='notebook',title='주간 판단 원장',group='주간 판단 원장',mode='iw',items=[])],missing=['원본 작성자의 주간 논평·과거 개인 기록을 복제하지 않습니다. 월말15복기·주간14연대기·두차트는 iw_review에서 팀 원장으로 생성합니다.','팀 공용 DB·동시 편집 서버는 미연결입니다. 로컬 백업 JSON은 첨부 파일을 포함합니다.'])
    return [lib,ask,iw]

def network_data(d,financial,ranks):
    graph=nx.Graph();meta={};links=[]
    def node(key,name,kind,**extra):
        graph.add_node(key);meta[key]=dict(id=key,name=name,kind=kind,**extra)
    def link(a,b,label):graph.add_edge(a,b);links.append(dict(source=a,target=b,relation=label,confidence=1))
    node('root','투자 유니버스','universe')
    finance={r['symbol']:r for r in financial}
    chosen=[]
    for market in ['KR','US']:
        chosen += [dict(a,market=market) for a in ranks[market]['leaders'][:12]]
    for a in chosen:
        country='country:'+a['market'];sector='sector:'+a['market']+':'+a['sector'];symbol='stock:'+a['symbol']
        if country not in meta:node(country,a['market'],'country');link('root',country,'시장 분류')
        if sector not in meta:node(sector,a['sector'],'sector');link(country,sector,'공식 업종')
        node(symbol,a['name'],'company',symbol=a['symbol'],r1m=a['r1m'],r3m=a['r3m'],rs=a['rs'],sector=a['sector']);link(sector,symbol,'업종 소속')
    positions=nx.spring_layout(graph,dim=3,seed=17,iterations=75)
    for key,p in positions.items():meta[key]['position']=[number(v) for v in p];meta[key]['degree']=graph.degree(key)
    return dict(type='graph',title='시장·공식 업종·기업 관계',nodes=list(meta.values()),links=links)

def quilt(d):
    names={'SPY':'미국 주식','EFA':'선진국 주식','EEM':'신흥국 주식','IWM':'미국 소형주','TLT':'장기 국채','IEF':'중기 국채','HYG':'하이일드','GLD':'금','DBC':'원자재','VNQ':'리츠','BTC-USD':'비트코인'}
    prices={s:d.price(s) for s in names};years=list(range(2016,pd.Timestamp(d.as_of).year+1));columns=[]
    for year in years:
        rows=[]
        for s,p in prices.items():
            before=p.loc[:str(year-1)];during=p.loc[str(year):str(year)]
            if len(before) and len(during):rows.append(dict(symbol=s,name=names[s],value=number((during.iloc[-1]/before.iloc[-1]-1)*100)))
        columns.append(dict(year=str(year)+(' YTD' if year==pd.Timestamp(d.as_of).year else ''),rows=sorted(rows,key=lambda a:a['value'],reverse=True)))
    return dict(type='quilt',title='자산군 연간 총수익 순위 · USD',columns=columns,symbols=list(names))

# Country display anchors. These are country aggregates, never claimed as company HQs.
COUNTRIES={'United States':[-98,39],'South Korea':[128,36],'Japan':[138,37],'Taiwan':[121,24],
 'United Kingdom':[-2,54],'Germany':[10,51],'France':[2,47],'Canada':[-106,56],'China':[105,35],
 'India':[79,22],'Switzerland':[8,47],'Netherlands':[5,52],'Ireland':[-8,53],'Luxembourg':[6,50],
 'Israel':[35,31],'Australia':[134,-25],'Brazil':[-51,-10]}

def networks(d,financial,ranks):
    graph=network_data(d,financial,ranks)
    aragorn=module('aragorn',d.as_of,'회전·선택 가능한 3D 관계 지도와 연간 수익률 퀼트를 구현했습니다. 관계는 KRX·미국 GICS 시장/업종 소속이라는 확인 가능한 사실만 연결합니다. 퀼트는 전년 말 대비 배당 조정종가이며 마지막 연도는 YTD입니다.',[graph,quilt(d)],missing=['원본의 매크로 인과 그래프 생성기가 없어 소속 관계를 인과관계로 표시하지 않습니다.'])
    dragon=module('dragonglass',d.as_of,'Entity 360의 기업·업종 관계 탐색과 관측 수치·워치 기록을 연결했습니다. 관계를 선택하면 연결 객체와 수치가 표시됩니다. 판단·시나리오 메모는 브라우저 로컬 원장에 보관됩니다.',[dict(graph,group='관계 지도'),dict(table('Entity 360',['객체','유형','종목','연결 수','1M %','3M %','RS'],[[a['name'],a['kind'],a.get('symbol'),a['degree'],a.get('r1m'),a.get('r3m'),a.get('rs')] for a in graph['nodes']]),group='Entity 360'),dict(type='journal',title='워치·시나리오 원장',group='원장')],missing=['시설·위성 관측·공급망 연결·전파 가중치가 없어 이들 값은 만들지 않았습니다. 원본 11개 하위 화면 중 관계 지도·Entity 360·원장을 구현했습니다.'])
    rows=[a for a in financial if a['country'] in COUNTRIES]
    grouped=[]
    for country in sorted({a['country'] for a in rows}):
        items=[a for a in rows if a['country']==country];grouped.append(dict(name=country,lon=COUNTRIES[country][0],lat=COUNTRIES[country][1],count=len(items),companies=[dict(name=a['name'],symbol=a['symbol'],sector=a['sector'],ytd=a['ytd'],margin=a['margin']) for a in items]))
    globe=module('globe',d.as_of,'정사영 지구본을 회전하며 국가와 기업을 탐색합니다. 기업 소재국은 수집된 공급자 메타데이터, 업종은 공개 카탈로그·공식 시장분류입니다. 지도 점은 국가 집계 위치이며 본사 좌표가 아닙니다.',[dict(type='globe',title='글로벌 기업 유니버스',countries=grouped),table('국가·업종별 기업',['국가','종목','종목코드','업종','YTD %','영업이익률 %'],[[a['country'],a['name'],a['symbol'],a['sector'],a['ytd'],a['margin']] for a in rows])],missing=['UN Comtrade 품목·교역량·물류 경로를 수집하지 않아 무역선이나 금액을 생성하지 않았습니다.'])
    return [aragorn,dragon,globe]

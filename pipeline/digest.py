"""Fact-only ASK summaries over this build's data; no LLM or remote requests."""
import copy,json,re
import numpy as np
import pandas as pd
from .engine import number,ret,ytd,curve,table,zscore
from .catalog import MULTI
from .store import ROOT,read_json
from .macro_modules import ratio
from .iw_review import monthly_states

PERIODS=[('r1w',pd.DateOffset(days=7),'1주'),('r1m',pd.DateOffset(months=1),'1개월'),('r3m',pd.DateOffset(months=3),'3개월'),('r6m',pd.DateOffset(months=6),'6개월'),('r1y',pd.DateOffset(years=1),'1년'),('r2y',pd.DateOffset(years=2),'2년')]
HORIZONS=[('short','단기 · 1주~1개월','r1m'),('mid','중기 · 6개월~1년','r6m'),('long','장기 · 2년','r2y')]


def snapshot(d,symbol):
    p=d.price(symbol).loc[:d.as_of];valid=len(p)>0 and (pd.Timestamp(d.as_of)-p.index[-1]).days<=7
    values={};starts={}
    for key,offset,_ in PERIODS:
        target=pd.Timestamp(d.as_of)-offset;past=p.loc[:target]
        anchor=valid and len(past)>0 and (target-past.index[-1]).days<=7
        values[key]=number((p.iloc[-1]/past.iloc[-1]-1)*100) if anchor else None;starts[key]=str(past.index[-1].date()) if anchor else None
    values['starts']=starts;values['ytd']=ytd(p) if valid else None
    ma=number(p.tail(200).mean()) if valid and len(p)>=200 else None
    values.update(symbol=symbol,date=str(p.index[-1].date()) if len(p) else None,price=number(p.iloc[-1]) if valid else None,ma200=ma)
    values['signal']='미산출' if ma is None or values['r3m'] is None else '상승' if p.iloc[-1]>ma and values['r3m']>0 else '하락' if p.iloc[-1]<ma and values['r3m']<0 else '혼조'
    return values


def themes(d,config):
    result=[]
    for theme in config['themes']:
        members=[dict(m,**snapshot(d,m['symbol'])) for m in theme['members']]
        values={k:number(np.mean([m[k] for m in members])) if all(m[k] is not None for m in members) else None for k in [*[k for k,_,_ in PERIODS],'ytd']}
        result.append(dict(id=theme['id'],name=theme['name'],members=members,returns=values,available=sum(m['price'] is not None for m in members),expected=len(members)))
    values=pd.Series({r['id']:r['returns']['r3m'] for r in result},dtype=float).dropna();ranks=(values.rank(method='average')-1)/max(1,len(values)-1)*100
    for r in result:r['heat']=number(ranks.get(r['id']));r['heat_count']=len(values)
    return sorted(result,key=lambda r:-(r['heat'] if r['heat'] is not None else -1))


def trend_panel(assets,key,title):
    rows=sorted([r for r in assets if r[key] is not None],key=lambda r:(-r[key],r['symbol']))
    return dict(key=key,title=title,leaders=[dict(name=r['name'],symbol=r['symbol'],value=r[key]) for r in rows[:3]],laggards=[dict(name=r['name'],symbol=r['symbol'],value=r[key]) for r in rows[-3:][::-1]],
        rows=[dict(name=r['name'],symbol=r['symbol'],value=r[key],group=r['group'],date=r['date']) for r in rows],available=len(rows),expected=len(assets))


def stock_watch(d,ranks,news):
    result=[]
    for market in ['US','KR']:
        for row in ranks[market]['rows'][:8]:
            r=snapshot(d,row['symbol']);pattern=r'(?<!\w)(?:'+re.escape(row['symbol'].removesuffix('.KS'))+'|'+re.escape(row['name'])+r')(?!\w)'
            matched=[n for n in news if re.search(pattern,n['title'],re.I)]
            result.append(dict(r,name=row['name'],market=market,sector=row['sector'],rs=row['rs'],membership_as_of=ranks[market]['membership_as_of'],
                signals=[f"공식 {market} 유니버스 RS {row['rs']:.1f}",f"가격 추세 {r['signal']}"],news_count=len(matched),news=matched[:3],guru=None))
    return result


def risk_findings(d,objects):
    result=[]
    def add(name,value,date,unit,threshold,higher_risk,module,rule):
        direction=0 if value is None or value==threshold else (-1 if (value>threshold)==higher_risk else 1)
        result.append(dict(name=name,value=number(value),date=date,unit=unit,threshold=threshold,direction=direction,module=module,rule=rule))
    def obs(s,lag=0):
        s=s.loc[:pd.Timestamp(d.as_of)-pd.Timedelta(days=lag)].dropna()
        return (number(s.iloc[-1]),str(s.index[-1].date())) if len(s) else (None,None)
    for name,s,unit,t,up,module,rule,lag in [
        ('VIX',d.price('^VIX'),'index',25,True,'risk','25 초과 변동성 경계 · 동일 값은 경계값',0),
        ('HY OAS',d.mac('BAMLH0A0HYM2'),'%',5,True,'risk','5% 초과 신용 경계 · 동일 값은 경계값',0),
        ('NFCI',d.mac('NFCI'),'z',0,True,'regime','0 초과 긴축 · 관측일에7일 시차',7),
        ('10Y−3M',d.mac('T10Y3M'),'%p',0,False,'pm_weekend','0 미만 장단기 역전',0)]:
        value,date=obs(s,lag);add(name,value,date,unit,t,up,module,rule)
    states=monthly_states(d);state=states[-1] if states else None
    for key,name,unit,t,up in [('m2','M2 YoY','%',0,False),('sahm','Sahm','%p',.5,True)]:
        add(name,state['inputs'][key] if state else None,state['macro_observation_month'] if state else None,unit,t,up,'regime',('0.5 초과 경계' if key=='sahm' else '0 미만 경계')+' · 동일 값은 경계값 · 관측월에2개월 시차')
    for symbol,name in [('SPY','S&P500 ETF'),('^KS11','KOSPI')]:
        r=snapshot(d,symbol);value=(r['price']/r['ma200']-1)*100 if r['price'] and r['ma200'] else None
        add(name+' / MA200',value,r['date'],'%',0,False,'risk','200관측 평균 대비 가격 괴리 · 상승은 추세 관측')
    epu=zscore(d.mac('USEPUINDXD'),252);value,date=obs(epu)
    add('정책 불확실성',value,date,'252D z',1,True,'geoecon','252관측 z가1 초과일 때 경계')
    for r in result:
        # Threshold equality is explicitly a boundary, not an invented direction.
        r['label']='경계' if r['direction']<0 else '위험선호 쪽' if r['direction']>0 else '미산출' if r['value'] is None else '경계값'
    return result


def key_charts(d,objects):
    result=[]
    for name,a,b in [('구리/금','HG=F','GC=F'),('주식/국채 · SPY/TLT','SPY','TLT'),('경기소비/필수소비 · XLY/XLP','XLY','XLP')]:
        s=ratio(d,a,b).loc[:d.as_of]
        result.append(dict(title=name,value=number(s.iloc[-1]) if len(s) else None,change=ret(s,63),change_unit='%',date=str(s.index[-1].date()) if len(s) else None,
            chart=curve(name+' · 최근180공통관측',[(name,s.tail(180),'left')],'가격비')))
    composite=next((s for s in objects['geoecon']['sections'] if s['type']=='geocomposites'),None)
    source=next(p['chart'] for p in composite['panels'] if p['id']=='stress') if composite else next(s for s in objects['geoecon']['sections'] if s.get('group')=='복합지표' and s['type']=='line')
    chart=copy.deepcopy(source);points=chart['series'][0]['points'];last=points[-1] if points else [None,None]
    result.append(dict(title='금융 스트레스 · VIX/HY' if composite else '금융·정책 스트레스',value=last[1],date=last[0],change=number(last[1]-points[-64][1]) if len(points)>63 else None,change_unit='z 차이',chart=chart))
    return result


def module_summaries(objects):
    summaries=[];labels={r['id']:r['title'] for r in json.loads((ROOT/'docs/modules.js').read_text(encoding='utf-8').removeprefix('const MODULES = ').strip().removesuffix(';'))}
    for key,d in objects.items():
        if key in ['principium','iw','ask_digest']:continue
        groups=list(dict.fromkeys(s.get('group','종합') for s in d.get('sections',[])))
        observations=[]
        for s in d.get('sections',[]):
            if s['type'] in ['table','quantledger'] and s['rows']:
                observations.append(dict(title=s['title'],columns=s['columns'][:7],rows=[r[:7] for r in s['rows'][:2]]))
            if len(observations)>=2:break
        summaries.append(dict(module=key,title=labels.get(key,key),as_of=d['as_of'],status=d['status'],cards=d.get('cards',[])[:6],groups=groups,observations=observations,missing=d.get('missing',[]),method_note=d['method_note']))
    return summaries


def digest_views(d,objects,ranks,news):
    config=read_json(ROOT/'config/digest_themes.json');assets=[dict(snapshot(d,s),name=n,group=g) for s,n,g in MULTI]
    panels=[dict(trend_panel(assets,key,title),id=id) for id,title,key in HORIZONS]
    cut=pd.Timestamp(d.as_of,tz='Asia/Seoul')+pd.Timedelta(days=1)
    eligible=[n for n in news if pd.Timestamp(n['published_at'])<cut]
    theme_rows=themes(d,config);stocks=stock_watch(d,ranks,eligible);risk=risk_findings(d,objects);charts=key_charts(d,objects)
    inputs=dict(objects)
    for key in ['rs','momentum','ml','maximus']:
        inputs[key]=read_json(ROOT/'docs/data'/(key+'.json'))
        if inputs[key]['as_of']>d.as_of:raise ValueError('Digest source newer than requested date: '+key)
    summaries=module_summaries(inputs)
    top=panels[0]['leaders'];theme=next((t for t in theme_rows if t['heat'] is not None),None)
    brief=dict(headline='단기 자산 추세 · '+(' / '.join(r['name'] for r in top) or '미산출'),
        market='현재 등록21자산의1개월 관측 수익률 상위입니다. '+('10개 사업 관찰목록 중3개월 평균이 가장 높은 테마는 '+theme['name']+'입니다.' if theme else '테마 가격은 준비 중입니다.'),
        horizons=[dict(title=p['title'],text='관측 상승 상위: '+', '.join(f"{r['name']} {r['value']:+.1f}%" for r in p['leaders'])+' / 하위: '+', '.join(f"{r['name']} {r['value']:+.1f}%" for r in p['laggards'])) for p in panels],
        note='기간은 과거 관측 창입니다. 향후 기대수익·매수 제안·자동 AI 분석을 생성한 것이 아닙니다.')
    prior=objects['ask_digest'];journal=[s for s in prior['sections'] if s['type']=='notebook']
    prior['sections']=[dict(type='digestbrief',title='시장 브리프',group='시장 브리프',**brief),
        dict(type='digesttrends',title='단기·중기·장기 추세',group='기간별 추세',panels=panels),
        dict(type='digestthemes',title='10개 사업 테마 · 공개 근거와 관측',group='테마 관찰',items=theme_rows,reviewed_at=config['reviewed_at'],scope=config['scope']),
        dict(type='digeststocks',title='공식 유니버스 RS 관찰16종목',group='종목 관찰',items=stocks,news_sample=len(eligible)),
        dict(table('21자산 · 시세/ETF 식별과 기간 수익률',['그룹','이름','심볼','실제 가격일','1W %','3M %','YTD %','가격 추세'],[[r['group'],r['name'],r['symbol'],r['date'],r['r1w'],r['r3m'],r['ytd'],r['signal']] for r in assets]),group='크로스에셋'),
        dict(type='digestrisk',title='위험선호·경계 관측',group='위험 요약',items=risk),
        dict(type='digestcharts',title='4개 핵심 차트',group='핵심 차트',items=charts),
        dict(type='digestmodules',title='모듈별 근거 요약',group='모듈 요약',items=summaries),
        dict(type='library',title='최근 공개 발표·보도 원문',group='최근 뉴스',items=eligible[:30])]+journal
    prior['cards']=[('사업 테마',len(theme_rows)),('공식 RS 관찰',len(stocks)),('크로스에셋',len(assets)),('요약 모듈',len(summaries))]
    prior['method_note']='ASK의 brief/기간별 추세/10테마/16종목/21자산/위험 양음/4핵심 차트/모듈별 요약 구조에 독립 계산값을 연결합니다. 테마 구성·사업 근거와 KRX/GICS 공식 산업분류는 구분합니다. 수익률은 조정가격, 핵심 차트의 비율은 비조정 종가 기준입니다. 선물은 근월물 가격 변화이며 롤 투자 성과가 아닙니다. 각 자산 현지 호가/통화 기준이며 원화환산하지 않습니다. 수치 기반 규칙 요약은 정기 수집 후 자동 재생성됩니다.'
    prior['missing']=['테마는 공식 사업 설명으로 구성한1~2기업 표본이며 전체 테마 수익률·사업 매출 순도·원본 heat 모델이 아닙니다. 현재 목록으로 과거 수익을 관찰하며 역사 편입 시점 성과가 아닙니다.',
        '구루 보유·전체 기업 뉴스 관심량·원본 LLM 해석은 미연결입니다. 표시한 RSS 제목 표본의 명시적 종목명 일치만 집계합니다.',
        '정적 사이트에는 자동 AI 질의 서버가 없습니다. 개인 질문·근거·첨부는 브라우저 로컬 기록에 저장합니다.']

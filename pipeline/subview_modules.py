"""Data-backed subviews. Estimates, observations and research rules stay distinct."""
import re
from collections import Counter
import numpy as np
import pandas as pd
from .engine import *
from .events_data import read
from .financial_modules import frame
from .macro_modules import regime_frame
from .platform_modules import LIBRARY

def event_data(d):
    result={}
    for base in d.bases:
        for p in (base/'events').glob('*.json.gz'):
            r=read(p);result[r['symbol']]=r
    return result

def event_returns(price,benchmark,timestamp,close_hour=16):
    """D0 is first regular close after release; drift starts at that close."""
    t=pd.Timestamp(timestamp)
    if t.tzinfo is None:return None
    local=t.tz_convert('America/New_York');day=local.tz_localize(None).normalize()
    eligible=price.index[price.index>day] if local.hour>=close_hour else price.index[price.index>=day]
    if not len(eligible):return None
    first=eligible[0];i=price.index.get_loc(first)
    if i==0:return None
    output=dict(first_session=str(first.date()),reaction=number((price.iloc[i]/price.iloc[i-1]-1)*100),drift=number((price.iloc[-1]/price.iloc[i]-1)*100),sessions=len(price)-i-1,curve=[])
    for h in [5,20]:
        output['d'+str(h)]=number((price.iloc[i+h]/price.iloc[i]-1)*100) if i+h<len(price) else None
        target=price.index[i+h] if i+h<len(price) else None
        output['excess'+str(h)]=number(output['d'+str(h)]-(benchmark.loc[target]/benchmark.loc[first]-1)*100) if target in benchmark.index and first in benchmark.index else None
    if first in benchmark.index:
        for j in range(i,min(len(price),i+21)):
            date=price.index[j]
            if date in benchmark.index:output['curve'].append(dict(x=j-i,y=number(((price.iloc[j]/price.iloc[i]-1)-(benchmark.loc[date]/benchmark.loc[first]-1))*100),name=str(date.date())))
    return output

def strategy_views(d,obj,events,quant):
    buys=[];pead=[];calendar=[];cut=pd.Timestamp(d.as_of);bench=d.price('SPY')
    for symbol,raw in events.items():
        f=frame(raw.get('insider'));price=d.price(symbol)
        if len(f):
            for _,r in f.iterrows():
                text=str(r.get('Text',''));date=pd.Timestamp(r.get('Start Date'))
                if date.tzinfo is not None:date=date.tz_localize(None)
                if pd.isna(date) or not cut-pd.Timedelta(days=90)<=date<=cut or not re.match(r'^Purchase\b',text,re.I):continue
                value=number(r.get('Value'));shares=number(r.get('Shares'))
                if value is None or value<=0 or shares is None or shares<=0:continue
                buys.append([symbol,str(date.date()),str(r.get('Insider','')),str(r.get('Position','')),shares,value,raw['retrieved_at'][:10]])
        f=frame(raw.get('earnings_dates'))
        if not len(price) or not len(f):continue
        for date,r in f.iterrows():
            t=pd.Timestamp(date);actual=number(r.get('Reported EPS'));surprise=number(r.get('Surprise(%)'))
            if t.tzinfo is None:continue
            local=t.tz_convert('America/New_York')
            if cut-pd.Timedelta(days=30)<=local.tz_localize(None)<=cut+pd.Timedelta(days=90):calendar.append([symbol,local.strftime('%Y-%m-%d %H:%M %Z'),number(r.get('EPS Estimate')),actual,surprise,'확정 실적' if actual is not None else '제공처 예정일'])
            if actual is None or surprise is None or local.tz_localize(None)<cut-pd.Timedelta(days=180):continue
            study=event_returns(price,bench,t)
            if study:pead.append(dict(symbol=symbol,published_at=t.isoformat(),surprise=surprise,**study))
    aggregate=[]
    for symbol in sorted({r[0] for r in buys}):
        r=[a for a in buys if a[0]==symbol];aggregate.append([symbol,len(set(a[2] for a in r)),len(r),sum(a[5] for a in r)/1e6,max(a[1] for a in r)])
    aggregate.sort(key=lambda r:r[3],reverse=True)
    obj['sections'] += [dict(table('90일 내부자 매수 클러스터',['종목','매수자 수','거래 수','금액 USD mn','최근 거래일'],aggregate),group='내부자 매수'),dict(table('매수 거래 원장',['종목','거래일','공시 내부자','직책','주식 수','USD 금액','수집일'],sorted(buys,key=lambda r:r[1],reverse=True)),group='내부자 매수')]
    pead.sort(key=lambda r:r['published_at'],reverse=True)
    obj['sections'].append(dict(table('발표 후 드리프트 · 최근 180일',['종목','발표 UTC','첫 반응 세션','서프라이즈 %','D0 반응 %','D+5 %','D+20 %','D+20 SPY 대비 %p','현재까지 %'],[[r['symbol'],r['published_at'],r['first_session'],r['surprise'],r['reaction'],r['d5'],r['d20'],r['excess20'],r['drift']] for r in pead]),group='PEAD'))
    for r in [r for r in pead if r['surprise']>=5 and len(r['curve'])>1][:8]:obj['sections'].append(dict(type='scatter',title=r['symbol']+' · '+r['first_session']+' 이후 SPY 대비',group='PEAD',trajectory=True,x_label='D0 이후 거래 관측',y_label='누적 초과수익 %p',points=r['curve']))
    obj['sections'] += [dict(s,group='스탯아브 페어') for s in quant['sections'] if s.get('group')=='Stat Arb']
    obj['method_note']+=' 내부자 매수는 제공처 Text의 Purchase·양의 금액만 선별하며 주식보상·증여·매도는 제외합니다. SEC 원문 코드P를 직접 대조한 목록은 아닙니다. PEAD는 실제 발표 시각을 미국 동부시간으로 정렬해 첫 반응 세션(D0) 이후 5·20거래일 수익률과 SPY 대비를 계산합니다. 현재 관측 이벤트 연구이며 매매 백테스트가 아닙니다.'
    obj['missing']=['내부자 거래의 SEC 원문 코드P·제출시점 교차검증과 전략별 거래비용 후 OOS는 남아 있습니다. 신규 수집 대상은 미국 60개 기업이며 전체 미국 시장을 의미하지 않습니다.']
    return calendar

def revision_views(d,obj,events):
    rows=[];trends=[]
    for s,raw in events.items():
        f=frame(raw.get('eps_revisions'));t=frame(raw.get('eps_trend'))
        for h in ['0y','+1y']:
            if h in f.index:
                a=f.loc[h];up=number(a.get('upLast30days'));down=number(a.get('downLast30days'))
                rows.append([s,h,up,down,number(up-down) if up is not None and down is not None else None,raw['retrieved_at'][:10]])
            if h in t.index:trends.append(dict(name=s+' '+h,group=h,values=[number(t.loc[h].get(k)) for k in ['90daysAgo','60daysAgo','30daysAgo','7daysAgo','current']]))
    obj['sections'] += [dict(table('FY EPS 추정치 상향·하향',['종목','회계연도','30D 상향 수','30D 하향 수','순상향 수','수집일'],rows),group='추정치 변화'),dict(heat('EPS 추정 빈티지 · 원통화/주',['90일 전','60일 전','30일 전','7일 전','현재'],trends),group='추정치 변화')]

def news_views(d,obj):
    from .geoecon_views import news_views as build_news
    return build_news(d,obj)


def regime_views(d,obj,calendar):
    for s in obj['sections']:
        t=s['title'];s['group']='월별 국면' if '월별' in t else '국면 전이' if '국면 전이' in t else '미국 경제국면' if t.startswith('US') else '한국 시장국면' if t.startswith('KR') else '시장국면'
    for market in ['US','KR']:
        reg=regime_frame(d,market);labels=reg.regime.copy();labels.index=labels.index+pd.offsets.MonthEnd(0)
        rows=[]
        for symbol in ['SPY','QQQ','IWM','TLT','IEF','GLD','HYG','EEM']:
            r=d.monthly(symbol).pct_change(fill_method=None)*100;f=pd.concat(dict(ret=r,regime=labels.reindex(r.index).shift(2)),axis=1).dropna()
            for label,g in f.groupby('regime'):rows.append([market,label,symbol,len(g),number(g.ret.mean()),number((g.ret>0).mean()*100)])
        obj['sections'].append(dict(table(market+' 국면별 다음 월 자산 성과 · 정보시차2개월',['국면 기준','국면','자산','월 수','평균 월수익 %','상승 월 %'],rows),group='국면별 성과'))
    vals=[]
    for symbol,raw in d.fund.items():
        info=raw['info'];pe=number(info.get('trailingPE'));forward=number(info.get('forwardPE'))
        if pe is not None and pe>0:vals.append([symbol,info.get('sector'),pe,forward,number(100/forward) if forward and forward>0 else None,raw['retrieved_at'][:10]])
    obj['sections'] += [dict(table('종목별 밸류에이션 · 지수 P/E와 구분',['종목','섹터','TTM P/E','Forward P/E','Forward 이익수익률 %','수집일'],vals),group='밸류에이션'),dict(table('실적 발표 달력 · 시각은 미국 동부시간',['종목','발표/예정 시각','EPS 추정','발표 EPS','서프라이즈 %','상태'],sorted(calendar,key=lambda r:r[1])),group='실적 이벤트')]
    obj['method_note']+=' 국면별 성과는 거시 관측월에2개월 시차를 적용한 월 수익률 조건부 평균입니다. 최신 수정 빈티지여서 실시간 PIT 성과로 해석하지 않습니다.'
    obj['missing']=['지수 전체의 역사 이익·밸류에이션 3단 게이지, 원본 Soros 합성 엔진·거시 발표 달력은 남아 있습니다. 종목 P/E를 지수 P/E로 표시하지 않습니다.']

def cot_views(d,obj):
    path=d.resource('cot.json.gz')
    if not path.exists():return
    raw=read(path);f=pd.DataFrame(raw['rows']);f['date']=pd.to_datetime(f.report_date_as_yyyy_mm_dd);rows=[]
    for name,g in f.groupby('contract_market_name'):
        g=g.sort_values('date').set_index('date');num=lambda k:pd.to_numeric(g[k],errors='coerce');oi=num('open_interest_all')
        lev=num('lev_money_positions_long')-num('lev_money_positions_short');asset=num('asset_mgr_positions_long')-num('asset_mgr_positions_short')
        obj['sections'].append(dict(curve(name+' · CFTC 보고 순포지션',[('Leveraged funds',lev,'left'),('Asset managers',asset,'left')],'계약 수',guides=[0]),group='CFTC 포지션'))
        rows.append([name,str(g.index[-1].date()),number(lev.iloc[-1]),number(asset.iloc[-1]),number(oi.iloc[-1]),number(lev.iloc[-1]/oi.iloc[-1]*100)])
    obj['sections'].append(dict(table('CFTC TFF · Futures Only',['계약','포지션 기준일','레버리지펀드 순계약','자산운용 순계약','전체 OI','레버리지펀드 순/OI %'],rows),group='CFTC 포지션'))
    obj['method_note']+=' CFTC TFF는 선물만의 주간 보고값이며 레버리지펀드는 CTA 전체와 같지 않습니다. 계약별 단위가 달라 계약 수를 자산 간 달러 익스포저처럼 합하지 않습니다.'

def dragon_views(d,obj,ranks,news,events):
    from .entities import entity_view, sensitivity
    from .financial_modules import financial_rows
    from .relation_views import companies
    from .attention_data import settings as attention_settings
    from .company_news import settings as news_settings
    obj["sections"]=[s for s in obj["sections"] if s.get("group")!="기업 상세" and s["type"]!="journal"]
    attention_companies=[dict(symbol=p['symbol'],name=p['title']) for p in attention_settings()['pages']]
    obj["sections"] += [entity_view(d,ranks,financial_rows(d),events,extra=companies()+attention_companies+news_settings()),dict(type="decisions",title="결정 원장",group="결정 원장")]
    for s in obj['sections']:
        if s['type']=='journal':s['group']='결정 원장'
    leaders=[dict(a,market=m) for m in ['KR','US'] for a in ranks[m]['leaders']];scenarios=[];alerts=[]
    for a in leaders:
        p=d.price(a['symbol']);b=d.price('^KS11' if a['market']=='KR' else 'SPY');r=pd.concat(dict(stock=p.pct_change(),benchmark=b.pct_change()),axis=1).dropna().tail(252)
        beta=sensitivity(p,b)
        if beta:scenarios.append(dict(symbol=a['symbol'],name=a['name'],market=a['market'],**beta))
        previous=rsi(p).iloc[-2];signal='RSI70 상향돌파' if previous<70<=a['rsi'] else 'RSI30 하향돌파' if previous>30>=a['rsi'] else '52주 고점 1% 이내' if a['high52']>=-1 else None
        if signal:alerts.append([a['name'],a['symbol'],signal,a['rs'],a['rsi'],a['as_of']])
    sources=[[k,m.get('name',k),m.get('source','FRED'),str(d.mac(k).index[-1].date()),m.get('unit'),m.get('retrieved_at','')[:10]] for k,m in d.macro_meta.items() if len(d.mac(k))]
    obj['sections'] += [dict(table('주목 종목 · 시장별 RS 상위15',['종목','시장','업종','RS','1W %','1M %','52주 고점 대비 %'],[[a['name'],a['market'],a['sector'],a['rs'],a['r1w'],a['r1m'],a['high52']] for a in leaders]),group='지금 주목'),dict(type='scenario',title='시장 충격 민감도 · 역사 Beta 선형 추정',group='시나리오',rows=scenarios),dict(table('가격 트리거 · 현재 관측 조건',['종목','코드','조건','RS','RSI','가격일'],alerts),group='트리거·촉매'),dict(type='library',title='팀 방법론·최근 원문 링크',group='리서치',items=LIBRARY+news[:12]),dict(table('거시 데이터 원장',['계열','지표','제공처','관측일','단위','수집일'],sources),group='데이터 소스'),dict(table('가격 수집·보정 현황',['항목','값'],[['가격 시계열',len(d.frames)],['거시 시계열',len(d.macro)],['재무 캐시',len(d.fund)],['KRX 보정 관측',d.correction_meta['corrected']],['KRX 격리 관측',d.correction_meta['quarantined']]]),group='현황판'),dict(type='text',title='관계와 충격 추정의 정의',group='방법론',text='관계 지도는 공식 시장/업종 소속이다. 시나리오는 최근252개 공통 일 수익률 Beta×사용자가 가정한 시장 충격으로 계산하며 인과 전파나 확정 손익이 아니다. 가격 트리거는 관측 조건이고 외부 알림·자동 주문을 발생시키지 않는다. 기업 상세은 현재 공식 유니버스의 가격·재무·실적 일정을 연결한다. 결정 원장은 가설·확신도·촉매·무효화·비중과 제안/실행/청산을 기록하며 실행 기록만 포트폴리오 민감도에 집계한다.')]
    obj['method_note']+=' 지금 주목·트리거·데이터 소스·현황판·방법론과 Beta 기반 선형 시나리오를 연결했습니다.'
    obj['missing']=['위성사진은 시설별 좌표·실관측 시계열이 없어 남아 있습니다. 시나리오는 원본의 공급망 인과 전파 엔진과 다릅니다. 결정 원장은 구조화된 브라우저 로컬 기록이며 팀 공용 DB가 아닙니다. 원본의 관계 기반 프리모템·군집 진단은 후속 대상입니다.']

def extend(d,objects,ranks):
    from .earnings_details import earnings_detail_views
    earnings_detail_views(d,objects['earnings'])
    events=event_data(d);calendar=strategy_views(d,objects['strategies'],events,objects['quant'])
    from .ownership_views import ownership_views
    ownership_views(d,objects['strategies'],events)
    revision_views(d,objects['earnings'],events);news=news_views(d,objects['geoecon']);regime_views(d,objects['regime'],calendar)
    dragon_views(d,objects['dragonglass'],ranks,news,events)
    from .pm_details import extend_pm
    from .industry_details import industry_views
    from .reflexivity import reflex_views
    extend_pm(d,objects['pm_weekend'],calendar)
    reflex_views(d,objects['regime']);industry_views(d,objects['regime'])
    from .valuation import valuation_views
    valuation_views(d,objects['regime'])
    from .calendar_views import calendar_views
    calendar_views(d,objects['regime'])
    cot_views(d,objects['pm_weekend']);cot_views(d,objects['risk'])
    from .wagdog import wagdog_views
    wagdog_views(d,objects['risk'])
    from .flows import flow_views,earnings_views
    flow_inputs=flow_views(d,objects['risk'])
    from .kr_shortgamma import views as kr_shortgamma_views
    kr_shortgamma_views(d,objects['risk'])
    if flow_inputs:earnings_views(d,objects['pm_weekend'],objects['earnings'],flow_inputs)
    for s in objects['risk']['sections']:
        if s.get('group'):continue
        t=s['title'];s['group']='파생·옵션' if any(k in t for k in ['GEX','감마','옵션','VIX','SKEW']) else '신호등 US·KR' if any(k in t for k in ['조기경보','변동성 · 시장']) else '쏠림·신용' if any(k in t for k in ['쏠림','신용']) else '리스크 콕핏'
    from .allocation_views import allocation_views
    allocation_views(d,objects['multiasset'])
    from .risk_cockpit import views as cockpit_views
    cockpit_views(d,objects['risk'],objects['multiasset'])
    from .risk_signals import views as risk_signal_views
    risk_signal_views(d,objects['risk'])
    from .technical_scan import scanner_view
    objects['multiasset']['sections'][2]=scanner_view(d)
    for i,s in enumerate(objects['multiasset']['sections']):s['group']='자산 모니터' if i<2 else '패턴 스캐너' if i==2 else '자산배분'
    from .asset_monitor import views as asset_monitor_views
    asset_monitor_views(d,objects['multiasset'])
    from .strategy_cards import views as strategy_card_views
    strategy_card_views(d,objects['strategies'])
    from .pead import views as pead_views
    pead_views(d,objects['strategies'])
    objects['ask_digest']['sections'].insert(0,dict(type='library',title='최근 발표·보도 원문',group='최근 뉴스',items=news[:30]))
    from .iw_review import iw_views
    iw_views(d,objects)
    from .digest import digest_views
    from .relation_views import relation_views
    relation_views(d,objects['dragonglass'])
    from .relation_discovery import views as relation_discovery_views
    relation_discovery_views(d,objects['dragonglass'])
    from .satellite_views import satellite_views
    satellite_views(d,objects['dragonglass'])
    from .dragon_research import views as dragon_research_views
    dragon_research_views(d,objects['dragonglass'])
    from .trade_views import views as trade_views
    trade_views(d,objects['globe'])
    from .sauron_views import views as sauron_views
    sauron_views(d,objects['globe'])
    from .chain_views import views as chain_views
    chain_views(d,objects['globe'])
    digest_views(d,objects,ranks,news)
    from .dragon_signals import views as dragon_signal_views
    from .attention_views import views as attention_views
    attention_views(d,objects['dragonglass'])
    from .company_news import views as company_news_views
    company_news_views(d,objects['dragonglass'])
    dragon_signal_views(objects,ranks)
    from .clinical_views import views as clinical_views
    clinical_views(d,objects["dragonglass"])
    from .guru_views import views as guru_views
    guru_views(d,objects["dragonglass"])
    from .dragon_operations import views as operation_views
    operation_views(d,objects)
    from .digest import module_summaries
    for s in objects["ask_digest"]["sections"]:
        if s["type"]=="digestmodules":
            for row in module_summaries({"dragonglass":objects["dragonglass"]}):
                s["items"]=[row if r["module"]=="dragonglass" else r for r in s["items"]]
    return objects

"""KOSPI200 daily-reset flow exposure and descriptive price diagnostics."""
import numpy as np
import pandas as pd
from .engine import number, rsi, table, curve
from .events_data import read
from .kr_shortgamma_data import FOLDER, BENCHMARKS, definitions, expiry_dates, history, numeric

GROUP='KOSPI 숏감마'
NOTE='ETF 일간 목표배율의 리밸런싱 민감도이며 옵션 OI 기반 딜러 감마가 아닙니다. 설정·환매, 실제 운용·헤지 및 장중 체결을 반영하지 않아 실제 종가 주문액이나 주가 영향의 예측이 아닙니다.'


def price_diagnostics(rows):
    f=pd.DataFrame(rows).set_index('date');f.index=pd.to_datetime(f.index);f=f.sort_index()
    c=f.close;r=c.pct_change(fill_method=None)
    rv=r.rolling(21,min_periods=21).std(ddof=1)*np.sqrt(252)*100
    short=r.rolling(5,min_periods=5).std(ddof=1)*np.sqrt(252)*100
    span=f.high-f.low;position=(c-f.low)/span.where(span>0)
    extreme=((position<=.15+1e-12)|(position>=.85-1e-12)).astype(float).where(position.notna())
    valid=extreme.notna().rolling(20,min_periods=20).sum()
    frequency=extreme.fillna(0).rolling(20,min_periods=20).sum()/valid.where(valid>0)*100
    high=c/f.high.rolling(252,min_periods=252).max()
    gate=((high-.9)/.1).clip(0,1)
    mean=rv.rolling(252,min_periods=252).mean();sd=rv.rolling(252,min_periods=252).std(ddof=0)
    z=((rv-mean)/sd.where(sd>0)).mask((sd==0)&mean.notna(),0)
    acceleration=(rv/rv.shift(21).where(rv.shift(21)>0)-1).mask((rv==0)&(rv.shift(21)==0),0)
    momentum=c.pct_change(63,fill_method=None)*100;strength=rsi(c)
    components=pd.DataFrame(dict(regime=(z/2).clip(0,1),expansion=(acceleration/.5).clip(0,1),heat=((strength-50)/30).clip(0,1),speed=(momentum/30).clip(0,1)))
    # Team parameters: all four inputs must be available, never mean(skipna).
    score=gate*components.mul([.4,.25,.2,.15]).sum(axis=1,min_count=4)*100
    out=pd.DataFrame(dict(close=c,return_pct=r*100,rv21=rv,rv5=short,vol_ratio=short/rv.where(rv>0),extreme_pct=frequency,extreme_valid=valid,high_pct=high*100,gate=gate,rv_z=z,rv_change_pct=acceleration*100,rsi=strength,return_3m=momentum,score=score,score_max60=score.rolling(60,min_periods=60).max()))
    return out


def fund_exposure(raw,master,as_of):
    day=pd.Timestamp(raw['date']).strftime('%Y-%m-%d') if raw else None
    if day and day>as_of:raise ValueError('Future KRX ETF AUM')
    observed={r['code']:r for r in raw.get('etfs',[])}
    if len(observed)!=len(raw.get('etfs',[])):raise ValueError('Duplicate KRX ETF quote')
    rows=[]
    for definition in definitions(master,as_of):
        code=definition['code'];quote=observed.get(code,{})
        matched=quote.get('benchmark','').replace(' ','')==definition['benchmark'].replace(' ','')
        reported=numeric(quote.get('reported_net_assets'));nav=numeric(quote.get('nav'));shares=numeric(quote.get('shares'))
        aum=reported if reported is not None and reported>0 else nav*shares if nav and nav>0 and shares and shares>0 else None
        reason='' if matched and aum and definition['leverage'] in [-2,-1,2,3,-3] else '기초지수·배율·순자산 확인 부족'
        if reason:aum=None
        method='KRX 보고 순자산총액' if reported is not None and reported>0 else 'NAV × 상장좌수 (대체)'
        L=definition['leverage'];coefficient=aum*(L*L-L) if aum is not None else None
        rows.append(dict(definition,aum_krw=aum,aum_method=method,date=day,coefficient=coefficient,per_1pct_krw=coefficient*.01 if coefficient is not None else None,reason=reason))
    # An unmatched leveraged quote must be exposed, not disappear from totals.
    known={r['code'] for r in rows}
    for code,r in observed.items():
        if code not in known and r['benchmark'].replace(' ','') in BENCHMARKS and any(k in r['name'] for k in ['레버리지','인버스']):
            rows.append(dict(code=code,name=r['name'],benchmark=r['benchmark'],kind=BENCHMARKS[r['benchmark'].replace(' ','')],leverage=None,leverage_label='미확인',listed_at=None,aum_krw=None,aum_method=None,date=day,coefficient=None,per_1pct_krw=None,reason='KRX 공식 배율 정의 미확보'))
    return sorted(rows,key=lambda r:-(r['aum_krw'] or 0)),day


def packet(d):
    def raw(name):
        p=d.resource(name)
        return read(p) if p.exists() else {}
    prices=history(d);master=raw(FOLDER+'etf_definitions.json.gz');kr=raw('flows/krx.json.gz');expiry=raw(FOLDER+'expiries.json.gz');collection=raw(FOLDER+'collection.json.gz');index=raw(FOLDER+'index.json.gz')
    f=price_diagnostics(prices) if prices else pd.DataFrame()
    latest={k:number(v) for k,v in f.iloc[-1].items()} if len(f) else {}
    price_date=f.index[-1].strftime('%Y-%m-%d') if len(f) else None
    funds,aum_date=fund_exposure(kr,master,d.as_of)
    covered=[r for r in funds if r['coefficient'] is not None]
    coefficient=sum(r['coefficient'] for r in covered) if covered else None
    complete=bool(funds) and len(covered)==len(funds)
    dates=expiry_dates(expiry);upcoming=next((date for date in dates if date>=d.as_of),None)
    days=(pd.Timestamp(upcoming)-pd.Timestamp(d.as_of)).days if upcoming else None
    one_pct=coefficient*.01 if coefficient is not None else None
    daily=coefficient*latest['rv21']/100/np.sqrt(252) if coefficient is not None and latest.get('rv21') is not None else None
    metadata=dict(as_of=d.as_of,price_date=price_date,aum_date=aum_date,index_code='1028',price_observations=len(f),fund_count=len(funds),covered_funds=len(covered),complete=complete,
        per_1pct_krw=number(one_pct),daily_sigma_krw=number(daily),next_expiry=upcoming,days_to_expiry=days,expiries=dates,latest=latest,funds=funds,
        definitions_retrieved_at=master.get('retrieved_at'),aum_retrieved_at=kr.get('retrieved_at'),index_retrieved_at=index.get('retrieved_at'),expiry_retrieved_at=expiry.get('retrieved_at'),collection=collection,
        future_definition_snapshot=bool(master and pd.Timestamp(master['retrieved_at']).tz_convert('Asia/Seoul').strftime('%Y-%m-%d')>d.as_of))
    metadata['stale']=any(not date or (pd.Timestamp(d.as_of)-pd.Timestamp(date)).days>7 for date in [price_date,aum_date])
    metadata['definition_stale']=not master or (pd.Timestamp(d.as_of)-pd.Timestamp(master['retrieved_at']).tz_convert('Asia/Seoul').tz_localize(None).normalize()).days>14
    metadata['collection_failed']=any(r.get('status')=='error' for r in collection.get('parts',[]))
    return metadata,f


def views(d,obj):
    p,f=packet(d);v=p['latest']
    fmt=lambda x,unit='',digits=1:'미확보' if x is None else f'{x:,.{digits}f}'+unit
    signal=lambda x,cuts:'미확보' if x is None else ['관측','주의','경계'][min(2,sum(x>=cut for cut in cuts))]
    meta=f"분석 기준 {d.as_of} · KOSPI200 시세 {p['price_date'] or '미확보'} · ETF 순자산 {p['aum_date'] or '미확보'} · 공식 대상 {p['fund_count']}개 중 {p['covered_funds']}개 확보."
    if p['stale'] or p['definition_stale'] or p['collection_failed']:meta+=' 일부 입력이 오래됐거나 수집에 실패했습니다. 아래 원장의 기준일을 확인하세요.'
    rows=[
        ['선행 취약성 종합지수 · 팀 설정',fmt(v.get('score'),'/100')+' (60거래일 최고 '+fmt(v.get('score_max60'))+')','≥45 주의 · ≥70 경계; 검증된 붕괴 확률 아님',signal(v.get('score'),[45,70])],
        ['구성 · 신고가 근접 / 변동성 / 과열','252일 고점의 '+fmt(v.get('high_pct'),'%')+' · RV '+fmt(v.get('rv21'),'%')+' · RSI '+fmt(v.get('rsi'))+' · 3M '+fmt(v.get('return_3m'),'%'),'고점 근접 게이트 × 변동성 국면·상승·RSI·3M 급등 속도','분해 관측'],
        ['레버리지·인버스 ETF 리밸런싱 · 지수 ±1%',fmt(p['per_1pct_krw']/1e8 if p['per_1pct_krw'] is not None else None,'억원'),'Σ 순자산 × (L²−L) × 1%; 상승 시 매수·하락 시 매도 가정','전체 확보' if p['complete'] else '일부/미확보'],
        ['현재 변동성의 하루 리밸런싱 · 1σ 크기',fmt(p['daily_sigma_krw']/1e8 if p['daily_sigma_krw'] is not None else None,'억원'),'위 민감도 × 21일 일간 σ; 실제 주문량·통계적 기대 절대액 아님','규모 추정'],
        ['KOSPI200 실현변동성 · 21일 연율',fmt(v.get('rv21'),'%'),'≥25% 주의 · ≥40% 경계; 옵션 내재 VKOSPI와 다른 지표',signal(v.get('rv21'),[25,40])],
        ['단기/장기 실현변동성 · 5일/21일',fmt(v.get('vol_ratio'),'',2),'≥1.1 확대 관찰선',signal(v.get('vol_ratio'),[1.1])],
        ['월간 옵션 만기 · 3·6·9·12월 선물 동시',f"D-{p['days_to_expiry']} ({p['next_expiry']})" if p['next_expiry'] else '미확보','KRX 실제 최종거래일; 분석기준일부터 0~5일 관찰, 위클리 제외','만기 근접' if p['days_to_expiry'] is not None and p['days_to_expiry']<=5 else '관측' if p['next_expiry'] else '미확보'],
        ['종가 극단 마감 · 최근20거래일',fmt(v.get('extreme_pct'),'%')+' (유효 '+fmt(v.get('extreme_valid'),digits=0)+'/20)','종가가 당일 고/저 15% 이내; ≥35% 관찰, 고가=저가 제외',signal(v.get('extreme_pct'),[35])]
    ]
    sections=[dict(type='text',title='KOSPI200 · 리밸런싱과 가격 취약성',text=meta+' '+NOTE),table('KOSPI 숏감마 · 8개 관측',['지표','현재 관측','정의·관찰선','상태'],rows)]
    if len(f):
        recent=f.tail(252)
        sections += [curve('팀 취약성 · 최근252거래일', [('취약성 점수',recent.score,'left')],left='0–100 점수',guides=[45,70],limits=[0,100]),
            curve('KOSPI200 실현변동성 · 최근252거래일',[('21일 RV',recent.rv21,'left'),('5일 RV',recent.rv5,'left')],left='연율 %',guides=[25,40]),
            table('취약성 구성·최근60거래일 계산 원장',['날짜','지수','고점 근접 %','게이트 0~1','RV21 %','RV z','RV 21일 변화 %','RSI14','3M %','점수'],[[t.strftime('%Y-%m-%d')]+[number(r[k]) for k in ['close','high_pct','gate','rv21','rv_z','rv_change_pct','rsi','return_3m','score']] for t,r in f.tail(60).iloc[::-1].iterrows()])]
    sections += [table('공식 ETF 대상·순자산·배율',['코드','상품명','KRX 기초지수','일간 배율','순자산 억원','±1% 민감도 억원','순자산 기준일','순자산 방식','확보 상태'],[[r['code'],r['name'],r['benchmark'],r['leverage'],number(r['aum_krw']/1e8) if r['aum_krw'] is not None else None,number(r['per_1pct_krw']/1e8) if r['per_1pct_krw'] is not None else None,r['date'],r['aum_method'],r['reason'] or '확인'] for r in p['funds']]),
        table('기초지수별 리밸런싱 분해',['기초지수','ETF 수','확보 수','+1% 가정 매수 억원','−1% 가정 매도 억원'],[[label,len([r for r in p['funds'] if r['kind']==kind]),len([r for r in p['funds'] if r['kind']==kind and r['coefficient'] is not None]),number(sum(r['per_1pct_krw'] for r in p['funds'] if r['kind']==kind and r['coefficient'] is not None)/1e8) if any(r['kind']==kind and r['coefficient'] is not None for r in p['funds']) else None,number(-sum(r['per_1pct_krw'] for r in p['funds'] if r['kind']==kind and r['coefficient'] is not None)/1e8) if any(r['kind']==kind and r['coefficient'] is not None for r in p['funds']) else None] for kind,label in [('spot','KOSPI200'),('futures','KOSPI200 선물지수')]]),
        dict(type='text',title='계산 설정과 범위',text='일 수익률은 KRX KOSPI200 종가의 단순 변화율, RV는 표본표준편차(ddof=1)×√252입니다. 1σ 금액은 현물·선물지수가 같은 폭으로 움직이는 시나리오입니다. 취약성 게이트=clip((종가/252일 장중고점−0.9)/0.1,0,1). 구성은 RV의252일 z÷2, RV의21일 증가율÷50%, (RSI14−50)÷30, 63거래일 수익률÷30%를 각각0~1로 제한하고40/25/20/15% 가중합니다. 모든 입력이 있어야 산출합니다. 미공개 가중치를 대체한 팀 설정이며 과거 폭락을 예측했다고 주장하지 않습니다. ETF는 KRX 기초지수·배율 분류를 사용하며 업종형·해외·코스닥·커버드콜·ETN은 제외합니다. 현재 정의 조회를 과거 시점 구성 이력으로 간주하지 않습니다. 순자산은 보고총액 우선, 없을 때 NAV×상장좌수입니다. 휴일 조정된 월간 옵션 최종거래일을 사용하며 만기 접근 자체는 감마 부호를 뜻하지 않습니다.'),
        table('출처·수집 시각',['자료','출처','수집 UTC'],[['KOSPI200 지수 1028','https://data.krx.co.kr/',p['index_retrieved_at']],['ETF 순자산','https://data.krx.co.kr/',p['aum_retrieved_at']],['ETF 공식 기초지수·배율','https://data.krx.co.kr/',p['definitions_retrieved_at']],['월간 KOSPI200 옵션 최종거래일','https://global.krx.co.kr/contents/GLB/02/0201/0201040202/GLB0201040202.jsp',p['expiry_retrieved_at']],['ETF 리밸런싱과 자금 유출입의 영향','https://www.federalreserve.gov/pubs/feds/2013/201348/index.html',None]])]
    for section in sections:
        if section['title']=='KOSPI 숏감마 · 8개 관측':section['readable']=True
        if section['title']=='취약성 구성·최근60거래일 계산 원장':section['collapsed']=True
    obj['sections']=[s for s in obj['sections'] if s.get('group')!=GROUP]+[dict(s,group=GROUP) for s in sections]
    obj['kr_shortgamma']=p
    obj['method_note']+=' 국내 숏감마 화면은 KRX 공식 KOSPI200 OHLC·ETF 배율/순자산·월간 옵션 최종거래일의8개 관측입니다. 딜러 옵션감마와 구분한 리밸런싱 민감도와 팀 취약성 설정을 표시합니다.'
    obj['missing'].append('국내 취약성의 원본 비공개 가중치·예측력과 실제 딜러 포지션은 미확인입니다. 공식 ETF 현재 정의는 역사 PIT 구성 이력이 아니며 실제 설정/환매·헤지는 리밸런싱 시나리오에 미포함입니다.')
    return p

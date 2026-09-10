"""Annual-profit recovery and the designated US/KR pair monitor, calculated locally."""
import warnings
import numpy as np
import pandas as pd
from scipy.stats import linregress
from statsmodels.tsa.stattools import coint
from .engine import number,clean_json
from .financial_modules import frame,statement_series,pct
from .store import ROOT,read_json


def settings():return read_json(ROOT/'config/strategy_screens.json')


def dated_price(p,as_of):
    p=p.loc[:as_of].dropna().sort_index()
    if not p.index.is_unique:raise ValueError('Duplicate strategy price dates')
    return p[np.isfinite(p)&(p>0)]


def spark(p):
    p=p.tail(130).iloc[::3]
    return [[str(t.date()),number(v)] for t,v in p.items()]


def pair_observation(a,b,as_of):
    p=pd.concat([dated_price(a,as_of).rename('a'),dated_price(b,as_of).rename('b')],axis=1).dropna()
    result=dict(date=str(p.index[-1].date()) if len(p) else None,observations=len(p),beta=None,corr=None,z=None,pvalue=None,signal='missing',spark=[],midrange=None,fit_start=None,z_start=None,spread_mean=None,spread_sd=None,reason='공통 252관측 미확보')
    if len(p)<252:return result
    if (pd.Timestamp(as_of)-p.index[-1]).days>7:return dict(result,reason='공통 가격이 기준일보다7일 초과 지연')
    q=np.log(p.tail(252))
    if q.b.std()<1e-10 or q.a.std()<1e-10:return dict(result,reason='회귀 가격의 변동 없음')
    fit=linregress(q.b,q.a);spread=q.a-fit.slope*q.b;tail=spread.tail(120);sd=float(tail.std(ddof=1));mean=float(tail.mean())
    z=float((tail.iloc[-1]-mean)/sd) if sd>1e-10 else None
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        pv=number(coint(q.a,q.b,trend='c',maxlag=5,autolag='aic')[1])
    points=spark(spread);values=[r[1] for r in points]
    return dict(result,beta=number(fit.slope),corr=number(p.pct_change(fill_method=None).tail(252).corr().iloc[0,1]),z=number(z),pvalue=pv,
                signal='missing' if z is None or fit.slope<=0 else 'long_a' if z<=-2 else 'short_a' if z>=2 else 'neutral',
                spark=points,midrange=number((min(values)+max(values))/2),fit_start=str(q.index[0].date()),z_start=str(tail.index[0].date()),spread_mean=number(mean),spread_sd=number(sd),
                reason='스프레드 변동 없음' if z is None else '비양수 β: 롱·숏 방향 미표시' if fit.slope<=0 else '')


def pairs(d):
    rows=[]
    for a,b,name,market in settings()['pairs']:
        r=pair_observation(d.price(a),d.price(b),d.as_of)
        rows.append(dict(r,id=a+'__'+b,a=a,b=b,name=name,market=market,source_a='https://finance.yahoo.com/quote/'+a+'/history/',source_b='https://finance.yahoo.com/quote/'+b+'/history/'))
    rows.sort(key=lambda r:(r['z'] is None,-abs(r['z'] or 0),r['id']))
    return dict(type='strategycards',kind='pairs',group='스탯아브 페어',title='미국·한국 지정13페어 · 스프레드 관찰',as_of=d.as_of,rows=rows,
                scope=dict(expected=13,available=sum(r['z'] is not None for r in rows)),
                note='분배금·분할 조정 종가의 공통252관측에서 log(A)=α+β·log(B)를 적합합니다. 선은 log(A)−β·log(B), z는 최근120관측 평균·표본표준편차(ddof=1) 기준입니다. 점선은 표시 선의 최저/최고 중간값이며 z=0선이 아닙니다. |z|≥2의 방향과 공적분 p값을 구분합니다. 현재 전체 구간의 β를 과거 진입에 사용한 성과가 아닙니다.')


def annual_rebound(annual,as_of):
    p=annual.loc[:as_of].dropna().sort_index().tail(3)
    if not p.index.is_unique:raise ValueError('Duplicate annual statement dates')
    if len(p)<3:return None
    gaps=p.index.to_series().diff().dropna().dt.days
    if not gaps.between(330,400).all() or (pd.Timestamp(as_of)-p.index[-1]).days>550:return None
    if not (p.iloc[-2]<p.iloc[-3] and p.iloc[-1]>p.iloc[-2] and p.iloc[-1]>0):return None
    return dict(annual=[[str(t.date()),number(v)] for t,v in p.items()],blackink=bool(p.iloc[-2]<0))


def recovery(annual,prices,as_of,growth=None):
    r=annual_rebound(annual,as_of);p=dated_price(prices,as_of)
    if not r or len(p)<252 or (pd.Timestamp(as_of)-p.index[-1]).days>7:return None
    window=p.tail(252);low=float(window.min());high=float(window.max());price=float(p.iloc[-1]);ma=float(p.tail(200).mean())
    off_low=(price/low-1)*100;off_high=(price/high-1)*100
    if off_low<10 or off_high>-15:return None
    above=price>ma;score=1+int(r['blackink'])+int(above)+int(growth is not None and growth>15)
    return dict(r,date=str(p.index[-1].date()),price=number(price),low=number(low),high=number(high),low_date=str(window.idxmin().date()),high_date=str(window.idxmax().date()),
                off_low=number(off_low),off_high=number(off_high),ma200=number(ma),above200=above,est_growth=growth,score=score,
                score_parts=[1,int(r['blackink']),int(above),int(growth is not None and growth>15)],spark=spark(p))


def turnaround(d):
    members={}
    for key,market in [('us_largecap','US'),('kr_largecap','KR'),('kospi200','KR')]:
        u=d.members.get(key,{})
        for m in u.get('members',[]):members[m['symbol']]=dict(m,market=market,membership_date=u.get('as_of'))
    rows=[];available=0;missing=[]
    for symbol,m in sorted(members.items()):
        raw=d.fund.get(symbol)
        if not raw:continue
        annual=statement_series(frame(raw.get('annual_income')),'NetIncome')
        if len(annual.loc[:d.as_of].dropna())<3:missing.append([symbol,'연간 순이익3개년 미확보']);continue
        available+=1;est=frame(raw.get('earnings_estimate'));info=raw.get('info',{})
        growth=pct(est.at['0y','avg'],est.at['0y','yearAgoEps']) if '0y' in est.index and {'avg','yearAgoEps'}<=set(est.columns) else None
        r=recovery(annual,d.price(symbol),d.as_of,growth)
        if not r:continue
        period=next((q.get('endDate') for q in raw.get('estimate_periods',[]) if q.get('period')=='0y'),None)
        rows.append(dict(r,id=symbol,symbol=symbol,name=m.get('name') or info.get('longName') or symbol,market=m['market'],currency=info.get('financialCurrency'),financial_retrieved_at=raw.get('retrieved_at'),membership_date=m['membership_date'],estimate_period=period,
                         source='https://finance.yahoo.com/quote/'+symbol+'/financials/'))
    rows.sort(key=lambda r:(-r['score'],-r['off_low'],r['symbol']))
    return dict(type='strategycards',kind='turnaround',group='턴어라운드',title='연간 이익 저점반등 · 가격 변곡',as_of=d.as_of,rows=rows,
                scope=dict(expected=len(members),available=available,financial_collected=sum(s in d.fund for s in members),selected=len(rows),missing=missing),
                note='공식 미국 대형주·KRX 대형주/KOSPI200 중 확보한 재무 표본을 검사합니다. 연간 순이익3개년의 가운데 해가 저점이고 최근 해가 흑자인 이익 반등에,252종가 저점 대비10% 이상·고점 대비−15% 이하의 팀 가격 조건을 적용합니다. 점수1+흑자전환1+MA200상회1+FY EPS 추정성장15%초과1이며 최대4점입니다. 기본 상위8개·전체보기와 시장필터를 제공합니다. 현재 수집 재무의 회계연도와 조회시각을 별도 표시하며 발표 당시 빈티지/투자 성과가 아닙니다.')


def views(d,obj):
    new=[turnaround(d),pairs(d)]
    obj['sections']=[new[0]]+[s for s in obj['sections'] if s.get('group') not in ['턴어라운드','스탯아브 페어']]+[new[1]]
    obj['cards']=[['연간 반등 후보',len(new[0]['rows'])],['재무 표본 / 공식 대상',str(new[0]['scope']['available'])+' / '+str(new[0]['scope']['expected'])],['지정 페어',13]]
    old='재무제표의 전년 동분기 순이익 적자→흑자 전환을 실제 분기값으로 선별합니다.'
    obj['method_note']=obj['method_note'].replace(old,'턴어라운드는 연간3개년 이익 저점반등과 가격 조건을 검사하며, 페어는 미국9쌍·한국4쌍의 지정 목록을 비교합니다.')
    gap='전략 카드: 턴어라운드 사전표본·가격 절단·점수의 정확한 원본 임계치는 미공개로 팀 기준을 표시합니다. 재무 표본 확대·발표 당시 빈티지, 공적분의 전체 가정/다중검정과 비용 후 OOS는 남아 있습니다.'
    obj['missing']=[m for m in obj['missing'] if not m.startswith('전략 카드:')]+[gap]
    return clean_json(obj)

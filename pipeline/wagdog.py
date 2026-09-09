"""Strike profiles and a transparent options-positioning diagnostic."""
import numpy as np
import pandas as pd
from .engine import *
from .events_data import read
from .option_analytics import gamma
from .pm_details import gauge,observation

def roots(x,y):
    if not np.any(np.isfinite(y)&(np.abs(y)>1e-12)):return []
    out=[]
    for i in range(len(x)-1):
        if not np.isfinite(y[i:i+2]).all():continue
        if y[i]==0:out.append(float(x[i]))
        elif y[i]*y[i+1]<0:out.append(float(x[i]-y[i]*(x[i+1]-x[i])/(y[i+1]-y[i])))
    if len(x) and np.isfinite(y[-1]) and y[-1]==0:out.append(float(x[-1]))
    return list(dict.fromkeys(out))

def profile(raw,spot,rate):
    f=pd.DataFrame(raw['records'])
    if f.empty or spot<=0:return None
    now=pd.Timestamp(raw['retrieved_at'])
    f['t']=[max(0,(pd.Timestamp(e+' 16:00',tz='America/New_York')-now).total_seconds())/(365.25*86400) for e in f.expiry]
    oi=f[(f.openInterest>0)&(f.t>0)&(f.contractSize=='REGULAR')].copy()
    f=oi[(oi.impliedVolatility>.01)&(oi.impliedVolatility<5)].copy()
    if f.empty:return None
    def gex(s):
        return gamma(s,f.strike,f.impliedVolatility,f.t,rate)*f.openInterest*100*s*s*.01*np.where(f.side=='call',1,-1)/1e9
    f['gex']=gex(spot)
    # OI includes contracts with missing IV; gamma separately excludes them.
    call=oi.loc[oi.side=='call'].groupby('strike').openInterest.sum()
    put=oi.loc[oi.side=='put'].groupby('strike').openInterest.sum()
    strike=f.groupby('strike').gex.sum();keys=sorted(set(call.index)|set(put.index))
    rows=[dict(strike=number(k),gex=number(strike.get(k)),call_oi=int(call.get(k,0)),put_oi=int(put.get(k,0)),gamma_available=k in strike.index) for k in keys if .8*spot<=k<=1.2*spot]
    grid=np.linspace(.8*spot,1.2*spot,161);values=np.array([gex(s).sum() for s in grid]);flips=roots(grid,values);flip=min(flips,key=lambda s:abs(s-spot)) if flips else None
    expiries=f[['expiry','t']].drop_duplicates().copy();expiries['distance']=(expiries.t-30/365.25).abs();chosen=expiries.sort_values('distance').iloc[0]
    near=f[f.expiry==chosen.expiry].copy();near['distance']=(near.strike-spot).abs()
    atm=near.sort_values('distance').groupby('side').head(1);iv=float(atm.impliedVolatility.mean()) if len(atm)==2 else None
    em=iv*np.sqrt(30/365.25)*100 if iv is not None else None
    return dict(symbol=raw['symbol'],spot=number(spot),retrieved_at=raw['retrieved_at'],expiries=raw['expiries'],profile=rows,
        net=number(f.gex.sum()),flip=number(flip),flips=[number(x) for x in flips],flip_distance=number((spot/flip-1)*100) if flip else None,
        call_wall=number(call.idxmax()) if len(call) else None,put_wall=number(put.idxmax()) if len(put) else None,
        put_call=number(put.sum()/call.sum()) if call.sum()>0 else None,em=number(em),em_expiry=chosen.expiry,
        em_low=number(spot*(1-em/100)) if em else None,em_high=number(spot*(1+em/100)) if em else None,
        valid_gamma=len(f),valid_oi=len(oi),contracts=len(raw['records']),curve=[dict(x=number(x),y=number(y),name=f'{x:.2f}') for x,y in zip(grid,values)],
        below=number(f.loc[f.strike<spot,'gex'].sum()),above=number(f.loc[f.strike>=spot,'gex'].sum()))

def packets(d):
    if hasattr(d,'_option_packets'):return d._option_packets
    files={p.name:p for base in d.bases for p in (base/'options').glob('*.json.gz')}
    rate=observation(d.mac('DGS3MO'))[0];result=[]
    for p in files.values():
        raw=read(p);price=d.price(raw['symbol'],False)
        if not len(price):continue
        packet=profile(raw,float(price.iloc[-1]),(rate or 0)/100)
        if raw.get('underlying_price') and abs(raw['underlying_price']/float(price.iloc[-1])-1)>.015:raise ValueError('Option and completed underlying prices differ more than 1.5%')
        if packet:packet['price_date']=str(price.index[-1].date());result.append(packet)
    d._option_packets=result
    return result

def wagdog_views(d,obj):
    items=[p for p in packets(d) if p['symbol'] in ['SPY','QQQ','IWM']]
    vix=d.price('^VIX',False);vix3=d.price('^VIX3M',False)
    aligned=pd.concat(dict(vix=vix,vix3=vix3),axis=1).dropna();term=aligned.vix/aligned.vix3
    tv=observation(term)[0];shorts=sum(p['net']<0 for p in items);longs=sum(p['net']>0 for p in items)
    interpretation='자료 부족' if len(items)<3 or tv is None else '숏감마·변동성 스트레스 동반' if shorts==3 and tv>=1 else '숏감마 우세' if shorts==3 else '롱감마·콘탱고 동반' if longs==3 and tv<1 else '지수별 혼재'
    sections=[dict(type='text',title='파생 포지셔닝 · '+interpretation,text=f'3개 ETF 중 순감마 음수 {shorts}개. VIX/VIX3M '+(f'{tv:.3f}' if tv is not None else '자료 없음')+'. 콜 OI를 +, 풋 OI를 −로 놓은 비교 규칙입니다. 실제 딜러 포지션·방향 예측이 아닙니다. 감마플립이 없으면 탐색 범위 내 교차가 없다는 뜻입니다.'),
        dict(type='gauges',title='변동성군 관측',items=[gauge('VIX',vix,'index',[10,40],[18,26],'18·26 관찰선'),
            gauge('VIX/VIX3M',term,'ratio',[.6,1.4],[.95,1],'1 이상 백워데이션'),
            gauge('SKEW',d.price('^SKEW',False),'index',[100,180],[140,145],'꼬리위험 가격 지표'),
            gauge('VVIX',d.price('^VVIX',False),'index',[60,160],[100,110],'VIX 옵션에서 산출한 VIX 변동성'),
            gauge('MOVE',d.price('^MOVE',False),'index',[40,160],[100,120],'채권 변동성 관찰선')]),
        table('지수 ETF 포지셔닝',['ETF','현물 USD','GEX USD bn/1%','감마플립 USD','현물/플립 거리 %','Put/Call OI','30D 기대폭 %'],[[p['symbol'],p['spot'],p['net'],p['flip'],p['flip_distance'],p['put_call'],p['em']] for p in items])]
    for p in items:
        sections += [dict(type='optionprofile',title=p['symbol']+' · 행사가별 부호 가정 감마',mode='gamma',**p),
            table(p['symbol']+' 핵심 가격대·비대칭',['현물','감마플립','콜 OI 최대 행사가','풋 OI 최대 행사가','30D 하단','30D 상단','현물 아래 GEX bn','현물 이상 GEX bn'],[[p['spot'],p['flip'],p['call_wall'],p['put_wall'],p['em_low'],p['em_high'],p['below'],p['above']]])]
        if p['symbol']=='SPY':sections.append(dict(type='optionprofile',title='SPY · 콜/풋 OI 상하 분포',mode='oi',**p))
    sections.append(table('옵션·기초자산 기준일과 필터',['ETF','종가일','옵션 수집 UTC','만기','계약 수','OI 유효','GEX 유효','기대폭 IV 만기'],[[p['symbol'],p['price_date'],p['retrieved_at'],', '.join(p['expiries']),p['contracts'],p['valid_oi'],p['valid_gamma'],p['em_expiry']] for p in items]))
    obj['sections'] += [dict(s,group='파생 Wag-the-Dog') for s in sections]
    obj['source']+=' · Cboe 공개 지연 옵션 호가/OI'
    obj['method_note']+=' 파생 Wag-the-Dog는 행사가 가로축·GEX 세로 막대·현물/플립/기대폭과 콜 위/풋 아래 OI 구조입니다. OI의 상하 배치는 매수·매도 방향을 뜻하지 않습니다. 30일 기대폭은30일에 가장 가까운 수집 만기의 ATM 콜/풋 IV 평균×√(30/365.25) 근사입니다. 감마는IV 유효 계약만, OI는IV 결측도 포함합니다. 전체 만기가 아닌 기존3만기 관측입니다.'

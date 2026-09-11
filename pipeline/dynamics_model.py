"""Causal price dynamics, dated monthly panels and explicit cost scenarios."""
import numpy as np
import pandas as pd
from .engine import number,clean_json,module,curve,performance
from .catalog import INDICES,DYNAMICS_STOCKS

WINDOWS=[5,10,20,40,60,90,120,180]
COSTS=[('gross','비용0 · 원형 비교',0,0),('cost5','편도5bp · 차입0%',5,0),('borrow3','편도5bp · 차입연3%',5,3),('borrow5','편도10bp · 차입연5%',10,5)]


def indicators(price,min_history=252):
    p=price.where(lambda s:s>0).sort_index();r=p.pct_change(fill_method=None)
    vol=r.rolling(21,min_periods=21).std(ddof=0);beta=r.rolling(21,min_periods=21).mean()/vol.where(vol>0)*np.sqrt(252)
    alpha=beta-beta.shift(5);tau=r.diff().abs().rolling(21,min_periods=21).std(ddof=0)/r.abs().rolling(21,min_periods=21).mean().replace(0,np.nan)
    def z(s):
        roll=s.expanding(min_history);sd=roll.std(ddof=0)
        return (s-roll.mean())/sd.where(sd>0)
    zb,za,zt=z(beta),z(alpha),z(tau);risk=100/(1+np.exp(-(zt-.5*zb-.5*za).clip(-50,50)))
    exposure=(.15/(vol*np.sqrt(252))).clip(0,1.5)*(1-.6*risk/100)
    return pd.DataFrame(dict(px=p,ret=r,vol=vol*np.sqrt(252)*100,beta=beta,alpha=alpha,tau=tau,z_beta=zb,z_alpha=za,z_tau=zt,risk=risk,exposure=exposure))


def monthly(frame):
    return frame.groupby(frame.index.to_period('M'),sort=True).tail(1)

def recent(frame,months,as_of):
    start=(pd.Timestamp(as_of).to_period('M')-(months-1)).start_time
    return frame.loc[start:as_of]


def simulate(frame,bps=0,borrow_pct=0):
    # All four scenarios start at the same uninterrupted valid suffix. Unknown
    # returns/exposures cannot silently become cash or be stitched across gaps.
    lag=frame.exposure.shift(1);valid=frame.ret.notna()&lag.notna();bad=np.flatnonzero(~valid.to_numpy())
    start=int(bad[-1]+1) if len(bad) else 1
    empty=dict(available=False,rows=[],origin=None,start=None,end=None,model={},benchmark={},chart=None,bankrupt=False)
    if start>=len(frame):return empty
    f=frame.iloc[start:];weights=lag.iloc[start:];dates=frame.index;nav=100.;bh=100.;held=0.;rows=[];bankrupt=False
    for i,(t,r,h) in enumerate(zip(f.index,f.ret,weights)):
        turnover=abs(h-held);fee=turnover*bps/10000;funding=max(h-1,0)*borrow_pct/100/252
        gross=h*r;net=gross-fee-funding;bh_ret=r-(bps/10000 if i==0 else 0)
        if net<=-1:net=-1.;bankrupt=True
        nav*=1+net;bh*=1+bh_ret
        rows.append(dict(date=str(t.date()),signal_date=str(dates[start+i-1].date()),held=held,weight=h,turnover=turnover,
          asset_return_pct=r*100,gross_return_pct=gross*100,fee_pct=fee*100,financing_pct=funding*100,
          net_return_pct=net*100,benchmark_return_pct=bh_ret*100,nav=nav,benchmark_nav=bh))
        if bankrupt:break
        held=h*(1+r)/(1+net)
    ledger=pd.DataFrame(rows).set_index('date');ledger.index=pd.to_datetime(ledger.index);origin=str(dates[start-1].date())
    navs=pd.concat([pd.DataFrame(dict(nav=[100.],benchmark_nav=[100.]),index=pd.to_datetime([origin])),monthly(ledger)[['nav','benchmark_nav']]])
    model=performance(ledger.net_return_pct/100);bench=performance(ledger.benchmark_return_pct/100)
    return dict(available=True,origin=origin,start=rows[0]['date'],end=rows[-1]['date'],sessions=len(rows),
      discarded_prefix=start,bankrupt=bankrupt,rows=clean_json(rows[-252:]),model=model,benchmark=bench,
      turnover=number(sum(r['turnover'] for r in rows)),fee_pct_sum=number(sum(r['fee_pct'] for r in rows)),financing_pct_sum=number(sum(r['financing_pct'] for r in rows)),
      chart=curve('노출 조절 vs Buy & Hold',[('노출 조절',navs.nav,'left'),('Buy & Hold',navs.benchmark_nav,'left')],'시작=100',n=len(navs)))


def prices(d,s):
    p=d.frames[s].adjusted_close.loc[:d.as_of].where(lambda p:p>0)
    calendar=d.price('^KS11' if s.endswith('.KS') or s=='^KS11' else '^GSPC').loc[:d.as_of].index
    # Do not prepend a benchmark's pre-IPO dates.
    calendar=calendar.union(p.index);calendar=calendar[(calendar>=p.index[0])&(calendar<=p.index[-1])]
    return p.reindex(calendar)


def state(risk):
    return '고위험' if risk>=70 else '경계' if risk>=57 else '중립' if risk>=45 else '안정' if risk>=32 else '강건'


def build(d):
    sections=[];definitions=[(s,n,'지수') for _,s,n in INDICES]+[(s,n,'한국 종목' if s.endswith('.KS') else '미국 종목') for s,n in DYNAMICS_STOCKS]
    for symbol,name,category in definitions:
        if symbol not in d.frames or d.frames[symbol].empty:
            sections.append(dict(type='dynamics',title=name,group=name,symbol=symbol,category=category,pending=True,reason='가격 원자료 미확보'));continue
        p=prices(d,symbol);f=indicators(p);valid=f.dropna(subset=['beta','alpha','tau','risk','exposure','px']);m=monthly(f);history=recent(monthly(valid),144,d.as_of)
        if valid.empty or (pd.Timestamp(d.as_of)-valid.index[-1]).days>7:
            sections.append(dict(type='dynamics',title=name,group=name,symbol=symbol,category=category,pending=True,reason='252개 확장창·21일 관측·분산 또는 최근 유효 신호 부족',first=str(p.index[0].date()),last=str(p.index[-1].date())));continue
        # Use the exact published monthly date for every surface column, including
        # null windows; unsupported cells are not turned into a zero-height face.
        sd=recent(m,60,d.as_of).index;surface=pd.DataFrame({w:f.ret.rolling(w,min_periods=w).std(ddof=0)*np.sqrt(252)*100 for w in WINDOWS}).reindex(sd)
        phase=recent(history,36,d.as_of);risk_history=recent(history,60,d.as_of);normalized=history.px/history.px.iloc[0]*100
        riskchart=curve('붕괴 취약성 · 최근60개월',[('취약성',risk_history.risk,'left'),('가격지수',normalized.reindex(risk_history.index),'right')],'취약성0–100','표시이력 시작=100',[65],[0,100]);riskchart['shade_above']=65
        cases=[]
        for key,label,bps,borrow in COSTS:cases.append(dict(id=key,label=label,bps=bps,borrow_pct=borrow,**simulate(f,bps,borrow)))
        baseline=cases[0];current=clean_json(valid.iloc[-1].to_dict());current['state']=state(current['risk'])
        series=[dict(date=str(t.date()),**clean_json(row.to_dict()),price_index=number(row.px/history.px.iloc[0]*100)) for t,row in history.iterrows()]
        daily=[dict(date=str(t.date()),**clean_json(row.to_dict())) for t,row in f.tail(252).iterrows()]
        sections.append(dict(type='dynamics',version=2,title=name,group=name,symbol=symbol,category=category,pending=False,
          current=current,date=str(valid.index[-1].date()),price_date=str(p.dropna().index[-1].date()),first=str(p.index[0].date()),
          price_observations=int(p.notna().sum()),missing_prices=[str(t.date()) for t in p.index[p.isna()]],
          surface=dict(windows=WINDOWS,dates=[str(t.date()) for t in sd],values=clean_json(surface.values.tolist()),playback=True),
          phase=[dict(x=number(row.beta),y=number(row.tau),value=number(row.risk),name=str(t.date())) for t,row in phase.iterrows()],
          series=series,daily=daily,charts=[riskchart,baseline['chart']],cost_cases=cases,
          stats=[dict(name='노출 조절',**baseline['model']),dict(name='Buy & Hold',**baseline['benchmark'])],
          note='21일·5일 변화·최소252개 확장창. 취약성은 확률이 아닙니다. 표면60개월×8기간·위상36개월·위험60개월이며 월내 마지막 실제 관측일을 표시합니다. 성과는 전일 신호를 적용한 마지막 연속 유효 구간만 비교합니다.'))
    index_cards=[(s['title']+' 취약성',s['current']['risk']) for s in sections if s['category']=='지수' and not s['pending']]
    obj=module('dynamics',d.as_of,'가격만으로 β·α·∇τ·확장창z·취약성·목표노출을 계산합니다. 전일 신호, 결측 시점, 드리프트 후 거래량과 명시적 비용 가정을 분리합니다. 지수의 노출/성과는 실제 매매상품이 아닌 가상 비교입니다.',sections,index_cards+[('관측 대상',sum(not s['pending'] for s in sections))],
      missing=['원본 확장창 최소표본·0분산 세부 처리/가격정정 빈티지 동등성은 미검증입니다. 팀 설정과 실제 가용 이력을 표시합니다.','비용은 사용자가 선택하는 가정이며 실제 스프레드·차입조건·시장충격·현금이자·세금과 과거 실시간 데이터 빈티지를 재현하지 않습니다.','결측 이후 연속 유효 구간만 성과를 비교합니다. 일부 종목은 전체22년 이력이 없으며 과거 월말 신호가 당시 발표된 투자판단이라는 보증은 없습니다.'])
    obj['contract']=dict(version=2,vol_window=21,alpha_lag=5,z_minimum=252,ddof=0,annual_sessions=252,
       signal_lag=1,target_volatility=.15,max_exposure=1.5,gate=.6,history_months=144,phase_months=36,surface_months=60,risk_months=60,
       source_vintage=getattr(d,'vintage',None),cost_cases=[dict(id=k,label=l,bps=b,borrow_pct=r) for k,l,b,r in COSTS])
    return obj

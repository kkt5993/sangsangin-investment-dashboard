"""Independent implementation of the publicly described five reflexivity rules.

This is a diagnostic, not an estimate of a structural Soros feedback parameter.
"""
import numpy as np
import pandas as pd
from .engine import *
from .financial_modules import frame,statement_series
from .pm_details import gauge,observation

AXES=[('cognition','인지게인','AR1'),('acceleration','초지수성','%p/year²'),
      ('fragility','취약성','합성 z'),('herding','허딩','−t(γ₂)'),('volatility','변동성','연율 %')]

def ols(y,x):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if len(y)<=x.shape[1] or np.linalg.matrix_rank(x)<x.shape[1]:return None,None
    beta=np.linalg.lstsq(x,y,rcond=None)[0];resid=y-x@beta
    se=np.sqrt(np.maximum(0,np.diag(np.linalg.inv(x.T@x))*float(resid@resid)/(len(y)-x.shape[1])))
    return beta,np.divide(beta,se,out=np.full_like(beta,np.nan),where=se>1e-12)

def acceleration(prices,window=250):
    p=prices.where(prices>0).dropna();x=np.arange(window)/252;x=x-x.mean();design=np.column_stack([np.ones(window),x,x*x])
    pinv=np.linalg.pinv(design);inv=np.linalg.inv(design.T@design)
    if len(p)<window:return pd.DataFrame(columns=['acceleration','tstat'],dtype=float)
    windows=np.lib.stride_tricks.sliding_window_view(np.log(p.to_numpy()),window)
    beta=windows@pinv.T;resid=windows-beta@design.T;se=np.sqrt((resid*resid).sum(axis=1)/(window-3)*inv[2,2])
    t=np.divide(beta[:,2],se,out=np.full(len(beta),np.nan),where=se>1e-12)
    return pd.DataFrame(dict(acceleration=beta[:,2]*200,tstat=t),index=p.index[window-1:])

def rolling_percentile(s,n):
    return s.rolling(n,min_periods=n).rank(pct=True)*100

def rolling_ar1(s,n):
    def ar1(a):
        x=a[:-1];y=a[1:]
        return np.corrcoef(x,y)[0,1] if x.std()>0 and y.std()>0 else np.nan
    return s.rolling(n,min_periods=n).apply(ar1,raw=True)

def herding_universe(d,market):
    key='us_largecap' if market=='US' else 'kr_largecap';limit=70 if market=='US' else 60
    rows=d.members.get(key,{}).get('members',[])
    def cap(m):return m.get('market_cap') or d.fund.get(m['symbol'],{}).get('info',{}).get('marketCap') or 0
    return [m['symbol'] for m in sorted(rows,key=lambda m:(-cap(m),m['symbol'])) if m['symbol'] in d.frames][:limit]

def csad_regression(returns,benchmark,window=120):
    # Require at least 85% of the explicitly selected cross section every day.
    r=returns.reindex(benchmark.index);required=int(np.ceil(len(r.columns)*.85))
    csad=r.sub(benchmark,axis=0).abs().mean(axis=1).where(r.notna().sum(axis=1)>=required)
    f=pd.concat(dict(csad=csad,market=benchmark),axis=1).dropna();rows=[]
    for i in range(window-1,len(f)):
        w=f.iloc[i-window+1:i+1];b,t=ols(w.csad,np.column_stack([np.ones(window),w.market.abs(),w.market*w.market]))
        if b is not None:rows.append([f.index[i],b[2],t[2],int(r.loc[w.index].notna().sum(axis=1).min())])
    out=pd.DataFrame(rows,columns=['date','gamma2','tstat','minimum_names']).set_index('date')
    return out,csad

def champion(d,symbol,name):
    raw=d.fund.get(symbol,{});q=statement_series(frame(raw.get('quarterly_income')),'NetIncome');growth=None;period=None;ni=None;prior=None
    if len(q):
        period=q.index[-1];ni=q.iloc[-1];previous=q.loc[period-pd.DateOffset(years=1)-pd.Timedelta(days=10):period-pd.DateOffset(years=1)+pd.Timedelta(days=10)]
        if len(previous):
            prior=previous.iloc[-1]
            if prior>0:growth=number((ni/prior-1)*100)
    price=ret(d.price(symbol),252)
    mode='자료 부족'
    if growth is not None and price is not None:
        mode='가격 상승·이익 감소' if price>0 and growth<0 else '멀티플 확장 우세' if price>max(growth,0) else '이익 동행 또는 가격 조정'
    return dict(symbol=symbol,name=name,price12=price,ni_yoy=growth,period=str(period.date()) if period is not None else None,mode=mode,source_date=raw.get('retrieved_at','')[:10])

def reflex_views(d,obj):
    sections=[];statistics={};herds={};histories={};universe={}
    for market,index,name in [('KR','^KS11','KOSPI'),('US','^GSPC','S&P500')]:
        symbols=herding_universe(d,market);universe[market]=symbols
        prices=pd.concat({s:d.price(s) for s in symbols},axis=1)
        herds[market],_=csad_regression(prices.pct_change(fill_method=None),d.price(index,False).pct_change(fill_method=None))
    for symbol,name,market in [('^KS11','KOSPI','KR'),('^GSPC','S&P500','US'),('^IXIC','Nasdaq','US')]:
        p=d.price(symbol,False);r=p.pct_change(fill_method=None);acc=acceleration(p)
        weekly=p.resample('W-FRI').last();weekly=weekly.loc[:p.index[-1]];wr=weekly.pct_change(fill_method=None)
        cog=rolling_ar1(wr,26);ar=rolling_ar1(r,60);var=r.rolling(60).var(ddof=1)
        ar_pct=rolling_percentile(ar,504);var_pct=rolling_percentile(var,504)
        fragility=(zscore(ar,504)+zscore(var,504))/2;vol=np.sqrt(var*252)*100
        herd=herds[market];lastacc=acc.iloc[-1];lastcog=observation(cog)[0]
        statistics[name]=dict(acceleration=number(lastacc.acceleration),accel_t=number(lastacc.tstat),cognition=lastcog,cog_pct=observation(rolling_percentile(cog,156))[0],
            csd_ar_pct=observation(ar_pct)[0],csd_var_pct=observation(var_pct)[0],volatility=observation(vol)[0],date=str(p.index[-1].date()))
        ss={'cognition':cog,'acceleration':acc.acceleration,'fragility':fragility,'herding':-herd.tstat,'volatility':vol}
        # Display z is a descriptive standardization of 36 monthly snapshots;
        # it is never passed to a predictive backtest or the diagnostic score.
        dates=observed_resample(p).tail(36).index
        raw=pd.DataFrame({k:s.reindex(dates,method='ffill') for k,s in ss.items()},index=dates)
        zz=(raw-raw.mean())/raw.std(ddof=0).replace(0,np.nan)
        rows=[dict(date=str(t.date()),raw={k:number(raw.at[t,k]) for k in raw},z={k:number(zz.at[t,k]) for k in zz}) for t in dates]
        histories[name]=dict(type='hologram',title=name+' · 재귀성 36개월 상태',axes=[dict(key=k,name=n,unit=u) for k,n,u in AXES],rows=rows)
    champs=[champion(d,s,n) for s,n in [('NVDA','NVIDIA'),('MSFT','Microsoft'),('005930.KS','삼성전자'),('000660.KS','SK하이닉스')]]
    scored=[statistics[k] for k in ['KOSPI','Nasdaq']]
    pts1=sum(a['acceleration']>0 and a['accel_t'] is not None and a['accel_t']>2 for a in scored)
    mx=max(a['cognition'] for a in scored);pts2=2 if mx>=.30 else 1 if mx>=.15 else 0
    pts3=sum(len(h)>0 and h.gamma2.iloc[-1]<0 and h.tstat.iloc[-1]<-1.64 for h in herds.values())
    pts4=2 if any(a['mode']=='가격 상승·이익 감소' for a in champs) else 1 if sum(a['mode']=='멀티플 확장 우세' for a in champs)>=2 else 0
    if any(a['mode']=='자료 부족' for a in champs) and pts4<2:pts4=None
    pts5=sum(a['csd_ar_pct'] is not None and a['csd_var_pct'] is not None and a['csd_ar_pct']>=80 and a['csd_var_pct']>=80 for a in scored)
    parts=[('초지수성',pts1,'KOSPI·Nasdaq 각각: 250일 lnP 2차항>0 그리고 t>2이면1점'),
           ('인지 게인',pts2,'두 지수의 최대26주 AR1: 0.15 이상1점, 0.30 이상2점'),
           ('CSAD 군집',pts3,'US·KR 각각: 120일 γ₂<0 그리고 t<−1.64이면1점'),
           ('가격·이익 괴리',pts4,'가격↑·최근분기 NI YoY↓ 기업1개 이상2점, 가격상승이 이익성장보다 큰 기업2개 이상1점'),
           ('임계감속',pts5,'지수별60일 AR1·분산이 각각504일 분포 P80 이상이면1점')]
    total=sum(p for _,p,_ in parts if p is not None);complete=all(p is not None for _,p,_ in parts)
    stage='자료 부족 · 합계 미확정' if not complete else '잠복' if total<=2 else '자기강화' if total<=5 else '과열·괴리' if total<=7 else '임계'
    sections += [dict(type='gauges',title='재귀성 진단 · '+stage,items=[dict(name='5개 기둥 합계',value=total if complete else None,date=d.as_of,unit='/10',min=0,max=10,cuts=[3,6,8],level=(0 if total<=2 else 1 if total<=5 else 2 if total<=7 else 3) if complete else None,rule='예측 확률이나 붕괴 시점이 아닌 공개 규칙 기반 진단')]),
        table('점수 판정 근거',['기둥','점수 /2','왜 이 점수인가'],[[n,p,r] for n,p,r in parts]),
        dict(type='text',title='펀더멘털 → 인식·가격 → 펀더멘털',text='5개 기둥은 가격의 자기강화와 이익의 동행 여부를 따로 측정합니다. 합계는 실제 구조방정식의 피드백 계수나 확률 추정값이 아닙니다.')]
    sections+=list(histories.values())
    sections.append(table('지수별 입력과 관측일',['지수','가격일','가속 %p/년²','2차항 t','주간 AR1','AR1 3Y 백분위','일간 AR1 P','일간 분산 P'],[[n,a['date'],a['acceleration'],a['accel_t'],a['cognition'],a['cog_pct'],a['csd_ar_pct'],a['csd_var_pct']] for n,a in statistics.items()]))
    for name in ['KOSPI','Nasdaq']:
        a=statistics[name]
        sections.append(dict(type='gauges',title=name+' · 기둥별 계기판',items=[
            gauge('로그가격 가속',pd.Series([a['acceleration']],index=[pd.Timestamp(a['date'])]),'%p/year²',[-100,300],[0,50,100],'가속>0 및 t>2가 점수 조건'),
            gauge('인지 게인',pd.Series([a['cognition']],index=[pd.Timestamp(a['date'])]),'AR1',[-.4,.6],[0,.15,.30],'26주 수익률 자기상관'),
            gauge('CSD 자기상관 위치',pd.Series([a['csd_ar_pct']],index=[pd.Timestamp(a['date'])]),'P',[0,100],[50,80],'분산도 P80 이상일 때만 동시 신호'),
            gauge('CSD 분산 위치',pd.Series([a['csd_var_pct']],index=[pd.Timestamp(a['date'])]),'P',[0,100],[50,80],'60일 분산의504관측 분포')]))
    sections.append(table('CSAD 회귀 · 최근120일',['시장','대상 수','최소 유효 수','γ₂','t 통계','관측일'],[[m,len(universe[m]),int(h.minimum_names.iloc[-1]),number(h.gamma2.iloc[-1]),number(h.tstat.iloc[-1]),str(h.index[-1].date())] for m,h in herds.items() if len(h)]))
    sections.append(table('대표 기업 가격·최근분기 이익',['종목','12M 주가 %','NI YoY %','결산일','판정','재무 수집일'],[[a['name'],a['price12'],a['ni_yoy'],a['period'],a['mode'],a['source_date']] for a in champs]))
    sections.append(table('군집 표본 원장',['시장','종목'],[[m,s] for m,symbols in universe.items() for s in symbols]))
    obj['sections'] += [dict(s,group='Soros 재귀성') for s in sections]
    obj['reflex_contract']=dict(score=total if complete else None,parts=[dict(name=n,points=p) for n,p,_ in parts],universe=universe,statistics=statistics)
    obj['method_note']+=' 재귀성은 공개된250일 2차 로그가격·26주 AR1·120일 CSAD·최근분기 NI·60일 CSD 규칙을 독립 계산합니다. 홀로그램은36개월 5축(x인지·깊이초지수·높이취약성·색군집·크기변동성)과4시점 레이더입니다. 군집 표본은 현재 공식 대형주 중 확보한 시총 우선 US70/KR60이며 역사 구성종목이 아닙니다.'
    obj['missing']=[m for m in obj['missing'] if 'Soros' not in m]
    obj['missing'].append('재귀성 원본의 정확한 표본70/60과 회귀 오차 보정 방식은 미공개입니다. 팀 OLS 표준오차·252일 연율을 사용합니다. 과거 군집 입력이 부족한 월은 회색/빈칸으로 표시합니다. 종목별 P/E는 지수 전체의 역사 밸류에이션을 대체하지 않습니다.')
    obj['missing'].append('거시 지표의 미래 발표 달력과 과거 발표 당시 빈티지별 국면은 추가 연결 대상입니다.')

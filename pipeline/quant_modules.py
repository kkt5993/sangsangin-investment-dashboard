"""Five price-based research screens. Screens are not execution instructions."""
import numpy as np
import pandas as pd
from scipy.stats import linregress
from statsmodels.tsa.stattools import coint
from .engine import *
from .catalog import MULTI

def hurst(s):
    a=np.asarray(s.dropna());lags=np.arange(2,21);v=np.array([np.std(a[n:]-a[:-n]) for n in lags]);ok=v>0
    return number(np.polyfit(np.log(lags[ok]),np.log(v[ok]),1)[0]) if ok.sum()>10 else None

def quant(d):
    members=d.members.get('kr_screen',{}).get('members',[]);rows=[];prices={}
    sector={m['symbol']:m['sector'] for m in d.members.get('kr_sectors',{}).get('members',[])}
    benchmark=d.price('^KS11');br=benchmark.pct_change()
    for m in members:
        s=m['symbol'];a=d.stats(s);p=d.price(s);f=d.frames.get(s)
        if not a or 'volume' not in f:continue
        r=p.pct_change();aligned=pd.concat(dict(a=r,b=br),axis=1).dropna().tail(252)
        if len(aligned)<220:continue
        mom=(p.iloc[-22]/p.iloc[-253]-1)*100;eff=abs(p.iloc[-1]-p.iloc[-127])/p.diff().abs().iloc[-126:].sum()
        monthly=p.resample('ME').last().pct_change().iloc[-12:];reversal=last5=(r.rolling(5).sum().iloc[-1]-r.rolling(5).sum().iloc[-252:].mean())/r.rolling(5).sum().iloc[-252:].std(ddof=0)
        a.update(name=m['name'],sector=sector.get(s,'미분류'),mom12_1=number(mom),eff=number(eff),beta=number(aligned.a.cov(aligned.b)/aligned.b.var()),reversal_z=number(reversal),max_daily=number(r.iloc[-252:].max()*100),stability=number(-monthly.std()),vol_improvement=a['volume_ratio'])
        a['excluded']=a['vol']>90 or a['max_daily']>15 or mom>300 or a['r1m']< -25
        rows.append(a);prices[s]=p
    sections=[]
    names={a['symbol']:a['name'] for a in rows}
    # Limit expensive pair tests to the 160 most liquid stocks; preserve this universe in the output.
    liquid=sorted(prices,key=lambda s:(d.frames[s].close*d.frames[s].volume).tail(63).mean(),reverse=True)[:160]
    p=pd.concat({s:prices[s] for s in liquid},axis=1).tail(505);returns=p.pct_change(fill_method=None);corr=returns.corr(min_periods=450)
    candidates=[]
    for i,a in enumerate(liquid):
        for b in liquid[i+1:]:
            cc=corr.at[a,b]
            if not .5<=cc<=.95:continue
            f=p[[a,b]].dropna()
            if len(f)<450:continue
            log=np.log(f);fit=linregress(log[b],log[a]);spread=log[a]-fit.intercept-fit.slope*log[b];h=hurst(spread)
            if h is None or h>=.5:continue
            candidates.append((h,a,b,cc,spread,fit.slope,log))
    pairs=[]
    for h,a,b,cc,spread,hedge,log in sorted(candidates,key=lambda v:v[0])[:60]:
        pv=float(coint(log[a],log[b],maxlag=5,autolag='aic')[1])
        if pv>.05:continue
        slope=linregress(spread.shift(1).dropna(),spread.diff().dropna()).slope
        phi=1+slope;half=-np.log(2)/np.log(phi) if 0<phi<1 else np.nan;z=zscore(spread,252);zlast=number(z.iloc[-1])
        pairs.append(dict(a=a,b=b,name=names[a]+' / '+names[b],hurst=h,corr=number(cc),pvalue=number(pv),half=number(half),hedge=number(hedge),z=zlast))
        c=curve(names[a]+' / '+names[b], [('스프레드 z',z.tail(252),'left')],'z-score',guides=[-2,0,2]);c['group']='Stat Arb';sections.append(c)
        if len(pairs)==10:break
    sections.insert(0,dict(table('페어 스크리닝',['페어','z','Hurst','반감기 일','수익률 상관','공적분 p'],[[a['name'],a['z'],a['hurst'],a['half'],a['corr'],a['pvalue']] for a in pairs]),group='Stat Arb'))
    good=[a for a in rows if not a['excluded']]
    features=[('mom12_1',.20,1),('r3m',.10,1),('eff',.15,1),('high52',.10,1),('r1w',.10,-1),('vol',.15,-1),('stability',.15,1),('vol_improvement',.05,1)]
    df=pd.DataFrame(good)
    if len(df):
        score=pd.Series(0.,index=df.index)
        for key,w,sign in features:
            col=pd.to_numeric(df[key],errors='coerce');std=col.std(ddof=0);z=((col-col.mean())/std).clip(-2.5,2.5) if std>0 else col*0
            score+=z.fillna(0)*sign*w
        for i,a in enumerate(good):a['factor']=number(score.iloc[i])
        factor=sorted(good,key=lambda a:a['factor'],reverse=True)[:30]
        sections.append(dict(table('8팩터 상위 30',['종목','점수','12-1M %','3M %','효율','52주 고점 %','변동성 %'],[[a['name'],a['factor'],a['mom12_1'],a['r3m'],a['eff'],a['high52'],a['vol']] for a in factor]),group='멀티팩터'))
        sections.append(dict(bars('팩터 점수',[(a['name'],a['factor']) for a in factor],''),group='멀티팩터'))
        eligible=sorted([a for a in rows if a['beta'] is not None and a['beta']>.05],key=lambda a:a['beta']);q=max(1,len(eligible)//5)
        low=[a for a in eligible[:q] if a['r1y']>0];high=eligible[-q:]
        for label,leg,sign in [('저베타 LONG',low,1),('고베타 SHORT',high,-1)]:
            legbeta=np.mean([a['beta'] for a in leg]) if leg else 1
            sections.append(dict(table(label,['종목','Beta 1Y','12M %','비중 %'],[[a['name'],a['beta'],a['r1y'],number(sign*100/len(leg)/legbeta)] for a in leg]),group='BAB'))
        reversal=[a for a in rows if (a['mom12_1']>20 and a['reversal_z']< -1.2) or (a['mom12_1']< -20 and a['reversal_z']>1.2)]
        sections.append(dict(table('추세 조건부 단기반전',['종목','방향','12-1M %','5D z','1W %'],[[a['name'],'LONG' if a['mom12_1']>0 else 'SHORT',a['mom12_1'],a['reversal_z'],a['r1w']] for a in sorted(reversal,key=lambda a:abs(a['reversal_z']),reverse=True)[:30]]),group='단기반전'))
    ts=[]
    for s,n,g in MULTI[:12]:
        a=d.stats(s)
        if not a:continue
        sign=np.sign(a['r1y']) if np.sign(a['r1y'])==np.sign(a['r3m']) else 0
        ts.append([n,'LONG' if sign>0 else 'SHORT' if sign<0 else 'FLAT',a['r1y'],a['r3m'],a['vol'],number(sign*min(2,10/a['vol'])) if a['vol'] else None])
    sections.append(dict(table('시계열 모멘텀',['자산','방향','12M %','3M %','변동성 %','10% 목표 노출'],ts),group='TSMOM'))
    return module('quant',d.as_of,'Naver 시가총액 KOSPI 상위 300·KOSDAQ 상위 150에서 우선주·SPAC·REIT를 제외합니다. 팩터는 8개 z-score(±2.5 제한) 가중합. BAB는 1년 KOSPI beta, TSMOM은 12M·3M 일치 및 변동성 10% 타게팅입니다. Stat Arb는 거래대금 상위 160 내 Hurst<0.5·Engle–Granger p<0.05로 선별합니다.',sections,
        [('유니버스',len(members)),('관측 가능',len(rows)),('팩터 통과',len(good)),('페어',len(pairs))],
        missing=['현재 유니버스의 스크리닝이며 역사 구성종목을 복원한 성과 검증이 아닙니다. 공적분 p값은 다중검정 보정 전이고 전체 구간 추정 헤지비율은 진입 시점 백테스트에 사용할 수 없습니다.'])

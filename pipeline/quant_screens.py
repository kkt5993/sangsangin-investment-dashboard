"""Offline price-ratio, factor, beta and trend screens with calculation ledgers."""
import numpy as np
import pandas as pd
from scipy.stats import linregress
from .engine import number, module, table, bars, curve, zscore, clean_json

FEATURES=[('mom12_1','12−1M 모멘텀',.20,1),('r3m','3M 모멘텀',.10,1),('eff','6M 경로효율',.15,1),('high52','52주 고점근접',.10,1),('r1w','5D 역추세',.10,-1),('vol','저변동성',.15,-1),('stability','월수익 안정성',.15,1),('vol_improvement','거래량 개선',.05,1)]
ASSETS=[('^KS11','KOSPI','지수',True),('^KQ11','KOSDAQ','지수',True),('^GSPC','S&P500','지수',True),('^IXIC','NASDAQ 종합','지수',True),('^N225','닛케이225','지수',True),('^TNX','미국10년 금리','금리수준',True),('GLD','금 ETF','ETF',False),('CL=F','WTI 선물','연속선물',False),('HG=F','구리 선물','연속선물',False),('DX-Y.NYB','달러지수','환지수',False),('KRW=X','원/달러','환율',False),('BTC-USD','비트코인','현물',False)]


def hurst(s):
    # Finite lagged differences retain gaps; never compress the time axis.
    a=np.asarray(s,dtype=float);lags=np.arange(2,21);v=[]
    for n in lags:
        diff=a[n:]-a[:-n];diff=diff[np.isfinite(diff)]
        v.append(np.std(diff) if len(diff)>=30 else np.nan)
    v=np.asarray(v);ok=np.isfinite(v)&(v>0)
    return number(np.polyfit(np.log(lags[ok]),np.log(v[ok]),1)[0]) if ok.sum()>10 else None


def pair_metrics(a,b):
    f=pd.concat(dict(a=a,b=b),axis=1).where(lambda x:x>0).tail(505)
    common=f.pct_change(fill_method=None).dropna()
    if len(common)<450 or f.iloc[-1].isna().any():return None
    corr=number(common.a.corr(common.b))
    if corr is None or not .5<=corr<=.95:return None
    ratio=f.a/f.b;h=hurst(ratio)
    if h is None or h>=.5:return None
    z=zscore(ratio,252,min_periods=220);last=number(z.iloc[-1])
    if last is None:return None
    lag=pd.concat(dict(x=ratio.shift(1),y=ratio.diff()),axis=1).dropna()
    slope=linregress(lag.x,lag.y).slope if lag.x.std()>0 else np.nan
    phi=1+slope;half=-np.log(2)/np.log(phi) if 0<phi<1 else np.nan
    return dict(hurst=h,corr=corr,half=number(half),phi=number(phi),z=last,
      state='진입 조건' if abs(last)>=2 else '대기' if abs(last)>=1 else '수렴권',long_leg='a' if last<0 else 'b' if last>0 else None,
      start=str(common.index[0].date()),end=str(f.index[-1].date()),observations=len(common),ratio=number(ratio.iloc[-1]),mean=number(ratio.tail(252).mean()),std=number(ratio.tail(252).std(ddof=0)),ratio_exact=repr(float(ratio.iloc[-1])),mean_exact=repr(float(ratio.tail(252).mean())),std_exact=repr(float(ratio.tail(252).std(ddof=0))),curve=z.tail(252))


def stock_metrics(d,m,calendar):
    s=m['symbol'];frame=d.frames.get(s);p=d.price(s).loc[:d.as_of]
    row=dict(symbol=s,name=m['name'],date=str(p.index[-1].date()) if len(p) else None,excluded=[],factor=None,components=[])
    if frame is None or 'volume' not in frame or len(p)<253:row['excluded']=['가격253개 또는 거래량 미확보'];return row
    if (pd.Timestamp(d.as_of)-p.index[-1]).days>7 or p.index[-1]<calendar[-1]:row['excluded']=['최근 시장일 가격 미확보'];return row
    p=p.reindex(calendar);r=p.pct_change(fill_method=None)
    if p.tail(127).isna().any() or p.tail(253).notna().sum()<220 or pd.isna(p.iloc[-253]):row['excluded']=['최근127시장일 또는12M 기준가격 결측'];return row
    br=d.price('^KS11').loc[:d.as_of].reindex(calendar).pct_change(fill_method=None)
    aligned=pd.concat(dict(a=r,b=br),axis=1).tail(252).dropna()
    beta=aligned.a.cov(aligned.b)/aligned.b.var() if len(aligned)>=220 and aligned.b.var()>0 else np.nan
    pct=lambda n:100*(p.iloc[-1]/p.iloc[-n-1]-1)
    mom=100*(p.iloc[-22]/p.iloc[-253]-1);path=p.diff().abs().tail(126).sum()
    end=pd.Timestamp(d.as_of).replace(day=1)-pd.Timedelta(days=1)
    monthly=p.loc[:end].resample('ME').last().pct_change(fill_method=None).tail(12)
    five=p.pct_change(5,fill_method=None)*100;rz=zscore(five,252,min_periods=220)
    volume=frame.volume.reindex(calendar);vbase=volume.tail(63)
    vr=volume.tail(5).mean()/vbase.mean() if vbase.notna().all() and vbase.mean()>0 else np.nan
    row.update(date=str(calendar[-1].date()),price=number(p.iloc[-1]),price_observations=int(p.tail(253).notna().sum()),return_observations=int(r.tail(252).notna().sum()),missing_dates=[str(t.date()) for t in p.tail(253).index[p.tail(253).isna()]],mom12_1=number(mom),r3m=number(pct(63)),r1y=number(pct(252)),r1m=number(pct(21)),r1w=number(pct(5)),eff=number(abs(p.iloc[-1]-p.iloc[-127])/path) if path>0 else None,high52=number(100*(p.iloc[-1]/p.tail(252).max()-1)),vol=number(r.tail(252).std(ddof=1)*np.sqrt(252)*100),max_daily=number(r.tail(252).max()*100),stability=number(-monthly.std(ddof=1)*100) if monthly.notna().sum()==12 else None,vol_improvement=number(vr),beta=number(beta),beta_start=str(aligned.index[0].date()) if len(aligned) else None,beta_end=str(aligned.index[-1].date()) if len(aligned) else None,beta_observations=len(aligned),reversal_z=number(rz.iloc[-1]))
    for key,limit,op,label in [('vol',90,lambda x,y:x>y,'연변동성>90%'),('max_daily',15,lambda x,y:x>y,'일간MAX>15%'),('mom12_1',300,lambda x,y:x>y,'12−1M>300%'),('r1m',-25,lambda x,y:x<y,'1M<−25%')]:
        if row[key] is not None and op(row[key],limit):row['excluded'].append(label)
    missing=[label for key,label,_,_ in FEATURES if row[key] is None]
    if missing:row['excluded'].append('팩터 결측: '+', '.join(missing))
    return row


def factor_scores(rows):
    good=[r for r in rows if not r['excluded']]
    for row in rows:row['factor']=None;row['components']=[]
    for key,label,weight,sign in FEATURES:
        values=np.array([r[key] for r in good]);mean=float(values.mean()) if len(values) else 0.;std=float(values.std()) if len(values) else 0.
        for row in good:
            z=float(np.clip((row[key]-mean)/std,-2.5,2.5)) if std>0 else 0.
            row['components'].append(dict(key=key,name=label,raw=row[key],mean=number(mean),std=number(std),mean_exact=repr(mean),std_exact=repr(std),z=number(z),weight=weight,sign=sign,contribution=number(z*weight*sign)))
    for row in good:row['factor']=number(sum(c['contribution'] for c in row['components']))
    return sorted(good,key=lambda r:(-r['factor'],r['symbol']))


def bab_legs(rows):
    eligible=sorted([r for r in rows if r.get('beta') is not None and r['beta']>.05],key=lambda r:(r['beta'],r['symbol']));q=len(eligible)//5
    low=[r for r in eligible[:q] if r['r1y']>0];high=list(reversed(eligible[-q:])) if q else [];legs=[]
    for label,values,sign in [('LONG',low,1),('SHORT',high,-1)]:
        mean=float(np.mean([r['beta'] for r in values])) if values else None
        rr=[dict(symbol=r['symbol'],name=r['name'],beta=r['beta'],r1y=r['r1y'],date=r['date'],beta_end=r.get('beta_end'),beta_observations=r.get('beta_observations'),weight=number(sign*100/len(values)/mean)) for r in values]
        legs.append(dict(side=label,rows=rr,mean_beta=number(mean),count=len(values),beta_exposure=number(sum(r['weight']/100*r['beta'] for r in rr)) if rr else None,gross=number(sum(abs(r['weight']) for r in rr)),available=bool(rr)))
    return dict(eligible=len(eligible),quintile=q,legs=legs,complete=all(l['available'] for l in legs),net_beta=number(sum(l['beta_exposure'] for l in legs)) if all(l['available'] for l in legs) else None)


def tsmom(d):
    rows=[]
    for symbol,name,kind,matched in ASSETS:
        p=d.price(symbol).loc[:d.as_of];r=p.pct_change(fill_method=None);periods=365 if symbol=='BTC-USD' else 252
        def change(months):
            if not len(p):return None,None
            target=p.index[-1]-pd.DateOffset(months=months);base=p.loc[:target]
            if not len(base) or (target-base.index[-1]).days>7:return None,None
            return number((p.iloc[-1]/base.iloc[-1]-1)*100),str(base.index[-1].date())
        m12,start12=change(12);m3,start3=change(3)
        vol=number(r.tail(periods).std(ddof=1)*np.sqrt(periods)*100) if len(p)>periods else None
        available=len(p)>periods and m12 is not None and m3 is not None and vol is not None and vol>0 and (pd.Timestamp(d.as_of)-p.index[-1]).days<=7
        sign=int(np.sign(m12)) if available and m12 is not None and m3 is not None and np.sign(m12)==np.sign(m3) else 0
        exposure=number(sign*min(2,10/vol)) if available and vol and kind!='금리수준' else None
        rows.append(dict(symbol=symbol,name=name,kind=kind,reference_named=matched,available=available,start12=start12,start3=start3,annual_sessions=periods,date=str(p.index[-1].date()) if len(p) else None,r1y=m12,r3m=m3,vol=vol,direction=('금리 상승' if sign>0 else '금리 하락' if sign<0 else '혼조') if kind=='금리수준' else 'LONG' if sign>0 else 'SHORT' if sign<0 else 'FLAT',exposure=exposure,signal=sign))
    return rows


def ledger(title,group,columns,rows,detail=None):
    return dict(type='quantledger',title=title,group=group,columns=columns,rows=rows,detail=detail or [],note='종목·코드·조건 검색과 계산 근거를 제공합니다. 현재 관측값이며 비용 후 순성과가 아닙니다.')


def quant(d):
    members=d.members.get('kr_screen',{}).get('members',[]);index=d.price('^KS11').loc[:d.as_of].index
    for m in members:index=index.union(d.price(m['symbol']).loc[:d.as_of].index)
    calendar=index.sort_values();rows=[stock_metrics(d,m,calendar) for m in members] if len(calendar) else [];good=factor_scores(rows);names={r['symbol']:r['name'] for r in rows};pairs=[];sections=[]
    ready=sorted(r['symbol'] for r in rows if r.get('price') is not None)
    price=pd.concat({s:d.price(s).loc[:d.as_of].reindex(calendar) for s in ready},axis=1).tail(505) if ready else pd.DataFrame()
    correlation=price.pct_change(fill_method=None).corr(min_periods=450);screened=0;arrays={s:price[s].to_numpy() for s in ready}
    for i,a in enumerate(ready):
        for b in ready[i+1:]:
            if not .5<=correlation.at[a,b]<=.95:continue
            screened+=1;h=hurst(arrays[a]/arrays[b])
            if h is not None and h<.5:pairs.append(dict(a=a,b=b,hurst=h))
    pairs.sort(key=lambda r:(r['hurst'],r['a'],r['b']));selected=[]
    for candidate in pairs:
        a,b=candidate['a'],candidate['b'];result=pair_metrics(price[a],price[b])
        if result:selected.append(dict(a=a,b=b,name=names[a]+' / '+names[b],**result))
        if len(selected)==10:break
    for r in selected:
        r['long']=names[r[r['long_leg']]] if r['long_leg'] else None;r['short']=names[r['b' if r['long_leg']=='a' else 'a']] if r['long_leg'] else None
    sections.append(ledger('가격비 평균회귀 페어 · Hurst 순 상위10','Stat Arb',['페어','A / B 코드','관측일','조건','Long 후보','Short 후보','가격비 z','Hurst','반감기 일','상관'],[[r['name'],r['a']+' / '+r['b'],r['end'],r['state'],r['long'] if abs(r['z'])>=1 else None,r['short'] if abs(r['z'])>=1 else None,r['z'],r['hurst'],r['half'],r['corr']] for r in selected],[dict(columns=['항목','값'],rows=[['가격비 A/B',r['ratio_exact']],['최근252시장일 평균',r['mean_exact']],['모집단 표준편차',r['std_exact']],['상관 시작',r['start']],['상관 종료',r['end']],['일수익 공통 관측',r['observations']],['OU 이산 AR 계수',r['phi']],['공적분 검정','선별에 사용하지 않음'],['포지션 단위','동일 금액 가정 · 베타중립 보증 아님']]) for r in selected]))
    for i,r in enumerate(selected,1):
        chart=curve(f"페어 #{i} · {r['name']} · Z {r['z']:+.2f}",[('가격비 z',r['curve'],'left')],'z-score',guides=[-2,0,2],n=252)
        chart.update(group='Stat Arb',note='가격비 A/B · 252일 rolling z · ±2 진입 조건, ±1 대기, 0 수렴. 현재 후보를 사후 선택한 관측 차트이며 백테스트가 아닙니다.');sections.append(chart)
    sections.append(ledger('8팩터 상위15','멀티팩터',['종목','코드','관측일','점수','12−1M %','3M %','효율','고점 대비 %','연변동성 %'],[[r['name'],r['symbol'],r['date'],r['factor'],r['mom12_1'],r['r3m'],r['eff'],r['high52'],r['vol']] for r in good[:15]],[dict(columns=['팩터','원값','표본 평균','표본 표준편차','제한 z','가중치','방향','점수 기여'],rows=[[c[k] for k in ['name','raw','mean_exact','std_exact','z','weight','sign','contribution']] for c in r['components']]) for r in good[:15]]))
    sections.append(dict(bars('8팩터 점수 Top15',[(r['name'],r['factor']) for r in good[:15]],''),group='멀티팩터'))
    sections.append(ledger('전체 유니버스 · 통과·제외 및 계산 근거','멀티팩터',['종목','코드','가격일','상태','점수','제외 사유'],[[r['name'],r['symbol'],r['date'],'제외' if r['excluded'] else '통과',r['factor'],' / '.join(r['excluded'])] for r in rows],[dict(columns=['항목','값'],rows=[[k,r.get(k)] for k in ['mom12_1','r3m','r1m','r1w','vol','max_daily','eff','high52','stability','vol_improvement','beta','beta_start','beta_end','beta_observations','reversal_z','price_observations','return_observations','missing_dates']]) for r in rows]))
    bab=bab_legs(rows)
    for leg in bab['legs']:sections.append(ledger('BAB '+leg['side'],'BAB',['종목','코드','가격일','Beta 종료일','Beta 관측 수','Beta 1Y','12M %','가정 비중 %'],[[r['name'],r['symbol'],r['date'],r['beta_end'],r['beta_observations'],r['beta'],r['r1y'],r['weight']] for r in leg['rows']]))
    sections.append(dict(bars('BAB · 저베타 Long(앞) / 고베타 Short(뒤)',[(r['name']+' · '+l['side'],r['beta']) for l in bab['legs'] for r in l['rows']],'β'),group='BAB'))
    sections.append(dict(table('BAB 레그 검산',['레그','종목 수','동일가중 Beta','절대노출 %','Beta 노출'],[[l['side'],l['count'],l['mean_beta'],l['gross'],l['beta_exposure']] for l in bab['legs']]+[['합산',sum(l['count'] for l in bab['legs']),None,sum(l['gross'] for l in bab['legs']),bab['net_beta']]]),group='BAB'))
    ts=tsmom(d)
    sections.append(ledger('TSMOM · 12개 자산·금리 관측','TSMOM',['자산','코드','종류','실제 관측일','방향','12M %','3M %','연변동성 %','10% 목표 노출','범위'],[[r['name'],r['symbol'],r['kind'],r['date'],r['direction'] if r['available'] else '미확보',r['r1y'],r['r3m'],r['vol'],r['exposure'],'보존본 명시' if r['reference_named'] else '팀 추가'] for r in ts],[dict(columns=['항목','값'],rows=[['12M 기준가격 날짜',r['start12']],['3M 기준가격 날짜',r['start3']],['실제 종료일',r['date']],['변동성 연환산 일수',r['annual_sessions']],['종류',r['kind']],['가용',str(r['available'])]]) for r in ts]))
    sections.append(dict(bars('TSMOM · 자산별12개월 변화율',[(r['name'],r['r1y']) for r in ts if r['available'] and r['r1y'] is not None],'%'),group='TSMOM'))
    sections.append(dict(type='text',title='TSMOM 관측 단위',group='TSMOM',text='12M·3M 부호가 일치할 때 방향을 표시하고 10%/연변동성 노출에2배 상한을 적용합니다. 미국10년 금리는 금리수준의 상대변화이며 채권 수익률이 아니므로 투자 노출을 계산하지 않습니다. 지수·환율·연속선물 변화도 실제 투자상품 비용 후 수익률이 아닙니다. 보존본 명시6개와 팀 추가6개를 구분합니다.'))
    rev=[r for r in rows if r.get('reversal_z') is not None and ((r['mom12_1']>20 and r['reversal_z']< -1.2) or (r['mom12_1']< -20 and r['reversal_z']>1.2))];rev.sort(key=lambda r:(-abs(r['reversal_z']),r['symbol']))
    sections.append(ledger('추세 조건부5일 반전','단기반전',['종목','코드','관측일','방향','12−1M %','5D z','5D %'],[[r['name'],r['symbol'],r['date'],'LONG' if r['mom12_1']>0 else 'SHORT',r['mom12_1'],r['reversal_z'],r['r1w']] for r in rev]))
    obj=module('quant',d.as_of,'현재 Naver KOSPI300·KOSDAQ150 필터 유니버스. 가격비 A/B의 상관0.5~0.95·Hurst<0.5 순 페어10개, 8팩터 횡단면 z±2.5 상위15, KOSPI Beta5분위/레그 역Beta, 12M·3M TSMOM과 추세 내5D 반전. 실제 날짜·결측·제외 및 점수 기여를 원장에 표시합니다.',sections,[('유니버스',len(members)),('팩터 통과',len(good)),('페어 / 진입',f'{len(selected)} / {sum(abs(r["z"])>=2 for r in selected)}'),('BAB Long / Short',f'{bab["legs"][0]["count"]} / {bab["legs"][1]["count"]}'),('TSMOM 관측',sum(r['available'] for r in ts)),('단기반전',len(rev))],missing=['현재 유니버스와 최신 정정가격의 단면 분석이며 역사 구성종목·PIT·대차/펀딩/거래비용 후 OOS 성과가 아닙니다.','공개되지 않은 rolling/Hurst/MAX/월안정성 세부 설정은 명시한 팀 설정입니다. 가격비 평균회귀를 공적분 검증이나 베타중립으로 부르지 않습니다.','TSMOM 보존본에서 이름이 확인된6개 외 나머지6개는 팀이 선택했습니다. 금리 상대변화에 투자노출을 부여하지 않습니다.'])
    obj['screen']=clean_json(dict(version=1,source_vintage=getattr(d,'vintage',None),calendar_end=str(calendar[-1].date()) if len(calendar) else None,universe=len(members),factor_pass=len(good),pair_universe=len(ready),pair_tested=len(ready)*(len(ready)-1)//2,correlation_pass=screened,hurst_pass=len(pairs),pairs=[{k:v for k,v in r.items() if k!='curve'} for r in selected],stocks=rows,bab=bab,tsmom=ts,reversal=[r['symbol'] for r in rev],features=FEATURES))
    return obj

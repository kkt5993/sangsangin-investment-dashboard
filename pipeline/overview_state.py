"""Six-axis macro and five-axis crowding coordinates with explicit availability lags."""
import numpy as np
import pandas as pd
from .engine import number,clean_json
from .financial_modules import frame,statement_series

SPECS={
 'growth':('성장','%YoY','INDPRO · 산업생산 전년동월비','x'),
 'inflation':('물가','%YoY','CPIAUCSL · 소비자물가 전년동월비','z'),
 'liquidity':('유동성','%YoY','WALCL−WTREGEN−1000×RRPONTSYD · 순유동성 근사','y'),
 'profits':('기업실적','%YoY','CP · 미국 전산업 세후이익 전년동기비','color'),
 'rate':('금리','%','FEDFUNDS · 실효 연방기금금리','size'),
 'momentum':('모멘텀','%12M','SPY/EEM 조정가격 12개월 수익률 동일평균','halo'),
 'overheat':('과열','%이격','S&P500 / 200거래일 단순평균 −1','x'),
 'concentration':('집중도','%vs3Y','SPY/RSP 조정가격비 / 36개월 평균 −1','z'),
 'speculation':('수급밀도','%vs3Y','SPHB/SPLV 조정가격비 / 36개월 평균 −1','y'),
 'valuation':('밸류에이션','%vs3Y','Wilshire5000 가격지수/GDP / 36개월 평균 −1','color'),
 'complacency':('안주','VIX','VIX 수준 · z의 부호를 반대로 표시','size'),
}


def anchors(as_of):
    end=pd.Timestamp(as_of);months=pd.date_range('2004-01-31',end,freq='ME')
    return months if len(months) and months[-1]==end else months.append(pd.DatetimeIndex([end]))


def align(source,available,period,index,max_age):
    """Known step values only; preserve period and availability of carried observations."""
    frame_=pd.DataFrame(dict(value=source.to_numpy(),period=list(period)),index=available).dropna(subset=['value'])
    frame_=frame_[~frame_.index.duplicated(keep='last')].sort_index()
    if frame_.empty:return pd.DataFrame(dict(value=np.nan,period=pd.NaT,available=pd.NaT),index=index)
    frame_['available']=frame_.index
    result=frame_.reindex(frame_.index.union(index)).sort_index().ffill().reindex(index)
    age=(pd.Series(index,index=index)-result.period).dt.days
    result.loc[age>max_age,['value','period','available']]=[np.nan,pd.NaT,pd.NaT]
    return result


def macro(d,key,index,freq='M',lag_months=1,lag_days=0,yoy=False):
    s=d.mac(key).copy();s=s.loc[:d.as_of]
    if s.empty:return align(s,pd.DatetimeIndex([]),pd.DatetimeIndex([]),index,90)
    s.index=s.index.to_period(freq).to_timestamp(how='end').normalize();s=s[~s.index.duplicated(keep='last')]
    full=pd.date_range(s.index[0],s.index[-1],freq='QE' if freq=='Q' else 'ME');s=s.reindex(full)
    if yoy:s=(s/s.shift(4 if freq=='Q' else 12).where(lambda x:x>0)-1)*100
    available=s.index+pd.offsets.MonthEnd(lag_months)+pd.Timedelta(days=lag_days)
    # Q4 corporate profits are normally first included in the March GDP release.
    if key=='CP' and freq=='Q':available=pd.DatetimeIndex([t+pd.offsets.MonthEnd(1) if period.month==12 else t for period,t in zip(s.index,available)])
    # Verified BEA shutdown delays; these are release-date overrides, not vintages.
    delayed={('CP','2025-09-30'):'2025-12-23',('GDP','2025-09-30'):'2025-12-23',('CP','2025-12-31'):'2026-04-09',('GDP','2025-12-31'):'2026-03-13'}
    available=pd.DatetimeIndex([max(t,pd.Timestamp(delayed.get((key,str(period.date())),t))) for period,t in zip(s.index,available)])
    return align(s,available,s.index,index,200 if freq=='Q' else 95)


def price(d,key,index):
    s=d.price(key).loc[:d.as_of]
    return align(s,s.index,s.index,index,7)


def relative36(s):return (s/s.rolling(36,min_periods=36).mean().where(lambda x:x>0)-1)*100


def history_z(s):
    return (s-s.rolling(120,min_periods=60).mean())/s.rolling(120,min_periods=60).std(ddof=0).where(lambda x:x>1e-12)


def liquidity(d,index):
    parts=[]
    for key,factor,age in [('WALCL',1,12),('WTREGEN',1,12),('RRPONTSYD',1000,7)]:
        s=d.mac(key).loc[:d.as_of]*factor
        if len(s):parts.append(align(s,s.index+pd.Timedelta(days=1),s.index,index,age))
        else:parts.append(align(s,pd.DatetimeIndex([]),pd.DatetimeIndex([]),index,age))
    levels=parts[0].value-parts[1].value-parts[2].value
    out=parts[0].copy();out['value']=(levels/levels.shift(12).where(lambda x:x>0)-1)*100
    return out,parts


def states(d):
    index=anchors(d.as_of);observations={}
    observations['growth']=macro(d,'INDPRO',index,yoy=True);observations['inflation']=macro(d,'CPIAUCSL',index,yoy=True)
    observations['profits']=macro(d,'CP',index,freq='Q',lag_months=2,yoy=True)
    observations['rate']=macro(d,'FEDFUNDS',index,lag_months=0,lag_days=7)
    observations['liquidity'],components=liquidity(d,index)
    series={k:r.value for k,r in observations.items()}
    spy=price(d,'SPY',index);em=price(d,'EEM',index);rsp=price(d,'RSP',index);high=price(d,'SPHB',index);low=price(d,'SPLV',index);wil=price(d,'^W5000',index);vix=price(d,'^VIX',index)
    series['momentum']=((spy.value/spy.value.shift(12)-1)+(em.value/em.value.shift(12)-1))*50
    sp=d.price('^GSPC',False);gap=(sp/sp.rolling(200,min_periods=200).mean()-1)*100
    heat=align(gap,gap.index,gap.index,index,7);series['overheat']=heat.value
    series['concentration']=relative36(spy.value/rsp.value);series['speculation']=relative36(high.value/low.value)
    gdp=macro(d,'GDP',index,freq='Q',lag_months=2);series['valuation']=relative36(wil.value/gdp.value)
    series['complacency']=vix.value
    observations.update(momentum=spy,overheat=heat,concentration=spy,speculation=high,valuation=wil,complacency=vix)
    values=pd.DataFrame(series,index=index);z=values.apply(history_z);z['complacency']=-z.complacency
    result=[]
    for id,title,keys in [('tesseract','TESSERACT · 세계의6축 상태',['growth','inflation','liquidity','profits','rate','momentum']),('crowding','CROWDING · 시장 쏠림5축',['overheat','concentration','speculation','valuation','complacency'])]:
        rows=[]
        for t in index[-36:]:
            provenance={k:dict(period=str(observations[k].at[t,'period'].date()) if pd.notna(observations[k].at[t,'period']) else None,available=str(observations[k].at[t,'available'].date()) if pd.notna(observations[k].at[t,'available']) else None) for k in keys}
            if id=='tesseract':
                provenance['liquidity']['components']=[dict(key=key,period=str(f.at[t,'period'].date()) if pd.notna(f.at[t,'period']) else None,available=str(f.at[t,'available'].date()) if pd.notna(f.at[t,'available']) else None) for key,f in zip(['WALCL','WTREGEN','RRPONTSYD'],components)]
                provenance['momentum']['secondary_period']=str(em.at[t,'period'].date()) if pd.notna(em.at[t,'period']) else None
            else:
                provenance['valuation']['gdp_period']=str(gdp.at[t,'period'].date()) if pd.notna(gdp.at[t,'period']) else None
                provenance['valuation']['gdp_available']=str(gdp.at[t,'available'].date()) if pd.notna(gdp.at[t,'available']) else None
                provenance['concentration']['secondary_period']=str(rsp.at[t,'period'].date()) if pd.notna(rsp.at[t,'period']) else None
                provenance['speculation']['secondary_period']=str(low.at[t,'period'].date()) if pd.notna(low.at[t,'period']) else None
            rows.append(dict(date=str(t.date()),partial_month=t!=t.to_period('M').end_time.normalize(),raw={k:number(values.at[t,k]) for k in keys},z={k:number(z.at[t,k]) for k in keys},provenance=provenance))
        result.append(dict(id=id,title=title,axes=[dict(key=k,name=SPECS[k][0],unit=SPECS[k][1],definition=SPECS[k][2],role=SPECS[k][3]) for k in keys],rows=rows,milestones=[dict(label=label,index=len(rows)-1-back,**rows[len(rows)-1-back]) for label,back in [('2년 전',24),('1년 전',12),('6개월 전',6),('현재',0)]],
            note='36개월 관측 시점(마지막 월은 기준일까지). z는 각 시점 이전 최대120개월·최소60개·모표준편차, 절대/관측 수치와 별도 표시. 거시 월말+1개월, 이익/GDP 분기말+2개월(Q4 이익만+3개월), 월금리+7일, 유동성 구성 관측+1일 팀 정보시차이며 확인된2025년 셧다운 지연을 추가 보정했습니다. 실제 과거 공표 빈티지는 아닙니다.'))
    return result


def leaders(d):
    candidates=[];fx=d.price('KRW=X',False);end=pd.Timestamp(d.as_of)
    for symbol,raw in d.fund.items():
        info=raw.get('info',{});cap=number(info.get('marketCap'));currency=info.get('currency')
        if cap is None or cap<=0 or currency not in ['USD','KRW']:continue
        if currency=='KRW':
            if fx.empty or (end-fx.index[-1]).days>7:continue
            cap/=fx.iloc[-1]
        p=d.price(symbol);before=p.loc[:end-pd.DateOffset(years=1)]
        if p.empty or before.empty or (end-p.index[-1]).days>7 or (end-pd.DateOffset(years=1)-before.index[-1]).days>7:continue
        ni=statement_series(frame(raw.get('quarterly_income')),'NetIncome').loc[:end];eg=None;period=None;previous=None
        if len(ni):
            period=ni.index[-1];prior=ni.loc[period-pd.DateOffset(years=1)-pd.Timedelta(days=10):period-pd.DateOffset(years=1)+pd.Timedelta(days=10)]
            if len(prior) and prior.iloc[-1]>0:eg=number((ni.iloc[-1]/prior.iloc[-1]-1)*100);previous=str(prior.index[-1].date())
        candidates.append(dict(symbol=symbol,name=info.get('shortName') or symbol,cap_usd_bn=number(cap/1e9),currency=currency,fx_date=str(fx.index[-1].date()) if currency=='KRW' else None,momentum=number((p.iloc[-1]/before.iloc[-1]-1)*100),growth=eg,profit_period=str(period.date()) if period is not None else None,prior_profit_period=previous,financial_as_of=raw.get('retrieved_at'),price_date=str(p.index[-1].date())))
    pool=sorted(candidates,key=lambda r:-r['cap_usd_bn'])[:50];eligible=[r for r in pool if r['growth'] is not None]
    if eligible:
        f=pd.DataFrame(dict(cap=[np.log(r['cap_usd_bn']) for r in eligible],momentum=[r['momentum'] for r in eligible],growth=[r['growth'] for r in eligible]))
        for key in ['momentum','growth']:f[key]=f[key].clip(*f[key].quantile([.05,.95]))
        zz=(f-f.mean())/f.std(ddof=0).replace(0,np.nan);score=zz.fillna(0).mul(pd.Series(dict(cap=.42,momentum=.35,growth=.23))).sum(axis=1)
        for row,value in zip(eligible,score):row['score']=number(value)
    return dict(stocks=sorted(eligible,key=lambda r:(-r['score'],r['symbol']))[:10],pool=len(pool),eligible=len(eligible),cached=len(d.fund),
        note='현재 재무 캐시의 USD/KRW 환산 시총 상위50 표본에서 12M 가격·분기 순이익 YoY가 있는 종목의 상위10. 전체 세계 시총순위가 아닙니다. 주도력=log 시총 z×0.42+모멘텀 z×0.35+이익성장 z×0.23; 후자2개는 표본5/95분위 winsorize. 재무 수집 시각·관측 결산일·환율일을 보존합니다.')


def build_overview(d):
    return clean_json(dict(schema_version=1,as_of=d.as_of,vintage=d.vintage,status='partial',panels=states(d),leaders=leaders(d),
        sources=[dict(name='FRED 산업생산',url='https://fred.stlouisfed.org/series/INDPRO'),dict(name='FRED CPI',url='https://fred.stlouisfed.org/series/CPIAUCSL'),dict(name='BEA 세후이익 CP',url='https://fred.stlouisfed.org/series/CP'),dict(name='Fed WALCL',url='https://fred.stlouisfed.org/series/WALCL'),dict(name='Fed TGA 주간평균',url='https://fred.stlouisfed.org/series/WTREGEN'),dict(name='Fed RRP',url='https://fred.stlouisfed.org/series/RRPONTSYD'),dict(name='Fed 실효금리',url='https://fred.stlouisfed.org/series/FEDFUNDS'),dict(name='BEA 명목GDP',url='https://fred.stlouisfed.org/series/GDP'),dict(name='S&P 고베타 / SPHB 정의',url='https://www.spglobal.com/spdji/en/indices/dividends-factors/sp-500-high-beta-index/'),dict(name='Invesco 저변동성 SPLV',url='https://www.invesco.com/us/en/financial-products/etfs/invesco-sp-500-low-volatility-etf.html'),dict(name='Wilshire 지수 정의',url='https://www.wilshireindexes.com/products/ft-wilshire-5000-index-series')],
        missing=['z 창·모멘텀 비중·주도력 극단치 처리는 팀 설정이며 원본의 비공개 세부 산식과 수치 동등성은 미검증입니다. 최신 수정 거시와 현재 재무 캐시를 사용하므로 과거 실시간 판단 자료가 아닙니다.',
            '수급밀도는 고베타/저변동 가격비이며 실제 자금 유출입이 아닙니다. Wilshire 가격지수/GDP는 시총/GDP의 상대 움직임 프록시로서 실제 시총/GDP 비율이나 공정가치가 아닙니다.',
            'TGA 주간평균과 WALCL 수요일 값·RRP를 이용한 순유동성 근사입니다. 지표 변환과 발표 시차가 가격 상태와 다르며 관측 기간을 표시합니다. 현재 월은 확정 월말이 아닙니다.']))

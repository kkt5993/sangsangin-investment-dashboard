"""Three-panel macro comparisons. Index / economy profit is not index P/E."""
import pandas as pd
from .engine import number

def monthly_fundamental(s,freq,index):
    f=s.copy();f.index=f.index.to_period(freq).to_timestamp(how='end').normalize()
    # A reference chart of the latest revised vintage by observation period,
    # not what was known then. Do not backfill values before their period end.
    values=f.reindex(f.index.union(index)).sort_index().ffill().reindex(index)
    periods=pd.Series(f.index.strftime('%Y-%m-%d'),index=f.index).reindex(f.index.union(index)).sort_index().ffill().reindex(index)
    return values,periods

def valuation_views(d,obj):
    panels=[]
    for name,symbol,profit,region,freq,unit in [('S&P500','^GSPC','CP','US','Q','USD bn SAAR'),('Nasdaq','^IXIC','CP','US','Q','USD bn SAAR'),('KOSPI','^KS11','KR_CORP_NI','KR','Y','KRW 조원')]:
        daily=d.price(symbol,False);px=daily.resample('ME').last().dropna()
        if len(px) and px.index[-1]>daily.index[-1]:px.index=pd.DatetimeIndex([*px.index[:-1],daily.index[-1]])
        earn=d.mac(profit)
        if region=='KR':
            if d.macro_meta.get(profit,{}).get('unit')!='백만원':raise ValueError('Unexpected Korean income unit')
            earn=earn/1e6
        if not len(earn):raise ValueError('Corporate profit data missing')
        values,periods=monthly_fundamental(earn,freq,px.index);last_period=earn.index[-1].to_period(freq).end_time.normalize()
        inflation=d.mac('KR_CPI' if region=='KR' else 'CPIAUCSL').pct_change(12,fill_method=None)*100
        # CPI is matched to its own observation month and never filled beyond it.
        inflation.index=inflation.index.to_period('M');rate=d.mac('KR_BASE' if region=='KR' else 'FEDFUNDS').resample('ME').last();rate.index=rate.index.to_period('M')
        rows=[]
        for t,price in px.items():
            value=values.loc[t];period=periods.loc[t]
            if pd.isna(value) or value<=0:continue
            rows.append(dict(date=str(t.date()),price=number(price),earnings=number(value),ratio=number(price/value),inflation=number(inflation.get(t.to_period('M'))),rate=number(rate.get(t.to_period('M'))),profit_period=period,carry=t>last_period))
        panels.append(dict(name=name,region=region,symbol=symbol,profit_key=profit,profit_name='미국 전산업 세후이익' if region=='US' else '한국 전산업 당기순손익',profit_unit=unit,last_profit_period=str(last_period.date()),rows=rows[-180:]))
    obj['sections'].insert(0,dict(type='valuation',group='밸류에이션',title='지수·기업이익·물가·금리 · 3단 비교',panels=panels,default_months=180))
    obj['sections'].append(dict(type='text',group='밸류에이션',title='전산업 이익 비교의 범위·날짜',text='상단은 지수와 전산업 이익의 실제 값·독립 로그축, 중단은 지수/이익의 수치비와 선택기간25/50/75분위, 하단은 CPI YoY와 정책금리의 공통%축입니다. 미국은 BEA 세후이익 CP(IVA·CCAdj 미적용, 분기 연율), 한국은 ECOS501Y002 전산업/종합/당기순손익(연간)입니다. 한국 백만원→조원은1e6으로 나눕니다. 지수 구성기업의 이익이나 주당 이익이 아니므로 P/E·시장 전체 시가총액/GDP가 아닙니다. 최신 수정 빈티지를 관측기간말부터 월별로 유지하며 당시 공표일 빈티지·예측력 주장이 아닙니다. 최신 이익 관측기간 이후 점선은 마지막 실제 이익을 유지한 비교 기준이며 미발표 이익 추정치가 아닙니다. CPI 결측월은 이어 그리지 않습니다.'))
    obj['missing']=[m for m in obj['missing'] if '밸류에이션 3단' not in m]
    obj['missing'].append('전산업 이익 관측기간과 공표 시점은 다릅니다. 한국2025/26년 이익을 임의 추정하지 않으며 현재 비율은 최신 실제 연간 이익을 기준으로 합니다. 해당 지수 구성기업의 역사 P/E와 발표시점 빈티지는 별도 과제입니다.')
    obj['source']+=' · BEA CP · ECOS501Y002'

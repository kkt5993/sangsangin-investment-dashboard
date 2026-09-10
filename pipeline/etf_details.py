"""ETF comparisons from local adjusted prices and ex-date cash observations."""
import pandas as pd
from .catalog import etfs
from .engine import module, number, ret, ytd

NOTES = {
    'monthly':'정기 인컴 상품과 리츠를 함께 비교합니다. 실제 지급일은 배당락일과 다릅니다.',
    'yieldmax':'옵션 인컴 상품의 분배 규모와 총수익률을 함께 비교합니다. 분배금에는 원금 반환이 포함될 수 있습니다.',
    'aristocrat':'배당 성장·고배당 주식에 투자하는 상품을 비교합니다.',
    'bondladder':'단기·장기 국채, 회사채, 신흥국채와 물가연동채를 구분해 비교합니다.',
    'bellwether':'주식·채권·금·원자재·리츠·비트코인·달러의 대표 상품입니다.',
    'disruption':'산업과 기술 테마에 투자하는 상품을 비교합니다.',
    'country':'미국 상장 국가·지역 ETF의 USD 성과입니다. 현지 통화 지수 수익률과 다릅니다.',
    'factor':'모멘텀·퀄리티·가치·저변동·규모·성장 스타일을 비교합니다.',
    'leverage':'표시 배수는 일간 목표입니다. 여러 날의 누적수익률에 같은 배수가 보장되지 않습니다.'}


def observed_frequency(events):
    """Recent ex-date spacing, not a promise about future pay dates."""
    if len(events)==0:return '관측 없음'
    if len(events)==1:return '1회 관측'
    days=events.index.to_series().diff().dt.days.dropna().tail(6)
    median=float(days.median())
    for name,lo,hi,minimum in [('주간 간격',5,9,3),('월간 간격',23,39,3),('분기 간격',65,115,2),('반기 간격',140,220,1)]:
        if len(days)>=minimum and lo<=median<=hi and (days.between(lo,hi).mean()>=.67):return name
    return '비정기·혼합'


def etf_row(d,item):
    symbol=item['symbol'];f=d.frames.get(symbol)
    row=dict(symbol=symbol,name=item['name'],feature=item.get('feature',item['name']),
             instrument_type='상장 리츠' if symbol=='O' else 'ETF·ETP',
             returns=[None]*4,yield_pct=None,payments=None,monthly_per_10m=None,
             frequency='확인 불가',events=[],as_of=None,reason=None,
             price_source=f'https://finance.yahoo.com/quote/{symbol}/history/',
             product_source=item.get('source'),
             retrieved_at=d.quality.get(symbol,{}).get('retrieved_at'))
    if f is None or f.empty:
        row['reason']='최근 가격 또는 분배 관측 자료 미수집';return row
    f=f.loc[:d.as_of].copy();f=f[f.close.gt(0)&f.adjusted_close.gt(0)].sort_index()
    if f.empty:
        row['reason']='기준일까지 유효 가격 없음';return row
    end=f.index[-1];row['as_of']=str(end.date())
    if (pd.Timestamp(d.as_of)-end).days>7:
        row['reason']='마지막 가격이 기준일보다 7일 초과 오래됨';return row
    p=f.adjusted_close;row['returns']=[ret(p,21),ret(p,63),ytd(p),ret(p,252)]
    cutoff=end-pd.DateOffset(years=1)
    row.update(window_start=str(cutoff.date()),history_start=str(f.index[0].date()),close=number(f.close.iloc[-1]))
    complete=f.index[0]<=cutoff
    row['complete_12m']=bool(complete)
    if 'dividend' not in f or f.loc[f.index>cutoff,'dividend'].isna().any():
        row['reason']='분배 관측 필드 누락';return row
    cash=f.loc[f.index>cutoff,'dividend'];cash=cash[cash>0]
    # Yahoo historical cash is split-adjusted already. Applying split factors again is wrong.
    row.update(events=[[str(t.date()),number(v)] for t,v in cash.items()],
               payments=len(cash),frequency=observed_frequency(cash),cash_per_share=number(cash.sum()))
    if not complete:
        row['reason']='12개월 전체 가격·분배 관측기간 미확보';return row
    row['yield_pct']=number(cash.sum()/f.close.iloc[-1]*100)
    row['monthly_per_10m']=number(10_000_000*row['yield_pct']/1200)
    return row


def monitor(d):
    sections=[];observed=0;positions=0;unique=set()
    for category in etfs():
        rows=[etf_row(d,dict(item,feature=item.get('feature',category.get('feature',item['name'])))) for item in category['items']]
        sort_key='yield_pct' if any((r['yield_pct'] or 0)>0 for r in rows) else 'return_1y'
        def value(r):return r['yield_pct'] if sort_key=='yield_pct' else r['returns'][3]
        rows.sort(key=lambda r:(value(r) is None,-(value(r) or 0),r['symbol']))
        title=category['name'];observed+=sum(r['yield_pct'] is not None for r in rows);positions+=len(rows);unique.update(r['symbol'] for r in rows)
        sections.append(dict(type='etf',id=category['id'],title=title,group=title,rows=rows,
                             note=NOTES[category['id']],sort_key=sort_key))
    return module('etfmon',d.as_of,
        '9분류의 1M·3M·YTD·1Y 수익률은 분배금 조정종가(USD) 기준입니다. 분배율은 최근 12개월 관측 현금분배 합계/시장 종가이며 운용사의 NAV 기준 분배율·SEC 수익률과 다릅니다. 월 금액은 세전 단순 월평균으로, 미래 지급액이나 실제 원화 투자성과가 아닙니다. 관측 날짜는 배당락일이며 지급일이 아닙니다.',
        sections,[('비교 위치',positions),('개별 상품',len(unique)),('12M 분배 관측',f'{observed}/{positions}')],
        'operational' if observed==positions else 'partial',
        missing=['주기는 최근 배당락일 간격에서 계산한 관측 분류입니다. 세금·환전비용·향후 지급일·원금 반환 비중은 별도 원천이 필요합니다.'])

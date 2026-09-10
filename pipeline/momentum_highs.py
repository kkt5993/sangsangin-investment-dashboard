"""O'Neil-style strength and 52-week high candidates in two declared universes."""
import numpy as np
import pandas as pd
from .analytics import clean
from .engine import number
from .market_modules import rankings
from .store import read_json

SPEC=dict(version=1,rs_min=65,high_distance_pct=5,high_sessions=252,
          spark_sessions=130,spark_points=44,maximum_price_age_days=7,
          maximum_membership_age_days=14,
          price='Dividend/split-adjusted OHLC rescaled to latest market close',
          rs='40/20/20/20 weighted cumulative 63/126/189/252 returns; full-universe percentile 1..99')


def observations(frame,as_of):
    """A split/dividend-consistent high and line, anchored to today's price units."""
    if not {'close','adjusted_close','high','low','open'}.issubset(frame):raise ValueError('OHLC 미확보')
    f=frame.loc[:as_of].copy()
    p=clean(f.adjusted_close,as_of)
    if len(p)<253 or len(f)<253:raise ValueError('253개 완료 관측 부족')
    if (pd.Timestamp(as_of)-p.index[-1]).days>SPEC['maximum_price_age_days']:raise ValueError('최근 가격 미확보')
    f=f.reindex(p.index)
    raw=f[['open','high','low','close','adjusted_close']]
    if not np.isfinite(raw.to_numpy()).all() or (raw<=0).any().any():raise ValueError('OHLC 결측·비양수')
    tolerance=f.close.abs()*1e-5
    if ((f.high+tolerance<f[['open','close','low']].max(axis=1))|(f.low-tolerance>f[['open','close','high']].min(axis=1))).tail(253).any():raise ValueError('최근 OHLC 범위 불일치')
    scale=f.adjusted_close/f.close*f.close.iloc[-1]/f.adjusted_close.iloc[-1]
    close=f.close*scale;high=f.high*scale
    high52=float(high.tail(252).max());prior=float(high.iloc[-253:-1].max());price=float(close.iloc[-1])
    from_high=100*(price/high52-1)
    sampled=close.tail(130)
    indexes=np.unique(np.linspace(0,len(sampled)-1,min(44,len(sampled)),dtype=int))
    return dict(price=number(price),high52=number(high52),from_high=number(from_high),
                new_high=bool(high.iloc[-1]>prior*(1+1e-8)),
                as_of=str(p.index[-1].date()),high_window_start=str(high.index[-252].date()),
                high_date=str(high.tail(252).idxmax().date()),
                spark=[[str(sampled.index[i].date()),number(sampled.iloc[i])] for i in indexes])


def build(d):
    groups=[];collect_path=d.resource('us100_collection.json')
    collection=read_json(collect_path) if collect_path.exists() else dict(status='missing')
    for market,key,title in [('US','us100','미국 S&P100 · OEF 공시 주식'),('KR','kospi200','한국 KOSPI200 · KRX 공식 구성')]:
        membership=d.members.get(key,{})
        group=dict(market=market,universe=key,title=title,expected=len(membership.get('members',[])),eligible=0,
                   selected=0,rows=[],excluded=[],members=[],source=membership.get('source'),
                   membership_as_of=membership.get('as_of'),membership_retrieved_at=membership.get('retrieved_at'),
                   membership_sha256=membership.get('sha256'),status='ok',reason=None)
        groups.append(group)
        if market=='US':group['collection']=collection
        date=group['membership_as_of']
        if not date or not membership.get('members'):
            group.update(status='missing',reason='공식 구성목록 미확보');continue
        age=(pd.Timestamp(d.as_of)-pd.Timestamp(date)).days
        if not 0<=age<=SPEC['maximum_membership_age_days']:
            group.update(status='missing',reason='구성목록 기준일이 가격일 이후이거나 14일 초과 경과');continue
        ranked=rankings(d,[(market,key)])[market]
        group['eligible']=ranked['available'];group['excluded']=ranked['excluded']
        for row in ranked['rows']:
            record={k:row[k] for k in ['symbol','name','sector','rs','as_of']}
            # Rank every price-eligible constituent before filtering proximity.
            try:
                metrics=observations(d.frames[row['symbol']],d.as_of)
                record.update({k:v for k,v in metrics.items() if k!='spark'})
                if row['rs']>=SPEC['rs_min'] and metrics['from_high']>=-SPEC['high_distance_pct']:
                    group['rows'].append(dict(record,spark=metrics['spark']))
                record['reason']=None
            except ValueError as error:
                record.update(reason=str(error),from_high=None,high52=None,new_high=False)
                group['excluded'].append(dict(symbol=row['symbol'],name=row['name'],reason=str(error)))
            group['members'].append(record)
        group['rows'].sort(key=lambda r:(-r['rs'],-r['from_high'],r['symbol']))
        group['selected']=len(group['rows'])
        group['high_eligible']=sum(r['reason'] is None for r in group['members'])
        if group['excluded'] or (market=='US' and collection.get('status')!='ok'):group['status']='partial'
    return dict(as_of=d.as_of,spec=SPEC,groups=groups,
                note='미국은 S&P100을 추종하는 OEF 공시 주식, 한국은 KRX KOSPI200 구성목록입니다. 전체 가격 가용 종목 안에서 RS를 계산한 뒤 RS≥65·최근252관측 고점5%이내를 선별합니다. 선별되지 않은 전체 비교 대상도 확인할 수 있습니다. 현재 구성 기준의 단면 관측이며 과거 편입 이력이나 매매 성과가 아닙니다.')

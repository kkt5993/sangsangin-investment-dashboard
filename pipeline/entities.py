"""Dated Entity 360 cards from existing official universes and local observations."""
import pandas as pd
from .engine import number, points
from .financial_modules import frame


def sensitivity(price, benchmark):
    aligned = pd.concat({'stock': price, 'market': benchmark}, axis=1).dropna()
    r = aligned.pct_change(fill_method=None).dropna().tail(252)
    if len(r) < 200 or r.market.var() <= 0:
        return None
    return dict(beta=number(r.stock.cov(r.market)/r.market.var()),
                r2=number(r.stock.corr(r.market)**2), observations=len(r),
                start=str(r.index[0].date()), end=str(r.index[-1].date()))


def entity_view(d, ranks, financial, events):
    # The KR large-cap RS takes precedence where KOSPI200 membership overlaps.
    chosen = {}
    for universe in ['KR', 'US', 'KOSPI200']:
        for a in ranks[universe]['rows']:
            chosen.setdefault(a['symbol'], dict(a, market='US' if universe == 'US' else 'KR', rs_universe=universe))
    statements = {a['symbol']: a for a in financial}
    entities = []
    for symbol, a in chosen.items():
        p = d.price(symbol); benchmark = '^KS11' if a['market'] == 'KR' else 'SPY'
        sample = p.tail(64); curve = points(sample/sample.iloc[0]*100, 14)
        raw = events.get(symbol, {}); releases = frame(raw.get('earnings_dates'))
        upcoming = []
        for t in releases.index:
            dt = pd.Timestamp(t)
            if dt.tzinfo is not None and d.as_of < str(dt.tz_convert('Asia/Seoul').date()) <= str((pd.Timestamp(d.as_of)+pd.Timedelta(days=90)).date()):
                upcoming.append(dt.tz_convert('Asia/Seoul').isoformat())
        f = statements.get(symbol)
        entity = dict(id='stock:'+symbol, name=a['name'], symbol=symbol, market=a['market'], kind='company',
                      sector=a['sector'], rs_universe=a['rs_universe'], rs=a['rs'], date=a['as_of'],
                      returns=[a[k] for k in ['r1w', 'r1m', 'r3m', 'ytd', 'r1y']], rsi=a['rsi'],
                      high52=a['high52'], curve=curve, benchmark=benchmark,
                      sensitivity=sensitivity(p, d.price(benchmark)),
                      upcoming=sorted(set(upcoming)), events_retrieved=raw.get('retrieved_at'),
                      financial=None)
        if f:
            entity['financial'] = {k: f[k] for k in ['financial_currency', 'financial_as_of', 'report_date',
                                                     'margin', 'net_income', 'eps1', 'eps2', 'estimate_currency']}
        entities.append(entity)
    return dict(type='entities', title='Entity 360 · 공식 유니버스 종목 탐색', group='Entity 360', entities=entities,
                coverage={k: dict(available=v['available'], expected=v['expected'], membership_as_of=v['membership_as_of']) for k,v in ranks.items()})

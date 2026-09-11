"""Dated 기업 상세 cards from existing official universes and local observations."""
import pandas as pd
from .engine import number, points
from .financial_modules import frame


def sensitivity(price, benchmark):
    # Preserve benchmark sessions with missing stock prices before daily returns.
    aligned = pd.concat({'stock': price, 'market': benchmark}, axis=1).sort_index()
    r = aligned.pct_change(fill_method=None).dropna().tail(252)
    if len(r) < 200 or r.market.var() <= 0:
        return None
    return dict(beta=number(r.stock.cov(r.market)/r.market.var()),
                r2=number(r.stock.corr(r.market)**2), observations=len(r),
                start=str(r.index[0].date()), end=str(r.index[-1].date()))


def entity_view(d, ranks, financial, events, extra=None):
    # The KR large-cap RS takes precedence where KOSPI200 membership overlaps.
    chosen = {}
    for universe in ['KR', 'US', 'KOSPI200']:
        for a in ranks[universe]['rows']:
            chosen.setdefault(a['symbol'], dict(a, market='US' if universe == 'US' else 'KR', rs_universe=universe))
    additions=[]
    for raw in extra or []:
        symbol=raw['symbol']
        if symbol in chosen:continue
        stats=d.stats(symbol)
        if not stats:continue
        chosen[symbol]=dict(stats,name=raw['name'],sector='공식 업종 미확보',market='KR' if symbol.endswith(('.KS','.KQ')) else 'US',rs_universe='추가 사업 관찰',rs=None)
        additions.append(symbol)
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
        identity=next((r for r in extra or [] if r['symbol']==symbol and r.get('identity_source')),None)
        if identity:entity['identity']={k:identity[k] for k in ['identity_source','identity_name','identity_checked_at']}
        entities.append(entity)
    return dict(type='entities', title='기업 상세 · 공식 유니버스와 추가 사업 관찰', group='기업 상세', entities=entities,extra_symbols=additions,
                coverage={k: dict(available=v['available'], expected=v['expected'], membership_as_of=v['membership_as_of']) for k,v in ranks.items()})

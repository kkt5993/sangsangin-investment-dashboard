"""Instrument identities; unresolved reference labels deliberately have no proxy.

US ticker labels are explicit in the saved reference chart notes.
KR code evidence and ambiguities: research/PRICE_CONTRACT.md.
"""
PAIRS = []


def pair(key, name, market, a, b, sector=False, reason=None):
    PAIRS.append(dict(id=key, name=name, market=market, a=a, b=b,
                      sector=sector, unresolved=reason))


for key, name, code in [
    ('transport', '운송', '140710'), ('it', 'IT', '266370'),
    ('banks', '은행', '091170'), ('chemicals', '에너지화학', '117460'),
    ('health', '헬스케어', '266420'), ('steel', '철강', '117680'),
    ('construction', '건설', '117700'), ('battery', '2차전지', '305720'),
    ('semi', '반도체', '091160'), ('brokers', '증권', '102970'),
    ('auto', '자동차', '091180'),
]:
    pair('kr_'+key, name+' / KOSPI', 'KR', code+'.KS', '^KS11', True)
pair('kr_ship', 'KODEX 조선TOP10 / KOSPI', 'KR', '0115D0.KS', '^KS11', True)
pair('kr_holdings', 'TIGER 지주회사 / KOSPI', 'KR', '307520.KS', '^KS11', True)
pair('kr_dividend', '고배당 vs KOSPI', 'KR', '279530.KS', '^KS11')
pair('kr_kq150', 'KQ150 vs KOSPI', 'KR', '229200.KS', '^KS11')
pair('kr_size', 'KOSPI 대형주 vs KOSPI200 중소형', 'KR', '337140.KS', '226980.KS')
pair('kr_style', 'KODEX 가치주 vs 성장주', 'KR', '275290.KS', '325010.KS')
pair('kr_cyclical', '경기소비재 vs 필수소비재', 'KR', '139290.KS', '266410.KS')

for key, name, code in [
    ('financials', 'Financials', 'XLF'), ('healthcare', 'Healthcare', 'XLV'),
    ('energy', 'Energy', 'XLE'), ('materials', 'Materials', 'XLB'),
    ('staples', 'Cons.Stap', 'XLP'), ('tech', 'Tech', 'XLK'),
    ('communication', 'Comm.Svc', 'XLC'), ('discretionary', 'Cons.Disc', 'XLY'),
    ('realestate', 'Real Estate', 'XLRE'), ('utilities', 'Utilities', 'XLU'),
    ('industrials', 'Industrials', 'XLI'),
]:
    pair('us_'+key, name+' / SPY', 'US', code, 'SPY', True)
for key, name, a, b in [
    ('style', 'Value vs Growth', 'IWD', 'IWF'),
    ('weight', 'Equal-Weight vs Cap-W', 'RSP', 'SPY'),
    ('dividend', 'High-Div vs S&P500', 'VYM', 'SPY'),
    ('cyclical', 'Cyclical vs Defensive', 'XLY', 'XLP'),
    ('size', 'Large vs Small', 'SPY', 'IWM'),
    ('nasdaq', 'Nasdaq vs S&P500', 'QQQ', 'SPY'),
]:
    pair('us_'+key, name, 'US', a, b)

ASSETS = []
for group, entries in [
    ('country', [('EWZ','Brazil'),('MCHI','China'),('EWT','Taiwan'),('EWJ','Japan'),
                 ('EWU','UK'),('EWG','Germany'),('EFA','Intl Dev'),('SPY','S&P 500'),
                 ('VGK','Europe'),('EEM','Emerging'),('EWW','Mexico'),('INDA','India'),('EWY','Korea')]),
    ('factor', [('PKW','Buyback'),('VLUE','Value'),('MOAT','Wide Moat'),('USMV','Low Vol'),
                ('VYM','High Div'),('QUAL','Quality'),('RSP','Equal Weight'),('IWF','Growth'),
                ('IWM','Small Cap'),('MTUM','Momentum')]),
    ('asset', [('BTC-USD','Bitcoin'),('DBC','Commodity'),('GLD','Gold'),('ARKK','Innovation'),
               ('DBMF','Managed Futures'),('HYG','High Yield'),('TIP','TIPS'),('VNQ','REIT'),('TLT','Long Bond')]),
]:
    ASSETS.extend(dict(symbol=s, name=n, group=group, currency='USD') for s,n in entries)


def symbols():
    # Never download half of an unresolved pair just to populate the cache.
    paired = {s for p in PAIRS if not p['unresolved'] for s in (p['a'], p['b'])}
    return sorted(paired | {a['symbol'] for a in ASSETS})

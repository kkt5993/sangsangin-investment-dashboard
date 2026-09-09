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
pair('kr_ship', '조선 / KOSPI', 'KR', None, '^KS11', True,
     '원본의 KODEX 조선 종목코드·과거 연결계열 미공개. 조선TOP10은 2025년 상장으로 원본 5년 계열을 설명하지 못함.')
pair('kr_holdings', '지주 / KOSPI', 'KR', None, '^KS11', True,
     '원본의 KODEX 코스피지주라는 표기만으로 종목코드를 확정할 수 없음.')
pair('kr_dividend', '고배당 vs KOSPI', 'KR', '279530.KS', '^KS11')
pair('kr_kq150', 'KQ150 vs KOSPI', 'KR', '229200.KS', '^KS11')
pair('kr_size', '대형 vs 중소형', 'KR', '069500.KS', '226980.KS')
pair('kr_style', '가치 vs 성장', 'KR', None, None, reason='KODEX 가치·성장이라는 축약명만 공개됨. 두 종목코드 확인 필요.')
pair('kr_cyclical', '경기민감 vs 방어', 'KR', '139290.KS', None,
     reason='TIGER 경기소비재는 139290. 분모 KODEX 생활소비재는 종목코드가 불명확하여 필수소비재로 임의 대체하지 않음.')
for p in PAIRS:
    if p['id'] == 'kr_it':
        p['unresolved'] = '공식 KODEX IT(266370)와 원본의 동일 기준일 3M 차이가 21%p 이상 다름. 원본의 실제 종목코드 확인 필요.'
    if p['id'] == 'kr_size':
        p['unresolved'] = 'KODEX 200/200중소형으로 대응했으나 원본의 동일 기준일 3M 차이가 7%p 이상 다름. 원본 유니버스 확인 필요.'

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

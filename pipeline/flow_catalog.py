"""Daily leverage objectives verified against issuer pages on 2026-09-09.

This is an explicit coverage list, not every fund listed worldwide. Changing a
fund's objective requires updating this reviewed definition, not guessing from
historical returns or the reference dashboard's older product names.
"""
US_STOCKS='COIN MSTR SMCI TSLA GME NVDA ORCL MU CRWD PLTR JPM LLY AMD GOOGL META MSFT NFLX AMZN AVGO AAPL'.split()
DIREXION='https://www.direxion.com/single-stock-etfs'
GRANITE='https://graniteshares.com/etfs/leveraged/'
ETF_DEFINITIONS=[]
for underlying,bull,bear in [('TSLA','TSLL','TSLS'),('AAPL','AAPU','AAPD'),('AMD','AMUU','AMDD'),('AMZN','AMZU','AMZD'),('AVGO','AVL','AVS'),('GOOGL','GGLL','GGLS'),('META','METU','METD'),('MSFT','MSFU','MSFD'),('MU','MUU','MUD'),('NFLX','NFXL','NFXS'),('NVDA','NVDU','NVDD'),('ORCL','ORCU','ORCS'),('PLTR','PLTU',None),('LLY','ELIL',None),('COIN','CONX',None)]:
    ETF_DEFINITIONS.append(dict(symbol=bull,underlying=underlying,leverage=2,source=DIREXION,kind='stock'))
    if bear:ETF_DEFINITIONS.append(dict(symbol=bear,underlying=underlying,leverage=-1,source=DIREXION,kind='stock'))
for symbol,underlying in [('CONL','COIN'),('NVDL','NVDA'),('FBL','META'),('AMDL','AMD'),('CRWL','CRWD')]:
    ETF_DEFINITIONS.append(dict(symbol=symbol,underlying=underlying,leverage=2,source=GRANITE,kind='stock'))
for symbol,underlying in [('GMEU','GME'),('NVDX','NVDA'),('TSLT','TSLA'),('AAPX','AAPL'),('GOOX','GOOGL'),('MSFX','MSFT'),('NFLU','NFLX')]:
    ETF_DEFINITIONS.append(dict(symbol=symbol,underlying=underlying,leverage=2,source='https://www.rexshares.com/t-rex-leveraged-etfs/',kind='stock'))
ETF_DEFINITIONS += [dict(symbol='SMCX',underlying='SMCI',leverage=2,source='https://www.defianceetfs.com/smcx/',kind='stock'),dict(symbol='PLTD',underlying='PLTR',leverage=-1,source='https://www.direxion.com/product/daily-pltr-bull-and-bear-leveraged-single-stock-etfs',kind='stock')]
for symbol,leverage in [('MSTU',2),('MSTZ',-2),('MSTX',2)]:
    ETF_DEFINITIONS.append(dict(symbol=symbol,underlying='MSTR',leverage=leverage,source='https://www.defianceetfs.com/mstx/' if symbol=='MSTX' else 'https://www.rexshares.com/mstr-etfs/',kind='stock'))
for symbol,underlying,leverage in [('TQQQ','Nasdaq-100',3),('SQQQ','Nasdaq-100',-3),('UPRO','S&P500',3),('SPXU','S&P500',-3),('SOXL','NYSE Semiconductor',3),('SOXS','NYSE Semiconductor',-3)]:
    ETF_DEFINITIONS.append(dict(symbol=symbol,underlying=underlying,leverage=leverage,kind='index',source='https://www.direxion.com/product/daily-semiconductor-bull-bear-3x-etfs' if symbol.startswith('SOX') else 'https://www.proshares.com/our-etfs/leveraged-and-inverse/'+symbol.lower()))

# Mutually exclusive first-match rules; geographic/geared ETFs are still
# disclosed in the member table. These are team themes, not KRX industry codes.
KR_THEMES=[('반도체',r'반도체|필라델피아'),('2차전지',r'2차전지|배터리|리튬'),('바이오·헬스',r'바이오|헬스|의료'),('AI·로봇',r'AI|인공지능|로봇'),('방산',r'방산|방위'),('조선',r'조선'),('전력·원전',r'전력|원자력|원전'),('자동차',r'자동차|모빌리티'),('금융',r'은행|금융|증권|보험'),('인터넷·콘텐츠',r'인터넷|플랫폼|게임|미디어|엔터'),('친환경',r'친환경|클린|신재생|태양광|풍력'),('소비재',r'소비|화장품|여행|레저|음식료')]

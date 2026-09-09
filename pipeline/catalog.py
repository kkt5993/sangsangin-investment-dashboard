"""Shared market instruments and official classification data contracts."""
from .store import ROOT, read_json

CONFIG=ROOT/'config'
INDICES=[('SP500','^GSPC','S&P500'),('KOSPI','^KS11','KOSPI'),('NASDAQ','^IXIC','NASDAQ')]
DYNAMICS_STOCKS=[('NVDA','NVIDIA'),('MSFT','Microsoft'),('AAPL','Apple'),('GOOGL','Alphabet'),
 ('AMZN','Amazon'),('META','Meta'),('AVGO','Broadcom'),('TSLA','Tesla'),('NFLX','Netflix'),('PLTR','Palantir'),
 ('005930.KS','삼성전자'),('000660.KS','SK하이닉스'),('373220.KS','LG에너지솔루션'),('207940.KS','삼성바이오로직스'),('005380.KS','현대차')]
MULTI=[('SPY','S&P500','주식-DM'),('QQQ','Nasdaq','주식-DM'),('IWM','Russell2000','주식-DM'),
 ('^N225','Nikkei225','주식-DM'),('^STOXX50E','EuroStoxx50','주식-DM'),('^KS11','KOSPI','주식-EM'),
 ('MCHI','China','주식-EM'),('INDA','India','주식-EM'),('EEM','EM 전체','주식-EM'),
 ('TLT','미국 장기국채','채권'),('IEF','미국 중기국채','채권'),('HYG','하이일드','채권'),
 ('GLD','금','원자재'),('CL=F','WTI 원유','원자재'),('HG=F','구리','원자재'),('SI=F','은','원자재'),
 ('DX-Y.NYB','달러지수(DXY)','FX'),('KRW=X','원/달러','FX'),('JPY=X','엔/달러','FX'),
 ('BTC-USD','비트코인','크립토'),('ETH-USD','이더리움','크립토')]
SCAN_EXTRA=[('^DJI','다우','주식-DM'),('^FTSE','영국 FTSE','주식-DM'),('^GDAXI','독일 DAX','주식-DM'),
 ('^KQ11','KOSDAQ','주식-EM'),('EWZ','브라질','주식-EM'),('NG=F','천연가스','원자재'),
 ('DBA','농산물','원자재'),('EURUSD=X','유로/달러','FX'),('SOL-USD','솔라나','크립토'),
 ('XBI','바이오텍','섹터'),('XLV','美 헬스케어','섹터'),('XLE','美 에너지','섹터'),
 ('XLK','美 기술','섹터'),('SMH','반도체','섹터'),('VNQ','리츠','리츠'),('UUP','달러 ETF','FX')]
MACRO={
 'CPIAUCSL':('CPI','index','M'), 'PCEPILFE':('근원 PCE','index','M'), 'INDPRO':('산업생산','index','M'),
 'UNRATE':('실업률','%','M'), 'FEDFUNDS':('연방기금금리','%','M'), 'DGS10':('미국 10Y','%','D'),
 'DGS2':('미국 2Y','%','D'), 'DGS3MO':('미국 3M','%','D'), 'DFII10':('미국 실질 10Y','%','D'),
 'T10YIE':('미국 10Y 기대인플레','%','D'), 'T10Y2Y':('10Y−2Y','%p','D'), 'T10Y3M':('10Y−3M','%p','D'),
 'NFCI':('금융여건','z','W'), 'M2SL':('M2','USD bn','M'), 'WALCL':('연준 자산','USD mn','W'),
 'BAMLH0A0HYM2':('HY OAS','%','D'), 'VIXCLS':('VIX','index','D'), 'SAHMREALTIME':('Sahm Rule','%p','M'),
 'RECPROUSM156N':('침체확률','%','M'), 'GDP':('미국 명목 GDP','USD bn SAAR','Q'),
 'GDPC1':('미국 실질 GDP','USD bn SAAR','Q'), 'USEPUINDXD':('미국 정책불확실성','index','D'),
 'ICSA':('신규 실업수당','persons','W'), 'PAYEMS':('비농업 고용','thousands','M'),
 'RSAFS':('소매판매','USD mn','M'), 'HOUST':('주택착공','thousands SAAR','M'),
 'USREC':('미국 침체 더미','0/1','M'), 'CBOEPUTCALL':('풋콜 비율','ratio','D'),
}
MACRO.update({
 'BAMLC0A0CM':('미국 투자등급 OAS','%','D'), 'RRPONTSYD':('연준 익일 역레포','USD bn','D'),
 'IPG3344S':('반도체·전자부품 산업생산','2017=100','M'),
 'PCU334413334413':('반도체 제조업 PPI','1998-12=100','M'),
 'WPU101':('철강 PPI','1982=100','M'), 'TSIFRGHT':('화물운송 물동량','2000=100','M'),
 'TOTALSA':('미국 자동차 판매','million SAAR','M'), 'IPG3361T3S':('자동차·부품 산업생산','2017=100','M'),
 'PERMIT':('건축허가','thousand SAAR','M'), 'MORTGAGE30US':('30년 고정 모기지','%','W'),
 'UMCSENT':('미시간 소비자심리','1966Q1=100','M'),
 'AMTMNO':('제조업 신규수주','USD mn','M'), 'DGORDER':('내구재 신규수주','USD mn','M'),
})
# Explicit support instruments, never an implicit all-market expansion.
DETAIL_PRICES=['USO','^MOVE','^VVIX','GC=F','^SOX','IYT','BDRY','KBE','JETS','IBB','ZC=F','ZW=F','ZS=F','LBR=F','RB=F','HO=F']


def etfs():
    return read_json(CONFIG/'etf_categories.json')


def reference_stocks():
    return read_json(CONFIG/'research_stocks.json')


def extra_price_symbols():
    from .universe import symbols
    return sorted({r['symbol'] for c in etfs() for r in c['items']} |
                  {s for s,n,g in MULTI+SCAN_EXTRA} | {s for _,s,_ in INDICES} |
                  {s for s,n in DYNAMICS_STOCKS} |
                  set(symbols()) | set(DETAIL_PRICES) | {'LQD','ACWI','SOXX','FXE','FXY','BIL','^VIX','^VIX3M','^SKEW','^TNX'})

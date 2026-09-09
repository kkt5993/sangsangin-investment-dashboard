"""Named monthly macro/market inputs; future data never enter transformations.

Current revised macro observations are shifted two full months. This is not a
reconstruction of release vintages. Missing blocks are declared, never invented.
"""
import numpy as np
import pandas as pd

LEVELS=['FEDFUNDS','DGS10','DGS2','DGS3MO','DFII10','T10YIE','T10Y2Y','T10Y3M','NFCI','BAMLH0A0HYM2','UNRATE','UMCSENT','MORTGAGE30US','KR_BASE','OECD_CLI_USA','OECD_CLI_KOR']
YOYS=['CPIAUCSL','PCEPILFE','INDPRO','PAYEMS','RSAFS','HOUST','PERMIT','M2SL','WALCL','KR_CPI','KR_EXPORT','KR_DEPOSIT','KR_MARGIN']
FORCED_KR=['KR_EXPORT','KR_EXPORT_d3','SOX_3m','SOX_6m','SOX_relative_3m','RS_SOX_z','OECD_CLI_KOR','OECD_CLI_KOR_d3','KR_DEPOSIT','KR_DEPOSIT_d3','KR_MARGIN','KR_MARGIN_z']
ALWAYS=['RISK_COMPOSITE','DGS10_d12','YIELD_VOL','MOVE_z','GAMMA_TERM','VVIX_z','SKEW_z','CONCENTRATION_3m','CONCENTRATION_DIV','NVDA_relative_z','RS_KOSPI_z','RS_QQQ_z']
MISSING=['Shiller CAPE/ERP','SF Fed news sentiment','global monthly EPU','VIX9D/VIX short-term structure','historical foreign investor net flows']


def rolling_z(s,n=60):
    mean=s.rolling(n,min_periods=min(36,n)).mean();sd=s.rolling(n,min_periods=min(36,n)).std(ddof=0)
    return ((s-mean)/sd.replace(0,np.nan)).mask(sd==0,0)


def build_features(d,symbol):
    p=d.monthly(symbol);index=p.loc['2004-01-01':].index
    f={}
    def month(s):return s.resample('ME').last().reindex(index)
    def mac(key):return month(d.mac(key))
    def px(key):return d.monthly(key).reindex(index)
    def change(s,n):return s.pct_change(n,fill_method=None)*100
    def log_return(s,n):return np.log(s/s.shift(n))*100
    for key in LEVELS+YOYS:
        m=mac(key)
        if key in YOYS:m=change(m,12)
        if key.startswith('OECD_CLI_'):m=m-100
        f[key]=m.shift(2);f[key+'_d3']=m.diff(3).shift(2)
    for key in ['BAMLH0A0HYM2','NFCI','KR_MARGIN']:
        f[key+'_z']=rolling_z(f[key])
    f['DGS10_d12']=mac('DGS10').diff(12).shift(2)
    f['YIELD_VOL']=mac('DGS10').diff().rolling(6).std(ddof=0).shift(2)
    hy=mac('BAMLH0A0HYM2')-mac('BAMLC0A0CM')
    f['HY_IG']=hy.shift(2);f['HY_IG_d3']=hy.diff(3).shift(2);f['HY_IG_z']=rolling_z(hy).shift(2)
    # Daily market observations known after the last session of each origin month.
    vix=mac('VIXCLS');f['VIX']=vix;f['VIX_d1']=vix.diff();f['VIX_z']=rolling_z(vix)
    for symbol_key,label in [('^MOVE','MOVE'),('^VVIX','VVIX'),('^SKEW','SKEW')]:
        q=px(symbol_key);f[label]=q;f[label+'_z']=rolling_z(q)
    f['GAMMA_TERM']=vix/px('^VIX3M');f['GAMMA_TERM_d3']=f['GAMMA_TERM'].diff(3)
    for symbol_key,label in [('^GSPC','SPX'),('^IXIC','NDX'),('^KS11','KOSPI'),('^SOX','SOX'),('^N225','NKY')]:
        q=px(symbol_key)
        for n in [1,3,6,12]:f[f'{label}_{n}m']=log_return(q,n)
    for symbol_key,label in [('EEM','EEM'),('IWM','IWM'),('QQQ','QQQ'),('^SOX','SOX'),('^KS11','KOSPI')]:
        relative=log_return(px(symbol_key),3)-log_return(px('^GSPC'),3)
        f[label+'_relative_3m']=relative;f['RS_'+label+'_z']=rolling_z(relative)
    for a,b,label in [('RSP','SPY','BREADTH'),('XLY','XLP','CYCLICAL'),('HYG','TLT','CREDIT_ROTATION')]:
        ratio=px(a)/px(b)
        for n in [3,12]:f[f'{label}_{n}m']=change(ratio,n)
    f['CONCENTRATION_3m']=change(px('QQQ')/px('RSP'),3)
    f['CONCENTRATION_DIV']=log_return(px('SPY'),3)-log_return(px('RSP'),3)
    f['QQQSPY_LEVEL_z']=rolling_z(px('QQQ')/px('SPY'))
    f['NVDA_relative_z']=rolling_z(log_return(px('NVDA'),3)-log_return(px('^GSPC'),3))
    f['TLT_3m']=log_return(px('TLT'),3)
    for a,label in [('GC=F','GOLD'),('HG=F','COPPER'),('KRW=X','KRW'),('JPY=X','JPY')]:f[label+'_3m']=log_return(px(a),3)
    f['OIL_YoY']=change(px('CL=F'),12);f['USD_YoY']=change(px('DX-Y.NYB'),12)
    f['COPPER_GOLD_d3']=(px('HG=F')/px('GC=F')).diff(3)
    f['GOLD_OIL_z']=rolling_z(px('GC=F')/px('CL=F'))
    for key,label in [('USEPUINDXD','EPU'),('GPR','GPR')]:
        q=d.mac(key).resample('ME').mean().reindex(index)
        f[label+'_z']=rolling_z(q).shift(2);f[label+'_d3']=change(q,3).shift(2)
    f['RISK_COMPOSITE']=pd.concat([rolling_z(f['VIX']),rolling_z(f['BAMLH0A0HYM2']),rolling_z(f['NFCI']),-rolling_z(f['T10Y2Y'])],axis=1).mean(axis=1,skipna=False)
    spx=d.price('^GSPC');r=spx.pct_change(fill_method=None)
    f['TAIL_SKEW']=month(r.rolling(63).skew());f['TAIL_KURT']=month(r.rolling(63).kurt())
    f['RVOL_RATIO']=month(r.rolling(21).std()/r.rolling(63).std())
    pair=pd.concat(dict(spy=d.price('SPY'),tlt=d.price('TLT')),axis=1).dropna().pct_change(fill_method=None)
    f['SPY_TLT_CORR']=month(pair.spy.rolling(63).corr(pair.tlt))
    f['SPX_DD']=(px('^GSPC')/px('^GSPC').rolling(12).max()-1)*100
    ndx=d.price('^IXIC');nr=ndx.pct_change(fill_method=None)
    f['NDX_DROP3_3M']=month((nr<-.03).astype(float).where(nr.notna()).rolling(63).sum())
    f['NDX_DROP2_1M']=month((nr<-.02).astype(float).where(nr.notna()).rolling(21).sum())
    f['NDX_WORST_1M']=month(nr.rolling(21).min()*100)
    f['NDX_BELOW50_1M']=month((ndx<ndx.rolling(50).mean()).astype(float).where(ndx.rolling(50).mean().notna()).rolling(21).mean()*100)
    q=p.reindex(index);f['OWN_VOL12']=q.pct_change(fill_method=None).rolling(12).std()*np.sqrt(12)*100
    f['OWN_MA10_DISTANCE']=(q/q.rolling(10).mean()-1)*100
    return pd.DataFrame(f,index=index).replace([np.inf,-np.inf],np.nan).iloc[12:],p

"""Public OI gamma convention, explicitly distinct from dealer inventory."""
import gzip,json
import numpy as np
import pandas as pd
from scipy.stats import norm
from .engine import number,bars,table,curve

def gamma(spot,strike,vol,t,rate):
    d1=(np.log(spot/strike)+(rate+.5*vol*vol)*t)/(vol*np.sqrt(t))
    return norm.pdf(d1)/(spot*vol*np.sqrt(t))

def option_sections(d):
    sections=[]
    for path in (d.base/'options').glob('*.json.gz'):
        raw=json.loads(gzip.decompress(path.read_bytes()));symbol=raw['symbol'];price=d.price(symbol,False)
        if not len(price):continue
        spot=float(price.iloc[-1]);f=pd.DataFrame(raw['records']);now=pd.Timestamp(raw['retrieved_at']);rate=d.mac('DGS3MO').iloc[-1]/100 if len(d.mac('DGS3MO')) else 0
        if f.empty:continue
        f['t']=[max(0,(pd.Timestamp(e+' 16:00',tz='America/New_York')-now).total_seconds())/(365.25*86400) for e in f.expiry]
        f=f[(f.openInterest>0)&(f.impliedVolatility>.01)&(f.impliedVolatility<5)&(f.t>0)&(f.contractSize=='REGULAR')].copy()
        if f.empty:continue
        sign=np.where(f.side=='call',1,-1)
        f['gex']=gamma(spot,f.strike,f.impliedVolatility,f.t,rate)*f.openInterest*100*spot**2*.01*sign/1e6
        f['strike_bucket']=(f.strike/5).round()*5;g=f.groupby('strike_bucket').gex.sum();g=g.loc[spot*.8:spot*1.2]
        sections.append(bars(symbol+' · 행사가별 부호 가정 GEX',[(f'{k:g}',v) for k,v in g.items()],'USD mn / 1%'))
        grid=np.linspace(spot*.8,spot*1.2,81);values=[]
        for s in grid:values.append(number((gamma(s,f.strike,f.impliedVolatility,f.t,rate)*f.openInterest*100*s*s*.01*sign/1e6).sum()))
        sections.append(dict(type='scatter',title=symbol+' · 가상 기초자산 가격별 감마',x_label='가상 기초자산 USD',y_label='USD mn / 1% 가격 변화',trajectory=True,points=[dict(x=number(s),y=v,name=f'Spot {s:.2f}') for s,v in zip(grid,values)]))
        calls=f.loc[f.side=='call','openInterest'].sum();puts=f.loc[f.side=='put','openInterest'].sum()
        sections.append(table(symbol+' 옵션 관측 범위',['항목','값'],[['기초자산 종가 기준',str(price.index[-1].date())],['옵션 수집 시각 UTC',raw['retrieved_at']],['만기',', '.join(raw['expiries'])],['수집 계약 수',len(raw['records'])],['유효 IV·OI 계약 수',len(f)],['Put/Call OI',number(puts/calls) if calls else None],['합계 GEX · USD mn / 1%',number(f.gex.sum())]]))
    return sections

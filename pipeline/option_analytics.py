"""Public OI gamma convention, explicitly distinct from dealer inventory."""
import numpy as np
from scipy.stats import norm
from .engine import table

def gamma(spot,strike,vol,t,rate):
    d1=(np.log(spot/strike)+(rate+.5*vol*vol)*t)/(vol*np.sqrt(t))
    return norm.pdf(d1)/(spot*vol*np.sqrt(t))

def option_sections(d):
    from .wagdog import packets
    sections=[]
    for p in packets(d):
        if p['symbol'] not in ['SPY','QQQ','IWM']:continue
        symbol=p['symbol']
        sections.append(dict(type='optionprofile',title=symbol+' · 행사가별 부호 가정 GEX',mode='gamma',**p))
        sections.append(dict(type='scatter',title=symbol+' · 가상 기초자산 가격별 감마',x_label='가상 기초자산 USD',y_label='USD bn / 1% 가격 변화',trajectory=True,points=p['curve']))
        sections.append(table(symbol+' 옵션 관측 범위',['항목','값'],[['기초자산 종가 기준',p['price_date']],['옵션 수집 시각 UTC',p['retrieved_at']],['만기',', '.join(p['expiries'])],['수집 계약 수',p['contracts']],['유효 IV·OI 계약 수',p['valid_gamma']],['Put/Call OI',p['put_call']],['합계 GEX · USD bn / 1%',p['net']]]))
    return sections

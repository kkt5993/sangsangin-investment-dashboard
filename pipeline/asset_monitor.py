"""The 21-asset reference monitor: actual indices, dated returns and MA states."""
import pandas as pd
from .catalog import MULTI
from .engine import number, clean_json

OVERRIDES={'SPY':'^GSPC','QQQ':'^IXIC','IWM':'^RUT','GLD':'GC=F'}
INSTRUMENTS=[(OVERRIDES.get(s,s),n,g) for s,n,g in MULTI]
PERIODS=[('1D',1),('1W',5),('1M',21),('3M',63),('YTD',None),('12M',252)]
ETF={'MCHI','INDA','EEM','TLT','IEF','HYG'}
UNITS={'CL=F':'USD/배럴','GC=F':'USD/트로이온스','HG=F':'USD/파운드','SI=F':'USD/트로이온스','KRW=X':'KRW/USD','JPY=X':'JPY/USD','DX-Y.NYB':'지수','BTC-USD':'USD/BTC','ETH-USD':'USD/ETH'}


def observation(prices,as_of):
    p=prices.loc[:as_of].dropna()
    p=p[p>0].sort_index()
    if not p.index.is_unique:raise ValueError('Duplicate monitor observations')
    empty=dict(date=None,price=None,ma50=None,ma200=None,signal='missing',values=[None]*6,anchors=[None]*6,observations=0,reason='가격 미확보')
    if p.empty:return empty
    date=str(p.index[-1].date());empty.update(date=date,observations=len(p))
    if (pd.Timestamp(as_of)-p.index[-1]).days>7:return dict(empty,reason='가격이 기준일보다 7일 초과 지연')
    anchors=[];values=[]
    for _,n in PERIODS:
        if n is None:
            year=p[p.index.year==pd.Timestamp(as_of).year]
            # A listing beginning midyear must not be called a full YTD observation.
            base=year.iloc[:1] if len(year) and year.index[0]<=pd.Timestamp(as_of).replace(month=1,day=10) else year.iloc[:0]
        else:base=p.iloc[-n-1:-n] if len(p)>n else p.iloc[:0]
        anchors.append(str(base.index[0].date()) if len(base) else None)
        values.append(number((p.iloc[-1]/base.iloc[0]-1)*100) if len(base) else None)
    ma50=float(p.iloc[-50:].mean()) if len(p)>=50 else None
    ma200=float(p.iloc[-200:].mean()) if len(p)>=200 else None
    signal='missing' if ma200 is None else 'long' if p.iloc[-1]>ma50>ma200 else 'short' if p.iloc[-1]<ma50<ma200 else 'neutral'
    return dict(date=date,price=number(p.iloc[-1]),ma50=number(ma50),ma200=number(ma200),signal=signal,values=values,anchors=anchors,observations=len(p),reason='200관측 이동평균 준비 중' if ma200 is None else '')


def monitor(d):
    rows=[]
    for symbol,name,group in INSTRUMENTS:
        adjusted=symbol in ETF
        item=observation(d.price(symbol,adjusted=adjusted),d.as_of)
        raw=d.price(symbol,adjusted=False).loc[:d.as_of]
        basis='분배금·분할 조정 종가' if adjusted else '연속선물 종가' if symbol.endswith('=F') else '환율' if symbol.endswith('=X') else '현물 가격' if symbol.endswith('-USD') else '가격지수'
        item.update(symbol=symbol,name=name,group=group,basis=basis,unit=UNITS.get(symbol,'USD/좌' if adjusted else '지수'),market_close=number(raw.iloc[-1]) if len(raw) and not item['reason'].startswith('가격') else None,
                    source='https://finance.yahoo.com/quote/'+symbol.replace('^','%5E').replace('=','%3D')+'/history/')
        rows.append(item)
    valid=[r for r in rows if r['values'][2] is not None]
    strongest=max(valid,key=lambda r:r['values'][2]) if valid else None
    weakest=min(valid,key=lambda r:r['values'][2]) if valid else None
    cards=[dict(label='추세 롱',value=sum(r['signal']=='long' for r in rows),detail='가격 > MA50 > MA200'),dict(label='추세 숏',value=sum(r['signal']=='short' for r in rows),detail='가격 < MA50 < MA200')]
    for label,row in [('1M 최강',strongest),('1M 최약',weakest)]:cards.append(dict(label=label,value=row['name'] if row else '미확보',detail=f"{row['values'][2]:+.1f}% · {row['date']}" if row else '유효 21관측 수익률 없음'))
    return clean_json(dict(type='assetmonitor',title='21자산 · 수익률과 추세',group='자산 모니터',as_of=d.as_of,rows=rows,cards=cards,columns=[p[0] for p in PERIODS],
        note='실제 지수·ETF·선물·환율·현물의 관측 수익률입니다. 1D/1W/1M/3M/12M은 각 1/5/21/63/252개 관측 간격(크립토는 주말 포함)이며 YTD는 올해 첫 관측 종가 대비입니다. ETF는 분배금 조정 종가, 지수는 가격지수입니다. 통화 간 환산·선물 롤/펀딩 비용은 포함하지 않습니다. 추세는 팀의 가격·MA50·MA200 정배열/역배열 규칙으로 분류합니다.'))


def views(d,obj):
    obj['sections']=[monitor(d)]+[s for s in obj['sections'] if s.get('group')!='자산 모니터']
    prefix='자산 모니터는 실제 S&P500·Nasdaq Composite·Russell2000 지수와 금 선물을 포함한21자산을 비교합니다. YTD는 원본과 같은 연초 첫 종가 대비이며, 아래 ETF 배분 모형과 구분합니다. '
    if not obj['method_note'].startswith(prefix):obj['method_note']=prefix+obj['method_note']
    gap='자산 모니터: 원본의 50/200MA 신호 세부 조건은 미공개이므로 팀 정배열/역배열을 명시했습니다. 원본 장중/시장별 기준시각과 완료 종가 사이 차이가 있으며 과거 수치의 완전 동일성을 주장하지 않습니다.'
    obj['missing']=[m for m in obj['missing'] if not m.startswith('자산 모니터:')]+[gap]

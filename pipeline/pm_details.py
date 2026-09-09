"""PM subviews: public observation gauges, rate identities and lagged TSMOM."""
import numpy as np
import pandas as pd
from .engine import *
from .macro_modules import ratio,yoy
from .catalog import MACRO

PM_GROUPS=['PM 키 게이지','금리·성장','크로스에셋 속보','CTA 시스템 트렌드','매크로 z-score','다이버전스·실적']
CTA=['SPY','EFA','EEM','TLT','IEF','GLD','DBC','USO','UUP','BTC-USD']

def monthly(s):
    return s.resample('MS').last().dropna() if len(s) else s

def align_observations(series):
    """Monthly observations matched by their economic month, not release date."""
    return pd.concat({k:monthly(s) for k,s in series.items()},axis=1).dropna()

def observation(s):
    s=s.dropna()
    return (number(s.iloc[-1]),str(s.index[-1].date())) if len(s) else (None,None)

def gauge(name,s,unit,limits,cuts,rule,reverse=False):
    value,date=observation(s)
    level=None if value is None else sum(value>=c for c in cuts)
    if reverse and level is not None:level=len(cuts)-level
    return dict(name=name,value=value,date=date,unit=unit,min=limits[0],max=limits[1],cuts=cuts,
                level=level,reverse=reverse,rule=rule)

def trend_model(prices,cost_bps=5):
    prices=prices.dropna();r=prices.pct_change(fill_method=None)
    signals=sum(np.sign(prices.pct_change(h,fill_method=None)) for h in [21,63,126,252])/4
    vol=r.rolling(63).std(ddof=1)*np.sqrt(252)
    targets=(signals*.10/vol.replace(0,np.nan)).clip(-2,2)/len(prices.columns)
    held=targets.shift(1);valid=held.notna().all(axis=1)&r.notna().all(axis=1)
    turnover=held.diff().abs().sum(axis=1)
    if valid.any():turnover.loc[valid[valid].index[0]]=held.loc[valid[valid].index[0]].abs().sum()
    pnl=(held*r).sum(axis=1)-turnover*cost_bps/10000
    return dict(returns=pnl.loc[valid],signals=signals,targets=targets,
                breadth=((signals>0).sum(axis=1)/len(prices.columns)*100).where(signals.notna().all(axis=1)))

def extend_pm(d,obj,calendar):
    sections=[]
    def add(group,*items):sections.extend(dict(s,group=group) for s in items)
    cut5=str((pd.Timestamp(d.as_of)-pd.DateOffset(years=5)).date())
    def line(title,ss,unit='%',guides=None,years=5):
        cut=str((pd.Timestamp(d.as_of)-pd.DateOffset(years=years)).date())
        return curve(title,[(n,s.loc[cut:],'left') for n,s in ss],unit,guides=guides)
    f=align_observations(dict(rate=d.mac('FEDFUNDS'),core=yoy(d.mac('PCEPILFE'))));realff=f.rate-f.core
    f=align_observations(dict(m2=d.mac('M2SL'),cpi=d.mac('CPIAUCSL')));realmoney=yoy(f.m2/f.cpi)
    claims=d.mac('ICSA').rolling(4).mean().pct_change(52,fill_method=None)*100
    key=[gauge('Sahm 실시간',d.mac('SAHMREALTIME'),'%p',[-.2,1],[.3,.5],'0.5%p 이상: 노동시장 경보'),
         gauge('Chauvet–Piger 침체확률',d.mac('RECPROUSM156N'),'%',[0,100],[10,20],'20% 이상: 모형 경보. 수정될 수 있는 스무딩 확률'),
         gauge('미국 10Y−3M',d.mac('T10Y3M'),'%p',[-2,4],[0,.5],'0 미만: 장단기 역전',True),
         gauge('실질 정책금리',realff,'%',[-4,4],[0,1],'월평균 Fed funds − 근원 PCE YoY; 1% 초과 관찰'),
         gauge('실업수당 4주 평균 YoY',claims,'%',[-20,30],[8,15],'52주 전 4주 평균 대비; 8%·15% 관찰선'),
         gauge('실질 M2 YoY',realmoney,'%',[-8,12],[0,2],'M2/CPI의 12개월 변화; 음수이면 실질 통화 감소',True),
         gauge('미국 투자등급 OAS',d.mac('BAMLC0A0CM'),'%',[0,3],[1.1,1.5],'1.1%·1.5% 관찰선; HY와 별개')]
    add(PM_GROUPS[0],dict(type='gauges',title='임계값과 최신 관측',items=key),
        line('Sahm 실시간 · 5년',[('Sahm',d.mac('SAHMREALTIME'))],'%p',[.5]),
        line('실질 연방기금금리 · 5년',[('Fed funds − Core PCE YoY',realff)],'%',[-0.,1]),
        line('미국 10년물 − 3개월물 · 5년',[('10Y−3M',d.mac('T10Y3M'))],'%p',[0]))
    cpi=yoy(d.mac('KR_CPI'));kr=align_observations(dict(rate=d.mac('KR_10Y'),cpi=cpi));krreal=kr.rate-kr.cpi
    usg=d.mac('GDP').pct_change(4,fill_method=None)*100
    # Quarterly GDP is stamped at the quarter end for visual alignment. No
    # forward fill into future months and no use of this series in a backtest.
    usg.index=usg.index.to_period('Q').to_timestamp(how='end').normalize()
    krg=d.mac('KR_REAL_GDP').pct_change(4,fill_method=None)*100
    krg.index=krg.index.to_period('Q').to_timestamp(how='end').normalize()
    def rg(g,rate,inflation=None):
        q=rate.resample('QE').mean();f=pd.concat(dict(g=g,r=q),axis=1).dropna()
        if inflation is not None:
            f['pi']=inflation.resample('QE').mean().reindex(f.index);f=f.dropna();f.g=f.g+f.pi
        return f.loc[:d.as_of]
    us=rg(usg,d.mac('DGS10'));kor=rg(krg,d.mac('KR_10Y'),cpi)
    rate_gauges=[gauge('미국 10Y 실질금리',d.mac('DFII10'),'%',[-2,4],[0,2],'TIPS 시장금리; 2% 관찰선'),
        gauge('미국 10Y BEI',d.mac('T10YIE'),'%',[0,4],[1.8,2.5],'명목 국채와 TIPS 금리 차이; 기대물가 외 프리미엄 포함'),
        gauge('미국 명목 g−r',us.g-us.r,'%p',[-5,8],[0,2],'분기 명목 GDP YoY − 분기평균 국채10Y',True),
        gauge('한국 CPI YoY',cpi,'%',[-1,6],[1.5,3],'실현 물가상승률'),
        gauge('한국 실질금리 근사',krreal,'%',[-3,5],[0,2.5],'월평균 국고10Y − 당월 CPI YoY'),
        gauge('한국 명목 g−r 근사',kor.g-kor.r,'%p',[-5,8],[0,2],'실질 GDP YoY + 분기평균 CPI YoY − 국고10Y',True)]
    add(PM_GROUPS[1],dict(type='gauges',title='금리·성장 관측',items=rate_gauges),
        line('미국 금리 분해 · 10Y',[('명목 국채10Y',d.mac('DGS10')),('실질 TIPS10Y',d.mac('DFII10')),('BEI10Y',d.mac('T10YIE'))]),
        line('미국 명목금리 vs 명목성장',[('국채10Y 분기평균',us.r),('GDP YoY',us.g)],'%', [0]),
        line('한국 금리 분해 · 10Y',[('명목 국고10Y',kr.rate),('실질금리 근사',krreal),('CPI YoY',kr.cpi)]),
        line('한국 명목금리 vs 명목성장 근사',[('국고10Y 분기평균',kor.r),('실질GDP YoY+CPI YoY',kor.g)],'%', [0]))
    pairs=[('SPY/TLT','SPY','TLT'),('XLY/XLP','XLY','XLP'),('SOXX/SPY','SOXX','SPY'),('HYG/LQD','HYG','LQD')]
    components={n:ratio(d,a,b) for n,a,b in pairs};components['구리/금']=ratio(d,'HG=F','GC=F')
    components['VIX']=d.price('^VIX',False);components['달러']=d.price('DX-Y.NYB',False)
    z=pd.concat({n:zscore(s,252)*(-1 if n in ['VIX','달러'] else 1) for n,s in components.items()},axis=1).dropna()
    add(PM_GROUPS[2],curve('리스크선호 종합 · 7계열 z',[('동일가중 z',z.mean(axis=1).tail(180),'left')],'z',guides=[0]),
        table('복합지표 구성과 단기 방향',['계열','원단위 최신값','20거래일 변화 %','252D z · 위험선호 부호'],[[n,observation(s)[0],ret(s,20),observation(z[n])[0]] for n,s in components.items()]))
    for n,a,b in pairs:add(PM_GROUPS[2],curve(n+' · 180거래일',[(n,components[n].tail(180),'left')],'가격비'))
    prices=pd.concat({s:d.price(s) for s in CTA},axis=1).reindex(d.price('SPY').index).dropna()
    model=trend_model(prices);r=model['returns'];equity=(1+r).cumprod();cut3=str((pd.Timestamp(d.as_of)-pd.DateOffset(years=3)).date())
    add(PM_GROUPS[3],curve('CTA 시스템 추세 · 누적 자산배수',[('비용 차감 TSMOM',equity.loc[cut3:],'left')],'전략 시작=1'),
        curve('트렌드 확산도 · 상승 추세 자산 비율',[('양의 합성신호 비중',model['breadth'].loc[cut3:],'left')],'%',guides=[20,50,80],limits=[0,100]),
        table('10자산 현재 신호·다음 세션 목표',['자산','합성신호 −1~1','포지션','12M 수익 %','목표 NAV %'],[[s,number(model['signals'][s].iloc[-1]),'롱' if model['targets'][s].iloc[-1]>0 else '숏' if model['targets'][s].iloc[-1]<0 else '중립',ret(prices[s],252),number(model['targets'][s].iloc[-1]*100)] for s in CTA]),
        table('CTA 역사 모형 성과',['첫 수익일','마지막 수익일','CAGR %','변동성 %','Sharpe rf=0','MDD %'],[[str(r.index[0].date()),str(r.index[-1].date()),*[performance(r)[k] for k in ['cagr','vol','sharpe','mdd']]]]))
    macros={'10Y−2Y':(d.mac('T10Y2Y'),'%p',252),'MOVE':(d.price('^MOVE',False),'index',252),'Fed RRP':(d.mac('RRPONTSYD'),'USD bn',252),
        'M2 YoY':(yoy(d.mac('M2SL')),'%',36),'DXY':(d.price('DX-Y.NYB',False),'index',252),'USD/KRW':(d.price('KRW=X',False),'KRW/USD',252),
        '금/원유':(ratio(d,'GC=F','CL=F'),'가격비',252),'구리/금':(ratio(d,'HG=F','GC=F'),'가격비',252),
        'VIX/VIX3M':(ratio(d,'^VIX','^VIX3M'),'가격비',252),'HY OAS':(d.mac('BAMLH0A0HYM2'),'%',252),'GPR':(d.mac('GPR'),'index',36)}
    rows=[]
    for name,(s,u,w) in macros.items():
        value,date=observation(s);tail=s.dropna().tail(w);zv=observation(zscore(s,w))[0]
        rows.append([name,value,u,date,zv,number(tail.le(value).mean()*100) if value is not None and len(tail)==w else None])
    add(PM_GROUPS[4],table('매크로 분포 위치',['지표','값','단위','관측일','z','백분위'],rows),
        bars('지표별 z · 일간252/월간36관측',[(a[0],a[4]) for a in rows],'σ'))
    divs=[('금–BTC','GC=F','BTC-USD'),('엔화–Nikkei','JPY=X','^N225'),('Nasdaq–반도체','QQQ','SOXX'),('원달러–삼성전자','KRW=X','005930.KS'),('SPY–TLT','SPY','TLT'),('금–은','GC=F','SI=F'),('달러–구리','DX-Y.NYB','HG=F'),('은행–국채10Y','KBE','^TNX')]
    divrows=[]
    for n,a,b in divs:
        f=pd.concat(dict(a=d.price(a),b=d.price(b)),axis=1).dropna();returns=f.pct_change(fill_method=None)
        corr=returns.a.rolling(60).corr(returns.b);zz=zscore(f.a/f.b,252)
        divrows.append([n,observation(corr)[0],observation(zz)[0],observation(f.a)[1]])
    add(PM_GROUPS[5],table('교차자산 다이버전스',['페어','60D 수익률 상관','가격비 252D z','공통 관측일'],divrows),
        table('실적 달력 · 제공처 예정 포함',['종목','발표/예정 시각 ET','EPS 추정','실제 EPS','서프라이즈 %','상태'],sorted(calendar,key=lambda a:a[1])))
    for s in obj['sections']:s['group']='기초 매크로 시계열'
    obj['sections']=sections+obj['sections']
    obj['method_note']='PM 6개 세부 화면: 임계 게이지·금리/성장·7계열 위험선호·10자산 CTA·z 분포·다이버전스/실적. 금리·GDP는 관측기간을 맞추며 한국 명목성장은 실질 GDP YoY+CPI 근사입니다. 게이지는 관찰 규칙이며 침체 확률이나 수익 보장이 아닙니다. CTA는 21/63/126/252일 수익 부호 평균, 63일 변동성에 자산별10% 타깃·레버리지2배 상한·동일 평균을 적용하고 하루 지연한 비중과 5bp 회전비용을 사용합니다. ETF 조정가격·USD 수익률 기준이며 현금 이자·차입/펀딩 비용은 미반영입니다.'
    obj['missing']=['원본이 공개하지 않은 CTA 변동성 창·비용·레버리지 및 z 준비 기간은 위 팀 설정으로 고정했습니다. 과거 실시간 거시 빈티지와 실제 CTA 계좌 포지션은 아닙니다.','실적 발표 종목별 ATM 스트래들 내재 변동폭은 개별주 옵션 연결 후 추가합니다.']
    unavailable=[a[0] for a in rows if a[1] is None]
    if unavailable:obj['missing'].append('수집 대기 지표: '+', '.join(unavailable))
    obj['cards']=[('PM 세부 화면',6),('CTA 자산',len(CTA)),('게이지',len(key)+len(rate_gauges))]

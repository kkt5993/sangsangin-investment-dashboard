"""Macro regimes and risk monitors with explicit units and observation dates."""
import numpy as np
import pandas as pd
from scipy.stats import kendalltau
from .engine import *
from .catalog import MACRO

def ratio(d,a,b):
    f=pd.concat([d.price(a,False),d.price(b,False)],axis=1).dropna()
    return f.iloc[:,0]/f.iloc[:,1] if len(f) else pd.Series(dtype=float)

def yoy(s):return s.pct_change(12,fill_method=None)*100

def last(s):return number(s.iloc[-1]) if len(s.dropna()) else None

def regime_frame(d,market):
    if market=='US':
        growth=yoy(d.mac('INDPRO'));inflation=yoy(d.mac('CPIAUCSL'))
    else:
        growth=d.mac('KR_COIN')-100;inflation=yoy(d.mac('KR_CPI'))
    f=pd.concat(dict(growth=growth,inflation=inflation),axis=1).dropna();f['g']=f.growth.diff(3);f['i']=f.inflation.diff(3)
    f=f.dropna();f['regime']=np.select([(f.g>=0)&(f.i<0),(f.g>=0)&(f.i>=0),(f.g<0)&(f.i>=0)],['회복','확장·리플레이션','스태그플레이션'],default='둔화·디스인플레')
    return f

def regimes(d):
    sections=[];cards=[]
    for market,symbol in [('US','^GSPC'),('KR','^KS11')]:
        f=regime_frame(d,market);p=d.price(symbol,False);weekly=observed_resample(p,'W-FRI');r=rsi(weekly)
        if len(f):
            cards.append((market+' 경제국면',f.regime.iloc[-1]+' · '+str(f.index[-1].date())))
            sections.append(dict(type='scatter',title=market+' · 성장×물가 방향 (최근 36개월)',group=market,x_label='성장 지표 3M 변화 (%p / 지수p)',y_label='CPI YoY 3M 변화 (%p)',trajectory=True,
                points=[dict(x=number(row.g),y=number(row.i),name=str(t.date())+' '+row.regime,value=i) for i,(t,row) in enumerate(f.tail(36).iterrows())]))
            sections.append(table(market+' 월별 경제국면',['관측월','성장 지표','CPI YoY %','국면'],[[str(t.date()),number(row.growth),number(row.inflation),row.regime] for t,row in f.tail(36).iloc[::-1].iterrows()]))
            transitions=pd.crosstab(f.regime.shift(1),f.regime,normalize='index')*100
            sections.append(heat(market+' 국면 전이 · 현재 빈티지 역사',['회복','확장·리플레이션','스태그플레이션','둔화·디스인플레'],[dict(name=idx,group=market,values=[number(row.get(c,0)) for c in ['회복','확장·리플레이션','스태그플레이션','둔화·디스인플레']]) for idx,row in transitions.iterrows()]))
        if len(p):cards.append((market+' 시장 추세','상승' if p.iloc[-1]>p.iloc[-200:].mean() else '하락'))
        sections.append(curve(market+' 주봉 RSI14 · 지수', [('주봉 RSI14',r.tail(156),'left'),('지수',weekly.tail(156),'right')],'RSI 0–100','가격지수',[30,70],[0,100]))
    cutoff=str(pd.Timestamp(d.as_of)-pd.DateOffset(years=3))[:10]
    for title,s,unit in [('미국 10Y−2Y',d.mac('T10Y2Y'),'%p'),('Chicago Fed NFCI',d.mac('NFCI'),'표준화 지수'),('구리 / 금',ratio(d,'HG=F','GLD'),'가격비'),('산업재 / 유틸리티',ratio(d,'XLI','XLU'),'가격비'),('하이일드 / 장기국채',ratio(d,'HYG','TLT'),'가격비'),('한국 10Y−3Y',d.mac('KR_10Y')-d.mac('KR_3Y'),'%p')]:
        sections.append(curve(title,[(title,s.loc[cutoff:],'left')],unit,guides=[0] if unit!='가격비' else []))
    return module('regime',d.as_of,'미국 성장=산업생산 YoY, 한국 성장=동행지수 순환변동치−100. 성장·CPI YoY의 3개월 방향으로 4국면을 구분합니다. 발표된 최신 빈티지의 관측월이며 과거 실시간 판정 기록은 아닙니다. 국면 전이 표는 관측빈도입니다.',sections,cards,missing=['원본의 경기모델 가중치·Soros 복합점수·밸류에이션 모델은 별도 검증이 필요합니다.'])

def csd_score(p):
    r=p.pct_change().dropna().tail(252)
    if len(r)<126:return None,{}
    indicators={'분산':r.rolling(21).var(),'자기상관':r.rolling(21).apply(lambda a:pd.Series(a).autocorr(1),raw=True),'왜도 절댓값':r.rolling(21).skew().abs()}
    values={}
    for name,s in indicators.items():
        a=s.dropna().tail(63);values[name]=number(kendalltau(np.arange(len(a)),a).statistic) if len(a)>20 else None
    good=[v for v in values.values() if v is not None]
    return number(50*(1+np.mean(good))) if good else None,values

def risk(d):
    sections=[];cards=[]
    for market,s in [('US','^GSPC'),('KR','^KS11')]:
        p=d.price(s,False);r=p.pct_change();score,details=csd_score(p)
        if len(p)<253:continue
        cards.extend([(market+' CSD 점수',score),(market+' 실현변동성 21D %',number(r.tail(21).std()*np.sqrt(252)*100))])
        sections.extend([table(market+' 조기경보',['지표','Kendall 추세 τ'],[[k,v] for k,v in details.items()]),
            curve(market+' 변동성 · 시장', [('21D 연환산 변동성',r.rolling(21).std()*np.sqrt(252)*100,'left'),('지수',p,'right')],'변동성 %','가격지수')])
    vix=d.price('^VIX',False);vix3=d.price('^VIX3M',False)
    sections.extend([curve('VIX 기간구조', [('VIX',vix.tail(756),'left'),('VIX3M',vix3.tail(756),'left')],'변동성 지수'),
        curve('SKEW · 하이일드 스프레드', [('SKEW',d.price('^SKEW',False).tail(756),'left'),('HY OAS',d.mac('BAMLH0A0HYM2').tail(756),'right')],'SKEW','OAS %'),
        curve('쏠림 · 동일가중/시총가중', [('RSP/SPY',ratio(d,'RSP','SPY').tail(756),'left')],'가격비'),
        curve('국내 신용 스프레드', [('AA− 회사채−국고채 3Y',(d.mac('KR_AA')-d.mac('KR_3Y')).tail(756),'left')],'%p')])
    from .option_analytics import option_sections
    sections+=option_sections(d)
    return module('risk',d.as_of,'US·KR 조기경보와 변동성·신용·쏠림을 계산합니다. CSD는 21일 분산·자기상관·왜도의 최근 63일 Kendall 추세 평균을 0–100으로 바꾼 진단점수입니다. 옵션은 수집 당시 현물·OI·IV로 계산한 콜 + / 풋 − 부호 가정 GEX입니다. ETF별 원장에 7~50일·행사가 ±15% 전체 제공 범위와 기존 제한만기를 구분합니다. 현재 종가로 과거 옵션을 재평가하지 않으며 실제 딜러 보유 포지션이 아닙니다.',sections,cards,
        missing=['전체 만기 딜러 포지션 및 레버리지 ETF 실제 순유입 원장은 연결되지 않았습니다. 옵션 IV를 고정한 가격 시나리오는 변동성 곡면 변화를 반영하지 않습니다.','원본 CSD 임계값의 예측력, 실제 포트폴리오 스트레스와 회복력은 미검증입니다.'])

def weekend(d):
    specs=[('미국 물가', [('CPI YoY',yoy(d.mac('CPIAUCSL')),'left'),('Core PCE YoY',yoy(d.mac('PCEPILFE')),'left')],'%',''),
        ('한국 물가', [('CPI YoY',yoy(d.mac('KR_CPI')),'left')],'%',''),
        ('미국 성장', [('산업생산 YoY',yoy(d.mac('INDPRO')),'left'),('실업률',d.mac('UNRATE'),'right')],'%','%'),
        ('한국 경기', [('선행 순환변동',d.mac('KR_LEAD'),'left'),('동행 순환변동',d.mac('KR_COIN'),'left')],'지수',''),
        ('정책금리', [('Fed funds',d.mac('FEDFUNDS'),'left'),('BOK',d.mac('KR_BASE'),'left')],'%',''),
        ('미국 장단기금리', [('10Y',d.mac('DGS10'),'left'),('2Y',d.mac('DGS2'),'left'),('3M',d.mac('DGS3MO'),'left')],'%',''),
        ('한국 시장금리', [('10Y',d.mac('KR_10Y'),'left'),('3Y',d.mac('KR_3Y'),'left'),('AA−',d.mac('KR_AA'),'left')],'%',''),
        ('실질금리 · 기대인플레', [('10Y TIPS',d.mac('DFII10'),'left'),('10Y BEI',d.mac('T10YIE'),'left')],'%',''),
        ('미국 유동성', [('M2 YoY',yoy(d.mac('M2SL')),'left'),('연준 자산',d.mac('WALCL')/1e6,'right')],'%','USD trillion'),
        ('금융여건 · 신용', [('NFCI',d.mac('NFCI'),'left'),('HY OAS',d.mac('BAMLH0A0HYM2'),'right')],'z','%'),
        ('미국 경기위험', [('Sahm',d.mac('SAHMREALTIME'),'left'),('침체확률',d.mac('RECPROUSM156N'),'right')],'%p','%'),
        ('고용', [('신규 실업수당',d.mac('ICSA')/1000,'left'),('고용 YoY',yoy(d.mac('PAYEMS')),'right')],'천명','%'),
        ('한국 수출 · 환율', [('수출 YoY',yoy(d.mac('KR_EXPORT')),'left'),('USD/KRW',d.price('KRW=X',False),'right')],'%','KRW/USD'),
        ('Risk On / Off', [('HYG/TLT',ratio(d,'HYG','TLT'),'left'),('XLI/XLU',ratio(d,'XLI','XLU'),'right')],'가격비','가격비')]
    cutoff=str(pd.Timestamp(d.as_of)-pd.DateOffset(years=5))[:10]
    sections=[curve(title,[(n,s.loc[cutoff:],a) for n,s,a in series],left,right) for title,series,left,right in specs]
    rows=[]
    for key,s in d.macro.items():
        if not len(s):continue
        rows.append([key,MACRO.get(key,(key,'ECOS 원단위',''))[0],str(s.index[-1].date()),last(s)])
    sections.append(table('발표 데이터 최신 관측일',['계열','지표','관측일','원단위 값'],rows))
    return module('pm_weekend',d.as_of,'5년 시계열 14개 패널. 월간 YoY는 월간 관측치의 12개월 변화율이며, 주간·일간 데이터를 12개 관측치 변화율로 잘못 계산하지 않습니다. 모든 차트에 서로 다른 단위·축을 표시합니다.',sections,[('매크로 계열',len(rows)),('패널',14)],missing=['원본의 CTA 추정 포지션·매매자금 예측은 실제 포지션 데이터가 없어 제외했습니다.'])

def geoecon(d):
    cutoff=str(pd.Timestamp(d.as_of)-pd.DateOffset(years=3))[:10]
    specs=[('정책 불확실성 · VIX',[('미국 EPU',d.mac('USEPUINDXD'),'left'),('VIX',d.price('^VIX',False),'right')],'EPU index','VIX'),
        ('달러 · 원유',[('DXY',d.price('DX-Y.NYB',False),'left'),('WTI',d.price('CL=F',False),'right')],'DXY','USD/barrel'),
        ('금리 · 신용',[('미국 10Y',d.mac('DGS10'),'left'),('HY OAS',d.mac('BAMLH0A0HYM2'),'right')],'%','%')]
    return module('geoecon',d.as_of,'정책 불확실성과 시장 반응을 분리해 비교합니다. 원본의 EPU·VIX, DXY·원유, 금리·신용 3개 이중축 구조입니다.',[curve(t,[(n,s.loc[cutoff:],a) for n,s,a in ss],l,r) for t,ss,l,r in specs],
        missing=['지정학 뉴스 NLP·이벤트별 인과 판정은 텍스트 수집과 검증을 별도로 연결해야 합니다. EPU는 뉴스 감성이나 전쟁 확률이 아닙니다.'])

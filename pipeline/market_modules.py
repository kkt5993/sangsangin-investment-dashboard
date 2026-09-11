"""Price and official-universe modules, entirely reproducible from local caches."""
import numpy as np
import pandas as pd
from .engine import *
from .catalog import MULTI,SCAN_EXTRA,INDICES,DYNAMICS_STOCKS,etfs
from .patterns import candidates
from .analytics import rs_percentiles
from .cache import valid_ohlc

def rankings(d,universes=None):
    out={}
    for market,key in universes or [('KR','kr_largecap'),('US','us_largecap'),('KOSPI200','kospi200')]:
        members=d.members.get(key,{}).get('members',[]);rows=[];excluded=[]
        for m in members:
            a=d.stats(m['symbol']);p=d.price(m['symbol'])
            if not a or (pd.Timestamp(d.as_of)-p.index[-1]).days>7 or any(a[k] is None for k in ['r1w','r1m','r3m','r6m','r1y']):
                excluded.append(dict(symbol=m['symbol'],name=m['name'],observations=len(p),reason='252일 수익률 계산을 위한 253개 가격 부족' if len(p) else '최근 유효 가격 미수집'))
                continue
            a.update(name=m['name'],sector=m['sector'],score=.4*a['r3m']+.2*a['r6m']+.2*ret(p,189)+.2*a['r1y']);rows.append(a)
        scores=pd.Series([r['score'] for r in rows],dtype=float);rank=rs_percentiles(scores)
        for i,r in enumerate(rows):r['rs']=number(rank.iloc[i])
        rows.sort(key=lambda r:r['rs'],reverse=True)
        ordered=sorted(rows,key=lambda r:r['r1w'],reverse=True)
        weak=sorted(rows,key=lambda r:r['r1w'])[:8]
        out[market]=dict(universe=key,expected=len(members),available=len(rows),excluded=excluded,membership_as_of=d.members.get(key,{}).get('as_of'),source=d.members.get(key,{}).get('source'),leaders=rows[:15],strong=ordered[:8],weak=weak[:6],weak_table=weak,rows=rows)
    return out

def etf_monitor(d):
    from .etf_details import monitor
    return monitor(d)

def multiasset(d):
    rows=[];scans=[]
    for s,n,g in MULTI+SCAN_EXTRA:
        a=d.stats(s)
        if not a:continue
        a.update(name=n,group=g)
        tag='중립'
        if a['price']>a['ma20']>a['ma50']>a['ma200']:tag='정배열'
        if a['high52']>=-1:tag='52주 신고가 근접'
        if a['rsi']>75:tag='과열'
        if a['price']<a['ma50']<a['ma200']:tag='하락 추세'
        p=d.price(s)
        if (p.rolling(50).mean()-p.rolling(200).mean()).iloc[-6]<0<a['ma50']-a['ma200']:tag='골든크로스'
        if p.pct_change().iloc[-21:].std()<.55*p.pct_change().iloc[-126:].std():tag='변동성 수축'
        if a['r1m']>5 and a['r6m']<0:tag='바닥 반등'
        a['signal']=tag;scans.append(a)
        if (s,n,g) in MULTI:rows.append(a)
    cols=['r1d','r1w','r1m','r3m','ytd','r1y']
    sections=[bars('멀티에셋 · 1M 수익률',[(a['name'],a['r1m']) for a in sorted(rows,key=lambda a:a['r1m'],reverse=True)]),
        heat('21개 자산 · 기간별 수익률',['1D %','1W %','1M %','3M %','YTD %','1Y %'],[dict(name=a['name'],group=a['group'],values=[a[c] for c in cols]) for a in rows]),
        table('37개 자산 패턴 스캐너',['자산','분류','신호','RSI14','1M %','3M %','52주 고점 대비 %','기준일'],[[a['name'],a['group'],a['signal'],a['rsi'],a['r1m'],a['r3m'],a['high52'],a['as_of']] for a in scans])]
    # A transparent tradable, USD ETF baseline. No futures rolls or yield-index returns.
    symbols=['SPY','EFA','EEM','IEF','TLT','GLD','HYG','DBC'];p=pd.concat({s:d.price(s) for s in symbols},axis=1).dropna()
    if len(p)>253:
        r=p.pct_change(fill_method=None);inv=1/r.rolling(63).std().replace(0,np.nan);w=inv.div(inv.sum(axis=1),axis=0)
        # Monthly rebalance using information from the previous completed session.
        br=monthly_portfolio(r,w,5)
        sections += [bars('리스크 패리티 기준 비중',[(s,100*w.iloc[-1][s]) for s in symbols]),curve('월 리밸런싱 · 기준 포트폴리오와 SPY', [('Inverse-volatility',(1+br).cumprod()*100,'left'),('SPY',(1+r.SPY.reindex(br.index)).cumprod()*100,'left')],'시작=100'),table('기준 포트폴리오 성과',['CAGR %','변동성 %','Sharpe (rf=0)','MDD %'],[list(performance(br).values())[:4]])]
    return module('multiasset',d.as_of,'21자산 수익률·37자산 스캐너를 계산합니다. FX는 표시 환율의 변화율, 선물은 제공처 연속선물 가격입니다. 자산배분은 월 리밸런싱 역변동성 기준모형(63일, 편도 5bp)입니다.',sections,[('자산',len(rows)),('스캐너',len(scans))],missing=['원본의 ML 자산배분 모델·가중치가 없어 기준모형을 구분해 제공합니다.'])

def dynamics(d):
    from .dynamics_model import build
    return build(d)


def candle_section(d,s,name,group=None,annotation=None):
    f=d.frames.get(s);p=d.price(s)
    if f is None or not all(k in f for k in ['open','high','low','volume']):return None
    valid=valid_ohlc(f);excluded=[str(t.date()) for t in f.index[~valid]];f=f.loc[valid]
    if f.empty:return None
    if excluded:annotation=(annotation or '')+' · OHLC 불일치 일봉 제외: '+', '.join(excluded)+' · 종가 기준 '+str(p.index[-1].date())+' / 캔들·기술 기준 '+str(f.index[-1].date())
    allf=f.copy();ratio=allf.adjusted_close/allf.close
    for k in ['open','high','low','close']:allf[k]=allf[k]*ratio
    weekly=allf.resample('W-FRI').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().tail(52)
    # Include the current partial week at the actual last observation date.
    if len(weekly) and weekly.index[-1]>allf.index[-1]:weekly=weekly.rename(index={weekly.index[-1]:allf.index[-1]})
    f=f.tail(120).copy();ratio=f.adjusted_close/f.close
    candles=[[str(t.date()),*[number(row[k]*ratio.loc[t]) for k in ['open','high','low','close']],number(row.volume)] for t,row in f.iterrows()]
    return dict(type='candles',title=name,group=group,candles=candles,annotation=annotation,excluded_bars=excluded,bar_as_of=str(f.index[-1].date()),
        weekly=[[str(t.date()),*[number(row[k]) for k in ['open','high','low','close','volume']]] for t,row in weekly.iterrows()],
        lines=[dict(name=f'MA{n}',points=points(p.rolling(n).mean().reindex(f.index))) for n in [20,50,200]])

def watch(d,ranks):
    from .technical_scan import scan
    picks=[]
    for market in ['KR','US']:
        rows=ranks[market]['rows'];bull=[]
        for a in rows:
            patterns=candidates(d.price(a['symbol']),d.as_of)
            if patterns:bull.append(dict(a,pattern=patterns[0]))
        bull.sort(key=lambda a:(a['pattern']['confirmed'],a['pattern']['score'],a['rs']),reverse=True)
        bear=[a for a in rows if a['price']<a['ma50']<a['ma200'] and a['r1m']<0]
        for label,items,n in [('상승 패턴',bull,6),('약세 추세',sorted(bear,key=lambda a:a['r1m']),4)]:
            for a in items[:n]:
                pattern=a.get('pattern');title=(pattern['name']+' · ' if pattern else '하락 추세 · ')+a['name']
                note=f"RS {a['rs']:.1f} · RSI {a['rsi']:.1f} · 1M {a['r1m']:.1f}%"
                if pattern:note+=' · '+pattern['evidence']+f" · 기하 적합도 {pattern['score']:.1f}/100 · "+('종가 저항 돌파' if pattern['confirmed'] else '저항 돌파 미확인')
                c=candle_section(d,a['symbol'],title,market+' · '+label,note)
                if c:
                    tech=scan(d.frames[a['symbol']]);c['technical']={k:tech[k] for k in ['score','available','adx','plus_di','minus_di','atr','ma_stars']}
                    c['annotation']+=' · ADX14 '+str(tech['adx'])+' · MA '+str(tech['ma_stars'])+'/4 · 12지표 합계 '+str(tech['score'])
                    if pattern:c['pattern']=pattern
                    picks.append(c)
    return module('watch',d.as_of,'공식 대형주에서 W바닥·컵앤핸들·상승깃발·역헤드앤숄더·상승삼각형을 명시한 수치 규칙으로 선별합니다. 피벗은 좌우 3봉이 확보된 과거 종가로 확인하며 미확인 돌파를 구분합니다. 적합도는 기하 조건 점수로 성공확률이 아닙니다. 약세는 가격<MA50<MA200 및 1M<0입니다. 120일·52주 조정 OHLC, 일봉 MA20/50/200, 거래량을 제공합니다.',picks,[('선별 종목',len(picks)),('기하 패턴 종류',5)],missing=['ADX14·±DI·ATR·MA4조건·12개 지표 합계를 추가했습니다. 원본의 미공개 패턴 판정·신뢰도·개별 임계 설정과 수치 동등성은 미검증입니다. 현재 후보의 향후 수익 성과를 의미하지 않습니다.'])

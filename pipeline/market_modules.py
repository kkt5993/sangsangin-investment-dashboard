"""Price and official-universe modules, entirely reproducible from local caches."""
import numpy as np
import pandas as pd
from .engine import *
from .catalog import MULTI,SCAN_EXTRA,INDICES,DYNAMICS_STOCKS,etfs
from .patterns import candidates

def rankings(d):
    out={}
    for market,key in [('KR','kr_largecap'),('US','us_largecap'),('KOSPI200','kospi200')]:
        members=d.members.get(key,{}).get('members',[]);rows=[];excluded=[]
        for m in members:
            a=d.stats(m['symbol']);p=d.price(m['symbol'])
            if not a or any(a[k] is None for k in ['r1w','r1m','r3m','r6m','r1y']):
                excluded.append(dict(symbol=m['symbol'],name=m['name'],observations=len(p),reason='252일 수익률 계산을 위한 253개 가격 부족' if len(p) else '최근 유효 가격 미수집'))
                continue
            a.update(name=m['name'],sector=m['sector'],score=.4*a['r3m']+.2*a['r6m']+.2*ret(p,189)+.2*a['r1y']);rows.append(a)
        scores=pd.Series([r['score'] for r in rows]);rank=scores.rank(method='average',pct=True)*98+1
        for i,r in enumerate(rows):r['rs']=number(rank.iloc[i])
        rows.sort(key=lambda r:r['rs'],reverse=True)
        ordered=sorted(rows,key=lambda r:r['r1w'],reverse=True)
        out[market]=dict(universe=key,expected=len(members),available=len(rows),excluded=excluded,membership_as_of=d.members.get(key,{}).get('as_of'),source=d.members.get(key,{}).get('source'),leaders=rows[:15],strong=ordered[:8],weak=ordered[-6:],rows=rows)
    return out

def etf_monitor(d):
    sections=[];counts=0
    for category in etfs():
        rows=[]
        for item in category['items']:
            s=item['symbol'];st=d.stats(s);f=d.frames.get(s)
            if not st:continue
            cutoff=f.index[-1]-pd.DateOffset(years=1)
            div=f.loc[f.index>cutoff,'dividend'];div=div[div>0]
            yield_=number(div.sum()/f.close.iloc[-1]*100)
            # Yahoo action cash amounts are already adjusted for splits: do not apply splits twice.
            rows.append(dict(name=item['name'],symbol=s,returns=[st['r1m'],st['r3m'],st['ytd'],st['r1y']],yield_pct=yield_,payments=len(div),monthly_per_10m=number(10_000_000*yield_/1200),as_of=st['as_of']))
        title=category.get('name') or category.get('title') or category.get('id');counts+=len(rows)
        sections.append(dict(type='etf',title=title,group=title,rows=rows))
    return module('etfmon',d.as_of,'9개 ETF 분류. 수익률은 분배금 조정종가, 분배율은 최근 12개월 실제 지급액/현재 종가입니다. 월 현금흐름은 세전 단순 월평균이며 미래 지급액이 아닙니다. 레버리지·옵션 ETF도 같은 정의를 적용합니다.',sections,
        [('관측 ETF 위치',str(counts)),('분류',str(len(sections))),('USD/KRW',number(d.price('KRW=X',False).iloc[-1]) if len(d.price('KRW=X')) else None)],'operational')

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
    sections=[]
    for s,n in [(s,n) for _,s,n in INDICES]+DYNAMICS_STOCKS:
        p=d.price(s);r=p.pct_change(fill_method=None)
        if len(p)<300:continue
        vol=r.rolling(21).std(ddof=0);beta=r.rolling(21).mean()/vol*np.sqrt(252);alpha=beta-beta.shift(5)
        tau=r.diff().abs().rolling(21).std(ddof=0)/r.abs().rolling(21).mean()
        a=expanding_z(tau)-.5*expanding_z(beta)-.5*expanding_z(alpha)
        risk=100/(1+np.exp(-a.clip(-50,50)));exposure=(.15/(vol*np.sqrt(252))).clip(0,1.5)*(1-.6*risk/100)
        f=pd.DataFrame(dict(beta=beta,alpha=alpha,tau=tau,risk=risk,exposure=exposure,px=p)).dropna()
        if f.empty:continue
        m=observed_resample(f).tail(144);ph=m.tail(60)
        dates=ph.index;windows=[5,10,20,40,60,90,120,180]
        surf=observed_resample(pd.DataFrame({w:r.rolling(w).std(ddof=0)*np.sqrt(252)*100 for w in windows})).reindex(dates)
        b=r.loc[f.index];model=exposure.shift(1).loc[f.index]*b;model=model.dropna();b=b.reindex(model.index)
        section=dict(type='dynamics',title=n,group=n,symbol=s,current=clean_json(f.iloc[-1].to_dict()),date=str(f.index[-1].date()),
            surface=dict(windows=windows,dates=[str(x.date()) for x in dates],values=surf.values.tolist()),
            phase=[dict(x=number(x.beta),y=number(x.tau),value=number(x.risk),name=str(t.date())) for t,x in ph.iterrows()],
            charts=[curve('붕괴 취약성 · 가격', [('위험 점수',ph.risk,'left'),('가격',ph.px,'right')],'0–100','가격',[65],[0,100]),
                    curve('노출 조절 vs Buy & Hold', [('노출 조절',observed_resample((1+model).cumprod())*100,'left'),('Buy & Hold',observed_resample((1+b).cumprod())*100,'left')],'시작=100')],
            stats=[dict(name='노출 조절',**performance(model)),dict(name='Buy & Hold',**performance(b))])
        sections.append(section)
    return module('dynamics',d.as_of,'공개된 β·α·τ·취약성·노출 공식을 구현했습니다. 21일·5일·expanding 252일, 모집단 표준편차를 사용합니다. 표면은 8개 기간의 연환산 변동성, 위상공간은 β×τ입니다. 백테스트는 전일 노출을 적용하며 비용·차입금리는 0입니다. 취약성은 통계적 점수이며 붕괴 확률이 아닙니다.',sections,[('대상',len(sections)),('표면 창',8)],'operational')

def candle_section(d,s,name,group=None,annotation=None):
    f=d.frames.get(s);p=d.price(s)
    if f is None or not all(k in f for k in ['open','high','low','volume']):return None
    allf=f.copy();ratio=allf.adjusted_close/allf.close
    for k in ['open','high','low','close']:allf[k]=allf[k]*ratio
    weekly=allf.resample('W-FRI').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().tail(52)
    # Include the current partial week at the actual last observation date.
    if len(weekly) and weekly.index[-1]>allf.index[-1]:weekly=weekly.rename(index={weekly.index[-1]:allf.index[-1]})
    f=f.tail(120).copy();ratio=f.adjusted_close/f.close
    candles=[[str(t.date()),*[number(row[k]*ratio.loc[t]) for k in ['open','high','low','close']],number(row.volume)] for t,row in f.iterrows()]
    return dict(type='candles',title=name,group=group,candles=candles,annotation=annotation,
        weekly=[[str(t.date()),*[number(row[k]) for k in ['open','high','low','close','volume']]] for t,row in weekly.iterrows()],
        lines=[dict(name=f'MA{n}',points=points(p.rolling(n).mean().reindex(f.index))) for n in [20,50,200]])

def watch(d,ranks):
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
                    if pattern:c['pattern']=pattern
                    picks.append(c)
    return module('watch',d.as_of,'공식 대형주에서 W바닥·컵앤핸들·상승깃발·역헤드앤숄더·상승삼각형을 명시한 수치 규칙으로 선별합니다. 피벗은 좌우 3봉이 확보된 과거 종가로 확인하며 미확인 돌파를 구분합니다. 적합도는 기하 조건 점수로 성공확률이 아닙니다. 약세는 가격<MA50<MA200 및 1M<0입니다. 120일·52주 조정 OHLC, 일봉 MA20/50/200, 거래량을 제공합니다.',picks,[('선별 종목',len(picks)),('기하 패턴 종류',5)],missing=['원본의 미공개 패턴 판정·신뢰도·ADX 합성 신호와 수치 동등성은 미검증입니다. 현재 후보의 향후 수익 성과를 의미하지 않습니다.'])

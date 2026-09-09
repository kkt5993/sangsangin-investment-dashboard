"""Four discovery buckets and three evidence lenses over official universes.

Only the 45/30/25 and KR technical-only weights are source-disclosed. Component
normalization and bucket thresholds below are explicit, independent team rules.
"""
import numpy as np
import pandas as pd
from .engine import number, clean_json, ret, module

BUCKETS=[('초기 변곡','최근21거래일 RS 0선 또는 200일선 회복과 수익률 가속'),
         ('추세 확인','가격>50일선>200일선, 200일선 상승, 양의 상대강도'),
         ('스마트머니','애널리스트 긍정 의견과 목표가 여력. 실제 기관 매매 자료가 아님'),
         ('리서치 워치리스트','과열·점수 간 괴리·추가 확인이 필요한 관찰 후보')]


def clip(v):return float(np.clip(v,-3,3))


def technical(price,benchmark,volume):
    aligned=pd.concat(dict(p=price,b=benchmark),axis=1).dropna().tail(800)
    if len(aligned)<315:return None
    p=aligned.p;b=aligned.b
    # Abnormal jumps are quarantined for this candidate, never winsorized to a signal.
    if p.pct_change(fill_method=None).tail(253).abs().gt(.55).any():return None
    rel=(p.pct_change(63,fill_method=None)-b.pct_change(63,fill_method=None))*100
    z=(rel-rel.rolling(252,min_periods=126).mean())/rel.rolling(252,min_periods=126).std(ddof=0).replace(0,np.nan)
    z=z.mask(rel.rolling(252,min_periods=126).std(ddof=0)==0,0)
    if pd.isna(z.iloc[-1]):return None
    m50=p.rolling(50).mean();m200=p.rolling(200).mean();r1,r3,r6=[ret(p,h) for h in [21,63,126]]
    accel=r3-r6/2;prox=(p.iloc[-1]/p.tail(252).max()-1)*100
    stage=bool(p.iloc[-1]>m50.iloc[-1]>m200.iloc[-1] and m200.iloc[-1]>m200.iloc[-21])
    inverse=bool(p.iloc[-1]<m50.iloc[-1]<m200.iloc[-1] and m200.iloc[-1]<m200.iloc[-21])
    recapture=bool(((p>m200)&(p.shift()<=m200.shift())).tail(21).any())
    cross=bool(((z>0)&(z.shift()<=0)).tail(21).any())
    overheat=bool(p.iloc[-1]>m50.iloc[-1]*1.2)
    v=volume.reindex(p.index);den=v.rolling(20).mean().iloc[-1];vr=number(v.tail(5).mean()/den) if den>0 else None
    components={'RS z':clip(z.iloc[-1]),'수익률 가속':clip(accel/10),'52주 고점 접근':clip((prox+15)/5),
                '추세 단계':2 if stage else -2 if inverse else 0,'최근 회복':1 if cross or recapture else 0}
    if vr is not None:components['거래량']=clip(max(0,vr-1)*np.sign(r1))
    score=clip(np.mean(list(components.values()))-(1 if overheat else 0))
    reasons=[]
    for yes,reason in [(cross,'RS 0선 상향 회복'),(recapture,'200일선 회복'),(accel>0,'3M 수익률 가속'),(prox>=-5,'52주 고점 5% 이내'),(stage,'상승 Stage 2'),(vr is not None and vr>=1.5,'거래량 1.5배 이상'),(overheat,'50일선 대비 20% 과열')]:
        if yes:reasons.append(reason)
    return clean_json(dict(score=score,date=str(p.index[-1].date()),metrics=dict(r1m=r1,r3m=r3,r6m=r6,rs_z=z.iloc[-1],accel=accel,prox=prox,vsurge=vr),
                           stage=stage,recapture=recapture,rs_cross=cross,overheat=overheat,components=components,reasons=reasons))


def combine(market,tech,fund,smart):
    if market=='KR':return number(tech)
    return number(.45*tech+.3*fund+.25*smart) if fund is not None and smart is not None else None


def bucket(t,smart,ncov):
    if t['overheat']:return '리서치 워치리스트'
    m=t['metrics']
    if (t['recapture'] or t['rs_cross']) and m['accel']>0 and m['r3m']<30:return '초기 변곡'
    if smart is not None and smart>=1 and ncov is not None and ncov>=5 and m['r1m']<20:return '스마트머니'
    if t['stage'] and m['rs_z']>=0 and m['r3m']>0:return '추세 확인'
    return '리서치 워치리스트'


def build(d,financial):
    from .financial_modules import frame
    enriched={r['symbol']:r for r in financial};work=[];coverage=[]
    for market,key in [('KR','kr_largecap'),('US','us_largecap')]:
        members=d.members.get(key,{}).get('members',[]);count=0
        for m in members:
            symbol=m['symbol'];p=d.price(symbol);raw=d.frames.get(symbol)
            if raw is None:continue
            volume=raw.volume if 'volume' in raw else pd.Series(dtype=float)
            t=technical(p,d.price('^KS11' if market=='KR' else 'SPY'),volume)
            if t is None:continue
            count+=1;f=enriched.get(symbol,{});info=d.fund.get(symbol,{}).get('info',{})
            eg=f.get('eps_growth1');sur=None;history=frame(d.fund.get(symbol,{}).get('earnings_history'))
            if len(history) and 'surprisePercent' in history:
                history=history.copy();history.index=pd.to_datetime(history.index)
                h=pd.to_numeric(history.sort_index().loc[:d.as_of,'surprisePercent'],errors='coerce').dropna()
                if len(h):sur=number(h.iloc[-1]*100)
            fund=number(np.mean([clip(eg/20)]+([clip(sur/10)] if sur is not None else []))) if eg is not None else None
            ncov=f.get('analyst_count');rating=f.get('rating');target=number(info.get('targetMeanPrice'))
            quote=number(info.get('currentPrice') or info.get('regularMarketPrice'))
            # Target and current quote from the same provider snapshot avoid mixed dates/currencies.
            upside=number((target/quote-1)*100) if target is not None and quote is not None and quote>0 and info.get('currency') else None
            smart=number(np.mean([clip((3-rating)*1.5),clip(upside/15)])) if rating is not None and 1<=rating<=5 and ncov is not None and ncov>=3 and upside is not None else None
            score=combine(market,t['score'],fund,smart);reasons=t['reasons'][:]
            if eg is not None and eg>=20:reasons.append('FY1 EPS 성장 20% 이상')
            if sur is not None and sur>=5:reasons.append('최근 EPS 서프라이즈 +5% 이상')
            if smart is not None and smart>=1:reasons.append('애널리스트 긍정 의견')
            if score is None:reasons.append('종합점수 자료 부족')
            work.append(dict(symbol=symbol,name=m['name'],market=market,sector=m.get('sector','미분류'),bucket=bucket(t,smart,ncov),score=score,tech=t['score'],fund=fund,smart=smart,
                             price_date=t['date'],financial_date=f.get('financial_as_of'),metrics=dict(t['metrics'],eps_growth=eg,surprise=sur,analysts=ncov,rating=rating,upside=upside),components=t['components'],reasons=reasons))
        coverage.append([market,len(members),count])
    work.sort(key=lambda r:(r['score'] is not None,r['score'] if r['score'] is not None else r['tech'],r['tech']),reverse=True)
    # Compact public shortlist: up to 15 per market/bucket, with full scan coverage stated.
    items=[]
    for market in ['US','KR']:
        for name,_ in BUCKETS:items += [r for r in work if r['market']==market and r['bucket']==name][:15]
    items.sort(key=lambda r:(r['score'] is not None,r['score'] if r['score'] is not None else r['tech'],r['tech']),reverse=True)
    view=dict(type='discovery',title='종목 발굴 · 4개 분류와 3개 평가축',items=items,buckets=[dict(name=n,note=v) for n,v in BUCKETS],coverage=coverage)
    note='공식 KRX 대형주·IVV 주식 유니버스를 기술 스캔하고 시장·분류별 최대15개 후보를 공개합니다. 기술·실적·애널리스트의 3개 평가축은 −3~+3 팀 척도입니다. 종합은 KR 기술100%, US 기술45%·실적30%·애널리스트25%이며 구성점수 결측 시 US 종합은 미산출합니다. 스마트머니는 애널리스트 의견을 뜻합니다. 4개 분류는 서로 배타적인 팀 조건이며 매수 추천이나 성공확률이 아닙니다.'
    return module('discovery',d.as_of,note,[clean_json(view)],[('공식 구성',sum(r[1] for r in coverage)),('기술 스캔 통과',len(work)),('공개 후보',len(items)),('US 종합 가용',sum(r['market']=='US' and r['score'] is not None for r in work))],missing=['원본의 내부 정규화·버킷 임계치는 미공개여서 동일 점수 재현은 미검증입니다. 팀 산식은 설명서와 코드에 명시합니다.','재무·애널리스트는 현재 확보된 기업만 연결됩니다. 매수 의견 비율의 과거 변화·실제 기관 수급은 아직 없으며 추정하지 않습니다.','한국 범위는 현재 공식 대형주입니다. 원본의 KOSDAQ 포함 시가총액 상위 범위와 다릅니다.'])

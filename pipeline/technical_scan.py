"""Twelve disclosed indicator families; explicit team thresholds and Wilder seeds."""
import numpy as np
import pandas as pd
from .engine import number,clean_json,ret,points
from .catalog import MULTI,SCAN_EXTRA


def wilder(s,n=14):
    out=pd.Series(np.nan,index=s.index,dtype=float)
    starts=np.flatnonzero(s.rolling(n).count().to_numpy()==n)
    if not len(starts):return out
    start=int(starts[0]);out.iloc[start]=s.iloc[start-n+1:start+1].mean()
    for j in range(start+1,len(s)):
        if pd.notna(s.iloc[j]) and pd.notna(out.iloc[j-1]):out.iloc[j]=(out.iloc[j-1]*(n-1)+s.iloc[j])/n
    return out


def indicators(frame):
    f=frame.copy();ratio=f.adjusted_close/f.close
    for k in ['open','high','low','close']:f[k]=f[k]*ratio
    f=f.dropna(subset=['open','high','low','close']).tail(800);p=f.close
    tr=pd.concat([f.high-f.low,(f.high-p.shift()).abs(),(f.low-p.shift()).abs()],axis=1).max(axis=1);tr.iloc[0]=np.nan
    up=f.high.diff();down=-f.low.diff()
    pdm=up.where((up>down)&(up>0),0).where(up.notna());mdm=down.where((down>up)&(down>0),0).where(down.notna())
    atr=wilder(tr);plus=100*wilder(pdm)/atr.replace(0,np.nan);minus=100*wilder(mdm)/atr.replace(0,np.nan)
    plus=plus.mask(atr==0,0);minus=minus.mask(atr==0,0)
    dx=100*(plus-minus).abs()/(plus+minus).replace(0,np.nan);dx=dx.mask((plus+minus)==0,0)
    adx=wilder(dx)
    delta=p.diff();gain=wilder(delta.clip(lower=0));loss=wilder(-delta.clip(upper=0))
    rsi=100-100/(1+gain/loss.replace(0,np.nan));rsi=rsi.mask((loss==0)&(gain>0),100).mask((loss==0)&(gain==0),50)
    ma={n:p.rolling(n).mean() for n in [5,20,50,60,120,200]}
    macd=p.ewm(span=12,adjust=False,min_periods=12).mean()-p.ewm(span=26,adjust=False,min_periods=26).mean()
    signal=macd.ewm(span=9,adjust=False,min_periods=9).mean();hist=macd-signal
    low=f.low.rolling(14).min();high=f.high.rolling(14).max();k=(100*(p-low)/(high-low).replace(0,np.nan)).mask(high==low,50).rolling(3).mean();sd=k.rolling(3).mean()
    std=p.rolling(20).std(ddof=0);upper=ma[20]+2*std;lower=ma[20]-2*std;width=4*std/ma[20].replace(0,np.nan)*100
    tp=(f.high+f.low+p)/3;deviation=tp.rolling(20).apply(lambda a:np.abs(a-a.mean()).mean(),raw=True)
    cci=((tp-tp.rolling(20).mean())/(.015*deviation.replace(0,np.nan))).mask(deviation==0,0)
    ceiling=p.rolling(252).max();floor=p.rolling(252).min();position=(100*(p-floor)/(ceiling-floor).replace(0,np.nan)).mask(ceiling==floor,50)
    volume=f.volume if 'volume' in f else pd.Series(np.nan,index=f.index)
    # Zero-volume index/FX histories contain no usable exchange activity measure.
    vr=volume.rolling(5).mean()/volume.rolling(20).mean().replace(0,np.nan)
    return dict(frame=f,price=p,ma=ma,rsi=rsi,adx=adx,plus_di=plus,minus_di=minus,atr=atr,macd=macd,macd_signal=signal,histogram=hist,
                stoch_k=k,stoch_d=sd,upper=upper,lower=lower,width=width,cci=cci,position=position,volume_ratio=vr)


def scan(frame):
    a=indicators(frame);p=a['price'];current=p.iloc[-1];last=lambda key:number(a[key].iloc[-1])
    ma={n:v.iloc[-1] for n,v in a['ma'].items()};rsi=last('rsi');r1m=ret(p,21);r3m=ret(p,63);pos=last('position')
    spread=a['ma'][5]-a['ma'][20];cross=np.sign(spread).diff();recent=cross.tail(5);fresh=bool((recent.abs()>0).any())
    up=current>ma[20]>ma[60];down=current<ma[20]<ma[60]
    width=a['width'].dropna().tail(252);squeeze=len(width)>=100 and width.iloc[-1]<=width.quantile(.2)
    rules=[]
    def add(key,value,observation,definition,active=False):rules.append(dict(key=key,value=value,observation=observation,rule=definition,active=bool(active or value not in [0,None])))
    add('MA정배열',1 if up else -1 if down else 0,{'MA20':number(ma[20]),'MA60':number(ma[60]),'MA120':number(ma[120])},'P>MA20>MA60 +1, 역순 −1. MA120까지 만족하면 완전 배열.')
    add('GC/DC',1 if spread.iloc[-1]>0 else -1 if spread.iloc[-1]<0 else 0,number(spread.iloc[-1]),'MA5−MA20 부호. 최근5봉 내 부호 전환은 신규 신호.',fresh)
    macd=last('histogram');add('MACD',None if macd is None else int(np.sign(macd)),macd,'EMA12−EMA26의 9EMA 대비 히스토그램 부호.')
    add('RSI',None if rsi is None else -1 if rsi>=70 else 1 if rsi<=30 or 50<rsi<=65 else -1 if 35<=rsi<50 else 0,rsi,'Wilder14. ≥70 −1, ≤30 +1, 50 초과~65 +1, 35~50 미만 −1.')
    k=last('stoch_k');sd=last('stoch_d');add('Stoch',None if k is None or sd is None else -1 if k>=80 else 1 if k<=20 else int(np.sign(k-sd)),{'K':k,'D':sd},'14·3·3. K≥80 −1, K≤20 +1, 나머지는 K−D 부호.')
    add('볼린저',-1 if current>a['upper'].iloc[-1] else 1 if current<a['lower'].iloc[-1] else int(np.sign(current-ma[20])),{'upper':last('upper'),'lower':last('lower')},'20일 평균±2 모집단 표준편차. 상단 밖 −1, 하단 밖 +1, 내부는 중심선 대비 부호.')
    cci=last('cci');add('CCI',None if cci is None else 1 if cci>=100 else -1 if cci<=-100 else 0,cci,'Typical price20, 0.015×평균절대편차. ≥100 +1, ≤−100 −1.')
    add('52주',None if pos is None else 1 if pos>=90 else -1 if pos<=10 else 0,pos,'252종가 범위 내 위치. ≥90% +1, ≤10% −1. 범위가0이면50%.')
    add('모멘텀',None if r1m is None or r3m is None else 1 if r1m>0 and r3m>0 else -1 if r1m<0 and r3m<0 else 0,{'1M':r1m,'3M':r3m},'21·63거래일 수익률이 모두 양수 +1, 모두 음수 −1.')
    vr=last('volume_ratio');add('거래량',None if vr is None else int(np.sign(r1m))*1 if vr>=1.5 and r1m is not None else 0,vr,'5/20일 평균거래량 ≥1.5배이면 1M 수익률 방향. 거래량 미제공은 결측.')
    adx=last('adx');plus=last('plus_di');minus=last('minus_di');add('ADX',None if adx is None or plus is None or minus is None else int(np.sign(plus-minus)) if adx>=25 else 0,{'ADX':adx,'+DI':plus,'−DI':minus},'Wilder14. ADX≥25이면 +DI−−DI 부호. ADX 자체는 방향이 없음.')
    add('변동성',0 if len(width)>=100 else None,last('width'),'Bollinger 폭이 최근252봉 P20 이하이면 압축. 방향 점수는0.',squeeze)
    if pos is not None and pos>=99.5:pattern='신고가'
    elif pos is not None and pos<=.5:pattern='신저가'
    elif fresh:pattern='골든크로스' if spread.iloc[-1]>0 else '데드크로스'
    elif r1m is not None and r3m is not None and r1m>3 and r3m<0 and current>ma[20]:pattern='저점반등(턴어라운드)'
    elif up and ma[60]>ma[120]:pattern='추세상승(정배열)'
    elif down and ma[60]<ma[120]:pattern='추세하락(역배열)'
    elif squeeze:pattern='변동성압축(돌파임박)'
    elif rsi is not None and rsi>=70:pattern='과열'
    elif rsi is not None and rsi<=30:pattern='과매도'
    else:pattern='중립·횡보'
    score=sum(r['value'] for r in rules if r['value'] is not None)
    stars=sum([current>ma[50],current>ma[200],ma[50]>ma[200],ma[200]>a['ma'][200].iloc[-21]])
    f=a['frame'].tail(90)
    return clean_json(dict(date=str(p.index[-1].date()),score=score,available=sum(r['value'] is not None for r in rules),pattern=pattern,fresh=fresh,
        bias='강세' if score>=3 else '약세' if score<=-3 else '중립',rules=rules,rsi=rsi,adx=adx,plus_di=plus,minus_di=minus,atr=last('atr'),
        r1m=r1m,r3m=r3m,position=pos,ma_stars=stars,
        candles=[[str(t.date()),*[number(row[k]) for k in ['open','high','low','close']]] for t,row in f.iterrows()],
        lines=[dict(name='MA'+str(n),values=[number(v) for v in a['ma'][n].reindex(f.index)]) for n in [20,60]]))


def scanner_view(d):
    items=[]
    for s,name,group in MULTI+SCAN_EXTRA:
        frame=d.frames.get(s)
        if frame is None or len(frame)<253:continue
        result=scan(frame);result.update(symbol=s,name=name,group=group);items.append(result)
    items.sort(key=lambda r:(abs(r['score'])+2*r['fresh'],abs(r['r1m'] or 0)),reverse=True)
    return dict(type='scanner',title='37자산 · 12개 기술 지표와 패턴별 탐색',group='패턴 스캐너',items=items,
                note='점수는 각 지표의 −1/0/+1 합계입니다. 결측은 합계에서 제외하고 가용 지표 수를 표시합니다. 최근5봉 교차·52주 범위·대표 패턴 우선순위는 공개된 지표군을 바탕으로 정한 팀 규칙입니다. 예측확률이 아닙니다. 차트는90봉 OHLC와 MA20/60, 기본 상위9개이며 필터 결과에서 다시 선택합니다.')

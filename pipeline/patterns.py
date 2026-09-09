"""Explicit geometric candidates, using only three-bar-confirmed close pivots.

These thresholds are team research rules, not the undisclosed reference engine.
Scores measure geometry, never the probability of a profitable trade.
"""
import numpy as np
from .engine import number

def pivots(p,side='low',width=3):
    a=np.asarray(p);out=[]
    for i in range(width,len(a)-width):
        window=a[i-width:i+width+1];best=window.min() if side=='low' else window.max()
        if a[i]==best and np.count_nonzero(window==best)==1:out.append(i)
    return out

def candidates(price,as_of):
    p=price.loc[:as_of].dropna().tail(120);a=np.asarray(p);n=len(a);out=[]
    if n<90:return out
    lows=pivots(p);highs=pivots(p,'high');last=a[-1]
    def add(name,indices,neck,score,evidence):
        out.append(dict(name=name,score=number(np.clip(score,0,100)),confirmed=bool(last>=neck),neckline=number(neck),
            evidence=evidence,points=[[str(p.index[i].date()),number(a[i])] for i in indices],
            confirmed_at=str(p.index[min(n-1,max(indices)+3)].date())))
    # W: two lows 10–65 sessions apart, <=5% difference and >=4% rebound.
    for j in lows[-5:]:
        if n-1-j>25:continue
        for i in lows:
            if not 10<=j-i<=65:continue
            k=i+int(np.argmax(a[i:j+1]));neck=a[k];diff=abs(a[i]/a[j]-1);depth=neck/max(a[i],a[j])-1
            if diff<=.05 and depth>=.04 and last>=neck*.94:
                add('W바닥', [i,k,j],neck,100-diff/.05*35,f'저점 차이 {diff*100:.1f}% · 중간 반등 {depth*100:.1f}%')
    # Inverse H&S: head >=5% below both shoulders, shoulders within 7%.
    for i,j,k in zip(lows,lows[1:],lows[2:]):
        if not 20<=k-i<=90 or n-1-k>25:continue
        l=i+int(np.argmax(a[i:j+1]));r=j+int(np.argmax(a[j:k+1]));neck=(a[l]+a[r])/2;diff=abs(a[i]/a[k]-1)
        if a[j]<min(a[i],a[k])*.95 and diff<.07 and abs(a[l]/a[r]-1)<.08 and last>neck*.94:
            add('역헤드앤숄더',[i,l,j,r,k],neck,100-diff/.07*35,'중앙 저점 5% 이상 낮음 · 어깨 차이 '+f'{diff*100:.1f}%')
    # Ascending triangle: >=3 flat highs and rising lows within 60 sessions.
    hh=[i for i in highs if i>=n-60];ll=[i for i in lows if i>=n-60]
    if len(hh)>=3 and len(ll)>=3:
        hh=hh[-3:];ll=ll[-3:];neck=float(a[hh].mean());flat=float(a[hh].max()/a[hh].min()-1);rise=a[ll[-1]]/a[ll[0]]-1
        if flat<=.035 and rise>=.035 and np.all(np.diff(a[ll])>0) and last>=neck*.96:
            add('상승삼각형',sorted(hh+ll),neck,100-flat/.035*30,f'고점 폭 {flat*100:.1f}% · 저점 상승 {rise*100:.1f}%')
    # Cup & handle: separated rims, a deep center, then a shallow handle.
    for r in highs[-4:]:
        if not 5<=n-1-r<=20:continue
        for l in highs:
            if not 30<=r-l<=90:continue
            b=l+int(np.argmin(a[l:r+1]));neck=max(a[l],a[r]);depth=1-a[b]/neck;rim=abs(a[l]/a[r]-1);handle=1-a[r:].min()/a[r]
            if .2<=(b-l)/(r-l)<=.8 and .08<=depth<=.4 and rim<=.05 and .015<=handle<=min(.12,depth/2) and last>=neck*.94:
                h=r+int(np.argmin(a[r:]))
                if h in lows:add('컵앤핸들',[l,b,r,h],neck,100-rim/.05*25,'컵 깊이 '+f'{depth*100:.1f}% · 핸들 {handle*100:.1f}%')
    # Bull flag: >=12% pole, 5–20 session shallow, declining consolidation.
    for top in highs[-4:]:
        length=n-1-top
        if not 5<=length<=20 or top<20:continue
        start=top-20+int(np.argmin(a[top-20:top]));gain=a[top]/a[start]-1;pull=1-a[top:].min()/a[top]
        slope=np.polyfit(np.arange(length+1),np.log(a[top:]),1)[0]
        if gain>=.12 and .02<=pull<=.12 and pull<gain*.5 and -.015<slope<0 and last>a[top]*.90:
            end=top+int(np.argmin(a[top:]))
            if end in lows:add('상승깃발',[start,top,end],a[top],100-pull/.12*25,f'선행 상승 {gain*100:.1f}% · 조정 {pull*100:.1f}%')
    # Keep one best candidate per family, all pivots dated no later than as_of.
    unique={}
    for r in sorted(out,key=lambda r:(r['confirmed'],r['score']),reverse=True):unique.setdefault(r['name'],r)
    return list(unique.values())

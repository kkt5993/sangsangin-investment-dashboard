"""Three-expert performance gate with cached index, macro and stock research modes."""
import argparse
import numpy as np
import pandas as pd
from .engine import *
from .catalog import INDICES,DYNAMICS_STOCKS
from .ml_models import features,walk_forward

def gated(records):
    out=[]
    for r in records:
        mature=[a for a in records if a['target']<=r['origin'] and a['actual'] is not None][-24:]
        names=list(r['models']);mse={name:np.mean([(a['models'][name]-a['actual'])**2 for a in mature]) if len(mature)>=12 else 1 for name in names}
        inverse={n:1/max(v,.01) for n,v in mse.items()};total=sum(inverse.values());w={n:.75*inverse[n]/total+.25/len(names) for n in names}
        out.append(dict(r,weights=clean_json(w),gated=number(sum(w[n]*r['models'][n] for n in names)),gate_samples=len(mature)))
    return out

def build(d):
    sections=[];targets=[('지수',s,n,None,'%') for _,s,n in INDICES]
    targets += [('종목',s,n,None,'%') for s,n in DYNAMICS_STOCKS]
    targets += [('매크로','SPY','미국 10Y 금리 변화','DGS10','bp'),('매크로','SPY','CPI MoM','CPIAUCSL','%')]
    for mode,s,name,macro,unit in targets:
        X,p=features(d,s);target=None
        if macro:
            m=d.mac(macro).resample('ME').last().reindex(X.index)
            if macro=='DGS10':target=m.shift(-1).sub(m)*100
            else:target=(m.shift(-1)/m-1)*100
            # Macro latest target whose next observation is unknown remains unknown.
            X=X.assign(target_lag1=m.shift(1),target_lag3=m.shift(3)).dropna()
        records,importance=walk_forward(X,p,1,target=target)
        if not records:continue
        records=gated(records);latest=records[-1];pred=pd.Series({pd.Timestamp(r['target']):r['gated'] for r in records});actual=pd.Series({pd.Timestamp(r['target']):r['actual'] for r in records},dtype=float)
        group=mode+' · '+name
        sections.append(dict(type='line',title=group+' · 실제와 게이트 예측',group=group,left=unit,right='',guides=[0],series=[dict(name='실제',axis='left',points=points(actual.tail(36))),dict(name='게이트 예측',axis='left',points=points(pred.tail(37)))],forecast=True))
        sections.append(dict(bars(group+' · 전문가 가중치',[(n,v*100) for n,v in latest['weights'].items()],'%'),group=group))
        sections.append(dict(table(group+' · 예측 원장',['원점','타깃','예측 '+unit,'실제 '+unit,'게이트 표본 수'],[[r['origin'],r['target'],r['gated'],r['actual'],r['gate_samples']] for r in records[-24:]]),group=group))
        print('MAXIMUS',group,len(records),flush=True)
    return module('maximus',d.as_of,'지수·매크로·15개 입력 후보 종목의 캐시 예측 콘솔입니다. 3개 전문가(Ridge·BayesianRidge·ExtraTrees), 만기가 끝난 최근 24개 OOS 오류의 역 MSE 75%와 동일가중 25%로 게이트를 계산합니다. 전문가별 가중치와 실제 결과를 표시합니다. 미관측 타깃은 비워 둡니다.',sections,
        missing=['원본 10-expert MoE·SIS·ADF 파이프라인과 다른 명시적 기준모형입니다. 원본 모델을 실행했다고 표시하지 않습니다.','GitHub Pages에서 Python 재학습·임의 종목 서버 요청은 실행하지 않습니다. 로컬 명령으로 캐시를 갱신합니다.'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default='2026-09-08');a=p.parse_args();d=Data(a.as_of);d.export(build(d))
if __name__=='__main__':main()

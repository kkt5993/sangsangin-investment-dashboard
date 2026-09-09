"""Small walk-forward baseline. No reference model weights or retrospective tuning."""
import argparse
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,BayesianRidge
from sklearn.ensemble import ExtraTreesRegressor
from scipy.stats import norm
from .engine import *
from .catalog import INDICES

def features(d,s):
    p=d.monthly(s);r=p.pct_change(fill_method=None)
    f=pd.DataFrame({f'return_{n}m':p.pct_change(n,fill_method=None)*100 for n in [1,3,6,12]})
    f['vol_12m']=r.rolling(12).std()*np.sqrt(12)*100;f['distance_ma12']=(p/p.rolling(12).mean()-1)*100
    for key,transform in [('CPIAUCSL','yoy'),('INDPRO','yoy'),('UNRATE','level'),('FEDFUNDS','level'),('T10Y2Y','level'),('NFCI','level'),('M2SL','yoy')]:
        m=d.mac(key).resample('ME').last()
        if len(m)<100:continue
        if transform=='yoy':m=m.pct_change(12,fill_method=None)*100
        # Two full calendar months lag. Releases/revisions are not reconstructed.
        f[key]=m.reindex(f.index).shift(2)
    return f.replace([np.inf,-np.inf],np.nan).dropna(),p

def model_set():return {'Ridge':make_pipeline(StandardScaler(),Ridge(alpha=10)),
    'BayesianRidge':make_pipeline(StandardScaler(),BayesianRidge()),
    'ExtraTrees':ExtraTreesRegressor(n_estimators=40,max_depth=3,min_samples_leaf=15,random_state=17,n_jobs=1)}

def walk_forward(X,p,h,min_train=60,target=None):
    y=(p.shift(-h)/p-1)*100 if target is None else target;y=y.reindex(X.index);records=[];models=model_set();importance=[]
    for i in range(min_train+h,len(X)):
        # A target is usable only after its horizon has fully elapsed.
        cutoff=i-h;tx=X.iloc[:cutoff+1];ty=y.iloc[:cutoff+1];mask=ty.notna();tx=tx[mask];ty=ty[mask]
        if len(tx)<min_train:continue
        predictions={}
        for name,model in models.items():model.fit(tx,ty);predictions[name]=float(model.predict(X.iloc[[i]])[0])
        pred=float(np.mean(list(predictions.values())))
        matured=[a['actual']-a['prediction'] for a in records if a['origin_index']+h<=i and a['actual'] is not None]
        intervals={};prob=None
        if len(matured)>=24:
            e=np.array(matured[-120:]);prob=float((np.sum(e> -pred)+.5)/(len(e)+1)*100)
            intervals={str(q):number(pred+np.quantile(e,q)) for q in [.05,.16,.84,.95]}
        records.append(dict(origin=str(X.index[i].date()),target=str((X.index[i]+pd.offsets.MonthEnd(h)).date()),origin_index=i,train_last_origin=str(tx.index[-1].date()),train_target_end=str((tx.index[-1]+pd.offsets.MonthEnd(h)).date()),
            prediction=number(pred),actual=number(y.iloc[i]),probability=number(prob),interval=intervals,models=clean_json(predictions),calibration_observations=len(matured)))
    if len(records):
        ridge=models['Ridge'].named_steps['ridge'];importance=[dict(name=n,value=number(c)) for n,c in zip(X.columns,ridge.coef_)]
    return records,importance

def build(d):
    sections=[];leaderboard=[];hits=[];cards=[]
    for code,s,name in INDICES:
        X,p=features(d,s)
        for h in [1,3]:
            records,importance=walk_forward(X,p,h)
            if not records:continue
            print('ML',code,h,len(records),flush=True)
            group=name+f' · {h}M';lastrec=records[-1];cards.append((group+' 전망 %',lastrec['prediction']))
            known=[r for r in records if r['actual'] is not None];recent=known[-36:]
            for model in model_set():
                errors=[r['models'][model]-r['actual'] for r in recent];hit=np.mean([np.sign(r['models'][model])==np.sign(r['actual']) for r in recent])*100 if recent else None
                leaderboard.append([group,model,len(recent),number(hit),number(np.mean(np.abs(errors)))])
            hits.append(dict(name=group,group=name,values=[1 if np.sign(r['prediction'])==np.sign(r['actual']) else -1 for r in recent]))
            pp=pd.Series({pd.Timestamp(r['origin']):r['probability'] for r in records},dtype=float).dropna();z=expanding_z(pp,24);price=p.reindex(z.index);price=(price/price.iloc[0]*100) if len(price) else price
            sec=dict(type='ml',title=group,group=group,records=records[-37:],horizon=h,origin=lastrec['origin'],latest=lastrec,
                charts=[curve('선행 신호 z-score · 지수', [('P(상승) expanding z',z,'left'),('지수',price,'right')],'z','시작=100',guides=[-1,0,1]),
                        curve('최근 36개월 · P(상승)와 지수', [('P(상승)',pp.tail(36),'left'),('지수',p.reindex(pp.tail(36).index),'right')],'%','가격',[50],[0,100])],
                diagnostics=dict(features=list(X.columns),minimum_training_months=60,macro_lag_months=2,models=list(model_set())),importance=importance)
            if h==1 and known:
                kr=pd.Series({pd.Timestamp(r['target']):r['actual']/100 for r in known});position=pd.Series({pd.Timestamp(r['target']):np.sign(r['prediction']) for r in known});cost=position.diff().fillna(position).abs()*.0005
                sec['charts'].append(curve('시간순 OOS · 방향전략과 Buy & Hold',[('방향전략',(1+position*kr-cost).cumprod(),'left'),('Buy & Hold',(1+kr).cumprod(),'left')],'시작=1'))
            sections.append(sec)
    sections.append(table('모델별 최근 36개월 평가',['대상','모델','표본 수','방향 적중 %','MAE %p'],leaderboard))
    sections.append(heat('방향 적중 스트립 (+1 적중 / −1 실패)',[f'-{36-i}개월' for i in range(36)],hits))
    return module('ml',d.as_of,'Ridge·BayesianRidge·ExtraTrees의 동일가중 기준모형입니다. 월말 가격·거시 13개 내외 변수, 최소 60개월 학습, 매월 재학습, 1M·3M 타깃 만기 이후만 학습합니다. 과거 OOS 잔차 24개 이상으로 경험적 68%·90% 구간과 상승확률을 계산합니다. 1M 방향전략은 편도 5bp입니다.',sections,cards,
        missing=['원본의 Boruta·SHAP·LSTM·모델 선택 규칙을 복제한 모델이 아닙니다. 최종 모델의 표준화 Ridge 계수를 별도로 표시합니다.','거시 데이터는 최신 수정 빈티지에 2개월 시차를 적용했습니다. 발표일·개정치를 복원한 point-in-time 실시간 성과는 아닙니다.'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default='2026-09-08');a=p.parse_args();d=Data(a.as_of);d.export(build(d))
if __name__=='__main__':main()

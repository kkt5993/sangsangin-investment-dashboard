"""Ten regression families, shadow ranking, and strictly past model selection."""
import hashlib, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import Lasso, ElasticNet, BayesianRidge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.exceptions import ConvergenceWarning
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from .engine import number, clean_json
from .events_data import read, save
from .catalog import INDICES
from .ml_features import build_features, FORCED_KR, ALWAYS, MISSING

MODEL_SPEC=1
MIN_TRAIN=96
SHADOW_REPEATS=12
REFIT_MONTHS=6
LSTM_REFIT_MONTHS=12


def model_set():
    linear=lambda m:make_pipeline(StandardScaler(),m)
    return {'Lasso':linear(Lasso(alpha=.15,max_iter=5000)),
            'ElasticNet':linear(ElasticNet(alpha=.2,l1_ratio=.3,max_iter=5000)),
            'BayesianRidge':linear(BayesianRidge()),
            'KNN':linear(KNeighborsRegressor(n_neighbors=12,weights='distance',n_jobs=1)),
            'RandomForest':RandomForestRegressor(n_estimators=64,max_depth=4,min_samples_leaf=8,random_state=17,n_jobs=1),
            'ExtraTrees':ExtraTreesRegressor(n_estimators=64,max_depth=4,min_samples_leaf=8,random_state=17,n_jobs=1),
            'XGBoost':XGBRegressor(n_estimators=64,max_depth=3,learning_rate=.04,min_child_weight=10,reg_lambda=5,random_state=17,n_jobs=1,device='cpu',verbosity=0),
            'LightGBM':LGBMRegressor(n_estimators=64,max_depth=3,num_leaves=7,min_child_samples=15,learning_rate=.04,reg_lambda=3,random_state=17,n_jobs=1,verbosity=-1,deterministic=True,force_col_wise=True),
            'MLP':TransformedTargetRegressor(regressor=linear(MLPRegressor(hidden_layer_sizes=(32,16),alpha=1,max_iter=250,learning_rate_init=.005,shuffle=False,early_stopping=False,random_state=17)),transformer=StandardScaler())}


def shadow_selection(X,y,forced=(),repeats=SHADOW_REPEATS):
    """Source-disclosed shadow-win ranking, not Boruta significance acceptance."""
    counts=X.notna().sum();std=X.std()
    regular=list(X.columns[(counts>=max(36,len(X)*.7))&(std>1e-9)])
    mandatory=[k for k in forced if k in X and counts[k]>=24 and std[k]>1e-9]
    columns=list(dict.fromkeys(regular+mandatory))
    if not columns:raise ValueError('No usable ML feature history')
    tx=X[columns].fillna(X[columns].median());matrix=tx.to_numpy();wins=np.zeros(len(columns),dtype=int);importance=np.zeros(len(columns));rng=np.random.default_rng(17)
    for i in range(repeats):
        shadow=np.column_stack([rng.permutation(matrix[:,j]) for j in range(matrix.shape[1])])
        forest=RandomForestRegressor(n_estimators=48,max_depth=4,min_samples_leaf=8,random_state=17+i,n_jobs=1)
        forest.fit(np.column_stack([matrix,shadow]),y)
        values=forest.feature_importances_;wins+=values[:len(columns)]>values[len(columns):].max();importance+=values[:len(columns)]
    order=sorted(range(len(columns)),key=lambda j:(-wins[j],-importance[j],columns[j]))
    chosen=[columns[j] for j in order[:22]];selected=list(dict.fromkeys(chosen+mandatory))
    return selected,dict(repeats=repeats,selected=selected,forced=mandatory,unavailable_forced=[k for k in forced if k not in mandatory],
                         candidates=len(columns),ranking=[dict(name=columns[j],wins=int(wins[j]),forced=columns[j] in mandatory) for j in order])


class SequenceRegressor:
    def __init__(self,epochs=60):self.model=None;self.epochs=epochs;self.origin=None;self.train_end=None
    def fit(self,X,y,columns,origin,horizon):
        import torch
        torch.set_num_threads(1);torch.manual_seed(17)
        self.columns=columns;self.median=X[columns].median();self.scaler=StandardScaler()
        x=self.scaler.fit_transform(X[columns].fillna(self.median));self.mean=float(y.mean());self.sd=max(float(y.std(ddof=0)),1e-6)
        windows=np.array([x[j-11:j+1] for j in range(11,len(x))]);labels=(y.iloc[11:].to_numpy()-self.mean)/self.sd
        if len(windows)<36:raise ValueError('Insufficient LSTM sequence labels')
        class Model(torch.nn.Module):
            def __init__(self,n):
                super().__init__();self.cell=torch.nn.LSTM(n,8,batch_first=True);self.head=torch.nn.Linear(8,1)
            def forward(self,a):return self.head(self.cell(a)[0][:,-1]).squeeze(1)
        model=Model(x.shape[1]);optimizer=torch.optim.Adam(model.parameters(),lr=.005,weight_decay=.02)
        tx=torch.tensor(windows,dtype=torch.float32);ty=torch.tensor(labels,dtype=torch.float32)
        for _ in range(self.epochs):
            optimizer.zero_grad();loss=torch.nn.functional.mse_loss(model(tx),ty);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step()
        model.eval();self.model=model;self.origin=origin;self.train_end=str((X.index[-1]+pd.offsets.MonthEnd(horizon)).date());self.train_origin=str(X.index[-1].date())
    def predict(self,X):
        import torch
        a=self.scaler.transform(X[self.columns].tail(12).fillna(self.median))
        with torch.no_grad():return float(self.model(torch.tensor(a[None],dtype=torch.float32))[0])*self.sd+self.mean


def select_model(records,origin,candidates,minimum=24):
    known=[r for r in records if r['target']<=origin and r['actual'] is not None]
    if len(known)<minimum:return 'Ens-Mean',len(known)
    def rank(name):
        pairs=[(r['models'][name],r['actual']) for r in known[-120:] if r['models'].get(name) is not None]
        if len(pairs)<minimum:return (1,float('inf'),name)
        a,b=np.asarray(pairs).T
        return (-float(np.mean(np.sign(a)==np.sign(b))),float(np.sqrt(np.mean((a-b)**2))),name)
    return min(candidates,key=rank),len(known)


def calibration(records,origin,model,pred,minimum=24):
    errors=[r['actual']-r['models'][model] for r in records if r['target']<=origin and r['actual'] is not None and r['models'].get(model) is not None][-120:]
    if len(errors)<minimum:return None,{},len(errors)
    sd=float(np.std(errors,ddof=1)) if len(errors)>1 else 0.
    prob=norm.cdf(pred/sd)*100 if sd>1e-8 else 100 if pred>0 else 0 if pred<0 else 50
    return number(prob),{str(q):number(pred+np.quantile(errors,q)) for q in [.05,.16,.84,.95]},len(errors)


def walk_forward(X,p,h,forced=(),min_train=MIN_TRAIN,shadow_repeats=SHADOW_REPEATS,sequence=True,lstm_epochs=60):
    y=((p.shift(-h)/p-1)*100).reindex(X.index);records=[];selections=[];seq=SequenceRegressor(lstm_epochs)
    first=min_train+h-1;fits={};selection=None;columns=[];median=None;fit_origin=None;train_end=None;train_origin=None
    for i in range(first,len(X)):
        origin=str(X.index[i].date());target=str((X.index[i]+pd.offsets.MonthEnd(h)).date())
        # y at i-h is known at origin i. A 3M forecast cannot mature in one month.
        tx=X.iloc[:i-h+1];ty=y.reindex(tx.index);mask=ty.notna();tx=tx.loc[mask];ty=ty.loc[mask]
        if len(tx)<min_train:continue
        if not fits or (i-first)%REFIT_MONTHS==0:
            columns,selection=shadow_selection(tx,ty,forced,shadow_repeats);median=tx[columns].median();prepared=tx[columns].fillna(median)
            fits=model_set();warnings_by_model=[]
            for name,fit in fits.items():
                with warnings.catch_warnings(record=True) as observed:
                    warnings.simplefilter('always',ConvergenceWarning);fit.fit(prepared,ty)
                if any(issubclass(w.category,ConvergenceWarning) for w in observed):warnings_by_model.append(name)
            fit_origin=origin;train_origin=str(tx.index[-1].date());train_end=str((tx.index[-1]+pd.offsets.MonthEnd(h)).date())
            selections.append(dict(origin=origin,train_target_end=train_end,convergence_warnings=warnings_by_model,**selection))
        if sequence and (seq.model is None or (i-first)%LSTM_REFIT_MONTHS==0):seq.fit(tx,ty,columns,origin,h)
        q=X.iloc[[i]][columns].fillna(median);predictions={name:float(fit.predict(q)[0]) for name,fit in fits.items()}
        if sequence:predictions['LSTM']=seq.predict(X.iloc[:i+1])
        values=list(predictions.values());predictions['Ens-Mean']=float(np.mean(values));predictions['Ens-Median']=float(np.median(values))
        selected,nknown=select_model(records,origin,predictions);pred=predictions[selected];prob,interval,ncal=calibration(records,origin,selected,pred)
        used_columns=seq.columns if selected=='LSTM' else list(dict.fromkeys(columns+(seq.columns if sequence and selected.startswith('Ens-') else [])))
        record=dict(origin=origin,target=target,train_last_origin=seq.train_origin if selected=='LSTM' else train_origin,train_target_end=seq.train_end if selected=='LSTM' else train_end,
                    model_fit_origin=seq.origin if selected=='LSTM' else fit_origin,lstm_fit_origin=seq.origin,selected_model=selected,selection_observations=nknown,
                    prediction=number(pred),actual=number(y.iloc[i]),probability=prob,interval=interval,models=clean_json(predictions),calibration_observations=ncal,feature_count=len(used_columns))
        records.append(record)
    return dict(records=records,selections=selections,latest_features=used_columns if records else [])


def explanation(X,p,h,selection):
    """Full available label fit for interpretation only; exact additive TreeSHAP."""
    y=((p.shift(-h)/p-1)*100).reindex(X.index);known=y.notna();columns=selection['selected'];tx=X.loc[known,columns];tx=tx.fillna(tx.median())
    model=model_set()['LightGBM'];model.fit(tx,y.loc[known]);q=tx.tail(120)
    contributions=model.booster_.predict(q,pred_contrib=True);prediction=model.predict(q)
    error=float(np.max(np.abs(contributions.sum(axis=1)-prediction)))
    if error>1e-6:raise ValueError('TreeSHAP contribution sum mismatch')
    rank=np.argsort(-np.abs(contributions[:,:-1]).mean(axis=0))[:20];rows=[]
    for j in rank:
        raw=q.iloc[:,j];lo,hi=raw.quantile([.05,.95]);color=((raw-lo)/(hi-lo)).clip(0,1) if hi>lo else raw*0+.5
        rows.append(dict(name=columns[j],mean_abs=number(np.abs(contributions[:,j]).mean()),points=[[number(v),number(c)] for v,c in zip(contributions[:,j],color)]))
    return dict(type='shap',title='LightGBM TreeSHAP · 학습표본 해석',rows=rows,dates=[str(t.date()) for t in q.index],additive_error=error,training_end=str(tx.index[-1].date()),training_observations=len(tx),expected_value=number(contributions[0,-1]),scope='full available-label fit; not OOS explanation')


def signature(X,p,h):
    sha=hashlib.sha256(Path(__file__).read_bytes());sha.update(Path(__file__).with_name('ml_features.py').read_bytes())
    sha.update(str((list(X.columns),h,MODEL_SPEC)).encode());sha.update(pd.util.hash_pandas_object(X,index=True).values.tobytes());sha.update(pd.util.hash_pandas_object(p,index=True).values.tobytes())
    return sha.hexdigest()


def build(d):
    out=dict(as_of=d.as_of,vintage=d.vintage,model_spec=MODEL_SPEC,targets={},missing=MISSING)
    for code,symbol,name in INDICES:
        X,p=build_features(d,symbol)
        for h in [1,3]:
            key=code+'_'+str(h)+'M';sig=signature(X,p,h);resource='ml_ensemble/'+key+'.json.gz';old=d.resource(resource)
            if old.exists() and read(old).get('signature')==sig:
                result=read(old);print('ML CACHE',key,flush=True)
            else:
                forced=list(dict.fromkeys(ALWAYS+(FORCED_KR if code=='KOSPI' else [])))
                result=walk_forward(X,p,h,forced)
                result.update(code=code,symbol=symbol,name=name,horizon=h,as_of=d.as_of,vintage=d.vintage,signature=sig,model_spec=MODEL_SPEC,
                              feature_names=list(X.columns),feature_coverage={k:int(v) for k,v in X.notna().sum().items()},origin=str(X.index[-1].date()),
                              parameters=dict(minimum_training_months=MIN_TRAIN,shadow_repeats=SHADOW_REPEATS,refit_months=REFIT_MONTHS,lstm_refit_months=LSTM_REFIT_MONTHS,lstm_epochs=60,macro_lag=2))
                if h==1 and code in ['KOSPI','SP500']:result['explanation']=explanation(X,p,h,result['selections'][-1])
                save(d.base/resource,result);print('ML COMPLETE',key,len(result['records']),'origins',flush=True)
            out['targets'][key]=result
    return out

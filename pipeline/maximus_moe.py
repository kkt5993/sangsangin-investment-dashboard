"""Ten experts, fold-local ADF/SIS, a past-OOS gate and audited crash adjustment."""
import hashlib,warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import ElasticNet,LogisticRegression
from sklearn.ensemble import HistGradientBoostingRegressor,RandomForestRegressor,AdaBoostRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF,WhiteKernel
from sklearn.exceptions import ConvergenceWarning
from xgboost import XGBRegressor
from threadpoolctl import threadpool_limits
from .engine import number,clean_json
from .events_data import read,save
from .maximus_features import build_inputs,target_labels,StationarySIS,feature_domain,MACRO_TARGETS
from .catalog import INDICES,DYNAMICS_STOCKS

MODEL_SPEC=1
NAMES=['ElasticNet','HistGB','XGBoost','RandomForest','AdaBoost','MLP','LSTM','GRU','GaussianProcess','MeanReversion']


def experts(columns):
    scale=lambda model:make_pipeline(StandardScaler(),model)
    return dict(ElasticNet=scale(ElasticNet(alpha=.2,l1_ratio=.3,max_iter=5000)),
        HistGB=HistGradientBoostingRegressor(max_iter=64,max_depth=3,max_leaf_nodes=7,min_samples_leaf=15,learning_rate=.05,l2_regularization=3,early_stopping=False,random_state=23),
        XGBoost=XGBRegressor(n_estimators=64,max_depth=3,learning_rate=.04,min_child_weight=10,reg_lambda=5,n_jobs=1,device='cpu',random_state=23,verbosity=0),
        RandomForest=RandomForestRegressor(n_estimators=64,max_depth=4,min_samples_leaf=8,n_jobs=1,random_state=23),
        AdaBoost=AdaBoostRegressor(estimator=DecisionTreeRegressor(max_depth=2,min_samples_leaf=8),n_estimators=64,learning_rate=.04,random_state=23),
        MLP=TransformedTargetRegressor(regressor=scale(MLPRegressor(hidden_layer_sizes=(24,8),alpha=1,learning_rate_init=.005,max_iter=250,shuffle=False,early_stopping=False,random_state=23)),transformer=StandardScaler()),
        GaussianProcess=scale(GaussianProcessRegressor(kernel=RBF(np.sqrt(columns))+WhiteKernel(.2),optimizer=None,normalize_y=True,alpha=1e-6,random_state=23)))


class Recurrent:
    def __init__(self,cell,epochs):self.cell=cell;self.epochs=epochs
    def fit(self,X,y):
        import torch
        torch.set_num_threads(1);torch.manual_seed(23)
        self.scaler=StandardScaler();a=self.scaler.fit_transform(X);self.mean=float(y.mean());self.sd=max(float(y.std(ddof=0)),1e-6)
        # Missing labels do not collapse the monthly sequence/calendar.
        windows=np.array([a[i-11:i+1] for i in range(11,len(a))]);labels=y.iloc[11:].to_numpy();mask=np.isfinite(labels)
        if mask.sum()<36:raise ValueError('Insufficient complete sequence labels')
        cell=self.cell
        class Net(torch.nn.Module):
            def __init__(self):
                super().__init__();self.cell=getattr(torch.nn,cell)(a.shape[1],8,batch_first=True);self.head=torch.nn.Linear(8,1)
            def forward(self,x):return self.head(self.cell(x)[0][:,-1]).squeeze(1)
        self.net=Net();opt=torch.optim.Adam(self.net.parameters(),lr=.005,weight_decay=.03)
        tx=torch.tensor(windows[mask],dtype=torch.float32);ty=torch.tensor((labels[mask]-self.mean)/self.sd,dtype=torch.float32)
        for _ in range(self.epochs):
            opt.zero_grad();loss=torch.nn.functional.mse_loss(self.net(tx),ty);loss.backward();torch.nn.utils.clip_grad_norm_(self.net.parameters(),1);opt.step()
        self.net.eval()
    def predict(self,X):
        import torch
        a=self.scaler.transform(X.tail(12))
        with torch.no_grad():return float(self.net(torch.tensor(a[None],dtype=torch.float32))[0])*self.sd+self.mean


class Bundle:
    def fit(self,X,y,epochs):
        self.sis=StationarySIS().fit(X,y);tx=self.sis.transform(X);known=y.notna();self.models=experts(tx.shape[1]);self.warnings=[]
        for name,model in self.models.items():
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always',ConvergenceWarning);model.fit(tx.loc[known],y.loc[known])
            if any(issubclass(w.category,ConvergenceWarning) for w in caught):self.warnings.append(name)
        self.recurrent={name:Recurrent(name,epochs) for name in ['LSTM','GRU']}
        for model in self.recurrent.values():model.fit(tx,y)
        self.mean=float(y.mean());self.sd=max(float(y.std(ddof=1)),1e-6);self.clip=(self.mean-2.5*self.sd,self.mean+2.5*self.sd)
        self.crash=X['cmp_crash'].dropna();self.crash_low=float(self.crash.quantile(.85)) if len(self.crash) else None;self.crash_high=float(self.crash.quantile(.99)) if len(self.crash) else None
        return self
    def predict(self,prepared):
        out={name:float(model.predict(prepared.tail(1))[0]) for name,model in self.models.items()}
        out.update({name:model.predict(prepared) for name,model in self.recurrent.items()})
        # Explicit team anchor: 15% of a past 10Y/min36M median level gap.
        out['MeanReversion']=float(prepared['anchor_gap'].iloc[-1])*.15 if 'anchor_gap' in prepared else self.mean
        return {name:float(np.clip(out[name],*self.clip)) for name in NAMES}


def known_before(records,origin,embargo=1):
    cutoff=str((pd.Timestamp(origin)-pd.offsets.MonthEnd(embargo)).date())
    return [r for r in records if r['target']<=cutoff and r['actual'] is not None]


def gate(records,origin,prepared):
    known=known_before(records,origin)[-48:];equal=np.ones(10)/10
    if len(known)<12:return dict(zip(NAMES,equal)),dict(observations=len(known),classifier_observations=0,classes=0)
    pred=np.asarray([[r['experts'][n] for n in NAMES] for r in known]);actual=np.asarray([r['actual'] for r in known]);mse=((pred-actual[:,None])**2).mean(axis=0)
    inverse=1/np.maximum(mse,1e-6);prior=.5*inverse/inverse.sum()+.5*equal;router=equal;labels=np.abs(pred-actual[:,None]).argmin(axis=1)
    dates=pd.to_datetime([r['origin'] for r in known]);classes=len(set(labels));nclassifier=0
    if len(known)>=24 and classes>1:
        model=make_pipeline(StandardScaler(),LogisticRegression(C=.5,max_iter=2000,random_state=23))
        model.fit(prepared.reindex(dates),labels);prob=model.predict_proba(prepared.tail(1))[0];router=np.zeros(10)
        router[model[-1].classes_]=prob;nclassifier=len(known)
    weights=.75*prior+.25*router
    return dict(zip(NAMES,weights)),dict(observations=len(known),classifier_observations=nclassifier,classes=classes)


def crash_adjustment(pred,crash,low,high,kind):
    severity=0.
    if pd.notna(crash) and low is not None and high is not None and high>low:severity=float(np.clip((crash-low)/(high-low),0,1))
    # A stock crash rule is not a CPI inflation-policy or bond-price forecast.
    adjusted=pred-max(pred,0)*.6*severity-3*severity if kind=='ret' else pred
    return adjusted,dict(applied=kind=='ret' and severity>0,severity=severity,threshold=low,scale=high,raw=pred,adjusted=adjusted)


@threadpool_limits.wrap(limits=1)
def walk_forward(X,context,min_train=96,epochs=60,explain=True,progress=False):
    y=target_labels(context).reindex(X.index);records=[];selections=[];bundle=None;last_fit=-100;latest_prepared=None
    for i in range(min_train+1,len(X)):
        origin=str(X.index[i].date());target=str((X.index[i]+pd.offsets.MonthEnd(1)).date())
        # One full extra information month between training target and test origin.
        tx=X.iloc[:i-1];ty=y.reindex(tx.index)
        if ty.notna().sum()<min_train:continue
        if bundle is None or i-last_fit>=6:
            bundle=Bundle().fit(tx,ty,epochs);last_fit=i;fit_origin=origin
            last_label=ty.last_valid_index();train_target_end=str((last_label+pd.offsets.MonthEnd(1)).date())
            selections.append(dict(origin=origin,train_target_end=train_target_end,features=bundle.sis.columns,report=bundle.sis.report,warnings=bundle.warnings))
            if progress and len(selections)%4==0:print('MAXIMUS FIT',origin,len(bundle.sis.columns),'inputs',flush=True)
        prepared=bundle.sis.transform(X.iloc[:i+1]);pred=bundle.predict(prepared);weights,diagnostics=gate(records,origin,prepared)
        raw=sum(pred[n]*weights[n] for n in NAMES);adjusted,override=crash_adjustment(raw,X['cmp_crash'].iloc[i],bundle.crash_low,bundle.crash_high,context['kind'])
        known=known_before(records,origin);residual=np.array([r['actual']-r['prediction'] for r in known[-120:]])
        sigma=float(residual.std(ddof=1)) if len(residual)>=24 else None;prob=norm.cdf(adjusted/sigma)*100 if sigma and sigma>1e-9 else None
        records.append(dict(origin=origin,target=target,fit_origin=fit_origin,train_target_end=train_target_end,experts=pred,weights=weights,gate=diagnostics,
            raw=raw,prediction=adjusted,actual=number(y.iloc[i]),sigma=sigma,probability=prob,calibration_observations=len(residual),override=override,
            baseline_mean=bundle.mean,momentum=number(context['level'].diff().iloc[i] if context['kind']=='diff' else context['level'].pct_change(fill_method=None).iloc[i]*100),current=number(context['level'].iloc[i]),feature_count=len(bundle.sis.columns)))
        latest_prepared=prepared
    result=dict(records=records,selections=selections,feature_names=list(X.columns),parameters=dict(min_train=min_train,refit_months=6,embargo=1,sequence=12,recurrent_epochs=epochs,gate_window=48,gate_logistic=.25,gate_prior=.75,prior_uniform=.5,anchor_speed=.15))
    if records and explain:result['explanation']=occlusion(bundle,latest_prepared,records[-1]['weights'])
    return clean_json(result)


def occlusion(bundle,prepared,weights):
    """Fixed-gate model sensitivity. No claim of SHAP or economic causality."""
    original=prepared.tail(12).copy();reference=original.copy()
    for name in reference:reference[name]=bundle.sis.mean[name]
    blend=lambda frame:sum(v*weights[k] for k,v in bundle.predict(frame).items())
    pred=blend(original);base=blend(reference);rows=[]
    for name in original:
        altered=original.copy();altered[name]=bundle.sis.mean[name];delta=pred-blend(altered)
        rows.append(dict(name=name,value=delta,importance=abs(delta),domain=feature_domain(name)))
    raw=sum(r['value'] for r in rows);desired=pred-base;scale=desired/raw if abs(raw)>1e-9 else None
    r=sum(a['value'] for a in rows if a['domain']=='R');i=sum(a['value'] for a in rows if a['domain']=='I')
    adjusted=scale is not None and abs(scale)<=10
    # Preserve any unstable interaction residual instead of forcing an identity.
    if adjusted:r*=scale;i*=scale
    residual=pred-base-r-i
    return dict(method='fixed-gate occlusion',prediction=pred,base=base,rational=r,irrational=i,interaction=residual,rescaled=adjusted,scale=scale,
                rows=sorted(rows,key=lambda r:-r['importance'])[:25],scope='latest fitted model; last 12 tokens replaced by training mean; not OOS or SHAP')


def build(d,only=None):
    targets=[('idx',s,n) for _,s,n in INDICES]+[('macro',k,n) for k,n,_ in MACRO_TARGETS]+[('stock',s,n) for s,n in DYNAMICS_STOCKS]
    result=dict(model_spec=MODEL_SPEC,as_of=d.as_of,vintage=d.vintage,targets={},unavailable=[])
    for mode,key,name in targets:
        if only and key not in only:continue
        X,ctx=build_inputs(d,key,mode)
        if ctx['technical'].notna().sum()<96:result['unavailable'].append(dict(symbol=key,reason='가격 이력8년 미만'));continue
        sha=hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name('maximus_features.py').read_bytes())
        sha.update(pd.util.hash_pandas_object(X,index=True).values.tobytes());sha.update(pd.util.hash_pandas_object(ctx['level'],index=True).values.tobytes());sig=sha.hexdigest()
        resource='maximus_moe/'+key.replace('^','').replace('=','_')+'.json.gz';old=d.resource(resource)
        if old.exists() and read(old).get('signature')==sig:target=read(old);print('MAXIMUS CACHE',key,flush=True)
        else:
            print('MAXIMUS TRAIN',key,len(X),'months',flush=True)
            target=walk_forward(X,ctx,progress=True);target.update(symbol=key,name=name,mode=mode,kind=ctx['kind'],unit=ctx['unit'],observation_lag=ctx['observation_lag'],signature=sig,model_spec=MODEL_SPEC,
                 as_of=d.as_of,vintage=d.vintage,history=[[str(t.date()),number(v)] for t,v in ctx['level'].tail(36).items()])
            save(d.base/resource,target);print('MAXIMUS COMPLETE',key,len(target['records']),flush=True)
        result['targets'][key]=target
    return result

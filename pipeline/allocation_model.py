"""Independent monthly macro allocation models, with nested time-ordered fitting.

The reference discloses model families but not all hyperparameters or 74 inputs.
Every choice here is a team setting; revised macro data are not PIT vintages.
"""
import argparse, warnings
import numpy as np
import pandas as pd
from boruta import BorutaPy
from lightgbm import LGBMRegressor, LGBMClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet, LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.stats import norm
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
from .engine import Data, number, clean_json
from .events_data import save

ASSETS={'주식':'SPY','채권':'IEF','금':'GLD','원자재':'DBC','리츠':'VNQ','크립토':'BTC-USD','달러':'UUP'}
STATES=['회복','과열','스태그플레이션','침체']
LEVELS=['FEDFUNDS','DGS10','DGS2','DGS3MO','DFII10','T10YIE','T10Y2Y','T10Y3M','NFCI',
        'BAMLH0A0HYM2','VIXCLS','UNRATE','KR_LEAD','KR_BASE','OECD_CLI_USA','OECD_CLI_KOR','OECD_CLI_JPN','OECD_CLI_CHN']
YOYS=['CPIAUCSL','PCEPILFE','INDPRO','M2SL','WALCL','KR_EXPORT','RSAFS','PAYEMS']
MIN_TRAIN=60
MODEL_SPEC=3
BORUTA_ITERATIONS=100


def aligned_price(d,symbol):
    p=d.price(symbol)
    # A crypto bar dated Monday closes at Tuesday 00:00 UTC, after Monday US close.
    if symbol.endswith('-USD'):p=p.copy();p.index=p.index+pd.Timedelta(days=1)
    return p.reindex(d.price('SPY').index)


def monthly_asset(d,symbol):
    end=pd.Timestamp(d.as_of).replace(day=1)-pd.Timedelta(days=1)
    return aligned_price(d,symbol).loc[:end].resample('ME').last()


def feature_frame(d):
    index=d.monthly('SPY').index
    f=pd.DataFrame(index=index)
    for key in LEVELS+YOYS:
        m=d.mac(key).resample('ME').last().reindex(index)
        if key.startswith('OECD_CLI_'):m=m-100
        if key in YOYS:m=m.pct_change(12,fill_method=None)*100
        f[key]=m.shift(2);f[key+'_3m']=m.diff(3).shift(2)
    for key in ['SPY','EEM','MCHI','SMH','GLD','USO']:
        m=d.monthly(key).reindex(index)
        for h in [3,6,12]:f[key+'_'+str(h)+'m']=m.pct_change(h,fill_method=None)*100
    for a,b in [('HG=F','GC=F'),('GLD','USO'),('SMH','SPY'),('HYG','TLT')]:
        p=d.monthly(a).reindex(index)/d.monthly(b).reindex(index)
        f[a+'/'+b]=p.pct_change(3,fill_method=None)*100
    assert len(f.columns)==74
    f=f.replace([np.inf,-np.inf],np.nan).iloc[15:]
    prices=pd.concat({a:monthly_asset(d,s) for a,s in ASSETS.items()},axis=1).reindex(index)
    monthly=prices.pct_change(fill_method=None)*100
    # These are observation-month labels. Training waits two months for release lag.
    growth=d.mac('OECD_CLI_USA').resample('ME').last().reindex(index)
    inflation=d.mac('CPIAUCSL').resample('ME').last().reindex(index).pct_change(12,fill_method=None)*100
    g=growth.diff(3);i=inflation.diff(3)
    clock=pd.Series(np.select([(g>=0)&(i<0),(g>=0)&(i>=0),(g<0)&(i>=0)],STATES[:3],default=STATES[3]),index=index).where(g.notna()&i.notna())
    return f,monthly,clock


def selected_inputs(train,current,target,iterations=BORUTA_ITERATIONS):
    columns=train.columns[(train.notna().mean()>=.8)&(train.std()>1e-8)]
    tx=train[columns];median=tx.median();tx=tx.fillna(median)
    forest=RandomForestRegressor(n_estimators=64,max_depth=4,min_samples_leaf=8,n_jobs=1,random_state=17)
    selector=BorutaPy(forest,n_estimators=64,max_iter=iterations,perc=100,random_state=17,verbose=0)
    selector.fit(tx.to_numpy(),target.to_numpy())
    selected=columns[selector.support_];tentative=columns[selector.support_weak_]
    mode='confirmed'
    if not len(selected):
        selected=columns[selector.support_|selector.support_weak_];mode='confirmed+tentative'
    if not len(selected):
        # Boruta can reject all features. Expose a baseline fallback, never call it acceptance.
        selected=columns[np.argsort(selector.ranking_)[:min(8,len(columns))]];mode='rank fallback'
    selected=list(selected)
    return tx[selected],current[selected].fillna(median[selected]),dict(candidates=len(columns),selected=selected,tentative=list(tentative),mode=mode)


def tree(cls):
    return cls(n_estimators=50,num_leaves=7,max_depth=3,min_child_samples=15,learning_rate=.04,
               reg_lambda=2,random_state=17,n_jobs=1,verbosity=-1,deterministic=True,force_col_wise=True)


class SequenceClassifier:
    def __init__(self):self.model=None;self.columns=[];self.origin=None
    def fit(self,features,target,columns,origin):
        import torch
        torch.set_num_threads(1);torch.manual_seed(17)
        self.columns=columns;self.median=features[columns].median();self.scaler=StandardScaler()
        x=self.scaler.fit_transform(features[columns].fillna(self.median))
        windows=[];labels=[]
        for j in range(11,len(x)):
            if pd.notna(target.iloc[j]):windows.append(x[j-11:j+1]);labels.append(float(target.iloc[j]))
        if len(windows)<36 or len(set(labels))<2:return
        class LSTM(torch.nn.Module):
            def __init__(self,n):
                super().__init__();self.cell=torch.nn.LSTM(n,8,batch_first=True);self.head=torch.nn.Linear(8,1)
            def forward(self,x):return self.head(self.cell(x)[0][:,-1]).squeeze(1)
        model=LSTM(x.shape[1]);optimizer=torch.optim.Adam(model.parameters(),lr=.01,weight_decay=.01)
        tx=torch.tensor(np.asarray(windows),dtype=torch.float32);ty=torch.tensor(labels,dtype=torch.float32)
        for _ in range(50):
            optimizer.zero_grad();loss=torch.nn.functional.binary_cross_entropy_with_logits(model(tx),ty);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step()
        model.eval();self.model=model;self.origin=origin
    def predict(self,features):
        if self.model is None or len(features)<12:return None
        import torch
        x=self.scaler.transform(features[self.columns].tail(12).fillna(self.median))
        with torch.no_grad():return float(torch.sigmoid(self.model(torch.tensor(x[None],dtype=torch.float32)))[0])


def markov_probability(spread,params=None):
    """One-step predictive positive-spread probability, never smoothed histories."""
    try:
        model=MarkovRegression(spread.dropna(),k_regimes=2,trend='c',switching_variance=True)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            fit=model.fit(maxiter=150,disp=False) if params is None else model.filter(params)
        if params is None and not fit.mle_retvals.get('converged',False):return None,None
        transition=np.asarray(fit.regime_transition)[:,:,0]
        filtered=np.asarray(fit.filtered_marginal_probabilities)[-1]
        next_state=transition@filtered
        means=np.array([fit.params['const[0]'],fit.params['const[1]']]);sigmas=np.sqrt([fit.params['sigma2[0]'],fit.params['sigma2[1]']])
        p=float(next_state@norm.cdf(means/sigmas))
        if not np.isfinite(p):return None,None
        return float(np.clip(p,0,1)),fit.params
    except (ValueError,RuntimeError,np.linalg.LinAlgError,KeyError,ZeroDivisionError):return None,None


def walk_forward(X,returns,clock,min_train=MIN_TRAIN,sequence=True,boruta_iterations=BORUTA_ITERATIONS):
    future=returns.shift(-1).reindex(X.index);spread=(returns['주식']-returns['채권'])
    risk=(future['주식']>future['채권']).astype(float).where(future['주식'].notna()&future['채권'].notna())
    records=[];seq=SequenceClassifier();ms_params=None;last_annual=None
    for j in range(min_train,len(X)):
        origin=X.index[j];target=origin+pd.offsets.MonthEnd(1)
        # A next-month return from j-1 is known at origin j, never y[j].
        train=X.iloc[:j];yspread=future['주식'].iloc[:j]-future['채권'].iloc[:j];mask=yspread.notna()
        train=train.loc[mask];yspread=yspread.loc[mask]
        if len(train)<min_train:continue
        tx,q,selection=selected_inputs(train,X.iloc[[j]],yspread,boruta_iterations)
        scaler=StandardScaler();sx=scaler.fit_transform(tx);sq=scaler.transform(q)
        mu={};parts={};observations={}
        for asset in ASSETS:
            y=future[asset].reindex(tx.index);known=y.notna();observations[asset]=int(known.sum())
            if known.sum()<min_train:mu[asset]=None;parts[asset]={};continue
            fits={'ElasticNet':ElasticNet(alpha=.15,l1_ratio=.2,max_iter=5000),
                  'RandomForest':RandomForestRegressor(n_estimators=48,max_depth=4,min_samples_leaf=10,random_state=17,n_jobs=1),
                  'LightGBM':tree(LGBMRegressor)}
            predictions={}
            for name,model in fits.items():
                a,b=(sx[known],sq) if name=='ElasticNet' else (tx.loc[known],q)
                model.fit(a,y.loc[known]);predictions[name]=float(model.predict(b)[0])
            mu[asset]=number(np.mean(list(predictions.values())));parts[asset]=clean_json(predictions)
        ry=risk.reindex(tx.index).astype(int)
        clf=[];drivers=[]
        if ry.nunique()>1:
            for model,a,b in [(LogisticRegression(C=.2,max_iter=1500),sx,sq),(tree(LGBMClassifier),tx,q)]:
                model.fit(a,ry);clf.append(float(model.predict_proba(b)[0,list(model.classes_).index(1)]))
            counts=model.feature_importances_;total=counts.sum()
            drivers=[dict(name=k,value=number(v/total*100)) for k,v in zip(tx.columns,counts) if total and v>0]
        else:clf=[float(ry.iloc[-1])]
        annual=last_annual is None or origin.year!=last_annual
        if annual:
            ms_params=None
            if sequence:seq.fit(train,risk.reindex(train.index),list(tx.columns),str(origin.date()))
            last_annual=origin.year
        pms,ms_params=markov_probability(spread.loc[:origin],ms_params)
        plstm=seq.predict(X.iloc[:j+1]) if sequence else None
        pp={'분류':float(np.mean(clf)),'Markov':pms,'LSTM':plstm}
        pr=float(np.median([p for p in pp.values() if p is not None]))
        # Future observation-month clock label becomes trainable only after 2-month lag.
        cy=clock.shift(-1).reindex(tx.index)
        matured=(tx.index+pd.offsets.MonthEnd(3)<=origin)&cy.notna()
        cx=tx.loc[matured];cy=cy.loc[matured]
        if cy.nunique()>1:
            cm=tree(LGBMClassifier);cm.fit(cx,cy);cp=cm.predict_proba(q)[0];prediction=str(cm.classes_[np.argmax(cp)]);cp=dict(zip(cm.classes_,map(float,cp)))
        else:prediction=str(cy.iloc[-1]);cp={prediction:1.}
        fit_end=clock.loc[:origin-pd.offsets.MonthEnd(2)].dropna().index[-1]
        perf={state:{asset:number(returns[asset].loc[:fit_end][clock.reindex(returns.loc[:fit_end].index)==state].mean()) for asset in ASSETS} for state in STATES}
        actual_clock=clock.get(target) if target<=fit_end else None
        record=dict(origin=str(origin.date()),target=str(target.date()),train_last_origin=str(tx.index[-1].date()),train_target_end=str((tx.index[-1]+pd.offsets.MonthEnd(1)).date()),
                    mu=mu,parts=parts,drivers=drivers,training=observations,actual={a:number(future.loc[origin,a]) for a in ASSETS},p_riskon=number(pr*100),p_parts={k:number(v*100) if v is not None else None for k,v in pp.items()},
                    realized_riskon=number(risk.loc[origin]),clock=prediction,clock_prob=clean_json(cp),clock_label_cutoff=str(fit_end.date()),cycle_perf=perf,
                    selection=selection,sequence_fit_origin=seq.origin)
        records.append(record)
        if len(records)%12==0:print('ALLOCATION',record['origin'],len(records),'selected',len(tx.columns),flush=True)
    # Evaluation labels are added after predictions, using the current 2-month release cutoff.
    cutoff=X.index[-1]-pd.offsets.MonthEnd(2)
    for record in records:
        t=pd.Timestamp(record['target']);value=clock.get(t);record['actual_clock']=value if t<=cutoff and pd.notna(value) else None
    return records


def build(d):
    X,returns,clock=feature_frame(d)
    records=walk_forward(X,returns,clock)
    if not records:raise ValueError('No allocation model forecasts')
    out=clean_json(dict(model_spec=MODEL_SPEC,as_of=d.as_of,origin=records[-1]['origin'],vintage=d.vintage,features=list(X.columns),records=records,
                       parameters=dict(minimum_training_months=MIN_TRAIN,macro_lag=2,boruta_iterations=BORUTA_ITERATIONS,boruta_trees=64,lstm_hidden=8,lstm_sequence=12,lstm_epochs=50,lstm_refit='annual',seed=17)))
    save(d.base/'allocation_model.json.gz',out)
    print('ALLOCATION COMPLETE',len(records),'origins',len(X.columns),'features',flush=True)
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();build(Data(a.as_of))
if __name__=='__main__':main()

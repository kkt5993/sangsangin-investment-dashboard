"""The saved leaderboard also contains a Transformer beyond its ten-model docs.

Add that expert to cached ten-family OOS predictions, then replay selection and
calibration in date order. Existing expensive independent model fits are reused.
"""
import copy,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from .engine import number,clean_json
from .events_data import read,save
from .ml_features import build_features
from .ml_ensemble import build as base_build,select_model,calibration


class TransformerRegressor:
    def __init__(self,epochs=60):self.epochs=epochs;self.model=None;self.columns=[];self.origin=None
    def fit(self,X,y,columns,origin,horizon):
        import torch
        torch.set_num_threads(1);torch.manual_seed(29)
        self.columns=columns;self.median=X[columns].median();self.scaler=StandardScaler()
        x=self.scaler.fit_transform(X[columns].fillna(self.median));self.mean=float(y.mean());self.sd=max(float(y.std(ddof=0)),1e-6)
        windows=np.array([x[j-11:j+1] for j in range(11,len(x))]);labels=(y.iloc[11:].to_numpy()-self.mean)/self.sd
        if len(windows)<36:raise ValueError('Insufficient Transformer labels')
        class Model(torch.nn.Module):
            def __init__(self,n):
                super().__init__();self.project=torch.nn.Linear(n,16)
                layer=torch.nn.TransformerEncoderLayer(d_model=16,nhead=2,dim_feedforward=32,dropout=0,batch_first=True,norm_first=True,activation='gelu')
                self.encoder=torch.nn.TransformerEncoder(layer,num_layers=1,enable_nested_tensor=False);self.head=torch.nn.Linear(16,1)
                position=torch.arange(12).unsqueeze(1);scale=torch.exp(torch.arange(0,16,2)*(-np.log(10000)/16));pe=torch.zeros(12,16)
                pe[:,0::2]=torch.sin(position*scale);pe[:,1::2]=torch.cos(position*scale);self.register_buffer('position',pe.unsqueeze(0))
            def forward(self,a):
                # Every token is at/before the prediction origin; no future tokens.
                return self.head(self.encoder(self.project(a)+self.position)[:,-1]).squeeze(1)
        model=Model(x.shape[1]);optimizer=torch.optim.Adam(model.parameters(),lr=.003,weight_decay=.03)
        tx=torch.tensor(windows,dtype=torch.float32);ty=torch.tensor(labels,dtype=torch.float32)
        for _ in range(self.epochs):
            optimizer.zero_grad();loss=torch.nn.functional.mse_loss(model(tx),ty);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step()
        model.eval();self.model=model;self.origin=origin;self.train_origin=str(X.index[-1].date());self.train_end=str((X.index[-1]+pd.offsets.MonthEnd(horizon)).date())
    def predict(self,X):
        import torch
        x=self.scaler.transform(X[self.columns].tail(12).fillna(self.median))
        with torch.no_grad():return float(self.model(torch.tensor(x[None],dtype=torch.float32))[0])*self.sd+self.mean


def augment(base,X,p,epochs=60):
    result=copy.deepcopy(base);history=[];model=TransformerRegressor(epochs);h=base['horizon'];y=((p.shift(-h)/p-1)*100).reindex(X.index)
    for i,old in enumerate(base['records']):
        origin=old['origin'];date=pd.Timestamp(origin);selection=next(s for s in reversed(base['selections']) if s['origin']<=origin)
        if model.model is None or i%12==0:
            tx=X.loc[:date-pd.offsets.MonthEnd(h)];ty=y.reindex(tx.index);known=ty.notna();model.fit(tx.loc[known],ty.loc[known],selection['selected'],origin,h)
        predictions={k:v for k,v in old['models'].items() if not k.startswith('Ens-')}
        predictions['Transformer']=number(model.predict(X.loc[:date]));values=list(predictions.values())
        predictions['Ens-Mean']=number(np.mean(values));predictions['Ens-Median']=number(np.median(values))
        selected,nknown=select_model(history,origin,predictions);pred=predictions[selected];prob,interval,ncal=calibration(history,origin,selected,pred)
        sequence=selected in ['LSTM','Transformer'];features=model.columns if sequence else list(dict.fromkeys(selection['selected']+(model.columns if selected.startswith('Ens-') else [])))
        record=dict(old,models=predictions,selected_model=selected,prediction=pred,probability=prob,interval=interval,selection_observations=nknown,calibration_observations=ncal,
                    transformer_fit_origin=model.origin,feature_count=len(features),model_fit_origin=model.origin if sequence else selection['origin'],
                    train_last_origin=model.train_origin if sequence else str((pd.Timestamp(selection['train_target_end'])-pd.offsets.MonthEnd(h)).date()),
                    train_target_end=model.train_end if sequence else selection['train_target_end'])
        history.append(record)
    result.update(records=history,latest_features=features,base_signature=base['signature'],model_spec=2)
    result['parameters'].update(transformer_hidden=16,transformer_heads=2,transformer_layers=1,transformer_sequence=12,transformer_refit_months=12,transformer_epochs=epochs)
    return clean_json(result)


def build(d):
    base=base_build(d);out=dict(base,model_spec=2,targets={})
    for key,target in base['targets'].items():
        sig=hashlib.sha256(Path(__file__).read_bytes()+target['signature'].encode()).hexdigest();resource='ml_transformer/'+key+'.json.gz';old=d.resource(resource)
        if old.exists() and read(old).get('signature')==sig:result=read(old);print('TRANSFORMER CACHE',key,flush=True)
        else:
            X,p=build_features(d,target['symbol']);result=augment(target,X,p);result['signature']=sig;save(d.base/resource,result);print('TRANSFORMER COMPLETE',key,len(result['records']),flush=True)
        out['targets'][key]=result
    return out

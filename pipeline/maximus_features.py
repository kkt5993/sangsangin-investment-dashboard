"""MAXIMUS inputs and target units, using only completed information months."""
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.filters.hp_filter import hpfilter
from statsmodels.tsa.stattools import adfuller
from .ml_features import build_features,rolling_z
from .technical_scan import wilder

CORE=['day_ret5','day_ret10','day_vol21','day_vol_ratio','day_drop2','day_rsi',
      'cmp_overheat','cmp_crash','cmp_turn','tech_rsi6','tech_drawdown12','anchor_gap']
MACRO_TARGETS=[('DGS10','미국채 10Y 금리','금리 %'),('CL=F','WTI 유가','USD/배럴'),
               ('KRW=X','원/달러 환율','KRW/USD'),('DX-Y.NYB','달러인덱스','지수'),
               ('GC=F','금','USD/트로이온스'),('CPIAUCSL','미국 CPI YoY','YoY %')]


def rsi(s,n):
    delta=s.diff();up=wilder(delta.clip(lower=0),n);down=wilder((-delta).clip(lower=0),n)
    return (100-100/(1+up/down.replace(0,np.nan))).mask((down==0)&(up>0),100).mask((down==0)&(up==0),50)


def expanding_z(s):
    mean=s.expanding(36).mean();sd=s.expanding(36).std(ddof=0)
    return ((s-mean)/sd.replace(0,np.nan)).mask(sd==0,0)


def endpoint_cycle(s):
    """Two HP filters re-estimated at each historical endpoint, never globally."""
    result=pd.Series(np.nan,index=s.index)
    for i in range(59,len(s)):
        q=s.iloc[:i+1]
        if q.notna().sum()<60 or pd.isna(q.iloc[-1]):continue
        # Interior gaps use earlier observations only; no backward fill.
        q=q.ffill().dropna()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            cycle,_=hpfilter(q,lamb=129600);_,smooth=hpfilter(cycle,lamb=14)
        result.iloc[i]=smooth.iloc[-1]
    return result


def target_series(d,key,mode):
    """CPI is change in YoY percentage points; yield is relative level change.

    CPI observation month M is conservatively usable at the end of M+1.
    A forecast origin is an information month, not an undisclosed release date.
    Missing CPI observations stay missing in the labels.
    """
    if key=='CPIAUCSL':
        raw=d.mac(key).resample('ME').last().reindex(pd.date_range('2004-01-31',pd.Timestamp(d.as_of)-pd.offsets.MonthEnd(1),freq='ME'))
        level=raw.pct_change(12,fill_method=None).mul(100).shift(1)
        return dict(level=level,technical=raw.shift(1),daily=None,kind='diff',unit='YoY %',observation_lag=1)
    if key=='DGS10':daily=d.mac(key);level=daily.resample('ME').last()
    else:daily=d.price(key);level=d.monthly(key)
    level=level.loc[:pd.Timestamp(d.as_of)-pd.offsets.MonthEnd(1)]
    return dict(level=level,technical=level,daily=daily,kind='ret',unit=dict((k,u) for k,_,u in MACRO_TARGETS).get(key,'가격'),observation_lag=0)


def build_inputs(d,key,mode):
    context=target_series(d,key,mode);p=context['technical'];level=context['level']
    X,_=build_features(d,'^KS11' if key.endswith('.KS') or key=='^KS11' else '^GSPC')
    X=X.drop(columns=['OWN_VOL12','OWN_MA10_DISTANCE']);index=X.index.intersection(p.index);X=X.reindex(index);p=p.reindex(index)
    f={};r=p.pct_change(fill_method=None)
    for n in [1,2,3,6,9,12,24,36]:f['tech_return'+str(n)]=p.pct_change(n,fill_method=None)*100
    for a,b in [(1,3),(3,12),(6,12),(12,24)]:f[f'tech_accel{a}_{b}']=f['tech_return'+str(a)]/a-f['tech_return'+str(b)]/b
    for n in [3,6,12,24]:
        f['tech_vol'+str(n)]=r.rolling(n).std()*np.sqrt(12)*100
        f['tech_ma'+str(n)]=(p/p.rolling(n).mean()-1)*100
    f['tech_vol_ratio']=f['tech_vol3']/f['tech_vol12']
    for a,b in [(3,12),(6,24)]:f[f'tech_mgap{a}_{b}']=(p.rolling(a).mean()/p.rolling(b).mean()-1)*100
    for n in [6,14]:f['tech_rsi'+str(n)]=rsi(p,n)
    for n in [6,12]:
        x=np.arange(n);den=((x-x.mean())**2).sum()
        f['tech_slope'+str(n)]=np.log(p.where(p>0)).rolling(n).apply(lambda y:np.dot(x-x.mean(),y-y.mean())/den,raw=True)*100
    for n in [3,6,12,24,36]:f['tech_drawdown'+str(n)]=(p/p.rolling(n).max()-1)*100
    for n in [12,24,36]:f['tech_z'+str(n)]=rolling_z(p,n)
    # The S&P target uses the other national index, never itself, for relative strength.
    benchmark=d.monthly('^KS11' if key.endswith('.KS') or key=='^GSPC' else '^GSPC').reindex(index)
    for n in [6,12]:f['tech_relative'+str(n)]=p.pct_change(n,fill_method=None)*100-benchmark.pct_change(n,fill_method=None)*100
    daily=context['daily']
    if daily is not None:
        daily=daily.loc[:index[-1]];dr=daily.pct_change(fill_method=None);day={}
        for n in [5,10,20,60]:day['day_ret'+str(n)]=daily.pct_change(n,fill_method=None)*100
        for n in [21,63]:day['day_vol'+str(n)]=dr.rolling(n).std()*np.sqrt(252)*100
        day['day_vol_ratio']=day['day_vol21']/day['day_vol63'];day['day_skew']=dr.rolling(63).skew();day['day_kurt']=dr.rolling(63).kurt()
        for threshold,n in [(2,21),(3,63)]:day['day_drop'+str(threshold)]=(dr<-threshold/100).astype(float).where(dr.notna()).rolling(n).sum()
        day['day_worst']=dr.rolling(21).min()*100
        for n in [50,200]:day['day_below'+str(n)]=(daily<daily.rolling(n).mean()).astype(float).where(daily.rolling(n).mean().notna()).rolling(21).mean()*100
        day['day_ma_gap']=(daily.rolling(50).mean()/daily.rolling(200).mean()-1)*100;day['day_ma200']=(daily/daily.rolling(200).mean()-1)*100
        day['day_high252']=(daily/daily.rolling(252).max()-1)*100;day['day_low252']=(daily/daily.rolling(252).min()-1)*100
        day['day_rsi']=rsi(daily,14);day['day_weekly_rsi']=rsi(daily.resample('W-FRI').last(),14)
        macd=daily.ewm(span=12,adjust=False,min_periods=12).mean()-daily.ewm(span=26,adjust=False,min_periods=26).mean();day['day_macd']=(macd-macd.ewm(span=9,adjust=False,min_periods=9).mean())/daily*100
        day['day_up_share']=(dr>0).astype(float).where(dr.notna()).rolling(21).mean()*100
        for name,s in day.items():f[name]=s.resample('ME').last().reindex(index)
    for a,b,mult,label in [('TQQQ','QQQ',3,'leverage_us'),('122630.KS','069500.KS',2,'leverage_kr')]:
        if d.price(a).empty or d.price(b).empty:f[label]=pd.Series(np.nan,index=index)
        else:
            lhs=d.monthly(a).pct_change(fill_method=None);rhs=d.monthly(b).pct_change(fill_method=None)
            f[label]=((lhs-mult*rhs)*100).reindex(index)
    current=pd.concat([X,pd.DataFrame(f,index=index)],axis=1)
    groups={'demand':['UMCSENT','RSAFS','KR_EXPORT'], 'it':['SOX_3m','KR_EXPORT'],
            'policy':['FEDFUNDS','KR_BASE','T10Y2Y'], 'inflation':['CPIAUCSL','PCEPILFE','OIL_YoY'],
            'production':['INDPRO','PAYEMS','PERMIT'], 'risk':['NFCI','VIX','BAMLH0A0HYM2']}
    for group,names in groups.items():
        values=pd.concat([expanding_z(current[k]) for k in names],axis=1);cycle=endpoint_cycle(values.mean(axis=1).where(values.notna().sum(axis=1)>=2))
        f['cycle_'+group]=cycle;f['cycle_'+group+'_d3']=cycle.diff(3);f['cycle_'+group+'_lag1']=cycle.shift(1)
    def combine(names,signs=None):
        names=[n for n in names if n in current];values=pd.concat([expanding_z(current[n])*(signs or {}).get(n,1) for n in names],axis=1)
        return values.mean(axis=1).where(values.notna().sum(axis=1)>=max(2,len(names)//2))
    f['cmp_overheat']=combine(['tech_rsi6','tech_ma12','leverage_us','VIX_z'],{'VIX_z':-1})
    f['cmp_crash']=combine(['tech_drawdown12','day_drop2','day_vol_ratio','GAMMA_TERM','SKEW_z'],{'tech_drawdown12':-1})
    f['cmp_turn']=(f['cmp_overheat']-f['cmp_crash']).diff()
    anchor=level.reindex(index).rolling(120,min_periods=36).median()
    f['anchor_gap']=anchor-level.reindex(index) if context['kind']=='diff' else (anchor/level.reindex(index)-1)*100
    result=pd.concat([X,pd.DataFrame(f,index=index)],axis=1).replace([np.inf,-np.inf],np.nan)
    context.update(level=level.reindex(index),technical=p)
    return result,context


class StationarySIS:
    """ADF decision, correlations, selection and imputation are fitted in-window."""
    def fit(self,X,y):
        self.transforms={};self.report=[]
        for name in X:
            q=X[name].dropna();before=None;after=None;diff=False
            if len(q)<(24 if name in CORE else max(36,len(X)*.7)) or q.std()<1e-9:continue
            try:before=float(adfuller(q,maxlag=min(6,len(q)//10),autolag='AIC')[1])
            except ValueError:continue
            # The structural anchor consumes the actual level gap, not its change.
            diff=before>.1 and name!='anchor_gap';self.transforms[name]=diff
            if diff:
                z=X[name].diff().dropna()
                try:after=float(adfuller(z,maxlag=min(6,len(z)//10),autolag='AIC')[1])
                except ValueError:pass
            self.report.append(dict(name=name,adf_p=before,difference=diff,adf_p_after=after))
        prepared=self.transform(X,selected=False);corr=prepared.corrwith(y).abs().dropna();k=min(50,max(30,len(y.dropna())//3))
        ranked=sorted(corr.index,key=lambda n:(-corr[n],n));core=[k for k in CORE if k in corr]
        self.columns=list(dict.fromkeys(ranked[:k]+core))
        if not self.columns:raise ValueError('No stationary SIS inputs')
        self.median=prepared[self.columns].median();self.mean=prepared[self.columns].fillna(self.median).mean()
        for row in self.report:row.update(selected=row['name'] in self.columns,core=row['name'] in core,correlation=float(corr.get(row['name'],0)))
        return self
    def transform(self,X,selected=True):
        out=pd.DataFrame({name:X[name].diff() if diff else X[name] for name,diff in self.transforms.items()},index=X.index)
        return out[self.columns].fillna(self.median) if selected else out


def target_labels(context):
    level=context['level']
    return level.shift(-1)-level if context['kind']=='diff' else (level.shift(-1)/level-1)*100


def feature_domain(name):
    return 'I' if name.startswith(('tech_','day_','cmp_','leverage_')) or any(s in name for s in ['VIX','SKEW','MOVE','EPU','GPR','CONCENTRATION','TAIL','DROP','BELOW','WORST','KR_DEPOSIT','KR_MARGIN']) else 'R'

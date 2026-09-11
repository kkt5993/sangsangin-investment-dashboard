"""Constrained allocation, auditable costs, and the reference's comparison panels."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf
from .engine import number,clean_json,curve,table,bars,heat,performance,observed_resample
from .events_data import read
from .allocation_model import ASSETS,STATES,MODEL_SPEC,aligned_price,feature_frame

UNIVERSE=[('SPY','미국 주식','주식'),('EFA','선진국 주식','주식'),('EEM','신흥국 주식','주식'),('QQQ','대형 성장','주식'),
 ('IWD','가치','주식'),('IWM','소형','주식'),('MTUM','모멘텀','주식'),('USMV','저변동','주식'),('SCHD','배당','주식'),
 ('XLK','기술','주식'),('SMH','반도체','주식'),('XLF','금융','주식'),('XLE','에너지','주식'),('XLV','헬스케어','주식'),('ARKK','혁신','주식'),
 ('EWY','한국','국가지수'),('EWJ','일본','국가지수'),('EWG','독일','국가지수'),('EWU','영국','국가지수'),('MCHI','중국','국가지수'),('INDA','인도','국가지수'),('EWT','대만','국가지수'),
 ('IEF','중기 국채','채권'),('TLT','장기 국채','채권'),('LQD','회사채','채권'),('GLD','금','실물'),('DBC','원자재','실물'),('VNQ','리츠','리츠'),
 ('BTC-USD','비트코인','크립토'),('UUP','달러','외환'),('FXE','유로','외환'),('FXY','엔','외환'),('BIL','단기 국채 현금 대용','현금')]
GROUPS=dict((s,g) for s,_,g in UNIVERSE)
CAPS={'주식':.50,'국가지수':.25,'채권':.50,'실물':.25,'리츠':.10,'크립토':.10,'외환':.15,'현금':1.}
MAPPING={s:('주식' if g in ['주식','국가지수'] else '채권' if g=='채권' else '금' if s=='GLD' else '원자재' if s=='DBC' else '달러' if g=='외환' else g) for s,_,g in UNIVERSE if s!='BIL'}


def constrained_target(cov,symbols,signal,vol_target=.10):
    """Inverse-volatility tilt, cap projection, then unlevered volatility scaling."""
    cash=symbols.index('BIL');sigma=np.sqrt(np.diag(cov));base=np.divide(1,sigma,out=np.zeros_like(sigma),where=sigma>1e-10);base[cash]=0
    base=base/base.sum()*.98;base[cash]=.02
    values=np.array([signal.get(s,np.nan) if signal.get(s) is not None else np.nan for s in symbols],dtype=float)
    mask=np.isfinite(values);z=np.zeros(len(symbols))
    if mask.sum()>1 and np.std(values[mask])>1e-8:z[mask]=(values[mask]-np.mean(values[mask]))/np.std(values[mask])
    tilt=base*np.exp(np.clip(.5*1.1*z,-1.1,1.1));tilt[cash]=.02;tilt/=tilt.sum()
    constraints=[{'type':'eq','fun':lambda w:w.sum()-1}]
    for group,cap in CAPS.items():
        ix=np.array([i for i,s in enumerate(symbols) if GROUPS[s]==group],dtype=int)
        if len(ix):constraints.append({'type':'ineq','fun':lambda w,ix=ix,cap=cap:cap-w[ix].sum()})
    bounds=[(0,1 if s=='BIL' else .1) for s in symbols]
    result=minimize(lambda w:float(np.sum((w-tilt)**2)),np.eye(1,len(symbols),cash)[0],method='SLSQP',bounds=bounds,constraints=constraints,options={'ftol':1e-11,'maxiter':300})
    if not result.success:raise ValueError('Allocation cap projection failed: '+result.message)
    w=np.maximum(result.x,0);w/=w.sum();cash_weight=np.eye(1,len(symbols),cash)[0]
    predicted=lambda x:float(np.sqrt(max(0,x@cov@x)))
    if predicted(w)>vol_target:
        lo,hi=0.,1.
        for _ in range(45):
            scale=(lo+hi)/2
            if predicted(scale*w+(1-scale)*cash_weight)>vol_target:hi=scale
            else:lo=scale
        w=lo*w+(1-lo)*cash_weight
    if predicted(w)>vol_target+1e-6:raise ValueError('Cash volatility exceeds target')
    assert abs(w.sum()-1)<1e-8 and w.min()>=0
    for group,cap in CAPS.items():assert sum(w[i] for i,s in enumerate(symbols) if GROUPS[s]==group)<=cap+1e-6
    return pd.Series(w,index=symbols),predicted(w)


def simulate(prices,targets,cost_bps=10):
    """Targets formed at month end trade at the following first session CLOSE.

    The day's return belongs to drifted old holdings; new weights start next day.
    Crypto prices were already shifted to the last fully closed UTC daily bar.
    """
    schedule={}
    for origin,w in targets.items():
        after=prices.index[prices.index>pd.Timestamp(origin)]
        if len(after):schedule[after[0]]=w.reindex(prices.columns,fill_value=0)
    if not schedule:return pd.Series(dtype=float),[],None
    daily=prices.pct_change(fill_method=None);held=pd.Series(0.,index=prices.columns);held['BIL']=1;results={};trades=[]
    first=min(schedule)
    for t,row in daily.loc[first:].iterrows():
        if t==first:gross=0.
        else:
            if row[held>1e-10].isna().any():raise ValueError('Held asset has a missing return at '+str(t.date()))
            gross=float((held*row.fillna(0)).sum());held=held*(1+row.fillna(0))/(1+gross)
        fee=0.
        if t in schedule:
            target=schedule[t];turn=float((target-held).abs().sum());fee=turn*cost_bps/10000;held=target
            trades.append(dict(date=str(t.date()),gross_turnover=number(turn*100),one_way_turnover=number(turn*50),fee_bps=number(fee*10000)))
        results[t]=(1+gross)*(1-fee)-1
    return pd.Series(results,dtype=float),trades,held


def mapped_signal(mu,monthly,origin,symbols):
    out={}
    for s in symbols:
        if s=='BIL':continue
        asset=MAPPING[s];value=mu.get(asset)
        if value is None:out[s]=None;continue
        anchor=ASSETS[asset]
        r=monthly[[s,anchor]].loc[:origin].dropna().tail(36) if s!=anchor else None
        beta=1.
        if r is not None:
            if len(r)<24 or r.iloc[:,1].var()<=0:out[s]=None;continue
            beta=float(r.iloc[:,0].cov(r.iloc[:,1])/r.iloc[:,1].var())
        out[s]=beta*value
    return out


def monthly_performance(returns):
    return [(str(t.date()),float(v)) for t,v in (1+returns).cumprod().resample('ME').last().items()]


def allocation_views(d,obj):
    file=d.resource('allocation_model.json.gz')
    if not file.exists():return
    model=read(file);records=model['records'];last=records[-1]
    if model.get('model_spec')!=MODEL_SPEC:raise ValueError('Allocation model specification changed; retrain before rendering')
    expected=str(d.monthly('SPY').index[-1].date())
    if model['origin']!=expected:raise ValueError('Allocation model must be refreshed for the latest closed month')
    prices=pd.concat({s:aligned_price(d,s) for s,_,_ in UNIVERSE},axis=1);daily=prices.pct_change(fill_method=None)
    monthly=prices.resample('ME').last().pct_change(fill_method=None)*100
    targets={k:{} for k in ['ML 국면','틸트 OFF','경기국면','60/40','동일가중']};vols={};signals={}
    for r in records[-96:]:
        t=pd.Timestamp(r['origin']);history=daily.loc[:t].tail(252)
        eligible=[s for s in prices if history[s].notna().sum()>=126 and prices.loc[:t,s].iloc[-1]>0]
        h=history[eligible].dropna()
        if len(h)<100 or 'BIL' not in eligible:raise ValueError('Insufficient joint return covariance')
        covariance=LedoitWolf().fit(h).covariance_*252
        signal=mapped_signal(r['mu'],monthly,t,eligible)
        cyc=mapped_signal(r['cycle_perf'][r['clock']],monthly,t,eligible)
        for label,sig in [('ML 국면',signal),('틸트 OFF',{}),('경기국면',cyc)]:
            w,vol=constrained_target(covariance,eligible,sig);targets[label][r['origin']]=w;vols[label]=vol
        targets['60/40'][r['origin']]=pd.Series({'SPY':.6,'IEF':.4,'BIL':0})
        targets['동일가중'][r['origin']]=pd.Series(1/len(eligible),index=eligible)
        signals[r['origin']]=signal
    simulations={k:simulate(prices,w) for k,w in targets.items()}
    performance_rows=[[label,*[performance(a[0]).get(k) for k in ['cagr','vol','sharpe','mdd']]] for label,a in simulations.items()]
    # Publish the exact target used by this view so the cockpit cannot use a
    # separate, hard-coded portfolio. Percentages share the UI's precision.
    current=targets['ML 국면'][last['origin']]
    obj['allocation_book']=clean_json(dict(schema_version=1,label='ML 국면',as_of=d.as_of,
        origin=last['origin'],target=last['target'],model_vintage=model['vintage'],
        expected_vol_pct=vols['ML 국면']*100,
        weights=[dict(symbol=s,name=n,group=g,weight_pct=number(current.get(s,0)*100)) for s,n,g in UNIVERSE],
        performance=[dict(strategy=k,start=str(a[0].index[0].date()),end=str(a[0].index[-1].date()),
                          **performance(a[0])) for k,a in simulations.items() if len(a[0])],
        cost_bps=10,sharpe_rf=0,performance_months=len(targets['ML 국면'])))
    histories={k:pd.DataFrame(w).T.fillna(0) for k,w in targets.items()}
    group_names=list(CAPS);wh=histories['ML 국면'].tail(12).iloc[::-1]
    group_history=[[str((pd.Timestamp(t)+pd.offsets.MonthEnd(1)).date())[:7],*[number(row[[s for s in row.index if GROUPS[s]==g]].sum()*100) for g in group_names]] for t,row in wh.iterrows()]
    instrument_history=[[str((pd.Timestamp(t)+pd.offsets.MonthEnd(1)).date())[:7],*[number(row.get(s,0)*100) for s,_,_ in UNIVERSE]] for t,row in wh.iterrows()]
    forecasts=pd.Series({pd.Timestamp(r['origin']):r['p_riskon'] for r in records})
    known=[r for r in records if r['realized_riskon'] is not None];cycle_known=[r for r in records if r['actual_clock'] is not None]
    diagnostics=[]
    for asset in ASSETS:
        pairs=[(r['mu'][asset],r['actual'][asset]) for r in records if r['mu'][asset] is not None and r['actual'][asset] is not None]
        hit=np.mean([np.sign(a)==np.sign(b) for a,b in pairs])*100 if pairs else None
        ic=np.corrcoef(np.asarray(pairs).T)[0,1] if len(pairs)>2 else None
        diagnostics.append([asset,ASSETS[asset],last['mu'][asset],number(hit),number(ic),len(pairs)])
    sections=[]
    for label in ['ML 국면','경기국면']:
        benchmark_labels=['ML 국면','틸트 OFF','60/40'] if label=='ML 국면' else ['경기국면','틸트 OFF','60/40']
        w=targets[label][last['origin']]
        sections.append(dict(type='allocation',title=label+' 배분 · '+last['target'][:7]+' 목표',group='자산배분',
            weights=sorted([dict(name=n+' · '+s,value=number(w.get(s,0)*100)) for s,n,_ in UNIVERSE],key=lambda a:a['value'],reverse=True),
            groups=[dict(name=g,value=number(sum(w.get(s,0) for s,_,sg in UNIVERSE if sg==g)*100)) for g in CAPS],
            chart=curve('누적성과 · 첫 리밸런싱 직전=1',[(key,observed_resample((1+simulations[key][0]).cumprod()),'left') for key in benchmark_labels],'자산배수'),
            performance=table('비용 후 성과',['전략','CAGR %','변동성 %','Sharpe rf=0','MDD %'],[r for r in performance_rows if r[0] in benchmark_labels+['동일가중']]),
            note='원점 '+last['origin']+' · 수축 공분산 예상 변동성 '+str(number(vols[label]*100))+'% · 다음 달 첫 거래일 종가에 적용 · 최근 편도 회전율 '+str(simulations[label][1][-1]['one_way_turnover'])+'%'))
    sections += [table('최근12개월 자산군 목표비중 %',['적용월',*group_names],group_history),table('최근12개월 ETF별 목표비중 %',['적용월',*[s for s,_,_ in UNIVERSE]],instrument_history),
       table('현재 국면·예측 구성',['항목','값'],[['모델 계산 기준일',model['as_of']],['모델 빈티지',model['vintage']],['예측 원점',last['origin']],['예측 대상월',last['target']],['다음달 경기국면',last['clock']],['리스크온 P(주식>채권) %',last['p_riskon']],*[['확률 '+k+' %',v] for k,v in last['p_parts'].items()],['리스크온 OOS 적중 %',number(np.mean([(r['p_riskon']>=50)==bool(r['realized_riskon']) for r in known])*100)],['리스크온 OOS 수',len(known)],['경기국면 OOS 적중 %',number(np.mean([r['clock']==r['actual_clock'] for r in cycle_known])*100)],['경기국면 OOS 수',len(cycle_known)],['국면 실측 학습 마지막월',last['clock_label_cutoff']]]),
       curve('리스크온 확률 · 최근24개월', [('앙상블 P(주식>채권)',forecasts.tail(24),'left')], '%','',guides=[50],limits=[0,100]),
       table('자산군 다음달 절대수익률 예측',['자산군','대표 ETF','μ %','OOS 방향 적중 %','IC','OOS 수'],diagnostics),
       table('경기국면 예측 이력 · 최근24개월',['원점','대상월','예측','현재 빈티지 실제','학습 국면 마지막월'],[[r['origin'],r['target'],r['clock'],r['actual_clock'],r['clock_label_cutoff']] for r in records[-24:][::-1]])]
    perf=last['cycle_perf'];sections.append(heat('국면별 자산 월평균 수익률 · 학습 가능 기간',list(ASSETS),[dict(name=s,group='경기국면',values=[perf[s][a] for a in ASSETS]) for s in STATES]))
    sections[-1]['type']='preference'
    cross=[]
    for asset in ASSETS:
        mu=last['mu'][asset];p=perf[last['clock']][asset];pref=None if p is None else 1 if p>=.3 else -1 if p<=-.3 else 0
        verdict='미산출' if mu is None or pref is None else '중립' if pref==0 else '정합' if (mu>0)==(pref>0) else '상충'
        cross.append([asset,mu,p,pref,verdict])
    sections.append(table('수익률 예측과 경기국면의 비교',['자산군','다음달 μ %','예측 국면 역사 월평균 %','선호 +1/0/−1','방향 비교'],cross))
    _,_,clock=feature_frame(d);style={s:n for s,n in [('IWD','가치'),('QQQ','성장'),('MTUM','모멘텀'),('QUAL','퀄리티'),('USMV','저변동'),('IWM','소형'),('SCHD','배당'),('SPY','대형')]}
    style_returns=pd.concat({n:d.monthly(s).pct_change(fill_method=None)*100 for s,n in style.items()},axis=1).loc[:last['clock_label_cutoff']]
    sections.append(heat('국면별 스타일·팩터 월평균 수익률 · 배분 대상과 구분',list(style.values()),[dict(name=s,group='스타일',values=[number(v) for v in style_returns.loc[clock.reindex(style_returns.index)==s].mean()]) for s in STATES]))
    sections[-1]['type']='preference'
    drivers=sorted(last.get('drivers',[]),key=lambda r:r['value'],reverse=True)[:7]
    sections.append(bars('리스크온 분류 드라이버 · LightGBM 분할 빈도 비율',[(r['name'],r['value']) for r in drivers]))
    selection=last['selection'];sections.append(table('모델 선택·훈련 계약',['항목','값'],[['74개 후보',', '.join(model['features'])],['이번 학습의 가용 후보',selection['candidates']],['선택 수',len(selection['selected'])],['선택 상태',{'confirmed':'확정 변수','confirmed+tentative':'확정 없음 · 미확정 변수','rank fallback':'우세 변수 없음 · 순위 보조모형'}[selection['mode']]],['Boruta 최대 반복',model['parameters']['boruta_iterations']],['선택 피처',', '.join(selection['selected'])],['미확정 후보',', '.join(selection['tentative'])],['회귀','ElasticNet / RandomForest / LightGBM 평균'],['리스크온','Logistic+LightGBM 평균, Markov, 12개월 LSTM 중앙값'],['경기국면','LightGBM 4-class'],['최소 학습월',model['parameters']['minimum_training_months']],['최신 LSTM 재학습 원점',last['sequence_fit_origin']]]))
    sections.append(table('리밸런싱 거래비용 원장 · 최근12회',['체결 기준 종가일','총 비중 변동 %','편도 회전율 %','차감 비용 bp'],[[a['date'],a['gross_turnover'],a['one_way_turnover'],a['fee_bps']] for a in simulations['ML 국면'][1][-12:][::-1]]))
    for s in sections:s['group']='자산배분'
    obj['sections']=obj['sections'][:3]+clean_json(sections)
    obj['source']+=' · OECD SDMX CLI (USA/KOR/JPN/CHN)'
    obj['method_note']='33개 대표 ETF·BTC의 USD 배분을 기존 자산·스캐너에 추가했습니다. 74개 팀 피처의 월별 Boruta, 3개 회귀 앙상블, 분류·Markov·LSTM 리스크온, 4개 경기국면을 독립 계산합니다. 성장=OECD 미국 선행지수의3개월 변화, 물가=CPI YoY의3개월 변화. 거시 입력·국면 학습은2개월 시차이며 최신 수정 빈티지입니다. 자산별 μ는 대표자산 예측×36개월 Beta(최소24개월); FXE/FXY도 달러 대표 ETF에 대한 실제 Beta로 부호를 정합니다. 비중은 역변동성×수축 틸트(0.5, λ1.1), Ledoit-Wolf 공분산·그룹/종목 상한·연10%변동성 타깃, 현금은BIL입니다. 최근96개 적용월(현재 월은 가격 기준일까지)의 배분을 비교합니다. 월말 정보로 다음 첫 거래일 종가에 리밸런싱하고 다음날부터 새 비중 수익률을 적용하며 총 절대 비중 변화에10bp를 차감합니다. BTC는 미국 종가 시점 이미 종료된 전날UTC봉입니다.'
    obj['missing']=['원본의 모든 하이퍼파라미터·74개 입력명·그룹별 상한은 공개되지 않아 팀 설정을 명시했습니다. 원본 수치와 동일하다는 주장이 아닙니다.','OECD 미국·한국·일본·중국 선행지수는 공식 API의 진폭 조정 지수(장기 평균100)입니다. OECD 전체 집계는 미확보입니다. Boruta 미확정/순위 대체와 Markov 추정 불가를 진단에 표시합니다.','과거 발표·개정 빈티지를 복원한 PIT 성과가 아니며 사후 설계 OOS입니다. 두 모델의 방향 정합은 측정된 신뢰도·성공확률 증가를 의미하지 않습니다.']

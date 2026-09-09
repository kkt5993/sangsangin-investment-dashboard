"""Model evidence, aligned leading panels and source-shaped interpretation views."""
import numpy as np
import pandas as pd
from .engine import number, clean_json, module, table, heat, curve, points


def score_signal(prob,mom,median):
    if prob is None:return '미산출'
    if prob>52:return '▲▲' if mom is not None and mom>0 and median is not None and prob>median else '▲'
    if prob<48:return '▼▼' if mom is not None and mom<0 and median is not None and prob<median else '▽'
    return '—'


def display_z(s):
    sd=s.std(ddof=0)
    return (s-s.mean())/sd if sd>0 else s*0


def zones(s):
    if not len(s):return []
    low,high=s.quantile([.25,.75]);out=[]
    for t,v in s.items():
        if v<=low or v>=high:out.append(dict(start=str((t-pd.offsets.MonthEnd(1)).date()),end=str(t.date()),kind='high' if v>=high else 'low'))
    return out


def metrics(records,name=None):
    pairs=[(r['models'][name] if name else r['prediction'],r['actual']) for r in records if r['actual'] is not None and (name is None or r['models'].get(name) is not None)]
    if not pairs:return [0,None,None,None]
    pred,actual=np.asarray(pairs).T
    return [len(pairs),number(np.mean(np.sign(pred)==np.sign(actual))*100),number(np.mean(np.abs(pred-actual))),number(np.sqrt(np.mean((pred-actual)**2)))]


def build_view(d,raw):
    sections=[];summary=[];hit_rows=[];leaderboards={};score_series={};evals=[]
    targets=raw['targets'];ordered=sorted(targets.values(),key=lambda t:(['KOSPI','NASDAQ','SP500'].index(t['code']),t['horizon']))
    for target in ordered:
        records=target['records'];latest=records[-1];h=target['horizon'];name=target['name'];group=name+f' · {h}M';p=d.monthly(target['symbol'])
        known_all=[r for r in records if r['actual'] is not None];known=known_all[-120:]
        score=pd.Series({pd.Timestamp(r['origin']):r['probability'] for r in known_all if r['probability'] is not None},dtype=float)
        score_series[target['code']+'_'+str(h)+'M']=score
        whole=pd.Series({pd.Timestamp(r['origin']):r['probability'] for r in records if r['probability'] is not None},dtype=float)
        current=pd.Timestamp(latest['origin']);mom=number(whole.diff().get(current));median=number(whole.loc[:current].median())
        signal=score_signal(latest['probability'],mom,median);trend='상승 추세' if p.iloc[-1]>p.rolling(10).mean().iloc[-1] and p.pct_change(12,fill_method=None).iloc[-1]>0 else '추세 조건 미충족'
        summary.append([group,latest['origin'],latest['target'],latest['selected_model'],latest['probability'],latest['prediction'],signal,trend])
        matched=p.reindex(score.index);lead=curve(group+' · 장기 선행 신호와 지수', [('ML score z',display_z(score),'left'),(name+' z',display_z(matched),'left')],'표시기간 z-score',guides=[0])
        lead['zones']=zones(score)
        detail=curve('최근36개월 · ML score와 지수',[('P(상승)',score.tail(36),'left'),(name,p.reindex(score.tail(36).index),'right')],'%','지수',[50]);detail['markers']=True;detail['zones']=zones(score.tail(36))
        charts=[lead,detail]
        if h==1:
            returns=pd.Series({pd.Timestamp(r['target']):r['actual']/100 for r in known});position=pd.Series({pd.Timestamp(r['target']):float(np.sign(r['prediction'])) for r in known});cost=position.diff().fillna(position).abs()*.0005
            charts.append(curve('월말 가정 체결 · 방향전략과 보유',[('방향전략',(1+position*returns-cost).cumprod(),'left'),('Buy & Hold',(1+returns).cumprod(),'left')],'시작=1'))
        rows=[]
        for r in records[-24:][::-1]:
            t=pd.Timestamp(r['origin']);v=whole.get(t);dv=whole.diff().get(t);dy=whole.diff(12).get(t)
            quadrant='미산출' if pd.isna(dv) or pd.isna(dy) else '강세 가속' if dv>=0 and dy>=0 else '회복 반전' if dv>=0 else '과열 둔화' if dy>=0 else '약세 가속'
            rows.append([r['origin'],r['target'],r['selected_model'],r['probability'],number(dv),number(dy),quadrant,r['prediction'],r['actual'],None if r['actual'] is None else '적중' if np.sign(r['prediction'])==np.sign(r['actual']) else '미적중',number(p.get(t)),number(p.pct_change(fill_method=None).get(t)*100),number(p.pct_change(12,fill_method=None).get(t)*100),score_signal(r['probability'],number(dv),number(whole.loc[:t].median()))])
        section=dict(type='ml',title=group,group=group,records=records[-37:],horizon=h,origin=latest['origin'],latest=latest,charts=charts,importance=[],
                     detail_table=table('최근24개월 원점·예측·실현',['원점','타깃','당시 선택','P상승 %','score MoM %p','score YoY %p','4분면','예측 %','실현 %','방향','지수','지수 MoM %','지수 YoY %','신호'],rows),
                     diagnostics=dict(features=target['latest_features'],minimum_training_months=target['parameters']['minimum_training_months'],macro_lag_months=2,models=list(latest['models'])),
                     model_note='과거에 만기가 끝난 예측의 최근120개 적중률·RMSE로 당시 모델을 선택. 최초24개 평가 전에는 평균 앙상블. 장기/36개월 선은 채점 가능한 원점만 표시하며 최신 예측은 위와 표에 분리합니다. z·사분위 음영은 표시기간 정규화이고 모형 입력이 아닙니다.')
        sections.append(section)
        hit_rows.append(dict(name=group,group=name,values=[1 if np.sign(r['prediction'])==np.sign(r['actual']) else -1 for r in known[-36:]]))
        leaderboards.setdefault(target['code'],dict(name=name,rows=[]))
        by_name={r['name']:r for r in leaderboards[target['code']]['rows']}
        for model in latest['models']:
            stats=metrics(known,model);evals.append([group,model,*stats,'현재 선택' if latest['selected_model']==model else ''])
            if model not in by_name:by_name[model]=dict(name=model,values=[None,None]);leaderboards[target['code']]['rows'].append(by_name[model])
            by_name[model]['values'][0 if h==1 else 1]=stats[1]
    overview=[dict(table('ML 전망 요약 · 3지수×1M/3M',['대상','원점','타깃','현재 선택','P상승 %','기대수익 %','신호','10MA·12M 추세'],summary),group='전망 요약')]
    # Common scored origins only: the 3M leg is never padded with an unscored value.
    score_frame=pd.concat(score_series,axis=1).dropna();comp=score_frame.mean(axis=1)
    if len(comp):
        indices=[('KOSPI','^KS11','KOSPI'),('NASDAQ','^IXIC','NASDAQ'),('S&P500','^GSPC','SP500')]
        combined=curve('6타깃 ML 컴포짓·지수3개·시장별 ML3개',[('ML composite',display_z(comp),'left')]+[(name,display_z(d.monthly(symbol).reindex(comp.index)),'left') for name,symbol,_ in indices]+[(name+' ML',display_z(score_frame[[code+'_1M',code+'_3M']].mean(axis=1)),'left') for name,_,code in indices],'표시기간 z-score',guides=[0])
        combined['series'][0].update(color='#b78c34',width=3)
        for i,color in enumerate(['#227d9c','#b05781','#735da7']):
            combined['series'][i+1].update(color=color,opacity=.5,legend=False)
            combined['series'][i+4].update(color=color,dashed=True)
        combined['zones']=zones(comp);combined['group']='전망 요약';overview.append(combined)
        lag_rows=[]
        for lag in range(-2,4):
            values=[]
            for symbol in ['^KS11','^IXIC','^GSPC']:
                price=d.monthly(symbol);values.append(price.pct_change(fill_method=None).shift(-lag).reindex(comp.index))
            aggregate=pd.concat(values,axis=1).mean(axis=1,skipna=False);pair=pd.concat([comp,aggregate],axis=1).dropna()
            lag_rows.append(dict(name=str(lag),value=number(pair.iloc[:,0].corr(pair.iloc[:,1])) if len(pair)>=24 else None,observations=len(pair)))
        overview.append(dict(type='lagcorrelation',title='컴포짓과 t+L개월 월수익률의 상관 · L>0 선행',group='전망 요약',rows=lag_rows,note='지수3개 월수익률의 같은 비중 평균과 비교한 설명적 상관입니다. 지연월 탐색의 선택편향을 교정한 예측 검정이 아니며 선행 신호선을 이동시키지 않습니다.'))
    sections=overview+sections
    sections += [dict(heat('월별 방향 적중 · 최근36개 채점 원점',[str(i-35) for i in range(36)],hit_rows),group='모델 비교'),
                 dict(type='modelleaderboard',title='모델별 OOS 방향 적중률 · 지수별 1M/3M',group='모델 비교',panels=list(leaderboards.values())),
                 dict(table('모형별 최근120개 채점 결과',['타깃','모델','표본','적중 %','MAE %p','RMSE %p','표시'],evals),group='모델 비교')]
    feature_panels=[]
    for code,label in [('SP500','US · S&P500 1M'),('KOSPI','KR · KOSPI 1M')]:
        target=targets[code+'_1M'];selection=target['selections'][-1]
        chosen=set(selection['selected']);rows=[dict(name=('★ ' if r['forced'] else '')+r['name'],value=r['wins'],forced=r['forced']) for r in selection['ranking'] if r['name'] in chosen]
        feature_panels.append(dict(title=label,rows=rows,repeats=selection['repeats']))
        if target.get('explanation'):
            e=dict(target['explanation'],title=label+' · LightGBM TreeSHAP',group='SHAP 해석');e['rows']=e['rows'][:15];sections.append(e)
    sections.append(dict(type='featureselection',title='Shadow 최대 중요도 초과 횟수 · US/KR',group='변수 선택',panels=feature_panels))
    coverage=[]
    for target in ordered:
        sel=target['selections'][-1];latest=target['records'][-1]
        coverage.append([target['name']+' '+str(target['horizon'])+'M',target['as_of'],target['vintage'],len(target['feature_names']),len(sel['selected']),len(sel['forced']),', '.join(sel['unavailable_forced']),latest['model_fit_origin'],latest['lstm_fit_origin'],latest['transformer_fit_origin'],', '.join(sel['convergence_warnings']) or '없음'])
    sections.append(dict(table('입력·학습·미확보 진단',['타깃','모델 기준일','빈티지','후보','선택','강제','강제 중 자료 부족','현재 모델 학습 원점','LSTM 학습 원점','Transformer 학습 원점','최근 학습 수렴 경고'],coverage),group='변수 선택'))
    note='월별 거시·시장 입력을 사용한 회귀 전망입니다. 선형·트리·거리·신경망 모델 및 평균/중앙값 앙상블을 과거 평가만으로 선택합니다. 3M은3개월 누적 수익률이며 학습·오차 보정·모델 선택에서 만기를 기다립니다. 68/90% 구간은 과거 선택 모델의 OOS 잔차 분위, P상승은 예측/잔차표준편차의 정규 누적확률이며 보장된 빈도가 아닙니다. 거시는2개월 시차의 현재 수정 빈티지입니다. 방향전략은 월말 가정 체결·편도5bp, 실제 배포 시점과 체결을 복원한 성과가 아닙니다.'
    out=module('ml',d.as_of,note,clean_json(sections),[('예측 대상',len(targets)),('최신 후보 입력',len(ordered[0]['feature_names'])),('최신 예측 원점',ordered[0]['origin'])],missing=['원본 전체 하이퍼파라미터·선택 주기 설정과 수치 동등성은 미검증입니다. 과거 발표/수정 빈티지와 과거 모형 설계를 복원한 PIT 실시간 성과가 아닙니다.',
                    'ICE 신용스프레드는 공개자료가 최근3년으로 제한되어 장기 z-score·일부 강제 위험 입력의 준비 기간이 부족합니다. 제외된 입력을 진단에 표시합니다.',
                    '추가 원자료가 필요한 블록: '+', '.join(raw['missing'])+'.','TreeSHAP는 별도 LightGBM 학습표본 해석이며 당시 선택 모델의 OOS 기여도·경제적 인과 효과가 아닙니다. US 변수 선택 패널은 S&P500 대표이며 Nasdaq은 별도 선택합니다.'])

    out['model_spec']=raw['model_spec'];return out

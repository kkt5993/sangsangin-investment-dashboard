"""MoE target cards and auditable forecast comparisons, without live-server claims."""
import numpy as np
import pandas as pd
from scipy.stats import norm
from .engine import number,clean_json,module,table,curve
from .maximus_moe import NAMES
from .maximus_features import feature_domain


def directional_test(pred,actual):
    """PT binary sign test. Zero outcomes/predictions are outside two categories."""
    a=np.asarray(pred);b=np.asarray(actual);valid=(a!=0)&(b!=0);a=a[valid]>0;b=b[valid]>0;n=len(a)
    if n<24:return None
    px=a.mean();py=b.mean();chance=px*py+(1-px)*(1-py)
    vp=chance*(1-chance)/n
    vs=((2*py-1)**2*px*(1-px)+(2*px-1)**2*py*(1-py))/n+4*px*py*(1-px)*(1-py)/n**2
    if vp<=vs+1e-12:return None
    z=(np.mean(a==b)-chance)/np.sqrt(vp-vs)
    return number(2*norm.sf(abs(z)))


def loss_test(pred,actual):
    """Two-sided DM: squared loss vs zero change, Bartlett HAC variance."""
    a=np.asarray(pred);b=np.asarray(actual);loss=b*b-(b-a)**2;n=len(loss)
    if n<24:return None
    centered=loss-loss.mean();lag=min(n-1,int(4*(n/100)**(2/9)))
    variance=np.dot(centered,centered)/n
    for k in range(1,lag+1):variance+=2*(1-k/(lag+1))*np.dot(centered[k:],centered[:-k])/n
    if variance<=1e-12:return 1. if abs(loss.mean())<=1e-12 else None
    return number(2*norm.sf(abs(loss.mean()/np.sqrt(variance/n))))


def compare(records):
    known=[r for r in records if r['actual'] is not None][-120:]
    if not known:return {}
    actual=np.array([r['actual'] for r in known]);pred=np.array([r['prediction'] for r in known]);mean=np.array([r['baseline_mean'] for r in known])
    equal=np.array([np.mean(list(r['experts'].values())) for r in known]);momentum=np.array([r['momentum'] if r['momentum'] is not None else 0 for r in known])
    hit=lambda a:float(np.mean(np.sign(a)==np.sign(actual))*100)
    singles={n:hit(np.array([r['experts'][n] for r in known])) for n in NAMES};den=np.square(actual-mean).sum()
    return dict(observations=len(known),start=known[0]['target'],end=known[-1]['target'],hit=hit(pred),equal_hit=hit(equal),momentum_hit=hit(momentum),single_hits=singles,best_single=max(singles.values()),
        r2=100*(1-np.square(actual-pred).sum()/den) if den>1e-12 else None,rmse=float(np.sqrt(np.mean((actual-pred)**2))),mae=float(np.mean(np.abs(actual-pred))),pt_p=directional_test(pred,actual),dm_p=loss_test(pred,actual))


def target_card(target):
    records=target['records'];latest=records[-1];selection=target['selections'][-1];e=target['explanation'];kind=target['kind'];cur=latest['current'];pred=latest['prediction'];sigma=latest['sigma']
    level=lambda value:cur+value if kind=='diff' else cur*(1+value/100)
    bands={str(z):[level(pred-z*sigma),level(pred+z*sigma)] for z in [1,1.96]} if sigma is not None and cur is not None else {}
    gate_known=[r for r in records if r['target']<latest['origin'] and r['actual'] is not None][-48:]
    experts=[dict(name=n,weight=latest['weights'][n]*100,prediction=latest['experts'][n],hit=np.mean([np.sign(r['experts'][n])==np.sign(r['actual']) for r in gate_known])*100 if gate_known else None) for n in NAMES]
    diagnostics=table('ADF·SIS·핵심 입력',['변수','영역','ADF p','차분','차분 후 p','|상관|','선택','핵심'],[[r['name'],feature_domain(r['name']),r['adf_p'],'Δ1' if r['difference'] else '유지',r['adf_p_after'],r['correlation'],'●' if r['selected'] else '', '★' if r['core'] else ''] for r in selection['report']])
    reported={r['name'] for r in selection['report']}
    diagnostics['rows'] += [[name,feature_domain(name),None,'관측·분산/ADF 요건 미충족',None,None,'',''] for name in target['feature_names'] if name not in reported]
    origins=table('최근24개 예측 원점',['정보 원점','예측 정보월','학습 라벨 종료','당시 예측','실현','P상승 %','학습 원점','게이트 표본'],[[r['origin'],r['target'],r['train_target_end'],r['prediction'],r['actual'],r['probability'],r['fit_origin'],r['gate']['observations']] for r in records[-24:][::-1]])
    unit='지수' if target['mode']=='idx' else target['unit']
    card=dict(symbol=target['symbol'],name=target['name'],mode=target['mode'],kind=kind,unit=unit,origin=latest['origin'],target=latest['target'],
        observation_lag=target['observation_lag'],current=cur,forecast=level(pred) if cur is not None else None,change=pred,probability=latest['probability'] if cur is not None else None,sigma=sigma,bands=bands,history=target['history'],
        experts=experts,override=latest['override'],explanation=e,feature_count=latest['feature_count'],candidate_features=len(target['feature_names']),diagnostics=diagnostics,ledger=origins,metrics=compare(records),warnings=selection['warnings'],
        fit_origin=latest['fit_origin'],calibration_observations=latest['calibration_observations'],gate=latest['gate'],anchor_note='학습 가능한 과거120개월·최소36개월 중앙 레벨로 월15% 수렴하는 팀 앵커. 지수 이익추정 앵커는 미확보.')
    if target['symbol']=='DGS10':card['bp_change']=(card['forecast']-cur)*100 if cur is not None else None
    known=[r for r in records if r['actual'] is not None][-120:]
    if kind=='ret' and target['symbol']!='DGS10' and known:
        a=pd.Series([r['actual']/100 for r in known],index=pd.to_datetime([r['target'] for r in known]));position=pd.Series([np.sign(r['prediction']) for r in known],index=a.index)
        cost=position.diff().fillna(position).abs()*.0005;strategy=position*a-cost
        wealth=(1+strategy).cumprod();bh=(1+a).cumprod();std=strategy.std(ddof=1)
        card['strategy']=dict(cumulative=(wealth.iloc[-1]-1)*100,buy_hold=(bh.iloc[-1]-1)*100,sharpe=strategy.mean()/std*np.sqrt(12) if std else None,mdd=(wealth/wealth.cummax().clip(lower=1)-1).min()*100)
        card['strategy_chart']=curve('월말 가정 · 방향전략과 기초가격 보유',[('방향전략',wealth,'left'),('가격 보유',bh,'left')],'시작=1')
    return card


def build_view(d,raw):
    sections=[];summary=[];by_mode={}
    for target in raw['targets'].values():
        if not target['records']:continue
        card=target_card(target);group='지수' if target['mode']=='idx' else '매크로' if target['mode']=='macro' else '종목'
        raw_fund=d.fund.get(target['symbol'],{});info=raw_fund.get('info',{})
        if target['mode']=='stock' and info:
            card['unit']=info.get('currency') or card['unit']
            card['stock_context']=dict(retrieved_at=raw_fund.get('retrieved_at'),currency=info.get('currency'),sector=info.get('sector'),industry=info.get('industry'),
                market_cap=number(info.get('marketCap')),trailing_pe=number(info.get('trailingPE')),forward_pe=number(info.get('forwardPE')),
                earnings_growth=number(info['earningsGrowth']*100) if info.get('earningsGrowth') is not None else None,
                sales_growth=number(info['revenueGrowth']*100) if info.get('revenueGrowth') is not None else None,target=number(info.get('targetMeanPrice')),analysts=number(info.get('numberOfAnalystOpinions')))
        if target['symbol']=='^IXIC':group='추가 지수'
        by_mode.setdefault(group,[]).append(card)
        summary.append([group,card['name'],card['origin'],card['target'],card['current'],card['forecast'],card['change'],card['probability'],card['feature_count']])
    for group in ['지수','매크로','종목','추가 지수']:
        if group in by_mode:sections.append(dict(type='moe',title=group+' · 1M 전문가 예측',group=group,cards=by_mode[group],select_target=group=='종목'))
    sections.append(dict(table('전체 캐시 예측',['구분','대상','정보 원점','예측 정보월','현재 레벨','1M 레벨','변화 % 또는 %p','P상승 %','선택 변수'],summary),group='방법론'))
    steps=[['자료','완료월·현재 수정 빈티지의 거시2개월 시차. CPI 관측월은 다음 월말 정보로 정렬.'],['정상화·선택','훈련창 ADF p>.10이면 차분, SIS |상관| 상위 min(50,max(30,N/3))+가용 핵심 입력. Anchor gap은 수준 보존.'],['학습','10전문가·최소96라벨·6개월 재학습·12개월 시퀀스. 학습 라벨 끝과 예측 원점 사이1개월 추가 간격.'],['게이트','만기·엠바고를 지난 최근48개 OOS. 로지스틱 C=.5 25%+역MSE/균등50:50 프라이어75%.'],['범위·보정','전문가 출력 학습평균±2.5σ 제한. 붕괴85/99분위 심도에 따라 강세60% 삭감·최대3%p 틸트. CPI 차분에는 적용하지 않음.'],['통계','최대120 OOS, 방향·RMSE·MAE·과거 학습평균 대비 R². PT 양측·DM 제곱손실/무변화 대비 HAC 양측. 모형 가족의 우월성 검정으로 해석하지 않음.'],['귀속','고정 게이트에서 학습평균으로12토큰 변수 치환한 occlusion. 불안정한 R/I 합계 재조정은 생략하고 상호작용 잔차를 별도 표시.']]
    sections.append(dict(table('계산 과정',['단계','계약'],steps),group='방법론'))
    if raw['unavailable']:sections.append(dict(table('이력 부족',['종목','사유'],[[r['symbol'],r['reason']] for r in raw['unavailable']]),group='종목'))
    note='3모드 1개월 Mixture of Experts입니다. 예측은 이 PC의 완료월 자료로 계산한 캐시입니다. 10개 전문가·ADF/SIS·과거 OOS 로지스틱/성능 게이트·붕괴 보정을 적용합니다. 금리의 변화율은 채권 수익률이 아니며 CPI는 YoY의 %p 변화입니다. 68/95% 팬은 당시 과거 OOS 잔차의 정규 근사입니다.'
    result=module('maximus',d.as_of,note,clean_json(sections),[('캐시 대상',len(summary)),('전문가',10),('정보 원점',summary[0][2] if summary else None)],missing=[
        '지수 밸류배수×이익추정 대신 과거 레벨 중앙값 앵커를 사용합니다. SEC filed 정렬 재무·한국 외국인 역사·일부 확장 거시 입력은 미연결입니다.',
        '원본과 다른 팀 하이퍼파라미터·가용 입력을 공개합니다. 현재 수정 거시에 시차를 준 결과이며 PIT 실시간 OOS가 아닙니다.',
        '완료월 추론입니다. 부분월 실시간 추론·웹 임의 종목 학습 서버는 아직 연결하지 않았습니다.',
        '변수 영향력은 고정 게이트 occlusion이며 SHAP/인과 효과가 아닙니다. 모델 선택·조정 규칙을 정한 기간과 분리한 전향 검증은 후속 대상입니다.',
        '방향전략은 월말 가정·편도5bp·rf=0이며 실제 주문·차입·선물 롤 비용을 복원하지 않습니다. CPI와 금리 수준에는 투자 수익률을 표시하지 않습니다.'])
    result['model_spec']=raw['model_spec'];return result

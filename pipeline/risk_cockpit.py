"""Current allocation targets, fixed-book risk, factors and matured ML evidence.

No network calls or model retraining. The stress matrix is an explicit team
assumption, not a reconstructed historical observation or a forecast.
"""
import numpy as np
import pandas as pd
from .engine import number, clean_json, table
from .store import ROOT, read_json
from .events_data import read
from .allocation_model import aligned_price
from .allocation_views import UNIVERSE

GROUP = '리스크 콕핏'
FACTORS = [('시장 β','SPY',None),('사이즈(소형)','IWM','SPY'),('가치','IWD','SPY'),
           ('모멘텀','MTUM','SPY'),('퀄리티','QUAL','SPY'),('저변동성','USMV','SPY'),
           ('금리(듀레이션)','TLT',None),('달러','UUP',None),('크레딧','HYG','IEF')]
NOTE = ('콕핏은 멀티에셋의 ML 국면 현재 목표비중을 공유합니다. 최근120개 완료월에 같은 비중을 매월 적용한 USD 가상 장부로, '
        '월 VaR/CVaR는 수익률 하위 분위·평균(손실은 음수), MDD는 월말 기준입니다. 실제 보유·동적 배분 성과와 구분합니다. '
        '9요인은 최근60개월 ETF 대용 수익률의 동시 OLS이며, 스트레스5종은 공개한 팀 충격 가정표의 가중합입니다. '
        '신호 신뢰도는 비용 후 배분 OOS와 만기 종료 ML을 각각 집계합니다. 과거 발표 빈티지를 복원한 실시간 성과는 아닙니다.')


def validated_weights(book, as_of):
    if book.get('schema_version') != 1 or book.get('label') != 'ML 국면':
        raise ValueError('Cockpit requires the allocation view target contract')
    end = str((pd.Timestamp(as_of).replace(day=1)-pd.Timedelta(days=1)).date())
    target = str((pd.Timestamp(end)+pd.offsets.MonthEnd(1)).date())
    if book.get('as_of') != as_of or book.get('origin') != end or book.get('target') != target:
        raise ValueError('Cockpit allocation target is stale or has a mismatched month')
    rows = book['weights']; symbols = [r['symbol'] for r in rows]
    if len(symbols) != len(set(symbols)) or set(symbols) != {s for s,_,_ in UNIVERSE}:
        raise ValueError('Cockpit allocation universe mismatch')
    w = pd.Series({r['symbol']:r['weight_pct']/100 for r in rows},dtype=float)
    if not np.isfinite(w).all() or (w < 0).any() or abs(w.sum()-1) > 1e-6:
        raise ValueError('Cockpit allocation must be finite, long-only and sum to one')
    # Percentage values are rounded for publication; remove only that rounding.
    return w/w.sum()


def monthly_returns(d, symbols):
    """All assets use the same last US session of each completed month.

    Never bridge a missing month, accept a stale last quote, or include a partial
    month. aligned_price supplies the allocation's previous-UTC-day BTC bar.
    """
    end = pd.Timestamp(d.as_of).replace(day=1)-pd.Timedelta(days=1)
    spy = d.price('SPY').loc[:end]
    if spy.empty:raise ValueError('Missing US month-end calendar')
    calendar = pd.date_range(spy.index[0].to_period('M').to_timestamp('M'),end,freq='ME')
    dates = spy.index.to_series().resample('ME').last().reindex(calendar)
    prices = {}
    for symbol in symbols:
        p = aligned_price(d,symbol).loc[:end]
        prices[symbol] = pd.Series([p.get(t,np.nan) if pd.notna(t) else np.nan for t in dates],index=calendar)
    return pd.DataFrame(prices).pct_change(fill_method=None)


def fixed_book(returns, weights, months=120):
    held = weights[weights > 0]
    sample = returns.reindex(columns=held.index).tail(months)
    if len(sample) != months or not np.isfinite(sample.to_numpy()).all():
        raise ValueError('Cockpit needs '+str(months)+' consecutive complete held-asset monthly returns')
    if (sample <= -1).any().any():raise ValueError('Invalid held-asset total return')
    book = sample.mul(held).sum(axis=1)
    wealth = (1+book).cumprod();drawdown = wealth/wealth.cummax().clip(lower=1)-1
    q95,q99 = book.quantile([.05,.01],interpolation='linear')
    tail = book[book <= q95]
    hhi = float((weights**2).sum())
    metrics = dict(vol_pct=book.std(ddof=1)*np.sqrt(12)*100,var95_pct=q95*100,
        cvar95_pct=tail.mean()*100,var99_pct=q99*100,mdd_pct=drawdown.min()*100,
        hhi=hhi,effective_assets=1/hhi,cash_pct=weights.get('BIL',0)*100,
        noncash_pct=(1-weights.get('BIL',0))*100,months=len(book),tail95_months=len(tail),
        start=str(book.index[0].date()),end=str(book.index[-1].date()))
    return book,wealth,drawdown,clean_json(metrics)


def factor_exposure(returns, book, months=60):
    x = pd.DataFrame({name:returns[a]-(returns[b] if b else 0) for name,a,b in FACTORS})
    window = pd.concat([book.rename('book'),x],axis=1).tail(months)
    sample = window.dropna()
    if len(sample) < 36:raise ValueError('Insufficient joint factor observations')
    y = sample['book'].to_numpy();f = sample.drop(columns='book').to_numpy()
    design = np.column_stack([np.ones(len(f)),f]);coef,_,rank,_ = np.linalg.lstsq(design,y,rcond=None)
    if rank != len(FACTORS)+1:raise ValueError('Factor matrix is rank deficient')
    fitted = design@coef;residual = y-fitted;tss = np.sum((y-y.mean())**2)
    condition = float(np.linalg.cond(np.column_stack([np.ones(len(f)),(f-f.mean(axis=0))/f.std(axis=0,ddof=1)])))
    return clean_json(dict(months=len(sample),start=str(sample.index[0].date()),end=str(sample.index[-1].date()),
        intercept_pct=coef[0]*100,r2=1-np.sum(residual**2)/tss if tss>0 else None,
        rank=int(rank),standardized_condition=condition,
        excluded_months=[str(t.date()) for t in window.index.difference(sample.index)],
        exposures=[dict(name=name,beta=beta,level='큼' if abs(number(beta))>=.7 else '보통' if abs(number(beta))>=.3 else '낮음',
                        proxy=a+(' − '+b if b else '')) for (name,a,b),beta in zip(FACTORS,coef[1:])],
        observations=[[str(t.date()),*row] for t,row in zip(sample.index,np.column_stack([y,fitted,residual])*100)]))


def stress_bucket(symbol):
    mapping={'IEF':'중기국채','TLT':'장기국채','LQD':'회사채','GLD':'금','DBC':'원자재',
             'VNQ':'리츠','BTC-USD':'크립토','UUP':'달러','FXE':'유로','FXY':'엔','BIL':'현금'}
    if symbol in mapping:return mapping[symbol]
    if symbol in {s for s,_,g in UNIVERSE if g in ['주식','국가지수']}:return '주식'
    raise ValueError('Unmapped stress instrument: '+symbol)


def stress_results(weights, config):
    buckets=config['buckets']
    if config.get('schema_version')!=1 or config.get('unit')!='asset_return_pct' or len(set(buckets))!=len(buckets):
        raise ValueError('Invalid stress matrix contract')
    totals={b:0. for b in buckets}
    for s,w in weights.items():totals[stress_bucket(s)]+=w
    if not np.isclose(sum(totals.values()),1):raise ValueError('Uncovered stress weights')
    output=[]
    if len(config['scenarios'])!=5 or len({s['id'] for s in config['scenarios']})!=5:
        raise ValueError('Expected five distinct stress assumptions')
    for s in config['scenarios']:
        shocks=np.asarray(s['shocks_pct'],dtype=float)
        if len(shocks)!=len(buckets) or not np.isfinite(shocks).all() or (shocks < -100).any():
            raise ValueError('Invalid stress shock vector')
        contributions=shocks*np.asarray([totals[b] for b in buckets])
        output.append(dict(id=s['id'],name=s['name'],impact_pct=float(contributions.sum()),
                           shocks_pct=list(shocks),contributions_pct=list(contributions)))
    return clean_json(dict(basis=config['basis'],buckets=buckets,weights_pct=[totals[b]*100 for b in buckets],scenarios=output))


def directional_confidence(records, as_of, horizon=1, band=1.):
    """Percent returns; strict +/-band boundaries, matured targets only."""
    cutoff=pd.Timestamp(as_of).replace(day=1)-pd.Timedelta(days=1)
    eligible=[];seen=set()
    for r in records:
        if r.get('actual') is None or r.get('prediction') is None or pd.Timestamp(r['target'])>cutoff:continue
        origin=pd.Timestamp(r['origin']);target=pd.Timestamp(r['target'])
        if target != origin+pd.offsets.MonthEnd(horizon) or origin>=target or r['origin'] in seen:
            raise ValueError('ML confidence target horizon or uniqueness mismatch')
        if pd.Timestamp(r['train_target_end'])>origin:raise ValueError('ML training label matures after forecast origin')
        if not np.isfinite([r['prediction'],r['actual']]).all():raise ValueError('Invalid ML score values')
        seen.add(r['origin']);eligible.append(r)
    eligible.sort(key=lambda r:r['origin'])
    def category(v):return 1 if v>band else -1 if v< -band else 0
    pred=np.asarray([category(r['prediction']) for r in eligible]);actual=np.asarray([category(r['actual']) for r in eligible])
    def score(mask):
        n=int(mask.sum());hits=int((pred[mask]==actual[mask]).sum())
        return dict(n=n,hits=hits,hit_pct=hits/n*100 if n else None)
    return clean_json(dict(horizon=horizon,band_pct=band,all=score(np.ones(len(pred),dtype=bool)),
        directional=score(pred!=0),up=score(pred==1),down=score(pred==-1),neutral=score(pred==0),
        start=eligible[0]['target'] if eligible else None,end=eligible[-1]['target'] if eligible else None,
        excluded=len(records)-len(eligible)))


def load_confidence(d):
    rows=[]
    for code,label in [('KOSPI','KOSPI'),('NASDAQ','NASDAQ'),('SP500','S&P500')]:
        for horizon in [1,3]:
            file=d.resource('ml_transformer/'+code+'_'+str(horizon)+'M.json.gz')
            if not file.exists():
                rows.append(dict(name=label,horizon=horizon,status='missing',reason='전체 OOS 예측 원장 미확보'));continue
            raw=read(file)
            if raw.get('model_spec')!=2 or raw['code']!=code or raw['horizon']!=horizon:
                raise ValueError('ML confidence cache contract mismatch')
            if raw['as_of']>d.as_of:raise ValueError('ML cache comes from a future calculation')
            rows.append(dict(name=label,status='available',model_as_of=raw['as_of'],model_vintage=raw['vintage'],
                             **directional_confidence(raw['records'],d.as_of,horizon)))
    return rows


def views(d, obj, allocation):
    obj['sections']=[s for s in obj['sections'] if s.get('group')!=GROUP]
    obj['cards']=[c for c in obj.get('cards',[]) if 'VaR' not in c[0]]
    contract=allocation.get('allocation_book')
    if not contract:
        obj.pop('cockpit',None)
        obj['sections'].insert(0,dict(type='text',title='리스크 콕핏 · 비중 자료 미확보',group=GROUP,
            text='멀티에셋의 현재 ML 국면 목표비중을 생성해야 콕핏을 계산할 수 있습니다.'))
        return
    weights=validated_weights(contract,d.as_of)
    symbols=list(dict.fromkeys([*weights.index,*[s for _,a,b in FACTORS for s in [a,b] if s]]))
    returns=monthly_returns(d,symbols)
    book,wealth,drawdown,metrics=fixed_book(returns,weights)
    factors=factor_exposure(returns.loc[:book.index[-1]],book)
    stress=stress_results(weights,read_json(ROOT/'config/risk_stress.json'))
    confidence=load_confidence(d)
    obj['cockpit']=clean_json(dict(schema_version=1,as_of=d.as_of,allocation=contract,metrics=metrics,
                                  factors=factors,stress=stress,confidence=confidence))
    sections=[table('리스크 콕핏 · ML 국면 현재 목표비중',['지표','값','단위·범위'],[
        ['비중 원점 / 적용월',contract['origin']+' / '+contract['target'][:7],'실제 보유가 아닌 목표비중'],
        ['연환산 변동성',metrics['vol_pct'],'% · 120개월 표본 표준편차 × √12'],
        ['월 VaR95',metrics['var95_pct'],'% · 수익률 하위5% 분위'],
        ['월 CVaR95',metrics['cvar95_pct'],'% · 하위 꼬리 '+str(metrics['tail95_months'])+'개월 평균'],
        ['월 VaR99',metrics['var99_pct'],'% · 수익률 하위1% 분위'],
        ['최대 낙폭 MDD',metrics['mdd_pct'],'% · 최초 자산1 포함, 월말 관측'],
        ['집중도 HHI',metrics['hhi'],'Σ 비중² · ETF/상품 단위'],
        ['유효 자산 수',metrics['effective_assets'],'1 / HHI · 독립 위험요인 수와 다름'],
        ['위험자산(현금 제외)',metrics['noncash_pct'],'% · 채권·금·외환 등 모든 비BIL 포함'],
        ['현금 대용 BIL',metrics['cash_pct'],'% · 단기 국채 ETF'],
        ['역사 표본',str(metrics['months'])+'개월',metrics['start']+' ~ '+metrics['end']],
        ['배분 예상 변동성',contract['expected_vol_pct'],'% · 최근252일 수축 공분산, 역사 변동성과 기간이 다름']]),
        table('팩터 노출 · 9요인 동시 OLS',['요인','Beta','크기','수익률 대용'],[
            [r['name'],r['beta'],r['level'],r['proxy']] for r in factors['exposures']]),
        table('스트레스 · 현재 비중 × 팀 충격 가정',['시나리오','장부 영향 %','해석'],[
            [r['name'],r['impact_pct'],'동시 충격 가정 · 역사 실현값/예측 아님'] for r in stress['scenarios']])]
    perf={r['strategy']:r for r in contract['performance']};ml=perf.get('ML 국면',{});off=perf.get('틸트 OFF',{})
    alpha=number(ml.get('sharpe',0)-off.get('sharpe',0)) if ml.get('sharpe') is not None and off.get('sharpe') is not None else None
    confidence_rows=[['배분 OOS · 비용 후 Sharpe',ml.get('sharpe'),'rf=0 · '+str(ml.get('sessions',0))+'거래일'],
        ['배분 OOS · CAGR %',ml.get('cagr'),str(ml.get('start'))+' ~ '+str(ml.get('end'))],
        ['배분 OOS · MDD %',ml.get('mdd'),'동적 비중 · 총 비중 변화에10bp 비용'],
        ['ML − 틸트 OFF Sharpe',alpha,'단순 차이 · 회귀 알파/유의성 아님']]
    for r in confidence:
        if r['horizon']!=1:continue
        if r['status']!='available':confidence_rows.append([r['name']+' 방향',None,r['reason']]);continue
        confidence_rows.append([r['name']+' 1M 방향 적중 %',r['directional']['hit_pct'],
                                '중립 예측 제외 · '+str(r['directional']['n'])+'건 · '+str(r['start'])+' ~ '+str(r['end'])])
    confidence_rows.append(['국면 안정성','국면 탭의 전이표 참조','관측 전이빈도 · 성공 확률로 해석하지 않음'])
    sections.append(table('시그널 신뢰도 · 배분 OOS와 지수 ML',['항목','값','표본·정의'],confidence_rows))
    sections += [dict(type='text',title='콕핏 계산 범위',text=NOTE+' 비중의 표시 반올림 오차만 합계1로 정규화합니다. '
        '수익률은 수정종가(배당 재투자 대용), BTC는 미국 종가에 이미 끝난 전날UTC봉입니다. 과거에 현재 비중을 알고 투자한 성과가 아닙니다.'),
        table('현재 목표비중 원장 · 멀티에셋과 공유',['자산','코드','자산군','목표 %','스트레스 분류'],[
            [r['name'],r['symbol'],r['group'],r['weight_pct'],stress_bucket(r['symbol'])] for r in contract['weights']]),
        table('팩터 회귀 진단',['항목','값'],[
            ['표본',str(factors['months'])+'개월 · '+factors['start']+' ~ '+factors['end']],['R²',factors['r2']],
            ['월 절편 %',factors['intercept_pct']],['행렬 계수(rank)',factors['rank']],['표준화 설계행렬 조건수',factors['standardized_condition']],
            ['결측으로 제외한 월',', '.join(factors['excluded_months']) or '없음'],
            ['Beta 분류','절댓값 <0.3 낮음, <0.7 보통, ≥0.7 큼'],
            ['모형','USD 장부 월수익률 = 절편 + 9요인 동시 OLS. 스타일은 SPY 대비 차이, 금리는 TLT 수익률(듀레이션 연수 아님).'],
            ['공선성','대용 ETF와 SPY 공유로 계수가 불안정할 수 있음. 순수 팩터·인과 계수·예측 신뢰도 아님.']]),
        table('스트레스 충격 가정표 · 자산 수익률 %',['시나리오',*stress['buckets']],
              [[r['name'],*r['shocks_pct']] for r in stress['scenarios']]),
        table('스트레스 자산군 기여 · 장부 %p',['시나리오',*stress['buckets']],
              [['현재 비중 %',*stress['weights_pct']]]+[[r['name'],*r['contributions_pct']] for r in stress['scenarios']]),
        dict(type='text',title='스트레스 가정 해석',text=stress['basis']+' 2008·2020은 위기 유형 이름이며 당시 실측 재현이 아닙니다. '
            '금리 +100bp는 금리 +1%p에 대한 채권·기타 자산 충격을 가정합니다. 원자재30%·달러10% 행도 다른 자산의 동시 충격을 포함합니다. '
            '현재 상품 비중을 분류별로 합산한 뒤 충격률을 곱합니다. 비선형성·기간·거래비용·후속 리밸런싱은 포함하지 않습니다.'),
        table('ML 3분류 검증 · 완료 타깃 전체 OOS',['대상','기간','분류','적중 %','적중 / 예측 수','첫 / 마지막 타깃','모델 기준일'],[
            [r['name'],str(r['horizon'])+'M',label,r[key]['hit_pct'],str(r[key]['hits'])+' / '+str(r[key]['n']),
             str(r['start'])+' / '+str(r['end']),r['model_as_of']]
            for r in confidence if r['status']=='available'
            for key,label in [('directional','방향 · 중립 예측 제외'),('all','전체 3분류'),('up','상승 예측'),('down','하락 예측'),('neutral','중립 예측')]]),
        dict(type='text',title='ML 적중률의 분모',text='예측·실현 모두 >+1% 상승, <−1% 하락, 나머지는 중립(경계 포함). '
            '방향 적중은 중립 예측만 제외하며 실제 중립을 방향 적중으로 세지 않습니다. 3M은3개월 누적 수익률이고 타깃이 겹칩니다. '
            '미만기·실현값 미확보는 제외하고 n=0은 미산출입니다. 화면의 최근37개 목록이 아닌 저장된 전체 당시 선택모델 OOS 원장을 사용합니다. '
            '현재 수정 데이터·사후 설계에 따른 검증이며 독립 실시간 운용 성과 또는 승률 보장이 아닙니다.'),
        table('고정 장부 월별 계산 원장',['월말','장부 수익률 %','누적 자산 · 시작1','낙폭 %'],[
            [str(t.date()),number(book[t]*100),number(wealth[t]),number(drawdown[t]*100)] for t in book.index[::-1]])]
    for s in sections:
        if s['type']=='table':s['readable']=True
        if s['title'].startswith(('현재 목표비중 원장','스트레스 충격 가정표','스트레스 자산군 기여','ML 3분류 검증','고정 장부 월별')):
            s['collapsed']=True
    obj['sections']=[dict(clean_json(s),group=GROUP) for s in sections]+obj['sections']
    obj['cards'] += [('모델북 월 VaR95 %',metrics['var95_pct']),('모델북 월 CVaR95 %',metrics['cvar95_pct'])]
    old='콕핏은 표시된 고정 비중 모형 장부의 120개월 역사 위험입니다.'
    obj['method_note']=obj['method_note'].replace(old,'').replace(NOTE,'').strip()+' '+NOTE

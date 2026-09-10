"""Observable US/KR warning inputs and price-based early-warning diagnostics."""
import numpy as np
import pandas as pd
from scipy.stats import kendalltau
from .engine import number,clean_json,table,curve
from .store import ROOT,read_json
from .risk_signals_data import history,FOLDER,NEWS_SOURCE
from .events_data import read

SIGNALS='신호등 US·KR'
SPECIAL='선제위험·감마'
COLORS=['🟢 정상','🟡 주의','🔴 경계','⚫ 극단']
MARKETS=['정상','주의','경계','극단']
NOTE=('신호등은 US12·KR7 관측의 값·단위·기준일을 표시합니다. 단계·합산점수는 공개한 팀 규칙이며, '
      '미확보·허용 지연을 넘긴 자료는 회색과 판정 보류로 처리합니다. SF Fed 뉴스감성은 원지수의252관측 백분위 대용으로 기사 긍정비율이 아닙니다. '
      '선제위험4개는 가격 수익률의 CSD·변동성 군집 진단으로 옵션 딜러 감마나 보정된 급락 확률이 아닙니다.')
GAP='신호등의 원본 다단계 점수·상대강도 기간·뉴스감성 분모와 CSD/군집의 세부 산식은 미공개입니다. 팀 설정과 SF Fed 백분위 대용을 명시했으며, 당시 관측 빈티지나 급락 예측력의 동등성은 미검증입니다.'


def shown(value):
    return '—' if value is None else format(value,'.6f').rstrip('0').rstrip('.')


def level(value,rule):
    if value is None or not np.isfinite(value):return None
    cuts=rule['cuts'];direction=rule['direction']
    if len(cuts)!=3 or direction not in ['high','low'] or cuts!=sorted(cuts,reverse=direction=='low'):
        raise ValueError('Risk thresholds must increase in severity order')
    return sum(value>=c if direction=='high' else value<=c for c in cuts)


def observation(series,as_of,max_age=0):
    s=series.loc[:as_of].replace([np.inf,-np.inf],np.nan).dropna()
    if s.empty:return dict(value=None,date=None,age_days=None,fresh=False)
    date=str(s.index[-1].date());age=(pd.Timestamp(as_of)-s.index[-1]).days
    return dict(value=number(s.iloc[-1]),date=date,age_days=age,fresh=0<=age<=max_age)


def percentile(s,n=252):
    return s.rolling(n,min_periods=n).apply(lambda a:100*((a<a[-1]).sum()+.5*(a==a[-1]).sum())/n,raw=True)


def inputs(d):
    us=d.price('SPY',False).index;kr=d.price('^KS11',False).index
    p=lambda s,cal:d.price(s,False).reindex(cal)
    spy=p('SPY',us);kospi=p('^KS11',kr)
    series={
        'qqq_daily':p('QQQ',us).pct_change(fill_method=None)*100,
        'spy_daily':spy.pct_change(fill_method=None)*100,
        'vix':p('^VIX',us),'death_cross':spy.rolling(50).mean()/spy.rolling(200).mean(),
        'yield_spread':d.mac('T10Y2Y'),'hy':d.mac('BAMLH0A0HYM2')*100,
        'spy_ma200':(spy/spy.rolling(200).mean()-1)*100,
        'dxy20':p('DX-Y.NYB',us).pct_change(20,fill_method=None)*100,
        'rsp_spy':(p('RSP',us)/spy).pct_change(20,fill_method=None)*100,
        'iwm_spy':(p('IWM',us)/spy).pct_change(20,fill_method=None)*100,
        'move':p('^MOVE',us),'kospi_daily':kospi.pct_change(fill_method=None)*100,
        'kosdaq_daily':p('^KQ11',kr).pct_change(fill_method=None)*100,
        'krw_daily':p('KRW=X',kr).pct_change(fill_method=None)*100,
        'kospi_ma200':(kospi/kospi.rolling(200).mean()-1)*100}
    investors,im=history(d,'investors');news,nm=history(d,'sentiment');vk,vm=history(d,'vkospi')
    raw_news=pd.Series({pd.Timestamp(r['date']):float(r['value']) for r in news},dtype=float)
    series['news']=percentile(raw_news)
    series['foreign']=pd.Series({pd.Timestamp(r['date']):r['foreign_krw']/1e8 for r in investors},dtype=float)
    series['institution']=pd.Series({pd.Timestamp(r['date']):r['institution_krw']/1e8 for r in investors},dtype=float)
    series['vkospi']=pd.Series({pd.Timestamp(r['date']):float(r['value']) for r in vk},dtype=float)
    metadata={k:dict(source='Yahoo Finance · 일자별 종가',max_age=0) for k in series}
    for k in ['yield_spread','hy']:metadata[k]=dict(source='FRED · '+('T10Y2Y' if k=='yield_spread' else 'BAMLH0A0HYM2'),max_age=7)
    metadata['news']=dict(source=NEWS_SOURCE,max_age=14,retrieved_at=nm.get('retrieved_at'))
    for k in ['foreign','institution']:metadata[k]=dict(source='KRX · 코스피 주식 순매수 금액',max_age=0,retrieved_at=im.get('retrieved_at'))
    metadata['vkospi']=dict(source='KRX · 코스피 200 변동성지수 (1300)',max_age=0,retrieved_at=vm.get('retrieved_at'))
    return series,metadata,raw_news


def snapshot(series,metadata,rules,date,market=None):
    result=[]
    for rule in rules:
        if market and rule['market']!=market:continue
        meta=metadata[rule['id']];obs=observation(series[rule['id']],date,meta['max_age'])
        tier=level(obs['value'],rule) if obs['fresh'] else None
        result.append(dict(rule,**obs,level=tier,source=meta['source'],retrieved_at=meta.get('retrieved_at'),
            max_age_days=meta['max_age'],signal=COLORS[tier] if tier is not None else '⚪ 자료 미확보' if obs['value'] is None else '⚪ 관측 지연'))
    return result


def aggregate(rows,config):
    known=[r for r in rows if r['level'] is not None]
    total=sum(config['points'][r['level']] for r in known);complete=len(known)==len(rows)
    tier=sum(total>=c for c in config['market_thresholds']) if complete else None
    return dict(points=total,available=len(known),expected=len(rows),complete=complete,level=tier,
                grade=MARKETS[tier] if tier is not None else '판정 보류')


def risk_streak(rows):
    """Consecutive fully observed sessions at score >= the warning tier.

    Incomplete observations stop evidence; they are never converted to zero risk.
    """
    if not rows or not rows[-1]['complete']:return dict(days=None,lower_bound=False)
    n=0
    for row in rows[::-1]:
        if not row['complete']:return dict(days=n,lower_bound=n>0)
        if row['level']<2:return dict(days=n,lower_bound=False)
        n+=1
    return dict(days=n,lower_bound=n>0)


def early_warning(price,config):
    p=price.tail(252+config['cluster']['long']+config['csd']['trend']+30)
    r=p.pct_change(fill_method=None);c=config['csd'];n=c['rolling']
    # A window of n returns has n-1 adjacent pairs for lag-one correlation.
    ar=r.rolling(n-1).corr(r.shift(1));variance=r.rolling(n).var(ddof=1);skew=r.rolling(n).skew().abs()
    def tau(a):return kendalltau(np.arange(len(a)),a).statistic
    trends=pd.DataFrame({k:s.rolling(c['trend']).apply(tau,raw=True) for k,s in [('variance_tau',variance),('ar1_tau',ar),('abs_skew_tau',skew)]})
    score=50*(1+trends.mean(axis=1,skipna=False));score=score.where(r.notna().cumsum()>=c['minimum_returns'])
    v=config['cluster'];rv_short=r.rolling(v['short']).std(ddof=1)*np.sqrt(252)*100
    rv_long=r.rolling(v['long']).std(ddof=1)*np.sqrt(252)*100
    expansion=(rv_short/rv_long.replace(0,np.nan)-1)*100
    ac=r.abs().rolling(v['autocorrelation']-1).corr(r.abs().shift(1))
    cluster=100*(v['weights'][0]*(expansion/v['expansion_full_pct']).clip(0,1)+v['weights'][1]*ac.clip(0,1))
    return pd.concat([trends,pd.DataFrame(dict(csd=score,cluster=cluster,rv21=rv_short,rv126=rv_long,expansion=expansion,abs_return_ar1=ac))],axis=1).replace([np.inf,-np.inf],np.nan).tail(252)


def views(d,obj):
    config=read_json(ROOT/'config/risk_signal_rules.json');rules=config['rules']
    if [sum(r['market']==m for r in rules) for m in ['US','KR']]!=[12,7]:raise ValueError('Risk panel contract needs US12/KR7 inputs')
    series,metadata,raw_news=inputs(d);rows=[];summary=[]
    for market,anchor in [('US','SPY'),('KR','^KS11')]:
        date=str(d.price(anchor,False).index[-1].date());part=snapshot(series,metadata,rules,date,market)
        rows+=part;summary.append(dict(market=market,date=date,**aggregate(part,config)))
    kr_history=[]
    for t in d.price('^KS11',False).index[-63:]:
        date=str(t.date());kr_history.append(dict(date=date,**aggregate(snapshot(series,metadata,rules,date,'KR'),config)))
    streak=risk_streak(kr_history)
    special=[];histories={};diagnostics=[]
    for market,name,symbol,anchor in [('US','S&P500','^GSPC','SPY'),('KR','KOSPI','^KS11','^KS11')]:
        f=early_warning(d.price(symbol,False).reindex(d.price(anchor,False).index),config);histories[market]=f
        last=f.iloc[-1];date=str(f.index[-1].date())
        for key,label in [('csd','선제위험 CSD'),('cluster','변동성 군집')]:
            value=number(last[key]);tier=sum(value>=c for c in config['special_thresholds']) if value is not None else None
            special.append(dict(market=market,name=name+' '+label,kind=key,value=value,date=date,
                                signal=COLORS[tier] if tier is not None else '⚪ 관측 부족·상수 구간'))
        diagnostics.append([name,date,*[number(last[k]) for k in ['variance_tau','ar1_tau','abs_skew_tau','rv21','rv126','expansion','abs_return_ar1']]])
    report_path=d.resource(FOLDER+'collection.json.gz')
    collection=read(report_path) if report_path.exists() else dict(parts=[])
    obj['risk_signals']=clean_json(dict(schema_version=1,as_of=d.as_of,rows=rows,summary=summary,kr_streak=streak,
        kr_history=kr_history,special=special,news_raw=observation(raw_news,d.as_of,14),collection=collection))
    obj['sections']=[s for s in obj['sections'] if s.get('group') not in [SIGNALS,SPECIAL]]
    obj['cards']=[c for c in obj.get('cards',[]) if not any(k in c[0] for k in ['CSD 점수','실현변동성 21D','신호등','KR 경계 연속'])]
    obj['cards'] += [(s['market']+' 신호등',s['grade']+' · '+str(s['points'])+'점 / '+str(s['available'])+'/'+str(s['expected'])+'관측') for s in summary]
    obj['cards'].append(('KR 경계 연속 관측',('미산출' if streak['days'] is None else ('≥' if streak['lower_bound'] else '')+str(streak['days'])+'일')))
    sections=[dict(table('US·KR 신호등 요약',['시장','관측일','상태','관측점수','가용 / 전체'],
        [[s['market'],s['date'],s['grade'],s['points'],str(s['available'])+' / '+str(s['expected'])] for s in summary]),group=SIGNALS)]
    for market in ['US','KR']:
        sections.append(dict(table(market+' 신호등 · '+str(sum(r['market']==market for r in rows))+'개 지표',
            ['지표','값','단위','관측일','신호','팀 주의 / 경계 / 극단'],
            [[r['name'],shown(r['value']),r['unit'],r['date'],r['signal'],('≥ ' if r['direction']=='high' else '≤ ')+' / '.join(str(v) for v in r['cuts'])] for r in rows if r['market']==market]),group=SIGNALS,readable=True))
    raw=obj['risk_signals']['news_raw']
    sections += [dict(type='text',title='신호등 계산과 미확보 처리',group=SIGNALS,text=NOTE+' 녹/황/적/흑은0/1/3/5점, 전체 합계3/6/10점부터 주의/경계/극단입니다. '
        '미확보가 있으면 관측된 점수만 보여주고 시장 판정을 보류합니다. 일자별 주가·외환 종가와 KRX 마감시각이 완전히 일치하는 장중 지표는 아닙니다.'),
        dict(table('관측 출처·지연·표시 기준',['지표','출처','실제 수집 UTC','허용 지연 달력일','가격일 대비 지연일'],[
            [r['name'],r['source'],r['retrieved_at'] or '가격·거시 빈티지 원장',r['max_age_days'],r['age_days']] for r in rows]),group=SIGNALS,collapsed=True,readable=True),
        dict(table('공개 경계값과 팀의 해석',['지표','보존 화면 경계값','팀 단계 해석'],[
            [r['name'],r['reference'],('높을수록' if r['direction']=='high' else '낮을수록')+' 주의 · 경계 포함'] for r in rows]),group=SIGNALS,collapsed=True,readable=True),
        dict(type='text',title='뉴스감성의 단위',group=SIGNALS,text='SF Fed 원지수 '+str(raw['value'])+' · 관측 '+str(raw['date'])+'. '
            '미국 경제 기사로 산출한 공식 연속지수이며 높을수록 긍정적입니다. 마지막252개 관측에서 (작은 값 수 + 동률 수/2) ÷252×100으로 백분위를 계산합니다. '
            '40/20/10 이하를 팀 주의/경계/극단으로 봅니다. 원본의40%와 분모가 같다는 뜻은 아닙니다. 주간 갱신 자료이므로 최대14달력일까지 관측일을 유지하고, 넘으면 판정을 보류합니다.'),
        dict(type='text',title='한국 시장 순매수 범위',group=SIGNALS,text='KRX 코스피 주식시장 전체의 하루 순매수 금액을1억원으로 나눕니다. ETF·ETN·ELW는 제외합니다. '
            '외국인은 기타외국인을 제외하고, 기관은 금융투자·보험·투신·사모·은행·기타금융·연기금의 합입니다. 주식 수나 대형주8종목 합계가 아닙니다.'),
        dict(type='text',title='VKOSPI의 의미',group=SIGNALS,text='KRX 코스피 200 변동성지수(1300)의 실제 종가입니다. 코스피200 옵션가격이 반영하는 향후30일 기대변동성을 연율로 나타내며, '
            '지수값은 연율 변동성의 퍼센트 값입니다. 과거 주가의 실현변동성과 다르며 아래 선제위험 진단에 대입하지 않습니다.'),
        dict(table('공식 입력 정기 수집 상태',['자료','이번 실행','마지막 성공 수집 UTC','오류 유형'],[
            [{'sentiment':'SF Fed 뉴스감성','investors':'KRX 코스피 순매수','vkospi':'KRX VKOSPI'}.get(r['part'],r['part']),
             {'reused':'기존 관측 재사용','collected':'수집·검증 완료','retained_error':'수집 실패 · 이전 관측 유지','missing_error':'수집 실패 · 미확보',
              'retained_permission_required':'인증 미사용 · 이전 관측 유지','missing_permission_required':'인증 미사용 · 미확보'}.get(r['status'],r['status']),
             r.get('retrieved_at'),r.get('error_type','—')] for r in collection['parts']]),group=SIGNALS,collapsed=True,readable=True),
        dict(table('KR 경계 연속 관측 · 최근63세션 원장',['관측일','점수','가용 / 전체','판정'],[
            [r['date'],r['points'],str(r['available'])+' / '+str(r['expected']),r['grade']] for r in kr_history[::-1]]),group=SIGNALS,collapsed=True),
        dict(type='text',title='연속일 집계 범위',group=SIGNALS,text='완전한7개 관측의 시장 점수가6 이상인 최근 연속 세션 수입니다. 미확보가 끼면 끊어 확인 가능한 하한만 표시하며 마지막 세션이 불완전하면 미산출입니다. '
            '현재 수정 빈티지의 과거 재계산이며 당시 발표·수집 시각을 복원한 운용 기록이 아닙니다.'),
        dict(table('선제위험·변동성 군집 · 4개 진단',['시장 지표','점수 / 100','관측일','상태'],[
            [r['name'],shown(r['value']),r['date'],r['signal']] for r in special]),group=SPECIAL,readable=True),
        dict(table('진단 입력 원장',['시장','관측일','분산 τ','AR1 τ','|왜도| τ','21관측 연변동성 %','126관측 연변동성 %','변동성 확장 %','|수익률| AR1'],
            [[*r[:2],*[shown(v) for v in r[2:]]] for r in diagnostics]),group=SPECIAL,readable=True),
        dict(type='text',title='CSD와 군집 점수의 계산',group=SPECIAL,text='CSD는21개 수익률의 분산·AR1·왜도 절댓값에서 최근63관측 Kendall 추세 τ를 구하고50×(1+세 τ 평균)으로 환산합니다. 최소126수익률과 모든 입력을 요구합니다. '
            '군집 점수는100×[0.5×clip((σ21/σ126−1),0,1)+0.5×clip(최근63개 절대수익률의 AR1,0,1)]입니다. '
            '두 점수 모두40부터 주의,66부터 경계이며 상수·결측 구간은 미산출입니다. 가중치·룩백은 공개한 팀 설정이고 급락 예측력은 검증되지 않았습니다. '
            '변동성 군집은 실제 옵션 감마·딜러 포지션을 측정하지 않습니다.')]
    for market,name in [('US','S&P500'),('KR','KOSPI')]:
        f=histories[market]
        sections.append(dict(curve(name+' · 선제위험과 변동성 군집 · 252관측',
            [('CSD',f.csd,'left'),('변동성 군집',f.cluster,'left')],'진단점수',guides=[40,66],limits=[0,100]),group=SPECIAL))
    obj['sections']+=clean_json(sections)
    obj['missing']=[m for m in obj.get('missing',[]) if not m.startswith('원본 CSD 임계값') and m!=GAP]+[GAP]
    old='CSD는 21일 분산·자기상관·왜도의 최근 63일 Kendall 추세 평균을 0–100으로 바꾼 진단점수입니다.'
    obj['method_note']=obj['method_note'].replace(old,'').replace(NOTE,'').strip()+' '+NOTE

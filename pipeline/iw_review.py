"""Numerical monthly reviews and versioned weekly observations, without authored prose."""
import copy,hashlib,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from .engine import number,clean_json,table
from .macro_modules import regime_frame
from .events_data import read,save
from .store import ROOT,read_json
from .ml_views import display_z,zones

INDICES=[('KOSPI','^KS11'),('NASDAQ','^IXIC'),('S&P500','^GSPC')]
ECON=['골디락스','리플레이션','스태그플레이션','침체압력']
MARKET=['금융장세(봄)','실적장세(여름)','역금융장세(가을)','역실적장세(겨울)']
RISK=['위험선호','중립','위험회피']


def last_month(date):return pd.Timestamp(date).replace(day=1)-pd.Timedelta(days=1)


def classify(growth,inflation,rate,flags):
    econ=market=risk=None
    if pd.notna(growth) and pd.notna(inflation):econ=0 if growth>=0 and inflation<0 else 1 if growth>=0 else 2 if inflation>=0 else 3
    if pd.notna(growth) and pd.notna(rate):market=0 if growth>=0 and rate<=0 else 1 if growth>=0 else 2 if rate>0 else 3
    if len(flags)==5 and all(v is not None for v in flags):risk=0 if sum(flags)<=1 else 1 if sum(flags)==2 else 2
    return econ,market,risk


def monthly_states(d):
    index=pd.date_range('2004-01-31',last_month(d.as_of),freq='ME')
    def monthly(key,lag=0,annual=False):
        source=d.mac(key)
        if source.empty:return pd.Series(np.nan,index=index)
        s=source.resample('ME').last()
        if annual:s=s.pct_change(12,fill_method=None)*100
        s.index=s.index+pd.offsets.MonthEnd(lag)
        return s.reindex(index)
    raw_econ=regime_frame(d,'US');econ=raw_econ.resample('ME').last() if not raw_econ.empty else pd.DataFrame(index=index,columns=['g','i'],dtype=float)
    econ.index=econ.index+pd.offsets.MonthEnd(2);econ=econ.reindex(index)
    ten=monthly('DGS10');nfci=d.mac('NFCI').copy()
    if nfci.empty:nfci=pd.Series(np.nan,index=index)
    nfci.index=nfci.index+pd.Timedelta(days=7);vix=d.price('^VIX')
    if vix.empty:vix=pd.Series(np.nan,index=index)
    frame=pd.DataFrame(dict(growth=econ.g,inflation=econ.i,rate=ten.diff(3),vix=vix.resample('ME').last().reindex(index),
        nfci=nfci.resample('ME').last().reindex(index),hy=monthly('BAMLH0A0HYM2'),m2=monthly('M2SL',2,True),sahm=monthly('SAHMREALTIME',2)),index=index)
    output=[]
    for t,r in frame.iterrows():
        flags=[None if pd.isna(r[k]) else bool(fn(r[k])) for k,fn in [('vix',lambda v:v>=25),('nfci',lambda v:v>0),('hy',lambda v:v>=5),('m2',lambda v:v<0),('sahm',lambda v:v>=.5)]]
        e,m,risk=classify(r.growth,r.inflation,r.rate,flags)
        output.append(dict(date=str(t.date()),economic=e,market=m,risk=risk,inputs={k:number(v) for k,v in r.items()},flags=flags,macro_observation_month=str((t-pd.offsets.MonthEnd(2)).date())))
    return output


def timeline(states,cutoff):
    rows=[r for r in states if r['date']<=str(last_month(cutoff).date())][-36:]
    return dict(type='statetimeline',title='3년 월별 국면 · 완료월 정보 기준',rows=[[r['date'],r['economic'],r['market'],r['risk']] for r in rows],
        panels=[dict(name='경제국면 · 성장×물가 방향',labels=ECON),dict(name='시장국면 · 성장×10Y금리 방향',labels=MARKET),dict(name='위험국면 · 5개 관측 조건',labels=RISK)],
        note='월말 정보 기준. 성장·물가·M2·Sahm은2개월, NFCI는7일 시차. 팀 규칙이며 확정 경기침체·수익 예측이 아닙니다. 회색은 필수 입력 미확보입니다.')


def composite_at(ml,cutoff):
    source=next((s for s in ml['sections'] if s['type']=='line' and s.get('group')=='전망 요약'),None)
    if source is None:return None
    result=copy.deepcopy(source);end=str(last_month(cutoff).date())
    for s in result['series']:
        points=[p for p in s['points'] if p[0]<=end]
        series=pd.Series({pd.Timestamp(t):v for t,v in points},dtype=float);z=display_z(series)
        s['points']=[[str(t.date()),round(float(v),3)] for t,v in z.items()]
    comp=pd.Series({pd.Timestamp(t):v for t,v in result['series'][0]['points']},dtype=float)
    result['zones']=zones(comp);result['left']='각 표시구간 z-score';return result


def state_at(states,date):
    rows=[r for r in states if r['date']<=date]
    if not rows:return None
    r=rows[-1]
    return dict(date=r['date'],economic=ECON[r['economic']] if r['economic'] is not None else '미산출',market=MARKET[r['market']] if r['market'] is not None else '미산출',risk=RISK[r['risk']] if r['risk'] is not None else '미산출')


def price_at(d,symbol,date):
    p=d.price(symbol).loc[:date]
    if p.empty or (pd.Timestamp(date)-p.index[-1]).days>7:return dict(level=None,date=None,r1w=None,ytd=None)
    previous=p.loc[:str(pd.Timestamp(date).year-1)]
    return dict(level=number(p.iloc[-1]),date=str(p.index[-1].date()),r1w=number((p.iloc[-1]/p.iloc[-6]-1)*100) if len(p)>5 else None,
        ytd=number((p.iloc[-1]/previous.iloc[-1]-1)*100) if len(previous) else None)


def model_sections(ml,horizon=1):return [s for s in ml['sections'] if s['type']=='ml' and s['horizon']==horizon]


def monthly_reviews(d,ml,states):
    out=[];models=model_sections(ml)
    months=sorted({r['target'] for s in models for r in s['records'] if r['actual'] is not None and r['target']<=str(last_month(d.as_of).date())})[-15:]
    for month in months[::-1]:
        rows=[];scored=hits=0
        for name,symbol in INDICES:
            s=next((s for s in models if s['title'].split(' · ')[0]==name),None)
            r=next((r for r in s['records'] if r['target']==month),None) if s else None
            p=price_at(d,symbol,month);hit=None
            if r and r['prediction'] is not None and r['actual'] is not None:hit=bool(np.sign(r['prediction'])==np.sign(r['actual']));scored+=1;hits+=int(hit)
            rows.append([name,p['level'],r['prediction'] if r else None,r['actual'] if r else None,'일치' if hit else '불일치' if hit is False else '미채점',r['selected_model'] if r else None,r['origin'] if r else None,r['train_target_end'] if r else None])
        out.append(dict(period=month[:7],as_of=month,scored=scored,hits=hits,summary=f'{month[:7]} · 1M 방향 {hits}/{scored} 일치',state=state_at(states,month),
            table=table('원점별 예측과 실현',['지수','월말 수준','당시 규칙 예측 %','실현 %','방향','선택 모형','예측 원점','학습 라벨 종료'],rows),
            note='현재 자료로 재생한 OOS 모형 원장입니다. 그 당시 게시한 예측이나 작성자의 과거 논평을 복원한 기록이 아닙니다.'))
    return out


def week_key(date):
    iso=pd.Timestamp(date).isocalendar();return f'{iso.year}-W{iso.week:02d}'


def weekly_frame(d,ml,states,date):
    rows=[];forecasts=[]
    for name,symbol in INDICES:
        p=price_at(d,symbol,date);rows.append([name,p['date'],p['level'],p['r1w'],p['ytd']])
        for horizon in [1,3]:
            s=next((s for s in model_sections(ml,horizon) if s['title'].split(' · ')[0]==name),None)
            eligible=[r for r in s['records'] if r['origin']<=date] if s else []
            r=eligible[-1] if eligible else None
            forecasts.append([name,horizon,r['origin'] if r else None,r['target'] if r else None,r['prediction'] if r else None,r['probability'] if r else None])
    def observed(series,lag=0):
        p=series.loc[:pd.Timestamp(date)-pd.Timedelta(days=lag)].dropna()
        return [number(p.iloc[-1]),str(p.index[-1].date())] if len(p) else [None,None]
    macro=[['VIX',*observed(d.price('^VIX'))],['미국10Y %',*observed(d.mac('DGS10'))],['NFCI · 7일 시차',*observed(d.mac('NFCI'),7)],['HY OAS %',*observed(d.mac('BAMLH0A0HYM2'))]]
    return dict(period=week_key(date),as_of=date,summary=week_key(date)+' · 지수·YTD·모형 전망 관측',state=state_at(states,str(last_month(date).date())),
        table=table('기록 기준일의 시장 관측',['지수','실제 가격일','수준','5거래일 %','YTD %'],rows),forecasts=table('원점이 지난 모형 전망',['지수','기간 M','예측 원점','타깃 월말','예측 %','P상승 %'],forecasts),
        macro=table('위험·금융여건 관측',['지표','값','실제 관측일'],macro),charts=[timeline(states,date),composite_at(ml,date)],
        note='가격 변화와 모형 전망을 기록한 규칙 요약입니다. 3M은 만기 전 실현 수익으로 채점하지 않습니다. 세계 사건이나 인과관계를 임의 서술하지 않습니다.')


def preserve_weeks(previous,frames,current_week,stamp):
    records={r['period']:r for r in previous}
    for f in frames:
        old=records.get(f['period'])
        if old and f['period']!=current_week:continue
        r=copy.deepcopy(f);r['first_recorded_at']=old['first_recorded_at'] if old else stamp;r['updated_at']=stamp
        r['retrospective']=old.get('retrospective',True) if old else f['period']!=current_week
        records[r['period']]=r
    return sorted(records.values(),key=lambda r:r['period'],reverse=True)


def iw_views(d,objects):
    ml_path=ROOT/'docs/data/ml.json';ml=read_json(ml_path);states=monthly_states(d);model_hash=hashlib.sha256(ml_path.read_bytes()).hexdigest()
    if ml['as_of']>d.as_of:raise ValueError('ML snapshot is newer than requested IW date')
    asof=pd.Timestamp(d.as_of);monday=asof-pd.Timedelta(days=asof.weekday())
    dates=[str(min(monday-pd.Timedelta(weeks=i)+pd.Timedelta(days=4),asof).date()) for i in range(14)]
    frames=[weekly_frame(d,ml,states,date) for date in dates]
    for f in frames:f.update(data_vintage=d.vintage,model_as_of=ml['as_of'],model_hash=model_hash,method_version=1)
    resource='iw_journal.json.gz';old_path=d.resource(resource);old=read(old_path) if old_path.exists() else dict(version=1,records=[])
    if old.get('version')!=1:raise ValueError('Unknown IW journal schema; preserve existing archive')
    if any(r['as_of']>d.as_of for r in old['records']):raise ValueError('IW journal cannot move backward in time')
    records=preserve_weeks(old['records'],frames,week_key(d.as_of),datetime.now(timezone.utc).isoformat())
    save(d.base/resource,dict(version=1,records=records))
    public=clean_json(records[:14]);monthly=monthly_reviews(d,ml,states);latest=[timeline(states,d.as_of),composite_at(ml,d.as_of)]
    note='월말 복기15건은 팀 ML 원점별 예측·실현을 같은 원장에서 집계합니다. 주간 연대기14건은 지수·YTD·국면·전망을 묶습니다. 최초 과거 주간은 현재 빈티지로 재구성했다고 표시하며 이후 지나간 주간의 기록과 그림은 보존합니다.'
    obj=objects['iw'];journal=[s for s in obj['sections'] if s['type']=='notebook']
    obj['sections']=[dict(type='reviewlog',title='월말 복기 · 모델 방향과 실현',group='월말 복기',items=monthly),dict(type='reviewlog',title='주간 관측 연대기',group='주간 연대기',items=[{k:v for k,v in r.items() if k!='charts'} for r in public]),
        dict(type='reviewcharts',title='국면·ML 그림 · 최신/기록 시점',group='이번 주의 그림',latest=latest,archives=[dict(period=r['period'],as_of=r['as_of'],retrospective=r['retrospective'],charts=r['charts']) for r in public])]+journal
    obj['method_note']=note;obj['cards']=[('월말 복기',len(monthly)),('주간 공개/누적',f'{len(public)}/{len(records)}'),('그림',2)]
    obj['missing']=['과거 재구성은 현재 수정 거시와 현재 팀 모형의 OOS 재생이며 과거 실제 발행본/PIT 예측이 아닙니다. 원본 본문·합계·표 사이의 불일치는 복제하지 않고 한 계산 결과에서 생성합니다.',
        '경제/시장/위험의 가용 입력·임계값은 공개한 팀 규칙입니다. 원본의 미공개 복합 가중치와 수치 동등성을 주장하지 않습니다.',
        '원본 작성자의 주간 논평·과거 개인 기록, 팀 공용 DB·LLM 자동 글쓰기는 미연결입니다. 사용자 판단과 첨부는 브라우저 로컬입니다.']
    objects['regime']['sections'].append(dict(timeline(states,d.as_of),group='월별 국면'))
    objects['regime']['sections'].append(dict(table('3종 국면의 정보 정렬·팀 규칙',['축','입력·규칙'],[
        ['경제','INDPRO YoY와 CPI YoY의3개월 변화 부호. 두 관측 모두2개월 뒤 정보월에 사용.'],['시장','위 성장 방향×미국10Y 월말 금리3개월 변화. 성장↑/금리↓봄,↑/↑여름,↓/↑가을,↓/↓겨울.'],
        ['위험','VIX≥25,NFCI>0,HY OAS≥5%,M2 YoY<0,Sahm≥0.5의5조건. 0~1개 위험선호,2개 중립,3개 이상 위험회피.'],['시차·미산출','M2/Sahm2개월·NFCI7일 시차. 위험 입력5개가 모두 있어야 분류. 정상값으로 결측을 채우지 않음.']]),group='월별 국면'))

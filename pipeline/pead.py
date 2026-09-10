"""PEAD mini cards with explicitly separated display-window and post-D0 returns."""
import pandas as pd
from .engine import clean_json,number
from .store import ROOT,read_json
from .financial_modules import frame
from .pead_data import sources
from .strategy_cards import dated_price

SPEC=dict(version=1,calendar_window=60,pre_event_calendar_days=5,default_cards=12,
          surprise_min=0,display_return_min=0,maximum_price_age_days=7,universe='us100',
          order='surprise_pct + display_return_pct descending; symbol ascending on ties')
CLOSES=read_json(ROOT/'config/us_equity_closes.json')


def observation(price,benchmark,timestamp,as_of):
    from .subview_modules import event_returns
    t=pd.Timestamp(timestamp)
    if pd.isna(t) or t.tzinfo is None:return None
    local=t.tz_convert('America/New_York');day=local.tz_localize(None).normalize();cut=pd.Timestamp(as_of)
    if not cut-pd.Timedelta(days=SPEC['calendar_window'])<=day<=cut:return None
    p=dated_price(price,as_of);b=dated_price(benchmark,as_of)
    if not len(p) or (cut-p.index[-1]).days>SPEC['maximum_price_age_days']:return None
    date=str(day.date())
    if not CLOSES['start']<=date<=CLOSES['end']:return None
    close_hour=CLOSES['early_close_hour'] if date in CLOSES['early_close_dates'] else CLOSES['regular_close_hour']
    event=event_returns(p,b,t,close_hour=close_hour)
    if not event:return None
    # Preserve the source's five-calendar-day context line. Its first-to-last
    # return includes pre-release moves and must not be named post-event drift.
    q=p.loc[day-pd.Timedelta(days=SPEC['pre_event_calendar_days']):]
    if len(q)<2 or q.index[0]>=day or p.index[0]>day-pd.Timedelta(days=SPEC['pre_event_calendar_days']):return None
    return dict(event,event_date=str(day.date()),published_at=t.isoformat(),published_local=local.isoformat(),
                days=(cut-day).days,date=str(p.index[-1].date()),close_hour=close_hour,spark=[[str(t.date()),number(v)] for t,v in q.items()],
                display_return=number((q.iloc[-1]/q.iloc[0]-1)*100),price=number(p.iloc[-1]),
                anchor=number(q.iloc[0]),anchor_date=str(q.index[0].date()))


def build(d):
    raw=sources(d);membership=d.members.get('us100',{});members=membership.get('members',[])
    rows=[];excluded=[];available=0;bench=d.price('SPY');cut=pd.Timestamp(d.as_of)
    membership_date=membership.get('as_of')
    valid_membership=bool(membership_date and 0<=(cut-pd.Timestamp(membership_date)).days<=14)
    for m in members:
        symbol=m['symbol'];record=raw.get(symbol)
        if not valid_membership:excluded.append([symbol,'구성목록이 미래이거나14일 초과 경과']);continue
        if not record:excluded.append([symbol,'발표일 자료 미확보']);continue
        available+=1;f=frame(record['earnings_dates']);candidates=[]
        for timestamp,r in f.iterrows():
            t=pd.Timestamp(timestamp);day=t.tz_convert('America/New_York').tz_localize(None).normalize()
            actual=number(r.get('Reported EPS'));surprise=number(r.get('Surprise(%)'))
            if actual is None or surprise is None or day>cut:continue
            candidates.append((t,r))
        if not candidates:excluded.append([symbol,'기준일 이전 확정 EPS 미확보']);continue
        candidates.sort(key=lambda r:r[0],reverse=True);t,r=candidates[0]
        # Conflicting duplicate observations must not choose arbitrary provider rows.
        same=[v for date,v in candidates if date==t]
        if len({(number(v.get('Reported EPS')),number(v.get('Surprise(%)'))) for v in same})>1:
            excluded.append([symbol,'동일 발표시각의 EPS 관측 충돌']);continue
        obs=observation(d.price(symbol),bench,t,d.as_of)
        if obs is None:excluded.append([symbol,'60일 발표 창·첫 반응 종가·가격 준비 조건 미충족']);continue
        surprise=number(r.get('Surprise(%)'))
        if surprise<=SPEC['surprise_min'] or obs['display_return']<=SPEC['display_return_min']:
            excluded.append([symbol,'양의 서프라이즈·표시구간 상승 조건 미충족']);continue
        rows.append(dict(obs,id=symbol,symbol=symbol,name=m.get('name') or symbol,market='US',surprise=surprise,
                         actual_eps=number(r.get('Reported EPS')),estimate_eps=number(r.get('EPS Estimate')),
                         score=number(surprise+obs['display_return']),retrieved_at=record['retrieved_at'],
                         source='https://finance.yahoo.com/calendar/earnings?symbol='+symbol))
    rows.sort(key=lambda r:(-r['score'],r['symbol']))
    return clean_json(dict(type='strategycards',kind='pead',group='PEAD',title='실적 서프라이즈 · 발표 전후 가격 카드',as_of=d.as_of,rows=rows,spec=SPEC,
        scope=dict(expected=len(members),available=available,selected=len(rows),excluded=excluded,membership_date=membership_date,membership_source=membership.get('source')),
        note='공식 S&P100 OEF 공시 주식의 최근60일 최신 확정 EPS 발표를 검사합니다. 양의 서프라이즈·발표5달력일 전부터의 표시구간 상승 후보를 두 수치의 합으로 정렬해 기본12개를 표시합니다. 이 선별·기간은 공개되지 않은 설정에 대한 팀 규칙입니다. 작은 선은 조정 종가이며 표시구간 변화에는 발표 전 움직임이 포함됩니다. 발표 후 수익률은 첫 반응 세션(D0) 종가부터 별도로 계산합니다. 발표 시각/EPS는 제공처 현재 빈티지이며 발표 당시 저장된 컨센서스나 투자 성과가 아닙니다.'))


def views(d,obj):
    section=build(d)
    # The compact card grid replaces the eight unrelated large scatter panels.
    # Keep the original event ledger under the same subview for broader history.
    ledger=[dict(s,title='별도 기존60기업 원장 · 최근180일') for s in obj['sections'] if s.get('group')=='PEAD' and s['type']=='table']
    obj['sections']=[s for s in obj['sections'] if s.get('group')!='PEAD']+[section]+ledger
    obj['cards']=[c for c in obj['cards'] if c[0]!='PEAD 후보']+[['PEAD 후보',len(section['rows'])]]
    note=' PEAD 카드의 표시구간 변화는 발표5달력일 전부터이며 D0 이후 수익과 분리합니다.'
    obj['method_note']=obj['method_note'].replace(note,'')+note
    obj['missing']=[m for m in obj['missing'] if not m.startswith('PEAD 카드:')]+['PEAD 카드: 원본 사전표본·기간/임계치의 비공개 설정, 제공처 발표시각의 발행사 전수 대조와 발표 당시 컨센서스 빈티지·비용 후 성과는 남아 있습니다.']
    return obj

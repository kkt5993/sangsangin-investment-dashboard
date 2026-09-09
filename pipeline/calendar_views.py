"""Combine independently dated US/KR schedule snapshots without inventing times."""
import hashlib
from urllib.parse import urlparse,parse_qs
import pandas as pd
from .calendar_data import RELEASES
from .events_data import read

def us_rows(raw):
    out=[]
    for r in raw['items']:
        rid=parse_qs(urlparse(r['url']).query).get('rid',[None])[0]
        if 'FRED' in r['source'] and rid not in RELEASES:raise ValueError('Unrecognized FRED release ID')
        agency=RELEASES.get(rid) or ('FOMC' if 'FOMC' in r['source'] else 'BEA')
        group='물가' if agency in ['BLS CPI','BLS PPI'] else '고용' if agency in ['BLS Employment','BLS JOLTS','DOL Claims'] else '정책회의' if agency=='FOMC' else '성장·소득' if agency=='BEA' else '생산·소비'
        identity='us:'+hashlib.sha256((agency+r['date']+r['name']).encode()).hexdigest()[:16]
        out.append(dict(r,id=identity,region='US',category=group,agency=agency,source_id='us:'+agency,observed_at=raw['retrieved_at'],notes=r.get('meeting_dates',''),time_status=r.get('time_status') or ('공표시각' if r['at'] else '시각 미표기'),timezone='America/Chicago' if rid else 'America/New_York'))
    return out

def combine(us,kr,as_of):
    captured=[pd.Timestamp(raw['retrieved_at']).tz_convert('Asia/Seoul') for raw in [us,kr] if raw]
    start=str(max(captured).date()) if captured else as_of
    end=str((pd.Timestamp(start)+pd.Timedelta(days=89)).date());sources=[];items=[]
    if us:
        items+=us_rows(us)
        sources += [dict(id='us:'+s['name'],name=s['name'],region='US',status=s['status'],count=s['count'],last_success_at=us['retrieved_at'] if s['status']=='ok' else None,checked_at=us['retrieved_at'],url=s['url'],error_type=s.get('error_type')) for s in us['sources']]
    if kr:
        items+=kr['items'];sources += [dict(s,region='KR') for s in kr['sources']]
    statuses={s['id']:s for s in sources};out=[]
    for item in items:
        r=dict(item);t=pd.Timestamp(r['at']) if r.get('at') else None
        if t is not None and t.tzinfo is None:raise ValueError('Calendar timestamp timezone missing')
        r['kst_at']=t.tz_convert('Asia/Seoul').isoformat() if t is not None else None
        r['display_date']=r['kst_at'][:10] if r['kst_at'] else r['date']
        r['date_basis']='한국시간' if t is not None or r['region']=='KR' else '미국 현지 날짜'
        if not start<=r['display_date']<=end:continue
        if r['source_id'] not in statuses:raise ValueError('Calendar event source is missing')
        source=statuses[r['source_id']];r['source_status']=source['status']
        r['observed_kst_date']=str(pd.Timestamp(r['observed_at']).tz_convert('Asia/Seoul').date())
        r['age_days']=max(0,(pd.Timestamp(start)-pd.Timestamp(r['observed_kst_date'])).days)
        out.append(r)
    if len({r['id'] for r in out})!=len(out):raise ValueError('Calendar identity duplicated across sources')
    out.sort(key=lambda r:(r['display_date'],r['kst_at'] or r['date']+'T99',r['name']))
    for s in sources:s['visible_count']=sum(r['source_id']==s['id'] for r in out)
    return dict(type='releasecalendar',group='거시 발표 달력',title='미국·한국 거시 발표 일정',from_date=start,to_date=end,days=90,items=out,sources=sources,
        note='가격 기준일과 별개로 최신 달력 수집일의 한국 날짜부터90일을 표시합니다. 공표 예정일이며 실제 발표 완료나 수치 확인이 아닙니다. 한국은행 통계/통화정책방향 회의, 국가데이터처 연도 명시 통계 보도계획, FRED·BEA·FOMC를 포함합니다. 국가데이터처 행정·교육 소식과 기준연도가 없는 제목은 제외합니다. 미국 시각은 원래 시간대의 서머타임을 적용하고, 시각이 없는 미국 회의는 미국 현지 날짜로 표시합니다. 없는 시각·미공개 내년 일정은 추정하지 않습니다. 실패한 출처는 직전 자료의 확인일과 함께 유지하며 새로 확인한 일정처럼 표시하지 않습니다.')

def calendar_views(d,obj):
    a=d.resource('release_calendar.json.gz');b=d.resource('kr_release_calendar.json.gz')
    us=read(a) if a.exists() else None;kr=read(b) if b.exists() else None
    obj['sections']=[s for s in obj['sections'] if s.get('group')!='거시 발표 달력']+[combine(us,kr,d.as_of)]
    obj['missing']=[m for m in obj['missing'] if '한국 거시 발표 일정' not in m]
    obj['missing'].append('달력은 계획이며 변경될 수 있습니다. 원문 미표기 발표시각·국가데이터처 미공개 다음 연도·계획에 없는 긴급회의와 과거 발표 당시 PIT 국면은 별도 대상입니다.')
    obj['source']+=' · 한국은행 공표일정/정책회의 · 국가데이터처 보도계획'

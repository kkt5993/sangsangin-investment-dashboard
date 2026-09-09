"""Verified P acquisitions, filing-vs-trade dates, and the original card layout."""
import re
from datetime import date
import numpy as np
import pandas as pd
from .engine import number,points
from .financial_modules import frame
from .sec_ownership import records,accepted_utc
from .events_data import read

def eligible_filings(filings,as_of):
    start=str((pd.Timestamp(as_of)-pd.Timedelta(days=89)).date())
    end=(pd.Timestamp(as_of)+pd.Timedelta(days=1)).tz_localize('America/New_York').tz_convert('UTC')
    result=[];rejected=[]
    unique={r['accession']:r for r in filings}
    amendments=[r for r in unique.values() if r['form']=='4/A' and accepted_utc(r.get('accepted_at')) and pd.Timestamp(r['accepted_at'])<end]
    for f in unique.values():
        owners={r['cik'] for r in f['owners']};why=[]
        accepted=accepted_utc(f.get('accepted_at'))
        if f['form']!='4':why.append('정정공시 개별 대조 필요')
        if accepted is None:why.append('SEC 접수 시각 미확보')
        elif pd.Timestamp(accepted)>=end:why.append('기준일 이후 접수')
        for amendment in amendments:
            if amendment['issuer_cik']!=f['issuer_cik'] or not owners.intersection(r['cik'] for r in amendment['owners']):continue
            original=amendment.get('original_filing_date')
            overlaps=set(r['date'] for r in amendment['transactions']).intersection(r['date'] for r in f['transactions'])
            if (original and original==f.get('filing_date')) or overlaps:why.append('동일 보고자·거래기간의 정정공시 존재')
        rows=[]
        for r in f['transactions']:
            try:
                if date.fromisoformat(r['date']).isoformat()!=r['date']:continue
            except (ValueError,TypeError):continue
            if not start<=r['date']<=as_of:continue
            if r['kind']!='nonDerivative' or r['code']!='P' or r['side']!='A':continue
            if r['shares'] is None or r['shares']<=0 or r['price'] is None or r['price']<=0:continue
            if accepted and r['date']>str(pd.Timestamp(accepted).tz_convert('America/New_York').date()):why.append('거래일이 접수일 이후')
            rows.append(dict(r,amount=number(r['shares']*r['price'])))
        if not rows:continue
        item=dict(f,transactions=rows,reasons=list(dict.fromkeys(why)))
        (rejected if why else result).append(item)
    return sorted(result,key=lambda r:r['accepted_at'],reverse=True),sorted(rejected,key=lambda r:r['accession'])

def provider_candidates(events,as_of):
    rows=[];cut=pd.Timestamp(as_of);start=cut-pd.Timedelta(days=89)
    for symbol,raw in events.items():
        f=frame(raw.get('insider'))
        for _,r in f.iterrows():
            try:date=pd.Timestamp(r.get('Start Date'))
            except (ValueError,TypeError):continue
            if pd.isna(date):continue
            if date.tzinfo is not None:date=date.tz_localize(None)
            shares=number(r.get('Shares'));amount=number(r.get('Value'))
            if not start<=date<=cut or not re.match(r'^Purchase\b',str(r.get('Text','')),re.I) or not shares or shares<0 or not amount or amount<0:continue
            rows.append(dict(symbol=symbol,date=str(date.date()),name=str(r.get('Insider','')),shares=shares,amount=amount,retrieved_at=raw['retrieved_at']))
    return sorted(rows,key=lambda r:r['date'],reverse=True)

def comparison(candidates,filings):
    normal=lambda s:re.sub('[^A-Z0-9]','',s.upper())
    out=[]
    for c in candidates:
        matches=[f for f in filings if f['symbol']==c['symbol'] and any(normal(o['name'])==normal(c['name']) for o in f['owners']) and max(r['date'] for r in f['transactions'])==c['date']]
        matches=[f for f in matches if abs(sum(r['shares'] for r in f['transactions'])-c['shares'])<1e-5]
        f=matches[0] if len(matches)==1 else None
        if f:
            amount=sum(r['amount'] for r in f['transactions']);delta=number(amount-c['amount'])
            status='원문·접수 확인' if not f['reasons'] and abs(delta)<=1 else '금액 차이 검토' if not f['reasons'] else ' · '.join(f['reasons'])
            out.append(dict(c,accession=f['accession'],source_url=f['source_url'],status=status,sec_rows=len(f['transactions']),sec_start=min(r['date'] for r in f['transactions']),sec_end=max(r['date'] for r in f['transactions']),sec_amount=number(amount),amount_delta=delta))
        else:out.append(dict(c,accession=None,source_url=None,status='원문 대조 대기' if not matches else '여러 공시와 중복 일치',sec_rows=None,sec_start=None,sec_end=None,sec_amount=None,amount_delta=None))
    return out

def ownership_views(d,obj,events):
    from .subview_modules import event_returns
    valid,pending=eligible_filings(records(d),d.as_of);cards=[];benchmark=d.price('SPY').loc[:d.as_of]
    for symbol in sorted({r['symbol'] for r in valid}):
        fs=[r for r in valid if r['symbol']==symbol];p=d.price(symbol).loc[:d.as_of];tail=p.tail(63);ix=np.unique(np.linspace(0,len(tail)-1,min(44,len(tail)),dtype=int)) if len(tail) else []
        low=p.tail(252).min() if len(p)>=252 else None
        for f in fs:f['study']=event_returns(p,benchmark,f['accepted_at']) if len(p) else None
        cards.append(dict(symbol=symbol,name=d.fund.get(symbol,{}).get('info',{}).get('shortName') or symbol,
            buyers=len({o['cik'] for f in fs for o in f['owners']}),filing_count=len(fs),transaction_count=sum(len(f['transactions']) for f in fs),
            amount_mn=number(sum(r['amount'] for f in fs for r in f['transactions'])/1e6),filings=fs,
            off_low=number((p.iloc[-1]/low-1)*100) if low and low>0 else None,price_date=str(p.index[-1].date()) if len(p) else None,spark=points(tail.iloc[ix]) if len(tail) else []))
    cards.sort(key=lambda r:r['amount_mn'],reverse=True)
    candidates=provider_candidates(events,d.as_of);path=d.resource('sec_collection.json.gz');health=read(path) if path.exists() else dict(status='not_collected',retrieved_at=None)
    section=dict(type='ownership',title='SEC Form4 · 코드P 매수 클러스터',group='내부자 매수',cards=cards,pending=pending,comparison=comparison(candidates,valid+pending),
        collection=health,scope=dict(event_companies=len(events),candidate_rows=len(candidates),reviewed_filings=len(valid)+len(pending),confirmed_filings=len(valid),confirmed_rows=sum(len(f['transactions']) for f in valid),
            start=str((pd.Timestamp(d.as_of)-pd.Timedelta(days=89)).date()),end=d.as_of,cutoff_timezone='America/New_York'))
    obj['sections']=[s for s in obj['sections'] if s.get('group')!='내부자 매수']+[section]
    obj['method_note']=obj['method_note'].replace('내부자 매수는 제공처 Text의 Purchase·양의 금액만 선별하며 주식보상·증여·매도는 제외합니다. SEC 원문 코드P를 직접 대조한 목록은 아닙니다.','내부자 후보는 제공처 Purchase 행에서 시작하며, 클러스터에는 SEC 비파생 코드P·취득A·양의 수량/가격과 기준일 이내 접수시각을 확인한 공시만 포함합니다. P는 공개시장 또는 사적 매수여서 공개시장 매수만이라고 단정하지 않습니다.')
    obj['method_note']+=' 접수시각은 SEC 색인의 미국 동부시각 또는 API의 명시된 시간대를 UTC로 변환합니다. SEC가 문서를 처음 공개한 실제 시각은 별도 없으므로 접수 기반 가격 관측은 참고이며 체결 백테스트가 아닙니다. 정정공시는 자동 합산하지 않습니다.'
    obj['missing']=['SEC 연속 자동수집은 PC HTTP 접근 상태에 따라 제한됩니다. 현재 원문 대조 표본과 미확인 후보를 구분하며 전체 미국 시장의 모든 내부자 거래를 의미하지 않습니다. Form4/A 정정 대조·13F·전략별 비용 후 OOS는 후속 대상입니다.']

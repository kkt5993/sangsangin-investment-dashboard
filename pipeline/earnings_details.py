"""Fiscal-period earnings panels. Estimates remain distinct from reported NI."""
import gzip,json
from urllib.parse import quote
import pandas as pd
from .engine import number
from .financial_modules import frame,statement_series
from .catalog import reference_stocks

US=['GOOGL','NVDA','MSFT','AMZN','AAPL','META','BRK-B','JPM','AVGO','TSLA']
KR=['005930.KS','000660.KS']
FX={'KRW':('KRW=X',False),'JPY':('JPY=X',False),'CNY':('CNY=X',False),
    'INR':('INR=X',False),'TWD':('TWD=X',False),'CAD':('CAD=X',False),
    'EUR':('EURUSD=X',True),'GBP':('GBPUSD=X',True)}
METRICS=[('ni','NetIncome','순이익'),('op','OperatingIncome','영업이익'),('revenue','TotalRevenue','매출')]

def val(f,row,col):
    return number(f.at[row,col]) if row in f.index and col in f.columns else None

def statements(raw,kind,cutoff):
    f=frame(raw.get(kind+'_income'));series={k:statement_series(f,field).loc[:cutoff] for k,field,_ in METRICS}
    dates=sorted(set().union(*(s.index for s in series.values())))
    return [dict(period=str(t.date()),**{k:number(s.get(t)) for k,s in series.items()}) for t in dates]

def fiscal_projection(raw,cutoff):
    annual=statements(raw,'annual',cutoff)
    base=next((r for r in reversed(annual) if r['ni'] is not None),None)
    e=frame(raw.get('earnings_estimate'));rev=frame(raw.get('revenue_estimate'))
    periods={r['period']:str(r.get('endDate') or '')[:10] for r in raw.get('estimate_periods',[])}
    currency=raw.get('info',{}).get('financialCurrency');issues=[]
    out=dict(base=base,forecasts=[],issues=issues)
    if not base:return out
    previous=base['ni'];prev_period=pd.Timestamp(base['period'])
    for horizon in ['0y','+1y']:
        end=periods.get(horizon);eps=val(e,horizon,'avg');prior_eps=val(e,horizon,'yearAgoEps')
        revenue=val(rev,horizon,'avg');prior_revenue=val(rev,horizon,'yearAgoRevenue')
        ec=e.at[horizon,'currency'] if horizon in e.index and 'currency' in e.columns else None
        rc=rev.at[horizon,'currency'] if horizon in rev.index and 'currency' in rev.columns else None
        reason=[]
        try:
            t=pd.Timestamp(end) if end else None
            aligned=t is not None and abs((t-pd.DateOffset(years=1)-prev_period).days)<=8
        except (ValueError,TypeError):t=None;aligned=False
        if not aligned:reason.append('추정 회계기간과 이전 연간 기간 불일치·미확보')
        if ec!=currency:reason.append('EPS 통화와 재무 통화 불일치·미확보')
        if previous is None or previous<=0 or prior_eps is None or prior_eps<=0 or eps is None:reason.append('양의 NI·EPS 기준 또는 EPS 추정 미확보')
        # For the first forecast, a provider rolling its estimate year early must
        # not silently link to a different actual annual statement.
        if horizon=='0y' and prior_revenue and base['revenue'] and abs(prior_revenue/base['revenue']-1)>.05:
            reason.append('전년 매출 기준이 연간 실적과5% 초과 차이')
        if horizon=='+1y':
            first_eps=val(e,'0y','avg')
            if first_eps and prior_eps and abs(prior_eps/first_eps-1)>.05:reason.append('FY2 전년 EPS와 FY1 EPS가5% 초과 차이')
        ni=number(previous*eps/prior_eps) if not reason else None
        if rc!=currency:revenue=None
        if not aligned:revenue=None
        record=dict(horizon=horizon,period=end or None,label=(end[:4]+'E') if end else ('FY1E' if horizon=='0y' else 'FY2E'),ni=ni,revenue=revenue,
            eps=eps,prior_eps=prior_eps,eps_analysts=val(e,horizon,'numberOfAnalysts'),revenue_analysts=val(rev,horizon,'numberOfAnalysts'),issues=reason)
        out['forecasts'].append(record);issues.extend(reason)
        previous=ni
        if t is not None:prev_period=t
    out['issues']=list(dict.fromkeys(issues))
    return out

def fx_rate(d,currency):
    if currency=='USD':return dict(rate=1.,quote=1.,symbol='USD',date=d.as_of,rule='USD 그대로')
    if currency not in FX:return None
    symbol,multiply=FX[currency];p=d.price(symbol,adjusted=False).loc[:d.as_of].dropna()
    if not len(p) or p.iloc[-1]<=0 or (pd.Timestamp(d.as_of)-p.index[-1]).days>7:return None
    return dict(rate=float(p.iloc[-1]) if multiply else 1/float(p.iloc[-1]),quote=float(p.iloc[-1]),symbol=symbol,date=str(p.index[-1].date()),rule='원통화×환율' if multiply else '원통화÷환율')

def context(d,symbol,name):
    raw=d.fund.get(symbol,{});info=raw.get('info',{});p=d.price(symbol,adjusted=False).loc[:d.as_of]
    price=number(p.iloc[-1]) if len(p) else None;target=number(info.get('targetMeanPrice'))
    return dict(symbol=symbol,name=name,financial_currency=info.get('financialCurrency'),quote_currency=info.get('currency'),price=price,
        price_date=str(p.index[-1].date()) if len(p) else None,target=target,upside=number((target/price-1)*100) if target and price else None,
        pe=number(info.get('trailingPE')),forward_pe=number(info.get('forwardPE')),market_cap=number(info.get('marketCap')),
        retrieved_at=raw.get('retrieved_at'),source='https://finance.yahoo.com/quote/'+quote(symbol,safe='')+'/analysis/')

def metric_rows(key,label,actual,forecast,scale,source,unit):
    return dict(key=key,name=label,unit=unit,rows=[dict(label=r['period'][:4]+'A',period=r['period'],value=number(r.get(key)/scale) if r.get(key) is not None else None,kind='actual',source='Yahoo 연간 재무제표') for r in actual]+
        [dict(label=r['label'],period=r.get('period'),value=number(r.get(key)/scale) if r.get(key) is not None else None,kind='estimate',source=source) for r in forecast])

def us_cards(d,names):
    result=[]
    for symbol in US:
        raw=d.fund.get(symbol,{})
        if not raw:continue
        p=fiscal_projection(raw,d.as_of);a=[p['base']] if p['base'] else []
        c=context(d,symbol,names.get(symbol,symbol));c.update(projection=p,metrics=[metric_rows(k,label,a,p['forecasts'],1e9,src,'USD bn') for k,label,src in [('ni','순이익 · EPS 성장 연결 근사','최근 실제 NI×EPS 성장률'),('revenue','매출 · 직접 컨센서스','Yahoo revenue estimate')]])
        if c['financial_currency']!='USD':continue
        result.append(c)
    return result

def korean_cards(d,names):
    path=d.resource('local_consensus.json.gz')
    raw=json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}
    data=raw.get('rows',[]);cards=[]
    for symbol in KR:
        f=d.fund.get(symbol,{})
        if not f:continue
        a=statements(f,'annual',d.as_of)[-3:];forecasts=[]
        # QuantiWise NI is attributable to the parent. Keep actuals on that
        # definition when supplied, rather than mix consolidated total NI.
        ni=statement_series(frame(f.get('annual_income')),'NetIncomeCommonStockholders')
        for r in a:r['ni']=number(ni.get(pd.Timestamp(r['period'])))
        year=max(int(d.as_of[:4]),int(a[-1]['period'][:4])+1 if a else 0)
        for y in [year,year+1]:
            r=dict(label=str(y)+'E',period=str(y)+'-12-31',source_dates={})
            for key,code in [('ni','E122710.M'),('op','E121500.M'),('revenue','E121000.M')]:
                rows=[v for v in data if v['ticker']=='A'+symbol[:6] and v['item_code']==code and v['period']==str(y)+'AS' and str(v['as_of'])[:10]<=d.as_of and v.get('unit')=='KRW 100mn']
                latest=max(rows,key=lambda v:v['as_of']) if rows else None
                r[key]=number(latest['value']*1e8) if latest else None;r['source_dates'][key]=str(latest['as_of'])[:10] if latest else None
            forecasts.append(r)
        c=context(d,symbol,names.get(symbol,symbol));c['projection']=dict(forecasts=forecasts,issues=[])
        c['metrics']=[metric_rows(k,label,a,forecasts,1e12,'QuantiWise · 출처 기준일 별도','조원') for k,label in [('op','영업이익'),('ni','지배주주 순이익')]]
        first=forecasts[0];c['forward_margin']=number(100*first['op']/first['revenue']) if first['op'] is not None and first['revenue'] and first['revenue']>0 else None
        c['consensus_source']='https://www.fnguide.com/';cards.append(c)
    return cards

def global_rows(d,names):
    candidates=[];excluded=0
    for symbol,name in names.items():
        raw=d.fund.get(symbol,{})
        if not raw:continue
        p=fiscal_projection(raw,d.as_of);base=p['base'];currency=raw.get('info',{}).get('financialCurrency');fx=fx_rate(d,currency)
        if not base or not fx or base['ni'] is None:excluded+=1;continue
        values=[base['ni']]+[r['ni'] for r in p['forecasts']]
        candidates.append(dict(symbol=symbol,name=name,currency=currency,fx=fx,actual_period=base['period'],forecast_periods=[r['period'] for r in p['forecasts']],
            values=[number(v*fx['rate']/1e9) if v is not None else None for v in values],issues=p['issues'],retrieved_at=raw['retrieved_at']))
    candidates.sort(key=lambda r:r['values'][0],reverse=True)
    return dict(rows=[dict(r,rank=i+1) for i,r in enumerate(candidates[:20])],available=len(candidates),excluded=excluded,expected=len(names))

def actual_cards(d,names):
    out=[]
    for symbol,name in names.items():
        raw=d.fund.get(symbol,{})
        if not raw or not raw.get('info',{}).get('financialCurrency'):continue
        annual=statements(raw,'annual',d.as_of)[-4:];quarterly=statements(raw,'quarterly',d.as_of)[-8:]
        if not annual and not quarterly:continue
        out.append(dict(symbol=symbol,name=name,currency=raw['info']['financialCurrency'],annual=annual,quarterly=quarterly,retrieved_at=raw['retrieved_at'],source='https://finance.yahoo.com/quote/'+quote(symbol,safe='')+'/financials/'))
    return out

def earnings_detail_views(d,obj):
    names={r['symbol']:r['name'] for r in reference_stocks()};global_data=global_rows(d,names)
    obj['sections'] += [dict(type='earningsglobal',title='글로벌 순이익 · 표본 Top20',group='글로벌 순이익',**global_data),
        dict(type='earningsestimates',title='삼성전자·SK하이닉스 추정 검증',group='국내 추정 상세',market='KR',cards=korean_cards(d,names)),
        dict(type='earningsestimates',title='미국 10기업 · 실적과 추정',group='미국 추정 상세',market='US',cards=us_cards(d,names)),
        dict(type='earningsactual',title='기업별 연간·분기 실적',group='연간·분기 상세',cards=actual_cards(d,names))]
    obj['method_note']+=' 글로벌 비교와 미국 상세의 미래 NI는 실제 NI에 EPS 컨센서스 성장률을 적용한 근사이며 직접 NI 컨센서스가 아닙니다. 매출은 직접 추정입니다. 제공처 회계기간·통화·전년 매출을 대조하고 불일치는 미산출합니다. 한국 상세는 QuantiWise OP/지배 NI, 억원→조원 변환과 기준일을 표시합니다. 가격일과 재무 조회일은 다르며 과거 시점 자료 빈티지가 아닙니다.'
    obj['missing']=['해외 직접 영업이익·순이익 컨센서스, 과거 발표 당시 빈티지, 한국 증권사별 원문 보고서 검증은 남아 있습니다. 글로벌 Top20은 현재 수집 기업 표본의 최근 실제 NI 순위이며 세계 전체 순위가 아닙니다.']

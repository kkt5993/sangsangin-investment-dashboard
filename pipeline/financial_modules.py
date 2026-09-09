"""Reported statements, explicitly named estimates, and dated local consensus."""
import numpy as np
import pandas as pd
from .engine import *
from .catalog import reference_stocks
from .market_modules import candle_section

def frame(raw):
    return pd.DataFrame(raw['data'],index=raw['index'],columns=raw['columns']) if raw else pd.DataFrame()

def pct(a,b):return number((a/b-1)*100) if number(a) is not None and number(b) is not None and b>0 else None

def statement_series(f,field):
    if field not in f.index:return pd.Series(dtype=float)
    s=pd.to_numeric(f.loc[field],errors='coerce');s.index=pd.to_datetime(s.index);return s.dropna().sort_index()

def financial_rows(d):
    rows=[];official_sectors={m['symbol']:m['sector'] for k in ['kr_sectors','us_largecap'] for m in d.members.get(k,{}).get('members',[])}
    for m in reference_stocks():
        s=m['symbol'];raw=d.fund.get(s);price=d.stats(s)
        if not raw or not price:continue
        info=raw.get('info',{});annual=frame(raw.get('annual_income'));quarter=frame(raw.get('quarterly_income'));est=frame(raw.get('earnings_estimate'));rev=frame(raw.get('revenue_estimate'))
        ni=statement_series(annual,'NetIncome');op=statement_series(annual,'OperatingIncome');sales=statement_series(annual,'TotalRevenue');qni=statement_series(quarter,'NetIncome')
        eps1=number(est.at['0y','avg']) if '0y' in est.index else None;eps2=number(est.at['+1y','avg']) if '+1y' in est.index else None
        eps0=number(est.at['0y','yearAgoEps']) if '0y' in est.index else None
        estimate_currency=str(est.at['0y','currency']) if '0y' in est.index and 'currency' in est else info.get('financialCurrency')
        m=dict(m,theme=m['sector'],sector=official_sectors.get(s) or info.get('sector') or '미분류')
        r=dict(**m,**{k:price[k] for k in ['r1m','r3m','ytd','r1y','rsi','price']},financial_as_of=raw['retrieved_at'][:10],price_as_of=price['as_of'],
            financial_currency=info.get('financialCurrency'),quote_currency=info.get('currency'),country=info.get('country'),industry=info.get('industry'),
            market_cap=number(info.get('marketCap')),margin=number(info.get('operatingMargins',np.nan)*100) if info.get('operatingMargins') is not None else None,
            net_income=last(ni),net_growth=pct(ni.iloc[-1],ni.iloc[-2]) if len(ni)>1 else None,
            op_growth=pct(op.iloc[-1],op.iloc[-2]) if len(op)>1 else None,report_date=str(ni.index[-1].date()) if len(ni) else None,
            eps1=eps1,eps2=eps2,eps_growth1=pct(eps1,eps0),eps_growth2=pct(eps2,eps1),estimate_currency=estimate_currency,
            analyst_count=number(info.get('numberOfAnalystOpinions')),rating=number(info.get('recommendationMean')),
            annual=[dict(period=str(t.date()),net_income=number(v),operating_income=number(op.get(t)),sales=number(sales.get(t))) for t,v in ni.items()],
            quarters=[dict(period=str(t.date()),net_income=number(v)) for t,v in qni.items()])
        if info.get('currency')==info.get('financialCurrency')=='USD':r['market_cap_usd']=r['market_cap']
        elif info.get('currency')=='KRW' and len(d.price('KRW=X')):r['market_cap_usd']=number(r['market_cap']/d.price('KRW=X').iloc[-1]) if r['market_cap'] else None
        else:r['market_cap_usd']=None
        rows.append(r)
    return rows

def last(s):return number(s.iloc[-1]) if len(s) else None

def local_growth(d):
    import gzip,json
    path=d.base/'local_consensus.json.gz'
    if path.exists():raw=json.loads(gzip.decompress(path.read_bytes()))
    else:
        path=d.base/'local_consensus.json'
        if not path.exists():return [],None
        raw=read_json(path)
    f=pd.DataFrame(raw['rows']);members={m['symbol']:m for k in ['kr_largecap','kospi200'] for m in d.members.get(k,{}).get('members',[])};result=[]
    for ticker,g in f.groupby('ticker'):
        symbol=ticker.removeprefix('A')+'.KS'
        if symbol not in members:continue
        p=d.stats(symbol)
        if not p:continue
        def get(code,year):
            a=g[(g.item_code==code)&(g.period==str(year)+'AS')]
            return number(a.value.iloc[-1]) if len(a) else None
        op0,op1,op2=[get('E121500.M',y) for y in [2025,2026,2027]];sales1=get('E121000.M',2026);sales2=get('E121000.M',2027)
        fy1=pct(op1,op0);fy2=pct(op2,op1)
        # Do not report growth from a negative or zero denominator as ordinary growth.
        margin1=get('E211000.M',2026);margin2=get('E211000.M',2027)
        if margin1 is None:margin1=number(100*op1/sales1) if op1 is not None and sales1 and sales1>0 else None
        if margin2 is None:margin2=number(100*op2/sales2) if op2 is not None and sales2 and sales2>0 else None
        info=d.fund.get(symbol,{}).get('info',{})
        result.append(dict(symbol=symbol,name=members[symbol]['name'],sector=members[symbol]['sector'],market='KR',fy1=fy1,fy2=fy2,margin1=margin1,margin2=margin2,ytd=p['ytd'],mcap=number(members[symbol].get('market_cap') or info.get('marketCap')),source_as_of=str(g.as_of.max()),
            profit=[get('E122710.M',y) for y in [2025,2026,2027]],status='정상' if fy1 is not None and fy2 is not None else '적자·0 기준 또는 추정치 없음'))
    return result,raw['as_of']

def earnings(d,rows,consensus):
    sections=[]
    for market in ['US','KR']:
        r=sorted([a for a in rows if a['market']==market and a['net_growth'] is not None],key=lambda a:a['net_growth'],reverse=True)[:10]
        sections += [dict(bars(market+' 연간 순이익 성장 Top 10',[(a['name'],a['net_growth']) for a in r]),group=market),
            dict(bars(market+' 이익성장 상위 종목 · YTD 주가',[(a['name'],a['ytd']) for a in r]),group=market)]
    cols=['1M %','3M %','YTD %','연간 NI YoY %','FY1 EPS 성장 %','FY2 EPS 성장 %']
    sections.append(heat('실적과 주가',cols,[dict(name=a['name'],group=a['market'],values=[a[k] for k in ['r1m','r3m','ytd','net_growth','eps_growth1','eps_growth2']]) for a in rows]))
    sections.append(table('글로벌 EPS 컨센서스',['종목','최근 연간 결산일','통화','FY1 EPS','FY2 EPS','FY1 성장 %','FY2 성장 %','추정 수집일'],[[a['name'],a['report_date'],a['estimate_currency'],a['eps1'],a['eps2'],a['eps_growth1'],a['eps_growth2'],a['financial_as_of']] for a in rows]))
    crows=[a for a in consensus if all(v is not None for v in a['profit'])]
    crows.sort(key=lambda a:a['profit'][1],reverse=True)
    sections.append(dict(type='groupedbars',title='국내 순이익 컨센서스 · 2025 / 2026 / 2027',labels=['2025','2026F','2027F'],unit='억원',rows=[dict(name=a['name'],values=a['profit']) for a in crows[:20]]))
    return module('earnings',d.as_of,'연간 순이익 성장률은 실제 재무제표, FY1/FY2 EPS는 Yahoo 애널리스트 추정치입니다. EPS를 현재 주식수로 곱해 순이익 컨센서스로 가장하지 않습니다. 국내 3개년 순이익은 별도 날짜의 로컬 QuantiWise 스냅샷(억원)을 사용합니다. 음수·0 분모 성장률은 —로 표시합니다.',sections,[('재무·가격 연결',len(rows)),('국내 3개년 추정',len(crows))],missing=['해외 영업이익·순이익 FY1/FY2 컨센서스는 EPS와 다른 항목이므로 동일 지표로 대체하지 않았습니다.'])

def growth(d,rows,consensus,consensus_as_of):
    sections=[]
    for horizon in [1,2]:
        pts=[dict(name=a['name'],symbol=a['symbol'],x=a[f'fy{horizon}'],y=a['ytd'],z=a[f'margin{horizon}'],size=a['mcap'],group=a['sector'],country='KR') for a in consensus if all(a[k] is not None for k in [f'fy{horizon}','ytd',f'margin{horizon}'])]
        sections.append(dict(type='scatter3d',title=f'FY{horizon} · 영업이익 성장 × YTD × 영업이익률',group=f'FY{horizon}',x_label='영업이익 성장 %',y_label='YTD 주가 %',z_label='영업이익률 %',points=pts))
    sections.append(table('국내 성장 컨센서스',['종목','KRX 업종','FY1 성장 %','FY2 성장 %','YTD %','FY1 이익률 %','기준일','상태'],[[a['name'],a['sector'],a['fy1'],a['fy2'],a['ytd'],a['margin1'],a['source_as_of'],a['status']] for a in consensus]))
    sections.append(heat('글로벌 실적·EPS 성장 (영업이익 추정과 구분)',['연간 영업이익 성장 %','FY1 EPS 성장 %','FY2 EPS 성장 %','YTD %','TTM 영업이익률 %'],[dict(name=a['name'],group=a['market'],values=[a['op_growth'],a['eps_growth1'],a['eps_growth2'],a['ytd'],a['margin']]) for a in rows]))
    return module('growth',d.as_of,'원본의 3D 축을 유지합니다: x=FY1/FY2 영업이익 성장, y=YTD, z=영업이익률. 국내는 KRX 대형주·KOSPI 200와 기존 로컬 컨센서스를 연결했습니다. FY1=2026, FY2=2027, 추정 빈티지는 '+str(consensus_as_of)+'. 시가총액 없는 종목은 같은 크기로 표시합니다.',sections,[('국내 대상',len(consensus)),('컨센서스 기준',consensus_as_of)],missing=['글로벌 100종목의 FY1/FY2 영업이익 컨센서스가 없어 해외 3D 점은 제외했습니다. 해외 EPS 성장률은 별도 표로 제공합니다.'])

def discovery(d,rows,ranks):
    allrank={a['symbol']:a['rs'] for market in ['KR','US'] for a in ranks[market]['rows']};work=[]
    for a in rows:
        rs=allrank.get(a['symbol']);tech=rs if rs is not None else number(np.clip(50+a['r3m'],0,100))
        growth=a['eps_growth1'];earn=number(np.clip(50+(growth or 0),0,100)) if growth is not None else None
        analyst=number((5-a['rating'])/4*100) if a['rating'] is not None else None
        # Missing a component does not silently become a neutral score.
        score=tech if a['market']=='KR' else number(.45*tech+.3*earn+.25*analyst) if earn is not None and analyst is not None else None
        lens='관찰'
        if growth is not None and growth>20 and a['r3m']<0:lens='실적↑ 가격↓'
        elif a['rsi']<35:lens='과매도'
        elif a['r3m']>20 and (growth is None or growth<0):lens='가격 선행'
        elif growth is not None and growth>20 and a['r3m']>0:lens='성장 동행'
        work.append(dict(a,score=score,rs=rs,lens=lens,tech=tech,earn=earn,analyst=analyst))
    work.sort(key=lambda a:a['score'] if a['score'] is not None else -1,reverse=True)
    sections=[table('통합 종목 랭킹',['종목','시장','렌즈','종합','기술','실적','애널리스트','3M %','FY1 EPS 성장 %'],[[a['name'],a['market'],a['lens'],a['score'],a['tech'],a['earn'],a['analyst'],a['r3m'],a['eps_growth1']] for a in work])]
    for lens in sorted({a['lens'] for a in work}):
        chosen=[a for a in work if a['lens']==lens][:8];sections.append(dict(table(lens,['종목','점수','RS','RSI','YTD %'],[[a['name'],a['score'],a['rs'],a['rsi'],a['ytd']] for a in chosen]),group=lens))
    return module('discovery',d.as_of,'KR은 기술 100%, US는 기술 45%·실적 30%·애널리스트 25%의 공개 가중치로 재계산했습니다. 대형주 RS가 없는 글로벌 종목의 기술점수는 clip(50+3M%,0,100)입니다. 실적·애널리스트 누락 시 종합은 산출하지 않습니다. 렌즈는 명시된 수치 규칙이며 LLM 의견이 아닙니다.',sections,[('분석 종목',len(work)),('점수 산출',sum(a['score'] is not None for a in work))],missing=['원본의 내부 점수 정규화·서술형 리서치 엔진은 미공개로 수치 동등성은 미검증입니다.'])

def strategies(d,rows):
    turn=[];surprise=[]
    for a in rows:
        q=a['quarters']
        if q:
            expected=pd.Timestamp(q[-1]['period'])-pd.DateOffset(years=1)
            prior=next((r for r in reversed(q[:-1]) if abs((pd.Timestamp(r['period'])-expected).days)<=7),None)
            if prior and q[-1]['net_income']>0 and prior['net_income']<0:turn.append(dict(a,turn_prior=prior))
        h=frame(d.fund[a['symbol']].get('earnings_history'))
        if len(h) and 'surprisePercent' in h:
            for period,row in h.tail(1).iterrows():
                surprise.append([a['name'],str(period)[:10],number(row.surprisePercent*100),a['r1m'],a['r3m']])
    sections=[dict(table('전년 동분기 대비 흑자전환',['종목','분기말','이번 순이익 · 원통화','전년 분기말','전년 동분기 순이익','통화','1M %'],[[a['name'],a['quarters'][-1]['period'],a['quarters'][-1]['net_income'],a['turn_prior']['period'],a['turn_prior']['net_income'],a['financial_currency'],a['r1m']] for a in turn]),group='턴어라운드'),
        dict(table('실적 서프라이즈 관찰',['종목','실적 대상 분기말','EPS 서프라이즈 %','최근 1M %','최근 3M %'],sorted(surprise,key=lambda a:a[2] if a[2] is not None else -1,reverse=True)),group='실적 모멘텀')]
    for a in turn[:8]:
        c=candle_section(d,a['symbol'],a['name'],'턴어라운드')
        if c:sections.append(c)
    return module('strategies',d.as_of,'재무제표의 전년 동분기 순이익 적자→흑자 전환을 실제 분기값으로 선별합니다. EPS 서프라이즈와 최근 수익률은 각각 별도 열로 표시합니다. 공급자의 earnings_history 날짜는 발표일이 아니라 실적 대상 분기말입니다.',sections,[('흑자전환',len(turn)),('서프라이즈 관측',len(surprise))],missing=['PEAD 이벤트 수익률은 정확한 발표 시각·거래일 정렬이 필요해 최근 1M 수익률로 대체하지 않습니다.','내부자 거래·공매도·13F 등 원본의 다른 전략은 이벤트 원장을 추가 연결해야 합니다.'])

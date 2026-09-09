"""Independent nonfundamental-flow panels and earnings straddle observations."""
import re
import numpy as np
import pandas as pd
from .engine import number,table,bars,heat
from .events_data import read
from .flow_catalog import US_STOCKS,ETF_DEFINITIONS,KR_THEMES
from .wagdog import packets,profile

def inputs(d):
    return {p.name:read(p) for b in d.bases for p in (b/'flows').glob('*.json.gz')}

def coefficient(funds):
    return sum((r['leverage']**2-r['leverage'])*r['aum'] for r in funds)

def sensitivity(rows):
    """Full-factor score only; missing fund coverage does not mean zero flow."""
    fields=['gamma_mcap_bp','letf_adv_pct','option_mcap_pct','short_float_pct']
    f=pd.DataFrame([{k:r.get(k) for k in fields} for r in rows],dtype=float)
    f.gamma_mcap_bp=f.gamma_mcap_bp.abs();z=(f-f.mean())/f.std(ddof=0).replace(0,np.nan)
    for i,r in enumerate(rows):
        r['factor_count']=int(f.iloc[i].notna().sum());r['sensitivity']=number(z.iloc[i].mean()) if z.iloc[i].notna().all() else None
        r['factor_z']=[number(x) for x in z.iloc[i]]
    return rows

def theme_rows(etfs):
    buckets={name:[] for name,_ in KR_THEMES};members=[]
    for r in etfs:
        if not r.get('aum_krw') or r['aum_krw']<=0:continue
        # A thematic view of unlevered funds; daily L/I positioning has its own
        # AUM card below. First-match assignment prevents overlapping totals.
        if re.search(r'레버리지|인버스|[23]X',r['name'],re.I):continue
        name=next((n for n,pat in KR_THEMES if re.search(pat,r['name'],re.I)),None)
        if name:buckets[name].append(r);members.append(dict(r,theme=name))
    out=[]
    for name,items in buckets.items():
        if not items:continue
        aum=sum(r['aum_krw'] for r in items);paired=[r for r in items if r['nav_1m_pct'] is not None and abs(r['nav_1m_pct'])<=100]
        covered=sum(r['aum_krw'] for r in paired);value=sum(r['traded_value'] or 0 for r in items)
        out.append(dict(theme=name,count=len(items),aum_krw=aum,nav_1m_pct=sum(r['nav_1m_pct']*r['aum_krw'] for r in paired)/covered if covered else None,return_coverage=covered/aum*100,turnover_pct=value/aum*100,representative=max(items,key=lambda r:r['aum_krw'])['name']))
    f=pd.DataFrame(out)
    if len(f):
        features=pd.DataFrame(dict(size=np.log(f.aum_krw),momentum=f.nav_1m_pct,turnover=f.turnover_pct));z=(features-features.mean())/features.std(ddof=0).replace(0,np.nan)
        for i,r in enumerate(out):r['hot']=number(z.iloc[i].mean()) if z.iloc[i].notna().all() else None
    return out,members

def straddle(raw):
    """Same-expiry, same-strike bid/ask mids; never last prices or zero bids."""
    spot=number(raw.get('spot'));expiry=raw.get('expiry')
    if not spot or not expiry:return dict(status='만기 자료 없음')
    valid={}
    for r in raw['records']:
        bid=number(r.get('bid'));ask=number(r.get('ask'));oi=number(r.get('openInterest'))
        if r['expiry']!=expiry or r.get('contractSize')!='REGULAR' or bid is None or ask is None or bid<=0 or ask<bid or not oi or oi<=0:continue
        mid=(bid+ask)/2
        if (ask-bid)/mid>.5:continue
        valid.setdefault(r['strike'],{})[r['side']]=dict(mid=mid,bid=bid,ask=ask,oi=oi)
    strikes=[k for k,a in valid.items() if set(a)=={'call','put'} and abs(k/spot-1)<=.03]
    if not strikes:return dict(status='ATM 양방향 호가 품질 부족')
    strike=min(strikes,key=lambda k:abs(k-spot));call=valid[strike]['call'];put=valid[strike]['put'];cost=call['mid']+put['mid']
    return dict(status='관측',strike=strike,call_mid=call['mid'],put_mid=put['mid'],cost=cost,move_pct=cost/spot*100,low=spot-cost,high=spot+cost,bid_cost=call['bid']+put['bid'],ask_cost=call['ask']+put['ask'])

def earnings_views(d,pm,earnings,raw):
    target=raw.get('earnings_targets.json.gz',{});rows=[]
    for symbol,event in target.get('events',{}).items():
        a=raw.get('earnings_'+symbol+'.json.gz',{});calc=straddle(a)
        # Parent observations for a different event must never be reused.
        if a.get('event_at')!=event:calc=dict(status='이벤트 옵션 미수집')
        rows.append([symbol,event,a.get('expiry'),a.get('spot'),calc.get('strike'),calc.get('call_mid'),calc.get('put_mid'),number(calc.get('move_pct')),number(calc.get('low')),number(calc.get('high')),calc['status'],a.get('retrieved_at')])
    cols=['종목','발표 예정 UTC','발표 후 첫 만기','현물 USD','ATM 행사가','콜 mid USD','풋 mid USD','스트래들/현물 %','현물−프리미엄','현물+프리미엄','호가 상태','옵션 수집 UTC']
    s=table('실적 발표 · ATM 스트래들 내재 변동폭',cols,rows)
    note=dict(type='text',title='발표 변동폭을 읽는 기준',text='향후21일의 수집 대상기업 중 가까운8개 발표를 확인합니다. 발표시각 이후 첫 만기의 같은 행사가 콜+풋 bid/ask 중간값 합계÷옵션 현물입니다. 양의 OI·양방향 호가·스프레드/mid 50% 이하·현물±3% ATM을 요구합니다. 확률구간이나 순수 실적 이벤트 변동성은 아니며 만기까지 다른 위험도 포함합니다. 달력은 제공처 예정일입니다. 현재 대상 '+str(len(rows))+'개 · 달력 확인 '+str(target.get('retrieved_at','자료 없음')))
    for obj,group in [(pm,'다이버전스·실적'),(earnings,'실적 이벤트')]:obj['sections'] += [dict(s,group=group),dict(note,group=group)]
    pm['missing']=[m for m in pm['missing'] if 'ATM 스트래들' not in m]
    pm['source']+=' · Cboe 공개 지연호가'

def flow_views(d,obj):
    raw=inputs(d)
    if not raw:return raw
    funds=[];coverage=[]
    for definition in ETF_DEFINITIONS:
        a=raw.get('info_'+definition['symbol']+'.json.gz',{});info=a.get('info',{});aum=number(info.get('totalAssets'))
        ok=a.get('status')=='ok' and info.get('quoteType')=='ETF' and info.get('currency')=='USD' and aum and aum>0
        coverage.append([definition['symbol'],definition['underlying'],definition['leverage'],aum if ok else None,a.get('retrieved_at'),definition['source'],'확인' if ok else 'AUM 미확보'])
        if ok:funds.append(dict(definition,aum=aum))
    rebal=[];indices=[]
    for underlying in sorted({a['underlying'] for a in ETF_DEFINITIONS}):
        selected=[r for r in funds if r['underlying']==underlying];expected=[r for r in ETF_DEFINITIONS if r['underlying']==underlying]
        if not selected:continue
        frame=d.frames.get(underlying,pd.DataFrame());adv=number((frame.close*frame.volume).tail(21).mean()) if len(frame)>=21 else None
        row=dict(name=underlying,coefficient=coefficient(selected),aum=sum(r['aum'] for r in selected),adv=adv,funds=[r['symbol'] for r in selected],coverage=f'{len(selected)}/{len(expected)}',price_date=str(frame.index[-1].date()) if len(frame) else None)
        (rebal if expected[0]['kind']=='stock' else indices).append(row)
    rebal.sort(key=lambda r:r['coefficient'],reverse=True);indices.sort(key=lambda r:r['coefficient'],reverse=True)
    rate=d.mac('DGS3MO').dropna();rate=float(rate.iloc[-1])/100 if len(rate) else 0;stocks=[]
    for symbol in US_STOCKS:
        source=raw.get('info_'+symbol+'.json.gz',{});info=source.get('info',{});cap=number(info.get('marketCap'));option=raw.get('options_'+symbol+'.json.gz',{});p=profile(option,option['underlying_price'],rate) if option.get('status')=='ok' else None
        r=next((r for r in rebal if r['name']==symbol),None);short=number(info.get('shortPercentOfFloat'))
        oi=sum(a.get('openInterest') or 0 for a in option.get('records',[]))
        stocks.append(dict(symbol=symbol,net=p['net'] if p else None,gamma_mcap_bp=p['net']*1e9/cap*10000 if p and cap else None,flip=p['flip'] if p else None,flip_distance=p['flip_distance'] if p else None,letf_adv_pct=r['coefficient']*.01/r['adv']*100 if r and r['adv'] else None,aum=r['aum']/1e9 if r else None,option_mcap_pct=oi*100*option['underlying_price']/cap*100 if p and cap else None,short_float_pct=short*100 if short is not None else None,days_to_cover=number(info.get('shortRatio')),short_date=pd.Timestamp(info['dateShortInterest'],unit='s',tz='UTC').strftime('%Y-%m-%d') if info.get('dateShortInterest') else None,retrieved_at=source.get('retrieved_at'),options_at=option.get('retrieved_at')))
    stocks=sensitivity(stocks);stocks.sort(key=lambda r:r['sensitivity'] if r['sensitivity'] is not None else -np.inf,reverse=True)
    sections=[dict(type='rebalancing',title='레버리지·인버스 ETF · 가정 충격별 일일 리밸런싱',stocks=rebal,indices=indices,default_shock=5),
        table('미국 지수 ETF · 부호 가정 감마',['ETF','GEX USD bn/1%','감마플립 USD','현물/플립 %','옵션 수집 UTC'],[[p['symbol'],p['net'],p['flip'],p['flip_distance'],p['retrieved_at']] for p in packets(d)]),
        table('미국 주식 · 기계적 수급 민감도',['종목','4요인 z 평균','확보 요인 수/4','GEX/시총 bp','현물/플립 %','LETF 리밸런싱/ADV % · 1% 충격','확보 LETF AUM USD bn','OI명목/시총 %','공매도/float %','숏커버 일수','공매도 기준일'],[[r[k] for k in ['symbol','sensitivity','factor_count','gamma_mcap_bp','flip_distance','letf_adv_pct','aum','option_mcap_pct','short_float_pct','days_to_cover','short_date']] for r in stocks]),
        heat('수급 민감도 분해 · 현재20종목 단면 z',['|감마|/시총','LETF/ADV','OI명목/시총','Short/Float'],[dict(name=r['symbol'],values=r['factor_z']) for r in stocks])]
    kr=raw.get('krx.json.gz')
    if kr:
        # Prefer the official net asset amount. NAV × shares is only a fallback
        # because the published NAV is rounded to two decimal places.
        for r in kr['etfs']:
            if (r.get('reported_net_assets') or 0)>0:r['aum_krw']=r['reported_net_assets'];r['aum_method']='KRX reported net assets'
        krows=sorted(kr['stocks'],key=lambda r:(r['foreign_net']+r['institution_net'])/r['total_volume'],reverse=True)
        sections.append(table('한국 대형주 · 최근5거래일 투자자 수급',['종목','코드','외국인 순매수 주','기관 순매수 주','전체 거래량 주','외국인/거래량 %','기관/거래량 %','합산/거래량 %','외국인 보유 %','시작','종료'],[[r['name'],r['symbol'],r['foreign_net'],r['institution_net'],r['total_volume'],r['foreign_net']/r['total_volume']*100,r['institution_net']/r['total_volume']*100,(r['foreign_net']+r['institution_net'])/r['total_volume']*100,r['foreign_holding_pct'],r['from_date'],r['date']] for r in krows]))
        themes,members=theme_rows(kr['etfs']);themes.sort(key=lambda r:r['hot'] if r['hot'] is not None else -np.inf,reverse=True)
        leveraged=[r for r in kr['etfs'] if '레버리지' in r['name'] and '인버스' not in r['name']];inverse=[r for r in kr['etfs'] if '인버스' in r['name']]
        la=sum(r['aum_krw'] or 0 for r in leveraged);ia=sum(r['aum_krw'] or 0 for r in inverse)
        sections += [table('한국 상장 레버리지·인버스 ETF 규모',['기준일','레버리지 개수','레버리지 NAV AUM 조원','인버스 개수','인버스 NAV AUM 조원','AUM 비율'],[[kr['date'],len(leveraged),la/1e12,len(inverse),ia/1e12,la/ia if ia else None]]),
            bars('한국 테마 ETF · 규모/모멘텀/회전 단면 z',[(r['theme'],r['hot']) for r in themes],'z'),
            table('한국 테마 ETF 관측',['팀 분류','개수','AUM 조원','NAV 1개월 변화 %','변화 확보 AUM %','당일 거래대금/AUM %','합성 z','대표 AUM 상품'],[[r['theme'],r['count'],r['aum_krw']/1e12,r['nav_1m_pct'],r['return_coverage'],r['turnover_pct'],r['hot'],r['representative']] for r in themes]),
            table('테마별 포함 ETF · 이름 규칙과 공식 기초지수',['팀 분류','코드','상품명','KRX 기초지수','NAV AUM 억원','NAV 1개월 변화 %'],[[r['theme'],r['code'],r['name'],r['benchmark'],r['aum_krw']/1e8,r['nav_1m_pct']] for r in members]),
            dict(type='text',title='한국 수급·테마의 단위와 기준',text=f"투자자 순매수는 주식 수이며 동일5거래일 전체 거래량으로 나눕니다. 외국인 지분율은 KRX 보고값입니다. ETF 기준 {kr['date']}, NAV 비교일 {kr['month_base']}. AUM은 KRX 보고 순자산총액을 우선하고 없을 때 NAV×상장좌수로 계산합니다. 분류는 상품명 첫 일치 규칙(공식 업종 아님). 테마는 비레버리지 상품만 포함하며 ln(AUM), AUM가중 NAV 변화, 당일 거래대금/AUM의 단면 z 평균입니다. NAV 변화는 분배금·분할 미조정이며 절대100% 초과 관측은 합성에서 제외합니다. 신규 상품의 1개월 결측은0으로 채우지 않습니다. ETF AUM·거래량은 설정/환매 순유입액이나 개인 실제 포지션이 아닙니다.")]
    sections += [table('레버리지 ETF 정의·AUM 수집 원장',['ETF','기초자산','일간 목표배율','AUM USD','수집 UTC','운용사 정의','상태'],coverage),
        table('미국 수급 관측 시각',['종목','정보 수집 UTC','옵션 수집 UTC','공매도 기준일'],[[r['symbol'],r['retrieved_at'],r['options_at'],r['short_date']] for r in stocks]),
        dict(type='text',title='수급 모형 범위',text='미국20종목·공식 정의를 확인한 ETF 목록의 관측입니다. 리밸런싱=Σ(L²−L)×수집 AUM×가정 충격이며 실제 체결 예측이 아닙니다. ADV는 기초종목의 최근21세션 비조정 종가×거래량 평균입니다. 지수는 실제 시장 ADV 분모가 없으므로 금액만 표시합니다. 주식 감마/OI는7~45일중첫3만기이고 콜+/풋− 가정입니다. 1% 충격 LETF/ADV, |GEX|/시총, OI명목/시총, Short/Float의 단면 z를 평균하며4요인이 전부 있어야 점수를 표시합니다. 미확보 LETF는0으로 처리하지 않습니다. AUM의 공급처 기준일은 별도 제공되지 않아 수집일과 구분 불가하며 공매도는 표시된 과거 보고일입니다.')]
    obj['sections'] += [dict(s,group='비펀더멘탈 수급') for s in sections];obj['method_note']+=' 비펀더멘탈 수급의 미국20종목·LETF 리밸런싱·한국 대형주 투자자·국내 테마 ETF 패널을 독립 계산합니다.'
    obj['missing'].append('레버리지 ETF는 수집 원장의 명시적 표본으로 전 세계 모든 상품이 아닙니다. 국내 단일주식/해외 한국주식 LETF, 전 만기 옵션·실제 딜러 inventory는 미포함입니다. 공매도·AUM 제공처 지연을 확인해야 합니다.')
    return raw

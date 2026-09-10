"""Research-sector directory and evidence-backed company geography."""
import re
from datetime import datetime,timezone
from .chain_data import settings,PROFILE,age_hours
from .chain_geo import COUNTRIES
from .events_data import read
from .store import ROOT,read_json
from .acquire import stamp

GROUP='밸류체인 유니버스'


def build(d,obj):
    c=settings();p=d.resource(PROFILE);pack=read(p) if p.exists() else {}
    p=d.resource('chain/locations.json.gz');geo=read(p) if p.exists() else {}
    p=d.resource('chain/collection.json.gz');report=read(p) if p.exists() else {}
    state={r['symbol']:r for r in report.get('companies',[])}
    companies=[];now=datetime.now(timezone.utc)
    for company in c['companies']:
        symbol=company['symbol'];r=pack.get('companies',{}).get(symbol,{});a=r.get('data',{})
        point=geo.get('locations',{}).get(symbol)
        if point and (point['profile_city']!=a.get('city') or point['profile_country']!=a.get('country')):point=None
        currency=a.get('currency');cap=a.get('marketCap')
        # Provider pence/cent conventions need a separate reviewed capital unit.
        cap_ok=bool(currency and re.fullmatch('[A-Z]{3}',currency))
        companies.append(dict(symbol=symbol,name=company['name'],provider_name=a.get('longName'),
            previous_symbol=company.get('previous_symbol'),symbol_source=company.get('symbol_source'),
            country=a.get('country'),country_code=COUNTRIES.get(a.get('country')),city=a.get('city'),
            region=a.get('state'),location=point,website=a.get('website'),sector=a.get('sector'),industry=a.get('industry'),
            market_cap=cap if cap_ok else None,cap_currency=currency if cap_ok else None,
            cap_unit_pending=cap is not None and not cap_ok,quote_time=a.get('regularMarketTime'),
            retrieved_at=r.get('retrieved_at'),checked_at=r.get('checked_at'),stale=age_hours(r.get('checked_at'),now)>7*24,
            collection_state=state.get(symbol,{}).get('state','unavailable')))
    available={r['symbol'] for r in companies}
    evidence=read_json(ROOT/'config/relation_evidence.json')
    relations=[dict(id=r['id'],source=r['source'],target=r['target'],kind='valuechain',label=r['basis'],
                    evidence=evidence['sources'][r['source_id']])
               for r in evidence['links'] if r['relation']=='supplies' and r['source'] in available and r['target'] in available]
    trade=next((s for s in obj['sections'] if s['type']=='tradeglobe'),{})
    return dict(type='chainuniverse',group=GROUP,title='밸류체인 유니버스 · 업종별 기업 탐색',
        groups=c['groups'],sectors=c['sectors'],companies=companies,relations=relations,
        company_areas=[dict(id='TW',name='대만',lon=121,lat=24)],
        trade_areas=trade.get('areas',[]),trade_year=trade.get('year'),geo_source=geo.get('source',{}),geo_error=geo.get('error_type'),
        scope=c['scope'],collection=report.get('companies',[]))


def views(d,obj):
    obj['sections']=[s for s in obj['sections'] if s.get('group')!=GROUP]
    obj['sections'].insert(0,build(d,obj));obj['generated_at']=stamp()
    if 'GeoNames' not in obj['source']:obj['source']+=' · GeoNames · SEC 공시 공급관계'
    obj['missing']=[m for m in obj['missing'] if not m.startswith('밸류체인 유니버스의')]
    obj['missing'].append('밸류체인 유니버스의53개 업종·151기업 탐색을 연결했습니다. 소재지는 공급자 프로필, 지도 점은 도시 대표 좌표입니다. 기업별 전체 공급·물류 및 경쟁우위 근거는 추가 수집 대상이며 소재국 총수출은 기업 수출이 아닙니다.')
    return obj

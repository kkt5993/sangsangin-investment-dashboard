"""Build all feasible tab snapshots from local data. No network and no scheduling."""
import argparse,json
from datetime import datetime,timezone
from .engine import *
from .market_modules import rankings,etf_monitor,multiasset,dynamics,watch
from .macro_modules import regimes,risk,weekend,geoecon
from .financial_modules import financial_rows,local_growth,earnings,growth,discovery,strategies
from .platform_modules import libraries,networks
from .quant_modules import quant
from .build import make_snapshots
from .universe import symbols
from .subview_modules import extend
from .subviews import attach

def build(d):
    rank=rankings(d);print('Official rankings',[(k,v['available'],v['expected']) for k,v in rank.items()],flush=True)
    price={s:d.price(s,adjusted=s.endswith('.KS')) for s in d.frames}
    quality={s:dict(m,first_date=m.get('first') or m.get('first_date'),last_date=m.get('last') or m.get('last_date')) for s,m in d.quality.items() if s in symbols()}
    rs,mom=make_snapshots(price,dict(provider='Yahoo Finance; KRX and official ETF definitions',vintage=d.as_of,instruments=quality),d.as_of)
    rs['stock_rankings']={market:{k:v for k,v in r.items() if k!='rows'} for market,r in rank.items()}
    for a in [rs,mom]:
        a['price_quality']=d.correction_meta
        a['method_note']='공식 KRX·ETF 운용사·미국 GICS 정의를 바탕으로 독립 계산합니다. 국내 종목 순위는 KRX 구성목록, 미국은 IVV 공시 주식입니다. 원본의 불명확한 종목명은 공식 상품명으로 확정해 표시하며, 비공개 원본 엔진과 수치 동등성은 미검증입니다.'
        write_json(ROOT/'docs/data'/(a['module']+'.json'),clean_json(a))
    objects={a['module']:a for a in [f(d) for f in [etf_monitor,multiasset,dynamics,regimes,risk,weekend,geoecon]]}
    objects['watch']=watch(d,rank);objects['quant']=quant(d)
    financial=financial_rows(d);consensus,casof=local_growth(d)
    for obj in [earnings(d,financial,consensus),growth(d,financial,consensus,casof),discovery(d,financial,rank),strategies(d,financial)]+libraries(d)+networks(d,financial,rank):objects[obj['module']]=obj
    for obj in extend(d,objects,rank).values():d.export(attach(obj))
    status={}
    for file in (ROOT/'docs/data').glob('*.json'):
        a=read_json(file)
        if not isinstance(a,dict) or not a.get('module'):continue
        if a.get('schema_version')==2:
            a=attach(a);write_json(file,a)
        if a.get('price_quality')!=d.correction_meta:
            a['price_quality']=d.correction_meta;write_json(file,a)
        status[a['module']]=dict(status=a['status'],as_of=a['as_of'],bytes=file.stat().st_size,sections=len(a.get('sections',[])),missing=a.get('missing',[]),subviews=a.get('subviews',[]))
    status['overview']=dict(status='operational',as_of=d.as_of);status['glance']=dict(status='operational',as_of=d.as_of)
    overview=dict(as_of=d.as_of,vintage=d.vintage,price_series=len(d.frames),macro_series=len(d.macro),financial_companies=len(financial),consensus_as_of=casof,price_quality=d.correction_meta,universes={k:{x:v for x,v in r.items() if x in ['available','expected','membership_as_of','source']} for k,r in rank.items()},
        implemented=len([k for k,v in status.items() if k not in ['overview','glance'] and v['status']!='blocked']),modules=status)
    write_json(ROOT/'docs/data/status.json',overview)
    (ROOT/'docs/status.js').write_text('const BUILD_STATUS = '+json.dumps(clean_json(overview),ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    print('Final public module snapshots',len(status),'price series',len(d.frames),'macro',len(d.macro),'financial',len(financial),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default='2026-09-08');a=p.parse_args();build(Data(a.as_of))
if __name__=='__main__':main()

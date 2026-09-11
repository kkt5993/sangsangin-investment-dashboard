"""Dated 13F cards and complete position ledger; no live-ownership inference."""
from copy import deepcopy
from datetime import date,datetime,timezone
from decimal import Decimal
from .guru_data import FILE,read,settings,latest
from .guru_identifiers import FILE as IDENTIFIERS,resolve

def holdings(report):
    groups={};denominator=report['table_sum']
    for r in report['entries']:
        if r['cusip']=='000000000' and r['value']==0 and Decimal(r['quantity'])==0:continue
        key=(r['cusip'],r['share_class'],r['quantity_type'],r['option'])
        g=groups.setdefault(key,dict(issuer=r['issuer'],share_class=r['share_class'],cusip=r['cusip'],option=r['option'],quantity_type=r['quantity_type'],value=0,quantity=Decimal(0),source_rows=0))
        g['value']+=r['value'];g['quantity']+=Decimal(r['quantity']);g['source_rows']+=1
    out=[]
    for g in groups.values():
        g['weight']=float(round(Decimal(g['value'])*100/denominator,6)) if denominator else None
        g['value']=str(g['value']);g['quantity']=str(g['quantity']);out.append(g)
    return sorted(out,key=lambda r:(-Decimal(r['value']),r['cusip'],r['share_class'],r['option'] or ''))

def views(d,dragon,now=None):
    now=now or datetime.now(timezone.utc)
    path=d.resource(FILE);packet=read(path) if path.exists() else {};reports=packet.get('filings',[]);items=[]
    identifiers=d.resource(IDENTIFIERS);mapping_packet=read(identifiers) if identifiers.exists() else {};mappings=mapping_packet.get('mappings',{})
    entities=next((s['entities'] for s in dragon['sections'] if s['type']=='entities'),[]);entity_lookup={e['id']:e for e in entities};excluded={};linked=0
    for e in entities:e['guru_positions']=[]
    for manager in settings():
        report=latest(reports,manager['cik'],d.as_of);item=deepcopy(manager);item.update(report=None,holdings=[],ledger=[])
        if report:
            item['report']={k:deepcopy(v) for k,v in report.items() if k not in ['entries','contact_hash']}
            for key in ['value_total','table_sum','reconciliation_difference']:item['report'][key]=str(report[key])
            item['report']['age_days']=(date.fromisoformat(d.as_of)-date.fromisoformat(report['report_date'])).days
            item['report']['latest_confirmed']=False # A reviewed filing is not an exhaustive submissions search.
            item['holdings']=holdings(report) if report['resolution']=='holdings' else []
            item['ledger']=[dict(r,value=str(r['value']),sole=str(r['sole']),shared=str(r['shared']),none=str(r['none'])) for r in report['entries']]
            for h in item['holdings']:
                h['entity'],h['link_reason']=resolve(h,mappings,entities,now)
                if not h['entity']:excluded[h['link_reason']]=excluded.get(h['link_reason'],0)+1;continue
                linked+=1;entity=h['entity'];entity_lookup[entity['id']]['guru_positions'].append(dict(manager_id=item['id'],manager=item['name'],filer=item['filer'],cik=item['cik'],report_date=report['report_date'],accepted_at=report['accepted_at'],filing_date=report['filing_date'],source_url=report['index_url'],unit=report['unit'],reconciliation_difference=str(report['reconciliation_difference']),position=deepcopy(h),mapping=deepcopy(entity)))
        items.append(item)
    collection={k:v for k,v in packet.get('collection',{}).items() if k not in ['contact_hash','config_hash']}
    view=dict(type='gurus',title='스마트머니 · 13F 공시 보유',group='지금 주목',items=items,collection=collection,source_vintage=path.parent.parent.name if path.exists() else None,
        scope='확인한 분기말 공시의 보유입니다. 현재 보유·매수 추천·전체 운용자산이 아니며 비공개 보유, 현금, 공매도 등은 포괄하지 않습니다. 인물명은 추적 분류이고 실제 보고 법인을 별도로 표시합니다. 최신 공시의 완전한 조회 여부는 수집 상태와 구분합니다.',
        weight_basis='비중 = 같은 CUSIP·주식 종류·수량 단위·PUT/CALL의 보고 금액 합 ÷ 전체 정보표 행의 보고 금액 합 ×100. 옵션의 보고 금액은 옵션 프리미엄·델타 노출이 아닙니다. 표지 총액과 정보표 합계를 별도로 대조합니다.')
    view['identifiers']=dict(source='OpenFIGI',source_url='https://www.openfigi.com/api/documentation',source_vintage=identifiers.parent.parent.name if identifiers.exists() else None,collection=mapping_packet.get('collection',{}),linked_positions=linked,linked_entities=sum(bool(e['guru_positions']) for e in entities),excluded=excluded,scope='CUSIP→미국 FIGI→티커와 현재 기업 상세의 정확한 일치만 연결합니다. 식별자 조회시각은 분기말 보유일과 다르며 과거 시점의 티커 대응을 보증하지 않습니다. 옵션은 기초종목 연결이며 주식 보유로 바꾸지 않습니다.')
    dragon['sections']=[s for s in dragon['sections'] if s['type']!='gurus'];pos=next((i+1 for i,s in enumerate(dragon['sections']) if s['type']=='dragonfocus'),len(dragon['sections']));dragon['sections'].insert(pos,view)
    alert=next((s for s in dragon['sections'] if s['type']=='dragontriggers'),None)
    if alert:
        alert['log']=[r for r in alert['log'] if r.get('kind')!='13F 공시']
        for item in items:
            r=item['report']
            if r:alert['log'].append(dict(id='13f:'+item['id'],date=r['accepted_at'],title=item['name']+' · '+item['filer'],kind='13F 공시',detail='접수일 기준 · 보고일 '+r['report_date']+' · 신규 편입 신호 아님',url=r['index_url']))
        alert['log'].sort(key=lambda r:(r['date'],r['id']),reverse=True);alert['log']=alert['log'][:8]
    # Holdings are displayed independently until exact security-to-entity mapping
    # and the reference rule's quarterly lag contract have been established.
    for s in dragon['sections']:
        if s['type'] in ['dragonfocus','dragontriggers']:
            for r in s['rules']:
                if r['id']=='guru':r['status']='공시 연결 · 신호 보류';r['basis']='6개 보고 법인 공시·확인된 CUSIP 기업 대응 연결. 최신 공시 완전성과 분기 시차 검증 전 +3 합산 보류'
    dragon['missing']=[m.replace('·13F·정량 투자뷰','·정량 투자뷰') for m in dragon['missing']]
    dragon['missing']=[m for m in dragon['missing'] if not m.startswith('13F는6개 보고 법인의 확인 공시')]
    gap='13F는6개 보고 법인 공시와 확인된 CUSIP의 기업 상세를 연결합니다. 최신 전체 조회·과거 연속 변화·미대응 식별자와 구루 뉴스/관심분야 자동집계는 미완이며 신호점수에 합산하지 않습니다.'
    if gap not in dragon['missing']:dragon['missing'].append(gap)
    return dragon

"""Dated 13F cards and complete position ledger; no live-ownership inference."""
from copy import deepcopy
from datetime import date
from decimal import Decimal
from .guru_data import FILE,read,settings,latest

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

def views(d,dragon):
    path=d.resource(FILE);packet=read(path) if path.exists() else {};reports=packet.get('filings',[]);items=[]
    for manager in settings():
        report=latest(reports,manager['cik'],d.as_of);item=deepcopy(manager);item.update(report=None,holdings=[],ledger=[])
        if report:
            item['report']={k:deepcopy(v) for k,v in report.items() if k not in ['entries','contact_hash']}
            for key in ['value_total','table_sum','reconciliation_difference']:item['report'][key]=str(report[key])
            item['report']['age_days']=(date.fromisoformat(d.as_of)-date.fromisoformat(report['report_date'])).days
            item['report']['latest_confirmed']=False # A reviewed filing is not an exhaustive submissions search.
            item['holdings']=holdings(report) if report['resolution']=='holdings' else []
            item['ledger']=[dict(r,value=str(r['value']),sole=str(r['sole']),shared=str(r['shared']),none=str(r['none'])) for r in report['entries']]
        items.append(item)
    collection={k:v for k,v in packet.get('collection',{}).items() if k not in ['contact_hash','config_hash']}
    view=dict(type='gurus',title='스마트머니 · 13F 공시 보유',group='지금 주목',items=items,collection=collection,source_vintage=path.parent.parent.name if path.exists() else None,
        scope='확인한 분기말 공시의 보유입니다. 현재 보유·매수 추천·전체 운용자산이 아니며 비공개 보유, 현금, 공매도 등은 포괄하지 않습니다. 인물명은 추적 분류이고 실제 보고 법인을 별도로 표시합니다. 최신 공시의 완전한 조회 여부는 수집 상태와 구분합니다.',
        weight_basis='비중 = 같은 CUSIP·주식 종류·수량 단위·PUT/CALL의 보고 금액 합 ÷ 전체 정보표 행의 보고 금액 합 ×100. 옵션의 보고 금액은 옵션 프리미엄·델타 노출이 아닙니다. 표지 총액과 정보표 합계를 별도로 대조합니다.')
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
                if r['id']=='guru':r['status']='공시 연결 · 신호 보류';r['basis']='6개 보고 법인 공시 원장 연결. CUSIP과 기업의 정확한 대응·분기 시차 검증 전 +3 합산 보류'
    dragon['missing']=[m.replace('·13F·정량 투자뷰','·정량 투자뷰') for m in dragon['missing']]
    gap='13F는6개 보고 법인의 확인 공시·비중·전체 행을 표시합니다. 최신 전체 조회·과거 연속 변화·기업 CUSIP 대응과 구루 뉴스/관심분야 자동집계는 미완이며 신호점수에 합산하지 않습니다.'
    if gap not in dragon['missing']:dragon['missing'].append(gap)
    return dragon

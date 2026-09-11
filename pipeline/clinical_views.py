"""Public registry summaries and provenance; recruitment is not an investment signal."""
from copy import deepcopy
from .clinical_data import FILE,read

def views(d,dragon):
    path=d.resource(FILE);packet=read(path) if path.exists() else {};rows=deepcopy(packet.get('scopes',[]))
    view=dict(type='clinical',source_vintage=path.parent.parent.name if path.exists() else None,group='트리거·촉매',title='임상시험 등록부 · 모집상태와 단계',items=rows,data_version=packet.get('data_version'),retrieved_at=packet.get('retrieved_at'),checked_at=packet.get('checked_at'),error=packet.get('error'),
        scope='모집 중은 RECRUITING 상태,3상은 모든 모집상태의 PHASE3 포함 연구입니다. 서로 포함관계가 아니므로 합산하지 않습니다. 각 목록은 최근 갱신5건이며 건수는 공식 API totalCount입니다. 등록부상 연구 상태이며 승인·효능·기업 수익 신호가 아닙니다.')
    dragon['sections']=[s for s in dragon['sections'] if s['type']!='clinical'];dragon['sections'].append(view)
    alert=next((s for s in dragon['sections'] if s['type']=='dragontriggers'),None)
    if alert is not None:
        alert['log']=[r for r in alert['log'] if r.get('kind')!='임상 등록부']
        for r in rows:
            active=r['groups']['recruiting']['count'];recent=r['groups']['all']['latest']
            if not active or not recent:continue
            latest=recent[0]
            alert['log'].append(dict(id='clinical:'+r['id'],date=latest['updated'],title=r['name'],kind='임상 등록부',detail=f"모집 중 {active}건 · 3상(전체 상태) {r['groups']['phase3']['count']}건 · 최근 기록 갱신일",url=latest['url']))
        alert['log'].sort(key=lambda r:(r['date'],r['id']),reverse=True);alert['log']=alert['log'][:8]
    dragon['missing']=[m.replace('완전한 합성점수와 임상 모집 로그는 미산출입니다.','완전한 합성점수는 미산출입니다.') for m in dragon['missing']]
    gap='임상 등록부는 명시된3검색범위의 모집/3상 건수와 최근5기록만 제공합니다. 원본 검색식은 미공개이며 모든 계열사·약물과 연구별 전체 변화 이력은 미확보입니다.'
    if gap not in dragon['missing']:dragon['missing'].append(gap)
    return dragon

"""Visible subview inventory, including the remaining unconnected source views."""
EXPECTED={
 'dragonglass':['관계 지도','지금 주목','위성 현장','Entity 360','시나리오','결정 원장','트리거·촉매','리서치','데이터 소스','현황판','방법론'],
 'geoecon':['주목 상황','지역 모니터','복합지표','키워드 트렌드','시장 지표','뉴스 원장','인과·영향 모델'],
 'regime':['월별 국면','미국 경제국면','한국 시장국면','시장국면','국면별 성과','국면 전이','밸류에이션','실적 이벤트','Soros 재귀성'],
 'strategies':['턴어라운드','내부자 매수','PEAD','스탯아브 페어','실적 모멘텀'],
 'risk':['리스크 콕핏','신호등 US·KR','파생·옵션','KOSPI 숏감마','쏠림·신용','CFTC 포지션'],
 'multiasset':['자산 모니터','패턴 스캐너','자산배분'],
 'pm_weekend':['매크로 브리프','CFTC 포지션'],
}
GAPS={'위성 현장':'시설별 좌표·검증된 위성 관측 필요','인과·영향 모델':'이벤트와 인과 관계·전파 가중치 필요','Soros 재귀성':'원본 복합 산식과 지수 이익 역사 필요','KOSPI 숏감마':'행사가·만기별 국내 옵션 OI·IV 필요'}
def attach(obj):
    groups=list(dict.fromkeys(s.get('group','종합') for s in obj.get('sections',[])))
    expected=EXPECTED.get(obj['module'],groups)
    obj['subviews']=[dict(name=g,status='connected' if g in groups else 'pending',sections=sum(s.get('group','종합')==g for s in obj.get('sections',[])),reason=GAPS.get(g,'')) for g in dict.fromkeys(expected+groups)]
    return obj

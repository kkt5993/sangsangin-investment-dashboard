"""Visible subview inventory, including the remaining unconnected source views."""
EXPECTED={
 'globe':['국가 교역','기업 국가 탐색','밸류체인 유니버스','SAURON'],
 'dragonglass':['관계 지도','지금 주목','위성 현장','Entity 360','시나리오','결정 원장','트리거·촉매','리서치','데이터 소스','현황판','방법론'],
 'geoecon':['주목 상황','지역 모니터','복합지표','키워드 트렌드','시장 지표','뉴스 원장','인과·영향 모델'],
 'regime':['월별 국면','미국 경제국면','한국 시장국면','시장국면','국면별 성과','국면 전이','밸류에이션','실적 이벤트','거시 발표 달력','산업별 핵심지표','Soros 재귀성'],
 'strategies':['턴어라운드','내부자 매수','PEAD','스탯아브 페어','실적 모멘텀'],
 'risk':['리스크 콕핏','신호등 US·KR','선제위험·감마','파생·옵션','KOSPI 숏감마','쏠림·신용','CFTC 포지션','파생 Wag-the-Dog','비펀더멘탈 수급'],
 'multiasset':['자산 모니터','패턴 스캐너','자산배분'],
 'pm_weekend':['PM 키 게이지','금리·성장','크로스에셋 속보','CTA 시스템 트렌드','매크로 z-score','다이버전스·실적','기초 매크로 시계열','CFTC 포지션'],
}
GAPS={'위성 현장':'22시설 실관측·NASA 전 지구 배경 연결; 고해상도 배경·지명 레이어는 추가 확인 필요','인과·영향 모델':'이벤트와 인과 관계·전파 가중치 필요','Soros 재귀성':'원본 복합 산식과 지수 이익 역사 필요'}
GAPS['비펀더멘탈 수급']='종목·레버리지 ETF AUM·공매도·국내 투자자별 수급 수집 중'
GAPS['밸류체인 유니버스']='53개 세부 업종·기업 본사/도시·회사별 공급 및 물류 관계 근거 연결 필요'
GAPS['SAURON']='시설·지진 스냅샷·SGP4 궤도·3D 카메라·6개 화면 효과 연결; Google 실사3D는 별도 키 필요'
def attach(obj):
    groups=list(dict.fromkeys(s.get('group','종합') for s in obj.get('sections',[])))
    expected=EXPECTED.get(obj['module'],groups)
    obj['subviews']=[dict(name=g,status='connected' if g in groups else 'pending',sections=sum(s.get('group','종합')==g for s in obj.get('sections',[])),reason=GAPS.get(g,'')) for g in dict.fromkeys(expected+groups)]
    return obj

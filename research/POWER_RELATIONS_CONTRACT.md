# 전력구매계약 관계

기업분석 관계 지도에 공식 발표를 확인한 전력구매계약5관계를 추가했다. Constellation→Microsoft/Meta, Vistra→Meta, NextEra→Alphabet(Google), AES→Microsoft다. `config/power_relations.json`은 발표일·검토시각·용량 기준·기간·조건·원문을 기록하며, 가격과 공식 업종은 기존 기업 상세와 PC 가격 캐시를 재사용한다. 새로운 공식 지수 편입을 주장하지 않는다.

## 실제 공급과 계약의 구분

| 계약 | 공개 수치 | 일정과 해석 |
|---|---|---|
| Crane / Microsoft | 20년·835MW | 2024-09-20 계약 발표, 2026-08-06 발표의2027년 재가동 목표. 최초2028년 계획에서 변경. 인허가·재가동 조건이며 현재 공급량 아님 |
| Clinton / Meta | 20년·1121MW | 2027년6월 구매 개시 예정. 기존 발전소 계속 운영/증설 지원. 추가30MW를1121MW에 다시 더하지 않음 |
| Vistra / Meta | 20년·2609MW | 2026년말 개시,2034년 전체 목표. 기존2176MW+증설433MW. 계통으로 공급되며 특정 데이터센터 전용선 아님 |
| Duane Arnold / Google | 25년·시설615MW | 2029년1분기 재가동 목표/인허가 조건. CIPCO가 잔여 물량을 구매하므로 Google 계약MW는 미확인 |
| AES / Microsoft | 태양광3사업475MW | MISO 계통,발표 당시2사업2025상반기 예상. 현재 가동 여부·개별 계약MW·기간 미확인. 기존1GW 초과 계약과 합산하지 않음 |

모든 수치는 발표된 계약·설비의 사실이다. 실시간 송전량·발전량(MWh)·매출·고객 수요 비중과 다르다. 가격 기준일보다 미래인 발표/후속 근거는 표시하지 않는다. 최신 검토 데이터이므로 과거 정보시점 백테스트에는 쓰지 않는다. 후속 수정의 원문이 과거 cutoff보다 늦으면 해당 수정 계약을 과거에 소급하지 않으며, 최초 계약의 완전한 PIT 이력을 재구성한 것은 아니다.

## 관계·차트·계산

기존3D 노드/선·객체/관계 필터·회전/확대·객체 상세·단일 충격·8시나리오 구조를 유지한다. `powers`는 화면에서 ‘전력 구매계약’으로 표시한다. 상세의 펼침 영역에 계약/시설MW를 분리하고 기간/발표/검토/문서확인/미확인을 표시한다. 새4기업의 가격을 기존 캐시에서 읽어 전체26기업의3개월 상관·동일시장1/3/5일 회귀와 전체 BY 보정을 다시 계산한다. 전체707기업의 원장 행렬·공식분류는 유지한다.

전파 계수는 기존가정 순방향0.28/역방향0.62 ×(0.7+0.1×weight)×0.9, weight=1이다. 계약MW나 실제 손익에 맞춰 추정한 탄력성이 아니며 미래 계약에도 ‘계약 관계의 가정 충격’을 적용한다. 확정 가동·수익률·인과 효과를 주장하지 않는다. 기술 협업은 기존 `collaborates`로 남긴다. 리서치 카탈로그는5최초 발표와 Crane 후속 발표를 URL별로 연결하고 발표일과 검토일을 분리한다.

## 정기 갱신

평일08/18시 refresh의 `pipeline.power_relations`가 기존 문서 검사 코드를 재사용한다. 원문은 로컬 `relations/power_evidence/`, 조회 기록은 `relations/power_sources.json.gz`에만 보관한다. 문서별30일 재확인, 같은 호스트 실패 후 같은 배치의 나머지 요청은 보류, 기존 성공 문서 보존. 보류 문서는 다음 실행에서 조회할 수 있다. URL 변경은 기존 확인 이력을 승계하지 않는다. 상태·본문 해시 변화는 표시하지만 계약 이행·신규 발표·계약 해지 의미를 자동 판정하지 않는다. 변경 감지 후 새 검토로 확인하기 전까지 ‘내용 재검토 필요’를 유지한다. 원문에 동적 요소가 있으면 의미 없는 변경도 감지될 수 있다.

웹 조회 도구에서6공식 페이지 내용을 확인했다. 이 PC의 직접 보존은 초기6조회 중4성공, Constellation 투자자 사이트2문서는 연결/읽기 시간초과로 미보존이며 화면의 문서 확인 상태에도 구분한다. 웹 검토 사실을 로컬 수집 성공으로 치환하지 않는다.

## 공식 근거

- [Crane 최초 계약](https://investors.constellationenergy.com/news-releases/news-release-details/constellation-launch-crane-clean-energy-center-restoring-jobs)
- [Crane 2026년2분기 진행상황](https://www.constellationenergy.com/news/2026/08/constellation-reports-second-quarter-2026-results.html)
- [Clinton 계약](https://investors.constellationenergy.com/news-releases/news-release-details/constellation-meta-sign-20-year-deal-clean-reliable-nuclear)
- [Vistra 계약](https://investor.vistracorp.com/2026-01-09-Vistra-and-Meta-Announce-Agreements-to-Support-Nuclear-Plants-in-PJM-and-Add-New-Nuclear-Generation-to-the-Grid)
- [NextEra 계약](https://www.investor.nexteraenergy.com/news-and-events/news-releases/2025/10-27-2025-203948689)
- [AES 계약](https://www.aes.com/newsroom/aes-delivers-more-carbon-free-power-support-microsoft-operations)

전체 전력계약/사업관계/원본255객체·581관계의 완성을 뜻하지 않는다. Talen→Amazon 공식 발표도 확인했지만 현재 기업 상세/가격 대상 밖이며 아직 연결하지 않았다. 나머지 사업관계 및 모든 계약의 연속 변경 이력은 계속 확장 대상이다.

"""Country export arcs with their own statistical area and annual denominator."""
from decimal import Decimal
from .trade_data import AREAS, CONFIG, FOLDER, API
from .events_data import read
from .engine import table
from .acquire import stamp

GROUP = '국가 교역'
COMPANIES = '기업 국가 탐색'
STATES = {'ok':'신규/변경 관측', 'unavailable':'응답에 자료 없음', 'reused':'기존 관측 재사용', 'error':'수집 실패 · 이전 관측 유지', 'deferred':'조회 보류'}


def build(d):
    year = int(d.as_of[:4]) - CONFIG['year_lag']
    manifest_path = d.resource(FOLDER+'collection.json.gz')
    manifest = read(manifest_path) if manifest_path.exists() else {}
    states = {r['code']: r for r in manifest.get('areas', [])} if manifest.get('year') == year else {}
    by_code = {a['code']: a['id'] for a in AREAS}
    areas = []
    for a in AREAS:
        file = d.resource(FOLDER+f'{year}/{a["code"]}.json.gz')
        raw = read(file) if file.exists() else {}
        if raw and (raw.get('reporter') != a['code'] or raw.get('year') != year):
            raise ValueError('Mismatched annual trade cache')
        rows = {r['partner']: r for r in raw.get('rows', [])}
        exports = [[by_code[code], r['usd'], r['reported'], r['aggregate']]
                   for code, r in rows.items() if code in by_code and code != a['code']]
        world = rows.get(0, {}).get('usd')
        if exports and (world is None or sum(Decimal(r[1]) for r in exports) > Decimal(world)*Decimal('1.000001')):
            raise ValueError('Selected partners double-count the world denominator')
        areas.append(dict(a, exports=exports, world_usd=world, official_name=raw.get('official_name'),
                          coverage=raw.get('coverage'), retrieved_at=raw.get('retrieved_at'),
                          checked_at=states.get(a['code'], {}).get('checked_at') or raw.get('checked_at'), state=states.get(a['code'], {}).get('state', 'unavailable'),
                          classifications=sorted({r['classification'] for r in rows.values()})))
    return dict(type='tradeglobe', title='국가 간 상품 수출 · 정사영 지구본', group=GROUP,
                year=year, areas=areas, source=API, checked_at=manifest.get('checked_at'),
                coordinate_note=CONFIG['coordinate_note'],
                flags=['isReported: 원자료 직접 보고 여부', 'isAggregate: UN 집계 여부'],
                scope='C / A / HS TOTAL / X / partner2 0 / C00 / MOT 0 / current USD')


def views(d, obj):
    obj['generated_at'] = stamp()
    obj['sections'] = [s for s in obj['sections'] if s.get('group') != GROUP]
    for s in obj['sections']:
        if not s.get('group') or s.get('group') == '종합': s['group'] = COMPANIES
    data = build(d)
    obj['sections'].insert(0, data)
    obj['sections'].append(dict(table('교역 수집 원장 · 통계지역별 관측 여부',
        ['국가·통계지역', 'UN 코드', '자료 연도', '연결 파트너', '대세계 수출 USD', '자료 확보 UTC', '확인 UTC', '수집 상태'],
        [[a['name'], a['code'], data['year'], len(a['exports']), a['world_usd'],
          a['retrieved_at'], a['checked_at'], '빈 응답 재사용' if a['state']=='reused' and a['world_usd'] is None else STATES.get(a['state'],a['state'])] for a in data['areas']]),
        group=GROUP, collapsed=True, readable=True))
    obj['source'] = 'UN Comtrade · Yahoo Finance · KRX · Natural Earth (자료별 관측일 표시)'
    obj['method_note'] = ('국가 교역은 UN Comtrade 연간 상품 총수출(HS TOTAL)을 국가·통계지역 사이의 구면 곡선으로 표시합니다. '
        '화살표는 수출 방향이며 선 굵기는 금액의 로그 척도입니다. 금액은 기업 매출·특정 품목이나 실제 선박 항로가 아닙니다. '
        '모든 지역은 같은 연도이며, 비교 가능성을 위해 실행 연도보다2년 전 자료를30일마다 재확인합니다. '
        '들어오는 선도 상대국의 수출 보고값으로, 선택국 수입 통계와 다를 수 있습니다. 기존 기업 표는 수집된 재무 표본의 소재국 탐색입니다.')
    obj['missing'] = [
        '밸류체인 유니버스의53개 세부 업종·151개 기업 본사/도시 및 기업별 공급·수출·물류 관계는 추가 근거 확보와 구현이 필요합니다.',
        'SAURON의3D 카메라·지진·궤도 위성·센서 스타일은 미연결입니다. 기존 DRAGONGLASS 시설 관측과 별도 기능입니다.',
        'UN 자료가 없는 국가·통계지역/방향은 미확보로 표시하며 거울 수입이나 추정값으로 채우지 않습니다.']
    return obj

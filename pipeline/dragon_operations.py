"""Public operational evidence from local manifests; no network or private config."""
from datetime import datetime, timezone, timedelta
from copy import deepcopy
from .events_data import read
from .store import ROOT, read_json


def section(obj, kind):
    return next((s for s in obj.get('sections', []) if s['type'] == kind), {})


def age(value, now):
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            return None
        hours = (now - dt).total_seconds() / 3600
        return round(hours, 2) if hours >= 0 else None
    except (AttributeError, TypeError, ValueError):
        return None


def row(key, name, category, url, cadence, now, *, observed=None, checked=None,
        retrieved=None, error=False, count=None, detail='', state=None, vintage=None):
    hours = age(retrieved, now)
    status = ('error' if error else state or ('waiting' if retrieved is None else
              'unknown' if hours is None else 'stale' if hours > cadence else 'current'))
    return dict(id=key, name=name, category=category, url=url, cadence_hours=cadence,
                observed_at=observed, checked_at=checked, retrieved_at=retrieved,
                age_hours=hours, status=status, count=count, detail=detail, vintage=vintage)


def sources(d, dragon, now):
    rows = []
    def packet(name):
        p = d.resource(name)
        return read(p) if p.exists() else {}
    news = packet('news.json.gz')
    for i, feed in enumerate(news.get('sources', [])):
        items = [r for r in news.get('items', []) if r['source'] == feed['name']]
        rows.append(row('rss:' + str(i), feed['name'], '뉴스·정책', feed['url'], 24, now,
            checked=news.get('retrieved_at'), retrieved=news.get('retrieved_at') if feed['status'] == 'ok' else None,
            observed=max((r['published_at'] for r in items), default=None), error=feed['status'] == 'error',
            count=len(items), detail='현재 RSS 응답의 제목 표본. 전체 보도량이 아니며 과거 기사 날짜를 수집 실패로 판정하지 않습니다.',
            state='empty' if feed['status'] == 'empty' else None))
    clinical = section(dragon, 'clinical')
    rows.append(row('clinical', 'ClinicalTrials.gov', '공시·등록부', 'https://clinicaltrials.gov/data-api/api', 24, now,
        checked=clinical.get('checked_at'), retrieved=clinical.get('retrieved_at'), observed=clinical.get('data_version'),
        error=bool(clinical.get('error')), count=len(clinical.get('items', [])), vintage=clinical.get('source_vintage'),
        detail='3개 검색범위. 등록부 시각은 API 원문이며 시간대가 미표기되어 있습니다. 건수 단위는 검색범위입니다.'))
    guru = section(dragon, 'gurus'); collection = guru.get('collection', {})
    dates = [r['report']['accepted_at'] for r in guru.get('items', []) if r.get('report')]
    rows.append(row('sec13f', 'SEC EDGAR · 13F', '공시·등록부', 'https://www.sec.gov/edgar/search/', 24, now,
        checked=collection.get('attempted_at'), observed=max(dates, default=None), count=len(dates),
        state='manual' if collection.get('status') == 'needs_contact' else 'unknown', error=bool(collection.get('errors')),
        vintage=guru.get('source_vintage'),
        detail='확인된 보고법인 수입니다. 자동수집 상태: '+str(collection.get('status', '미확인'))+' · 검토 공시 보유와 최신 전체 조회 성공은 다릅니다. 접수일은 수집 성공일이 아닙니다.'))
    identifiers = packet('guru/identifiers.json.gz'); mappings = list(identifiers.get('mappings', {}).values())
    dates = [r.get('checked_at') for r in mappings if r.get('checked_at')]
    rows.append(row('figi', 'OpenFIGI · CUSIP', '공시·등록부', 'https://www.openfigi.com/api/documentation', 720, now,
        checked=identifiers.get('collection', {}).get('attempted_at'), retrieved=min(dates, default=None), count=len(mappings),
        error=bool(identifiers.get('collection', {}).get('errors')), vintage=guru.get('identifiers', {}).get('source_vintage'),
        detail='정상 매핑 30일·미대응 7일 캐시. 성공/미대응 식별자의 가장 오래된 확인 시각을 표시합니다. CUSIP 건수이며 기업 수와 다릅니다.'))
    attention = section(dragon, 'attention')
    if attention:
        records = attention.get('items', []); dates = [r['retrieved_at'] for r in records if r.get('retrieved_at')]
        ends = [r['metrics']['end'] for r in records if r.get('metrics', {}).get('end')]
        rows.append(row('wikimedia', 'Wikimedia · 기업 문서 관심도', '뉴스·정책', 'https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/', 24, now,
            checked=attention.get('collection', {}).get('attempted_at'), retrieved=min(dates, default=None), observed=min(ends, default=None),
            error=bool(attention.get('collection', {}).get('errors')), count=len(dates), vintage=attention.get('source_vintage'),
            detail='영문 기업 문서 직접 user 열람. 가장 오래된 성공 수집·UTC 관측일을 표시합니다. 뉴스량·고유 투자자 수가 아닙니다.'))
    company_news = section(dragon, 'companynews')
    if company_news:
        records=company_news.get('items',[]);dates=[r['retrieved_at'] for r in records if r.get('retrieved_at')]
        latest=[r['latest'] for r in records if r.get('latest')]
        rows.append(row('company-news','Yahoo Finance · 기업 RSS','뉴스·정책','https://finance.yahoo.com/',24,now,
            checked=company_news.get('collection',{}).get('attempted_at'),retrieved=min(dates,default=None),observed=max(latest,default=None),
            error=any(r.get('error') for r in records),count=len(dates),vintage=company_news.get('source_vintage'),
            detail='기업 피드별 관측 기사. 가장 오래된 성공 수집과 가장 최근 포함 기사 발행일을 구분합니다. 전체 뉴스량·기업 감성은 아닙니다.'))
    satellite = packet('satellite_collection.json.gz'); sites = satellite.get('sites', [])
    captures = [r['scene']['captured_at'] for r in sites if r.get('scene')]
    rows.append(row('sentinel', 'Sentinel-2 · Earth Search', '위성·위치', 'https://earth-search.aws.element84.com/v1', 168, now,
        checked=satellite.get('retrieved_at'), retrieved=satellite.get('retrieved_at'), observed=max(captures, default=None),
        count=len(captures), error=any(r.get('status') == 'error' for r in sites),
        detail=f'시설 {len(sites)}곳 중 영상 {len(captures)}곳. 가장 최근 촬영일과 수집 시각은 별개입니다. 구름·궤도 주기로 최신 촬영이 오래될 수 있습니다.'))
    sauron = packet('sauron/collection.json.gz')
    for key, name, hours, url in [('quakes', 'USGS 지진', 1, 'https://earthquake.usgs.gov/'),
                                 ('stations', 'CelesTrak 궤도 요소', 2, 'https://celestrak.org/')]:
        data = packet('sauron/' + key + '.json.gz'); report = next((r for r in sauron.get('sources', []) if r['key'] == key), {})
        content = data.get('data', {} if key == 'quakes' else [])
        observed = content.get('generated_at') if key == 'quakes' else min((r['EPOCH'] for r in content), default=None)
        count = len(content.get('events', [])) if key == 'quakes' else len(content)
        rows.append(row(key, name, '위성·위치', url, hours, now, observed=observed, count=count,
            checked=report.get('checked_at'), retrieved=data.get('retrieved_at'), error=bool(report.get('error_type')),
            detail='지진은 제공처 생성 시각, 궤도는 가장 오래된 요소 epoch입니다. 실시간 센서 수신을 뜻하지 않습니다.'))
    for key, name, category, file, field, hours, url in [
        ('trade', 'UN Comtrade', '교역·기업', 'trade/collection.json.gz', 'areas', 720, 'https://comtradeplus.un.org/'),
        ('company', 'Yahoo 기업 프로필', '교역·기업', 'chain/collection.json.gz', 'companies', 24, 'https://finance.yahoo.com/')]:
        p = packet(file); records = p.get(field, []); dates = [r['retrieved_at'] for r in records if r.get('retrieved_at')]
        rows.append(row(key, name, category, url, hours, now, observed=str(p['year']) if p.get('year') else None,
            checked=p.get('checked_at'), retrieved=min(dates, default=None), count=len(dates),
            error=any(r.get('state') == 'error' or r.get('error_type') for r in records),
            detail='성공 보존된 지역/기업 수와 가장 오래된 성공 수집 시각입니다. 일부 실패는 이전 성공값이 남아 있어도 오류로 표시합니다.'))
    # Preserve each series' observation and retrieval dates from the existing ledger.
    macro = next((s for s in dragon['sections'] if s.get('title') == '거시 데이터 원장'), {})
    providers = {}
    for r in macro.get('rows', []):
        providers.setdefault(r[2], []).append(dict(id=r[0], name=r[1], observed_at=r[3], unit=r[4], retrieved_at=r[5]))
    if not providers:
        for r in section(dragon, 'dragonsources').get('items', []):
            if r.get('series'):
                providers[r['name']] = deepcopy(r['series'])
    for i, (provider, records) in enumerate(sorted(providers.items())):
        r = row('macro:' + str(i), provider, '거시·시장', provider if provider.startswith('https://') else 'https://fred.stlouisfed.org/',
            24, now, count=len(records), state='unknown', detail='계열별 관측일과 수집일만 확인됩니다. 날짜만으로 24시간 캐시 준수 여부나 최근 요청 성공을 추정하지 않습니다.')
        r['series'] = records; rows.append(r)
    return rows


def views(d, objects, previous=None, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware build time required')
    dragon = objects['dragonglass']; graph = section(dragon, 'relationlab')
    source_rows = sources(d, dragon, now)
    displayed = {r['id'] for kind in ['dragonfocus', 'dragontriggers'] for r in section(dragon, kind).get('items', []) if r.get('hits')}
    counts = dict(objects=len(graph.get('nodes', [])), links=len(graph.get('links', [])),
        research=len(section(dragon, 'dragonresearch').get('items', [])), insights=None,
        signals=len(displayed), sites=len(section(dragon, 'satellite').get('sites', [])),
        countries=sum(r.get('kind') == 'country' for r in graph.get('nodes', [])))
    if previous is None:
        p = ROOT / 'docs/data/dragonglass.json'; previous = read_json(p) if p.exists() else {}
    prior = section(previous, 'dragonstatus').get('history', [])
    today = now.astimezone(timezone(timedelta(hours=9))).date().isoformat()
    # Only inherit previously published observations; never invent backfilled days.
    history = {r['date']: deepcopy(r) for r in prior if r['date'] < today}
    history[today] = dict(date=today, observed_at=now.isoformat(), **counts)
    module_objects = dict(objects)
    for key in ['rs', 'momentum']:
        path = ROOT / 'docs/data' / (key + '.json')
        if key not in module_objects and path.exists():
            module_objects[key] = read_json(path)
    modules = [dict(id=key, status=o['status'], as_of=o['as_of'], generated_at=o.get('generated_at'),
                   sections=len(o.get('sections', [])), missing=len(o.get('missing', [])))
               for key, o in sorted(module_objects.items())]
    common = dict(built_at=now.isoformat(), as_of=dragon['as_of'], schedule=dict(timezone='Asia/Seoul', hours=[8, 18], weekdays=[1, 2, 3, 4, 5]),
        scope='게시된 수집 기록을 보여주는 스냅샷입니다. 현재 PC의 실행 상태·예약 성공을 실시간 확인하지 않습니다. 한국시간 평일 08시·18시 예정이며 PC와 앱이 실행 중이어야 합니다. 실패한 갱신은 기존 사이트를 유지합니다.')
    added = [dict(type='dragonsources', group='데이터 소스', title='데이터 소스 · 수집 근거', items=source_rows, **common),
             dict(type='dragonstatus', group='현황판', title='현황판 · 데이터와 모듈', counts=counts,
                  history=[history[k] for k in sorted(history)], modules=modules, sources=source_rows,
                  definition='객체·관계는 관계지도 범위, 신호는 지금 주목/트리거 화면의 고유 신호 기업 수, 리서치는 공식·팀 문서 수입니다. 인사이트는 미산출(null)이며 0건으로 바꾸지 않습니다. 날짜별 마지막 게시 관측을 보존하고 빈 날짜를 채우지 않습니다.', **common)]
    dragon['sections'] = [s for s in dragon['sections'] if s.get('group') not in ['데이터 소스', '현황판']] + added
    dragon['generated_at'] = now.isoformat()
    for m in modules:
        if m['id'] == 'dragonglass':
            m.update(generated_at=dragon['generated_at'], sections=len(dragon['sections']))
    # The new source cards contain the complete series ledger, so no duplicate table.
    return dragon

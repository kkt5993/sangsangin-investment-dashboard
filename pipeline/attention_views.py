"""Observed article attention; not unique investors, sentiment, or a backtest."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from .attention_data import FILE, read, settings, age


def metrics(points, asof):
    rows = {r['date']: r['views'] for r in points if r['date'] <= asof}
    end = max(rows, default=None)
    result = dict(end=end, recent=None, previous=None, change=None, complete=False)
    if end is None:
        return result
    days = [(date.fromisoformat(end) - timedelta(days=i)).isoformat() for i in range(14)]
    if not all(k in rows for k in days):
        return result
    recent = sum(rows[k] for k in days[:7]); previous = sum(rows[k] for k in days[7:])
    return dict(end=end, recent=recent, previous=previous, change=round((recent / previous - 1) * 100, 6) if previous else None, complete=True,
                recent_start=days[6], previous_start=days[13], previous_end=days[7])


def views(d, dragon, now=None):
    now = now or datetime.now(timezone.utc); cfg = settings(); path = d.resource(FILE)
    packet = read(path) if path.exists() else {}; items = []
    entities = next(s for s in dragon['sections'] if s['type'] == 'entities')['entities']
    for e in entities:
        e.pop('attention', None)
    for spec in cfg['pages']:
        p = packet.get('pages', {}).get(spec['symbol'], {})
        same = all(p.get(k) == spec[k] for k in ['title', 'pageid', 'wikidata']) and p.get('project') == cfg['project']
        points = deepcopy(p.get('points', [])) if same else []
        points = [r for r in points if r['date'] <= d.as_of]
        metric = metrics(points, d.as_of); end = metric['end']
        fresh = bool(metric['complete'] and metric['change'] is not None and end and 0 <= (date.fromisoformat(d.as_of) - date.fromisoformat(end)).days <= 3
                     and 0 <= age(p.get('retrieved_at'), now) <= 72 and not p.get('error'))
        match = [e for e in entities if e['symbol'] == spec['symbol']]
        item = dict(**spec, entity=match[0]['id'] if len(match) == 1 else None, points=points, metrics=metric, fresh=fresh,
                    spike=bool(fresh and metric['change'] is not None and metric['change'] >= 40),
                    retrieved_at=p.get('retrieved_at') if same else None, checked_at=p.get('checked_at'), error=p.get('error'),
                    source_url=p.get('source_url') if same else None, article_url='https://' + cfg['project'] + '/wiki/' + quote(spec['title'].replace(' ', '_'), safe=''))
        items.append(item)
        if len(match) == 1:
            match[0]['attention'] = deepcopy(item)
    view = dict(type='attention', group='지금 주목', title='기업 관심도 · 위키백과 열람', items=items,
                collection=packet.get('collection', {}), source_vintage=path.parent.parent.name if path.exists() else None,
                scope='영문 위키백과 10개 지정 기업 문서의 일별 user 열람입니다. 최근7일 합계와 직전7일을 비교하며 +40% 이상을 관심도 급등으로 표시합니다. 고유 방문자·투자자 수·검색량·뉴스 감성이 아닙니다. 원본의 비교 기간은 미공개이며 이 계산은 팀 규칙입니다. UTC 일자를 쓰고 이틀의 수집 시차를 둡니다. 분모0·14일 누락·오래된/실패 관측은 신호를 만들지 않습니다.')
    dragon['sections'] = [s for s in dragon['sections'] if s['type'] != 'attention'] + [view]
    return dragon
